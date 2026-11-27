"""Isolated offline variants of the frozen S2 (V2 Standard) packet: explicit paper resolution + balanced allocation.
0 model calls. Frozen S2 code is imported unchanged; nothing in the demo engine changes.

Rule (fixed before any result was measured):
  1. Requested papers. Named terms are taken from the question (components.named_terms: words with internal
     capitals or digits, hyphenated names, quoted phrases; generic acronyms excluded). A paper is REQUESTED when a
     named term occurs as a whole word in its title AND the paper has at least one passage in S2's top-120 for the
     question. No paper IDs, benchmark questions or answers are used.
  2. Fewer than two requested papers: the packet is exactly frozen S2 (single-paper and unnamed questions unchanged).
  3. Two or more (B1, balanced allocation): the 30-candidate window is rebuilt as a round-robin over the requested
     papers, each contributing its passages in S2's own order (from the top-120), up to WINDOW // n_papers each,
     followed by the rest of S2's top-30. Then the frozen select_grouped at 6,000 tokens and the frozen C2 conclusion
     allowance, unchanged.
  B2 (separately scoped expansion): as B1, but each requested paper's candidate list is ordered by its best rank in
     S2's original ranking or in any question-component ranking restricted to that paper (paper-scoped component
     candidates, no original-paper filter). Extra searches run only when >= 2 papers are requested.
"""
import re

import s3_env  # noqa: F401
import evidence as ev  # frozen V2
from components import components, named_terms


def requested_papers(question, ranked_ids, titles):
    terms = [t for t in named_terms(question) if not t.lower().startswith('gpt')] or []
    pool = {}
    for cid in ranked_ids[:ev.CANDIDATE_DEPTH]:
        pool.setdefault(cid.split('_')[0], None)
    out = []
    for paper in pool:
        title = titles.get(paper, '')
        if any(re.search(r'(?<![\w-])' + re.escape(t) + r'(?![\w-])', title, re.I) for t in terms):
            out.append(paper)
    return out


def packet(question, order, rows, count, tables, titles, *, mode, component_orders=None):
    """order: S2's ranked chunk ids for the question. mode: 'S2' | 'B1' | 'B2'."""
    ranked = lambda q, n: [rows[c] for c in order[:n]]  # noqa: E731
    papers = requested_papers(question, order, titles) if mode != 'S2' else []
    if len(papers) < 2:
        return ev.standard_packet(question, ranked, count, tables), papers
    per = {}
    for p in papers:
        own = [c for c in order[:ev.CANDIDATE_DEPTH] if c.startswith(p + '_')]
        if mode == 'B2':
            best = {c: i for i, c in enumerate(own)}
            for co in component_orders or []:
                for i, c in enumerate([x for x in co if x.startswith(p + '_')][:ev.WINDOW]):
                    best[c] = min(best.get(c, 10 ** 6), i)
            own = sorted(best, key=lambda c: (best[c], c))
        per[p] = own[:ev.WINDOW // len(papers)]
    window = []
    for i in range(max(len(v) for v in per.values())):
        window += [v[i] for v in per.values() if i < len(v) and v[i] not in window]
    window += [c for c in order[:ev.WINDOW] if c not in window]
    passages, _notes, used = ev.select_grouped([rows[c] for c in window[:ev.WINDOW]], ev.STANDARD_TOKENS, count, tables)
    candidates = [rows[c] for c in order[:ev.CANDIDATE_DEPTH]]
    conclusions, extra, _ = ev.conclusion_coverage(candidates, passages, count)
    if conclusions and ev.serialized_estimate(passages + conclusions) > ev.DEEP_EVIDENCE_EST:
        conclusions, extra = [], 0
    passages = passages + conclusions
    return {'passages': passages, 'tokens': used + extra, 'base_tokens': used,
            'notes': ev.table_notes(passages, tables)}, papers


if __name__ == '__main__':  # self-check on synthetic titles (not from any evaluation set)
    titles = {'P1': 'FooNet: fast things', 'P2': 'BarGuard 2.0: guards', 'P3': 'Unrelated GPT-4 study'}
    ids = ['P1_c0000', 'P2_c0000', 'P3_c0000']
    assert requested_papers('How do FooNet and BarGuard compare with GPT-4?', ids, titles) == ['P1', 'P2']
    assert requested_papers('What does the catalyst study report?', ids, titles) == []
    print('ok')

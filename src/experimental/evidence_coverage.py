"""General evidence coverage for bounded answer evidence.

Three rules, none keyed to question wording, paper titles or expected answers:

1. Part coverage: each independently retrievable part of a multi-part or
   comparison question (see question_parts) gets its own retrieval, and its best
   passages are anchored before the shared ranking fills the remaining budget.
2. Paper balance: when a question has several parts, no single paper may take
   more than half the budget while another part's paper is waiting.
3. Role coverage: a paper that holds at least three slots keeps its own
   abstract, a quantitative passage and (for externally discovered papers) a
   dated study-scope passage when those exist, replacing that paper's lowest-
   ranked passages. Other papers' slots and the paper's best passage are never
   displaced, and the evidence budget never grows.
"""
import math
import re

from .question_parts import question_parts
from .retriever import Lexical, tokens

QUANT = re.compile(r"\d+(?:\.\d+)?\s*(?:\\?%|percent\b|\\times|×|x\b|points?\b|pp\b)"
                   r"|\b\d+\.\d+\b|\b\d{1,3}(?:,\d{3})+\b", re.I)
DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
                  r"\s+\d{1,2}(?:,|\s)|\b(?:19|20)\d{2}-\d{2}-\d{2}\b", re.I)
EXCLUDED_SECTION = re.compile(r"reference|bibliograph|acknowledg", re.I)
ABSTRACT = re.compile(r"^\s*abstract\s*$", re.I)
RESULTS_SECTION = re.compile(r"results?|evaluation|experimental|methods?", re.I)
SCOPE_SECTION = re.compile(r"method|experiment|evaluation|setup|setting|data|procedure|protocol", re.I)
METHOD = 'part-balanced-role-coverage-v2'
GENERIC = set('one ones each some only much many it its they them this that those these was were up any all '
              'whether also there their then than'.split())


def coverage_candidates(question, parents, papers):
    """Offer results/methods passages without reserving evidence slots."""
    return [p['chunk_id'] for p in parents if p.get('arxiv_id') in papers
            and re.search(r"results?|evaluation|experiments?|performance|methods?|methodology", p.get('section', ''), re.I)]


def retrievable_parts(question):
    """Parts with enough content to retrieve on their own (no dangling pronoun clauses)."""
    return [p for p in question_parts(question) if len(set(tokens(p)) - GENERIC) >= 3]


def _paper(p):
    return p.get('arxiv_id') or p.get('title')


def merge_ranked(lists, top_k):
    """Anchor each list's best passages, then fill by reciprocal-rank fusion with paper balance."""
    lists = [l for l in lists if l]
    if not lists:
        return []
    byid, fused = {}, {}
    for ranked in lists:  # each explicit part counts as much as the whole question
        weight = 1.0
        for rank, p in enumerate(ranked):
            byid.setdefault(p['chunk_id'], p)
            fused[p['chunk_id']] = fused.get(p['chunk_id'], 0) + weight / (20 + rank)
    selected = []
    for depth in range(2 if len(lists) > 1 else 1):
        for ranked in lists:
            pick = next((p['chunk_id'] for p in ranked if p['chunk_id'] not in selected), None)
            if pick and len(selected) < top_k:
                selected.append(pick)
    order = sorted(fused, key=lambda i: (-fused[i], i))
    cap = top_k if len(lists) == 1 else max(2, math.ceil(top_k / 2))
    papers = {_paper(byid[s]) for s in selected}
    for ident in order:
        if len(selected) >= top_k:
            break
        if ident in selected:
            continue
        paper = _paper(byid[ident])
        if len(papers) > 1 and sum(_paper(byid[s]) == paper for s in selected) >= cap:
            continue
        selected.append(ident)
    for ident in order:  # budget left after balancing: fill without a cap
        if len(selected) >= top_k:
            break
        if ident not in selected:
            selected.append(ident)
    return [byid[i] for i in selected]


def _best(candidates, query):
    if not candidates:
        return None
    scores = Lexical([c.get('title', '') + ' ' + c.get('section', '') + ' ' + c['text']
                      for c in candidates]).score(query)
    # Among comparably relevant passages, prefer the one reporting more values.
    scores = [s * (1 + min(5, len(QUANT.findall(c['text']))) / 10) for s, c in zip(scores, candidates)]
    # Candidates already belong to a paper the ranking selected, so a role passage
    # with no lexical overlap (e.g. a dated methods passage) remains eligible.
    return candidates[max(range(len(candidates)), key=lambda i: (scores[i], -i))]


def _is_abstract(p):
    return bool(ABSTRACT.match(p.get('section', '')))


def _is_quantitative(p):
    """A reported-results passage: at least two values outside the abstract."""
    return not _is_abstract(p) and len(QUANT.findall(p['text'])) >= 2


def _is_scope(p):
    return bool(DATE.search(p['text']) and SCOPE_SECTION.search(
        p.get('section', '') + ' ' + p.get('subsection', '')))


def cover_roles(query, selected, paper_passages, *, external=False):
    """Fill missing evidence roles for papers that dominate the budget (budget unchanged).

    Library evidence keeps only the abstract role: swapping in a 'results' passage
    displaced the ranked table row or method passage that actually answered the
    question (development set). Newly read external papers keep abstract, results
    and study-scope roles, which that evaluation did not cover.
    """
    result = list(selected)
    papers = list(dict.fromkeys(_paper(p) for p in result))
    roles = [_is_abstract] + ([_is_quantitative, _is_scope] if external else [])
    for paper in papers:
        own = [i for i, p in enumerate(result) if _paper(p) == paper]
        if len(own) < 3:
            continue
        pool = [p for p in paper_passages.get(paper, []) if not EXCLUDED_SECTION.search(p.get('section', ''))]
        present = {result[i]['chunk_id'] for i in own}
        replaceable = own[1:]  # never displace the paper's best passage
        for role in roles:
            if not replaceable:
                break
            if role is _is_scope:  # any dated scope passage suffices
                if any(role(result[i]) for i in own):
                    continue
                pick = _best([p for p in pool if role(p) and p['chunk_id'] not in present], query)
            else:  # the paper's most relevant abstract / results passage must be present
                pick = _best([p for p in pool if role(p)], query)
                if pick is not None and pick['chunk_id'] in present:
                    continue
            if pick is None:
                continue
            slot = replaceable.pop()  # lowest-ranked remaining passage of this paper
            present.discard(result[slot]['chunk_id'])
            result[slot] = pick
            present.add(pick['chunk_id'])
            own = [i for i, p in enumerate(result) if _paper(p) == paper]
    return _abstracts_for_minor_papers(query, result, paper_passages)


def _abstracts_for_minor_papers(query, result, paper_passages, max_swaps=2):
    """Give a paper holding one or two slots its abstract, taken from a crowded paper's tail.

    The swap happens only when that abstract matches the question at least as well
    as the crowded paper's passage it replaces, and never touches the crowded
    paper's two best passages.
    """
    counts = {}
    for p in result:
        counts[_paper(p)] = counts.get(_paper(p), 0) + 1
    if not counts:
        return result
    dominant = max(counts, key=lambda k: counts[k])
    if counts[dominant] < 4:
        return result
    minors = [k for k in dict.fromkeys(_paper(p) for p in result) if counts[k] <= 2]
    swaps = 0
    for paper in minors:
        if swaps >= max_swaps:
            break
        if any(_paper(p) == paper and _is_abstract(p) for p in result):
            continue
        abstracts = [p for p in paper_passages.get(paper, []) if _is_abstract(p)]
        tail = [i for i in [i for i, p in enumerate(result) if _paper(p) == dominant][2:]
                if not _is_abstract(result[i])]
        if not abstracts or not tail:
            continue
        slot = tail[-1]
        texts = [result[slot]] + abstracts
        scores = Lexical([c.get('title', '') + ' ' + c['text'] for c in texts]).score(query)
        best = max(range(1, len(texts)), key=lambda i: (scores[i], -i))
        if scores[best] > 0 and scores[best] >= scores[0]:
            result[slot] = texts[best]
            swaps += 1
    return result


def with_result_coverage(retrieve, parents, *, retrieve_part=None):
    """Library retrieval with part coverage, paper balance and role coverage.

    `retrieve_part` ranks question parts (default: `retrieve`); the B2 adapter
    supplies its lower-cost light ranking so a part does not repeat a full rerank.
    """
    by_paper = {}
    for p in parents:
        by_paper.setdefault(_paper(p), []).append(p)
    part_search = retrieve_part or retrieve

    def search(question, top_k):
        parts = retrievable_parts(question)
        main = retrieve(question, min(20, 2 * top_k) if parts else top_k)
        lists = [main] + [part_search(part, top_k) for part in parts]
        return cover_roles(question, merge_ranked(lists, top_k), by_paper)
    search.coverage = coverage_provenance()
    return search


def coverage_provenance():
    """Identify the evidence-coverage implementation in result provenance."""
    from hashlib import sha256
    from pathlib import Path
    here = Path(__file__).resolve().parent
    return {'method': METHOD, 'implementation_sha256': {
        name: sha256((here / name).read_bytes()).hexdigest()
        for name in ('evidence_coverage.py', 'question_parts.py')}}


def cross_encoder_scorer(model, *, pool=60):
    """Semantic relevance for external passages using the library's local cross-encoder.

    Scoring only: passages are truncated for the score, while the full passage is
    what gets cited.
    """
    def score(question, passages):
        pairs = [(question, 'Title: ' + p['title'] + '\nSection: ' + p.get('section', '') + '\n' + p['text'])
                 for p in passages]
        return [float(x) for x in model.predict(pairs, batch_size=16, show_progress_bar=False)]
    score.pool = pool
    return score


def select_external(question, terms, passages, top_k, rerank=None):
    """Rank passages from newly read papers with the same coverage rules."""
    if not passages:
        return []
    query = question + ' ' + ' '.join(terms)
    lexical = Lexical([p['title'] + ' ' + p['text'] for p in passages])

    def ranked(q, scores=None, semantic_query=None):
        scores = lexical.score(q) if scores is None else scores
        order = [passages[i] for i in sorted(range(len(passages)), key=lambda i: (-scores[i], i)) if scores[i] > 0]
        if rerank is not None and order:
            head = order[:rerank.pool]
            ce = rerank(semantic_query or q, head)
            order = [head[i] for i in sorted(range(len(head)), key=lambda i: (-ce[i], i))] + order[rerank.pool:]
        return order
    scores = lexical.score(query)
    for i, p in enumerate(passages):  # findings sections outrank background at equal term match
        if RESULTS_SECTION.search(p.get('section', '')):
            scores[i] *= 1.25
    lists = [ranked(query, scores, semantic_query=question)] + [ranked(part) for part in retrievable_parts(question)]
    best = {}
    for p, s in zip(passages, scores):
        best[_paper(p)] = max(best.get(_paper(p), 0), s)
    top = max(best.values()) if best else 0
    relevant = [k for k, v in best.items() if top > 0 and v >= 0.5 * top]
    if len(relevant) > 1:  # each comparably relevant paper contributes its own best passages
        lists += [[p for p in lists[0] if _paper(p) == paper] for paper in relevant]
    by_paper = {}
    for p in passages:
        by_paper.setdefault(_paper(p), []).append(p)
    return cover_roles(query, merge_ranked(lists, top_k), by_paper, external=True)

"""S3 retrieval R: component-fusion evidence packet (no model calls).

Measured offline (PLAN.md §1, policy "FA at 8k"): covered 162/185 anchored development points vs 142 for the frozen
V2 Standard packet, 3 points lost, off-paper share 11% vs 15%.

  1. components(question): deterministic asks (components.py), at most 6, each prefixed with the question's names.
  2. One B2 search per component (3 workers), restricted to papers that appear in the original question's top-30.
  3. Fused order over the original top-120 and each component's paper-scoped top-30:
        score = 1/(20 + rank_original) + mean_c 1/(20 + rank_c)      (B2's own facet fusion, over every component)
     The original top-4 are kept first, unconditionally.
  4. The frozen V2 select_grouped (whole table groups or an incomplete-table note) over the top-30 of that order,
     HARD CAP 8,000 passage tokens; then the frozen C2 conclusion coverage in its own 800-token allowance.
  5. Request-size guard: if the serialized packet exceeds V2's 38k estimate, conclusions are dropped first, then
     the lowest-fused passages from the end (never the original top-4), exactly as V2 Deep trims.
A failed component search is skipped and recorded; the original search failing propagates (as in V2).
"""
from concurrent.futures import ThreadPoolExecutor

import s3_env  # noqa: F401
import evidence as ev  # frozen V2
from components import components

S3_TOKENS = 8000          # hard cap on base passage tokens (V2 Deep's existing budget)
PROTECT_TOP = 4
COMPONENT_DEPTH = 300     # component rankings are read this deep before paper scoping
RRF_K = 20


def _paper(passage):
    return passage.get('arxiv_id') or passage['chunk_id'].split('_')[0]


def _component_search(ranked, query):
    try:
        return ranked(query, COMPONENT_DEPTH), None
    except Exception as error:  # a component search never blocks the answer
        return [], f'{type(error).__name__}: {str(error)[:160]}'


def fused_order(question, ranked, *, parallel=True):
    """Returns (ordered candidate passages, search log)."""
    original = ranked(question, ev.CANDIDATE_DEPTH)
    papers = {_paper(p) for p in original[:ev.WINDOW]}
    comps = components(question)
    if parallel and len(comps) > 1:
        with ThreadPoolExecutor(max_workers=min(ev.SEARCH_WORKERS, len(comps))) as pool:
            results = list(pool.map(lambda q: _component_search(ranked, q), comps))
    else:
        results = [_component_search(ranked, q) for q in comps]
    log = [{'query': question, 'purpose': 'original question', 'role': 'original',
            'chunk_ids': [p['chunk_id'] for p in original[:ev.WINDOW]], 'error': None}]
    by_id = {p['chunk_id']: p for p in original}
    r0 = {p['chunk_id']: i + 1 for i, p in enumerate(original)}
    rc = []
    for query, (found, error) in zip(comps, results):
        scoped = [p for p in found if _paper(p) in papers][:ev.WINDOW]
        for p in scoped:
            by_id.setdefault(p['chunk_id'], p)
        rc.append({p['chunk_id']: i + 1 for i, p in enumerate(scoped)})
        log.append({'query': query, 'purpose': 'question component', 'role': 'component',
                    'chunk_ids': [p['chunk_id'] for p in scoped], 'error': error})
    usable = [r for r, (_, error) in zip(rc, results) if error is None]

    def score(cid):
        value = 1 / (RRF_K + r0.get(cid, 10 ** 6))
        if usable:
            value += sum(1 / (RRF_K + r.get(cid, 10 ** 6)) for r in usable) / len(usable)
        return value
    head = [p['chunk_id'] for p in original[:PROTECT_TOP]]
    rest = sorted((c for c in by_id if c not in head), key=lambda c: (-score(c), c))
    order = head + rest
    return [by_id[c] for c in order], original, log


def s3_packet(question, ranked, count, tables, *, budget=S3_TOKENS, parallel=True):
    ordered, original, log = fused_order(question, ranked, parallel=parallel)
    passages, _notes, used = ev.select_grouped(ordered[:ev.WINDOW], budget, count, tables)
    assert used <= budget
    conclusions, extra, considered = ev.conclusion_coverage(original, passages, count)
    if conclusions and ev.serialized_estimate(passages + conclusions) > ev.DEEP_EVIDENCE_EST:
        conclusions, extra = [], 0
        considered = [{**c, 'dropped': 'request-size guard'} for c in considered]
    head = {p['chunk_id'] for p in ordered[:PROTECT_TOP]}
    trimmed = []
    while ev.serialized_estimate(passages) > ev.DEEP_EVIDENCE_EST and passages and passages[-1]['chunk_id'] not in head:
        dropped = passages.pop()
        trimmed.append(dropped['chunk_id'])
        used -= count(dropped)
    passages = passages + conclusions
    return {'passages': passages, 'notes': ev.table_notes(passages, tables), 'tokens': used + extra,
            'base_tokens': used, 'base_budget': budget, 'conclusion_tokens': extra,
            'conclusion_allowance': ev.CONCLUSION_TOKENS, 'conclusion_ids': [c['chunk_id'] for c in conclusions],
            'conclusion_considered': considered, 'protected_ids': [p['chunk_id'] for p in passages],
            'supplementary_ids': [], 'trimmed_for_request_size': trimmed, 'searches': log,
            'components': components(question)}

"""Shared evidence management for Standard and Deep Research (no model calls). (consolidated-v2)

v2: C2 bounded conclusion coverage (separate, reported allowance), C3 consolidated incomplete-table notes,
L3 parallel supplementary searches with deterministic merge order.

Reuses B2 ranking and the evidence-budget skip-fit policy (experiments/evidence-budget). Additions, each tied to a
documented failure:
  - Protected packet: the original-question packet (6k skip-fit, window 30) is selected first and is never displaced.
  - Deep merge: supplementary passages from planned searches are added round-robin after the protected packet,
    deduplicated by chunk_id, within a bounded total (8k MiniLM passage tokens, at most 40 passages).
  - Table groups (combined-v1 G07.2/G07.3: one row of a two-row comparison was retrieved): when a table row is
    selected, its sibling rows from the same table are added as a whole group if the group fits the budget. If not,
    the selected rows are kept and the table is recorded as incomplete; that note goes to synthesis and is published,
    so a partial table is never presented as a complete comparison.
Whole parent rows only, original text, original chunk IDs and metadata.
"""
from copy import deepcopy
import re

STANDARD_TOKENS = 6000
DEEP_TOKENS = 8000
WINDOW = 30
SUPPLEMENTARY_TOP_K = 8
MAX_PASSAGES = 40
DEEP_EVIDENCE_EST = 38_000  # request-guard estimate (ceil(UTF-8 bytes / 3)) of the serialized packet; guard cap is 40,000
MAX_GROUP_ROWS = 12
CONCLUSION_TOKENS = 800      # C2: explicit supplementary allowance, reported separately from the 6k base budget
CONCLUSION_PAPERS = 2        # at most two papers
CONCLUSION_RANK_LIMIT = 100  # a conclusion must itself rank within B2's top 100 for the question (general relevance)
CANDIDATE_DEPTH = 120
SEARCH_WORKERS = 3
_CONCLUSION = re.compile(r'conclu', re.I)  # larger tables are never expanded (a row of them is kept and marked incomplete)
_TABLE = re.compile(r'^(?P<table>.+_table_[0-9a-f]+)_(?P<row>\d+)$')
_CAPTION = re.compile(r'(Table\s+\d+[^.;]{0,100})')


def table_key(chunk_id):
    match = _TABLE.match(chunk_id or '')
    return (match.group('table'), int(match.group('row'))) if match else (None, None)


class TableIndex:
    """Every row of every table in the bundle, by table key (from parents.jsonl rows)."""

    def __init__(self, rows):
        self.tables = {}
        for row in rows:
            key, number = table_key(row.get('chunk_id'))
            if key:
                self.tables.setdefault(key, []).append((number, row))
        for key in self.tables:
            self.tables[key].sort(key=lambda item: item[0])

    def siblings(self, chunk_id):
        key, _ = table_key(chunk_id)
        return [row for _, row in self.tables.get(key, [])] if key else []


def _caption(rows):
    for row in rows:
        match = _CAPTION.search(row.get('text', ''))
        if match:
            return match.group(1).strip()
    return 'a table'


def select_grouped(candidates, budget, count, tables, *, protected=(), max_passages=MAX_PASSAGES):
    """Skip-fit over `candidates` in order, after `protected` (kept whole, first). A table row brings its sibling
    rows as one group when the whole group fits; otherwise the row alone is considered (Baseline behaviour).
    Returns (passages, notes)."""
    chosen, ids, used = [], set(), 0
    for passage in protected:
        if passage['chunk_id'] not in ids:
            chosen.append(deepcopy(passage))
            ids.add(passage['chunk_id'])
            used += count(passage)
    for passage in candidates:
        if passage['chunk_id'] in ids or len(chosen) >= max_passages:
            continue
        group = [row for row in tables.siblings(passage['chunk_id']) if row['chunk_id'] not in ids]
        if group and len(tables.siblings(passage['chunk_id'])) <= MAX_GROUP_ROWS:
            # Retrieved metadata wins for the retrieved row; siblings come from the bundle unchanged.
            group = [passage if row['chunk_id'] == passage['chunk_id'] else row for row in group]
            cost = sum(count(row) for row in group)
            if used + cost <= budget and len(chosen) + len(group) <= max_passages:
                for row in group:
                    chosen.append(deepcopy(row))
                    ids.add(row['chunk_id'])
                used += cost
                continue
        cost = count(passage)
        if used + cost <= budget:
            chosen.append(deepcopy(passage))
            ids.add(passage['chunk_id'])
            used += cost
    return chosen, table_notes(chosen, tables), used


def table_notes(passages, tables):
    """Incomplete-table notes. C3: when one paper has more than two partial tables, they are consolidated into one
    note that still names every table and its row coverage, so no missing evidence is hidden."""
    present, per_paper = {}, {}
    for passage in passages:
        key, number = table_key(passage['chunk_id'])
        if key:
            present.setdefault(key, []).append(number)
    for key, numbers in present.items():
        rows = tables.tables.get(key, [])
        if rows and len(numbers) < len(rows):
            all_rows = [row for _, row in rows]
            title = all_rows[0].get('title') or all_rows[0].get('arxiv_id', '')
            per_paper.setdefault(title, []).append(
                {'kind': 'incomplete_table', 'table': key, 'rows_in_evidence': sorted(numbers),
                 'rows_in_table': len(rows), 'caption': _caption(all_rows)})
    notes = []
    for title, items in per_paper.items():
        if len(items) <= 2:
            for n in items:
                notes.append({**n, 'text': f"Only {len(n['rows_in_evidence'])} of {n['rows_in_table']} rows of "
                                          f"{n['caption']} ({title}) are in the evidence, so a comparison across that "
                                          'table may be incomplete.'})
        else:
            parts = '; '.join(f"{n['caption'][:60]}: {len(n['rows_in_evidence'])} of {n['rows_in_table']} rows"
                              for n in items)
            notes.append({'kind': 'incomplete_tables', 'tables': [n['table'] for n in items], 'paper': title,
                          'text': f'{len(items)} tables from {title} are only partly in the evidence ({parts}), so '
                                  'comparisons across those tables may be incomplete.'})
    return notes


def conclusion_coverage(candidates, passages, count, *, allowance=CONCLUSION_TOKENS):
    """C2: add the conclusion passage of up to CONCLUSION_PAPERS papers that contribute the most passages (at least 2)
    to the packet, if that conclusion ranks within CONCLUSION_RANK_LIMIT for the question and fits the allowance.
    Selection uses only the packet and B2's ranking; nothing is labelled by evaluation questions."""
    ids = {p['chunk_id'] for p in passages}
    order = {p['chunk_id']: i for i, p in enumerate(candidates)}
    tally = {}
    for p in passages:
        tally.setdefault(p.get('arxiv_id'), []).append(order.get(p['chunk_id'], 10**6))
    papers = sorted((a for a, ranks in tally.items() if a and len(ranks) >= 2),
                    key=lambda a: (-len(tally[a]), min(tally[a])))[:CONCLUSION_PAPERS]
    added, used, considered = [], 0, []
    for arxiv in papers:
        pick = next((c for c in candidates[:CONCLUSION_RANK_LIMIT]
                     if c.get('arxiv_id') == arxiv and c['chunk_id'] not in ids
                     and _CONCLUSION.search(c.get('section') or '')), None)
        considered.append({'paper': arxiv, 'conclusion': pick['chunk_id'] if pick else None,
                           'rank': order[pick['chunk_id']] + 1 if pick else None})
        if pick and used + count(pick) <= allowance:
            added.append(deepcopy(pick))
            ids.add(pick['chunk_id'])
            used += count(pick)
    return added, used, considered


def standard_packet(question, ranked, count, tables, budget=STANDARD_TOKENS):
    """Protected original-question packet: group-aware 6k skip-fit over B2's top-30, plus C2 conclusion coverage
    within its own reported allowance. If the conclusions would push the serialized request past the guard estimate,
    they are dropped (never silently exceeded)."""
    candidates = ranked(question, CANDIDATE_DEPTH)
    passages, notes, used = select_grouped(candidates[:WINDOW], budget, count, tables)
    conclusions, extra, considered = conclusion_coverage(candidates, passages, count)
    if conclusions and serialized_estimate(passages + conclusions) > DEEP_EVIDENCE_EST:
        conclusions, extra = [], 0
        considered = [{**c, 'dropped': 'request-size guard'} for c in considered]
    passages = passages + conclusions
    return {'passages': passages, 'notes': table_notes(passages, tables), 'tokens': used + extra,
            'base_tokens': used, 'base_budget': budget, 'conclusion_tokens': extra,
            'conclusion_allowance': CONCLUSION_TOKENS, 'conclusion_ids': [c['chunk_id'] for c in conclusions],
            'conclusion_considered': considered, 'protected_ids': [p['chunk_id'] for p in passages],
            'searches': [{'query': question, 'purpose': 'original question', 'role': 'protected',
                          'chunk_ids': [p['chunk_id'] for p in passages], 'error': None}]}


def _search(ranked, search):
    try:
        return ranked(search['query'], SUPPLEMENTARY_TOP_K)[:SUPPLEMENTARY_TOP_K], None
    except Exception as error:  # a supplementary search never blocks the answer
        return [], f'{type(error).__name__}: {str(error)[:160]}'


def run_searches(ranked, searches, *, parallel=True):
    """L3: independent supplementary searches run concurrently (at most SEARCH_WORKERS threads); results are returned
    in the planned order, so the merge is deterministic. Each search's error is isolated."""
    if not parallel or len(searches) < 2:
        return [_search(ranked, s) for s in searches]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(SEARCH_WORKERS, len(searches))) as pool:
        return list(pool.map(lambda s: _search(ranked, s), searches))


def deep_packet(question, searches, ranked, count, tables, *, protected=None, budget=DEEP_TOKENS, parallel=True):
    """Protected packet first, then supplementary passages round-robin across planned searches (top-8 each),
    deduplicated, bounded to `budget` total. A failed supplementary search is skipped and recorded."""
    base = protected or standard_packet(question, ranked, count, tables)
    log, batches = list(base['searches']), []
    for search, (found, error) in zip(searches, run_searches(ranked, searches, parallel=parallel)):
        log.append({'query': search['query'], 'purpose': search['purpose'], 'role': 'supplementary',
                    'chunk_ids': [p['chunk_id'] for p in found], 'error': error})
        batches.append(found)
    interleaved, seen = [], set(base['protected_ids'])
    for depth in range(max((len(b) for b in batches), default=0)):
        for batch in batches:
            if depth < len(batch) and batch[depth]['chunk_id'] not in seen:
                interleaved.append(batch[depth])
                seen.add(batch[depth]['chunk_id'])
    passages, notes, used = select_grouped(interleaved, budget + base.get('conclusion_tokens', 0), count, tables,
                                           protected=base['passages'])
    protected_ids = set(base['protected_ids'])
    trimmed = []
    # Table-heavy passages serialize large: keep the request under the guard by dropping supplementary passages from
    # the end (never protected ones), so Deep never fails a request that Standard's packet alone would pass.
    while serialized_estimate(passages) > DEEP_EVIDENCE_EST and passages[-1]['chunk_id'] not in protected_ids:
        dropped = passages.pop()
        trimmed.append(dropped['chunk_id'])
        used -= count(dropped)
    if trimmed:
        notes = table_notes(passages, tables)
    assert [p['chunk_id'] for p in passages[:len(protected_ids)]] == base['protected_ids'], 'protected packet displaced'
    return {'passages': passages, 'notes': notes, 'tokens': used, 'protected_ids': base['protected_ids'],
            'supplementary_ids': [p['chunk_id'] for p in passages if p['chunk_id'] not in protected_ids],
            'trimmed_for_request_size': trimmed, 'searches': log,
            'base_budget': budget, 'conclusion_tokens': base.get('conclusion_tokens', 0),
            'conclusion_allowance': base.get('conclusion_allowance', 0), 'conclusion_ids': base.get('conclusion_ids', [])}


def serialized_estimate(passages):
    """The request guard's estimate of the evidence part of a synthesis request (request_guard.evidence_of)."""
    import json
    import math
    from synthesis import compact_passage  # v2: measure what is actually sent (compact serialization)
    body = json.dumps([[compact_passage(p) for p in passages]], ensure_ascii=False)
    return math.ceil(len(body.encode('utf-8')) / 3)

"""Model-free chart preview: retrieved table rows -> audit-verified complete tables.

Experimental, isolated (2026-11-17). Used by ``POST /api/chart-preview`` so an explicit chart
question can show a verified chart within seconds, before (and independently of) the
generated research explanation.

Inputs are the passages the B2 retriever returns for the question and the ``TableIndex``
(which only returns a table when the extractor audit proves it complete). Nothing is generated,
parsed into new values or inferred. The page re-runs its own checks on the result (round trip
of the retrieved rows, merge against the complete table, chart eligibility) before drawing.
"""
import re

MAX_TABLES = 3            # verified tables returned per question
MAX_QUERY_CHARS = 2000
CHART_INTENT = re.compile(r'\b(?:charts?|graphs?|plots?|plotting|visuali[sz](?:e|ed|ing|ation)|bar\s+charts?|diagram)\b', re.I)
TABLE_REFERENCE = re.compile(r'\btables?\s+([A-Z]?\d{1,3})\b', re.I)
CAPTION_NUMBER = re.compile(r'^\s*Table\s*([A-Z]?\d{1,3})\b', re.I)


def chart_intent(query):
    """True only when the question explicitly asks for a chart, graph, plot or visualization."""
    return isinstance(query, str) and bool(CHART_INTENT.search(query))


def requested_tables(query):
    """Table numbers the question names explicitly ("using Table 4" -> {'4'})."""
    return {match.upper() for match in TABLE_REFERENCE.findall(query or '')}


NUMBER_WORDS = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
                'ten': 10, 'eleven': 11, 'twelve': 12}
ENTITY_COUNT = re.compile(r'\b(\d{1,2}|' + '|'.join(NUMBER_WORDS) + r')\s+(?:[a-z-]+\s+){0,2}(?:models|methods|systems|datasets|benchmarks|baselines)\b', re.I)


def requested_count(query):
    """'the seven base models' -> 7. Used only to order candidate tables, never to filter rows."""
    match = ENTITY_COUNT.search(query or '')
    if not match:
        return None
    token = match.group(1).lower()
    return int(token) if token.isdigit() else NUMBER_WORDS[token]


def caption_number(caption):
    match = CAPTION_NUMBER.match(caption or '')
    return match.group(1).upper() if match else None


def candidate_tables(passages, query, tables=None):
    """Group retrieved table rows by table, most relevant first.

    Priority: a table the question names ("Table 4"); then, when the question states a count
    ("seven base models") and the index is available, a table whose first column has exactly that
    many distinct labels; then the table with more retrieved rows; then the better best rank.
    Text passages are ignored here; they stay in the research answer.
    """
    named = requested_tables(query)
    count = requested_count(query)
    groups = {}
    for rank, passage in enumerate(passages, 1):
        if passage.get('representation') != 'linearized_table' or not passage.get('table_id'):
            continue
        key = (passage.get('arxiv_id'), passage['table_id'])
        group = groups.setdefault(key, {'key': f'{key[0]}#{key[1]}', 'arxiv_id': key[0], 'table_id': key[1],
                                        'caption': passage.get('caption'), 'best_rank': rank, 'rows': []})
        group['rows'].append(passage)
    for group in groups.values():
        number = caption_number(group['caption'])
        group['caption_number'] = number
        group['named_in_question'] = bool(number and number in named)
        group['matches_count'] = False
        if count and tables is not None:
            stored = tables.tables.get((group['arxiv_id'], group['table_id']), [])
            labels = {p.get('row_label') for p in stored}
            group['matches_count'] = len(labels) == count
    return sorted(groups.values(), key=lambda g: (not g['named_in_question'], not g['matches_count'],
                                                  -len(g['rows']), g['best_rank']))


def preview(query, passages, tables, index_sha256, *, max_tables=MAX_TABLES):
    """Return verified complete tables for the question's retrieved table rows (0 model calls)."""
    from evidence_tables import TableUnavailable
    candidates = candidate_tables(passages, query, tables)
    out, evidence = [], []
    for group in candidates[:max_tables]:
        entry = {'key': group['key'], 'arxiv_id': group['arxiv_id'], 'table_id': group['table_id'],
                 'caption': group['caption'], 'caption_number': group['caption_number'],
                 'named_in_question': group['named_in_question'], 'matches_count': group['matches_count'],
                 'best_rank': group['best_rank'],
                 'retrieved_rows': [p['table_row'] for p in group['rows']]}
        try:
            entry.update(status='complete', table=tables.table(group['rows'][0]['chunk_id'], index_sha256))
        except TableUnavailable as error:
            # Never offered as a chart: the page keeps such rows as "retrieved rows only".
            entry.update(status='refused', code=error.code, reason=error.reason, table=None)
        out.append(entry)
        evidence.extend({k: v for k, v in p.items() if k != 'reader'} for p in group['rows'])
    return {'query': query, 'chart_intent': chart_intent(query), 'requested_tables': sorted(requested_tables(query)),
            'requested_count': requested_count(query),
            'index_sha256': index_sha256, 'tables': out, 'evidence': evidence,
            'skipped_tables': [g['key'] for g in candidates[max_tables:]], 'model_calls': 0}

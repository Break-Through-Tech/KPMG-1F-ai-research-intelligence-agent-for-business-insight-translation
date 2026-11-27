"""Read-only, model-free reconstruction of complete source tables from an indexed bundle.

Experimental prototype (2026-11-17). Not part of the shared application.

Input: the bundle's ``parents.jsonl``, already produced by the deterministic HTML extractor
(``src/experimental/html_evidence.py``). Every accepted table is emitted row by row as a
``linearized_table`` passage with ``table_row`` numbered 1..N; a rejected table emits no rows.

A table is returned only when the stored rows can be reassembled without guessing:
rows 1..N present exactly once, one shared header list, caption, source hash, extractor
version, header status and footnotes, and every row has one cell per header with matching
row and column numbers. Otherwise ``TableUnavailable`` names the failed check and no
partial table is returned. Values are copied verbatim; nothing is parsed, filled or inferred.

Completeness (audit fix, 2026-11-17): the checks above cannot tell a whole table from a
contiguous prefix (rows 1..N-1). A table is therefore returned as complete only when an
independent extractor audit (``build_table_audit.py``), bound to this index's SHA-256, says
the extractor accepted the table and emitted exactly N rows that are field-for-field
identical to the stored rows, for the same source hash and extractor version. Without that
audit, or when it disagrees, the table is refused (fail closed, 422 ``completeness_unverified``).
The serialized response is also capped at ``MAX_RESPONSE_BYTES``.
"""
from hashlib import sha256
import json
import re
from pathlib import Path

MAX_ROWS = 200
MAX_COLUMNS = 40
MAX_CELL_CHARS = 2000
MAX_RESPONSE_BYTES = 1_000_000
AUDIT_KIND = 'extractor_table_audit_v1'
CHUNK_ID = re.compile(r'^\d{4}\.\d{4,5}v[1-9]\d*_table_[0-9a-f]{16}_[1-9]\d{0,3}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
SHARED = ('arxiv_id', 'title', 'table_id', 'caption', 'source_sha256', 'extractor_version',
          'header_provenance', 'header_review', 'html_url', 'pdf_url', 'document_region')


class TableUnavailable(Exception):
    """The table cannot be returned; ``code`` is stable, ``reason`` is human-readable."""

    def __init__(self, code, reason, status):
        super().__init__(reason)
        self.code, self.reason, self.status = code, reason, status


class TableIndex:
    def __init__(self, parents_path, audit_path=None):
        path = Path(parents_path)
        raw = path.read_bytes()
        self.index_sha256 = sha256(raw).hexdigest()
        self.audit, self.audit_problem = load_audit(audit_path, self.index_sha256)
        self.rows_by_chunk = {}
        self.tables = {}
        for line in raw.decode('utf-8').splitlines():
            if not line.strip():
                continue
            passage = json.loads(line)
            if passage.get('representation') != 'linearized_table':
                continue
            key = (passage.get('arxiv_id'), passage.get('table_id'))
            self.tables.setdefault(key, []).append(passage)
            self.rows_by_chunk[passage['chunk_id']] = key

    def table(self, chunk_id, index_sha256):
        if not isinstance(chunk_id, str) or not CHUNK_ID.fullmatch(chunk_id):
            raise TableUnavailable('bad_request', 'chunk_id must be a table-row passage ID.', 400)
        if not isinstance(index_sha256, str) or not SHA256.fullmatch(index_sha256):
            raise TableUnavailable('bad_request', 'index must be the 64-character index SHA-256.', 400)
        if index_sha256 != self.index_sha256:
            raise TableUnavailable('index_mismatch',
                'This answer was produced from a different index than the one loaded here.', 409)
        key = self.rows_by_chunk.get(chunk_id)
        if key is None:
            raise TableUnavailable('table_not_in_index', 'No table row with this ID is in the loaded index.', 404)
        return assemble(self.tables[key], self.index_sha256, self.audit, self.audit_problem)


def load_audit(audit_path, index_sha256):
    """Return ``(tables, None)`` for a usable audit, or ``(None, reason)`` so every table fails closed."""
    if audit_path is None:
        return None, 'No extractor audit was loaded, so completeness cannot be established.'
    try:
        audit = json.loads(Path(audit_path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, 'The extractor audit could not be read.'
    if not isinstance(audit, dict) or audit.get('kind') != AUDIT_KIND or not isinstance(audit.get('tables'), dict):
        return None, 'The extractor audit has an unknown format.'
    if audit.get('index_sha256') != index_sha256:
        return None, 'The extractor audit was made for a different index.'
    return audit['tables'], None


def _fail(reason):
    raise TableUnavailable('table_not_reconstructable', reason, 422)


def _unverified(reason):
    raise TableUnavailable('completeness_unverified', reason, 422)


def check_completeness(first, count, audit, audit_problem):
    """Bind the row count to the extractor's own accepted-row count for this exact source."""
    if audit is None:
        _unverified(audit_problem or 'No extractor audit was loaded, so completeness cannot be established.')
    entry = audit.get(f"{first.get('arxiv_id')}#{first.get('table_id')}")
    if not isinstance(entry, dict):
        _unverified('The extractor audit has no record of this table.')
    if entry.get('source_sha256') != first.get('source_sha256') or entry.get('extractor_version') != first.get('extractor_version'):
        _unverified('The extractor audit describes a different source or extractor version.')
    if entry.get('status') != 'accepted':
        _unverified('The extractor did not accept this table.')
    emitted = entry.get('rows_emitted')
    if not isinstance(emitted, int) or isinstance(emitted, bool) or emitted != count:
        _unverified(f'The extractor emitted {emitted} rows for this table but {count} are stored.')
    if entry.get('rows_identical_to_bundle') is not True:
        _unverified('Re-extraction did not reproduce the stored rows exactly.')
    return emitted


def assemble(passages, index_sha256, audit=None, audit_problem=None):
    rows = sorted(passages, key=lambda p: p.get('table_row', 0))
    count = len(rows)
    if count > MAX_ROWS:
        _fail(f'Table has {count} rows; the limit is {MAX_ROWS}.')
    numbers = [p.get('table_row') for p in rows]
    if numbers != list(range(1, count + 1)):
        _fail('Stored rows are not numbered 1..N exactly once.')
    first = rows[0]
    for field in SHARED:
        if any(p.get(field) != first.get(field) for p in rows):
            _fail(f'Rows disagree on {field}.')
    headers = first.get('table_headers')
    if not isinstance(headers, list) or not headers or len(headers) > MAX_COLUMNS:
        _fail('Header list missing or too wide.')
    if [h.get('column') for h in headers] != list(range(len(headers))) or any(not h.get('text') for h in headers):
        _fail('Headers are not one non-empty label per column.')
    for p in rows:
        if p.get('table_headers') != headers:
            _fail('Rows disagree on headers.')
        if p.get('source_notes', []) != first.get('source_notes', []):
            _fail('Rows disagree on footnotes.')
        cells = p.get('table_cells')
        if (not isinstance(cells, list) or [c.get('column') for c in cells] != list(range(len(headers)))
                or any(c.get('row') != p['table_row'] for c in cells)):
            _fail(f'Row {p["table_row"]} does not have exactly one cell per header.')
        if any(not isinstance(c.get('text'), str) or len(c['text']) > MAX_CELL_CHARS for c in cells):
            _fail(f'Row {p["table_row"]} has a missing or oversized cell value.')
        if p.get('row_label') != cells[0]['text']:
            _fail(f'Row {p["table_row"]} label does not match its first cell.')
    emitted = check_completeness(first, count, audit, audit_problem)
    table = {
        'arxiv_id': first['arxiv_id'], 'paper_title': first.get('title'), 'table_id': first['table_id'],
        'caption': first.get('caption'), 'html_url': first.get('html_url'), 'pdf_url': first.get('pdf_url'),
        'document_region': first.get('document_region'),
        'source_sha256': first.get('source_sha256'), 'extractor_version': first.get('extractor_version'),
        'header_provenance': first.get('header_provenance'), 'header_review': first.get('header_review'),
        'header_verified': first.get('header_review') == 'verified',
        'header_rows': first.get('header_rows', 1),
        'headers': headers, 'source_notes': first.get('source_notes', []),
        'rows': [{'chunk_id': p['chunk_id'], 'table_row': p['table_row'], 'row_label': p['row_label'],
                  **({'row_group': p['row_group']} if p.get('row_group') else {}),
                  'cells': p['table_cells']} for p in rows],
        'row_count': count, 'complete': True, 'index_sha256': index_sha256,
        'extractor_rows_emitted': emitted, 'completeness_check': AUDIT_KIND,
        'completeness_basis': 'Row count equals the accepted-row count in the extractor audit for this source '
                              'hash and extractor version, and re-extraction reproduced every stored row.',
        'model_calls': 0,
    }
    size = len(json.dumps(table, ensure_ascii=False).encode('utf-8'))
    if size > MAX_RESPONSE_BYTES:
        raise TableUnavailable('table_too_large', f'The table response would be {size} bytes; the limit is {MAX_RESPONSE_BYTES}.', 422)
    return table

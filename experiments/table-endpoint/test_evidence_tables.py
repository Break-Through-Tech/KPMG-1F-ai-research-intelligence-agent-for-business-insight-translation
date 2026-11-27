"""Model-free tests for the experimental full-table endpoint.

Run:  python -I test_evidence_tables.py   (from this folder; reads the demo-100 bundle read-only)
"""
import copy
import http.client
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evidence_tables  # noqa: E402
from evidence_tables import TableIndex, TableUnavailable, assemble  # noqa: E402
import recorded_backend  # noqa: E402

EXPORT = Path(r'D:\KPMG-demo-corpus\main-727b0b3')
BUNDLE = EXPORT / 'data/processed/demo-bundles/demo-100'
RECORDED = Path(r'D:\KPMG-demo-corpus\fable-live-briefs.sqlite3')
CU_DPO_ROW = '2602.00931v2_table_080f58af664ee53b_4'
AUDIT_PATH = HERE / 'table-audit-demo-100.json'
INDEX = TableIndex(BUNDLE / 'parents.jsonl', AUDIT_PATH)


def bundle_rows(table_id, arxiv_id='2602.00931v2'):
    out = []
    with (BUNDLE / 'parents.jsonl').open(encoding='utf-8') as f:
        for line in f:
            p = json.loads(line)
            if p.get('arxiv_id') == arxiv_id and p.get('table_id') == table_id and p.get('representation') == 'linearized_table':
                out.append(p)
    return out


class TableIndexTests(unittest.TestCase):
    def test_complete_table_is_exact_copy_of_indexed_cells(self):
        table = INDEX.table(CU_DPO_ROW, INDEX.index_sha256)
        source = sorted(bundle_rows('S3.T2'), key=lambda p: p['table_row'])
        self.assertEqual(table['row_count'], 16)
        self.assertTrue(table['complete'])
        self.assertEqual([r['cells'] for r in table['rows']], [p['table_cells'] for p in source])
        self.assertEqual(table['headers'], source[0]['table_headers'])
        self.assertEqual(table['caption'], source[0]['caption'])
        self.assertFalse(table['header_verified'])
        self.assertEqual(table['header_review'], 'pending_human_verification')
        self.assertEqual(table['model_calls'], 0)

    def test_every_retrieved_row_of_recorded_answers_resolves_to_its_own_table(self):
        db = sqlite3.connect(f'file:{RECORDED}?mode=ro', uri=True)
        checked = 0
        for (env,) in db.execute('select envelope_json from brief_versions'):
            result = json.loads(env)['result']
            index = result['provenance']['index']['indexed_records_sha256']
            for p in result['evidence']:
                if p.get('representation') != 'linearized_table':
                    continue
                table = INDEX.table(p['chunk_id'], index)
                row = next(r for r in table['rows'] if r['chunk_id'] == p['chunk_id'])
                self.assertEqual(row['cells'], p['table_cells'])
                self.assertEqual(table['headers'], p['table_headers'])
                checked += 1
        self.assertGreaterEqual(checked, 7)

    def test_index_identity_is_enforced(self):
        with self.assertRaises(TableUnavailable) as caught:
            INDEX.table(CU_DPO_ROW, '0' * 64)
        self.assertEqual((caught.exception.code, caught.exception.status), ('index_mismatch', 409))

    def test_bad_and_unknown_ids(self):
        for bad in ['', '../etc', '2602.00931v2_c0000', CU_DPO_ROW + 'x', None, 'a' * 500]:
            with self.assertRaises(TableUnavailable) as caught:
                INDEX.table(bad, INDEX.index_sha256)
            self.assertEqual(caught.exception.status, 400, bad)
        with self.assertRaises(TableUnavailable) as caught:
            INDEX.table('2602.00931v2_table_0000000000000000_1', INDEX.index_sha256)
        self.assertEqual(caught.exception.status, 404)

    def check_rejected(self, rows, fragment):
        with self.assertRaises(TableUnavailable) as caught:
            assemble(rows, INDEX.index_sha256, INDEX.audit)
        self.assertEqual(caught.exception.status, 422)
        self.assertIn(fragment, caught.exception.reason)

    def test_partial_tables_are_refused_not_returned(self):
        rows = bundle_rows('S3.T2')
        self.check_rejected([r for r in rows if r['table_row'] != 7], 'numbered 1..N')
        self.check_rejected(rows + [copy.deepcopy(rows[0])], 'numbered 1..N')

    def test_inconsistent_tables_are_refused(self):
        rows = copy.deepcopy(bundle_rows('S3.T2'))
        rows[3]['caption'] = 'changed'
        self.check_rejected(rows, 'caption')
        rows = copy.deepcopy(bundle_rows('S3.T2'))
        rows[2]['table_headers'][2]['text'] = 'Accuracy'
        self.check_rejected(rows, 'headers')
        rows = copy.deepcopy(bundle_rows('S3.T2'))
        rows[5]['table_cells'].pop()
        self.check_rejected(rows, 'one cell per header')
        rows = copy.deepcopy(bundle_rows('S3.T2'))
        rows[1]['row_label'] = 'other'
        self.check_rejected(rows, 'label')

    def test_empty_cells_stay_empty(self):
        for key, rows in INDEX.tables.items():
            if any(c['text'] == '' for r in rows for c in r['table_cells']):
                try:
                    table = INDEX.table(rows[0]['chunk_id'], INDEX.index_sha256)
                except TableUnavailable:
                    continue
                empties = sum(c['text'] == '' for r in table['rows'] for c in r['cells'])
                self.assertEqual(empties, sum(c['text'] == '' for r in rows for c in r['table_cells']))
                return
        self.skipTest('no reconstructable table with empty cells')

    def test_whole_bundle_profile(self):
        ok = 0
        refused = {}
        for rows in INDEX.tables.values():
            try:
                table = INDEX.table(rows[0]['chunk_id'], INDEX.index_sha256)
                self.assertEqual(table['extractor_rows_emitted'], table['row_count'])
                ok += 1
            except TableUnavailable as error:
                self.assertEqual(error.status, 422)
                refused[error.code] = refused.get(error.code, 0) + 1
        print(f'\n  tables complete and verified: {ok}; refused: {refused}')
        self.assertGreater(ok, 0)


class CompletenessAuditTests(unittest.TestCase):
    """Audit finding H2: a table missing its final row passed every structural check."""

    def prefix(self):
        rows = sorted(copy.deepcopy(bundle_rows('S3.T2')), key=lambda p: p['table_row'])
        return rows[:-1]

    def assert_unverified(self, rows, audit, fragment, problem=None):
        with self.assertRaises(TableUnavailable) as caught:
            assemble(rows, INDEX.index_sha256, audit, problem)
        self.assertEqual((caught.exception.code, caught.exception.status), ('completeness_unverified', 422))
        self.assertIn(fragment, caught.exception.reason)

    def test_reproduction_prefix_passes_every_structural_check(self):
        # Rows 1..15 of a 16-row table are contiguous, consistent and well formed. Only an
        # independent count can catch it: with an audit that (wrongly) says 15, it would pass.
        key = '2602.00931v2#S3.T2'
        lying = {key: {**INDEX.audit[key], 'rows_emitted': 15}}
        self.assertEqual(assemble(self.prefix(), INDEX.index_sha256, lying)['row_count'], 15)

    def test_missing_final_row_is_refused(self):
        self.assert_unverified(self.prefix(), INDEX.audit, 'emitted 16 rows for this table but 15 are stored')

    def test_whole_table_still_passes_with_extractor_count(self):
        table = INDEX.table(CU_DPO_ROW, INDEX.index_sha256)
        self.assertEqual((table['row_count'], table['extractor_rows_emitted'], table['completeness_check']),
                         (16, 16, 'extractor_table_audit_v1'))

    def test_fails_closed_without_audit_or_with_foreign_audit(self):
        rows = bundle_rows('S3.T2')
        self.assert_unverified(rows, None, 'No extractor audit')
        no_audit = TableIndex(BUNDLE / 'parents.jsonl', None)
        with self.assertRaises(TableUnavailable) as caught:
            no_audit.table(CU_DPO_ROW, no_audit.index_sha256)
        self.assertEqual(caught.exception.code, 'completeness_unverified')
        with tempfile.TemporaryDirectory() as tmp:
            foreign = Path(tmp) / 'audit.json'
            data = json.loads(AUDIT_PATH.read_text(encoding='utf-8'))
            data['index_sha256'] = '0' * 64
            foreign.write_text(json.dumps(data), encoding='utf-8')
            other = TableIndex(BUNDLE / 'parents.jsonl', foreign)
            self.assertIn('different index', other.audit_problem)
            with self.assertRaises(TableUnavailable):
                other.table(CU_DPO_ROW, other.index_sha256)

    def test_audit_disagreements_are_refused(self):
        rows = bundle_rows('S3.T2')
        key = '2602.00931v2#S3.T2'
        base = INDEX.audit[key]
        for change, fragment in [({'source_sha256': 'f' * 64}, 'different source'),
                                 ({'extractor_version': 'other'}, 'different source'),
                                 ({'status': 'rejected'}, 'did not accept'),
                                 ({'rows_emitted': True}, 'emitted True rows'),
                                 ({'rows_identical_to_bundle': False}, 'reproduce the stored rows')]:
            self.assert_unverified(rows, {key: {**base, **change}}, fragment)
        self.assert_unverified(rows, {}, 'no record of this table')

    def test_response_size_ceiling(self):
        rows = bundle_rows('S3.T2')
        original = evidence_tables.MAX_RESPONSE_BYTES
        evidence_tables.MAX_RESPONSE_BYTES = 1000
        try:
            with self.assertRaises(TableUnavailable) as caught:
                assemble(rows, INDEX.index_sha256, INDEX.audit)
            self.assertEqual((caught.exception.code, caught.exception.status), ('table_too_large', 422))
        finally:
            evidence_tables.MAX_RESPONSE_BYTES = original


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        working = Path(cls.tmp.name) / 'briefs.sqlite3'
        working.write_bytes(RECORDED.read_bytes())
        handler = recorded_backend.make_handler(EXPORT, INDEX, working)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.tmp.cleanup()

    def get(self, path, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        conn.request('GET', path, headers={'Host': f'127.0.0.1:{self.port}', **(headers or {})})
        response = conn.getresponse()
        body = json.loads(response.read() or b'null')
        conn.close()
        return response.status, body

    def test_table_route(self):
        status, body = self.get(f'/api/evidence-table?chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}')
        self.assertEqual(status, 200)
        self.assertEqual(body['row_count'], 16)

    def test_route_rejects_extra_or_missing_params_and_cross_site(self):
        self.assertEqual(self.get(f'/api/evidence-table?chunk_id={CU_DPO_ROW}')[0], 400)
        self.assertEqual(self.get(f'/api/evidence-table?chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}&x=1')[0], 400)
        self.assertEqual(self.get(f'/api/evidence-table?chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}',
                                  {'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.get(f'/api/evidence-table?chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}',
                                  {'Host': 'evil.example'})[0], 403)

    def test_parser_errors_are_structured_400(self):
        ok = f'chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}'
        for query in ['chunk_id=%ff%fe&index=' + INDEX.index_sha256, ok + '&&', 'a&b&c&d&e&f', ok + '&chunk_id=x', '=&=']:
            status, body = self.get('/api/evidence-table?' + query)
            self.assertEqual(status, 400, query)
            self.assertEqual(body['code'], 'bad_request')

    def test_table_route_is_get_only(self):
        for method in ['POST', 'PUT', 'DELETE']:
            conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
            conn.request(method, f'/api/evidence-table?chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}',
                         body=b'{}', headers={'Host': f'127.0.0.1:{self.port}', 'Content-Type': 'application/json'})
            response = conn.getresponse()
            body = json.loads(response.read())
            conn.close()
            self.assertEqual((response.status, response.getheader('Allow'), body['code']), (405, 'GET', 'method_not_allowed'), method)

    def test_refusal_with_a_body_is_never_lost(self):
        # Verification blocker 4 (WinError 10053): the 405 used to be sent without reading the
        # request body; closing a socket with unread bytes makes Windows reset the connection and
        # the client can lose the response (62 of 300 in the diagnosis). The body is now read
        # first, so every refusal must arrive, for small and large bodies alike.
        lost = []
        for attempt, body in enumerate([b'{}'] * 200 + [b'x' * 60000] * 20):
            conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
            try:
                conn.request('POST', f'/api/evidence-table?chunk_id={CU_DPO_ROW}&index={INDEX.index_sha256}', body=body,
                             headers={'Host': f'127.0.0.1:{self.port}', 'Content-Type': 'application/json'})
                response = conn.getresponse()
                self.assertEqual(response.status, 405)
                response.read()
            except (ConnectionAbortedError, ConnectionResetError) as error:
                lost.append((attempt, type(error).__name__))
            finally:
                conn.close()
        self.assertEqual(lost, [])

    def test_shared_routes_unchanged(self):
        status, config = self.get('/api/config')
        self.assertEqual(status, 200)
        self.assertEqual((config['live'], config['library']), (False, True))
        status, briefs = self.get('/api/briefs?q=&archived=0&offset=0')
        self.assertEqual(status, 200)
        self.assertEqual(len(briefs['briefs']), 4)

    def test_original_recorded_database_untouched(self):
        before = RECORDED.stat().st_mtime_ns
        self.get('/api/briefs?q=&archived=0&offset=0')
        self.assertEqual(RECORDED.stat().st_mtime_ns, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)

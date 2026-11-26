"""Model-free tests for the chart-first additions (2026-11-17): chart preview, evidence
compaction, progress reporting and the experimental routes.

Run:  python -I -B test_chart_first.py   (same local QA inputs as test_evidence_tables.py:
the demo-100 bundle, the baseline export and table-audit-demo-100.json beside this file).

Retrieval is replayed from recorded B2 results (chunk IDs captured 2026-11-17 with
retrieval_check.py, 0 model calls). No model is loaded and no generation call is made: the
provider is replaced by in-process fakes.
"""
import http.client
import json
import sys
import tempfile
import threading
import types
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evidence_tables import TableIndex  # noqa: E402
import chart_preview  # noqa: E402
import evidence_compaction  # noqa: E402
from progress import Progress  # noqa: E402

EXPORT = Path(r'D:\KPMG-demo-corpus\main-727b0b3')
BUNDLE = EXPORT / 'data/processed/demo-bundles/demo-100'
RECORDED = Path(r'D:\KPMG-demo-corpus\fable-live-briefs.sqlite3')
AUDIT_PATH = HERE / 'table-audit-demo-100.json'
INDEX = TableIndex(BUNDLE / 'parents.jsonl', AUDIT_PATH)
sys.path.insert(0, str(EXPORT))

DEEPMATH_Q = ('Compare the accuracy of DeepSeek-R1, Qwen3, and Gemma-2 before and after CU-DPO training on the '
              'DeepMath benchmark. Show a grouped bar chart using Table 4, with the exact numerical values and source citations.')
DEEPMATH_IDS = ['2602.00931v2_table_8811e0196b0cbdb7_2', '2602.00931v2_table_8811e0196b0cbdb7_1',
                '2602.00931v2_table_8811e0196b0cbdb7_8', '2602.00931v2_table_8811e0196b0cbdb7_4',
                '2602.00931v2_table_8811e0196b0cbdb7_7', '2602.00931v2_table_8811e0196b0cbdb7_3',
                '2602.00931v2_table_e0d6f55c56cc4354_2', '2602.00931v2_table_e0d6f55c56cc4354_1']
SEVEN_Q = ("Compare the seven base models' performance before and after CU-DPO. Show a chart using the paper's "
           'original numerical results table, with citations for each value.')
SEVEN_IDS = ['2602.00931v2_table_b8e933772f6631bb_7', '2602.00931v2_table_8811e0196b0cbdb7_10',
             '2602.00931v2_table_080f58af664ee53b_2', '2602.00931v2_table_b8e933772f6631bb_10',
             '2602.00931v2_table_080f58af664ee53b_8', '2602.00931v2_table_080f58af664ee53b_10',
             '2602.00931v2_table_080f58af664ee53b_1', '2602.00931v2_table_b8e933772f6631bb_5']


def load_passages():
    wanted = set(DEEPMATH_IDS) | set(SEVEN_IDS)
    found = {}
    with (BUNDLE / 'parents.jsonl').open(encoding='utf-8') as handle:
        for line in handle:
            if '_table_' in line:
                passage = json.loads(line)
                if passage['chunk_id'] in wanted:
                    found[passage['chunk_id']] = passage
    return found


PASSAGES = load_passages()
RECORDED_RETRIEVAL = {DEEPMATH_Q: DEEPMATH_IDS, SEVEN_Q: SEVEN_IDS}


def replay_retrieve(query, top_k):
    return [json.loads(json.dumps(PASSAGES[i])) for i in RECORDED_RETRIEVAL[query][:top_k]]


class IntentTests(unittest.TestCase):
    def test_explicit_chart_requests_only(self):
        for query in [DEEPMATH_Q, SEVEN_Q, 'Plot accuracy by model', 'Can you visualize Table 2?', 'show a graph of results']:
            self.assertTrue(chart_preview.chart_intent(query), query)
        for query in ['How much did CU-DPO improve accuracy?', 'Explain the method', 'Which table reports DeepMath?']:
            self.assertFalse(chart_preview.chart_intent(query), query)
        self.assertEqual(chart_preview.requested_tables(DEEPMATH_Q), {'4'})
        self.assertEqual(chart_preview.requested_count(SEVEN_Q), 7)
        self.assertIsNone(chart_preview.requested_count(DEEPMATH_Q))


class PreviewTests(unittest.TestCase):
    def test_named_table_is_first_complete_and_exact(self):
        result = chart_preview.preview(DEEPMATH_Q, replay_retrieve(DEEPMATH_Q, 8), INDEX, INDEX.index_sha256)
        self.assertEqual(result['model_calls'], 0)
        first = result['tables'][0]
        self.assertEqual((first['table_id'], first['named_in_question'], first['status']), ('S4.T4.fig1', True, 'complete'))
        table = first['table']
        self.assertEqual((table['row_count'], table['extractor_rows_emitted'], table['completeness_check']),
                         (14, 14, 'extractor_table_audit_v1'))
        self.assertEqual(sorted(first['retrieved_rows']), [1, 2, 3, 4, 7, 8])
        # Values are the indexed cells, untouched.
        stored = sorted(INDEX.tables[('2602.00931v2', 'S4.T4.fig1')], key=lambda p: p['table_row'])
        self.assertEqual([r['cells'] for r in table['rows']], [p['table_cells'] for p in stored])
        # Evidence returned to the page is exactly the retrieved table rows (for its round-trip check).
        self.assertEqual({p['chunk_id'] for p in result['evidence']}, set(DEEPMATH_IDS))

    def test_stated_model_count_puts_the_seven_model_table_first(self):
        result = chart_preview.preview(SEVEN_Q, replay_retrieve(SEVEN_Q, 8), INDEX, INDEX.index_sha256)
        order = [(t['table_id'], t['matches_count']) for t in result['tables']]
        self.assertEqual(order[0], ('S4.T4.fig1', True), order)
        self.assertEqual({t['table_id'] for t in result['tables']}, {'S4.T4.fig1', 'S3.T2', 'A2.T11'})
        self.assertTrue(all(t['status'] == 'complete' for t in result['tables']))

    def test_unverified_tables_are_refused_not_offered(self):
        no_audit = TableIndex(BUNDLE / 'parents.jsonl', None)
        result = chart_preview.preview(DEEPMATH_Q, replay_retrieve(DEEPMATH_Q, 8), no_audit, no_audit.index_sha256)
        self.assertTrue(result['tables'])
        for entry in result['tables']:
            self.assertEqual((entry['status'], entry['code'], entry['table']), ('refused', 'completeness_unverified', None))

    def test_text_passages_and_table_cap(self):
        passages = replay_retrieve(SEVEN_Q, 8)
        passages.insert(0, {'chunk_id': 'x_c0000', 'text': 'prose', 'representation': None})
        result = chart_preview.preview(SEVEN_Q, passages, INDEX, INDEX.index_sha256, max_tables=1)
        self.assertEqual(len(result['tables']), 1)
        self.assertEqual(len(result['skipped_tables']), 2)
        self.assertNotIn('x_c0000', {p['chunk_id'] for p in result['evidence']})


class CompactionTests(unittest.TestCase):
    def capture_synthesis_prompt(self, passages, answer=None):
        from src.research_chat import synthesize
        seen = {}

        def fake(prompt, response_schema=None):
            seen['prompt'] = prompt
            if answer is None:
                raise RuntimeError('captured')
            return json.dumps(answer)
        fake.supports_response_schema = True
        wrapped = evidence_compaction.compacting(fake, on_compact=lambda stats: seen.update(stats=stats))
        try:
            result = synthesize(DEEPMATH_Q, passages, generate=wrapped)
        except RuntimeError:
            result = None
        return seen, result

    def test_synthesis_prompt_keeps_ids_and_exact_text_and_shrinks(self):
        passages = replay_retrieve(DEEPMATH_Q, 8)
        seen, _ = self.capture_synthesis_prompt(passages)
        stats = seen['stats']
        self.assertTrue(stats['compacted'])
        self.assertLess(stats['chars_after'], stats['chars_before'] * 0.45, stats)
        prompt = seen['prompt']
        start = prompt.find(evidence_compaction.MARKER)
        payload = json.loads(prompt[start:])
        self.assertEqual([p['chunk_id'] for p in payload['paper_passages']], [p['chunk_id'] for p in passages])
        self.assertEqual([p['text'] for p in payload['paper_passages']], [p['text'] for p in passages])
        self.assertEqual(payload['question'], DEEPMATH_Q)
        for passage in payload['paper_passages']:
            self.assertLessEqual(set(passage), set(evidence_compaction.KEEP))
        # The text still carries the caption with its unit, the column labels and the exact values.
        first = payload['paper_passages'][0]['text']
        for fragment in ['Pass@1, %', 'Base model: DeepSeek-R1 (8B)', 'Setting: + CU- DPO', 'DM: 69.8']:
            self.assertIn(fragment, first)

    def test_citations_still_validate_against_full_records(self):
        passages = replay_retrieve(DEEPMATH_Q, 8)
        row = next(p for p in passages if p['table_row'] == 2 and p['table_id'] == 'S4.T4.fig1')
        answer = {'status': 'ok', 'limitations': [], 'claims': [{
            'kind': 'finding', 'text': 'DeepSeek-R1 (8B) with CU-DPO reaches 69.8 on DM.',
            'support': [{'chunk_id': row['chunk_id'], 'quote': 'Setting: + CU- DPO; DM: 69.8'}]}]}
        _, result = self.capture_synthesis_prompt(passages, answer)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['claims'][0]['chunk_ids'], [row['chunk_id']])
        bad = json.loads(json.dumps(answer))
        bad['claims'][0]['support'][0]['quote'] = 'Setting: + CU- DPO; DM: 99.9'
        with self.assertRaises(ValueError):
            self.capture_synthesis_prompt(passages, bad)

    def test_quality_review_shape_and_unknown_prompts(self):
        passages = replay_retrieve(DEEPMATH_Q, 2)
        review = 'POLICY TEXT\n' + json.dumps({'question': 'q', 'draft': {'claims': []},
                                               'passages': [{k: v for k, v in p.items() if k != 'reader'} for p in passages]},
                                              ensure_ascii=False)
        compacted, stats = evidence_compaction.compact_prompt(review)
        self.assertTrue(stats['compacted'])
        self.assertTrue(compacted.startswith('POLICY TEXT\n{"question": "q", "draft": {"claims": []}'))
        for prompt in ['Business template with evidence in the middle: {"a": 1} and more text', 'plain', '{"question": broken']:
            self.assertEqual(evidence_compaction.compact_prompt(prompt), (prompt, {'compacted': False,
                             'chars_before': len(prompt), 'chars_after': len(prompt)}))


class ProgressTests(unittest.TestCase):
    def test_stages_timeout_error_and_budget(self):
        now = [100.0]
        progress = Progress(clock=lambda: now[0])
        self.assertEqual(progress.snapshot()['stage'], 'idle')
        progress.begin(); progress.stage('retrieval'); now[0] += 2.5
        progress.retrieval_done(2.5, 8)
        self.assertEqual(progress.snapshot()['stage'], 'validating')
        progress.call_started(1, 300, 4800, 22900); now[0] += 41
        snap = progress.snapshot({'cap': 9, 'used': 1})
        self.assertEqual((snap['stage'], snap['call']['number'], snap['call']['seconds'], snap['call']['timeout']), ('generation', 1, 41.0, 300))
        self.assertEqual((snap['call']['prompt_chars'], snap['call']['compacted_from'], snap['budget']['used']), (4800, 22900, 1))
        now[0] += 259
        progress.call_finished(1, 300.05, 'provider_error', {'type': 'TimeoutExpired', 'message': 'x'})
        progress.end(failed=True)
        snap = progress.snapshot()
        self.assertEqual((snap['stage'], snap['active'], snap['last_error']['kind']), ('failed', False, 'timeout'))
        self.assertIn('did not respond within 300 s (call 1)', snap['last_error']['message'])
        self.assertNotIn('prompt', json.dumps(snap['steps']))

    def test_capped_generator_reports_calls_and_keeps_its_safeguards(self):
        import capped_codex_ui
        events = []

        class PipelineError(Exception):
            pass

        def inner(prompt, response_schema=None):
            try:
                raise TimeoutError('TimeoutExpired stand-in')
            except TimeoutError as cause:
                raise PipelineError('provider failed') from cause
        fake_module = types.ModuleType('src.codex_generation')
        fake_module.create_codex_generate = lambda **kw: (inner, {'provider': 'fake'})
        saved = sys.modules.get('src.codex_generation')
        sys.modules['src.codex_generation'] = fake_module
        capped_codex_ui._state.update(calls=0, stopped=False)
        with tempfile.TemporaryDirectory() as tmp:
            try:
                capped_codex_ui.configure(2, Path(tmp) / 'calls.jsonl', observer=lambda e, i: events.append((e, i['number'])))
                generate, _ = capped_codex_ui.create()
                with self.assertRaises(PipelineError):
                    generate('p', response_schema={})
                with self.assertRaises(RuntimeError):   # stopped after a provider error: no second call
                    generate('p', response_schema={})
                capped_codex_ui.configure(2, Path(tmp) / 'calls.jsonl', observer=lambda e, i: 1 / 0)
                capped_codex_ui._state.update(calls=0, stopped=False)
                generate2, _ = capped_codex_ui.create()
                with self.assertRaises(PipelineError):  # a failing observer never changes the call
                    generate2('p', response_schema={})
            finally:
                capped_codex_ui.configure(0, Path(tmp) / 'calls.jsonl')
                capped_codex_ui._state.update(calls=0, stopped=False)
                if saved is not None:
                    sys.modules['src.codex_generation'] = saved
                else:
                    sys.modules.pop('src.codex_generation', None)
        self.assertEqual(events, [('call_started', 1), ('call_finished', 1)])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import recorded_backend
        cls.tmp = tempfile.TemporaryDirectory()
        working = Path(cls.tmp.name) / 'briefs.sqlite3'
        working.write_bytes(RECORDED.read_bytes())
        cls.progress = Progress()
        handler = recorded_backend.make_handler(EXPORT, INDEX, working, preview_retrieve=replay_retrieve,
                                                progress=cls.progress, budget=lambda: {'cap': 0, 'used': 0})
        disabled = recorded_backend.make_handler(EXPORT, INDEX, working)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.plain = ThreadingHTTPServer(('127.0.0.1', 0), disabled)
        for server in (cls.server, cls.plain):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        for server in (cls.server, cls.plain):
            server.shutdown(); server.server_close()
        cls.tmp.cleanup()

    def call(self, method, path, body=None, server=None, headers=None):
        port = (server or self.server).server_port
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=20)
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        conn.request(method, path, body=data, headers={'Host': f'127.0.0.1:{port}', 'Content-Type': 'application/json', **(headers or {})})
        response = conn.getresponse()
        payload = json.loads(response.read() or b'null')
        conn.close()
        return response.status, payload, response.getheader('Allow')

    def test_chart_preview_route(self):
        status, body, _ = self.call('POST', '/api/chart-preview', {'query': DEEPMATH_Q})
        self.assertEqual(status, 200)
        self.assertEqual((body['model_calls'], body['tables'][0]['table_id'], body['tables'][0]['status']), (0, 'S4.T4.fig1', 'complete'))
        self.assertIn('retrieval', body['timings_seconds'])

    def test_preview_rejects_bad_input_and_wrong_methods(self):
        for body in [b'', b'not json', {'query': ''}, {'query': 'x' * 2001}, {'q': 'x'}]:
            self.assertEqual(self.call('POST', '/api/chart-preview', body)[0], 400, body)
        self.assertEqual(self.call('GET', '/api/chart-preview')[:3:2], (405, 'POST'))
        self.assertEqual(self.call('POST', '/api/progress', {})[:3:2], (405, 'GET'))
        self.assertEqual(self.call('POST', '/api/chart-preview', {'query': DEEPMATH_Q}, headers={'Origin': 'http://evil.example'})[0], 403)

    def test_progress_route_and_config_flags(self):
        status, body, _ = self.call('GET', '/api/progress')
        self.assertEqual((status, body['stage'], body['budget']['cap'], body['model_calls']), (200, 'idle', 0, 0))
        status, config, _ = self.call('GET', '/api/config')
        self.assertEqual((config['chart_preview'], config['progress']), (True, True))
        status, config, _ = self.call('GET', '/api/config', server=self.plain)
        self.assertEqual((config['chart_preview'], config['progress']), (False, False))
        self.assertEqual(self.call('POST', '/api/chart-preview', {'query': 'x'}, server=self.plain)[0], 404)
        self.assertEqual(self.call('GET', '/api/progress', server=self.plain)[0], 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from budget import Ledger, LimitReached, MAX_OUTPUT
from run import application_generate


class LedgerTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'test.sqlite3'
        self.ledger = Ledger(self.path)

    def test_atomic_shared_cap_and_per_arm_cap(self):
        def reserve(arm):
            try:
                Ledger(self.path).reserve(arm, 'U1', 100)
            except LimitReached:
                return None
            return arm

        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(reserve, ['S2', 'R2'] * 24))
        self.assertEqual(accepted.count('S2'), 20)
        self.assertEqual(accepted.count('R2'), 20)
        with self.assertRaises(LimitReached):
            Ledger(self.path).reserve('S2', 'U2', 100)

    def test_input_limit_persists_even_with_no_receipt(self):
        first = self.ledger.reserve('S2', 'U1', 1_199_999)
        self.ledger.failure(first, 60, TimeoutError())
        with self.assertRaises(LimitReached):
            Ledger(self.path).reserve('R2', 'U2', 2)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT outcome FROM dispatch').fetchone(), ('TimeoutError',))

    def test_project_pacing_survives_restart_and_counts_unknown_usage(self):
        for index, (bound, burst) in enumerate(((100, 15), (100_000, 2))):
            now = [1000.0]
            waits = []
            def wait(seconds):
                waits.append(seconds)
                now[0] += seconds
            path = self.path.with_name(f'pacing-{index}.sqlite3')
            for _ in range(burst):
                Ledger(path, pace=True, clock=lambda: now[0], wait=wait).reserve('S2', 'U1', bound)
            self.assertEqual(waits, [])
            Ledger(path, pace=True, clock=lambda: now[0], wait=wait).reserve('R2', 'U1', bound)
            self.assertEqual(waits, [61.0])

    def test_confirmed_input_usage_reconciles_the_reservation(self):
        first = self.ledger.reserve('S2', 'U1', 1_199_999)
        self.ledger.record(first, {'prompt': 100, 'candidates': 20}, 1)
        Ledger(self.path).reserve('R2', 'U1', 1_199_900)

    def test_thinking_is_charged_and_a_breach_stops_future_calls(self):
        dispatch = self.ledger.reserve('S2', 'U1', 1000)
        with self.assertRaises(LimitReached):
            self.ledger.record(dispatch, {'prompt': 900, 'candidates': 3500, 'thoughts': 251}, 1)
        with self.assertRaises(LimitReached):
            Ledger(self.path).reserve('R2', 'U2', 100)

    def test_real_adapter_preserves_schema_timeout_and_meters_transient_retry(self):
        requests = []

        class TransientError(Exception):
            code = 503

        def send(**kwargs):
            requests.append(kwargs)
            if len(requests) == 1:
                raise TransientError()
            return SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')], text='{"ok":true}',
                usage_metadata=SimpleNamespace(prompt_token_count=8, candidates_token_count=4, thoughts_token_count=0))

        def client(**kwargs):
            self.assertEqual(kwargs['http_options'].timeout, 60000)
            self.assertEqual(kwargs['http_options'].retry_options.attempts, 1)
            return SimpleNamespace(models=SimpleNamespace(generate_content=send))

        generate, metadata = application_generate(self.ledger, lambda: ('S2', 'U1'), 'fake-test-key',
                                                   client_factory=client, sleep=lambda _: None)
        schema = {'type': 'object', 'properties': {'ok': {'type': 'boolean'}}, 'required': ['ok']}
        self.assertEqual(generate('test prompt', response_schema=schema), '{"ok":true}')
        self.assertEqual(metadata['model'], 'gemini-3.1-flash-lite')
        self.assertEqual(len(requests), 2)
        config = requests[-1]['config']
        self.assertEqual(config.max_output_tokens, MAX_OUTPUT)
        self.assertEqual(config.temperature, 0)
        self.assertEqual(config.response_json_schema, schema)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT outcome FROM dispatch ORDER BY id').fetchall(),
                             [('TransientError',), ('response',)])

    def test_real_sdk_client_survives_adapter_construction(self):
        import gc
        import json
        import httpx
        from google import genai

        requests = []
        sdk_client = genai.Client

        def respond(request):
            requests.append((request.url.path, json.loads(request.content)))
            return httpx.Response(200, json={
                'candidates': [{'content': {'parts': [{'text': '{"ok":true}'}], 'role': 'model'},
                                'finishReason': 'STOP'}],
                'usageMetadata': {'promptTokenCount': 8, 'candidatesTokenCount': 4},
            })

        def factory(**kwargs):
            kwargs['http_options'].client_args = {'transport': httpx.MockTransport(respond)}
            return sdk_client(**kwargs)

        generate, _ = application_generate(self.ledger, lambda: ('S2', 'U1'), 'fake-test-key',
                                             client_factory=factory)
        gc.collect()
        self.assertEqual(generate('Offline probe', response_schema={'type': 'object'}), '{"ok":true}')
        from unittest.mock import patch
        from server import MODEL, quota_generate
        from src.generation import create_generate
        from src.generation_config import GenerationConfig

        with patch.object(genai, 'Client', factory):
            production, _ = create_generate(GenerationConfig('gemini', MODEL, 'fake-test-key'))
        quota = SimpleNamespace(reserve=lambda _: None)
        self.assertEqual(quota_generate(production, quota)('Offline probe', response_schema={'type': 'object'}),
                         '{"ok":true}')
        self.assertEqual(len(requests), 2)
        evaluation_path, evaluation = requests[0]
        production_path, production_body = requests[1]
        self.assertEqual(evaluation_path, '/v1beta/models/gemini-3.1-flash-lite:generateContent')
        self.assertEqual(evaluation_path, production_path)
        self.assertEqual(evaluation['generationConfig'].pop('maxOutputTokens'), MAX_OUTPUT)
        self.assertEqual(evaluation, production_body)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM dispatch').fetchone(), (1,))

    def test_google_400_diagnostic_keeps_labels_and_discards_provider_text(self):
        from contextlib import redirect_stderr
        from io import StringIO
        from google.genai.errors import ClientError

        dispatch = self.ledger.reserve('S2', 'U1', 100)
        error = ClientError(400, {'error': {
            'status': 'INVALID_ARGUMENT', 'message': 'private-prompt',
            'details': [
                {'@type': 'type.googleapis.com/google.rpc.BadRequest', 'fieldViolations': [
                    {'field': 'generation_config.thinking_config.thinking_level',
                     'description': 'private-value'},
                    {'field': 'generationConfig.responseJsonSchema.properties.private-name'},
                    {'field': 'private-field'},
                ]},
                {'@type': 'type.googleapis.com/google.rpc.ErrorInfo',
                 'reason': 'API_KEY_INVALID', 'metadata': {'hidden': 'private-credential'}},
            ],
        }})
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.ledger.failure(dispatch, 0.3, error)
        expected = 'ClientError HTTP 400 API_KEY_INVALID response_json_schema thinking_level'
        self.assertEqual(stderr.getvalue().strip(), 'evaluation-provider-rejection ' + expected)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT outcome FROM dispatch').fetchone(), (expected,))

    def test_local_payload_screen_blocks_prompt_and_schema_before_sdk_dispatch(self):
        def send(**kwargs):
            self.fail('A flagged body must never reach the SDK.')

        generate, _ = application_generate(
            self.ledger, lambda: ('S2', 'U1'), 'fake-test-key',
            client_factory=lambda **_: SimpleNamespace(models=SimpleNamespace(generate_content=send)),
        )
        from src.generation import PipelineError

        schema = {'type': 'object', 'description': 'Contact person@example.org.'}
        for prompt, response_schema in [('Evidence person@example.org', None), ('Evidence', schema)]:
            with self.assertRaises(PipelineError):
                generate(prompt, response_schema=response_schema)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM dispatch').fetchone(), (0,))
        with self.assertRaisesRegex(SystemExit, 'Free-tier payload screen failed'):
            self.ledger.check_blocked()

    def test_missing_usage_fails_closed(self):
        dispatch = self.ledger.reserve('S2', 'U1', 100)
        with self.assertRaises(LimitReached):
            self.ledger.record(dispatch, {}, 1)
        with self.assertRaises(SystemExit):
            Ledger(self.path).check_blocked()


if __name__ == '__main__':
    unittest.main()

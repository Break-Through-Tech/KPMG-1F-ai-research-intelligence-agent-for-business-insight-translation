"""Local fake-provider endpoint checks; never contact a research engine/model."""
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import Mock

from src.brief_store import BriefStore
from src.business_demo import BusinessHandler
from src.research_demo import DemoHandler
from tests.test_downstream_business import CONTEXT, business, result_for


class BusinessHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BriefStore(Path(self.tmp.name) / 'briefs.sqlite3')
        self.saved = self.store.save({'mode': 'indexed', 'scenario': 'summary-only',
            'result': result_for(), 'error': None})
        self.generator = Mock(return_value=json.dumps(business()))
        self.handler = type('IsolatedBusinessHandler', (BusinessHandler,), {
            'library': self.store, 'business_generate': staticmethod(self.generator),
            'business_metadata': {'execution': 'injected_fixture'}, 'research': None})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), self.handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True); self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.tmp.cleanup()

    def payload(self):
        return {'brief_id': self.saved['library']['brief']['id'],
            'expected_version': self.saved['library']['version']['id'],
            'fingerprint': self.saved['result']['review_fingerprint'], 'context': CONTEXT}

    def request(self, path='/api/business', payload=None, headers=None, method='POST'):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request(method, path, body=json.dumps(payload or self.payload()) if method == 'POST' else None,
                     headers=headers or {'Content-Type': 'application/json'})
        response = conn.getresponse(); data = json.loads(response.read()); conn.close()
        return response.status, data

    def test_one_translation_saves_a_new_version_and_stale_retry_spends_no_call(self):
        original = self.saved['result']
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['result']['business_insight']['status'], 'ok')
        self.assertEqual(data['result']['summary'], original['summary'])
        self.assertEqual(data['library']['version']['number'], 2)
        self.assertEqual(self.request()[0], 409)
        self.assertEqual(self.generator.call_count, 1)

    def test_rejects_stale_fingerprint_context_and_client_supplied_evidence(self):
        for change in ({'fingerprint': 'stale'}, {'context': {}}, {'result': result_for()}):
            self.assertEqual(self.request(payload={**self.payload(), **change})[0], 400)
        self.generator.assert_not_called()

    def test_failure_keeps_research_in_new_snapshot(self):
        self.generator.side_effect = RuntimeError('SECRET')
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['error']['stage'], 'business')
        self.assertEqual(data['result']['summary'], self.saved['result']['summary'])
        self.assertNotIn('SECRET', json.dumps(data))

    def test_origin_and_capability_boundaries(self):
        self.assertEqual(self.request(headers={'Content-Type': 'application/json', 'Origin': 'https://external.invalid'})[0], 403)
        status, config = self.request('/api/config', method='GET')
        self.assertEqual(status, 200)
        self.assertTrue(config['business_translation'])
        self.assertIsNone(self.handler.research)
        self.assertFalse(hasattr(DemoHandler, 'business_generate'))
        self.generator.assert_not_called()

    def test_fixture_identity_survives_translation(self):
        self.saved = self.store.save({'mode': 'fixture', 'fixture_file': 'synthetic-source',
            'scenario': 'summary-only', 'result': result_for(), 'error': None})
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['mode'], 'fixture')
        self.assertEqual(data['fixture_file'], 'synthetic-source')


if __name__ == '__main__': unittest.main()

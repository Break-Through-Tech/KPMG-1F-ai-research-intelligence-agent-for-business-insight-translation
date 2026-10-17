"""Offline adapter and HTTP boundary checks; no model/storage dependencies."""
import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from src.research_contracts import validate_result
from src.research_demo import DemoHandler, FIXTURES, SCENARIOS, load_demo


class DemoAdapterTests(unittest.TestCase):
    def test_all_drafts_validate_without_mutating_canonical_fixtures(self):
        before = {path: path.read_bytes() for path in FIXTURES.glob('*.json')}
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                demo = load_demo({'query': 'A different question'}, scenario)
                self.assertEqual(demo['submitted_request']['query'], 'A different question')
                if demo['result']:
                    validate_result(demo['result'])
                    self.assertNotEqual(demo['result']['request']['query'], 'A different question')
                    self.assertFalse(demo['result']['approved'])
                else:
                    self.assertEqual(demo['error']['code'], 'provider_unavailable')
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_partial_keeps_summary_and_abstains_business(self):
        result = load_demo({'query': 'Q'}, 'partial')['result']
        self.assertEqual(result['summary']['status'], 'ok')
        self.assertEqual(result['business_insight']['status'], 'insufficient_evidence')
        self.assertEqual(result['business_insight']['implications'], [])

    def test_normal_is_exact_shared_fixture_and_preserves_locations(self):
        normal = json.loads((FIXTURES / 'normal-v1.json').read_text())
        result = load_demo({'query': 'Q'}, 'full')['result']
        self.assertEqual(result, normal)
        self.assertIsNone(result['evidence'][0]['page_number'])
        self.assertTrue(result['evidence'][1]['source_url'].endswith('#page=2'))
        result['evidence'].clear()
        self.assertEqual(load_demo({'query': 'Q'}, 'full')['result'], normal)

    def test_abstention_is_distinct_from_empty(self):
        for scenario, count in [('insufficient', 2), ('empty', 0)]:
            result = load_demo({'query': 'Q'}, scenario)['result']
            self.assertEqual(len(result['evidence']), count)
            self.assertEqual(result['summary']['claims'], [])

    def test_invalid_and_reviewed_fixtures_are_not_exposed(self):
        for request, scenario in [({'query': ' '}, 'full'), ({'query': 'Q'}, '../invalid-v1.json')]:
            with self.assertRaises(ValueError):
                load_demo(request, scenario)
        normal = json.loads((FIXTURES / 'normal-v1.json').read_text())
        normal['approved'] = True
        with patch('src.research_demo.json.loads', return_value=normal):
            with self.assertRaises(ValueError):
                load_demo({'query': 'Q'}, 'full')


class DemoHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), DemoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def call(self, method, path, body=None, headers=None):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_assets_and_unknown_paths(self):
        for path in ['/', '/app.js', '/styles.css']:
            status, headers, body = self.call('GET', path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertEqual(headers['Cache-Control'], 'no-store')
        for path in ['/../.env', '/tests/fixtures/research/invalid-v1.json', '/api/live']:
            self.assertEqual(self.call('GET', path)[0], 404)

    def test_api_validates_input_and_keeps_demo_error_separate(self):
        for scenario in SCENARIOS:
            status, _, body = self.call('POST', '/api/demo',
                                       json.dumps({'query': 'Q', 'scenario': scenario}),
                                       {'Content-Type': 'application/json'})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)['mode'], 'fixture')
        for payload in ['[]', '{', '{"query":" "}', '{"query":"Q","scenario":[]}']:
            self.assertEqual(self.call('POST', '/api/demo', payload,
                                      {'Content-Type': 'application/json'})[0], 400)
        self.assertEqual(self.call('POST', '/api/demo', '{}')[0], 415)


if __name__ == '__main__':
    unittest.main()

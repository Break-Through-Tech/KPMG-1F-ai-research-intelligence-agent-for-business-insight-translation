"""HTTP library integration: replay is offline; accepted answers survive failed saves."""
from copy import deepcopy
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from src.brief_store import BriefStore
from src.research_demo import DemoHandler, load_demo


class LibraryHttpTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = BriefStore(Path(self.folder.name) / 'library.sqlite3')
        self.handler = type('LibraryHandler', (DemoHandler,), {'library': self.store})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), self.handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def call(self, path, payload=None, headers=None):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request('GET' if payload is None else 'POST', path,
                body=None if payload is None else json.dumps(payload),
                headers={'Content-Type': 'application/json', **(headers or {})})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_autosave_list_open_review_revision_and_stale_conflicts(self):
        status, saved = self.call('/api/demo', {'query': 'Typed question'})
        self.assertEqual(status, 200)
        lib = saved['library']
        brief_id, version_id = lib['brief']['id'], lib['version']['id']
        self.assertFalse(lib['replayed'])
        self.assertEqual(self.call('/api/briefs')[1]['briefs'][0]['mode'], 'fixture')
        with patch.object(self.handler, 'research', staticmethod(lambda req: self.fail('Replay called research'))):
            reopened = self.call(f'/api/briefs/{brief_id}')[1]
            self.assertEqual(reopened['result'], saved['result'])
            self.assertTrue(reopened['library']['replayed'])
        status, reviewed = self.call(f'/api/briefs/{brief_id}/reviews', {
            'version_id': version_id, 'fingerprint': lib['version']['fingerprint'],
            'reviewer': 'Test reviewer', 'decision': 'revise', 'notes': 'Check limitations.'})
        self.assertEqual(status, 200)
        self.assertEqual(reviewed['library']['reviews'][0]['decision'], 'revise')
        payload = {'query': 'Revision', 'library_revision': {'brief_id': brief_id, 'expected_version': version_id}}
        status, revised = self.call('/api/demo', payload)
        self.assertEqual(status, 200)
        self.assertEqual(revised['library']['version']['number'], 2)
        self.assertEqual(revised['library']['reviews'], [])
        self.assertEqual(self.call('/api/demo', payload)[0], 409)
        self.assertEqual(self.call(f'/api/briefs/{brief_id}?version={version_id}')[1]['library']['reviews'][0]['decision'], 'revise')
        self.assertEqual(self.call(f'/api/briefs/{brief_id}/reviews', {
            'version_id': version_id, 'fingerprint': lib['version']['fingerprint'],
            'reviewer': 'Test reviewer', 'decision': 'approve'})[0], 409)

    def test_import_raw_result_and_envelope_archive_restore(self):
        result = load_demo({'query': 'Q'}, 'full')['result']
        status, saved = self.call('/api/briefs', {'result': result})
        self.assertEqual(status, 200)
        lib = saved['library']
        path = '/api/briefs/' + lib['brief']['id']
        expected = {'expected_version': lib['version']['id']}
        self.assertEqual(self.call(path, {**expected, 'title': 'Retained result'})[0], 200)
        self.assertEqual(self.call(path, {**expected, 'archived': True})[0], 200)
        self.assertEqual(self.call('/api/briefs')[1]['briefs'], [])
        self.assertEqual(len(self.call('/api/briefs?archived=1')[1]['briefs']), 1)
        self.assertEqual(self.call(path, {**expected, 'archived': False})[0], 200)
        self.assertEqual(self.call('/api/briefs', {'envelope': saved})[0], 200)

    def test_failed_save_keeps_accepted_live_answer_and_does_not_retry_model(self):
        calls = []
        response = load_demo({'query': 'Q'}, 'full')
        response['mode'] = 'live-synthesis'
        def research(request):
            calls.append(request)
            return deepcopy(response)
        with patch.object(self.handler, 'research', staticmethod(research)), patch.object(
                self.store, 'save', side_effect=sqlite3.OperationalError('injected')):
            status, answer = self.call('/api/research', {'query': 'Q'})
        self.assertEqual(status, 200)
        self.assertEqual(answer['result'], response['result'])
        self.assertIn('not saved', answer['library_error'])
        self.assertNotIn('library', answer)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.store.list(), [])

    def test_revision_target_changed_during_live_execution_retains_answer(self):
        first = self.call('/api/demo', {'query': 'Q'})[1]
        lib = first['library']
        target = {'brief_id': lib['brief']['id'], 'expected_version': lib['version']['id']}
        def research(request):
            # Another writer advances the head while this model call is running.
            self.store.save(first, **target)
            response = load_demo({'query': 'Q'}, 'full')
            response['mode'] = 'live-synthesis'
            return response
        with patch.object(self.handler, 'research', staticmethod(research)):
            status, answer = self.call('/api/research', {'query': 'Q', 'library_revision': target})
        self.assertEqual(status, 200)
        self.assertIn('library_error', answer)
        self.assertNotIn('library', answer)
        self.assertEqual(answer['result'], first['result'])
        self.assertEqual(len(self.store.load(target['brief_id'])['library']['versions']), 2)

    def test_boundary_validation_precedes_any_store_access(self):
        with patch.object(self.store, 'list', side_effect=AssertionError('Forbidden read')):
            self.assertEqual(self.call('/api/briefs', headers={'Origin': 'https://attacker.example'})[0], 403)
        for path, payload in [('/api/briefs', {'result': {'approved': True}}),
                              ('/api/briefs', {'envelope': []}),
                              ('/api/demo', {'query': 'Q', 'library_revision': []})]:
            self.assertEqual(self.call(path, payload)[0], 400)
        self.assertEqual(self.call('/api/briefs?offset=-1')[0], 400)
        self.assertEqual(self.call('/api/briefs/unknown')[0], 404)
        self.assertEqual(self.call('/api/briefs/unknown/extra')[0], 404)

    def test_no_result_does_not_create_a_brief(self):
        self.assertEqual(self.call('/api/demo', {'query': 'Q', 'scenario': 'provider-error'})[0], 200)
        self.assertEqual(self.store.list(), [])

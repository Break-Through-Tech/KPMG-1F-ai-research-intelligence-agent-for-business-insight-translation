"""Model-free tests for the ui-consult development host (serve.py), audit fixes of 2026-11-17.

Run:  python -I ui-consult/tests/test_serve.py   (standard library only; starts two loopback servers)

Covers: the static-asset allowlist (design notes, fixtures and Python never served unless
tests are requested), the method-aware proxy (the table route is GET-only and refused
methods never reach the backend), and the bounded proxy read.
"""
import http.client
import importlib.util
import json
import sys
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('consult_serve', HERE.parent / 'serve.py')
serve = importlib.util.module_from_spec(spec)
sys.modules['consult_serve'] = serve
spec.loader.exec_module(serve)


class FakeBackend(BaseHTTPRequestHandler):
    """Stands in for the research backend; records every request it receives."""
    seen = []
    big = 0

    def log_message(self, *args):
        pass

    def reply(self, body, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        FakeBackend.seen.append(('GET', self.path))
        if self.path.startswith('/api/evidence-table') and FakeBackend.big:
            return self.reply(b'"' + b'x' * FakeBackend.big + b'"')
        self.reply(json.dumps({'ok': True, 'path': self.path}).encode())

    committed = []

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        self.rfile.read(length)
        FakeBackend.seen.append(('POST', self.path))
        if '/5104dead/' in self.path:
            # Late commit: the write is stored only after the proxy has given up waiting.
            time.sleep(1.2)
            FakeBackend.committed.append(self.path)
        self.reply(b'{"ok": true}')


def start(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class ServeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = start(ThreadingHTTPServer(('127.0.0.1', 0), FakeBackend))
        handler = type('H', (serve.Handler,), {'backend': ('127.0.0.1', cls.backend.server_port), 'serve_tests': False,
                                               'api_timeout': 0.4})
        cls.host = start(serve.Server(('127.0.0.1', 0), handler))
        # A loopback port with nothing listening: the backend connection can never open.
        probe = socket.socket(); probe.bind(('127.0.0.1', 0)); dead_port = probe.getsockname()[1]; probe.close()
        dead = type('D', (serve.Handler,), {'backend': ('127.0.0.1', dead_port), 'serve_tests': False})
        cls.dead_host = start(serve.Server(('127.0.0.1', 0), dead))
        tests_handler = type('T', (serve.Handler,), {'backend': None, 'serve_tests': True})
        cls.tests_host = start(serve.Server(('127.0.0.1', 0), tests_handler))

    @classmethod
    def tearDownClass(cls):
        for server in (cls.backend, cls.host, cls.tests_host, cls.dead_host):
            server.shutdown(); server.server_close()

    def request(self, method, path, server=None, body=None):
        server = server or self.host
        port = server.server_port
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        headers = {'Host': f'127.0.0.1:{port}'}
        if body is not None:
            headers.update({'Content-Type': 'application/json', 'Content-Length': str(len(body))})
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, data

    def test_runtime_assets_are_served(self):
        for path in ['/', '/app.js', '/evidence.js', '/async-guards.js', '/consult.css', '/math.js',
                     '/source-reader.js', '/vendor/katex/katex.min.css', '/vendor/katex/fonts/KaTeX_AMS-Regular.woff2']:
            self.assertEqual(self.request('GET', path)[0], 200, path)

    def test_design_notes_fixtures_and_code_are_not_served(self):
        for path in ['/design/UI-QA-REPORT.md', '/design/CODEX-UI-HANDOFF.md', '/tests/fixtures/recorded-cu-dpo.json',
                     '/tests/evidence.test.html', '/serve.py', '/tests/test_serve.py', '/vendor/katex/LICENSE',
                     '/../ui-next/index.html', '/%2e%2e/README.md', '/brief-library.js', '/styles.css']:
            self.assertEqual(self.request('GET', path)[0], 404, path)

    def test_tests_are_served_only_on_request(self):
        self.assertEqual(self.request('GET', '/tests/evidence.test.html', self.tests_host)[0], 200)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = 'tests/fixtures/portable-example.json'
            fixture = root / path
            fixture.parent.mkdir(parents=True)
            fixture.write_bytes(b'{"fixture": true}')
            with patch.object(serve, 'ROOTS', (*serve.ROOTS, root)):
                self.assertEqual(self.request('GET', '/' + path)[0], 404)
                self.assertEqual(self.request('GET', '/' + path, self.tests_host), (200, b'{"fixture": true}'))
        self.assertEqual(self.request('GET', '/design/UI-QA-REPORT.md', self.tests_host)[0], 404)

    def test_table_route_is_get_only_and_refusals_never_reach_the_backend(self):
        FakeBackend.seen.clear()
        self.assertEqual(self.request('GET', '/api/evidence-table?chunk_id=a&index=b')[0], 200)
        for method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            status, body = self.request(method, '/api/evidence-table?chunk_id=a&index=b', body=b'{}')
            self.assertEqual(status, 405, method)
            self.assertEqual(json.loads(body)['code'], 'method_not_allowed')
        self.assertEqual(self.request('GET', '/api/research')[0], 405)
        self.assertEqual(self.request('POST', '/api/config', body=b'{}')[0], 405)
        self.assertEqual(self.request('GET', '/api/briefs/abc/reviews')[0], 405)
        self.assertEqual(self.request('POST', '/api/briefs/abc/reviews', body=b'{}')[0], 200)
        self.assertEqual(FakeBackend.seen, [('GET', '/api/evidence-table?chunk_id=a&index=b'),
                                            ('POST', '/api/briefs/abc/reviews')])

    def test_proxy_read_is_bounded(self):
        FakeBackend.big = serve.MAX_RESPONSE['/api/evidence-table'] + 10
        try:
            status, body = self.request('GET', '/api/evidence-table?chunk_id=a&index=b')
        finally:
            FakeBackend.big = 0
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)['code'], 'backend_response_too_large')

    def test_proxy_timeout_after_forwarding_a_write_is_unknown_not_rejected(self):
        # Verification blocker 1: a 504 after the write was forwarded must not read as a rejection.
        FakeBackend.committed.clear()
        status, body = self.request('POST', '/api/briefs/5104dead/reviews', body=b'{}')
        self.assertEqual(status, 504)
        self.assertEqual(json.loads(body)['write_outcome'], 'unknown')
        self.assertEqual(FakeBackend.committed, [], 'not stored yet when the proxy answered')
        time.sleep(1.5)
        self.assertEqual(FakeBackend.committed, ['/api/briefs/5104dead/reviews'], 'the write committed later')

    def test_write_that_never_reached_the_backend_is_not_sent(self):
        status, body = self.request('POST', '/api/briefs/abc/reviews', self.dead_host, body=b'{}')
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body)['write_outcome'], 'not_sent')

    def test_refusals_read_the_body_first(self):
        # Blocker 4 applies here too: replies sent before reading a body were lost on Windows,
        # and on a kept-alive connection the unread bytes became the next "request".
        lost = 0
        for _ in range(150):
            try:
                status, _ = self.request('POST', '/api/evidence-table?chunk_id=a&index=b', body=b'{}')
                self.assertEqual(status, 405)
            except (ConnectionAbortedError, ConnectionResetError):
                lost += 1
        self.assertEqual(lost, 0)
        port = self.host.server_port
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        headers = {'Host': f'127.0.0.1:{port}', 'Content-Type': 'application/json'}
        conn.request('POST', '/api/evidence-table?chunk_id=a&index=b', body=b'{"x": 1}', headers=headers)
        first = conn.getresponse(); first.read()
        conn.request('GET', '/api/config', headers={'Host': f'127.0.0.1:{port}'})
        second = conn.getresponse(); second.read()
        conn.close()
        self.assertEqual((first.status, second.status), (405, 200), 'same connection still parses the next request')


if __name__ == '__main__':
    unittest.main(verbosity=2)

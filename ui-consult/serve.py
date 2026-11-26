"""Development host for the consultant research workspace (ui-consult, experimental redesign).

Serves ui-consult/ at the site root and falls back to the existing ui/ assets, with
the same Content-Security-Policy as src/research_demo.py. No research code is
imported here.

Modes are decided by the backend you connect, never by a silent fallback:

    python ui-consult/serve.py 8821 --backend http://127.0.0.1:8787   # live or recorded backend
    python ui-consult/serve.py                                        # no backend: explicit "not connected"

Mock data (invented, for UI-state testing only) runs only when the page is opened
with ?mock=1, and the page then says so on every screen.

With --backend, /api/* is forwarded to that already-running backend on this machine,
so the page talks to it same-origin. The page shows which kind of backend it is
(live research, recorded replay) from /api/config.

The optional read-only GET /api/evidence-table route is forwarded too; a backend
without it answers 404 and the page keeps partial tables labelled as partial.

The proxy only accepts requests from this page's own loopback origin, only
forwards the known research and saved-brief endpoints with the methods each one
accepts (the table route is GET-only), only to a loopback backend, and reads at most
a bounded number of bytes back. It never starts a backend and holds no credentials.

Static files come from an explicit allowlist of runtime assets. Design notes, Python
files and recorded test fixtures are never served; the in-browser tests and their
fixtures are served only when started with --serve-tests (audit, 2026-11-17).
"""
import argparse
import http.client
import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
ROOTS = (HERE, HERE.parent / 'ui')
CSP = ("default-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; script-src 'self'; "
       "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
       "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
TYPES = {'.png': 'image/png', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
         '.html': 'text/html; charset=utf-8', '.woff2': 'font/woff2', '.json': 'application/json'}
# Each forwarded route with the methods it accepts. Anything else is 404 (unknown route) or
# 405 (known route, wrong method) and never reaches the backend.
ROUTES = (
    (re.compile(r'/api/(?:config|saved-result)'), {'GET'}),
    (re.compile(r'/api/(?:research|demo)'), {'POST'}),
    (re.compile(r'/api/evidence-table'), {'GET'}),
    # Experimental, model-free chart-first routes (offered only by the isolated backend).
    (re.compile(r'/api/progress'), {'GET'}),
    (re.compile(r'/api/chart-preview'), {'POST'}),
    # Experimental multi-agent research (offered only by a live backend started with --agentic).
    (re.compile(r'/api/agentic-research'), {'POST'}),
    (re.compile(r'/api/briefs(?:/[0-9a-f]{1,64})?'), {'GET', 'POST'}),
    (re.compile(r'/api/briefs/[0-9a-f]{1,64}/reviews'), {'POST'}),
)
# Largest backend response the proxy will hold in memory. The table endpoint caps itself at
# 1 MB; saved briefs and research envelopes stay well under 32 MB.
MAX_RESPONSE = {'/api/evidence-table': 2_000_000, '/api/progress': 64_000,
                '/api/chart-preview': 4_000_000}  # up to 3 verified tables plus their retrieved rows
MAX_RESPONSE_DEFAULT = 32_000_000
# Runtime assets only. Tests are added by --serve-tests.
STATIC = {'kpmg-logo-white.png', 'index.html', 'app.js', 'evidence.js', 'chart-select.js', 'async-guards.js', 'chart-svg.js', 'consult.css', 'prefs.js', 'mock-api.js',
          'research-speech.js', 'read-aloud.mjs', 'read-aloud.css', 'answer-export.js', 'math.js', 'source-reader.js'}
STATIC_PATTERN = re.compile(r'vendor/katex/(?:katex\.min\.(?:js|css)|fonts/[A-Za-z0-9_-]+\.(?:woff2|woff|ttf))|fonts/[a-z0-9-]+\.woff2')
TEST_STATIC = re.compile(r'tests/(?:evidence\.test\.(?:html|js)|chart-gallery\.(?:html|js)|run-tests\.js|tests\.css|fixtures/[a-z0-9-]+\.json)')
# Modules the page loads unmodified from the Research Desk UI. In live mode they come
# from the backend itself so they always match the API version being served.
SHARED = re.compile(r'/(?:research-speech\.js|read-aloud\.mjs|read-aloud\.css|answer-export\.js|math\.js|'
                    r'source-reader\.js|vendor/katex/[A-Za-z0-9_./-]+\.(?:js|css|woff2))')
MAX_BODY = 8_500_000  # Snapshot imports are capped at 8 MB by the page.


def route_methods(path):
    for pattern, methods in ROUTES:
        if pattern.fullmatch(path):
            return methods
    return None


def static_allowed(name, serve_tests=False):
    return name in STATIC or bool(STATIC_PATTERN.fullmatch(name)) or (serve_tests and bool(TEST_STATIC.fullmatch(name)))


class ResponseTooLarge(Exception):
    pass
RESEARCH_TIMEOUT = 1600  # The page's own research timeout is 1560 s.
# Multi-agent worst case: 6 model calls of up to 300 s each plus retrieval. The page waits 1860 s.
AGENTIC_TIMEOUT = 1900


class Handler(BaseHTTPRequestHandler):
    backend = None  # (host, port) when live mode is enabled
    serve_tests = False
    api_timeout = 30  # seconds for saved-work and table requests (tests shorten it)
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        """Do not log user queries or request payloads."""

    def send(self, status, body, kind='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', CSP)
        self.end_headers()
        self.wfile.write(body)

    def same_origin(self):
        hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        return (self.headers.get('Host') in hosts
                and self.headers.get('Origin') in {None, *(f'http://{host}' for host in hosts)}
                and self.headers.get('Sec-Fetch-Site') not in {'cross-site', 'same-site'})

    def upstream(self, method, target, body=None, timeout=30, limit=MAX_RESPONSE_DEFAULT, delivery=None):
        """One request to the configured loopback backend, presented as its own origin."""
        host, port = self.backend
        origin = f'{host}:{port}'
        headers = {'Host': origin, 'Accept': 'application/json'}
        if body is not None:
            headers.update({'Content-Type': 'application/json', 'Content-Length': str(len(body)),
                            'Origin': f'http://{origin}', 'Sec-Fetch-Site': 'same-origin'})
        connection = http.client.HTTPConnection(host, port, timeout=timeout)
        try:
            connection.connect()
            # From here on some of the request may reach the backend: a later failure leaves a
            # write's outcome unknown (only a failed connect proves nothing was sent).
            if delivery is not None:
                delivery['sent'] = True
            connection.request(method, target, body=body, headers=headers)
            response = connection.getresponse()
            declared = response.getheader('Content-Length')
            if declared and declared.isdigit() and int(declared) > limit:
                raise ResponseTooLarge()
            payload = response.read(limit + 1)  # never more than the cap in memory
            if len(payload) > limit:
                raise ResponseTooLarge()
            return response.status, payload, response.getheader('Content-Type') or 'application/json'
        finally:
            connection.close()

    def read_body(self):
        """Read the declared request body before any reply. Returns (bytes | None, error status | None).

        Replying while request bytes are still unread and then closing makes Windows reset the
        connection, which can discard the reply (WinError 10053); on a kept-alive connection the
        leftover bytes would also be parsed as the next request. A body too large to read is
        refused with the connection closed."""
        raw = self.headers.get('Content-Length')
        if raw is None:
            return b'', None
        try:
            length = int(raw)
        except ValueError:
            self.close_connection = True
            return None, 400
        if not 0 <= length <= MAX_BODY:
            self.close_connection = True
            return None, 413
        return self.rfile.read(length), None

    def proxy(self, method):
        parts = urlsplit(self.path)
        body = None
        if method != 'GET':
            body, problem = self.read_body()
            if problem == 400:
                return self.send(400, {'error': 'Content-Length must be a number.'})
            if problem == 413:
                return self.send(413, {'error': 'Request is too large.'})
        if not self.same_origin():
            return self.send(403, {'error': 'Use the local research page.'})
        if self.backend is None:
            return self.send(503, {'code': 'no_backend', 'write_outcome': 'not_sent', 'error': 'No research backend is connected to this page. Start one, then restart serve.py with --backend. No illustrative answers are served.'})
        methods = route_methods(parts.path)
        if methods is None:
            return self.send(404, {'error': 'Not found.'})
        if method not in methods:
            return self.send(405, {'code': 'method_not_allowed', 'error': f'{parts.path} accepts {", ".join(sorted(methods))} only.'})
        if method == 'POST':
            if (self.headers.get('Content-Type') or '').split(';')[0].strip().lower() != 'application/json':
                return self.send(415, {'error': 'Use application/json.'})
            if self.headers.get('Content-Length') is None:
                return self.send(411, {'error': 'Content-Length is required.'})
        target = parts.path + (f'?{parts.query}' if parts.query else '')
        delivery = {'sent': False}
        try:
            status, payload, kind = self.upstream(
                method, target, body if method == 'POST' else None,
                AGENTIC_TIMEOUT if parts.path == '/api/agentic-research'
                else RESEARCH_TIMEOUT if parts.path in {'/api/research', '/api/demo'} else self.api_timeout,
                MAX_RESPONSE.get(parts.path, MAX_RESPONSE_DEFAULT), delivery)
        except ResponseTooLarge:
            return self.send(502, {'code': 'backend_response_too_large', 'write_outcome': 'unknown' if method == 'POST' else None,
                                   'error': 'The backend response exceeded the size this page accepts. Nothing was shown.'})
        except (TimeoutError, OSError) as error:
            # Once a write has been handed to the backend, losing its answer says nothing about
            # whether it was stored: report the outcome as unknown, never as a rejection.
            outcome = None if method != 'POST' else ('unknown' if delivery['sent'] else 'not_sent')
            if isinstance(error, TimeoutError):
                return self.send(504, {'code': 'backend_timeout', 'write_outcome': outcome,
                                       'error': 'The research backend did not answer in time.' + (' The change may still have been saved.' if outcome == 'unknown' else ' Your question is unchanged; retry when ready.')})
            host, port = self.backend
            return self.send(503, {'code': 'backend_unreachable', 'write_outcome': outcome,
                                   'error': f'The research backend at {host}:{port} is not running or not ready.' + (' The connection dropped after the change was sent, so it may have been saved.' if outcome == 'unknown' else ' Start it, wait until it is ready, then retry. Your question is unchanged.')})
        self.send(status, payload, kind)

    def do_POST(self):
        if urlsplit(self.path).path.startswith('/api/'):
            return self.proxy('POST')
        self.send(404, {'error': 'Not found.'})

    def _refuse_method(self):
        if urlsplit(self.path).path.startswith('/api/'):
            return self.proxy(self.command)  # same-origin, route and method checks; never forwarded
        self.send(405, {'code': 'method_not_allowed', 'error': 'Static files accept GET only.'})

    do_PUT = do_DELETE = do_PATCH = _refuse_method

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path.startswith('/api/'):
            return self.proxy('GET')
        if self.backend is not None and SHARED.fullmatch(path) and '..' not in path:
            try:
                status, payload, kind = self.upstream('GET', path)
                if status == 200:
                    return self.send(200, payload, kind)
            except OSError:
                pass  # Fall back to the local copy so the page still loads.
        name = 'index.html' if path == '/' else path.lstrip('/')
        if '..' in name or '\\' in name or not static_allowed(name, self.serve_tests):
            return self.send(404, {'error': 'Not found.'})
        for root in ROOTS:
            target = (root / name).resolve()
            if root in target.parents and target.is_file() and target.suffix != '.py':
                kind = TYPES.get(target.suffix) or mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
                return self.send(200, target.read_bytes(), kind)
        self.send(404, {'error': 'Not found.'})


class Server(ThreadingHTTPServer):
    # On Windows, address reuse would let this bind a port another local server already owns.
    allow_reuse_address = False
    daemon_threads = True


def loopback_backend(value):
    parts = urlsplit(value)
    if parts.scheme != 'http' or parts.hostname not in {'127.0.0.1', 'localhost'} or not parts.port \
            or parts.path not in {'', '/'} or parts.query or parts.username:
        raise argparse.ArgumentTypeError('Use a loopback origin such as http://127.0.0.1:8801')
    return '127.0.0.1', parts.port


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('port', nargs='?', type=int, default=int(os.environ.get('PORT') or 8820))
    parser.add_argument('--serve-tests', action='store_true',
                        help='Also serve /tests/ (in-browser tests and their recorded fixtures). Off by default.')
    parser.add_argument('--backend', type=loopback_backend, default=None,
                        help='Loopback origin of a running Research Desk backend, e.g. http://127.0.0.1:8801')
    args = parser.parse_args()
    if os.environ.get('RESEARCH_BACKEND') and args.backend is None:
        args.backend = loopback_backend(os.environ['RESEARCH_BACKEND'])
    if args.backend and args.backend[1] == args.port:
        sys.exit('The backend and this host cannot share a port.')
    Handler.backend = args.backend
    Handler.serve_tests = args.serve_tests
    try:
        server = Server(('127.0.0.1', args.port), Handler)
    except OSError:
        sys.exit(f'Port {args.port} is already in use. Run: python ui-consult/serve.py <another port>')
    if args.backend:
        print(f'Research workspace: http://127.0.0.1:{args.port}/  ->  backend http://{args.backend[0]}:{args.backend[1]}', flush=True)
    else:
        print(f'Research workspace (not connected): http://127.0.0.1:{args.port}/  (mock UI states: ?mock=1)', flush=True)
    server.serve_forever()

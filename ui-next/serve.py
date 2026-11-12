"""Development host for the redesigned research workspace.

Serves ui-next/ at the site root and falls back to the existing ui/ assets, with
the same Content-Security-Policy as src/research_demo.py. No research code is
imported here.

Mock mode (default): /api/* is answered in the browser by mock-api.js.

    python ui-next/serve.py                       # http://127.0.0.1:8814/

Live mode (opt-in): forward /api/* to an already-running Research Desk backend
on this machine, so the page talks to it same-origin. Open the page with ?live=1.

    python ui-next/serve.py --backend http://127.0.0.1:8801
    # then http://127.0.0.1:8814/?live=1

The proxy only accepts requests from this page's own loopback origin, only
forwards the known research and saved-brief endpoints, and only to a loopback
backend. It never starts a backend and holds no credentials.
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
TYPES = {'.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
         '.html': 'text/html; charset=utf-8', '.woff2': 'font/woff2', '.json': 'application/json'}
API = re.compile(r'/api/(?:config|saved-result|research|demo|briefs(?:/[0-9a-f]{1,64})?(?:/reviews)?)')
# Modules the page loads unmodified from the Research Desk UI. In live mode they come
# from the backend itself so they always match the API version being served.
SHARED = re.compile(r'/(?:research-speech\.js|read-aloud\.mjs|read-aloud\.css|answer-export\.js|math\.js|'
                    r'source-reader\.js|vendor/katex/[A-Za-z0-9_./-]+\.(?:js|css|woff2))')
MAX_BODY = 8_500_000  # Snapshot imports are capped at 8 MB by the page.
RESEARCH_TIMEOUT = 1600  # The page's own research timeout is 1560 s.


class Handler(BaseHTTPRequestHandler):
    backend = None  # (host, port) when live mode is enabled
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

    def upstream(self, method, target, body=None, timeout=30):
        """One request to the configured loopback backend, presented as its own origin."""
        host, port = self.backend
        origin = f'{host}:{port}'
        headers = {'Host': origin, 'Accept': 'application/json'}
        if body is not None:
            headers.update({'Content-Type': 'application/json', 'Content-Length': str(len(body)),
                            'Origin': f'http://{origin}', 'Sec-Fetch-Site': 'same-origin'})
        connection = http.client.HTTPConnection(host, port, timeout=timeout)
        try:
            connection.request(method, target, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, response.read(), response.getheader('Content-Type') or 'application/json'
        finally:
            connection.close()

    def proxy(self, method):
        parts = urlsplit(self.path)
        if not self.same_origin():
            return self.send(403, {'error': 'Use the local research page.'})
        if self.backend is None:
            return self.send(404, {'error': 'Live mode is off. Restart serve.py with --backend to reach a research backend.'})
        if not API.fullmatch(parts.path):
            return self.send(404, {'error': 'Not found.'})
        body = None
        if method == 'POST':
            if (self.headers.get('Content-Type') or '').split(';')[0].strip().lower() != 'application/json':
                return self.send(415, {'error': 'Use application/json.'})
            try:
                length = int(self.headers.get('Content-Length') or '')
            except ValueError:
                return self.send(400, {'error': 'Content-Length is required.'})
            if not 0 <= length <= MAX_BODY:
                return self.send(413, {'error': 'Request is too large.'})
            body = self.rfile.read(length)
        target = parts.path + (f'?{parts.query}' if parts.query else '')
        try:
            status, payload, kind = self.upstream(
                method, target, body, RESEARCH_TIMEOUT if parts.path in {'/api/research', '/api/demo'} else 30)
        except TimeoutError:
            return self.send(504, {'code': 'backend_timeout', 'error': 'The research backend did not answer in time. Your question is unchanged; retry when ready.'})
        except OSError:
            host, port = self.backend
            return self.send(503, {'code': 'backend_unreachable', 'error': f'The research backend at {host}:{port} is not running or not ready. Start it, wait until it is ready, then retry. Your question is unchanged.'})
        self.send(status, payload, kind)

    def do_POST(self):
        if urlsplit(self.path).path.startswith('/api/'):
            return self.proxy('POST')
        self.send(404, {'error': 'Not found.'})

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
    parser.add_argument('port', nargs='?', type=int, default=int(os.environ.get('PORT') or 8814))
    parser.add_argument('--backend', type=loopback_backend, default=None,
                        help='Loopback origin of a running Research Desk backend, e.g. http://127.0.0.1:8801')
    args = parser.parse_args()
    if os.environ.get('RESEARCH_BACKEND') and args.backend is None:
        args.backend = loopback_backend(os.environ['RESEARCH_BACKEND'])
    if args.backend and args.backend[1] == args.port:
        sys.exit('The backend and this host cannot share a port.')
    Handler.backend = args.backend
    try:
        server = Server(('127.0.0.1', args.port), Handler)
    except OSError:
        sys.exit(f'Port {args.port} is already in use. Run: python ui-next/serve.py <another port>')
    if args.backend:
        print(f'Research workspace (live): http://127.0.0.1:{args.port}/?live=1  ->  backend http://{args.backend[0]}:{args.backend[1]}', flush=True)
    print(f'Research workspace (mock): http://127.0.0.1:{args.port}/  (Ctrl+C to stop)', flush=True)
    server.serve_forever()

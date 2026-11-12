"""Prototype-only static host for the redesigned research workspace.

Serves ui-next/ at the site root and falls back to the existing ui/ assets, so
the prototype loads the real source reader, math, export and read-aloud modules
from the same absolute paths the production demo server uses. It sends the same
Content-Security-Policy as src/research_demo.py. No research code is imported;
/api/* is answered in the browser by mock-api.js.

    python ui-next/serve.py            # http://127.0.0.1:8814/
"""
import mimetypes
import os
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        name = 'index.html' if path == '/' else path.lstrip('/')
        body = None
        for root in ROOTS:
            target = (root / name).resolve()
            if root in target.parents and target.is_file() and target.suffix != '.py':
                body = target.read_bytes()
                break
        if body is None or path.startswith('/api/'):
            body, status, kind = b'{"error": "Not found."}', 404, 'application/json'
        else:
            status = 200
            kind = TYPES.get(target.suffix) or mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', CSP)
        self.end_headers()
        self.wfile.write(body)


class Server(ThreadingHTTPServer):
    # On Windows, address reuse would let this bind a port another local server already owns.
    allow_reuse_address = False


if __name__ == '__main__':
    port = int(os.environ.get('PORT') or (sys.argv[1] if len(sys.argv) > 1 else 8814))
    try:
        server = Server(('127.0.0.1', port), Handler)
    except OSError:
        sys.exit(f'Port {port} is already in use. Run: python ui-next/serve.py <another port>')
    print(f'Research workspace prototype: http://127.0.0.1:{port}/  (Ctrl+C to stop)', flush=True)
    server.serve_forever()

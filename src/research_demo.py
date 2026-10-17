"""Offline fixture adapter and loopback-only UI. No live pipeline imports."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from src.research_contracts import validate_request, validate_result

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures' / 'research'
ASSETS = ROOT / 'ui'
SCENARIOS = {
    'full': 'normal-v1.json',
    'partial': 'normal-v1.json',
    'insufficient': 'insufficient-v1.json',
    'empty': 'empty-v1.json',
    'provider-error': None,
}


def load_demo(request: dict, scenario: str) -> dict:
    """Return a demo envelope; never relabel a canned answer as a live query."""
    submitted = validate_request(request)
    if scenario not in SCENARIOS:
        raise ValueError('Unknown demo scenario.')
    envelope = {
        'mode': 'fixture', 'scenario': scenario, 'submitted_request': submitted,
        'fixture_file': SCENARIOS[scenario], 'result': None, 'error': None,
    }
    if scenario == 'provider-error':
        envelope['error'] = {
            'code': 'provider_unavailable',
            'message': 'Simulated provider failure. No provider was called; no draft was produced.',
        }
        return envelope
    result = json.loads((FIXTURES / SCENARIOS[scenario]).read_text())
    if scenario == 'partial':
        # A UI-only variant: supported summary, abstained business translation.
        # Leave the shared canonical fixtures untouched.
        result['business_insight'].update(
            status='insufficient_evidence', implications=[], risks=[],
            limitations=['Demo partial state: evidence supports the summary, not a business recommendation.'],
        )
    validate_result(result)
    envelope['result'] = result
    return envelope


class DemoHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Do not log user queries or request payloads."""

    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; style-src 'self'; script-src 'self'; "
                         "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
                         "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        assets = {'/': ('index.html', 'text/html'),
                  '/app.js': ('app.js', 'text/javascript'),
                  '/styles.css': ('styles.css', 'text/css')}
        asset = assets.get(urlsplit(self.path).path)
        if asset is None:
            self.respond(404, {'error': 'Not found.'})
            return
        name, kind = asset
        self.respond(200, (ASSETS / name).read_bytes(), kind + '; charset=utf-8')

    def do_POST(self):
        if self.path != '/api/demo':
            self.respond(404, {'error': 'Not found.'})
            return
        if self.headers.get_content_type() != 'application/json':
            self.respond(415, {'error': 'Use application/json.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16384:
                raise ValueError('Request must be between 1 and 16384 bytes.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Request must be an object.')
            scenario = payload.get('scenario', 'full')
            if not isinstance(scenario, str):
                raise ValueError('Scenario must be a string.')
            response = load_demo({'query': payload.get('query')}, scenario)
        except (ValueError, TypeError):
            self.respond(400, {'error': 'Enter a nonempty query and choose a valid demo scenario.'})
            return
        self.respond(200, response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), DemoHandler) as server:
        print(f'Fixture demo: http://127.0.0.1:{server.server_port} (no live execution)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()

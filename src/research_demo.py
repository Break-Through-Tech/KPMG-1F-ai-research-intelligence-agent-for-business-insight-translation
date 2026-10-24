"""Loopback UI: offline fixtures, saved results, or explicit single-paper or persistent-index synthesis."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit
import mimetypes

from src.research_contracts import validate_request, validate_result
from src.paper_conversation import validate_history
from src.indexed_research import IndexedContextError
from src.plain_language import fixture_view, plain_language_view

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures' / 'research'
ASSETS = ROOT / 'ui'
VENDOR_ASSETS = {
    '/' + path.relative_to(ASSETS).as_posix():
        (path.relative_to(ASSETS).as_posix(), mimetypes.guess_type(path)[0] or 'application/octet-stream')
    for path in (ASSETS / 'vendor' / 'katex').rglob('*')
    if path.is_file() and path.suffix in {'.js', '.css', '.woff2'}
}
SCENARIOS = {
    'full': 'normal-v1.json',
    'plain-language': 'plain-language-v1.json',
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
    envelope['plain_language'] = fixture_view(result)
    return envelope


def saved_result_envelope(result):
    """Preserve validated stage states rather than relabeling replay as success."""
    validate_result(result)
    if not result['evidence']:
        scenario = 'empty'
    elif result['summary']['status'] == 'insufficient_evidence':
        scenario = 'insufficient'
    elif (result.get('business_insight')
          and result['business_insight']['status'] == 'insufficient_evidence'):
        scenario = 'partial'
    else:
        scenario = 'full'
    return {'mode': 'saved-real-result', 'scenario': scenario,
            'submitted_request': result['request'], 'result': result,
            'error': None, 'fixture_file': None, 'plain_language': plain_language_view(result)}


class DemoHandler(BaseHTTPRequestHandler):
    saved_result = None
    research = None
    research_lock = Lock()
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
                         "default-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; script-src 'self'; "
                         "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
                         "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        hosts = {f'127.0.0.1:{self.server.server_port}',
                 f'localhost:{self.server.server_port}'}
        return (self.headers.get('Host') in hosts
                and self.headers.get('Origin') in {None, *(f'http://{host}' for host in hosts)}
                and self.headers.get('Sec-Fetch-Site') != 'cross-site')

    def do_GET(self):
        if not self.local_request():
            self.respond(403, {'error': 'Use the local research page.'})
            return
        if self.path == '/api/config':
            config = {'live': self.research is not None}
            if getattr(self.research, 'mode', None) == 'indexed':
                config.update(self.research.config())
            context_id = getattr(self.research, 'paper_context_id', None)
            if context_id:
                config['paper_context_id'] = context_id
            self.respond(200, config)
            return
        if self.path == '/api/saved-result':
            self.respond(200, self.saved_result)
            return
        assets = {'/': ('index.html', 'text/html'),
                  '/app.js': ('app.js', 'text/javascript'),
                  '/answer-export.js': ('answer-export.js', 'text/javascript'),
                  '/math.js': ('math.js', 'text/javascript'),
                  '/source-reader.js': ('source-reader.js', 'text/javascript'),
                  '/styles.css': ('styles.css', 'text/css'),
                  '/reading-preferences.js': ('reading-preferences.js', 'text/javascript'),
                  '/reading-preferences.css': ('reading-preferences.css', 'text/css')}
        asset = assets.get(urlsplit(self.path).path)
        # Fixed inventory, not arbitrary file serving (including encoded traversal).
        if asset is None:
            asset = VENDOR_ASSETS.get(urlsplit(self.path).path)
        if asset is None:
            self.respond(404, {'error': 'Not found.'})
            return
        name, kind = asset
        self.respond(200, (ASSETS / name).read_bytes(), kind)

    def do_POST(self):
        if not self.local_request():
            self.respond(403, {'error': 'Use the local research page.'})
            return
        if self.path not in {'/api/demo', '/api/research'}:
            self.respond(404, {'error': 'Not found.'})
            return
        if self.path == '/api/research':
            if self.research is None:
                self.respond(503, {'error': 'Live synthesis is not configured.'})
                return
        if self.headers.get_content_type() != 'application/json':
            self.respond(415, {'error': 'Use application/json.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            limit = 196608 if self.path == '/api/research' else 16384
            if not 0 < length <= limit:
                raise ValueError('Request exceeds the local endpoint limit.')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Request must be an object.')
            scenario = payload.get('scenario', 'full')
            if not isinstance(scenario, str):
                raise ValueError('Scenario must be a string.')
            if self.path == '/api/research':
                request = (self.research.prepare_request(payload) if getattr(self.research, 'mode', None) == 'indexed' else
                    validate_request({'query': payload.get('query'),
                    'history': validate_history(payload.get('history', []))}))
                context_id = getattr(self.research, 'paper_context_id', None)
                if request.get('history') and context_id and payload.get('paper_context_id') != context_id:
                    self.respond(409, {'code': 'paper_changed',
                        'error': 'The active paper changed; clear previous conversation context and retry.',
                        'paper_context_id': context_id})
                    return
                if len(request['query']) > 2000:
                    raise ValueError('Question exceeds 2000 characters.')
            else:
                response = load_demo({'query': payload.get('query')}, scenario)
        except (ValueError, TypeError):
            self.respond(400, {'error': 'Enter a question (up to 2000 characters) and valid bounded conversation history or demo scenario.'})
            return
        if self.path == '/api/research':
            if not self.research_lock.acquire(blocking=False):
                self.respond(409, {'error': 'A synthesis is already running. Please wait, then retry.'})
                return
            try:
                if getattr(self.research, 'mode', None) == 'indexed':
                    response = self.research.execute(payload)
                else:
                    response = self.research(request)
                if response.get('result'):
                    response['plain_language'] = plain_language_view(response['result'])
                if response.get('result') and getattr(self.research, 'mode', None) != 'indexed':
                    type(self).saved_result = {**response, 'mode': 'saved-real-result'}
            except IndexedContextError:
                self.respond(409, {'code': 'indexed_context_changed', 'error': 'Indexed context changed or request is invalid. Reload after restarting with the active index; no answer accepted.'})
                return
            except Exception:
                self.respond(502, {'error': 'Synthesis failed or its citations did not validate. No answer was accepted. Retry your question.'})
                return
            finally:
                self.research_lock.release()
        self.respond(200, response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--result', type=Path, help='Replay a validated pending research result; does not execute queries.')
    parser.add_argument('--paper', type=Path, help='Enable live synthesis over one local arXiv PDF.')
    parser.add_argument('--pdf-only', action='store_true', help='Skip arXiv HTML lookup; use PDF text without math recovery.')
    parser.add_argument('--codex-model', help='Explicit model for the existing ChatGPT login; no API key.')
    parser.add_argument('--codex-bin', help='Path to the installed Codex CLI.')
    parser.add_argument('--index', type=Path, help='Query an existing Chroma persistent index; never builds/downloads one.')
    parser.add_argument('--collection', default='arxiv_papers')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--configured-provider', action='store_true', help='Explicitly use the existing RESEARCH_PROVIDER configuration for indexed mode.')
    args = parser.parse_args()
    if sum(bool(x) for x in (args.paper, args.index, args.result)) > 1:
        parser.error('--paper, --index and --result are mutually exclusive')
    if args.index:
        if bool(args.codex_model) == bool(args.configured_provider):
            parser.error('--index requires exactly one of --codex-model or --configured-provider')
        from src.indexed_research import IndexedResearch, open_index, code_revision
        try:
            retrieve, identity, index_path = open_index(args.index, args.collection)
            if args.codex_model:
                from src.codex_generation import create_codex_generate
                generate, metadata = create_codex_generate(model=args.codex_model, binary=args.codex_bin)
            else:
                from src.generation import create_generate
                generate, metadata = create_generate()
            import sys
            DemoHandler.research = IndexedResearch(retrieve=retrieve, identity=identity,
                generate=generate, metadata=metadata, index_path=index_path, top_k=args.top_k,
                code_revision=code_revision(), command=sys.argv)
        except Exception:
            parser.error('Indexed startup failed. Check existing index/collection, cached encoder, explicit provider and model. No fallback, rebuild or download was attempted.')
    if args.paper:
        if not args.codex_model:
            parser.error('--paper requires --codex-model')
        from src.codex_generation import create_codex_generate
        from src.research_chat import PaperResearch, load_paper
        try:
            passages, source = load_paper(args.paper, prefer_html=not args.pdf_only)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        generate, metadata = create_codex_generate(model=args.codex_model, binary=args.codex_bin)
        DemoHandler.research = PaperResearch(passages, generate, metadata, source=source)
    if args.result:
        result = json.loads(args.result.read_text())
        DemoHandler.saved_result = saved_result_envelope(result)
    with ThreadingHTTPServer(('127.0.0.1', args.port), DemoHandler) as server:
        label = 'Indexed research' if args.index else 'Paper synthesis' if args.paper else 'Saved-result viewer' if args.result else 'Fixture demo'
        note = 'live indexed synthesis' if args.index else 'live LLM synthesis' if args.paper else 'no live execution'
        print(f'{label}: http://127.0.0.1:{server.server_port} ({note})', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()

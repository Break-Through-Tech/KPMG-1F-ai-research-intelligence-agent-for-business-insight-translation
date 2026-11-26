"""Single-process, access-gated Render preview around the existing B2 handler."""
import base64
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
from hmac import compare_digest
from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import os
import re
import sqlite3
import sys
from threading import BoundedSemaphore, Lock
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'experiments/table-endpoint')]
from engine_runtime import SESSION, build_s2, engine_settings, session_token
from evidence_tables import TableIndex
from recorded_backend import make_handler
from src.experimental.b2 import open_b2
from src.experimental.demo import create_research
from src.generation import ProviderUnavailable, create_generate, log_provider_failure
from src.generation_config import GenerationConfig
from src.indexed_research import fingerprint
from jsonschema import Draft202012Validator

ASSETS = {
    'index.html', 'app.js', 'async-guards.js', 'chart-select.js', 'chart-svg.js',
    'consult.css', 'evidence.js', 'prefs.js', 'answer-export.js', 'math.js',
    'read-aloud.css', 'read-aloud.mjs', 'research-speech.js', 'source-reader.js',
    'kpmg-logo-white.png',
}
VENDOR = re.compile(r'vendor/katex/(?:katex\.min\.(?:js|css)|fonts/[A-Za-z0-9_-]+\.woff2)')
FONTS = re.compile(r'fonts/[a-z0-9-]+\.woff2')  # bundled Inter and Source Serif 4
BRIEF = r'/api/briefs/[0-9a-f]{32}'
READ_API = re.compile(rf'/api/(?:config|saved-result|evidence-table|briefs)|{BRIEF}')
WRITE_API = re.compile(rf'/api/(?:research|briefs)|{BRIEF}(?:/reviews)?')
MODEL = 'gemini-3.1-flash-lite'


class QuotaExhausted(RuntimeError):
    pass


class Budget:
    """Persist reservations before dispatch, including calls that later fail."""
    def __init__(self, path, clock=time.time, *, smoke=False):
        self.path, self.clock, self.smoke = path, clock, smoke
        with closing(sqlite3.connect(path)) as store, store:
            store.execute('CREATE TABLE IF NOT EXISTS attempts (at REAL NOT NULL, tokens INTEGER NOT NULL)')

    def reserve(self, estimate):
        with closing(sqlite3.connect(self.path, timeout=5)) as store, store:
            store.execute('PRAGMA synchronous=FULL')
            store.execute('BEGIN IMMEDIATE')
            if self.smoke:
                count, = store.execute('SELECT COUNT(*) FROM attempts').fetchone()
                if count >= 10:
                    raise QuotaExhausted('Gemini smoke test attempt cap reached.')
            now = self.clock()
            latest, = store.execute('SELECT MAX(at) FROM attempts').fetchone()
            day, = store.execute('SELECT COUNT(*) FROM attempts WHERE at >= ?', (now - 86400,)).fetchone()
            minute, tokens = store.execute(
                'SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM attempts WHERE at >= ?', (now - 60,)).fetchone()
            if (latest is not None and now < latest) or day >= 60 or minute >= 6 or tokens + estimate > 160_000:
                raise QuotaExhausted('Demo generation budget unavailable.')
            store.execute('INSERT INTO attempts VALUES (?, ?)', (now, estimate))


def wire_schema(schema):
    """Relax only decoder bounds. The original schema still validates every result."""
    wire = deepcopy(schema)

    def visit(node):
        for key in ('minLength', 'maxLength', 'minItems', 'maxItems', 'minimum', 'maximum'):
            node.pop(key, None)
        for name, child in node.get('properties', {}).items():
            if name == 'chunk_id':
                child.pop('enum', None)
            visit(child)
        if isinstance(node.get('items'), dict):
            visit(node['items'])

    visit(wire)
    return wire


REPLY_ALLOWANCE = 8192


def reservation(payload_bytes):
    """Tokens to reserve for one call. Gemini measured about 3.6 UTF-8 bytes per input token on demo-100 prompts,
    so one token per 2 bytes still over-reserves input about 1.8x, plus a fixed allowance for the reply. The former
    2 tokens per byte over-reserved about 7x, so one S2 question (drafting + review) could exceed the 160k minute
    budget on its own and fail at review."""
    return payload_bytes // 2 + REPLY_ALLOWANCE


TRANSIENT_RETRY_DELAYS = (2, 6)  # seconds before the 2nd and 3rd attempt after a provider 5xx


def quota_generate(generate, budget, *, sleep=time.sleep):
    def guarded(prompt, *, response_schema=None):
        wire = wire_schema(response_schema) if response_schema is not None else None
        payload = json.dumps({'prompt': prompt, 'schema': wire}, ensure_ascii=False).encode()
        for attempt in range(len(TRANSIENT_RETRY_DELAYS) + 1):
            # Every attempt, including a retry, is reserved first, so all minute, daily and smoke limits apply.
            try:
                budget.reserve(reservation(len(payload)))
            except QuotaExhausted as error:
                log_provider_failure('local_budget', error)
                raise
            try:
                text = generate(prompt, response_schema=wire)
                break
            except ProviderUnavailable:
                if attempt == len(TRANSIENT_RETRY_DELAYS):
                    raise
                print(f'provider-retry attempt={attempt + 2} after=transient_server_error', file=sys.stderr, flush=True)
                sleep(TRANSIENT_RETRY_DELAYS[attempt])
        if response_schema is not None:
            try:
                Draft202012Validator(response_schema).validate(json.loads(text))
            except Exception as error:
                log_provider_failure('contract_schema', error)
                raise
        return text

    guarded.supports_response_schema = True
    return guarded


def verify_snapshot(path):
    manifest = json.loads((path / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if sha256((path / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Staged asset identity check failed.')
    return manifest


def build_handler(snapshot, state, origin, password, generate, metadata, *, synthetic_fixture=False):
    manifest = verify_snapshot(snapshot)
    if bool(manifest.get('synthetic_fixture')) != synthetic_fixture:
        raise ValueError('Synthetic snapshots require explicit offline fixture mode.')
    bundle = snapshot / 'artifacts/bundle'
    engine, paper_balance = engine_settings(os.environ)
    smoke = os.environ.get('KPMG_GEMINI_SMOKE', '0')
    if smoke not in ('0', '1') or (smoke == '1' and (engine != 's2' or paper_balance)):
        raise ValueError('Gemini smoke mode requires Standard S2.')
    ledger = state / ('gemini-smoke-attempts.sqlite3' if smoke == '1' else 'provider-usage.sqlite3')
    guarded = quota_generate(generate, Budget(ledger, smoke=smoke == '1'))
    encoder = snapshot / 'artifacts/encoder'
    reranker = snapshot / 'artifacts/reranker'
    if engine == 's2':
        research, index = build_s2(bundle, encoder, reranker, guarded, metadata,
                                   state / 's2-checkpoints', paper_balance=paper_balance)
    else:
        retrieval = open_b2(bundle, encoder_path=encoder, reranker_path=reranker)
        index = retrieval[1]()
        research = create_research(retrieval, guarded, metadata, top_k=8)
    tables = TableIndex(bundle / 'parents.jsonl', snapshot / 'artifacts/table-audit.json')
    if tables.audit_problem or tables.index_sha256 != index['indexed_records_sha256']:
        raise ValueError('Table audit or retrieval identity does not match the bundle.')
    # Apply display-safe provenance before the context or snapshot is fingerprinted.
    research.provenance['index_path'] = 'synthetic-fixture' if synthetic_fixture else 'demo-100'
    research.provenance['retrieval']['reranker'] = 'ms-marco-MiniLM-L6-v2'
    research.provenance['code_revision'] = manifest['backend_head']
    research.context_id = fingerprint(research.provenance)
    base = make_handler(ROOT, tables, state / 'briefs.sqlite3')
    auth = b'Basic ' + base64.b64encode(('reviewer:' + password).encode('ascii'))
    authority = urlsplit(origin).netloc
    assets = snapshot / 'assets'

    class Handler(base):
        def local_request(self):
            # Auth and exact Host/Origin are checked before entering the inherited handler.
            return self.accepted

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Robots-Tag', 'noindex, nofollow')
            self.send_header('X-Content-Type-Options', 'nosniff')
            cookie = getattr(self, 's2_cookie', None)
            if cookie:
                self.send_header('Set-Cookie', cookie + ('; Secure' if origin.startswith('https://') else ''))
            super().end_headers()

        def admit(self, write=False):
            incoming = self.headers.get('Authorization', '').encode('latin-1')
            if self.headers.get('Host') != authority or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.respond(403, {'error': 'Use the configured review site.'})
            elif not compare_digest(incoming, auth):
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="KPMG review preview"')
                self.send_header('Content-Length', '0')
                self.end_headers()
            elif write and self.headers.get('Origin') != origin:
                self.respond(403, {'error': 'Writes require the same-origin review page.'})
            else:
                self.accepted = True
                return True
            return False

        def do_GET(self):
            if self.path == '/healthz':
                return self.respond(200, {'status': 'ready'})
            if not self.admit():
                return
            path = urlsplit(self.path).path
            if engine == 's2' and path == '/api/config':
                _, self.s2_cookie = session_token(self.headers.get('Cookie'), password.encode('ascii'))
            if READ_API.fullmatch(path):
                return super().do_GET()
            name = 'index.html' if path == '/' else path.removeprefix('/')
            if name in ASSETS or VENDOR.fullmatch(name) or FONTS.fullmatch(name):
                file = assets / name
                if file.is_file():
                    media = {'.js': 'text/javascript', '.mjs': 'text/javascript',
                             '.woff2': 'font/woff2'}.get(file.suffix, mimetypes.guess_type(name)[0])
                    return self.respond(200, file.read_bytes(), media or 'application/octet-stream')
            return self.respond(404, {'error': 'Not found.'})

        def do_POST(self):
            if not self.admit(write=True):
                return
            if not WRITE_API.fullmatch(urlsplit(self.path).path) or self.headers.get('Transfer-Encoding'):
                return self.respond(404, {'error': 'Not found.'})
            if engine != 's2' or self.path != '/api/research':
                return super().do_POST()
            identity, self.s2_cookie = session_token(self.headers.get('Cookie'), password.encode('ascii'))
            token = SESSION.set(identity)
            try:
                return super().do_POST()
            finally:
                SESSION.reset(token)
                self.s2_cookie = None

        def log_error(self, format, *args):
            # Avoid arbitrary request fragments or provider details in logs.
            return

    def research_only(payload):
        if payload.get('risk_assessment') or payload.get('industry') or payload.get('interpret_context'):
            raise ValueError('Business and regulatory analysis are disabled in this research preview.')
        return original_prepare(payload)

    original_prepare = research.prepare_request
    research.prepare_request = research_only
    Handler.research = research
    Handler.research_lock = Lock()
    return Handler


class Server(ThreadingHTTPServer):
    """Keep one warm set of models and bound the number of request threads."""
    slots = BoundedSemaphore(16)

    def get_request(self):
        socket, address = super().get_request()
        socket.settimeout(15)
        return socket, address

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            try:
                request.sendall(b'HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n')
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

    def handle_error(self, request, address):
        print('A preview connection ended unexpectedly.', flush=True)


def main():
    render = os.environ.get('RENDER') == 'true'
    port = int(os.environ.get('PORT', 8821))
    origin = os.environ.get('KPMG_ORIGIN') or os.environ.get('RENDER_EXTERNAL_URL') or f'http://127.0.0.1:{port}'
    parsed = urlsplit(origin)
    if (parsed.username or parsed.password or not parsed.hostname or parsed.path or parsed.query or parsed.fragment
            or (render and parsed.scheme != 'https')
            or (not render and (parsed.hostname != '127.0.0.1' or parsed.scheme != 'http' or parsed.port != port))):
        raise SystemExit('Set the canonical HTTPS site origin, or use the local loopback origin.')
    password = os.environ.get('KPMG_REVIEW_PASSWORD', '')
    if len(password) < 24 or not password.isascii() or not password.isprintable():
        raise SystemExit('Configure a unique preview password of at least 24 printable ASCII characters.')
    if os.environ.get('KPMG_GEMINI_DEDICATED_FREE') != 'true' or any(
            os.getenv(name) for name in ('GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_VERTEX_BASE_URL', 'GOOGLE_GEMINI_BASE_URL')):
        raise SystemExit('Confirm a dedicated free-tier Gemini Developer API project and remove alternate endpoints.')
    state = Path(os.environ['KPMG_STATE_DIR']).resolve()
    if render and not state.is_mount():
        raise SystemExit('The persistent disk must be mounted at KPMG_STATE_DIR.')
    if not state.is_dir():
        raise SystemExit('Create a private state directory for this preview.')
    config = GenerationConfig('gemini', MODEL, os.environ.get('GOOGLE_API_KEY', ''))
    generate, metadata = create_generate(config)
    snapshot = Path(os.environ.get('KPMG_SNAPSHOT', ROOT / 'snapshot')).resolve()
    start = time.perf_counter()
    handler = build_handler(snapshot, state, origin, password, generate, metadata)
    with Server(('0.0.0.0' if render else '127.0.0.1', port), handler) as service:
        print(f'Research preview ready in {time.perf_counter() - start:.1f}s on port {port}.', flush=True)
        service.serve_forever()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, RuntimeError, sqlite3.Error):
        sys.exit('Preview startup failed. Check the sealed assets, disk and provider configuration.')

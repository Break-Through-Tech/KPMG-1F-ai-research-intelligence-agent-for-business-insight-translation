"""Offline end-to-end check of the Render start path in synthetic-fixture mode.

Starts deploy/render/start.py exactly as Render would (minus HTTPS and the
mounted disk), with a throwaway state directory, then exercises the security
gates, the UI, research with a cited answer, saved work, review and restart
persistence. No provider is constructed and no network access is needed.

    python -B deploy/render/test_hosted_fixture.py [--engine baseline|s2] [--retrieval s2|r2]

Run after: KPMG_DEPLOY_MODE=fixture bash deploy/render/build.sh
"""
import argparse
import base64
from contextlib import closing
import http.client
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
QUESTION = 'What does the test fixture contain?'


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class Client:
    def __init__(self, port, auth=None, host=None):
        self.port, self.auth, self.host = port, auth, host or f'127.0.0.1:{port}'
        self.cookie = None

    def call(self, method, path, body=None, origin=None, cross_site=False):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=120)
        headers = {'Host': self.host}
        if self.auth:
            headers['Authorization'] = self.auth
        if self.cookie:
            headers['Cookie'] = self.cookie
        if origin:
            headers['Origin'] = origin
        if cross_site:
            headers['Sec-Fetch-Site'] = 'cross-site'
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        conn.request(method, path, data, headers)
        response = conn.getresponse()
        raw = response.read()
        cookie = response.getheader('Set-Cookie')
        if cookie:
            self.cookie = cookie.split(';', 1)[0]
        conn.close()
        kind = response.getheader('Content-Type', '')
        return response.status, (json.loads(raw) if 'json' in kind and raw else raw), dict(response.getheaders())


def launch(port, state, password, engine, retrieval):
    env = {**os.environ, 'KPMG_DEPLOY_MODE': 'fixture', 'PORT': str(port), 'KPMG_STATE_DIR': str(state),
           'KPMG_REVIEW_PASSWORD': password, 'RESEARCH_ENGINE': engine, 'S2_PAPER_BALANCE': '0',
           'S2_RETRIEVAL': retrieval}
    for name in ('RENDER', 'RENDER_EXTERNAL_URL', 'KPMG_ORIGIN', 'GOOGLE_API_KEY', 'KPMG_GEMINI_SMOKE'):
        env.pop(name, None)
    start = time.perf_counter()
    child = subprocess.Popen([sys.executable, '-B', str(ROOT / 'deploy/render/start.py')], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    line = child.stdout.readline()
    if 'ready' not in line:
        child.kill()
        raise SystemExit(f'Startup failed: {line.strip()} {child.stdout.read()[-2000:]}')
    return child, time.perf_counter() - start, line.strip()


def check(label, condition, detail=''):
    print(('PASS ' if condition else 'FAIL ') + label + (f' ({detail})' if detail else ''), flush=True)
    if not condition:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=('baseline', 's2'), default='baseline')
    parser.add_argument('--retrieval', choices=('s2', 'r2'), default='s2')
    args = parser.parse_args()
    if args.retrieval == 'r2' and args.engine != 's2':
        parser.error('--retrieval r2 requires --engine s2')
    password = secrets.token_urlsafe(24)
    auth = 'Basic ' + base64.b64encode(f'reviewer:{password}'.encode()).decode()
    port = free_port()
    origin = f'http://127.0.0.1:{port}'
    with tempfile.TemporaryDirectory(prefix='kpmg-render-state-') as tmp:
        state = Path(tmp)
        child, seconds, banner = launch(port, state, password, args.engine, args.retrieval)
        try:
            check('startup banner marks the synthetic fixture', 'SYNTHETIC FIXTURE' in banner, f'{seconds:.1f}s')
            check('healthz is public and minimal', Client(port).call('GET', '/healthz')[:2] == (200, {'status': 'ready'}))
            check('homepage requires authentication', Client(port).call('GET', '/')[0] == 401)
            check('wrong password is rejected', Client(port, 'Basic ' + base64.b64encode(b'reviewer:wrong').decode())
                  .call('GET', '/api/config')[0] == 401)
            check('wrong Host is rejected', Client(port, auth, host='evil.example').call('GET', '/')[0] == 403)
            check('cross-site fetch is rejected', Client(port, auth).call('GET', '/api/config', cross_site=True)[0] == 403)
            user = Client(port, auth)
            status, body, headers = user.call('GET', '/')
            check('approved UI is served', status == 200 and b'<html' in body.lower() and
                  headers.get('Cache-Control') == 'no-store')
            check('mock API script is stripped', b'mock-api.js' not in body)
            check('KaTeX vendor asset is served', user.call('GET', '/vendor/katex/katex.min.js')[0] == 200)
            status, config, _ = user.call('GET', '/api/config')
            check('config is live indexed', status == 200 and config.get('live') is True, json.dumps(config)[:160])
            if args.engine == 's2':
                check('S2 session cookie is issued', bool(user.cookie) and user.cookie.startswith('kpmg_s2_session='))
            request = {'query': QUESTION, 'context_id': config.get('context_id'), 'interpret_context': False,
                       'scenario': 'full'}
            check('write without same Origin is rejected', user.call('POST', '/api/research', request)[0] == 403)
            check('business analysis is refused', user.call('POST', '/api/research',
                  {**request, 'industry': 'banking'}, origin=origin)[0] in (400, 409))
            started = time.perf_counter()
            status, envelope, _ = user.call('POST', '/api/research', request, origin=origin)
            took = time.perf_counter() - started
            result = (envelope or {}).get('result') or {}
            summary = result.get('summary') or {}
            claims = summary.get('claims') or []
            check('research returns a cited answer', status == 200 and claims and claims[0].get('support'),
                  f'{took:.2f}s, {json.dumps(summary)[:200]}')
            chunk = claims[0]['support'][0]['chunk_id']
            evidence = {p.get('chunk_id') for p in result.get('evidence', []) or []}
            check('citation points at retrieved evidence', chunk in evidence, chunk)
            if args.engine == 's2':
                checkpoints = state / 's2-checkpoints'
                first = set(checkpoints.glob('*/*/fingerprint.json'))
                second = Client(port, auth)
                status2, config2, _ = second.call('GET', '/api/config')
                check('independent S2 session cookies', status2 == 200 and second.cookie and
                      second.cookie != user.cookie)
                status2, envelope2, _ = second.call('POST', '/api/research',
                    {**request, 'context_id': config2['context_id']}, origin=origin)
                check('independent session completes research', status2 == 200 and
                      envelope2.get('result', {}).get('summary', {}).get('claims'))
                check('independent session uses a separate checkpoint',
                      len(first) == 1 and len(set(checkpoints.glob('*/*/fingerprint.json')) - first) == 1)
            check('human review is pending', result.get('human_review', {}).get('status') == 'pending')
            other = user.call('POST', '/api/research', {**request, 'query': 'Unrelated question?'}, origin=origin)
            check('unscripted question does not fabricate', other[0] == 200 and not
                  ((other[1].get('result') or {}).get('summary') or {}).get('claims'))
            status, saved, _ = user.call('POST', '/api/briefs', {'envelope': envelope, 'title': 'Fixture brief'},
                                         origin=origin)
            check('brief saves to the state disk', status == 200 and saved.get('library'), json.dumps(saved)[:120]
                  if isinstance(saved, dict) else str(saved)[:120])
            brief = saved['library']['brief']['id']
            version = saved['library']['version']
            status, reviewed, _ = user.call('POST', f'/api/briefs/{brief}/reviews', {
                'version_id': version['id'], 'fingerprint': version['fingerprint'], 'reviewer': 'Fixture Reviewer',
                'decision': 'approve', 'notes': 'Hosting check only.'}, origin=origin)
            check('review records against the exact version', status == 200, json.dumps(reviewed)[:160]
                  if isinstance(reviewed, dict) else str(reviewed)[:160])
            check('SQLite lives in KPMG_STATE_DIR', (state / 'briefs.sqlite3').is_file() and
                  (state / 'provider-usage.sqlite3').is_file())
        finally:
            child.terminate()
            child.wait(timeout=30)
        if args.engine == 's2':
            before_switch = set(checkpoints.glob('*/*/fingerprint.json'))
            # These checks share the real fixture ledger. The first run has
            # already spent the six calls available in one minute.
            with closing(sqlite3.connect(state / 'provider-usage.sqlite3')) as usage:
                latest, = usage.execute('SELECT MAX(at) FROM attempts').fetchone()
            time.sleep(max(0, 60.1 - (time.time() - latest)))
            alternate = 's2' if args.retrieval == 'r2' else 'r2'
            child, _, _ = launch(port, state, password, args.engine, alternate)
            try:
                same = Client(port, auth)
                same.cookie = user.cookie
                status, alternate_config, _ = same.call('GET', '/api/config')
                check('other strategy exposes a fresh context', status == 200 and
                      alternate_config['context_id'] != request['context_id'])
                status, answer, _ = same.call('POST', '/api/research',
                    {**request, 'context_id': alternate_config['context_id']}, origin=origin)
                check('other retrieval strategy answers with the same session',
                      status == 200 and (answer.get('result') or {}).get('summary', {}).get('claims'),
                      f'HTTP {status} {answer.get("error")}')
                added = set(checkpoints.glob('*/*/fingerprint.json')) - before_switch
                expected_mode = 'standard+r2-opt' if alternate == 'r2' else 'standard'
                check('retrieval strategies use separate checkpoints',
                      same.cookie == user.cookie and len(added) == 1 and
                      json.loads(next(iter(added)).read_bytes())['mode'] == expected_mode)
            finally:
                child.terminate()
                child.wait(timeout=30)
        child, seconds, _ = launch(port, state, password, args.engine, args.retrieval)
        try:
            user = Client(port, auth)
            status, listing, _ = user.call('GET', '/api/briefs')
            titles = [b.get('title') for b in (listing or {}).get('briefs', [])]
            check('saved brief survives restart', status == 200 and 'Fixture brief' in titles, f'restart {seconds:.1f}s')
            status, loaded, _ = user.call('GET', f'/api/briefs/{brief}')
            check('review survives restart', status == 200 and any(r.get('decision') == 'approve'
                  for r in (loaded.get('library') or {}).get('reviews', [])))
        finally:
            child.terminate()
            child.wait(timeout=30)
    print(f'ALL CHECKS PASSED ({args.engine}/{args.retrieval}, synthetic fixture: hosting only)')


if __name__ == '__main__':
    main()

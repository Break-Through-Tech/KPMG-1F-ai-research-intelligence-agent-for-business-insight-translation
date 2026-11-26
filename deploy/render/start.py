"""Render start entry point for the supervised research preview.

Runs the verified staged context produced by deploy/render/build.sh, never the
working tree, so the hosted code and assets are exactly the hashed snapshot.

  KPMG_DEPLOY_MODE=real     unchanged experiments/render-staging/server.py (Gemini,
                            quota ledger, Basic auth, same-origin checks).
  KPMG_DEPLOY_MODE=fixture  the same handler, authentication, quotas, saved work and
                            persistent disk, but with the synthetic index and the
                            scripted developer responses. It never constructs a model
                            provider, so it verifies hosting only, not research quality.
"""
import os
from pathlib import Path
import runpy
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def staged_context(fixture):
    workspace = ROOT / '.kpmg-onboarding' / ('fixture' if fixture else '')
    record = workspace / 'context.txt'
    if not record.is_file():
        raise SystemExit('No staged context. Run deploy/render/build.sh with the same KPMG_DEPLOY_MODE.')
    context = (ROOT / record.read_text(encoding='utf-8').strip()).resolve()
    if not (context / 'snapshot/manifest.json').is_file() or not context.is_relative_to(ROOT):
        raise SystemExit('The staged context is missing. Rebuild before starting.')
    return context


def settings():
    """The same origin, password and disk rules as server.main()."""
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
    state = Path(os.environ.get('KPMG_STATE_DIR', '')).resolve()
    if not os.environ.get('KPMG_STATE_DIR') or (render and not os.path.ismount(state)):
        raise SystemExit('The persistent disk must be mounted at KPMG_STATE_DIR.')
    if not state.is_dir():
        raise SystemExit('Create a private state directory for this preview.')
    return render, port, origin, password, state


def run_fixture(context):
    if os.environ.get('KPMG_GEMINI_SMOKE', '0') != '0':
        raise SystemExit('The synthetic fixture never calls a provider; unset KPMG_GEMINI_SMOKE.')
    render, port, origin, password, state = settings()
    import time
    from dev_server import FIXTURE_QUESTION, FIXTURE_QUOTE, fake
    from server import Server, build_handler

    def generate(prompt, *, response_schema):
        return fake(prompt, response_schema=response_schema, question=FIXTURE_QUESTION,
                    quote=FIXTURE_QUOTE, claim=FIXTURE_QUOTE)

    start = time.perf_counter()
    handler = build_handler(context / 'snapshot', state, origin, password, generate,
                            {'provider': 'synthetic-fixture-scripted'}, synthetic_fixture=True)
    with Server(('0.0.0.0' if render else '127.0.0.1', port), handler) as service:
        print(f'SYNTHETIC FIXTURE preview ready in {time.perf_counter() - start:.1f}s on port {port}. '
              'Not research validation.', flush=True)
        print(f'Scripted question: {FIXTURE_QUESTION}', flush=True)
        service.serve_forever()


def main():
    mode = os.environ.get('KPMG_DEPLOY_MODE', '')
    if mode not in ('fixture', 'real'):
        raise SystemExit('Set KPMG_DEPLOY_MODE to fixture or real.')
    os.environ.setdefault('RESEARCH_ENGINE', 'baseline')
    os.environ.setdefault('S2_PAPER_BALANCE', '0')
    for name, value in (('HF_HUB_OFFLINE', '1'), ('TRANSFORMERS_OFFLINE', '1'),
                        ('HF_HUB_DISABLE_PROGRESS_BARS', '1'), ('TOKENIZERS_PARALLELISM', 'false')):
        os.environ[name] = value
    for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        os.environ.setdefault(name, '1')
    context = staged_context(mode == 'fixture')
    sys.path.insert(0, str(context / 'experiments/render-staging'))
    if mode == 'fixture':
        try:
            run_fixture(context)
        except (ValueError, KeyError, OSError, RuntimeError) as error:
            sys.exit(f'Fixture startup failed: {type(error).__name__}.')
        return
    os.environ['KPMG_SNAPSHOT'] = str(context / 'snapshot')
    server = context / 'experiments/render-staging/server.py'
    sys.argv = [str(server)]
    runpy.run_path(str(server), run_name='__main__')


if __name__ == '__main__':
    main()

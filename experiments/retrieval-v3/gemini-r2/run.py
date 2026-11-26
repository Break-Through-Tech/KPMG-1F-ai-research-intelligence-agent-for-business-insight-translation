"""Sealed paired evaluation. With no --authorized-run, performs offline checks only."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import time
from unittest.mock import patch

from budget import GuardedModels, Ledger

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BACKOFF = 300


def verify(base, manifest):
    for name, expected in manifest.items():
        path = base / name
        raw = path.read_bytes()
        digest = expected['sha256'] if isinstance(expected, dict) else expected
        if sha256(raw).hexdigest() != digest or (isinstance(expected, dict) and len(raw) != expected['bytes']):
            raise SystemExit(f'File does not match its pin: {name}')


def verified_inputs(assets, snapshot=None):
    verify(ROOT, json.loads((HERE / 'seal.json').read_bytes()))
    deployment = json.loads((HERE / 'deployment.json').read_bytes())
    verify(ROOT, deployment['code_files'])
    if snapshot is not None:
        verify(snapshot, deployment['snapshot_files'])
    spec = json.loads((ROOT / 'onboarding/assets.json').read_bytes())
    verify(assets, spec['files'])
    bundle = assets / 'demo-100'
    questions = json.loads((HERE / 'questions.json').read_bytes())
    with (bundle / 'parents.jsonl').open(encoding='utf-8') as stream:
        chunks = {row['chunk_id'] for row in map(json.loads, stream)}
    if (len(questions) != 8 or sum(len(q['required_points']) for q in questions) != 36 or
            [q['id'] for q in questions] != [f'U{i}' for i in range(1, 9)]):
        raise SystemExit('Expected eight ordered questions and 36 scoring points.')
    for q in questions:
        for point in q['required_points']:
            if not all(group and set(group) <= chunks for group in point['anchors']):
                raise SystemExit(f'Invalid evidence anchor for {q["id"]}.')
    return bundle, questions


def application_generate(ledger, scope, key, *, client_factory=None, sleep=time.sleep):
    from google import genai
    sys.path[:0] = [str(ROOT), str(ROOT / 'experiments/render-staging')]
    from src.generation import create_generate, _usage
    from src.generation_config import GenerationConfig
    from server import MODEL, quota_generate

    factory = client_factory or genai.Client

    def limited_client(**kwargs):
        client = factory(**kwargs)
        return SimpleNamespace(models=GuardedModels(client.models, ledger, _usage, scope))

    with patch.object(genai, 'Client', limited_client):
        raw, metadata = create_generate(GenerationConfig('gemini', MODEL, key))

    class DispatchBudget:
        def reserve(self, _tokens):
            # The SDK boundary accounts for every actual send.
            return

    return quota_generate(raw, DispatchBudget(), sleep=sleep), metadata


def run(assets, bundle, questions, state):
    import re
    sys.path[:0] = [str(ROOT), str(ROOT / 'experiments/render-staging')]
    from engine_runtime import build_s2

    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    # The campaign uses the public Gemini Developer API directly. Reject endpoint overrides.
    if os.environ.get('GOOGLE_GEMINI_BASE_URL') or os.environ.get('GOOGLE_GENAI_USE_VERTEXAI'):
        raise SystemExit('Clear Gemini endpoint and Vertex AI overrides for this campaign.')
    key = os.environ.get('GEMINI_EVAL_API_KEY')
    if not key:
        raise SystemExit('Set the approved, dedicated GEMINI_EVAL_API_KEY in the process environment.')
    if state.is_relative_to(ROOT):
        raise SystemExit('Use private state outside the checkout.')
    state.mkdir(mode=0o700, exist_ok=True)
    # Fail closed after a crash. The operator must inspect state before removing a stale lock.
    with (state / 'active.lock').open('x') as lock:
        lock.write(str(os.getpid()))
        lock.flush()
        try:
            ledger = Ledger(state / 'dispatch.sqlite3', pace=True)
            ledger.check_blocked()
            scope = ('S2', 'U1')
            guarded, metadata = application_generate(ledger, lambda: scope, key)
            engines = {}

            def one(arm, q):
                nonlocal scope
                qid = q['id']
                if not re.fullmatch(r'U[1-8]', qid):
                    raise SystemExit('Unexpected question ID.')
                scope = arm, qid
                folder = state / arm / qid
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / 'result.json'
                if target.is_file():
                    return True
                starts = sorted(folder.glob('attempt-*.json'))
                if len(starts) >= 2:
                    return False
                if starts:
                    time.sleep(max(0, BACKOFF - (time.time() - starts[-1].stat().st_mtime)))
                if arm not in engines:
                    engines[arm], _ = build_s2(bundle, assets / 'models/encoder', assets / 'models/reranker',
                        guarded, metadata, state / 'checkpoints', retrieval_strategy=arm.lower())
                engine = engines[arm]
                attempt = folder / f'attempt-{len(starts) + 1}.json'
                attempt.touch(exist_ok=False)
                started = time.monotonic()
                payload = {'query': q['question'], 'context_id': engine.context_id,
                           'interpret_context': False, 'scenario': 'full'}
                try:
                    answer = engine.execute(payload, session_id=f'eval-{arm}-{qid}')
                    ledger.check_blocked()
                    summary = (answer.get('result') or {}).get('summary', {})
                    if summary.get('status') != 'ok' or not any(
                            claim.get('support') for claim in summary.get('claims', [])):
                        raise ValueError('No cited claims returned.')
                except Exception as error:
                    attempt.write_text(json.dumps({'seconds': time.monotonic() - started,
                                                   'error': type(error).__name__}), encoding='utf-8')
                    ledger.check_blocked()
                    return False
                attempt.write_text(json.dumps({'seconds': time.monotonic() - started}), encoding='utf-8')
                temp = target.with_suffix('.tmp')
                temp.write_text(json.dumps(answer, ensure_ascii=False), encoding='utf-8')
                temp.replace(target)
                return True

            for q in questions[:2]:
                if not one('S2', q):
                    raise SystemExit('Smoke failed. Inspect the ledger before any authorized continuation.')
            print('Smoke passed. Continuing the sealed paired schedule.', flush=True)
            schedule = [(q, 'R2') for q in questions[:2]]
            schedule += [(q, arm) for i, q in enumerate(questions[2:])
                         for arm in (('S2', 'R2') if i % 2 == 0 else ('R2', 'S2'))]
            for _ in range(2):
                for q, arm in schedule:
                    one(arm, q)
            for arm in ('S2', 'R2'):
                complete = sum((state / arm / q['id'] / 'result.json').is_file() for q in questions)
                print(f'{arm}: {complete}/{len(questions)} completed.', flush=True)
        finally:
            lock.close()
            (state / 'active.lock').unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, help='Also verify the locally staged real deployment snapshot')
    parser.add_argument('--state', type=Path)
    parser.add_argument('--authorized-run', action='store_true')
    parser.add_argument('--accept-estimated-token-guard', action='store_true',
                        help='Explicitly allow the local token reservation with post-response usage reconciliation')
    args = parser.parse_args()
    bundle, questions = verified_inputs(args.assets.resolve(), args.snapshot)
    print('Verified campaign seal, runtime assets and eight evidence keys (36 points).')
    if args.authorized_run:
        if not args.accept_estimated_token_guard:
            parser.error('Provider token enforcement is estimated; approve it explicitly before live dispatch')
        if args.state is None:
            parser.error('--authorized-run requires persistent private --state')
        run(args.assets.resolve(), bundle, questions, args.state.resolve())


if __name__ == '__main__':
    main()

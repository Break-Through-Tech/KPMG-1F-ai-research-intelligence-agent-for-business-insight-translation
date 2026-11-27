"""fresh-v3 arm S1: the FROZEN consolidated v1 Standard engine as a control. NOT run until approved.

Runs in its own process with only ../consolidated (v1) on the module path, so no v2 module can be imported by mistake.
The v1 code is verified against its original seal (fresh-v2/seal.json covers every v1 engine file) and is not edited;
only the output folder is redirected in memory, to data/processed/fresh-v3-S1-consolidated-v1-standard.

    python -I run_fresh3_s1.py --check
    python -I run_fresh3_s1.py --run
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / 'consolidated'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arms = load(HERE / 'fresh3_arms.py', 'fresh3_arms')
seal_v3 = load(HERE / 'seal_v3.py', 'seal_v3')
sys.path.insert(0, str(V1))
import run_consolidated as rc1  # noqa: E402  (v1 runner; its env puts only v1 + shared frozen modules on the path)

assert Path(rc1.__file__).resolve().parent == V1, 'v1 runner not loaded from ../consolidated'


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    import codex_paired
    from codex_baseline import free_commit_gb, MIN_FREE_COMMIT_GB
    from prepare import BUNDLE, CLI, ENCODER, PIN, RERANKER
    ready = codex_paired.checks(CLI)
    ready['v1_code_seal'] = rc1.verify_seal()      # frozen v1 engine unchanged since the v1 evaluation
    ready['fresh_v3_seal'] = seal_v3.verify()
    ready['free_commit_gb'] = round(free_commit_gb(), 1)
    questions = json.loads((arms.SET / 'questions.json').read_text(encoding='utf-8'))
    print(json.dumps({**ready, 'arm': 'S1', 'engine': 'consolidated v1 Standard (frozen)', 'questions': len(questions),
                      'call_cap': arms.ARM_CAP['S1'], 'expected_calls': arms.EXPECTED['S1']}, indent=1))
    print(json.dumps(arms.combined_check('S1')))
    if args.check:
        return
    if ready['free_commit_gb'] < MIN_FREE_COMMIT_GB:
        raise SystemExit('Not enough free memory; nothing was run.')
    import evidence as ev
    import evidence_budget
    from codex_paired import Budget, CodexCalls, EFFORT, MODEL, TIMEOUT
    from engine import ConsolidatedResearch
    from request_guard import RequestGuard
    from src.codex_generation import create_codex_generate
    import env
    assert Path(ev.__file__).resolve().parent == V1 and Path(env.__file__).resolve().parent == V1
    receipts = []
    generate, _metadata = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT,
                                                receipts=receipts)
    _r, identity, ranked, count, _p, _v = evidence_budget.open_ranked(BUNDLE, encoder_path=ENCODER,
                                                                      reranker_path=RERANKER, table_comparisons=False)
    if identity()['indexed_records_sha256'] != PIN:
        raise SystemExit('Unexpected B2 index')
    rc1.ARMS = {'standard': arms.ARM_DIRS['S1']}  # in-memory redirect only; the v1 file is unchanged
    out = arms.OUT / arms.ARM_DIRS['S1']
    out.mkdir(parents=True, exist_ok=True)
    calls = CodexCalls(generate, receipts, Budget(out / 'calls.sqlite3', cap=arms.ARM_CAP['S1']))
    guard = RequestGuard(calls)  # v1 behaviour, as evaluated
    engine = ConsolidatedResearch('standard', ranked=ranked, count=count, tables=ev.TableIndex(env.bundle_rows()),
                                  generate=guard, v2=env.load_v2(), gate=env.load_gate())
    started = time.perf_counter()
    status = rc1.run('standard', engine=engine, calls=calls, guard=guard, receipts=receipts, out_root=arms.OUT,
                     questions=questions)
    print(json.dumps({'status': status, 'calls_used': calls.budget.used(),
                      'wall_seconds': round(time.perf_counter() - started, 1)}, indent=1))


if __name__ == '__main__':
    main()

"""fresh-v4 final validation runner: S3 (candidate) vs S2 (frozen V2 Standard), same fresh questions, same bundle.

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I run_fresh4.py --check S3|S2     (readiness; 0 calls)
    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I run_fresh4.py --run S3|S2       (live; needs approval)

Budget: expected 20 calls per arm (2 per question x 10), cap 25 per arm, PERSISTENT COMBINED CAP 50 (retries included),
counted from both arms' sqlite ledgers. One resume per question (at most 2 attempts). 300 s call timeout. Refuses to
run below 6 GB free memory, on an unverified seal, or on an unexpected validation bundle.
"""
import argparse
import json
import sys
import time
from contextlib import closing
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I omits the script folder
import s3_env  # noqa: E402

HERE = s3_env.HERE
ROOT = s3_env.ROOT
OUT = ROOT / 'data/processed'
SET = HERE / 'fresh-v4'
BUNDLE = ROOT / 'data/processed/validation-bundles/fresh-v4-110'
ARM_DIRS = {'S3': 'fresh-v4-S3-component-coverage', 'S2': 'fresh-v4-S2-consolidated-v2-standard'}
ARM_CAP = {'S3': 25, 'S2': 25}
COMBINED_CAP = 50
MAX_ATTEMPTS = 2


def calls_used(arm, out_root=OUT):
    path = out_root / ARM_DIRS[arm] / 'calls.sqlite3'
    if not path.is_file():
        return 0
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]


def combined_check(arm, out_root=OUT):
    used = {a: calls_used(a, out_root) for a in ARM_DIRS}
    worst = sum(used.values()) + (ARM_CAP[arm] - used[arm])
    if worst > COMBINED_CAP:
        raise SystemExit(f'Combined cap: {sum(used.values())} used; {arm} could use {ARM_CAP[arm] - used[arm]} more, '
                         f'exceeding {COMBINED_CAP}. Nothing was run.')
    return {'combined_used': sum(used.values()), 'arm': arm, 'arm_remaining': ARM_CAP[arm] - used[arm],
            'combined_cap': COMBINED_CAP}


def bundle_pin():
    return json.loads((SET / 'bundle-record.json').read_text(encoding='utf-8'))['manifest']['artifact_sha256']['parents.jsonl']


def make_engine(arm, *, ranked, count, tables, generate):
    if arm == 'S3':
        from s3_engine import S3Research
        return S3Research(ranked=ranked, count=count, tables=tables, generate=generate,
                          v2=s3_env.v2env.load_v2(), gate=s3_env.v2env.load_gate())
    from engine import ConsolidatedResearch  # frozen V2 Standard, unchanged
    return ConsolidatedResearch('standard', ranked=ranked, count=count, tables=tables, generate=generate,
                                v2=s3_env.v2env.load_v2(), gate=s3_env.v2env.load_gate())


def run(arm, *, engine, calls, guard, receipts, out_root, questions):
    """Run or resume one arm (V2's runner semantics). Injectable for offline tests."""
    from codex_paired import BudgetExhausted
    out = out_root / ARM_DIRS[arm]
    status_path = out / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    for question in questions:
        qid, folder = question['id'], out / question['id']
        attempts_path = folder / 'attempts.json'
        attempts = json.loads(attempts_path.read_text(encoding='utf-8')) if attempts_path.is_file() else []
        if status.get(qid, {}).get('state') == 'complete':
            continue
        if len(attempts) >= MAX_ATTEMPTS:
            status[qid] = {'state': 'failed', 'reason': f'{MAX_ATTEMPTS} attempts used'}
            continue
        print('Running', arm, qid, flush=True)
        calls.question, guard.records = qid, []
        before_receipts, before_calls = len(receipts), calls.budget.used()
        try:
            engine.run(question['question'], folder)
            state = {'state': 'complete'}
        except BudgetExhausted as error:
            status[qid] = {'state': 'stopped', 'reason': str(error)}
            break
        except MemoryError:
            status[qid] = {'state': 'stopped', 'reason': 'MemoryError: free system memory and rerun to resume'}
            break
        except Exception as error:
            state = {'state': 'execution_error', 'error': f'{type(error).__name__}: {str(error)[:200]}',
                     'codex': calls.fatal}
        log_path = folder / 'calls.json'
        log = json.loads(log_path.read_text(encoding='utf-8')) if log_path.is_file() else []
        log.append({'attempt': len(json.loads(attempts_path.read_text(encoding='utf-8'))) if attempts_path.is_file() else 0,
                    'calls': calls.budget.used() - before_calls, 'requests_estimated': guard.records,
                    'actual_usage': [r.get('usage') for r in receipts[before_receipts:]]})
        folder.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(log, indent=1), encoding='utf-8')
        status[qid] = state
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
        if calls.fatal:
            print('Stopping: provider reported', calls.fatal, flush=True)
            break
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', choices=ARM_DIRS)
    action.add_argument('--run', choices=ARM_DIRS)
    args = parser.parse_args()
    arm = args.check or args.run
    import codex_paired
    import seal_s3
    from codex_baseline import free_commit_gb, MIN_FREE_COMMIT_GB
    from prepare import CLI, ENCODER, RERANKER
    ready = codex_paired.checks(CLI)
    ready['s3_seal'] = seal_s3.verify()
    ready['free_commit_gb'] = round(free_commit_gb(), 1)
    questions = json.loads((SET / 'questions.json').read_text(encoding='utf-8'))
    print(json.dumps({**ready, 'arm': arm, 'questions': len(questions), 'arm_cap': ARM_CAP[arm],
                      'expected_calls': 2 * len(questions)}, indent=1))
    print(json.dumps(combined_check(arm)))
    if args.check:
        return
    if ready['free_commit_gb'] < MIN_FREE_COMMIT_GB:
        raise SystemExit(f'Only {ready["free_commit_gb"]} GB free; free at least {MIN_FREE_COMMIT_GB} GB. Nothing was run.')
    import evidence as ev
    import evidence_budget
    from codex_paired import Budget, CodexCalls, EFFORT, MODEL, TIMEOUT
    from accounting import ProviderGuard
    from src.codex_generation import create_codex_generate
    receipts = []
    generate, _metadata = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT,
                                                receipts=receipts)
    _retrieve, identity, ranked, count, _path, _prov = evidence_budget.open_ranked(
        BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
    if identity()['indexed_records_sha256'] != bundle_pin():
        raise SystemExit('Unexpected validation bundle')
    out = OUT / ARM_DIRS[arm]
    out.mkdir(parents=True, exist_ok=True)
    calls = CodexCalls(generate, receipts, Budget(out / 'calls.sqlite3', cap=ARM_CAP[arm]))
    guard = ProviderGuard(calls, 'codex', receipts=receipts)
    rows = [json.loads(l) for l in (BUNDLE / 'parents.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    engine = make_engine(arm, ranked=ranked, count=count, tables=ev.TableIndex(rows), generate=guard)
    started = time.perf_counter()
    status = run(arm, engine=engine, calls=calls, guard=guard, receipts=receipts, out_root=OUT, questions=questions)
    print(json.dumps({'status': status, 'calls_used': calls.budget.used(),
                      'wall_seconds': round(time.perf_counter() - started, 1)}, indent=1))


if __name__ == '__main__':
    main()

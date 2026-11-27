"""Runner for the proposed consolidated live validation (Standard vs Deep, 8 fresh questions). NOT run yet.

    python -I run_consolidated.py --check standard     # offline readiness: seals, login, model listing, caps
    python -I run_consolidated.py --run standard       # live: at most ARM_CAP['standard'] calls
    python -I run_consolidated.py --run deep           # live: at most ARM_CAP['deep'] calls

Rules:
  - Hard cap COMBINED_CAP = 50 model calls across both arms, retries included (persistent SQLite ledgers). An arm
    refuses to start if its remaining allowance could push the combined total past 50.
  - Each question may be resumed ONCE (two attempts in total). A resume repeats only the failed stage (checkpoints).
  - The request guard (estimated tokens) refuses oversized requests before a call is reserved. Actual provider usage
    from the Codex receipts is recorded separately from the estimate.
  - Login, quota, rate-limit, budget and memory failures stop the run; any other failure is recorded and the run
    moves on. Rerunning the same command resumes.
  - The code and question set are sealed; any change after sealing refuses to run.
"""
import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
import time

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))  # -I omits the script folder
import env  # noqa: E402

HERE = env.HERE
ROOT = env.ROOT
SET = HERE / 'fresh-v2'
OUT = ROOT / 'data/processed'
ARMS = {'standard': 'consolidated-v1-standard', 'deep': 'consolidated-v1-deep'}
ARM_CAP = {'standard': 20, 'deep': 30}  # 8 x 2 = 16 and 8 x 3 = 24 expected, plus spare for one resume each
COMBINED_CAP = 50
MAX_ATTEMPTS = 2
SEALED_CODE = ['engine.py', 'evidence.py', 'synthesis.py', 'review.py', 'publication.py', 'env.py', 'run_consolidated.py',
               '../verification-repair/numeric_checks_v2.py', '../verification-repair/interpretation_gate.py',
               '../verification-repair/verification_v2.py', '../agentic/statistical_reports.py',
               '../evidence-budget/evidence_budget.py', '../evidence-budget/request_guard.py',
               '../../src/answer_quality.py', '../../src/research_chat.py']


def calls_used(path):
    if not path.is_file():
        return 0
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]


def combined_check(out_root, mode):
    used = {arm: calls_used(out_root / directory / 'calls.sqlite3') for arm, directory in ARMS.items()}
    worst = sum(used.values()) + (ARM_CAP[mode] - used[mode])
    if worst > COMBINED_CAP:
        raise SystemExit(f'Combined cap: {sum(used.values())} used; {mode} could use {ARM_CAP[mode] - used[mode]} more, '
                         f'exceeding {COMBINED_CAP}. Nothing was run.')
    return {'combined_used': sum(used.values()), 'arm_remaining': ARM_CAP[mode] - used[mode],
            'combined_cap': COMBINED_CAP}


def seal_files():
    files = {f'set/{p.name}': p for p in sorted(SET.glob('*')) if p.name != 'seal.json' and p.is_file()}
    files.update({f'code/{name}': (HERE / name).resolve() for name in SEALED_CODE})
    return files


def write_seal():
    seal = {name: sha256(path.read_bytes()).hexdigest() for name, path in seal_files().items()}
    (SET / 'seal.json').write_text(json.dumps(seal, indent=1), encoding='utf-8')
    return seal


def verify_seal():
    seal = json.loads((SET / 'seal.json').read_text(encoding='utf-8'))
    files = seal_files()
    if set(seal) != set(files):
        raise SystemExit('Sealed file list changed.')
    for name, path in files.items():
        if sha256(path.read_bytes()).hexdigest() != seal[name]:
            raise SystemExit(f'Sealed file changed after sealing: {name}')
    return 'verified'


def run(mode, *, engine, calls, guard, receipts, out_root, questions):
    """Run or resume one arm. engine: ConsolidatedResearch; calls: CodexCalls (budget); guard: RequestGuard.
    Injectable for offline tests."""
    from codex_paired import BudgetExhausted
    out = out_root / ARMS[mode]
    status_path = out / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    for question in questions:
        qid = question['id']
        folder = out / qid
        attempts = json.loads((folder / 'attempts.json').read_text(encoding='utf-8')) if (folder / 'attempts.json').is_file() else []
        if status.get(qid, {}).get('state') == 'complete':
            continue
        if len(attempts) >= MAX_ATTEMPTS:
            status[qid] = {'state': 'failed', 'reason': f'{MAX_ATTEMPTS} attempts used'}
            continue
        print('Running', qid, flush=True)
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
        usage = [r.get('usage') for r in receipts[before_receipts:]]
        log_path = folder / 'calls.json'
        log = json.loads(log_path.read_text(encoding='utf-8')) if log_path.is_file() else []
        log.append({'attempt': len(json.loads((folder / 'attempts.json').read_text(encoding='utf-8'))),
                    'calls': calls.budget.used() - before_calls, 'requests_estimated': guard.records,
                    'actual_usage': usage})
        log_path.write_text(json.dumps(log, indent=1), encoding='utf-8')
        status[qid] = state
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
        if calls.fatal:
            print('Stopping: provider reported', calls.fatal, flush=True)
            break
    status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', choices=ARMS)
    action.add_argument('--run', choices=ARMS)
    args = parser.parse_args()
    mode = args.check or args.run
    import codex_paired
    from codex_baseline import free_commit_gb, MIN_FREE_COMMIT_GB
    from prepare import BUNDLE, CLI, ENCODER, PIN, RERANKER
    ready = codex_paired.checks(CLI)
    ready['set_and_code_seal'] = verify_seal()
    ready['free_commit_gb'] = round(free_commit_gb(), 1)
    questions = json.loads((SET / 'questions.json').read_text(encoding='utf-8'))
    print(json.dumps({**ready, 'mode': mode, 'questions': len(questions), 'arm_cap': ARM_CAP[mode],
                      'expected_calls': len(questions) * (2 if mode == 'standard' else 3)}, indent=1))
    print(json.dumps(combined_check(OUT, mode)))
    if args.check:
        return
    if ready['free_commit_gb'] < MIN_FREE_COMMIT_GB:
        raise SystemExit(f'Only {ready["free_commit_gb"]} GB free; free at least {MIN_FREE_COMMIT_GB} GB. Nothing was run.')
    import evidence as ev
    import evidence_budget
    from codex_paired import Budget, CodexCalls, EFFORT, MODEL, TIMEOUT
    from engine import ConsolidatedResearch
    from request_guard import RequestGuard
    from src.codex_generation import create_codex_generate
    receipts = []
    generate, _metadata = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT,
                                                receipts=receipts)
    _retrieve, identity, ranked, count, _path, _prov = evidence_budget.open_ranked(
        BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
    if identity()['indexed_records_sha256'] != PIN:
        raise SystemExit('Unexpected B2 index')
    out = OUT / ARMS[mode]
    out.mkdir(parents=True, exist_ok=True)
    calls = CodexCalls(generate, receipts, Budget(out / 'calls.sqlite3', cap=ARM_CAP[mode]))
    guard = RequestGuard(calls)
    engine = ConsolidatedResearch(mode, ranked=ranked, count=count, tables=ev.TableIndex(env.bundle_rows()),
                                  generate=guard, v2=env.load_v2(), gate=env.load_gate())
    started = time.perf_counter()
    status = run(mode, engine=engine, calls=calls, guard=guard, receipts=receipts, out_root=OUT, questions=questions)
    print(json.dumps({'status': status, 'calls_used': calls.budget.used(),
                      'wall_seconds': round(time.perf_counter() - started, 1)}, indent=1))


if __name__ == '__main__':
    main()

"""Automated unseen S2 vs S2-R2 live evaluation (one process, both arms, counterbalanced, resumable).

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I run_unseen.py --check   (readiness, 0 calls)
    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I run_unseen.py --run     (live; only after approval)

Arms: S2 = frozen engine.ConsolidatedResearch('standard'); R2 = S2R2Research('r2'). Identical provider/model/effort/
timeout, validation index and budget. Order alternates per question (U1: S2 then R2, U2: R2 then S2, ...).

Budget: one persistent ledger per arm, cap 20 each = HARD CAP 40 across both, failures and retries included.
Recovery: pass 1 runs everything; if any (question, arm) failed (timeout, rate limit, provider error) the runner waits
BACKOFF_S and makes ONE resume pass (stage checkpoints mean only the failed stage repeats). Re-running the command
resumes; completed questions are never repeated. Every attempt is recorded (attempts.json, calls.json, status.json,
unseen-r2-progress.log, unseen-r2-order.json); nothing is excluded silently.
"""
import argparse
from hashlib import sha256
import json
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import s3_env  # noqa: E402

ROOT = s3_env.ROOT
SET = HERE
OUT = ROOT / 'data/processed'
ARMS = {'S2': 'unseen-r2-S2-frozen', 'R2': 'unseen-r2-S2R2'}
ARM_CAP, COMBINED_CAP, MAX_ATTEMPTS = 20, 40, 2
BACKOFF_S = 300
VAL = ROOT / 'data/processed/validation-bundles/fresh-v4-110'
FREEZE = HERE / 'code-freeze.json'
PROGRESS = OUT / 'unseen-r2-progress.log'
CODE = [HERE.parent / n for n in ('s2_r2.py', 's2_paper_balance.py', 'paper_balance.py', 's3_evidence.py',
                                  'components.py', 's3_env.py')] + [HERE / 'run_unseen.py'] + [
    s3_env.V2 / n for n in ('engine.py', 'evidence.py', 'synthesis.py', 'review.py', 'publication.py', 'env.py',
                            'accounting.py')]
SET_FILES = ['questions.json', 'references.json', 'rules.json', 'answer-key.md', 'build_unseen.py']
assert 2 * ARM_CAP == COMBINED_CAP


def digest(paths):
    return {Path(p).resolve().relative_to(ROOT).as_posix(): sha256(Path(p).read_bytes()).hexdigest() for p in paths}


def verify():
    if json.loads(FREEZE.read_text(encoding='utf-8')) != digest(CODE):
        raise SystemExit('Frozen code changed')
    seal = HERE / 'seal.json'
    if not seal.is_file() or json.loads(seal.read_text(encoding='utf-8')) != digest([HERE / f for f in SET_FILES]):
        raise SystemExit('Question set not sealed or changed')
    return 'verified'


def used(arm):
    p = OUT / ARMS[arm] / 'calls.sqlite3'
    if not p.is_file():
        return 0
    with closing(sqlite3.connect(p)) as db:
        return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]


def note(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open('a', encoding='utf-8') as fh:
        fh.write(line + '\n')


def run_one(arm, q, engines, calls, receipts, status, order_log):
    from codex_paired import BudgetExhausted
    folder = OUT / ARMS[arm] / q['id']
    att = folder / 'attempts.json'
    if att.is_file() and len(json.loads(att.read_text(encoding='utf-8'))) >= MAX_ATTEMPTS:
        status[arm][q['id']] = {'state': 'failed', 'reason': f'{MAX_ATTEMPTS} attempts used'}
        return 'failed'
    note(f"{q['id']} {arm} start (calls used {sum(used(a) for a in ARMS)}/{COMBINED_CAP})")
    order_log.append({'q': q['id'], 'arm': arm, 'started': time.time()})
    before = len(receipts)
    calls[arm].question = q['id']
    try:
        engines[arm].run(q['question'], folder)
        state = {'state': 'complete'}
    except BudgetExhausted as error:
        state = {'state': 'stopped', 'reason': str(error)}
    except Exception as error:
        state = {'state': 'execution_error', 'error': f'{type(error).__name__}: {str(error)[:200]}'}
    folder.mkdir(parents=True, exist_ok=True)
    log = folder / 'calls.json'
    prior = json.loads(log.read_text(encoding='utf-8')) if log.is_file() else []
    log.write_text(json.dumps(prior + [{'usage': [r.get('usage') for r in receipts[before:]]}], indent=1),
                   encoding='utf-8')
    status[arm][q['id']] = state
    (OUT / ARMS[arm] / 'status.json').write_text(json.dumps(status[arm], indent=1), encoding='utf-8')
    note(f"{q['id']} {arm} -> {state}")
    return state['state']


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    for f in ('--check', '--run', '--freeze-code', '--seal-set'):
        g.add_argument(f, action='store_true')
    args = ap.parse_args()
    if args.freeze_code:
        FREEZE.write_text(json.dumps(digest(CODE), indent=1), encoding='utf-8')
        return print('code frozen', len(CODE))
    if args.seal_set:
        (HERE / 'seal.json').write_text(json.dumps(digest([HERE / f for f in SET_FILES]), indent=1), encoding='utf-8')
        return print('set sealed')
    import codex_paired
    from codex_baseline import free_commit_gb, MIN_FREE_COMMIT_GB
    from prepare import CLI, ENCODER, RERANKER
    import run_fresh4 as rf
    ready = codex_paired.checks(CLI)
    ready['seal'] = verify()
    ready['free_commit_gb'] = round(free_commit_gb(), 1)
    ready['calls_used'] = {a: used(a) for a in ARMS}
    print(json.dumps({**ready, 'expected_calls': 32, 'cap': COMBINED_CAP}, indent=1))
    if args.check:
        return
    if ready['free_commit_gb'] < MIN_FREE_COMMIT_GB:
        raise SystemExit('Not enough free memory. Nothing was run.')
    import evidence as ev
    import evidence_budget
    from codex_paired import Budget, CodexCalls, EFFORT, MODEL, TIMEOUT
    from accounting import ProviderGuard
    from engine import ConsolidatedResearch
    from src.codex_generation import create_codex_generate
    from s2_r2 import S2R2Research
    receipts = []
    generate, _ = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT, receipts=receipts)
    _r, identity, ranked, count, _p, _v = evidence_budget.open_ranked(VAL, encoder_path=ENCODER, reranker_path=RERANKER,
                                                                      table_comparisons=False)
    if identity()['indexed_records_sha256'] != rf.bundle_pin():
        raise SystemExit('Unexpected validation index')
    rows = {r['chunk_id']: r for r in (json.loads(l) for l in (VAL / 'parents.jsonl').read_text(
        encoding='utf-8').splitlines() if l.strip())}
    tables = ev.TableIndex(rows.values())
    calls, engines, status = {}, {}, {}
    for arm, d in ARMS.items():
        (OUT / d).mkdir(parents=True, exist_ok=True)
        calls[arm] = CodexCalls(generate, receipts, Budget(OUT / d / 'calls.sqlite3', cap=ARM_CAP))
        guard = ProviderGuard(calls[arm], 'codex', receipts=receipts)
        kw = dict(ranked=ranked, count=count, tables=tables, generate=guard, v2=s3_env.v2env.load_v2(),
                  gate=s3_env.v2env.load_gate())
        engines[arm] = (ConsolidatedResearch('standard', **kw) if arm == 'S2'
                        else S2R2Research(retrieval_strategy='r2', rows=rows, **kw))
        sp = OUT / d / 'status.json'
        status[arm] = json.loads(sp.read_text(encoding='utf-8')) if sp.is_file() else {}
    questions = json.loads((SET / 'questions.json').read_text(encoding='utf-8'))
    order_log = []
    for pass_no in (1, 2):
        todo = [(q, arm) for i, q in enumerate(questions)
                for arm in (('S2', 'R2') if i % 2 == 0 else ('R2', 'S2'))
                if status[arm].get(q['id'], {}).get('state') != 'complete']
        if not todo:
            break
        if pass_no == 2:
            note(f'resume pass for {[(q["id"], a) for q, a in todo]} after {BACKOFF_S} s backoff')
            time.sleep(BACKOFF_S)
        for q, arm in todo:
            if sum(used(a) for a in ARMS) >= COMBINED_CAP:
                note('combined cap reached; stopping')
                break
            if run_one(arm, q, engines, calls, receipts, status, order_log) == 'stopped':
                break
    (OUT / 'unseen-r2-order.json').write_text(json.dumps(order_log, indent=1), encoding='utf-8')
    note(f'done: calls used {dict((a, used(a)) for a in ARMS)}; status ' +
         json.dumps({a: {k: v['state'] for k, v in s.items()} for a, s in status.items()}))


if __name__ == '__main__':
    main()

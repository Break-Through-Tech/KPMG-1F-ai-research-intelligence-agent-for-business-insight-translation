"""B1 live diagnostic: S2 + paper balance (flag on) on J03 (demo-100 index) and K05, K07 (validation index).
Comparison = the SAVED frozen-S2 answers for the same questions (no S2 rerun).

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I run_b1_diagnostic.py --check
    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I run_b1_diagnostic.py --run

ONE persistent ledger, HARD CAP 8 calls (6 expected), one resume per question, 300 s call timeout. Refuses on a
changed frozen file (b1-freeze.json), an unexpected index, or < 6 GB free memory.
"""
import argparse
from hashlib import sha256
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s3_env  # noqa: E402

HERE, ROOT = s3_env.HERE, s3_env.ROOT
OUT = ROOT / 'data/processed/b1-diagnostic-S2-paper-balance'
CAP = 8
FREEZE = HERE / 'b1-freeze.json'
FROZEN = [HERE / n for n in ('s2_paper_balance.py', 'paper_balance.py', 'components.py', 'run_b1_diagnostic.py',
                             'run_fresh4.py', 's3_env.py')] + [s3_env.V2 / n for n in (
    'engine.py', 'evidence.py', 'synthesis.py', 'review.py', 'publication.py', 'env.py', 'accounting.py')]
DEMO = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100')
VAL = ROOT / 'data/processed/validation-bundles/fresh-v4-110'
QUESTIONS = [('J03', s3_env.V2 / 'fresh-v3/questions.json', DEMO),
             ('K05', HERE / 'fresh-v4/questions.json', VAL),
             ('K07', HERE / 'fresh-v4/questions.json', VAL)]


def digest():
    return {p.resolve().relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest() for p in FROZEN}


def verify():
    if not FREEZE.is_file():
        raise SystemExit('b1-freeze.json missing')
    if json.loads(FREEZE.read_text(encoding='utf-8')) != digest():
        raise SystemExit('A frozen B1 file changed after freezing')
    return 'verified'


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--check', action='store_true')
    g.add_argument('--run', action='store_true')
    g.add_argument('--freeze', action='store_true')
    args = ap.parse_args()
    if args.freeze:
        if FREEZE.is_file():
            raise SystemExit('already frozen')
        FREEZE.write_text(json.dumps(digest(), indent=1), encoding='utf-8')
        print('frozen', len(FROZEN))
        return
    import codex_paired
    from codex_baseline import free_commit_gb, MIN_FREE_COMMIT_GB
    from prepare import CLI, ENCODER, RERANKER, PIN
    import run_fresh4 as rf
    ready = codex_paired.checks(CLI)
    ready['b1_freeze'] = verify()
    ready['free_commit_gb'] = round(free_commit_gb(), 1)
    used = _used()
    print(json.dumps({**ready, 'calls_used': used, 'cap': CAP, 'expected': 6}, indent=1))
    if args.check:
        return
    if ready['free_commit_gb'] < MIN_FREE_COMMIT_GB:
        raise SystemExit(f'Only {ready["free_commit_gb"]} GB free; need {MIN_FREE_COMMIT_GB}. Nothing was run.')
    import evidence as ev
    import evidence_budget
    from codex_paired import Budget, CodexCalls, EFFORT, MODEL, TIMEOUT, BudgetExhausted
    from accounting import ProviderGuard
    from src.codex_generation import create_codex_generate
    from s2_paper_balance import S2Research
    receipts = []
    generate, _ = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT, receipts=receipts)
    OUT.mkdir(parents=True, exist_ok=True)
    calls = CodexCalls(generate, receipts, Budget(OUT / 'calls.sqlite3', cap=CAP))
    guard = ProviderGuard(calls, 'codex', receipts=receipts)
    status_path = OUT / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    engines = {}
    for qid, qpath, bundle in QUESTIONS:
        if status.get(qid, {}).get('state') == 'complete':
            continue
        folder = OUT / qid
        att = folder / 'attempts.json'
        if att.is_file() and len(json.loads(att.read_text(encoding='utf-8'))) >= 2:
            status[qid] = {'state': 'failed', 'reason': '2 attempts used'}
            continue
        if bundle not in engines:
            _r, identity, ranked, count, _p, _v = evidence_budget.open_ranked(
                bundle, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
            pin = PIN if bundle == DEMO else rf.bundle_pin()
            if identity()['indexed_records_sha256'] != pin:
                raise SystemExit(f'Unexpected index {bundle}')
            rows = {r['chunk_id']: r for r in (json.loads(l) for l in (bundle / 'parents.jsonl').read_text(
                encoding='utf-8').splitlines() if l.strip())}
            engines[bundle] = S2Research(ranked=ranked, count=count, tables=ev.TableIndex(rows.values()), generate=guard,
                                         v2=s3_env.v2env.load_v2(), gate=s3_env.v2env.load_gate(),
                                         paper_balance=True, rows=rows)
        question = next(q['question'] for q in json.loads(qpath.read_text(encoding='utf-8')) if q['id'] == qid)
        print('Running', qid, flush=True)
        calls.question = qid
        try:
            engines[bundle].run(question, folder)
            status[qid] = {'state': 'complete'}
        except BudgetExhausted as error:
            status[qid] = {'state': 'stopped', 'reason': str(error)}
            break
        except Exception as error:
            status[qid] = {'state': 'execution_error', 'error': f'{type(error).__name__}: {str(error)[:200]}'}
        status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    print(json.dumps({'status': status, 'calls_used': calls.budget.used()}, indent=1))


def _used():
    import sqlite3
    from contextlib import closing
    path = OUT / 'calls.sqlite3'
    if not path.is_file():
        return 0
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]


if __name__ == '__main__':
    main()

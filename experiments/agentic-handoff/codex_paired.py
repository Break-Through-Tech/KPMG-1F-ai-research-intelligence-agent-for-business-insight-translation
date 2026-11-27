"""Codex-backed paired evaluation (current vs handoff), separate from every Gemini run.

Generation goes through the existing src.codex_generation adapter. It uses the saved ChatGPT login (never an
API key), runs each call in an empty temporary directory with shell, exec and integrations disabled, refuses
tool-using replies, and validates every answer against the schema it was given. The agents then validate again
against their full schemas.

Both arms get quote grounding and the deterministic interpretation policy. Retrieval is the frozen B2 route,
with one shared plan per question and matched initial evidence (gemini_paired.replay_pair).

Operation (one command; re-running the same label resumes):
  - A persistent SQLite call budget is reserved before every model call and survives restarts.
  - A question whose pair finished is never repeated. An unfinished attempt folder is kept as F0x.attempt-N
    and the question is run again.
  - An execution failure on one question is recorded and the run moves on. Budget exhaustion,
    login/authentication, quota or rate limits, and integrity failures stop the run.
  - At the end the scenario report is written automatically.

    python -I codex_paired.py --check pilot     # offline: seal, comparator, CLI flags, login, model listing
    python -I codex_paired.py --run pilot       # live: F01 and F03, at most 18 calls
    python -I codex_paired.py --run full        # live: F01-F10, at most 90 calls
"""
import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / 'experiments/agentic'),
                str(ROOT / 'experiments/measure/fresh-diagnostic-v1')]

MODEL, EFFORT, TIMEOUT = 'gpt-6.1-sol', 'low', 300
LABELS = {  # label: (output directory, questions, call cap = 9 per question)
    'pilot': ('codex-paired-v1-pilot', ('F01', 'F03')),
    'full': ('codex-paired-v1-full', tuple(f'F{i:02d}' for i in range(1, 11))),
}
STOP_CATEGORIES = {'authentication', 'rate_limited', 'configuration', 'forbidden_tool_output'}
STOP_CODES = {'insufficient_quota', 'rate_limit_exceeded', 'model_not_found'}
SEAL_SHA256 = 'd79d8719f53d5822d0ca9f11ebadb391acec6b7d2fe224ef0e288045dafc12dd'


class BudgetExhausted(RuntimeError):
    pass


class Budget:
    """Persistent call reservations: one row per attempted model call, written before the call."""

    def __init__(self, path, cap):
        self.path, self.cap = path, cap
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, at REAL, question TEXT, '
                       'prompt_sha256 TEXT, status TEXT, diagnostic TEXT, seconds REAL, usage TEXT)')

    def used(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]

    def reserve(self, question, prompt):
        with closing(sqlite3.connect(self.path, isolation_level='EXCLUSIVE')) as db, db:
            if db.execute('SELECT COUNT(*) FROM calls').fetchone()[0] >= self.cap:
                raise BudgetExhausted(f'Call cap of {self.cap} reached')
            return db.execute('INSERT INTO calls (at, question, prompt_sha256, status) VALUES (?, ?, ?, ?)',
                              (time.time(), question, sha256(prompt.encode()).hexdigest(), 'started')).lastrowid

    def finish(self, call_id, record):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE calls SET status=?, diagnostic=?, seconds=?, usage=? WHERE id=?',
                       (record.get('status'), json.dumps(record.get('diagnostic')), record.get('elapsed_seconds'),
                        json.dumps(record.get('usage')), call_id))


class CodexCalls:
    """Budgeted wrapper over the adapter's generate; replay_pair sets .stopped on integrity failures."""
    supports_response_schema = True

    def __init__(self, generate, receipts, budget):
        self.generate, self.receipts, self.budget = generate, receipts, budget
        self.question, self.stopped, self.fatal = None, None, None

    def __call__(self, prompt, *, response_schema):
        call_id = self.budget.reserve(self.question, prompt)
        before = len(self.receipts)
        try:
            return self.generate(prompt, response_schema=response_schema)
        except Exception as error:
            diagnostic = getattr(error, 'codex_diagnostic', {}) or {}
            if (diagnostic.get('category') in STOP_CATEGORIES or diagnostic.get('provider_code') in STOP_CODES):
                self.fatal = diagnostic
            raise
        finally:
            record = self.receipts[-1] if len(self.receipts) > before else {'status': 'not_started'}
            self.budget.finish(call_id, record)


def checks(binary):
    """Offline readiness: frozen inputs, comparator, CLI isolation flags and ChatGPT login, model listing."""
    from preflight import verify
    from src.codex_generation import REQUIRED_EXEC_FLAGS
    import subprocess
    sealed = ROOT / 'experiments/measure/fresh-diagnostic-v1'
    if sha256((sealed / 'seal.json').read_bytes()).hexdigest() != SEAL_SHA256:
        raise SystemExit('Frozen seal hash changed.')
    verify()
    for name, digest in json.loads((HERE / 'current-multi-agent.json').read_bytes())['files'].items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise SystemExit(f'Comparator source changed: {name}')
    help_text = subprocess.run([str(binary), 'exec', '--help'], capture_output=True, text=True, timeout=15).stdout
    missing = [flag for flag in REQUIRED_EXEC_FLAGS if flag not in help_text]
    login = subprocess.run([str(binary), 'login', 'status'], capture_output=True, text=True, timeout=15)
    cache = json.loads((Path.home() / '.codex/models_cache.json').read_text(encoding='utf-8'))
    listed = any(m.get('slug') == MODEL and m.get('visibility') == 'list'
                 and any(level.get('effort') == EFFORT for level in m.get('supported_reasoning_levels', []))
                 for m in cache.get('models', []))
    result = {'cli_flags_missing': missing, 'chatgpt_login': 'Logged in using ChatGPT' in login.stdout + login.stderr,
              'model': MODEL, 'effort': EFFORT, 'model_listed': listed, 'model_cache_fetched': cache.get('fetched_at')}
    if missing or not result['chatgpt_login'] or not listed:
        raise SystemExit(f'Not ready: {result}')
    return result


def run(label, *, generate, receipts, retrieve, identity, out_root, pair=None):
    """Run or resume a label. Returns the per-question status map. Injectable for offline tests."""
    from gemini_paired import replay_pair
    pair = pair or replay_pair
    directory, selected = LABELS[label]
    out = out_root / directory
    out.mkdir(parents=True, exist_ok=True)
    budget = Budget(out / 'calls.sqlite3', cap=9 * len(selected))
    calls = CodexCalls(generate, receipts, budget)
    questions = {q['id']: q for q in json.loads(
        (ROOT / 'experiments/measure/fresh-diagnostic-v1/questions.json').read_text(encoding='utf-8'))}
    order = [q for q in questions]  # frozen schedule; arm order alternates by frozen position
    status_path = out / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    for position, qid in enumerate(order):
        if qid not in selected or status.get(qid, {}).get('state') == 'complete':
            continue
        folder = out / qid
        if folder.exists():  # unfinished earlier attempt: keep it, never overwrite
            attempt = 1 + sum(1 for _ in out.glob(f'{qid}.attempt-*'))
            folder.rename(out / f'{qid}.attempt-{attempt}')
        folder.mkdir()
        calls.question, calls.stopped = qid, None
        arm_order = ('current', 'handoff') if position % 2 == 0 else ('handoff', 'current')
        print('Running', qid, flush=True)
        try:
            pair(folder, questions[qid]['question'], retrieve, identity, calls, arm_order,
                 quote_grounding=True, withhold_interpretations=True)
            status[qid] = {'state': 'complete'}
        except BudgetExhausted as error:
            status[qid] = {'state': 'stopped', 'reason': str(error)}
            break
        except Exception as error:
            status[qid] = {'state': 'execution_error', 'error': type(error).__name__,
                           'codex': calls.fatal or None, 'integrity': calls.stopped}
            if calls.fatal or calls.stopped:
                break  # login, quota, rate limit or integrity: later questions would fail the same way
        finally:
            status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    (out / 'run.json').write_text(json.dumps({
        'label': label, 'provider': 'codex_subscription (existing ChatGPT login)', 'model': MODEL,
        'reasoning_effort': EFFORT, 'timeout_seconds': TIMEOUT, 'quote_grounding': True,
        'withhold_interpretations': True, 'questions': list(selected), 'call_cap': budget.cap,
        'calls_used': budget.used(), 'status': status}, indent=1), encoding='utf-8')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', choices=LABELS)
    mode.add_argument('--run', choices=LABELS)
    args = parser.parse_args()
    from prepare import CLI
    ready = checks(CLI)
    label = args.check or args.run
    print(json.dumps({**ready, 'label': label, 'questions': list(LABELS[label][1]),
                      'call_cap': 9 * len(LABELS[label][1])}, indent=1))
    if args.check:
        return
    from preflight import open_route
    from src.codex_generation import create_codex_generate
    from stage_a_report import report
    receipts = []
    generate, _ = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT,
                                        receipts=receipts)
    retrieve, identity = open_route()
    out_root = ROOT / 'data/processed'
    status = run(args.run, generate=generate, receipts=receipts, retrieve=retrieve, identity=identity,
                 out_root=out_root)
    out = out_root / LABELS[args.run][0]
    (out / 'report.json').write_text(json.dumps(report(out), indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(status, indent=1))
    print(f'Report: {out / "report.json"}')


if __name__ == '__main__':
    main()

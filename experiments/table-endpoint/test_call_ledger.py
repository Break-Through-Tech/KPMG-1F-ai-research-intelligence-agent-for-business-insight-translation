"""Model-free tests for the cross-process call ledger and the capped wrapper that uses it.

Run:  py -3.14 -I -B experiments/table-endpoint/test_call_ledger.py
Child processes stand in for independently started backends. The provider is a fake module; no
model is ever called.
"""
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import call_ledger  # noqa: E402
from call_ledger import CallLedger, LedgerError  # noqa: E402

CHILD = textwrap.dedent(r'''
import os, sys, time, types
sys.path.insert(0, {here!r}); sys.path.insert(0, {root!r})
fake = types.ModuleType('src.codex_generation')
def create_codex_generate(**kwargs):
    def inner(prompt, response_schema=None):
        if {crash!r}:
            os._exit(3)          # simulated crash while the provider call is in flight
        time.sleep(0.2)
        return '{{}}'
    return inner, {{}}
fake.create_codex_generate = create_codex_generate
sys.modules['src.codex_generation'] = fake
import capped_codex_ui as wrapper
wrapper.configure(40, {log!r}, ledger={ledger!r}, authorized={authorized}, experiment={experiment!r}, experiment_cap={cap!r})
generate = wrapper.create()[0]
time.sleep(max(0, {start} - time.time()))
try:
    generate('x'); print('CALLED')
except Exception as error:
    print('REFUSED', error)
''')


@contextmanager
def workdir(test):
    """A temporary folder removed AFTER the test's ledger cleanups (cleanups run last-in, first-out)."""
    path = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, path, True)
    yield path


def seed_file(folder, count, *, tail=''):
    path = Path(folder) / 'seed.jsonl'
    lines = [json.dumps({'call': i + 1, 'at': f'2026-11-17T00:{i:02d}:00', 'outcome': 'ok' if i % 5 else 'provider_error'})
             for i in range(count)]
    path.write_text(''.join(line + '\n' for line in lines) + tail, encoding='utf-8')
    return path


def child(folder, ledger, *, start=0, crash=False, experiment=None, cap=None, authorized=40):
    code = CHILD.format(here=str(HERE), root=str(ROOT), log=str(Path(folder) / 'session.jsonl'), ledger=str(ledger),
                        authorized=authorized, experiment=experiment, cap=cap, start=start, crash=crash)
    return subprocess.Popen([sys.executable, '-I', '-B', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def sql(ledger, statement, *, write=False):
    connection = sqlite3.connect(ledger, isolation_level=None)
    try:
        if write:
            connection.execute('PRAGMA ignore_check_constraints = ON')
        return connection.execute(statement).fetchall()
    finally:
        connection.close()


def rows(ledger):
    return sql(ledger, 'SELECT id, state, experiment FROM calls')


def opened(test, *args, **kwargs):
    ledger = CallLedger(*args, **kwargs)
    test.addCleanup(ledger.close)
    return ledger


class Seed(unittest.TestCase):
    def test_init_imports_every_seed_record_with_its_outcome(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            status = call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 20))
            self.assertEqual((status['used'], status['remaining'], status['integrity']), (20, 20, 'ok'))
            self.assertEqual(status['states'], {'completed': 16, 'failed': 4})
            self.assertEqual(len({r[0] for r in rows(ledger)}), 20)  # unique IDs

    def test_init_never_overwrites(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 3))
            with self.assertRaisesRegex(LedgerError, 'never recreated'):
                call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 0))
            self.assertEqual(len(rows(ledger)), 3)

    def test_truncated_malformed_or_blank_seed_is_refused(self):
        with workdir(self) as tmp:
            for tail in ('{"call": 21, "at": "2026-', 'not json\n', '\n'):
                ledger = Path(tmp) / f'l{abs(hash(tail))}.sqlite3'
                with self.assertRaises(LedgerError, msg=repr(tail)):
                    call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 5, tail=tail))
                self.assertFalse(ledger.exists())


class CrossProcess(unittest.TestCase):
    def test_concurrent_processes_never_exceed_the_authorization(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 37))
            start = time.time() + 3
            procs = [child(tmp, ledger, start=start) for _ in range(8)]
            results = [p.communicate(timeout=120)[0].strip() for p in procs]
            self.assertEqual(sum(r.startswith('CALLED') for r in results), 3, results)
            self.assertEqual(len(rows(ledger)), 40)
            self.assertTrue(all('Cumulative authorized cap of 40' in r for r in results if r.startswith('REFUSED')), results)

    def test_last_slot_goes_to_exactly_one_of_two_processes(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 39))
            start = time.time() + 3
            results = [p.communicate(timeout=120)[0].strip() for p in [child(tmp, ledger, start=start) for _ in range(2)]]
            self.assertEqual(sorted(r.split()[0] for r in results), ['CALLED', 'REFUSED'], results)

    def test_experiment_cap_is_shared_across_processes_and_never_raised(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 20))
            start = time.time() + 3
            procs = [child(tmp, ledger, start=start, experiment='ab-test', cap=2) for _ in range(4)]
            results = [p.communicate(timeout=120)[0].strip() for p in procs]
            self.assertEqual(sum(r.startswith('CALLED') for r in results), 2, results)
            self.assertTrue(any('Experiment cap of 2' in r for r in results), results)
            with self.assertRaisesRegex(LedgerError, 'never changed'):
                opened(self, ledger, authorized=40, experiment='ab-test', experiment_cap=5)
            self.assertEqual(len(rows(ledger)), 22)  # the overall count includes experiment calls

    def test_crash_during_a_call_leaves_a_counted_unresolved_reservation(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 20))
            crashed = child(tmp, ledger, crash=True)
            crashed.communicate(timeout=120)
            self.assertEqual(crashed.returncode, 3)
            usage = opened(self, ledger, authorized=40).usage()
            self.assertEqual((usage['used'], usage['states']['unresolved'], usage['remaining']), (21, 1, 19))

    def test_crash_inside_the_reservation_transaction_rolls_back_cleanly(self):
        with workdir(self) as tmp:
            ledger = Path(tmp) / 'ledger.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, 20))
            code = textwrap.dedent(f'''
                import os, sqlite3
                c = sqlite3.connect({str(ledger)!r}, isolation_level=None)
                c.execute('BEGIN IMMEDIATE')
                c.execute("INSERT INTO calls (id, state, reserved_at) VALUES ('half', 'reserved', 'now')")
                os._exit(4)  # crash before COMMIT
            ''')
            self.assertEqual(subprocess.run([sys.executable, '-I', '-B', '-c', code]).returncode, 4)
            self.assertEqual(len(rows(ledger)), 20)  # nothing half-written survives
            ledger_after = opened(self, ledger, authorized=40)
            ledger_after.finish(ledger_after.reserve(), 'completed')  # and the lock was released
            self.assertEqual(len(rows(ledger)), 21)


class FailClosed(unittest.TestCase):
    def make(self, tmp, count=20):
        ledger = Path(tmp) / 'ledger.sqlite3'
        call_ledger.init(ledger, authorized=40, seed=seed_file(tmp, count))
        return ledger

    def test_missing_or_jsonl_ledger_is_refused(self):
        sys.modules.pop('capped_codex_ui', None)
        import capped_codex_ui as wrapper
        with workdir(self) as tmp:
            with self.assertRaises(ValueError):
                wrapper.configure(40, Path(tmp) / 'log', ledger=Path(tmp) / 'missing.sqlite3', authorized=40)
            jsonl = seed_file(tmp, 3)
            with self.assertRaisesRegex(ValueError, 'no longer accepted'):
                wrapper.configure(40, Path(tmp) / 'log', ledger=jsonl, authorized=40)

    def test_changed_authorization_is_refused(self):
        with workdir(self) as tmp:
            with self.assertRaisesRegex(LedgerError, 'authorizes 40'):
                opened(self, self.make(tmp), authorized=60)

    def test_deleted_rows_are_detected_as_a_reset(self):
        with workdir(self) as tmp:
            ledger = self.make(tmp)
            sql(ledger, "DELETE FROM calls WHERE id IN (SELECT id FROM calls LIMIT 5)", write=True)
            with self.assertRaisesRegex(LedgerError, 'fewer records'):
                opened(self, ledger, authorized=40)

    def test_unknown_state_is_refused(self):
        with workdir(self) as tmp:
            ledger = self.make(tmp)
            sql(ledger, "UPDATE calls SET state = 'refunded' WHERE rowid = 1", write=True)
            with self.assertRaisesRegex(LedgerError, 'unknown call state|integrity check'):
                opened(self, ledger, authorized=40)

    def test_corrupted_file_is_refused(self):
        with workdir(self) as tmp:
            ledger = self.make(tmp, count=30)
            data = bytearray(ledger.read_bytes())
            data[2048:4096] = b'\xff' * 2048
            ledger.write_bytes(bytes(data))
            with self.assertRaises(LedgerError):
                opened(self, ledger, authorized=40)

    def test_wrapper_refuses_calls_when_the_ledger_breaks_after_start(self):
        import types
        fake = types.ModuleType('src.codex_generation')
        fake.create_codex_generate = lambda **k: ((lambda prompt, response_schema=None: '{}'), {})
        saved = sys.modules.get('src.codex_generation')
        sys.modules['src.codex_generation'] = fake
        try:
            with workdir(self) as tmp:
                ledger = self.make(tmp)
                sys.modules.pop('capped_codex_ui', None)
                import capped_codex_ui as wrapper
                wrapper.configure(40, Path(tmp) / 'log', ledger=ledger, authorized=40)
                generate = wrapper.create()[0]
                generate('ok')
                sql(ledger, "DELETE FROM calls WHERE id IN (SELECT id FROM calls LIMIT 2)", write=True)
                with self.assertRaisesRegex(LedgerError, 'fewer records'):
                    generate('refused')
                self.assertEqual(wrapper.usage()['remaining'], 0)
                wrapper.LEDGER.close()
        finally:
            if saved is None:
                sys.modules.pop('src.codex_generation', None)
            else:
                sys.modules['src.codex_generation'] = saved

    def test_failed_and_completed_states_are_recorded(self):
        with workdir(self) as tmp:
            ledger = opened(self, self.make(tmp), authorized=40)
            first, second = ledger.reserve(), ledger.reserve()
            ledger.finish(first, 'completed', outcome='ok', seconds=1.0)
            ledger.finish(second, 'failed', outcome='provider_error', seconds=300.0)
            with self.assertRaises(LedgerError):
                ledger.finish(first, 'failed')  # a finished reservation cannot be rewritten
            self.assertEqual(ledger.usage()['states'], {'reserved': 0, 'completed': 17, 'failed': 5, 'unresolved': 0})


class RealLedger(unittest.TestCase):
    PATH = Path(r'D:\KPMG-demo-corpus\table-endpoint-exp\codex-authorization-40.ledger.sqlite3')

    @unittest.skipUnless(PATH.is_file(), 'local authorization ledger not present')
    def test_the_real_ledger_is_intact_at_20_of_40(self):
        status = call_ledger.status(self.PATH)  # read-only
        self.assertEqual((status['integrity'], status['authorized'], status['used'], status['remaining']), ('ok', 40, 20, 20))
        self.assertEqual(status['seed_records'], 20)


if __name__ == '__main__':
    unittest.main(verbosity=1)

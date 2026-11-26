"""Model-free tests for audit #3 ledger findings: the ab-agentic-1 profile (14-call A/B cap) and the
ledger initialization race. Uses only disposable copies of the real ledger; the real ledger is read, never written.

Run:  py -3.14 -I -B experiments/table-endpoint/test_ab_profile.py
"""
import hashlib
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

REAL = Path(r'D:\KPMG-demo-corpus\table-endpoint-exp\codex-authorization-40.ledger.sqlite3')
PROFILE = ['--profile', 'ab-agentic-1', '--authorized-calls', '40', '--experiment', 'ab-agentic-1', '--experiment-cap', '14']
DUMMY = ['--export', 'unused', '--bundle', 'unused', '--encoder', 'unused', '--reranker', 'unused', '--library', 'unused']

# A child that sets up its call budget EXACTLY as the launcher does (build_parser, validate_budget,
# configure_call_budget), then attempts calls through the real capped wrapper with a fake provider.
CHILD = textwrap.dedent(r'''
import sys, time, types
sys.path.insert(0, {here!r}); sys.path.insert(0, {root!r})
fake = types.ModuleType('src.codex_generation')
fake.create_codex_generate = lambda **k: ((lambda prompt, response_schema=None: (time.sleep(0.05), '{{}}')[1]), {{}})
sys.modules['src.codex_generation'] = fake
{stand_in}
import live_backend, capped_codex_ui
parser = live_backend.build_parser()
args = parser.parse_args({argv!r})
try:
    live_backend.validate_budget(parser, args)
    live_backend.configure_call_budget(args, capped_codex_ui)
except SystemExit as error:
    print('LAUNCH_REFUSED'); sys.exit(0)
except Exception as error:
    print('LAUNCH_REFUSED', error); sys.exit(0)
generate = capped_codex_ui.create()[0]
time.sleep(max(0, {start} - time.time()))
made = 0
for _ in range({attempts}):
    try:
        generate('x'); made += 1
    except Exception as error:
        last = str(error)
print('CALLS', made)
''')


@contextmanager
def workdir(test):
    path = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, path, True)
    yield Path(path)


def ledger_copy(folder):
    copy = folder / 'ledger.sqlite3'
    shutil.copy(REAL, copy)
    return copy


def stand_in_code(path):
    """TEST-ONLY: make a disposable copy stand in for the canonical ledger inside one child process.

    This is exactly the trust boundary the profile documents: the copy is accepted only because this test edits
    the profile in memory. Without it (stand_in=None) the real launcher refuses every copy.
    """
    if path is None:
        return ''
    return (f"import sys; sys.path.insert(0, {str(HERE)!r}); from pathlib import Path; import ab_profile; "
            f"ab_profile.PROFILES['ab-agentic-1']['ledger_path'] = Path({str(path)!r})")


def launch(ledger, *flags, budget_only=True, stand_in='same'):
    stand_in = ledger if stand_in == 'same' else stand_in
    argv = [*DUMMY, '--call-ledger', str(ledger), *flags] + (['--budget-check-only'] if budget_only else [])
    code = f"{stand_in_code(stand_in)}\nimport sys; sys.path.insert(0, {str(HERE)!r})\nimport live_backend\nlive_backend.main({argv!r})"
    return subprocess.run([sys.executable, '-I', '-B', '-c', code], capture_output=True, text=True, timeout=120, cwd=str(HERE))


def child(ledger, argv_tail, *, attempts=1, start=0, max_calls=40, stand_in='same'):
    stand_in = ledger if stand_in == 'same' else stand_in
    # The session log goes beside the disposable ledger, never into the repository.
    argv = [*DUMMY, '--call-ledger', str(ledger), '--call-log', str(Path(ledger).parent / 'session-calls.jsonl'),
            '--max-calls', str(max_calls), *argv_tail]
    code = CHILD.format(here=str(HERE), root=str(ROOT), argv=argv, start=start, attempts=attempts,
                        stand_in=stand_in_code(stand_in))
    return subprocess.Popen([sys.executable, '-I', '-B', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            cwd=str(HERE))


def calls_made(output):
    return int(output.split('CALLS')[1]) if 'CALLS' in output else 0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@unittest.skipUnless(REAL.is_file(), 'the authorization ledger is not on this machine')
class Launcher(unittest.TestCase):
    def test_real_ledger_is_untouched_by_this_suite(self):
        before = sha(REAL)
        status = call_ledger.status(REAL)
        self.assertEqual((status['used'], status['authorized'], status['locked_experiment']), (20, 40, None))
        self.addCleanup(lambda: self.assertEqual(sha(REAL), before))

    def test_exact_profile_is_accepted_read_only(self):
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            before = sha(ledger)
            result = launch(ledger, *PROFILE)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['ledger']['remaining'], 20)
            self.assertEqual(sha(ledger), before)  # the budget check writes nothing

    def test_omitted_renamed_or_changed_profile_flags_are_refused_before_loading(self):
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            cases = {
                'experiment omitted': ['--profile', 'ab-agentic-1', '--authorized-calls', '40'],
                'cap omitted': ['--profile', 'ab-agentic-1', '--authorized-calls', '40', '--experiment', 'ab-agentic-1'],
                'experiment renamed': ['--profile', 'ab-agentic-1', '--authorized-calls', '40', '--experiment', 'ab-agentic-2', '--experiment-cap', '14'],
                'cap raised': ['--profile', 'ab-agentic-1', '--authorized-calls', '40', '--experiment', 'ab-agentic-1', '--experiment-cap', '20'],
                'authorization changed': ['--profile', 'ab-agentic-1', '--authorized-calls', '50', '--experiment', 'ab-agentic-1', '--experiment-cap', '14'],
                'profile experiment without the profile': ['--authorized-calls', '40', '--experiment', 'ab-agentic-1', '--experiment-cap', '14'],
            }
            for name, flags in cases.items():
                with self.subTest(name):
                    result = launch(ledger, *flags)
                    self.assertEqual(result.returncode, 2, (name, result.stdout, result.stderr))
                    self.assertNotIn('Traceback', result.stderr)

    def test_another_ledger_is_refused_for_the_profile(self):
        with workdir(self) as tmp:
            seed = tmp / 'seed.jsonl'
            seed.write_text('{"at": "2026-11-17T00:00:00", "outcome": "ok"}\n', encoding='utf-8')
            other = tmp / 'other.sqlite3'
            call_ledger.init(other, authorized=40, seed=seed)
            result = launch(other, *PROFILE)
            self.assertEqual(result.returncode, 2)
            self.assertIn('not the approved authorization ledger', result.stderr)

    def test_cap_holds_across_restarts_and_omission_or_rename_after_first_launch(self):
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            first = child(ledger, PROFILE, attempts=10).communicate(timeout=120)[0]
            self.assertEqual(calls_made(first), 10, first)
            restart = child(ledger, PROFILE, attempts=10).communicate(timeout=120)[0]
            self.assertEqual(calls_made(restart), 4, restart)  # 14 in total, across two processes
            # The ledger is now locked to the profile: every bypass fails closed.
            for flags in (['--authorized-calls', '40'],
                          ['--authorized-calls', '40', '--experiment', 'renamed-run', '--experiment-cap', '14']):
                out = child(ledger, flags, attempts=3).communicate(timeout=120)[0]
                self.assertIn('LAUNCH_REFUSED', out, flags)
                self.assertEqual(launch(ledger, *flags).returncode, 2, flags)
            for kwargs in ({}, {'experiment': 'renamed-run', 'experiment_cap': 14}):
                # Refused either because the ledger is locked or (audit #5 hardening) because the name is not approved.
                with self.assertRaisesRegex(LedgerError, 'locked to experiment|not approved'):
                    CallLedger(ledger, authorized=40, **kwargs)
            status = call_ledger.status(ledger)
            self.assertEqual((status['used'], status['experiment_used'], status['locked_experiment']), (34, {'ab-agentic-1': 14}, 'ab-agentic-1'))

    def test_concurrent_profile_processes_share_one_14_call_cap(self):
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            start = time.time() + 4
            procs = [child(ledger, PROFILE, attempts=5, start=start) for _ in range(5)]
            outputs = [p.communicate(timeout=180)[0] for p in procs]
            self.assertEqual(sum(calls_made(o) for o in outputs), 14, outputs)
            status = call_ledger.status(ledger)
            self.assertEqual((status['used'], status['experiment_caps']), (34, {'ab-agentic-1': 14}))

    def test_a_process_opened_before_the_lock_cannot_spend_after_it(self):
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            early = CallLedger(ledger, authorized=40)  # opened before any profile launch
            self.addCleanup(early.close)
            out = child(ledger, PROFILE, attempts=1).communicate(timeout=120)[0]
            self.assertEqual(calls_made(out), 1, out)
            with self.assertRaisesRegex(LedgerError, 'locked to experiment'):
                early.reserve()

    def test_overall_authorization_still_applies_inside_an_experiment(self):
        with workdir(self) as tmp:
            seed = tmp / 'seed.jsonl'
            seed.write_text(''.join(json.dumps({'at': f't{i}', 'outcome': 'ok'}) + '\n' for i in range(35)), encoding='utf-8')
            ledger = tmp / 'l.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed)
            capped = CallLedger(ledger, authorized=40, experiment='trial', experiment_cap=14, lock_experiment=True)
            self.addCleanup(capped.close)
            made = 0
            for _ in range(14):
                try:
                    capped.finish(capped.reserve(), 'completed'); made += 1
                except LedgerError as error:
                    self.assertIn('Cumulative authorized cap of 40', str(error))
            self.assertEqual(made, 5)


class LedgerLevelLock(unittest.TestCase):
    """Codex's original probe used the ledger API directly, not the launcher: the cap must hold there too."""

    def test_registering_an_experiment_locks_the_ledger_even_without_the_lock_flag(self):
        with workdir(self) as tmp:
            seed = tmp / 'seed.jsonl'
            seed.write_text(''.join(json.dumps({'at': f't{i}', 'outcome': 'ok'}) + '\n' for i in range(20)), encoding='utf-8')
            ledger = tmp / 'l.sqlite3'
            call_ledger.init(ledger, authorized=40, seed=seed)
            # A non-approved experiment name: the approved one is refused outside the canonical ledger (audit #4).
            capped = CallLedger(ledger, authorized=40, experiment='trial-1', experiment_cap=14)
            for _ in range(14):
                capped.finish(capped.reserve(), 'completed')
            with self.assertRaisesRegex(LedgerError, 'Experiment cap of 14'):
                capped.reserve()
            capped.close()
            for kwargs in ({}, {'experiment': 'trial-2', 'experiment_cap': 14}):
                with self.assertRaisesRegex(LedgerError, 'locked to experiment'):
                    CallLedger(ledger, authorized=40, **kwargs)
            self.assertEqual(call_ledger.status(ledger)['used'], 34)


REAL_SEED = Path(r'D:\KPMG-demo-corpus\table-endpoint-exp\codex-authorization-40.ledger.jsonl')


@unittest.skipUnless(REAL.is_file() and REAL_SEED.is_file(), 'the authorization ledger is not on this machine')
class OneAuthoritativeLedger(unittest.TestCase):
    """Audit #4 HIGH 1: a second ledger from the approved seed must not get its own 14-call allocation."""

    def test_codex_two_database_bypass_is_refused_at_init(self):
        with workdir(self) as tmp:
            for name in ('first.sqlite3', 'second.sqlite3'):
                with self.assertRaisesRegex(LedgerError, 'a second ledger is never created'):
                    call_ledger.init(tmp / name, authorized=40, seed=REAL_SEED)
                self.assertFalse((tmp / name).exists())

    def test_two_copies_of_the_canonical_file_yield_one_14_call_allocation(self):
        # Copies made outside the application (the trust boundary): only the file the profile names is accepted.
        with workdir(self) as tmp:
            first, second = tmp / 'first.sqlite3', tmp / 'second.sqlite3'
            shutil.copy(REAL, first)
            shutil.copy(REAL, second)
            made = 0
            for ledger in (first, second):
                out = child(ledger, PROFILE, attempts=20, stand_in=first).communicate(timeout=120)[0]
                made += calls_made(out)
                if ledger == second:
                    self.assertIn('LAUNCH_REFUSED', out)
            self.assertEqual(made, 14)
            with self.assertRaisesRegex(LedgerError, 'Only the canonical ledger'):
                CallLedger(second, authorized=40, experiment='ab-agentic-1', experiment_cap=14)
            self.assertEqual(call_ledger.status(second)['used'], 20)

    def test_the_real_launcher_refuses_any_file_but_the_canonical_ledger(self):
        with workdir(self) as tmp:
            copy = ledger_copy(tmp)
            result = launch(copy, *PROFILE, stand_in=None)  # no test stand-in: the shipped profile
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('Only the canonical ledger', result.stderr)

    def test_a_recreated_or_identity_less_ledger_is_refused(self):
        with workdir(self) as tmp:
            recreated = ledger_copy(tmp)
            connection = sqlite3.connect(recreated)
            connection.execute("UPDATE meta SET value = '2026-12-01T00:00:00' WHERE key = 'created_at'")
            connection.commit(); connection.close()
            self.assertIn('different creation', launch(recreated, *PROFILE).stderr)
            missing = tmp / 'missing.sqlite3'
            shutil.copy(REAL, missing)
            connection = sqlite3.connect(missing)
            connection.execute("DELETE FROM meta WHERE key = 'created_at'")
            connection.commit(); connection.close()
            self.assertIn('no identity', launch(missing, *PROFILE).stderr)

    def test_closing_the_allocation_frees_the_remaining_six_and_never_reopens_it(self):
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            self.assertEqual(calls_made(child(ledger, PROFILE, attempts=20).communicate(timeout=120)[0]), 14)
            with self.assertRaisesRegex(LedgerError, 'locked to experiment'):
                CallLedger(ledger, authorized=40)  # still locked until the owner closes it
            status = call_ledger.close_experiment(ledger, authorized=40, experiment='ab-agentic-1')
            self.assertEqual((status['used'], status['remaining'], status['locked_experiment'], status['closed_experiments']),
                             (34, 6, None, ['ab-agentic-1']))
            out = child(ledger, PROFILE, attempts=3).communicate(timeout=120)[0]
            self.assertIn('LAUNCH_REFUSED', out)  # the closed allocation never reopens
            with self.assertRaisesRegex(LedgerError, 'closed'):
                CallLedger(ledger, authorized=40, experiment='ab-agentic-1', experiment_cap=14)
            # Audit #5 hardening: a new allocation name must first be listed in ab_profile.AUTHORIZATIONS.
            with self.assertRaisesRegex(LedgerError, 'not approved'):
                CallLedger(ledger, authorized=40, experiment='separately-approved', experiment_cap=6)
            later = CallLedger(ledger, authorized=40)  # the remaining calls, without an experiment, still under the 40
            self.addCleanup(later.close)
            for _ in range(6):
                later.finish(later.reserve(), 'completed')
            with self.assertRaisesRegex(LedgerError, 'Cumulative authorized cap of 40'):
                later.reserve()

    def test_lookalike_experiment_names_are_refused_on_the_approved_ledger(self):
        # Audit #5: before any profile run, "AB-AGENTIC-1" (cap 20) could lock the approved ledger and block the A/B.
        with workdir(self) as tmp:
            ledger = ledger_copy(tmp)
            for name in ('AB-AGENTIC-1', 'ab-agentic-1 ', 'ab_agentic_1', 'ab-agentic-2'):
                with self.subTest(name):
                    with self.assertRaisesRegex(LedgerError, 'not approved'):
                        CallLedger(ledger, authorized=40, experiment=name, experiment_cap=20)
                    result = launch(ledger, '--authorized-calls', '40', '--experiment', name, '--experiment-cap', '20')
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn('not approved', result.stderr)
            status = call_ledger.status(ledger)
            self.assertEqual((status['used'], status['experiment_caps'], status['locked_experiment']), (20, {}, None))
            # The approved profile still launches, and plain use without an experiment is unchanged.
            self.assertEqual(launch(ledger, *PROFILE).returncode, 0)
            self.assertEqual(launch(ledger, '--authorized-calls', '40').returncode, 0)

    def test_research_only_profile(self):
        sys.path.insert(0, str(ROOT / 'experiments' / 'agentic'))
        import ab_profile
        self.assertTrue(ab_profile.PROFILES['ab-agentic-1']['research_only'])


class InitRace(unittest.TestCase):
    def seed(self, folder, name, count):
        path = folder / name
        path.write_text(''.join(json.dumps({'at': f'{name}-{i}', 'outcome': 'ok'}) + '\n' for i in range(count)), encoding='utf-8')
        return path

    def test_a_ledger_published_during_init_is_never_overwritten(self):
        with workdir(self) as tmp:
            target = tmp / 'race.sqlite3'
            mine, theirs = self.seed(tmp, 'mine.jsonl', 1), self.seed(tmp, 'theirs.jsonl', 5)
            original = call_ledger._connect
            state = {'raced': False}

            def connect(path):
                # Codex's interleaving: the competitor publishes after our existence check, before our publish.
                if not state['raced'] and str(path).endswith('.creating'):
                    state['raced'] = True
                    call_ledger._connect = original
                    call_ledger.init(target, authorized=40, seed=theirs)
                    call_ledger._connect = connect
                return original(path)
            call_ledger._connect = connect
            try:
                with self.assertRaisesRegex(LedgerError, 'appeared during initialization'):
                    call_ledger.init(target, authorized=40, seed=mine)
            finally:
                call_ledger._connect = original
            self.assertEqual(call_ledger.status(target)['used'], 5)  # the competitor's history is preserved
            self.assertEqual([p.name for p in tmp.iterdir() if p.name.endswith('.creating')], [])

    def test_competing_initializer_processes_publish_exactly_one_ledger(self):
        with workdir(self) as tmp:
            target = tmp / 'race.sqlite3'
            seeds = [self.seed(tmp, f's{i}.jsonl', i + 1) for i in range(4)]
            start = time.time() + 3
            code = textwrap.dedent('''
                import sys, time
                sys.path.insert(0, {here!r})
                import call_ledger
                time.sleep(max(0, {start} - time.time()))
                try:
                    call_ledger.init({target!r}, authorized=40, seed={seed!r}); print('PUBLISHED', {count})
                except call_ledger.LedgerError as error:
                    print('REFUSED')
            ''')
            procs = [subprocess.Popen([sys.executable, '-I', '-B', '-c', code.format(here=str(HERE), start=start, target=str(target),
                                                                                     seed=str(seed), count=i + 1)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i, seed in enumerate(seeds)]
            outputs = [p.communicate(timeout=120)[0].strip() for p in procs]
            published = [o for o in outputs if o.startswith('PUBLISHED')]
            self.assertEqual(len(published), 1, outputs)
            self.assertEqual(call_ledger.status(target)['used'], int(published[0].split()[1]))  # the winner's records, intact
            self.assertEqual([p.name for p in tmp.iterdir() if p.name.endswith('.creating')], [])

    def test_init_refuses_an_existing_ledger_and_keeps_it(self):
        with workdir(self) as tmp:
            target = tmp / 'l.sqlite3'
            call_ledger.init(target, authorized=40, seed=self.seed(tmp, 'a.jsonl', 3))
            before = sha(target)
            with self.assertRaises(LedgerError):
                call_ledger.init(target, authorized=40, seed=self.seed(tmp, 'b.jsonl', 1))
            self.assertEqual(sha(target), before)


if __name__ == '__main__':
    unittest.main(verbosity=1)

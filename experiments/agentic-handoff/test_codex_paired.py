"""Offline tests for the Codex paired runner: scripted adapter, real replay_pair, orchestrators and checks."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import codex_paired
from agents import VERIFIER_PROMPT
from stage_a_report import report
from test_agentic import Provider, plan, verdicts
from test_quote_grounding import NODES, PACKET, SPLIT, reply
from test_scope_review import MISATTRIBUTED

MISATTRIBUTED_PROSE = {**MISATTRIBUTED, 'support': [{'chunk_id': 'prose', 'quote':
                       'This improvement underscores the MultiFinRAG framework�s ability to retrieve relevant trunks'}]}


class FakeAdapter:
    """Behaves like create_codex_generate: appends a receipt per call, raises with codex_diagnostic on failure."""
    supports_response_schema = True

    def __init__(self, fail_on=None):
        self.receipts, self.calls, self.fail_on = [], [], fail_on or {}

    def __call__(self, prompt, *, response_schema=None):
        role = Provider.role(prompt)
        self.calls.append(role)
        record = {'provider': 'codex_subscription', 'status': 'started'}
        self.receipts.append(record)
        failure = self.fail_on.get(len(self.calls))
        if failure:
            record.update(status='failed', diagnostic=failure)
            error = RuntimeError('Codex generation failed')
            error.codex_diagnostic = failure
            raise error
        if role == 'plan':
            text = json.dumps(plan())
        elif role == 'research':
            text = reply(NODES, SPLIT, MISATTRIBUTED_PROSE)
        else:
            claims = json.loads(prompt[len(VERIFIER_PROMPT):])['claims']
            text = json.dumps(verdicts(*[('supported', [])] * len(claims)))
        record.update(status='ok', usage=[{'input_tokens': 1}], elapsed_seconds=0.01)
        return text


def go(root, adapter, label='pilot'):
    return codex_paired.run(label, generate=adapter, receipts=adapter.receipts,
                            retrieve=lambda q, k: [dict(p) for p in PACKET],
                            identity=lambda: {'indexed_records_sha256': 'fixture'}, out_root=root)


def calls_used(root, label='pilot'):
    return codex_paired.Budget(root / codex_paired.LABELS[label][0] / 'calls.sqlite3', 18).used()


class Runner(unittest.TestCase):
    def test_pilot_completes_with_grounding_and_policy_in_both_arms(self):
        with TemporaryDirectory() as temp:
            root, adapter = Path(temp), FakeAdapter()
            status = go(root, adapter)
            self.assertEqual(status, {'F01': {'state': 'complete'}, 'F03': {'state': 'complete'}})
            self.assertEqual(calls_used(root), 10)  # per question: shared plan + 2 x (draft, verify)
            out = root / 'codex-paired-v1-pilot'
            for q, arms in report(out)['questions'].items():
                for arm in arms:
                    rows = {r['text']: r for r in arm['claims'] if r['field'] == 'claims'}
                    self.assertEqual(rows[SPLIT['text']]['outcome'], 'published')  # elided quote recovered
                    self.assertIn('withheld by policy', rows[MISATTRIBUTED['text']]['held_reason'])
            run_info = json.loads((out / 'run.json').read_text())
            self.assertEqual((run_info['model'], run_info['reasoning_effort'], run_info['call_cap']), ('gpt-6.1-sol', 'low', 18))

    def test_rerun_never_repeats_completed_questions(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            go(root, FakeAdapter())
            again = FakeAdapter()
            go(root, again)
            self.assertEqual((again.calls, calls_used(root)), ([], 10))

    def test_one_failed_question_is_recorded_and_the_run_continues_then_resumes_only_that_question(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            status = go(root, FakeAdapter(fail_on={2: {'category': 'timeout'}}))  # F01 draft times out
            self.assertEqual(status['F01']['state'], 'execution_error')
            self.assertEqual(status['F03']['state'], 'complete')
            resumed = FakeAdapter()
            status = go(root, resumed)
            self.assertEqual(status['F01']['state'], 'complete')
            out = root / 'codex-paired-v1-pilot'
            self.assertTrue((out / 'F01.attempt-1').is_dir())  # failed attempt preserved
            self.assertEqual(resumed.calls.count('plan'), 1)  # only F01 ran again

    def test_quota_or_login_errors_stop_the_run(self):
        for diagnostic in ({'category': 'rate_limited', 'http_status': 429},
                           {'category': 'cli_exit', 'provider_code': 'insufficient_quota'},
                           {'category': 'authentication', 'http_status': 401}):
            with self.subTest(diagnostic=diagnostic), TemporaryDirectory() as temp:
                root = Path(temp)
                status = go(root, FakeAdapter(fail_on={1: diagnostic}))
                self.assertEqual(list(status), ['F01'])  # F03 never started
                self.assertEqual(status['F01']['codex'], diagnostic)

    def test_call_cap_is_persistent_across_restarts(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            original = codex_paired.LABELS['pilot']
            codex_paired.LABELS['pilot'] = (original[0], ('F01',))  # cap 9; F01 alone needs 5
            try:
                go(root, FakeAdapter(fail_on={2: {'category': 'timeout'}}))  # 2 calls spent
                go(root, FakeAdapter(fail_on={2: {'category': 'timeout'}}))  # 4 spent
                status = go(root, FakeAdapter())                              # 5 available: completes
                self.assertEqual(status['F01']['state'], 'complete')
                self.assertEqual(calls_used(root), 9)
                codex_paired.LABELS['pilot'] = (original[0], ('F01', 'F03'))  # cap 18 now, budget shared
            finally:
                codex_paired.LABELS['pilot'] = original

    def test_every_call_is_reserved_before_it_is_made_and_receipts_are_persisted(self):
        with TemporaryDirectory() as temp:
            root, adapter = Path(temp), FakeAdapter(fail_on={2: {'category': 'timeout'}})
            go(root, adapter)
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(root / 'codex-paired-v1-pilot' / 'calls.sqlite3')) as db:
                rows = db.execute('SELECT question, status, diagnostic FROM calls ORDER BY id').fetchall()
            self.assertEqual(len(rows), len(adapter.calls))
            self.assertEqual(rows[1][1:], ('failed', json.dumps({'category': 'timeout'})))


class Adapter(unittest.TestCase):
    """The real adapter's isolation flags, checked without starting the CLI for a model call."""

    def test_command_disables_tools_and_requires_chatgpt_login(self):
        import inspect
        from src import codex_generation
        source = inspect.getsource(codex_generation.create_codex_generate)
        for needle in ("'--sandbox', 'read-only'", 'web_search="disabled"', 'approval_policy="never"',
                       "'--ignore-user-config'", "'--ephemeral'", "'--output-schema'",
                       "'Logged in using ChatGPT'", 'Draft202012Validator(response_schema).validate'):
            self.assertIn(needle, source)
        for feature in ('shell_tool', 'unified_exec', 'apps', 'plugins', 'multi_agent', 'browser_use', 'computer_use'):
            self.assertIn(feature, codex_generation.DISABLED_FEATURES)

    def test_labels_are_separate_from_every_gemini_directory(self):
        from gemini_paired import STAGED
        gemini = {entry[0] for entry in STAGED.values()}
        self.assertFalse({d for d, _ in codex_paired.LABELS.values()} & gemini)
        self.assertTrue(all(d.startswith('codex-') for d, _ in codex_paired.LABELS.values()))


if __name__ == '__main__':
    unittest.main()

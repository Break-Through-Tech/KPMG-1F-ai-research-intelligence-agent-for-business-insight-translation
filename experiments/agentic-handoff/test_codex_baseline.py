"""Offline tests for the Baseline/B2 Codex runner: the app's own create_research, scripted Codex replies."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import codex_baseline
import fake_provider
from test_quote_grounding import PACKET


class FakeAdapter:
    supports_response_schema = True

    def __init__(self, fail_on=None):
        self.receipts, self.prompts, self.fail_on = [], [], fail_on or {}

    def __call__(self, prompt, *, response_schema=None):
        self.prompts.append(prompt[:40])
        record = {'status': 'started'}
        self.receipts.append(record)
        failure = self.fail_on.get(len(self.prompts))
        if failure:
            record.update(status='failed', diagnostic=failure)
            error = RuntimeError('Codex generation failed')
            error.codex_diagnostic = failure
            raise error
        record['status'] = 'ok'
        return json.dumps(fake_provider.answer(prompt))


def engine():
    from src.experimental.demo import create_research
    identity = lambda: {'collection': 'fixture', 'count': len(PACKET), 'indexed_records_sha256': 'fixture'}
    retrieval = (lambda q, k: [dict(p) for p in PACKET][:k], identity, 'fixture-index', {'method': 'fixture'})
    return create_research(retrieval, lambda *a, **k: None, {'provider': 'fake'}, 8)


def go(root, adapter):
    research = engine()
    return codex_baseline.run('deployed', research=research, generate=adapter, receipts=adapter.receipts, out_root=root)


class BaselineRunner(unittest.TestCase):
    def test_runs_all_ten_questions_with_two_calls_each_and_records_evidence(self):
        with TemporaryDirectory() as temp:
            root, adapter = Path(temp), FakeAdapter()
            status = go(root, adapter)
            self.assertEqual(set(status), set(codex_baseline.QUESTIONS))
            self.assertTrue(all(v['state'] == 'complete' for v in status.values()))
            out = root / 'codex-baseline-v1-deployed'
            used = json.loads((out / 'run.json').read_text())['calls_used']
            self.assertEqual(used, 20)  # synthesis + answer-quality review per question, as the app runs it
            self.assertTrue((out / 'F01' / '1-synthesis.evidence.json').is_file())
            rows = codex_baseline.report(out)
            self.assertEqual(rows['F01']['calls'], 2)
            self.assertTrue(rows['F01']['claims'])
            self.assertIn('required_points', rows['F05'])

    def test_failed_question_is_recorded_and_resume_reruns_only_it(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            status = go(root, FakeAdapter(fail_on={1: {'category': 'timeout'}}))  # F01 synthesis times out
            self.assertEqual(status['F01']['state'], 'execution_error')
            self.assertEqual(status['F02']['state'], 'complete')
            again = FakeAdapter()
            status = go(root, again)
            self.assertEqual(status['F01']['state'], 'complete')
            self.assertEqual(len(again.prompts), 2)  # only F01 re-ran
            self.assertTrue((root / 'codex-baseline-v1-deployed' / 'F01.attempt-1').is_dir())

    def test_memory_error_stops_instead_of_failing_every_question_then_resumes(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            research = engine()
            real = research.execute
            calls = {'n': 0}

            def flaky(payload):
                calls['n'] += 1
                if calls['n'] == 3:
                    raise MemoryError()
                return real(payload)
            research.execute = flaky
            adapter = FakeAdapter()
            status = codex_baseline.run('deployed', research=research, generate=adapter, receipts=adapter.receipts, out_root=root)
            self.assertEqual(list(status), ['F01', 'F02', 'F03'])
            self.assertEqual(status['F03']['state'], 'stopped')
            again = FakeAdapter()
            status = go(root, again)
            self.assertTrue(all(v['state'] == 'complete' for v in status.values()))
            self.assertEqual(len(again.prompts), 16)  # F03-F10 only; F01 and F02 not repeated

    def test_free_commit_is_measured(self):
        self.assertGreater(codex_baseline.free_commit_gb(), 0)

    def test_quota_error_stops(self):
        with TemporaryDirectory() as temp:
            status = go(Path(temp), FakeAdapter(fail_on={1: {'category': 'cli_exit', 'provider_code': 'insufficient_quota'}}))
            self.assertEqual(list(status), ['F01'])

    def test_directories_never_overlap_with_multi_agent_or_gemini(self):
        from gemini_paired import STAGED
        names = {v[0] for v in codex_baseline.VARIANTS.values()}
        self.assertFalse(names & {e[0] for e in STAGED.values()})
        self.assertFalse(names & {d for d, _ in __import__('codex_paired').LABELS.values()})


if __name__ == '__main__':
    unittest.main()

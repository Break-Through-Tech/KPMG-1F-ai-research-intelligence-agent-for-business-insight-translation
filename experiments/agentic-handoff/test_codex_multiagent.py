"""Offline tests for the business-set Multi-Agent runner. Scripted Codex adapter; real orchestrator and safeguards."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import codex_multiagent
from test_codex_paired import MISATTRIBUTED_PROSE, FakeAdapter
from test_quote_grounding import PACKET, SPLIT


def go(root, adapter, build=codex_multiagent.engine):
    return codex_multiagent.run(generate=adapter, receipts=adapter.receipts,
                                retrieve=lambda q, k: [dict(p) for p in PACKET][:k], index_sha256='fixture',
                                out_root=root, build=build)


def out(root):
    return root / codex_multiagent.TARGET


class Runner(unittest.TestCase):
    def tearDown(self):
        import statistical_reports
        statistical_reports.disable()  # the runner enables it process-wide; keep other suites unaffected

    def test_runs_the_fifteen_frozen_questions_with_safeguards_and_saves_everything(self):
        with TemporaryDirectory() as temp:
            root, adapter = Path(temp), FakeAdapter()
            status = go(root, adapter)
            self.assertEqual(list(status), [f'C{i:02d}' for i in range(1, 16)])
            self.assertTrue(all(v['state'] == 'complete' for v in status.values()))
            info = json.loads((out(root) / 'run.json').read_text())
            self.assertEqual((info['call_cap'], info['calls_used']), (75, 45))  # plan + synthesis + verify each
            saved = json.loads((out(root) / 'C01' / 'result.json').read_text(encoding='utf-8'))
            published = [c['text'] for c in saved['envelope']['result']['summary']['claims']]
            self.assertIn(SPLIT['text'], published)                    # elided quote recovered (quote grounding)
            self.assertNotIn(MISATTRIBUTED_PROSE['text'], published)   # interpretation withheld (policy)
            self.assertTrue(list((out(root) / 'C01').glob('*-synthesis.evidence.json')))
            self.assertGreaterEqual(saved['retrieval_invocations'], 1)

    def test_statistical_report_fix_is_enabled_for_the_run(self):
        import numeric_checks
        import statistical_reports
        codex_multiagent.engine(lambda *a, **k: None, lambda q, k: [], 'fixture')
        self.assertIs(numeric_checks.ground_text, statistical_reports._ground_text)
        statistical_reports.disable()

    def test_resume_never_repeats_completed_questions(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            go(root, FakeAdapter())
            again = FakeAdapter()
            go(root, again)
            self.assertEqual(again.calls, [])

    def test_quota_error_stops_the_run(self):
        with TemporaryDirectory() as temp:
            status = go(Path(temp), FakeAdapter(fail_on={1: {'category': 'rate_limited', 'http_status': 429}}))
            self.assertEqual(list(status), ['C01'])
            self.assertEqual(status['C01']['state'], 'execution_error')

    def test_memory_error_stops_and_resume_continues(self):
        def flaky(generate, retrieve, sha):
            class Boom:
                def run(self, question):
                    raise MemoryError()
            return Boom()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            status = go(root, FakeAdapter(), build=flaky)
            self.assertEqual(status['C01']['state'], 'stopped')
            status = go(root, FakeAdapter())
            self.assertTrue(all(v['state'] == 'complete' for v in status.values()))
            self.assertTrue((out(root) / 'C01.attempt-1').is_dir())


if __name__ == '__main__':
    unittest.main()

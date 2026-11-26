"""Offline tests of run_consolidated.run (simulated provider; 0 model calls)."""
import json
from pathlib import Path
import tempfile
import unittest

import env  # noqa: F401
import run_consolidated as rc
from codex_paired import Budget, CodexCalls
from engine import ConsolidatedResearch
from request_guard import RequestGuard
from test_consolidated import (GOOD_REVIEW, GOOD_SYNTHESIS, GATE, P1, P2, PLAN, TABLES, V2, count, ranked_from)


class Scripted:
    """Provider behind CodexCalls: replies by stage, appends a receipt per call like the Codex adapter."""

    def __init__(self, receipts, script):
        self.receipts, self.script = receipts, script

    def __call__(self, prompt, *, response_schema=None):
        stage = ('synthesis' if prompt.startswith('Synthesize') else 'review'
                 if prompt.startswith('ANSWER QUALITY REVIEW') else 'plan')
        reply = self.script[stage].pop(0) if isinstance(self.script[stage], list) else self.script[stage]
        self.receipts.append({'status': 'failed' if isinstance(reply, Exception) else 'ok',
                              'usage': None if isinstance(reply, Exception) else [{'input_tokens': len(prompt) // 4}]})
        if isinstance(reply, Exception):
            raise reply
        return json.dumps(reply)


def arm(tmp, mode, script, cap=None):
    receipts = []
    out = Path(tmp) / rc.ARMS[mode]
    out.mkdir(parents=True, exist_ok=True)
    calls = CodexCalls(Scripted(receipts, script), receipts, Budget(out / 'calls.sqlite3', cap=cap or rc.ARM_CAP[mode]))
    guard = RequestGuard(calls)
    engine = ConsolidatedResearch(mode, ranked=ranked_from({}, [P1, P2]), count=count, tables=TABLES, generate=guard,
                                  v2=V2, gate=GATE)
    return engine, calls, guard, receipts


QUESTIONS = [{'id': 'H01', 'question': 'q one'}, {'id': 'H02', 'question': 'q two'}]


class RunnerTests(unittest.TestCase):
    def test_sim_standard_arm_two_calls_per_question_with_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, calls, guard, receipts = arm(tmp, 'standard', {'synthesis': GOOD_SYNTHESIS, 'review': GOOD_REVIEW})
            status = rc.run('standard', engine=engine, calls=calls, guard=guard, receipts=receipts,
                            out_root=Path(tmp), questions=QUESTIONS)
            self.assertEqual({v['state'] for v in status.values()}, {'complete'})
            self.assertEqual(calls.budget.used(), 4)
            log = json.loads((Path(tmp) / rc.ARMS['standard'] / 'H01' / 'calls.json').read_text())
            self.assertEqual(log[0]['calls'], 2)
            self.assertEqual(len(log[0]['requests_estimated']), 2)
            self.assertTrue(all(u for u in log[0]['actual_usage']))

    def test_sim_one_resume_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = {'plan': PLAN, 'synthesis': GOOD_SYNTHESIS,
                      'review': [TimeoutError('300 s'), TimeoutError('300 s'), GOOD_REVIEW, GOOD_REVIEW]}
            engine, calls, guard, receipts = arm(tmp, 'deep', script)
            first = rc.run('deep', engine=engine, calls=calls, guard=guard, receipts=receipts, out_root=Path(tmp),
                           questions=QUESTIONS[:1])
            self.assertEqual(first['H01']['state'], 'execution_error')
            second = rc.run('deep', engine=engine, calls=calls, guard=guard, receipts=receipts, out_root=Path(tmp),
                            questions=QUESTIONS[:1])
            self.assertEqual(second['H01']['state'], 'execution_error')
            self.assertEqual(calls.budget.used(), 4)  # plan, synthesis, review | review (resume repeats only review)
            third = rc.run('deep', engine=engine, calls=calls, guard=guard, receipts=receipts, out_root=Path(tmp),
                           questions=QUESTIONS[:1])
            self.assertEqual(third['H01'], {'state': 'failed', 'reason': '2 attempts used'})
            self.assertEqual(calls.budget.used(), 4)  # no third attempt

    def test_sim_arm_cap_stops_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, calls, guard, receipts = arm(tmp, 'standard', {'synthesis': GOOD_SYNTHESIS, 'review': GOOD_REVIEW}, cap=3)
            status = rc.run('standard', engine=engine, calls=calls, guard=guard, receipts=receipts,
                            out_root=Path(tmp), questions=QUESTIONS)
            self.assertEqual(status['H02']['state'], 'stopped')
            self.assertEqual(calls.budget.used(), 3)

    def test_unit_combined_cap_refuses_before_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / rc.ARMS['standard']
            out.mkdir()
            budget = Budget(out / 'calls.sqlite3', cap=50)
            for _ in range(21):
                budget.reserve('x', 'p')
            with self.assertRaises(SystemExit):
                rc.combined_check(Path(tmp), 'deep')  # 21 + 30 > 50
            self.assertEqual(rc.ARM_CAP['standard'] + rc.ARM_CAP['deep'], rc.COMBINED_CAP)


if __name__ == '__main__':
    unittest.main()

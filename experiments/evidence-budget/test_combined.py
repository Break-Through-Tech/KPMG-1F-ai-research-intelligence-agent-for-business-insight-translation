"""Offline tests for combined-v1: evidence budget, budgeted Multi-Agent research, and both engines' fresh arms run
end to end with scripted Codex replies. No model calls.   python -I test_combined.py"""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path[:0] = [str(HERE), str(EXP / 'agentic-handoff'), str(EXP / 'verification-repair')]
import codex_baseline  # noqa: E402  (sets the agentic and src paths)
import codex_multiagent  # noqa: E402
import evidence_budget as eb  # noqa: E402
from budgeted_research import BudgetedResearchAgent, MERGED_TOKENS  # noqa: E402
from test_codex_baseline import FakeAdapter as BaselineAdapter, PACKET  # noqa: E402
from test_codex_paired import FakeAdapter as MultiAgentAdapter  # noqa: E402


def rows(n, cost=100, prefix='p'):
    return [{'chunk_id': f'{prefix}{i}', 'text': 'x', 'cost': cost} for i in range(n)]


COUNT = lambda p: p.get('cost', 100)  # noqa: E731


class Select(unittest.TestCase):
    def test_fixed_is_the_prefix_in_order(self):
        self.assertEqual([p['chunk_id'] for p in eb.select(rows(30), eb.fixed(16), COUNT)], [f'p{i}' for i in range(16)])

    def test_skip_fit_skips_a_long_row_and_continues_within_the_window(self):
        ranked = rows(5) + [{'chunk_id': 'long', 'text': 'x', 'cost': 5900}] + rows(40, prefix='q')
        chosen = eb.select(ranked, eb.skip_fit(3000, 30), COUNT)
        ids = [p['chunk_id'] for p in chosen]
        self.assertNotIn('long', ids)
        self.assertEqual(ids[:6], ['p0', 'p1', 'p2', 'p3', 'p4', 'q0'])
        self.assertEqual(len(ids), 29)  # window 30 minus the skipped row; 2,900 tokens
        self.assertLessEqual(sum(COUNT(p) for p in chosen), 3000)

    def test_rows_are_whole_copies(self):
        ranked = rows(3)
        chosen = eb.select(ranked, eb.skip_fit(1000), COUNT)
        chosen[0]['text'] = 'changed'
        self.assertEqual(ranked[0]['text'], 'x')

    def test_budgeted_retrieve_asks_for_the_window(self):
        asked = []
        retrieve = eb.budgeted_retrieve(lambda q, n: asked.append(n) or rows(n), COUNT, eb.skip_fit(6000, 30))
        self.assertEqual(len(retrieve('q', 8)), 30)
        self.assertEqual(asked, [30])


class Research(unittest.TestCase):
    def agent(self, captured):
        def synthesize(question, passages, generate, findings_only=False):
            captured.append([p['chunk_id'] for p in passages])
            return {'status': 'ok', 'claims': [], 'limitations': [], 'limitation_support': []}
        patcher = mock.patch('src.research_chat.synthesize', synthesize)
        patcher.start()
        self.addCleanup(patcher.stop)
        budget = mock.Mock()
        agent = BudgetedResearchAgent(lambda q, k: rows(k, prefix=q[:1]), 8,
                                      lambda q: rows(16, prefix='I'), COUNT)
        return agent, budget

    def test_first_round_keeps_the_budgeted_packet_whole_and_first(self):
        captured = []
        agent, budget = self.agent(captured)
        task = {'payload': {'question': 'Q?', 'searches': [{'query': 'Q?', 'purpose': 'original question'},
                                                            {'query': 'a', 'purpose': 'x'}, {'query': 'b', 'purpose': 'y'}]}}
        status, out = agent.run(task, budget)
        ids = captured[0]
        self.assertEqual(ids[:16], [f'I{i}' for i in range(16)])
        self.assertEqual(ids[16:20], ['a0', 'b0', 'a1', 'b1'])
        self.assertLessEqual(len(ids) * 100, MERGED_TOKENS)
        self.assertTrue(out['searches'][0]['budgeted'] and not out['searches'][1]['budgeted'])

    def test_targeted_round_is_bounded_and_keeps_new_slots(self):
        captured = []
        agent, budget = self.agent(captured)
        existing = rows(80, prefix='E')
        task = {'payload': {'question': 'Q?', 'existing_passages': existing, 'pinned_ids': [p['chunk_id'] for p in existing],
                            'require_new': True, 'searches': [{'query': 'new', 'purpose': 'gap'}]}}
        agent.run(task, budget)
        ids = captured[0]
        self.assertLessEqual(len(ids), 40)
        self.assertGreaterEqual(sum(i.startswith('n') for i in ids), 4)  # RESERVED_NEW still honoured
        self.assertFalse(any(i.startswith('I') for i in ids))           # no budgeted packet in later rounds


def fresh_set(temp):
    folder = Path(temp) / 'set'
    folder.mkdir()
    source = codex_baseline.SETS['completion'][0]
    questions = json.loads((source / 'questions.json').read_text(encoding='utf-8'))[:2]
    (folder / 'questions.json').write_text(json.dumps(questions), encoding='utf-8')
    (folder / 'references.json').write_text((source / 'references.json').read_text(encoding='utf-8'), encoding='utf-8')
    return folder, [q['id'] for q in questions]


class Engines(unittest.TestCase):
    def tearDown(self):
        import statistical_reports
        import verification_v2
        statistical_reports.disable()
        verification_v2.disable()

    def test_baseline_fresh_arms_record_their_evidence_policy(self):
        from src.experimental.demo import create_research
        identity = lambda: {'collection': 'fixture', 'count': len(PACKET), 'indexed_records_sha256': 'fixture'}  # noqa: E731
        with TemporaryDirectory() as temp:
            folder, ids = fresh_set(temp)
            with mock.patch.dict(codex_baseline.SETS, {'fresh': (folder, None)}):
                for variant, budget in (('fresh-top16', 'fixed-16'), ('fresh-skipfit6k', 'skip-fit-6000-w30')):
                    retrieve = eb.budgeted_retrieve(lambda q, n: [dict(p) for p in PACKET][:n], lambda p: 50,
                                                    eb.skip_fit(6000, 30))
                    research = create_research((retrieve, identity, 'fixture', {'method': 'fixture'}), lambda *a, **k: None,
                                               {'provider': 'fake'}, 16 if variant == 'fresh-top16' else 20)
                    adapter = BaselineAdapter()
                    status = codex_baseline.run(variant, research=research, generate=adapter, receipts=adapter.receipts,
                                                out_root=Path(temp))
                    self.assertEqual(set(status), set(ids))
                    self.assertTrue(all(v['state'] == 'complete' for v in status.values()))
                    info = json.loads((Path(temp) / codex_baseline.VARIANTS[variant][0] / 'run.json').read_text())
                    self.assertEqual((info['evidence'], info['call_cap'], info['calls_used']), (budget, codex_baseline.fresh_cap(variant), 4))
                    saved = json.loads((Path(temp) / codex_baseline.VARIANTS[variant][0] / ids[0] / 'result.json').read_text(encoding='utf-8'))
                    self.assertTrue(saved['requests'] and all(r['allowed'] and r['request_tokens'] for r in saved['requests']))
                    self.assertGreater(saved['requests'][0]['evidence_tokens'], 0)

    def test_multiagent_fresh_arms_run_with_budget_and_v2_gate(self):
        with TemporaryDirectory() as temp:
            folder, ids = fresh_set(temp)
            with mock.patch.dict(codex_baseline.SETS, {'fresh': (folder, None)}):
                for evidence, verification in (('top8', 'frozen'), ('top16', 'frozen'), ('skipfit6k', 'v2')):
                    initial = None if evidence == 'top8' else eb.budgeted_retrieve(
                        lambda q, n: [dict(p) for p in PACKET][:n], lambda p: 50,
                        eb.fixed(16) if evidence == 'top16' else eb.skip_fit(6000, 30))
                    adapter = MultiAgentAdapter()
                    target = codex_multiagent.fresh_target(evidence, verification)
                    status = codex_multiagent.run(
                        generate=adapter, receipts=adapter.receipts,
                        retrieve=lambda q, k: [dict(p) for p in PACKET][:k], index_sha256='fixture', out_root=Path(temp),
                        build=codex_multiagent.fresh_engine(verification, initial, lambda p: 50), target=target,
                        question_set='fresh')
                    self.assertTrue(all(v['state'] == 'complete' for v in status.values()), status)
                    saved = json.loads((Path(temp) / target / ids[0] / 'result.json').read_text(encoding='utf-8'))
                    summary = saved['envelope']['result']['summary']
                    self.assertFalse(any(c.get('kind') == 'interpretation' for c in summary['claims']))
                    research = [s for s in saved['agentic']['trace'] if s.get('agent') == 'research_agent']
                    if verification == 'v2':
                        rows_ = [c['verification'] for c in summary['held_claims'] + summary.get('interpretations', [])
                                 if c.get('kind') == 'interpretation']
                        self.assertTrue(rows_ and all('interpretation_gate' in r for r in rows_))
                        import agents
                        self.assertEqual(agents.ground_claim.__module__, 'numeric_checks_v2')
                    self.assertTrue(research or saved['agentic'])
                import verification_v2
                verification_v2.disable()


class Guard(unittest.TestCase):
    def test_oversized_request_is_refused_before_any_call_is_reserved(self):
        from request_guard import RequestGuard, RequestTooLarge
        sent = []
        guard = RequestGuard(lambda prompt, **k: sent.append(prompt) or '{}', evidence_cap=100, request_cap=10_000, reserve=1_000)
        small = 'Instructions ' + json.dumps({'question': 'q', 'paper_passages': [{'chunk_id': 'a', 'text': 'x' * 30}]})
        big = 'Instructions ' + json.dumps({'question': 'q', 'paper_passages': [{'chunk_id': 'a', 'text': 'x' * 3000}]})
        guard(small, response_schema={'type': 'object'})
        with self.assertRaises(RequestTooLarge):
            guard(big, response_schema={'type': 'object'})
        self.assertEqual(len(sent), 1)
        self.assertEqual([r['allowed'] for r in guard.records], [True, False])
        self.assertEqual(guard.records[0]['evidence_passages'], 1)
        self.assertLess(guard.records[0]['evidence_tokens'], guard.records[0]['request_tokens'])

    def test_whole_request_cap_applies_without_evidence(self):
        from request_guard import RequestGuard, RequestTooLarge
        guard = RequestGuard(lambda prompt, **k: '{}', request_cap=2_000, reserve=1_000)
        with self.assertRaises(RequestTooLarge):
            guard('y' * 4000)
        self.assertEqual(guard.records[0]['evidence_tokens'], 0)

    def test_guard_failure_in_baseline_spends_no_budget(self):
        from src.experimental.demo import create_research
        import request_guard
        identity = lambda: {'collection': 'fixture', 'count': len(PACKET), 'indexed_records_sha256': 'fixture'}  # noqa: E731
        with TemporaryDirectory() as temp, mock.patch.object(request_guard, 'EVIDENCE_CAP', 1):
            folder, ids = fresh_set(temp)
            with mock.patch.dict(codex_baseline.SETS, {'fresh': (folder, None)}):
                research = create_research(((lambda q, k: [dict(p) for p in PACKET][:k]), identity, 'fixture', {}),
                                           lambda *a, **k: None, {'provider': 'fake'}, 16)
                adapter = BaselineAdapter()
                status = codex_baseline.run('fresh-top16', research=research, generate=adapter,
                                            receipts=adapter.receipts, out_root=Path(temp))
            self.assertTrue(all(v['state'] == 'execution_error' for v in status.values()), status)
            self.assertEqual(adapter.prompts, [])
            info = json.loads((Path(temp) / 'combined-v1-baseline-top16' / 'run.json').read_text())
            self.assertEqual(info['calls_used'], 0)

    def test_combined_cap_counts_every_arm(self):
        from codex_paired import Budget
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for name, n in (('combined-v1-baseline-top8', 20), ('combined-v1-baseline-top16', 20)):
                (root / name).mkdir()
                budget = Budget(root / name / 'calls.sqlite3', cap=22)
                for _ in range(n):
                    budget.reserve('q', 'p')
            self.assertEqual(codex_baseline.check_combined_cap(root, 'combined-v1-multiagent-top16-v2', 55)['combined_used'], 40)
            with self.assertRaises(SystemExit):
                codex_baseline.check_combined_cap(root, 'combined-v1-multiagent-top16-v2', 61)


    def test_fresh_caps_and_one_resume(self):
        self.assertEqual([codex_baseline.fresh_cap(v) for v in ('fresh-top8', 'fresh-skipfit6k')], [22, 23])
        self.assertEqual(22 + 23 + codex_baseline.FRESH_ARM_CAP['multiagent'], codex_baseline.COMBINED_CAP)
        with TemporaryDirectory() as temp:
            out = Path(temp)
            self.assertTrue(codex_baseline.resumes_left(out, 'G04'))
            (out / 'G04.attempt-1').mkdir()
            self.assertFalse(codex_baseline.resumes_left(out, 'G04'))
            self.assertTrue(codex_baseline.resumes_left(out, 'G08'))

if __name__ == '__main__':
    unittest.main()

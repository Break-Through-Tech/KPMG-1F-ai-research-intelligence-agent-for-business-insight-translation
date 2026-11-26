"""Offline tests for withholding interpretations. Scripted replies and recorded live drafts; no provider calls."""
import copy
import json
import sys
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE), str(HERE.parent / 'agentic-handoff')]
import interpretation_policy  # noqa: E402
from agents import OrchestratorAgent  # noqa: E402
from test_agentic import CORPUS, Provider, Retriever, plan, verdicts  # noqa: E402
from test_scope_review import IMAGE_CAUSE, MISATTRIBUTED, PACKET, SPLIT  # noqa: E402

NODES = {'text': 'Cora has 2,708 nodes.', 'kind': 'finding', 'support': [
    {'chunk_id': 'cora', 'quote': 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708'}]}


def row(kind, decision='accepted', reason=None):
    return {'kind': kind, 'text': kind, 'decision': decision, 'held_reason': reason}


def output(*rows, coverage='full'):
    return {'claims': list(rows), 'coverage': coverage, 'missing_aspects': [], 'retrieval_request': None}


class Apply(unittest.TestCase):
    def test_accepted_interpretation_is_held_and_findings_untouched(self):
        out = output(row('finding'), row('interpretation'))
        self.assertEqual(interpretation_policy.apply(out), 1)
        self.assertEqual([r['decision'] for r in out['claims']], ['accepted', 'held'])
        self.assertEqual(out['claims'][1]['held_reason'], interpretation_policy.REASON)
        self.assertEqual(out['coverage'], 'partial')
        self.assertIn('withheld by policy', out['missing_aspects'][-1])

    def test_only_interpretations_means_no_coverage(self):
        out = output(row('interpretation'))
        interpretation_policy.apply(out)
        self.assertEqual(out['coverage'], 'none')

    def test_findings_only_answer_is_unchanged(self):
        out = output(row('finding'), row('finding'))
        before = copy.deepcopy(out)
        self.assertEqual(interpretation_policy.apply(out), 0)
        self.assertEqual({k: v for k, v in out.items() if k != 'interpretations_withheld'}, before)

    def test_existing_hold_reasons_are_kept(self):
        out = output(row('finding'), row('interpretation', 'held', 'verifier judged unsupported'), coverage='partial')
        self.assertEqual(interpretation_policy.apply(out), 0)
        self.assertEqual(out['claims'][1]['held_reason'], 'verifier judged unsupported')
        self.assertEqual(out['coverage'], 'partial')


def run(claims, verdict_items, coverage='full', enabled=True):
    p = Provider(plan=[plan()], research=[{'status': 'ok', 'claims': claims, 'limitations': []}],
                 verify=[verdicts(*verdict_items, coverage=coverage)])
    corpus = {x['chunk_id']: x for x in PACKET}
    with unittest.mock.patch.dict(CORPUS, corpus):
        engine = OrchestratorAgent(generate=p, retrieve=Retriever({'Why': list(corpus)}), top_k=8, research_only=True)
        r = (interpretation_policy.enable(engine) if enabled else engine).run('Why did MultiFinRAG beat the Baseline?')
    return r, p


class EndToEnd(unittest.TestCase):
    def test_misattributed_interpretation_is_held_even_when_the_verifier_accepts_it(self):
        r, p = run([NODES, MISATTRIBUTED], [('supported', []), ('supported', [])])
        self.assertEqual([c['text'] for c in r['summary']['claims']], [NODES['text']])
        held = r['summary']['held_claims'][0]
        self.assertEqual(held['verification']['held_reason'], interpretation_policy.REASON)
        self.assertEqual(held['verification']['automated']['verdict'], 'supported')  # verifier's view is kept on record
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])  # no extra model call

    def test_valid_interpretation_is_also_withheld_trade_off(self):
        r, _ = run([NODES, IMAGE_CAUSE], [('supported', []), ('supported', [])])
        self.assertEqual([c['text'] for c in r['summary']['claims']], [NODES['text']])

    def test_interpretation_only_answer_abstains_cleanly(self):
        r, _ = run([MISATTRIBUTED], [('supported', [])])
        self.assertEqual((r['status'], r['summary']['claims']), ('insufficient_evidence', []))
        self.assertEqual(len(r['summary']['held_claims']), 1)

    def test_without_the_policy_the_same_draft_publishes_the_interpretation(self):
        r, _ = run([NODES, MISATTRIBUTED], [('supported', []), ('supported', [])], enabled=False)
        self.assertEqual(len(r['summary']['claims']), 2)

    def test_number_checks_and_quote_checks_still_apply_to_findings(self):
        wrong = {'text': 'Cora has 3,000 nodes.', 'kind': 'finding', 'support': NODES['support']}
        r, _ = run([wrong, SPLIT], [('supported', []), ('supported', [])])
        self.assertEqual([c['text'] for c in r['summary']['claims']], [SPLIT['text']])
        self.assertIn('numbers_and_qualifiers', r['summary']['held_claims'][0]['verification']['held_reason'])


class MultiRound(unittest.TestCase):
    def test_handoff_does_not_carry_a_withheld_interpretation_as_verified(self):
        from handoff import EvidenceHandoffOrchestrator
        from test_handoff import ReplayProvider
        from test_quote_grounding import ARXIV, CORA, LIMIT, TQ
        first = [dict(p) for p in PACKET if p['chunk_id'] != 'arxiv']
        provider = ReplayProvider(MISATTRIBUTED, NODES, LIMIT)
        engine = EvidenceHandoffOrchestrator(
            generate=provider, retrieve=lambda q, k: [dict(ARXIV)] if 'second method' in q else [dict(p) for p in first],
            top_k=8, index_sha256='fixture')
        r = interpretation_policy.enable(engine).run(TQ)
        self.assertEqual(len(provider.synthesis_packets), 2)  # the revision round really ran
        carried = provider.synthesis_packets[1]['research_handoff']['prior_verified_claims']
        self.assertNotIn(MISATTRIBUTED['text'], json.dumps(carried))
        self.assertEqual([c['text'] for c in r['summary']['claims']], [NODES['text']])


class RecordedLiveDrafts(unittest.TestCase):
    """Every live F01 draft (Stage A v3 both arms, scoped v4 current) replayed through its real orchestrator."""

    def test_live_drafts_before_and_after(self):
        from replay_scope_review import ROOT, replay
        base = ROOT / 'data/processed'
        cases = [(base / 'gemini-handoff-paired-v3-grounded-stage-a' / q / a, False, q)
                 for q in ('F01', 'F03') for a in ('current', 'handoff')]
        cases.append((base / 'gemini-handoff-paired-v4-scoped-stage-a' / 'F01' / 'current', True, 'F01'))
        if not all(d.exists() for d, _, _ in cases):
            self.skipTest('live runs not present')
        for arm_dir, scoped, question in cases:
            with self.subTest(arm=str(arm_dir.relative_to(base))):
                before = replay(arm_dir, scope=scoped, label=None)
                after = replay(arm_dir, scope=scoped, label=None, policy=True)
                findings_before = [t for t in before['published'] if not t.startswith('The significant performance gap')]
                self.assertEqual(after['published'], findings_before)  # every finding kept
                if question == 'F01':
                    self.assertEqual((len(before['published']), len(after['published'])), (4, 3))
                    self.assertEqual(after['held'][0]['reason'], interpretation_policy.REASON)
                else:
                    self.assertEqual(after['published'], before['published'])
                    self.assertEqual(after['answer_scope'], 'full')


if __name__ == '__main__':
    unittest.main()

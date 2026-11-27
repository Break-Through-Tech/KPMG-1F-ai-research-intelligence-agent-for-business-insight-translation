"""Permanent regressions for Codex audit #4 (2026-11-19): single-mention numeric grounding, factual premises
inside proposals, and the research-only A/B profile. Model-free.

Every numeric case runs END TO END through the orchestrator with a PERMISSIVE fake verifier that calls every
claim supported, so what is tested is the code's own decision.

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_audit4.py
The two-database ledger bypass is covered in experiments/table-endpoint/test_ab_profile.py (OneAuthoritativeLedger).
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import route  # noqa: E402
from agents import OrchestratorAgent  # noqa: E402
from numeric_checks import ground_text, screen_business  # noqa: E402
from test_agentic import CORPUS, Provider, Retriever, draft, passage, plan, verdicts  # noqa: E402

SIGNS = 'Model X changed accuracy by -3.2%, while Model Y changed accuracy by +3.2%.'
# (name, claim, source, expected end-to-end outcome: 'held' or 'kept', expected issue for held claims)
PAIRS = [
    ('Codex 1: X claimed +3.2% where only Y is +3.2%', 'Model X changed accuracy by +3.2%.', SIGNS, 'held', 'sign_flip'),
    ('valid twin: Y +3.2%', 'Model Y changed accuracy by +3.2%.', SIGNS, 'kept', None),
    ('valid twin: X -3.2%', 'Model X changed accuracy by -3.2%.', SIGNS, 'kept', None),
    ('Codex 2: 78% adult patients from 78% pediatric', 'Model X reached 78% accuracy for adult patients.',
     'Model X reached 78% accuracy for pediatric patients.', 'held', 'population_mismatch'),
    ('valid twin: pediatric kept pediatric', 'Model X reached 78% accuracy for pediatric patients.',
     'Model X reached 78% accuracy for pediatric patients.', 'kept', None),
    ('Codex 3: affirmative claim from explicitly negated evidence', 'Model X improved accuracy by 5%.',
     'Model X did not improve accuracy by 5%.', 'held', 'negation_mismatch'),
    ('valid twin: negation kept', 'Model X did not improve accuracy by 5%.', 'Model X did not improve accuracy by 5%.', 'kept', None),
    ('Codex 4: "minors under age 18" for "participants under age 18" (valid)', 'Model X reached 78% accuracy for minors under age 18.',
     'Model X reached 78% accuracy for participants under age 18.', 'kept', None),
    ('Codex 4 variant: share of minors under 18 (valid)', '78% of minors under 18 reported fewer errors with Model X.',
     '78% of participants under 18 reported fewer errors with Model X.', 'kept', None),
    ('invalid twin: adults for participants under 18', 'Model X reached 78% accuracy for adults.',
     'Model X reached 78% accuracy for participants under age 18.', 'held', 'population_mismatch'),
    # Previously passing behaviour that must be preserved.
    ('preserved: 0.5 seconds as 500 milliseconds', 'Model X answered in 0.5 seconds per query.',
     'Model X answered in 500 milliseconds per query.', 'kept', None),
    ('preserved: comparison across two models', 'Model X reached 78.0%, higher than 64.5% for Model Y.',
     'Model X: 78.0%; Model Y: 64.5%.', 'kept', None),
    ('preserved: subjects swapped', 'Model X reached 64.5% and Model Y reached 78.0%.',
     'Model X reached 78.0% and Model Y reached 64.5%.', 'held', 'subject_mismatch'),
]


def run_claim(claim_text, source, chunk='S1'):
    CORPUS[chunk] = passage(chunk, source)
    try:
        claim = {'text': claim_text, 'kind': 'finding', 'support': [{'chunk_id': chunk, 'quote': source.rstrip('.')}]}
        provider = Provider(plan=[plan()], research=[draft(claim, limits=[])], verify=[verdicts(('supported', []))])
        return OrchestratorAgent(generate=provider, retrieve=Retriever({'Model': [chunk]}), top_k=4).run('How did Model X perform?')
    finally:
        del CORPUS[chunk]


class SingleMentionEndToEnd(unittest.TestCase):
    def test_pairs_with_a_permissive_verifier(self):
        for name, claim, source, outcome, issue in PAIRS:
            with self.subTest(name):
                r = run_claim(claim, source)
                kept = bool(r['summary']['claims'])
                self.assertEqual('kept' if kept else 'held', outcome, r['summary'].get('held_claims'))
                if outcome == 'held':
                    row = r['summary']['held_claims'][0]['verification']
                    self.assertEqual(row['automated']['verdict'], 'supported')  # the verifier was permissive...
                    self.assertIn(issue, row['deterministic']['numbers_and_qualifiers'])  # ...code held it anyway

    def test_mentions_are_never_combined(self):
        # Sign from Model Y, subject from Model X: no single source mention supports "+3.2% for Model X".
        result = ground_text('Model X changed accuracy by +3.2%.', [SIGNS])
        self.assertEqual(result['status'], 'contradicted')

    def test_codex_probes_are_covered(self):
        self.assertEqual(sum(name.startswith('Codex') for name, *_ in PAIRS), 5)


VERIFIED = [{'text': 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.', 'chunk_ids': ['A1']}]
PASSAGES = [{'chunk_id': 'A1', 'text': 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.'}]


def screen(text, action='Pilot Model X on a sample of clinical notes.'):
    row = {'text': text, 'chunk_ids': ['A1'], 'suggested_action': action, 'assumptions': []}
    return screen_business({'status': 'ok', 'industry': 'Healthcare', 'implications': [row], 'risks': [], 'limitations': []},
                           PASSAGES, VERIFIED)


class FactualPremises(unittest.TestCase):
    def test_codex_case_unsupported_premise_inside_a_proposal_is_withheld(self):
        screened, screening = screen('Model X has already achieved accuracy in clinical deployment, so consider a pilot.')
        self.assertEqual(screened['implications'], [])
        self.assertIn('unsupported_premise', screening[0]['issues']['implication'])
        self.assertIn('setting_transfer', screening[0]['issues']['implication'])

    def test_supported_premise_with_a_proposal_is_kept(self):
        screened, screening = screen('Model X reached 78.0% accuracy on the benchmark after fine-tuning, so consider a clinical pilot.')
        self.assertEqual(len(screened['implications']), 1, screening)
        self.assertEqual(screening[0]['categories']['implication'], 'conditional_proposal')

    def test_unsupported_premise_inside_an_action_is_withheld(self):
        screened, _ = screen('Fine-tuned Model X may suit clinical documentation if its benchmark accuracy transfers.',
                             action='Because Model X already works in hospitals, expand the pilot.')
        self.assertEqual(screened['implications'], [])

    def test_premise_in_a_risk_line_is_checked(self):
        output = {'status': 'ok', 'industry': 'Healthcare', 'risks': ['Model X was proven in production, so drift may be limited.'],
                  'limitations': [], 'implications': [{'text': 'Fine-tuned Model X may suit clinical documentation if its benchmark accuracy transfers.',
                                                        'chunk_ids': ['A1'], 'suggested_action': 'Pilot Model X on a sample of clinical notes.',
                                                        'assumptions': []}]}
        screened, _ = screen_business(output, PASSAGES, VERIFIED)
        self.assertEqual(screened['risks'], [])


class ResearchOnly(unittest.TestCase):
    class Research:
        provenance, context_id = {'index': {'indexed_records_sha256': 'f' * 64}}, 'c'

        def check_context(self, context_id):
            pass

    def test_research_only_route_refuses_an_industry_before_any_call(self):
        provider = Provider(plan=[plan()], research=[], verify=[])
        orchestrator = OrchestratorAgent(generate=provider, retrieve=Retriever({}), top_k=4, research_only=True)
        status, body = route.handle({'query': 'How accurate is Model X?', 'context_id': 'c', 'industry': 'Healthcare'},
                                    orchestrator=orchestrator, research=self.Research(),
                                    usage=lambda: {'remaining': 40, 'stopped': False, 'cap': 40}, top_k=4, research_only=True)
        self.assertEqual((status, body['code'], provider.calls), (400, 'research_only', []))

    def test_research_only_orchestrator_never_routes_business(self):
        CORPUS['R1'] = passage('R1', 'Model X reached 78.0% accuracy on the benchmark.')
        try:
            claim = {'text': 'Model X reached 78.0% accuracy on the benchmark.', 'kind': 'finding',
                     'support': [{'chunk_id': 'R1', 'quote': 'Model X reached 78.0% accuracy on the benchmark'}]}
            provider = Provider(plan=[plan(business=True, industry='healthcare')], research=[draft(claim, limits=[])],
                                verify=[verdicts(('supported', []))])
            r = OrchestratorAgent(generate=provider, retrieve=Retriever({'Model': ['R1']}), top_k=4, research_only=True).run(
                'What does Model X accuracy mean for healthcare?', industry='Healthcare')
        finally:
            del CORPUS['R1']
        self.assertEqual(provider.calls, ['plan', 'research', 'verify'])
        self.assertIsNone(r['business_industry'])
        routing = [e for e in r['trace'] if e.get('decision') == 'business_routing'][0]
        self.assertIn('Research-only', routing['reason'])


if __name__ == '__main__':
    unittest.main(verbosity=1)

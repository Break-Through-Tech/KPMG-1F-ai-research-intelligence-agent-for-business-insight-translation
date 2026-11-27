"""Regression tests for generalized automatic business-intent detection (offline, no model calls)."""
import json
import tempfile
import unittest
from pathlib import Path

from src.brief_store import BriefStore
from src.business_demo import research_business_flags
from src.business_insights import automatic_business_context, business_context_hint, derive_business_context
from tests.test_downstream_business import result_for

FIXTURES = Path(__file__).resolve().parent / 'fixtures/business'
BLIND2_FLOOR = 0.75  # measured 0.82 after one revision informed by this split
REPORTED = ('How can logistics companies use LLM agents to improve delivery route planning, and what evidence '
            'and risks should decision-makers consider before implementing these systems?')


def splits():
    data = json.loads((FIXTURES / 'intent-eval-v1.json').read_text(encoding='utf-8'))
    blind = json.loads((FIXTURES / 'intent-eval-blind-v1.json').read_text(encoding='utf-8'))
    blind2 = json.loads((FIXTURES / 'intent-eval-blind-v2.json').read_text(encoding='utf-8'))
    return {'dev': data['dev'], 'heldout': data['heldout'], 'blind': blind['blind'], 'blind2': blind2['blind2']}


class BusinessIntentTests(unittest.TestCase):
    def test_reported_logistics_question_starts_automatically_with_full_context(self):
        context = automatic_business_context(REPORTED)
        self.assertEqual(context['industry'], 'logistics')
        self.assertIn('delivery route planning', context['workflow'])
        self.assertIn(context['workflow'], REPORTED)
        self.assertEqual(context['decision'], REPORTED)

    def test_labelled_sets_have_no_false_positives_and_high_recall(self):
        # Floors are below the measured results so wording tweaks fail loudly only on real regressions.
        floors = {'dev': 1.0, 'heldout': 1.0, 'blind': 0.85, 'blind2': BLIND2_FLOOR}
        for name, rows in splits().items():
            with self.subTest(split=name):
                business = [row for row in rows if row['label'] == 'business']
                others = [row for row in rows if row['label'] != 'business']
                found = [row for row in business if automatic_business_context(row['q'])]
                false_positive = [row['q'] for row in others if automatic_business_context(row['q'])]
                self.assertEqual(false_positive, [])
                self.assertGreaterEqual(len(found) / len(business), floors[name])
                for row in found:
                    context = automatic_business_context(row['q'])
                    self.assertIn(context['workflow'], ' '.join(row['q'].split()))  # never invented

    def test_academic_questions_naming_sectors_stay_research_only(self):
        for question in ('In the logistics routing benchmark paper, what optimality gap do LLM planners show?',
                         'Which bank-sector case study reports the highest error rate?',
                         'How do logistics researchers use LLM agents to simulate traffic?',
                         'How can hospitals\' clinical notes be used to train language models?',
                         'What are the business implications of model routing in retail? Academic only.'):
            with self.subTest(question=question):
                self.assertIsNone(automatic_business_context(question))
                self.assertIsNone(business_context_hint(question))

    def test_intent_without_workflow_prefills_known_context_and_asks_only_for_workflow(self):
        hint = business_context_hint('Our bank is weighing whether to adopt this. What would it take?')
        self.assertEqual(hint['industry'], 'banking')
        self.assertEqual(hint['missing'], ['workflow'])
        self.assertIsNone(automatic_business_context('Our bank is weighing whether to adopt this. What would it take?'))
        self.assertIsNone(business_context_hint(REPORTED))  # complete: generated automatically instead
        self.assertIsNone(business_context_hint('What is the business takeaway?'))

    def test_manual_derivation_uses_generalized_workflow_and_sector(self):
        context = derive_business_context('We run a regional airline. Would LLM-based crew scheduling assistants pay off?', {})
        self.assertEqual(context['industry'], 'aviation')
        self.assertIn('crew scheduling', context['workflow'])

    def test_research_response_flags_spend_no_call_and_mark_one_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            store = BriefStore(Path(directory) / 'briefs.sqlite3')
            def saved(question):
                body = store.save({'mode': 'indexed', 'submitted_request': {'query': question}, 'result': result_for()})
                return {**body, 'library': {**body['library'], 'replayed': False}}
            auto = research_business_flags(saved(REPORTED))
            self.assertIs(auto['business_auto'], True)
            self.assertNotIn('business_hint', auto)
            hinted = research_business_flags(saved('Our bank is weighing whether to adopt this. What would it take?'))
            self.assertNotIn('business_auto', hinted)
            self.assertEqual(hinted['business_hint']['missing'], ['workflow'])
            academic = research_business_flags(saved('By how much did CU-DPO improve strategy-selection accuracy?'))
            self.assertNotIn('business_auto', academic)
            self.assertNotIn('business_hint', academic)
            replay = saved(REPORTED)
            replay['library'] = {**replay['library'], 'replayed': True}
            self.assertNotIn('business_auto', research_business_flags(replay))  # reopening never re-dispatches


if __name__ == '__main__':
    unittest.main()

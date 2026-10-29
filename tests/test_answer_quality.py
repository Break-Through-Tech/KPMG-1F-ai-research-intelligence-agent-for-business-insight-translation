"""Review transport and filtering tests; scripted verdicts are not accuracy proof."""
from copy import deepcopy
import json
import unittest

from src.answer_quality import review_summary
from src.research_chat import synthesize
from tests.test_research_chat import PASSAGES, ANSWER
from tests.test_indexed_research import adapter, generator


class AnswerQualityTests(unittest.TestCase):
    def review(self, decisions=None, coverage='partial', gap='The passages do not establish banking-specific performance.'):
        return {'coverage': coverage, 'gap': gap, 'decisions': decisions or [
            {'index': 0, 'supported': True, 'relevant': True, 'reason': 'Bounded finding supported.'}]}

    def test_partial_keeps_supported_finding_and_original_evidence(self):
        before = deepcopy(ANSWER)
        result = review_summary('Banking?', ANSWER, PASSAGES,
            generate=lambda p: json.dumps(self.review()))
        self.assertEqual(result['claims'], ANSWER['claims'])
        self.assertEqual(result['answer_scope'], 'partial')
        self.assertIn('banking-specific', result['answer_lead'])
        self.assertEqual(ANSWER, before)
        self.assertEqual(result['quality_review']['reviewer'], 'model_not_independent_human')

    def test_off_topic_and_unsupported_claims_are_removed_but_retained_for_audit(self):
        for supported, relevant in [(False, True), (True, False)]:
            decision = {'index': 0, 'supported': supported, 'relevant': relevant, 'reason': 'Rejected.'}
            result = review_summary('Q', ANSWER, PASSAGES, generate=lambda p: json.dumps(
                self.review([decision], coverage='none')))
            self.assertEqual(result['status'], 'insufficient_evidence')
            self.assertEqual(result['claims'], [])
            self.assertEqual(result['quality_review']['original_claims'], ANSWER['claims'])

    def test_malformed_incomplete_duplicate_and_contradictory_reviews_fail_closed(self):
        summary = deepcopy(ANSWER)
        summary['claims'] *= 2
        d = self.review()['decisions'][0]
        for review in [self.review([d, d]), self.review([d]),
                       self.review([d, {**d, 'index': 1}], coverage='none'),
                       self.review([d, {**d, 'index': 1}], gap=' '),
                       {**self.review([d, {**d, 'index': 1}]), 'approved': True}]:
            with self.subTest(review=review), self.assertRaises(Exception):
                review_summary('Q', summary, PASSAGES, generate=lambda p: json.dumps(review))

    def test_review_failure_is_not_evidence_abstention(self):
        def fail(prompt):
            raise RuntimeError('provider failure')
        with self.assertRaises(RuntimeError):
            review_summary('Q', ANSWER, PASSAGES, generate=fail)

    def test_findings_only_rejects_recommendation_kind(self):
        answer = deepcopy(ANSWER)
        answer['claims'][0]['kind'] = 'interpretation'
        with self.assertRaises(Exception):
            synthesize('Q', PASSAGES, generate=lambda p: json.dumps(answer), findings_only=True)

    def test_business_receives_only_accepted_claims_and_passages(self):
        prompts = []
        def generate(prompt, **kwargs):
            prompts.append(prompt)
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return json.dumps(self.review([
                    {'index': 0, 'supported': True, 'relevant': True, 'reason': 'Supported.'},
                    {'index': 1, 'supported': True, 'relevant': False, 'reason': 'Adjacent.'}]))
            return generator(prompt, **kwargs)
        research = adapter(generate=generate, quality_check=True)
        result = research.execute({'query': 'Compare for banking.', 'industry': 'banking',
                                  'context_id': research.context_id})
        self.assertIsNone(result['error'])
        self.assertEqual(len(result['result']['summary']['claims']), 1)
        self.assertEqual(len(result['result']['evidence']), 2)
        self.assertIn('research findings only', prompts[0])
        self.assertNotIn('Paper 2 reports', prompts[-1])
        self.assertNotIn('original_claims', prompts[-1])

    def test_all_rejected_skips_business_and_review_error_reports_summary_failure(self):
        def generate(prompt, **kwargs):
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return json.dumps(self.review([
                    {'index': i, 'supported': False, 'relevant': False, 'reason': 'Unsupported.'}
                    for i in range(2)], coverage='none'))
            self.assertIn('PAPER PASSAGES', prompt)
            return generator(prompt, **kwargs)
        research = adapter(generate=generate, quality_check=True)
        response = research.execute({'query': 'Q', 'industry': 'banking', 'context_id': research.context_id})
        self.assertEqual(response['result']['provenance']['stages']['business'], 'skipped')
        self.assertFalse(response['result']['approved'])
        def broken(prompt, **kwargs):
            return 'invalid' if prompt.startswith('ANSWER QUALITY REVIEW') else generator(prompt, **kwargs)
        research = adapter(generate=broken, quality_check=True)
        response = research.execute({'query': 'Q', 'context_id': research.context_id})
        self.assertEqual(response['error']['code'], 'summary_failed')
        self.assertIsNone(response['result'])


if __name__ == '__main__':
    unittest.main()

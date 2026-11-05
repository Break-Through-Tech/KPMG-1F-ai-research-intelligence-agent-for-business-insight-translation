"""Review transport and filtering tests; scripted verdicts are not accuracy proof."""
from copy import deepcopy
import json
import unittest

from src.answer_quality import review_summary
from src.research_chat import synthesize
from tests.test_research_chat import PASSAGES, ANSWER
from tests.test_indexed_research import adapter, generator


class AnswerQualityTests(unittest.TestCase):
    def review(self, decisions=None, coverage='partial', gap='The passages do not establish banking-specific performance.',
               limitations=None):
        decisions = decisions if decisions is not None else [
            {'index': 0, 'supported': True, 'relevant': True, 'reason': 'Bounded finding supported.'}]
        return {'coverage': coverage, 'gap': gap, 'decisions': decisions,
                'retained_claim_indices': [d['index'] for d in decisions if d['supported'] and d['relevant']],
                'limitations': limitations or []}

    def test_removing_irrelevant_claim_does_not_downgrade_complete_answer(self):
        summary = deepcopy(ANSWER)
        summary['claims'].append({**deepcopy(ANSWER['claims'][0]), 'text': 'An unrelated comparison.'})
        decisions = [
            {'index': 0, 'supported': True, 'relevant': True, 'reason': 'Answers the question.'},
            {'index': 1, 'supported': True, 'relevant': False, 'reason': 'Unrelated.'}]
        prompts = []
        def generate(prompt):
            prompts.append(prompt)
            return json.dumps(self.review(decisions, coverage='full', gap='', limitations=ANSWER['limitations']))
        result = review_summary('What score was reported?', summary, PASSAGES, generate=generate)
        self.assertEqual(result['answer_scope'], 'full')
        self.assertEqual(result['answer_lead'], '')
        self.assertEqual(len(result['claims']), 1)
        self.assertEqual(len(prompts), 1)  # No additional sequential review call.
        self.assertIn('ONLY those retained claims', prompts[0])
        self.assertEqual(len(result['quality_review']['original_claims']), 2)

    def test_mixed_stale_limit_replaced_with_cited_scope_and_audit_preserved(self):
        summary = synthesize('Q', PASSAGES, generate=lambda p: json.dumps(ANSWER))
        stale = 'Scores describe evaluated systems; the deleted trip comparison was unrelated.'
        summary['limitations'] = [stale]
        summary['limitation_support'][0]['text'] = stale
        before = deepcopy(summary)
        result = review_summary('Q', summary, PASSAGES, generate=lambda p: json.dumps(
            self.review(coverage='full', gap='', limitations=ANSWER['limitations'])))
        self.assertEqual(result['limitations'], [ANSWER['limitations'][0]['text']])
        self.assertEqual(result['limitation_support'][0]['chunk_ids'], ['paper-page-1'])
        self.assertNotIn('trip', json.dumps(result['limitations']))
        self.assertEqual(result['quality_review']['original_limitations'], [stale])
        self.assertEqual(result['quality_review']['original_limitation_support'], before['limitation_support'])
        self.assertEqual(summary, before)

    def test_true_missing_part_still_partial_after_claim_rejection(self):
        summary = deepcopy(ANSWER)
        summary['claims'] *= 2
        decisions = [
            {'index': 0, 'supported': True, 'relevant': True, 'reason': 'Score supported.'},
            {'index': 1, 'supported': False, 'relevant': True, 'reason': 'Cost unsupported.'}]
        result = review_summary('What score and cost were reported?', summary, PASSAGES,
            generate=lambda p: json.dumps(self.review(decisions, gap='The passages do not establish cost.')))
        self.assertEqual(result['answer_scope'], 'partial')
        self.assertEqual(result['answer_lead'], 'The passages do not establish cost.')

    def test_invalid_rebuilt_limitations_fail_closed(self):
        for key, value in [('chunk_id', 'unknown'), ('quote', 'The mean score was 0.999')]:
            limits = deepcopy(ANSWER['limitations'])
            limits[0]['support'][0][key] = value
            with self.subTest(key=key), self.assertRaises(Exception):
                review_summary('Q', ANSWER, PASSAGES, generate=lambda p: json.dumps(
                    self.review(coverage='full', gap='', limitations=limits)))

    def test_coverage_cannot_use_rejected_claims_or_conflicting_status(self):
        accepted = self.review(coverage='full', gap='')
        rejected = self.review([{'index': 0, 'supported': False, 'relevant': True, 'reason': 'Unsupported.'}],
                               coverage='none')
        for review in [{**accepted, 'retained_claim_indices': []},
                       {**accepted, 'retained_claim_indices': [0, 0]},
                       {**accepted, 'gap': 'Actually missing cost.'},
                       {**rejected, 'retained_claim_indices': [0]},
                       {**rejected, 'coverage': 'partial'},
                       {**rejected, 'coverage': 'full', 'gap': ''}]:
            with self.subTest(review=review), self.assertRaises(Exception):
                review_summary('Q', ANSWER, PASSAGES, generate=lambda p: json.dumps(review))

    def test_abstention_skips_generation_and_preserves_original(self):
        summary = {'status': 'insufficient_evidence', 'claims': [], 'limitations': ['No evidence.']}
        result = review_summary('Q', summary, [], generate=lambda p: self.fail('Unexpected model call.'))
        self.assertEqual(result, summary)
        self.assertIsNot(result, summary)

    def test_review_native_schema_binds_rebuilt_limits_to_passages(self):
        def generate(prompt, *, response_schema):
            from jsonschema import Draft202012Validator
            Draft202012Validator.check_schema(response_schema)
            ids = response_schema['properties']['limitations']['items']['properties']['support']['items']['properties']['chunk_id']['enum']
            self.assertEqual(ids, ['paper-page-1'])
            return json.dumps(self.review(coverage='full', gap='', limitations=ANSWER['limitations']))
        generate.supports_response_schema = True
        result = review_summary('Q', ANSWER, PASSAGES, generate=generate)
        self.assertEqual(result['quality_review']['policy'], 'answer-quality-v2')
        self.assertEqual(result['answer_scope'], 'full')

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

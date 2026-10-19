"""Synthesis guardrails: reject fabricated, missing or mismatched source support."""
from copy import deepcopy
import json
import unittest

from src.research_chat import PaperResearch, synthesize
from src.research_contracts import validate_result


PASSAGES = [{'chunk_id': 'paper-page-1', 'text': 'The mean score was 0.166 across the evaluated systems.',
             'title': 'Test paper', 'arxiv_id': '2608.20318v1', 'source': 'pdf',
             'pdf_url': 'https://arxiv.org/pdf/2608.20318v1',
             'source_url': 'https://arxiv.org/pdf/2608.20318v1#page=1', 'page_number': 1}]
ANSWER = {'status': 'ok', 'claims': [{'text': 'The evaluated systems achieved a mean score of 0.166.',
    'kind': 'finding', 'support': [{'chunk_id': 'paper-page-1', 'quote': 'The mean score was 0.166'}]}],
    'limitations': [{'text': 'These results describe only the evaluated systems.',
        'support': [{'chunk_id': 'paper-page-1', 'quote': 'across the evaluated systems.'}]}]}


class SynthesisTests(unittest.TestCase):
    def run_answer(self, answer):
        return synthesize('What were the results?', PASSAGES, generate=lambda prompt: json.dumps(answer))

    def test_valid_answer_maps_quote_to_citation_and_preserves_kind(self):
        answer = self.run_answer(ANSWER)
        self.assertEqual(answer['claims'][0]['chunk_ids'], ['paper-page-1'])
        self.assertEqual(answer['claims'][0]['kind'], 'finding')
        self.assertEqual(answer['support_check'], 'exact_quote_membership_only_not_semantic_entailment')

    def test_whitespace_normalization_does_not_change_quote_membership(self):
        answer = deepcopy(ANSWER)
        answer['claims'][0]['support'][0]['quote'] = 'The mean\n score was 0.166'
        self.assertEqual(self.run_answer(answer)['status'], 'ok')

    def test_unknown_missing_and_fabricated_support_are_rejected(self):
        cases = []
        for field, value in [('chunk_id', 'invented-id'), ('quote', 'The mean score was 0.999')]:
            answer = deepcopy(ANSWER)
            answer['claims'][0]['support'][0][field] = value
            cases.append(answer)
        answer = deepcopy(ANSWER)
        answer['claims'][0]['support'] = []
        cases.append(answer)
        answer = deepcopy(ANSWER)
        del answer['claims'][0]['support']
        cases.append(answer)
        for answer in cases:
            with self.subTest(answer=answer), self.assertRaises(Exception):
                self.run_answer(answer)

    def test_abstention_cannot_carry_claims(self):
        answer = deepcopy(ANSWER)
        answer['status'] = 'insufficient_evidence'
        with self.assertRaises(ValueError):
            self.run_answer(answer)
        answer['claims'] = []
        self.assertEqual(self.run_answer(answer)['status'], 'insufficient_evidence')

    def test_interpretations_require_the_same_source_support(self):
        answer = deepcopy(ANSWER)
        answer['claims'][0]['kind'] = 'interpretation'
        self.assertEqual(self.run_answer(answer)['claims'][0]['kind'], 'interpretation')
        answer['claims'][0]['support'] = []
        with self.assertRaises(Exception):
            self.run_answer(answer)

    def test_native_schema_is_bound_to_actual_evidence(self):
        def generate(prompt, *, response_schema):
            self.assertIn('paper_passages', prompt)
            allowed = response_schema['properties']['claims']['items']['properties']['support']['items']['properties']['chunk_id']['enum']
            self.assertEqual(allowed, ['paper-page-1'])
            return json.dumps(ANSWER)
        generate.supports_response_schema = True
        self.assertEqual(synthesize('Q', PASSAGES, generate=generate)['status'], 'ok')

    def test_no_evidence_skips_generation(self):
        def generate(prompt):
            self.fail('Generation must not run without evidence')
        self.assertEqual(synthesize('Q', [], generate=generate)['claims'], [])

    def test_full_pipeline_preserves_pending_review_and_provenance(self):
        research = PaperResearch(PASSAGES, lambda prompt: json.dumps(ANSWER), {'provider': 'test'})
        result = research({'query': 'Q'})
        validate_result(result['result'])
        self.assertEqual(result['mode'], 'live-synthesis')
        self.assertFalse(result['result']['approved'])
        self.assertEqual(result['result']['human_review']['status'], 'pending')


if __name__ == '__main__':
    unittest.main()

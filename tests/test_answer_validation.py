"""Provider failures vs answer-validation rejections: retry, diagnostics and safe abstention.

Validators (exact quotes, numeric literals, schema, quality review) are unchanged; these
tests cover only what happens after a validator rejects an answer. Model replies are scripted.
"""
import json
import unittest
from copy import deepcopy

from src.answer_validation import ProviderFailure, guard_provider, provider_cause
from src.indexed_research import IndexedResearch


def p(cid, paper, text, section='results'):
    return {'chunk_id': cid, 'arxiv_id': paper, 'title': f'Paper {paper}', 'text': text, 'section': section,
            'source': 'html', 'page_number': None, 'pdf_url': f'https://arxiv.org/pdf/{paper}',
            'html_url': f'https://arxiv.org/html/{paper}', 'source_url': f'https://arxiv.org/html/{paper}'}


PASSAGES = [p('p1', '2608.00001v1', 'The benchmark resolved 62 percent of requests in 2024.'),
            p('p2', '2608.00002v1', 'The second study reports a latency of 40 seconds.')]


def answer(text, quote, cid='p1'):
    return json.dumps({'status': 'ok', 'claims': [{'kind': 'finding', 'text': text,
                       'support': [{'chunk_id': cid, 'quote': quote}]}], 'limitations': []})


def review_all(prompt):
    draft = json.loads(prompt[prompt.find('{"question"'):])['draft']
    n = len(draft['claims'])
    return json.dumps({'coverage': 'full', 'gap': '', 'decisions': [
        {'index': i, 'supported': True, 'relevant': True, 'reason': 'ok'} for i in range(n)],
        'retained_claim_indices': list(range(n)), 'limitations': []})


def research(generate, *, arxiv=None, quality=True):
    return IndexedResearch(retrieve=lambda q, k: deepcopy(PASSAGES), identity=lambda: {'count': 2},
                           generate=generate, metadata={'provider': 'scripted'}, index_path='fixture',
                           quality_check=quality, arxiv_search=arxiv)


class AnswerValidationTests(unittest.TestCase):
    def run_q(self, service):
        return service.execute({'query': 'What share of requests was resolved?', 'context_id': service.context_id})

    def test_invented_number_is_retried_with_reason_then_accepted(self):
        prompts = []
        def generate(prompt, **kw):
            prompts.append(prompt)
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return review_all(prompt)
            if 'AUTOMATED VALIDATION REJECTED' in prompt:
                return answer('The benchmark resolved 62 percent of requests.', PASSAGES[0]['text'])
            return answer('The benchmark resolved 72 percent of requests.', PASSAGES[0]['text'])
        searched = []
        response = self.run_q(research(generate, arxiv=lambda q, k: searched.append(q) or ([], {})))
        summary = response['result']['summary']
        self.assertIsNone(response['error'])
        self.assertEqual(summary['claims'][0]['text'], 'The benchmark resolved 62 percent of requests.')
        self.assertEqual(summary['validation']['status'], 'accepted_after_retry')
        self.assertEqual(summary['validation']['attempts'][0]['stage'], 'numeric_citation_check')
        self.assertIn('number absent', summary['validation']['attempts'][0]['reason'])
        self.assertIn('number absent', [x for x in prompts if 'AUTOMATED VALIDATION' in x][0])
        self.assertEqual(searched, [])

    def test_repeated_overreach_is_a_qualified_abstention_not_an_error_or_evidence_gap(self):
        def generate(prompt, **kw):
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return review_all(prompt)
            return answer('This cuts monthly costs by 40 percent, about $12,000.', PASSAGES[0]['text'])
        searched = []
        response = self.run_q(research(generate, arxiv=lambda q, k: searched.append(q) or ([], {})))
        summary = response['result']['summary']
        self.assertIsNone(response['error'])
        self.assertEqual(summary['claims'], [])
        self.assertEqual(summary['validation']['status'], 'rejected')
        self.assertEqual(len(summary['validation']['attempts']), 2)
        self.assertIn('not a finding that the evidence is absent', summary['answer_lead'])
        self.assertNotIn('12,000', json.dumps(summary['claims']))
        self.assertEqual(searched, [], 'a validation abstention must not trigger external search')

    def test_provider_failure_is_never_retried_or_turned_into_abstention(self):
        calls = []
        def generate(prompt, **kw):
            calls.append(prompt)
            raise RuntimeError("You've hit your usage limit. Try again at 8:01 PM. secret-token-123")
        response = self.run_q(research(generate))
        self.assertIsNone(response['result'])
        self.assertEqual(response['error']['code'], 'summary_failed')
        self.assertEqual(response['error']['cause'], 'rate_limited')
        self.assertIn('not an evidence result', response['error']['message'])
        self.assertNotIn('secret-token', json.dumps(response))
        self.assertEqual(len(calls), 1)

    def test_provider_failure_during_retry_still_propagates(self):
        def generate(prompt, **kw):
            if 'AUTOMATED VALIDATION REJECTED' in prompt:
                raise TimeoutError('provider timed out')
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return review_all(prompt)
            return answer('Resolved 99 percent.', PASSAGES[0]['text'])
        response = self.run_q(research(generate, arxiv=lambda q, k: ([], {})))  # enables numeric check
        self.assertIsNone(response['result'])
        self.assertEqual(response['error']['cause'], 'timeout')

    def test_rejected_external_answer_preserves_library_draft_with_reason(self):
        external = [p('x1', '2601.12345v2', 'The support benchmark resolved 62 percent of requests.')]
        def generate(prompt, **kw):
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return review_all(prompt)
            rows = json.loads(prompt.rsplit('\n', 1)[-1])['paper_passages']
            row = next((r for r in rows if r['chunk_id'] == 'x1'), rows[0])
            if row['chunk_id'] == 'x1':
                return answer('Resolved 62 percent.', 'Quote that is not in the passage at all.', 'x1')
            return json.dumps({'status': 'insufficient_evidence', 'claims': [], 'limitations': [
                {'text': 'Not reported.', 'support': [{'chunk_id': row['chunk_id'], 'quote': row['text']}]}]})
        response = self.run_q(research(generate, arxiv=lambda q, k: (deepcopy(external), {'query': 'q', 'candidates': []})))
        result = response['result']
        self.assertEqual({x['chunk_id'] for x in result['evidence']}, {'p1', 'p2'})
        search = result['provenance']['arxiv_search']
        self.assertEqual(search['status'], 'answer_failed')
        self.assertEqual(search['cause'], 'validation_rejected')
        self.assertEqual(len(search['validation']['attempts']), 2)

    def test_validators_are_unchanged(self):
        from src.research_chat import attach_validated_citations, validate_reported_numbers
        item = {'kind': 'finding', 'text': 'Resolved 72 percent.', 'support': [{'chunk_id': 'p1', 'quote': PASSAGES[0]['text']}]}
        attach_validated_citations([item], PASSAGES)
        with self.assertRaisesRegex(ValueError, 'number absent'):
            validate_reported_numbers([item])
        bad = {'kind': 'finding', 'text': 'x', 'support': [{'chunk_id': 'p1', 'quote': 'A quote not in the passage.'}]}
        with self.assertRaisesRegex(ValueError, 'absent from'):
            attach_validated_citations([bad], PASSAGES)

    def test_provider_cause_classification_is_coarse_and_never_echoes_secrets(self):
        self.assertEqual(provider_cause(RuntimeError('HTTP 429 Too Many Requests')), 'rate_limited')
        self.assertEqual(provider_cause(TimeoutError()), 'timeout')
        self.assertEqual(provider_cause(RuntimeError('boom')), 'provider_error')
        guarded = guard_provider(lambda prompt: (_ for _ in ()).throw(ValueError('bad key sk-123')))
        with self.assertRaises(ProviderFailure) as ctx:
            guarded('x')
        self.assertNotIn('sk-123', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()

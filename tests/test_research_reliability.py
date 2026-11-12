"""Regression tests for reliability v2: evidence coverage, crowding, and failure handling.

Each failure class reproduced in the 30-scenario evaluation has a test here:
paper crowding on a multi-part question (L6, M2), a single paper absorbing a
comparison (M1), missing abstract/result passages in external evidence (N3, N4),
a numeric overreach becoming summary_failed (I2), and provider failure being
indistinguishable from validation failure (M1 live). All model replies are scripted.
"""
import json
import unittest
from copy import deepcopy

from src.answer_validation import ProviderFailure, guard_provider, provider_cause
from src.experimental.evidence_coverage import (cover_roles, merge_ranked, retrievable_parts,
                                                select_external, with_result_coverage)
from src.experimental.question_parts import question_parts
from src.indexed_research import IndexedResearch


def p(cid, paper, text, section='introduction'):
    return {'chunk_id': cid, 'arxiv_id': paper, 'title': f'Paper {paper}', 'text': text, 'section': section,
            'source': 'html', 'page_number': None, 'pdf_url': f'https://arxiv.org/pdf/{paper}',
            'html_url': f'https://arxiv.org/html/{paper}', 'source_url': f'https://arxiv.org/html/{paper}'}


class QuestionPartsTests(unittest.TestCase):
    def test_single_part_questions_are_not_split(self):
        for q in ('How accurate are routing agents on optimal trip planning?',
                  'Do scanners agree on which add-ons are dangerous?'):
            self.assertEqual(question_parts(q), [])

    def test_clauses_and_comparisons_split_without_topic_knowledge(self):
        self.assertEqual(question_parts('Do streaming detectors beat static ones, and do language agents '
                                        'degrade over longer conversations?'),
                         ['Do streaming detectors beat static ones',
                          'do language agents degrade over longer conversations'])
        self.assertEqual(question_parts('Compare how Alpha Net and Beta Former reduce memory use'),
                         ['Alpha Net reduce memory use', 'Beta Former reduce memory use'])

    def test_dangling_parts_are_not_retrieved_alone(self):
        q = 'Can a monitor detect covert goal pursuit by an agent, and how was that tested?'
        self.assertEqual(retrievable_parts(q), ['Can a monitor detect covert goal pursuit by an agent'])


class CoverageTests(unittest.TestCase):
    def test_one_paper_cannot_crowd_out_a_second_part(self):
        main = [p(f'a{i}', 'A', 'streaming detector results') for i in range(10)]
        part = [p(f'b{i}', 'B', 'agent conversation depth results') for i in range(5)]
        merged = merge_ranked([main, main, part], 8)
        self.assertEqual(len(merged), 8)
        self.assertGreaterEqual(sum(x['arxiv_id'] == 'B' for x in merged), 2)
        self.assertLessEqual(sum(x['arxiv_id'] == 'A' for x in merged), 6)

    def test_single_part_order_is_unchanged(self):
        main = [p(f'a{i}', 'A' if i % 3 else 'B', 'x y z') for i in range(10)]
        self.assertEqual(merge_ranked([main], 8), main[:8])

    def test_multi_part_library_retrieval_queries_each_part(self):
        calls = []
        corpus = {'A': [p(f'a{i}', 'A', 'monitor results') for i in range(20)],
                  'B': [p(f'b{i}', 'B', 'covert goal detection monitor') for i in range(5)]}
        def retrieve(q, k):
            calls.append((q, k))
            return deepcopy((corpus['B'] if 'covert' in q and len(calls) > 1 else corpus['A'])[:k])
        search = with_result_coverage(retrieve, corpus['A'] + corpus['B'])
        result = search('Which monitors work in practice, and can a monitor detect covert goal pursuit by agents?', 8)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][1], 16)  # wider main pool before balancing
        self.assertIn('B', {x['arxiv_id'] for x in result})
        self.assertEqual(len(result), 8)

    def test_roles_fill_abstract_and_numbers_without_displacing_best_or_other_papers(self):
        best = p('a0', 'A', 'core method description')
        selected = [best, p('a1', 'A', 'related work'), p('b0', 'B', 'other paper'), p('a2', 'A', 'background')]
        pool = {'A': selected[:2] + [selected[3], p('abs', 'A', 'We find that the method works.', 'abstract'),
                                     p('num', 'A', 'Accuracy rose from 41.2% to 73.5% on the test set.', 'results')]}
        out = cover_roles('method accuracy', selected, pool)
        self.assertEqual(out[0], best)
        self.assertEqual(out[2]['chunk_id'], 'b0')
        self.assertEqual(len(out), 4)
        self.assertEqual({x['chunk_id'] for x in out if x['arxiv_id'] == 'A'}, {'a0', 'abs', 'num'})

    def test_external_ranking_keeps_abstract_numbers_and_each_relevant_paper(self):
        a = [p(f'a{i}', 'A', f'self preference evaluator bias discussion {i}', 'discussion') for i in range(10)]
        a += [p('aabs', 'A', 'Evaluators prefer their own outputs.', 'abstract'),
              p('anum', 'A', 'GPT-4 is 73.5% accurate at self-recognition versus 50% chance.', 'introduction')]
        b = [p(f'b{i}', 'B', f'self preference evaluator bias study {i}', 'results') for i in range(4)]
        out = select_external('Do AI graders favor their own writing?', ['self preference evaluator bias'], a + b, 8)
        ids = {x['chunk_id'] for x in out}
        self.assertEqual(len(out), 8)
        self.assertIn('aabs', ids)
        self.assertIn('anum', ids)
        self.assertTrue(any(x['arxiv_id'] == 'B' for x in out))


PASSAGES = [p('p1', '2608.00001v1', 'The benchmark resolved 62 percent of requests in 2024.', 'results'),
            p('p2', '2608.00002v1', 'The second study reports a latency of 40 seconds.', 'results')]


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


class FailureHandlingTests(unittest.TestCase):
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
        self.assertEqual(summary['status'], 'ok')
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
        self.assertNotIn('12,000', json.dumps(response['result']['summary']['claims']))
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
        external = [p('x1', '2601.12345v2', 'The support benchmark resolved 62 percent of requests.', 'results')]
        def generate(prompt, **kw):
            if prompt.startswith('ANSWER QUALITY REVIEW'):
                return review_all(prompt)
            payload = json.loads(prompt.rsplit('\n', 1)[-1])
            rows = payload['paper_passages']
            # main combines library and external evidence for the fallback answer
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

    def test_provider_cause_classification_is_coarse(self):
        self.assertEqual(provider_cause(RuntimeError('HTTP 429 Too Many Requests')), 'rate_limited')
        self.assertEqual(provider_cause(TimeoutError()), 'timeout')
        self.assertEqual(provider_cause(RuntimeError('boom')), 'provider_error')
        guarded = guard_provider(lambda prompt: (_ for _ in ()).throw(ValueError('bad key sk-123')))
        with self.assertRaises(ProviderFailure) as ctx:
            guarded('x')
        self.assertNotIn('sk-123', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()

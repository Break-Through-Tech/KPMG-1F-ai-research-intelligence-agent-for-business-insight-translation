"""Model-free tests for the experimental agentic research mode.

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_agentic.py
(The shared synthesis code needs jsonschema.) No model is loaded and no provider is called:
retrieval and every agent reply are scripted in-process. The real shared validators run.
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
import agents  # noqa: E402
from agents import OrchestratorAgent  # noqa: E402


def passage(cid, text, arxiv='2601.00001v1'):
    url = f'https://arxiv.org/html/{arxiv}'
    return {'chunk_id': cid, 'text': text, 'arxiv_id': arxiv, 'title': f'Paper {arxiv}', 'pdf_url': f'https://arxiv.org/pdf/{arxiv}',
            'source': 'html', 'source_url': url, 'page_number': None, 'section': 'Results'}


CORPUS = {
    'A1': passage('A1', 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.'),
    'A2': passage('A2', 'Model Y reached 64.5% accuracy on the same benchmark.'),
    'B1': passage('B1', 'Hospitals piloting the assistant reported fewer documentation errors.', '2601.00002v1'),
    'C1': passage('C1', 'Latency rose from 1.2 seconds to 3.4 seconds when retrieval was enabled.', '2601.00003v1'),
    'T1': {**passage('T1', 'Table 4: Model | Accuracy (%) | X | 78.0'), 'representation': 'linearized_table', 'table_id': 't4'},
}


class Retriever:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, query, top_k):
        self.calls.append(query)
        for key, ids in self.routes.items():
            if key in query:
                return [dict(CORPUS[i]) for i in ids][:top_k]
        return []


class Provider:
    """Scripted replies by agent role, identified from each agent's distinct prompt."""
    supports_response_schema = True

    def __init__(self, **scripts):
        self.scripts = {k: list(v) for k, v in scripts.items()}
        self.calls, self.prompts = [], []

    @staticmethod
    def role(prompt):
        for prefix, role in (('You are the planning orchestrator', 'plan'), ('Synthesize an answer', 'research'),
                             ('You are an independent evidence verifier', 'verify'), ('Prompt ID: business-translation', 'business')):
            if prompt.startswith(prefix):
                return role
        raise AssertionError('unknown prompt')

    def __call__(self, prompt, response_schema=None):
        role = self.role(prompt)
        self.calls.append(role)
        self.prompts.append((role, prompt))
        if not self.scripts.get(role):
            raise AssertionError(f'unexpected {role} call')
        reply = self.scripts[role].pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply if isinstance(reply, str) else json.dumps(reply)


def plan(subs=(), business=False, industry='', chart=False):
    return {'question_type': 'comparison' if subs else 'single_fact',
            'subquestions': [{'query': q, 'purpose': 'part'} for q in subs],
            'business': {'delegate': business, 'industry_in_question': industry, 'reason': 'test plan'},
            'chart': {'delegate': chart, 'reason': 'test plan'}, 'notes': ''}


def claim(text, cid, quote, kind='finding'):
    return {'text': text, 'kind': kind, 'support': [{'chunk_id': cid, 'quote': quote}]}


def draft(*claims, status='ok', limits=None):
    limits = limits if limits is not None else [{'text': 'Only one benchmark was reported.',
                                                   'support': [{'chunk_id': 'A1', 'quote': 'accuracy on the benchmark after fine-tuning'}]}]
    return {'status': status, 'claims': list(claims), 'limitations': limits}


def verdicts(*items, coverage='full', request=None):
    return {'verdicts': [{'index': i, 'verdict': v, 'issues': iss, 'reason': 'checked'} for i, (v, iss) in enumerate(items)],
            'coverage': coverage, 'missing_aspects': [] if coverage == 'full' else ['the Y result'],
            'retrieval_request': request or {'needed': False, 'query': '', 'reason': 'enough evidence'}}


X = claim('Model X reached 78.0% accuracy after fine-tuning.', 'A1', 'Model X reached 78.0% accuracy on the benchmark')
Y = claim('Model Y reached 64.5% accuracy.', 'A2', 'Model Y reached 64.5% accuracy on the same benchmark')
Q = 'How accurate is Model X after fine-tuning?'


def run(provider, retriever, question=Q, **kwargs):
    industry = kwargs.pop('industry', None)
    return OrchestratorAgent(generate=provider, retrieve=retriever, top_k=4, **kwargs).run(question, industry=industry)


def decision(result, name):
    return [e for e in result['trace'] if e['type'] == 'decision' and e['decision'] == name]


class Routing(unittest.TestCase):
    def test_simple_question_uses_three_calls_and_skips_optional_agents(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1', 'A2']}))
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])
        self.assertEqual(r['model_calls']['by_agent'], {'orchestrator': 1, 'research_agent': 1, 'verification_agent': 1})
        self.assertEqual(r['agents_run'], ['orchestrator', 'research_agent', 'verification_agent'])
        self.assertFalse(decision(r, 'business_routing')[0]['run'])
        self.assertFalse(decision(r, 'chart_routing')[0]['run'])
        self.assertEqual(r['human_review'], {'status': 'pending', 'reviewer': None})
        self.assertFalse(r['approved'])

    def test_planned_subquestions_each_retrieve_and_share_the_evidence_budget(self):
        retriever = Retriever({'Compare': ['A1'], 'latency': ['C1'], 'Model Y': ['A2']})
        p = Provider(plan=[plan(subs=['Model Y accuracy', 'retrieval latency'])], research=[draft(X)],
                     verify=[verdicts(('supported', []))])
        r = run(p, retriever, question='Compare Model X accuracy with Model Y and the latency cost')
        self.assertEqual(retriever.calls, ['Compare Model X accuracy with Model Y and the latency cost', 'Model Y accuracy', 'retrieval latency'])
        self.assertEqual([e['chunk_id'] for e in r['evidence']], ['A1', 'A2', 'C1'])
        self.assertTrue(decision(r, 'decompose')[0]['run'])

    def test_invalid_plan_falls_back_to_the_baseline_route(self):
        p = Provider(plan=['{"question_type": "nonsense"}'], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['plan']['source'], 'fallback')
        self.assertEqual(r['status'], 'ok')

    def test_plan_cannot_invent_subquestion_count_beyond_limit(self):
        bad = plan(subs=['a b c d e', 'f g h i j', 'k l m n o', 'p q r s t'])
        p = Provider(plan=[bad], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['plan']['source'], 'fallback')


class Verification(unittest.TestCase):
    def test_with_and_without_headers_bind_values_without_negating_the_result(self):
        source = 'Metric: Fairness; With COT: -0.4385; Without COT: 0.3021'
        valid = ('The researchers reported fairness scores of -0.4385 with chain-of-thought (CoT) '
                 'and 0.3021 without CoT. The condition without CoT had the higher score.')
        for wording, expected in (
            (valid, None),
            ('Without CoT: 0.3021; With CoT: -0.4385.', None),
            ('Fairness was -0.4385 without CoT and 0.3021 with CoT.', 'condition_mismatch'),
            ('Fairness was 0.4385 with CoT and 0.3021 without CoT.', 'sign_flip'),
            ('Fairness was -0.4385 with CoT and 0.5 without CoT.', 'numbers_absent'),
            ('Without CoT, fairness did not reach 0.3021.', 'negation_mismatch'),
        ):
            with self.subTest(wording=wording):
                issues = agents.ground_claim({'text': wording, 'support': [{'quote': source}]})['contradictions']
                if expected is None:
                    self.assertEqual(issues, [])
                else:
                    self.assertIn(expected, issues)

    def test_condition_labels_do_not_mask_action_negation(self):
        source = ['Accuracy was 81% with caching.', 'Accuracy was 72% without caching.']
        valid = agents.ground_claim({'text': 'Accuracy was 72% without caching and 81% with caching.',
                                     'support': [{'quote': q} for q in source]})
        self.assertNotEqual(valid['status'], 'contradicted')
        unsupported = agents.ground_claim({'text': 'Accuracy was 72% with caching.',
                                          'support': [{'quote': q} for q in source]})
        self.assertIn('condition_mismatch', unsupported['contradictions'])
        negated = agents.ground_claim({'text': 'The test ended without reaching 81% accuracy.',
                                     'support': [{'quote': 'The test reached 81% accuracy.'}]})
        self.assertIn('negation_mismatch', negated['contradictions'])

    def test_verifier_uses_supported_wire_schema_and_validates_uniqueness_locally(self):
        class StrictTransport(Provider):
            def __call__(self, prompt, response_schema=None):
                if self.role(prompt) == 'verify' and 'uniqueItems' in json.dumps(response_schema):
                    raise ValueError('unsupported schema keyword')
                return super().__call__(prompt, response_schema)

        for issues, expected in (([], 'ok'), (['numeric_misread', 'numeric_misread'], 'insufficient_evidence')):
            with self.subTest(issues=issues):
                scripted = StrictTransport(plan=[plan()], research=[draft(X)],
                                           verify=[verdicts(('supported', issues))])
                result = run(scripted, Retriever({'Model X': ['A1']}))
                self.assertEqual(result['status'], expected)
                self.assertEqual(scripted.calls, ['plan', 'research', 'verify'])
                if issues:
                    self.assertIn('non-unique', result['verification'][0]['verification']['rejection'])

    def test_only_independently_supported_claims_are_kept(self):
        p = Provider(plan=[plan()], research=[draft(X, Y)],
                     verify=[verdicts(('supported', []), ('unsupported', ['missing_support']), coverage='partial')])
        r = run(p, Retriever({'Model X': ['A1', 'A2']}))
        self.assertEqual([c['text'] for c in r['summary']['claims']], [X['text']])
        self.assertEqual(r['summary']['held_claims'][0]['verification']['held_reason'], 'verifier judged unsupported (missing_support)')
        self.assertEqual(r['summary']['answer_scope'], 'partial')

    def test_deterministic_number_check_overrides_a_lenient_verifier(self):
        wrong = claim('Model X reached 91.0% accuracy.', 'A1', 'Model X reached 78.0% accuracy on the benchmark')
        p = Provider(plan=[plan()], research=[draft(wrong)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['status'], 'insufficient_evidence')
        held = r['summary']['held_claims'][0]['verification']
        self.assertEqual(held['deterministic']['numbers_and_qualifiers'], 'failed: numbers_absent')
        self.assertEqual(held['automated']['verdict'], 'supported')  # automated judgment recorded separately

    def test_supported_verdict_with_issues_is_not_accepted(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', ['overgeneralization']))])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['status'], 'insufficient_evidence')

    def test_malformed_verifier_output_fails_closed(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=['{"verdicts": []}'])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertEqual(r['summary']['claims'], [])

    def test_invented_quote_is_rejected_before_verification(self):
        fake = claim('Model X is the best model.', 'A1', 'Model X is clearly the best model available')
        p = Provider(plan=[plan()], research=[draft(fake)])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertEqual(p.calls, ['plan', 'research'])
        self.assertTrue(decision(r, 'draft_rejected'))

    def test_unknown_source_id_is_rejected(self):
        fake = claim('Model Z reached 99%.', 'Z9', 'Model Z reached 99% accuracy overall')
        p = Provider(plan=[plan()], research=[draft(fake)])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['status'], 'insufficient_evidence')

    def test_abstention_skips_verification(self):
        abstain = draft(status='insufficient_evidence')
        p = Provider(plan=[plan()], research=[abstain])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertEqual(p.calls, ['plan', 'research'])
        self.assertIn('Only one benchmark was reported.', r['summary']['limitations'])


class TargetedRetrieval(unittest.TestCase):
    REQUEST = {'needed': True, 'query': 'Model Y accuracy on the benchmark', 'reason': 'Y result missing'}

    def test_verifier_request_triggers_one_targeted_pass(self):
        retriever = Retriever({'Model Y': ['A2'], 'Model X': ['A1']})
        p = Provider(plan=[plan()], research=[draft(X), draft(X, Y)],
                     verify=[verdicts(('supported', []), coverage='partial', request=self.REQUEST),
                             verdicts(('supported', []), ('supported', []))])
        r = run(p, retriever, question='Compare Model X with the other model')
        self.assertEqual(p.calls, ['plan', 'research', 'verify', 'research', 'verify'])
        self.assertEqual(retriever.calls[-1], self.REQUEST['query'])
        self.assertEqual(len(r['summary']['claims']), 2)
        self.assertEqual(len(r['verification']), 2)
        self.assertTrue(decision(r, 'targeted_retrieval')[0]['run'])

    def test_at_most_one_retry_even_if_verifier_keeps_asking(self):
        again = {'needed': True, 'query': 'another search for Model Y', 'reason': 'still missing'}
        p = Provider(plan=[plan()], research=[draft(X), draft(X)],
                     verify=[verdicts(('supported', []), coverage='partial', request=self.REQUEST),
                             verdicts(('supported', []), coverage='partial', request=again)])
        r = run(p, Retriever({'Model Y': ['A2'], 'Model': ['A1']}))
        self.assertEqual(p.calls.count('research'), 2)
        self.assertEqual(r['status'], 'ok')

    def test_retry_skipped_when_budget_is_short(self):
        p = Provider(plan=[plan()], research=[draft(X)],
                     verify=[verdicts(('supported', []), coverage='partial', request=self.REQUEST)])
        r = run(p, Retriever({'Model': ['A1', 'A2']}), available_calls=lambda: 4)
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])
        self.assertIn('call(s) left', decision(r, 'targeted_retrieval')[0]['reason'])

    def test_failed_retry_keeps_the_first_verified_answer(self):
        bad = claim('Invented.', 'A2', 'this sentence is not in any passage')
        p = Provider(plan=[plan()], research=[draft(X), draft(bad)],
                     verify=[verdicts(('supported', []), coverage='partial', request=self.REQUEST)])
        r = run(p, Retriever({'Model': ['A1', 'A2']}))
        self.assertEqual([c['text'] for c in r['summary']['claims']], [X['text']])


class Business(unittest.TestCase):
    BUSINESS = {'status': 'ok', 'industry': 'Healthcare',
                'implications': [{'text': 'Fine-tuned models may improve accuracy in clinical documentation tasks.',
                                  'chunk_ids': ['A1'], 'suggested_action': 'Run a scoped pilot.',
                                  'assumptions': ['Benchmark transfers to clinical text.']}],
                'risks': ['Benchmark is not clinical.'], 'limitations': ['Single benchmark.']}

    def test_user_selected_industry_delegates_with_verified_claims_only(self):
        p = Provider(plan=[plan()], research=[draft(X, Y)],
                     verify=[verdicts(('supported', []), ('contradicted', ['contradiction']), coverage='partial')],
                     business=[self.BUSINESS])
        r = run(p, Retriever({'Model X': ['A1', 'A2']}), industry='Healthcare')
        self.assertEqual(p.calls, ['plan', 'research', 'verify', 'business'])
        self.assertEqual(r['business_insight']['status'], 'ok')
        prompt = p.prompts[-1][1]
        self.assertIn(X['text'], prompt)
        self.assertNotIn(Y['text'], prompt)       # held claim never reaches business advice
        self.assertNotIn('Model Y reached 64.5%', prompt)  # nor its uncited passage

    def test_business_citing_unverified_passage_is_rejected(self):
        bad = {**self.BUSINESS, 'implications': [{**self.BUSINESS['implications'][0], 'chunk_ids': ['A2']}]}
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))], business=[bad])
        r = run(p, Retriever({'Model X': ['A1', 'A2']}), industry='Healthcare')
        self.assertEqual(r['business_insight']['status'], 'failed')
        self.assertEqual(r['status'], 'ok')  # the verified research answer survives

    def test_industry_named_in_question_is_used(self):
        q = 'What does Model X accuracy mean for healthcare providers?'
        biz = {**self.BUSINESS, 'industry': 'healthcare'}
        p = Provider(plan=[plan(business=True, industry='healthcare')], research=[draft(X)],
                     verify=[verdicts(('supported', []))], business=[biz])
        r = run(p, Retriever({'Model X': ['A1']}), question=q)
        self.assertEqual(r['business_insight']['industry'], 'healthcare')

    def test_invented_industry_is_not_used(self):
        p = Provider(plan=[plan(business=True, industry='banking')], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}), question='What does Model X accuracy mean for businesses?')
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])
        self.assertIn('no industry was selected or named', decision(r, 'business_routing')[0]['reason'])

    def test_no_business_call_without_verified_findings(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('unsupported', ['missing_support']), coverage='none')])
        r = run(p, Retriever({'Model X': ['A1']}), industry='Healthcare')
        self.assertNotIn('business', p.calls)
        self.assertIsNone(r['business_insight'])

    def test_business_is_skipped_rather_than_exceeding_the_limit(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}), industry='Healthcare', available_calls=lambda: 3)
        self.assertEqual(r['status'], 'ok')
        self.assertTrue(decision(r, 'business_run'))


class Charts(unittest.TestCase):
    def test_chart_tool_is_model_free_and_receives_retrieved_passages(self):
        seen = []
        def tool(question, passages):
            seen.append([p['chunk_id'] for p in passages])
            return {'index_sha256': 'f' * 64, 'tables': [{'key': 'x#t4', 'status': 'complete'}], 'model_calls': 0}
        p = Provider(plan=[plan(chart=True)], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1', 'T1']}), chart_tool=tool, index_sha256='f' * 64)
        self.assertEqual(seen, [['A1', 'T1']])
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])
        self.assertEqual(r['charts']['tables'][0]['status'], 'complete')

    def test_chart_is_not_offered_when_no_answer_index_is_bound(self):
        tool = lambda q, ps: {'index_sha256': 'f' * 64, 'tables': [{'key': 'x#t4', 'status': 'complete'}]}  # noqa: E731
        p = Provider(plan=[plan(chart=True)], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1', 'T1']}), chart_tool=tool)
        self.assertEqual((r['charts']['status'], r['charts']['rejected']), ('unavailable', 'index_mismatch'))

    def test_explicit_chart_request_runs_even_if_plan_says_no(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}), question='Show a bar chart of Model X accuracy',
                chart_tool=lambda q, ps: {'tables': []})
        self.assertTrue(decision(r, 'chart_routing')[0]['run'])

    def test_chart_unavailable_without_tool(self):
        p = Provider(plan=[plan(chart=True)], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}))
        self.assertIn('not configured', decision(r, 'chart_routing')[0]['reason'])
        self.assertIsNone(r['charts'])

    def test_chart_tool_failure_does_not_lose_the_answer(self):
        def broken(q, ps):
            raise RuntimeError('audit missing')
        p = Provider(plan=[plan(chart=True)], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}), chart_tool=broken)
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['charts']['status'], 'failed')


class Limits(unittest.TestCase):
    def test_refuses_before_any_call_when_budget_is_too_small(self):
        p = Provider()
        r = run(p, Retriever({}), available_calls=lambda: 2)
        self.assertEqual(r['status'], 'execution_error')
        self.assertEqual(r['error']['cause'], 'call_budget')
        self.assertEqual(p.calls, [])

    def test_provider_failure_stops_the_run_without_retry(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[RuntimeError('Codex request timed out')])
        r = run(p, Retriever({'Model X': ['A1']}), industry='Healthcare')
        self.assertEqual(r['status'], 'execution_error')
        self.assertEqual(r['error'], {'stage': 'verification_agent', 'kind': 'provider', 'cause': 'timeout'})
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])
        self.assertIsNone(r['summary'])  # no unverified draft is returned as an answer

    def test_provider_failure_inside_shared_business_code_is_still_a_provider_failure(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))],
                     business=[RuntimeError('HTTP 429 rate limit')])
        r = run(p, Retriever({'Model X': ['A1']}), industry='Healthcare')
        # The verified research answer is kept; only the optional business step failed, as a provider failure.
        self.assertEqual(r['status'], 'ok')
        self.assertIsNone(r['error'])
        self.assertEqual((r['business_insight']['status'], r['business_insight']['cause']), ('failed', 'provider_failure'))

    def test_provider_failure_at_planning(self):
        p = Provider(plan=[RuntimeError('Approved cap of 4 calls reached; no call made.')])
        r = run(p, Retriever({}))
        self.assertEqual((r['error']['cause'], r['error']['kind']), ('per_run_call_cap', 'budget'))
        self.assertEqual(p.calls, ['plan'])

    def test_worst_case_never_exceeds_six_calls(self):
        req = TargetedRetrieval.REQUEST
        p = Provider(plan=[plan()], research=[draft(X), draft(X, Y)],
                     verify=[verdicts(('supported', []), coverage='partial', request=req),
                             verdicts(('supported', []), ('supported', []))],
                     business=[Business.BUSINESS])
        r = run(p, Retriever({'Model Y': ['A2'], 'Model': ['A1']}), industry='Healthcare')
        self.assertEqual(r['model_calls']['used'], 6)
        self.assertLessEqual(r['model_calls']['used'], agents.MAX_CALLS)

    def test_retrieval_errors_are_recorded_not_raised(self):
        def retriever(query, top_k):
            raise ValueError('Query would truncate; shorten it before retrying.')
        p = Provider(plan=[plan()])
        r = run(p, retriever)
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertEqual(p.calls, ['plan'])

    def test_trace_pairs_every_task_with_one_reply(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        r = run(p, Retriever({'Model X': ['A1']}))
        tasks = [e['task_id'] for e in r['trace'] if e['type'] == 'task']
        replies = [e['task_id'] for e in r['trace'] if e['type'] == 'reply']
        self.assertEqual(tasks, replies)
        research_reply = [e for e in r['trace'] if e['type'] == 'reply' and e['from'] == 'research_agent'][0]
        self.assertEqual(research_reply['output']['passage_ids'], ['A1'])  # IDs in the trace, not passage text
        self.assertNotIn('passages', research_reply['output'])


if __name__ == '__main__':
    unittest.main(verbosity=1)

"""Synthetic server/session integration coverage, not semantic model evaluation."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from src.indexed_clarification import ClarifyingIndexedResearch
from src.indexed_research import IndexedContextError
from src.research_pipeline import require_current_review
from tests.test_indexed_research import PASSAGES, IDENTITY, generator


def continued(query):
    return dict(decision='continue', resolved_query=query, question='', options=[])


def clarify(*, phase, query, history, passages):
    if phase == 'pre' and query == 'What are its limitations?' and not history:
        return dict(decision='clarify', resolved_query='', question='Which paper do you mean?',
                    options=[dict(text='Paper 1', support=[])])
    if phase == 'pre' and 'User clarification exchanges' in query:
        return continued('What are the limitations of Paper 1?')
    return continued(query)


def adapter(**kwargs):
    defaults = dict(retrieve=lambda q, k: deepcopy(PASSAGES), identity=lambda: deepcopy(IDENTITY),
        generate=generator, metadata={'provider': 'injected_test'}, index_path='/test/index',
        clarify_fn=clarify)
    return ClarifyingIndexedResearch(**{**defaults, **kwargs})


class SessionTests(unittest.TestCase):
    def payload(self, research, config, query, **extra):
        return dict(query=query, context_id=research.context_id,
                    conversation_id=config['conversation_id'], **extra)

    def test_prompt_context_survives_clarification_without_reextracting_answer(self):
        from unittest.mock import patch
        research = adapter()
        config = research.config()
        with patch('src.indexed_research.explicit_business_context', return_value='banking') as extract:
            response = research.execute(self.payload(research, config, 'What are its limitations?',
                                        interpret_context=True))
            self.assertEqual(response['scenario'], 'clarification')
            response = research.execute(self.payload(research, config, 'Paper 1', action='resume',
                                        interpret_context=True))
            self.assertEqual(extract.call_count, 1)
        self.assertEqual(response['result']['business_insight']['industry'], 'banking')

    def test_pending_resume_retains_original_question_industry_and_fresh_retrieval(self):
        calls = []
        research = adapter(retrieve=lambda q, k: calls.append(q) or deepcopy(PASSAGES))
        config = research.config()
        response = research.execute(self.payload(research, config, 'What are its limitations?', industry='banking'))
        self.assertEqual(response['scenario'], 'clarification')
        self.assertIsNone(response['result'])
        self.assertEqual(calls, [])
        response = research.execute(self.payload(research, config, 'Paper 1', action='resume'))
        self.assertEqual(response['result']['request']['query'], 'What are the limitations of Paper 1?')
        self.assertEqual(response['submitted_request']['query'], 'What are its limitations?')
        self.assertEqual(response['result']['business_insight']['industry'], 'banking')
        self.assertEqual(calls, ['What are the limitations of Paper 1?'])
        self.assertEqual(response['result']['provenance']['clarification']['turns'][0]['answer'], 'Paper 1')
        require_current_review(response['result'])

    def test_server_history_isolated_between_tabs_and_cleared_by_new_session(self):
        histories = []
        def observe(**kwargs):
            histories.append(deepcopy(kwargs['history']))
            return clarify(**kwargs)
        research = adapter(clarify_fn=observe)
        a, b = research.config(), research.config()
        self.assertNotEqual(a['conversation_id'], b['conversation_id'])
        research.execute(self.payload(research, a, 'Compare the studies.'))
        research.execute(self.payload(research, a, 'What are its limitations?'))
        self.assertTrue(histories[-1])
        response = research.execute(self.payload(research, b, 'What are its limitations?'))
        self.assertEqual(response['scenario'], 'clarification')
        self.assertEqual(histories[-1], [])
        c = research.config()
        self.assertEqual(research.execute(self.payload(research, c, 'What are its limitations?'))['scenario'], 'clarification')

    def test_business_failure_after_resume_recovers_with_original_request(self):
        research = adapter()
        config = research.config()
        original = self.payload(research, config, 'What are its limitations?', industry='banking')
        research.execute(original)
        with patch('src.indexed_research.translate', side_effect=RuntimeError('Injected business failure')):
            partial = research.execute(self.payload(research, config, 'Paper 1', action='resume'))
        self.assertEqual(partial['scenario'], 'partial')
        self.assertEqual(partial['result']['summary']['status'], 'ok')
        self.assertEqual(partial['submitted_request']['query'], original['query'])
        with self.assertRaises(IndexedContextError):
            research.execute(self.payload(research, config, 'Paper 1', action='resume'))
        recovered = research.execute({**original, 'action': 'ask'})
        self.assertEqual(recovered['scenario'], 'full')
        self.assertEqual(recovered['result']['business_insight']['industry'], 'banking')
        self.assertEqual(partial['result']['summary']['status'], 'ok')

    def test_unknown_expired_and_wrong_context_rejected(self):
        now = [0]
        research = adapter(clock=lambda: now[0], ttl=30)
        config = research.config()
        for payload in [dict(query='Q', context_id=research.context_id),
                        self.payload(research, {'conversation_id': 'forged'}, 'Q'),
                        dict(query='Q', context_id='old', conversation_id=config['conversation_id'])]:
            with self.assertRaises(IndexedContextError):
                research.execute(payload)
        now[0] = 31
        with self.assertRaises(IndexedContextError):
            research.execute(self.payload(research, config, 'Q'))

    def test_pending_and_capacity_are_not_silently_overwritten(self):
        research = adapter(max_sessions=1)
        config = research.config()
        research.execute(self.payload(research, config, 'What are its limitations?'))
        with self.assertRaises(ValueError):
            research.config()
        with self.assertRaises(IndexedContextError):
            research.execute(self.payload(research, config, 'New unrelated question'))
        self.assertIsNotNone(research.execute(self.payload(research, config, 'Paper 1', action='resume'))['result'])

    def test_post_options_include_retrieved_sources_but_no_draft(self):
        def post(**kwargs):
            if kwargs['phase'] == 'post':
                return dict(decision='clarify', resolved_query='', question='Which result?', options=[
                    dict(text='Paper 1 result', support=[{'chunk_id': 'p1', 'quote': PASSAGES[0]['text']}])])
            return continued(kwargs['query'])
        research = adapter(clarify_fn=post)
        response = research.execute(self.payload(research, research.config(), 'Compare'))
        self.assertEqual(response['phase'], 'post')
        self.assertEqual(response['clarification_evidence'], PASSAGES)
        self.assertIsNone(response['result'])

    def test_retry_retains_pending_and_sanitizes_failure(self):
        fail = [False]
        def injected(**kwargs):
            if fail[0]:
                raise RuntimeError('SECRET_TOKEN')
            return clarify(**kwargs)
        research = adapter(clarify_fn=injected)
        config = research.config()
        research.execute(self.payload(research, config, 'What are its limitations?'))
        fail[0] = True
        failed = research.execute(self.payload(research, config, 'Paper 1', action='resume'))
        self.assertEqual(failed['error']['stage'], 'Clarification (pre)')
        self.assertNotIn('SECRET_TOKEN', str(failed))
        fail[0] = False
        self.assertIsNotNone(research.execute(self.payload(research, config, 'Paper 1', action='resume'))['result'])

    def test_changed_index_rejects_session_even_with_valid_token(self):
        research = adapter()
        config = research.config()
        with patch.object(research, 'identity', return_value={'count': 99}):
            with self.assertRaises(IndexedContextError):
                research.execute(self.payload(research, config, 'Q'))

    def test_empty_index_clear_question_abstains_without_post_or_summary(self):
        phases = []
        def record(**kwargs):
            phases.append(kwargs['phase'])
            return continued(kwargs['query'])
        def forbidden(*a, **kw):
            self.fail('Empty evidence must not generate a summary')
        research = adapter(retrieve=lambda q, k: [], clarify_fn=record, generate=forbidden)
        response = research.execute(self.payload(research, research.config(), 'Clear research question'))
        self.assertEqual(response['scenario'], 'empty')
        self.assertEqual(phases, ['pre'])

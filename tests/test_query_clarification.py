"""Offline contract/orchestration regressions, not model-quality measurements."""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from src.query_clarification import (
    ClarifyingResearch, clarification_with_generation, validate_decision,
)
from src.research_pipeline import PipelineError, require_current_review
from tests.research_fixtures import demo_retrieve, demo_summary, demo_translate


def proceed(query='agents'):
    return {'decision': 'continue', 'resolved_query': query, 'question': '', 'options': []}


def clarify():
    return {'decision': 'clarify', 'resolved_query': '',
            'question': 'Which method do you mean?', 'options': []}


class ClarificationTests(unittest.TestCase):
    def make_session(self, decisions=None, **kwargs):
        self.gate = Mock(side_effect=decisions or (lambda **kw: proceed(kw['query'])))
        self.retrieve = Mock(side_effect=demo_retrieve)
        self.summary = Mock(side_effect=lambda q, ps, **kw: demo_summary(q, ps))
        return ClarifyingResearch(context_id='corpus-config-A', clarify_fn=self.gate,
            retrieve=kwargs.pop('retrieve', self.retrieve), summarize_fn=self.summary, **kwargs)

    def ask(self, session, query='agents', **kwargs):
        return session.ask({'query': query, **kwargs}, context_id='corpus-config-A')

    def test_clear_question_runs_both_gates_and_existing_business_contract(self):
        session = self.make_session(translate_fn=demo_translate)
        result = self.ask(session, industry='banking')['result']
        self.assertEqual([c.kwargs['phase'] for c in self.gate.call_args_list], ['pre', 'post'])
        self.assertEqual(result['evidence'], demo_retrieve('agents', 5))
        self.assertFalse(result['approved'])
        self.assertEqual(result['human_review']['status'], 'pending')
        self.assertEqual(result['business_insight']['status'], 'ok')
        require_current_review(result)

    def test_pre_ambiguity_blocks_retrieval_and_resumes_original_request(self):
        session = self.make_session([clarify(), proceed('Granite limitations'),
                                     proceed('Granite limitations')])
        pending = self.ask(session, 'What are its limitations?')
        self.assertEqual(pending['status'], 'clarification_required')
        self.assertIsNone(pending['result'])
        self.retrieve.assert_not_called()
        self.summary.assert_not_called()
        # Returned payload is not mutable session state.
        pending['original_request']['query'] = 'tampered'
        result = session.resume('Granite', context_id='corpus-config-A')['result']
        self.assertEqual(result['request']['query'], 'Granite limitations')
        trace = result['provenance']['clarification']
        self.assertEqual(trace['original_request']['query'], 'What are its limitations?')
        self.assertEqual(trace['turns'][0]['answer'], 'Granite')
        self.assertIn('Granite', self.gate.call_args_list[1].kwargs['query'])

    def test_post_ambiguity_blocks_synthesis_then_retrieves_fresh_on_resume(self):
        decision = clarify()
        passage = demo_retrieve('agents', 5)[0]
        decision['options'] = [{'text': 'Task-specific evaluation', 'support': [
            {'chunk_id': passage['chunk_id'], 'quote': passage['text']}]}]
        session = self.make_session([proceed(), decision, proceed('evaluation'), proceed('evaluation')])
        pending = self.ask(session)
        self.assertEqual(pending['phase'], 'post')
        self.summary.assert_not_called()
        session.resume('evaluation', context_id='corpus-config-A')
        self.assertEqual(self.retrieve.call_count, 2)
        self.summary.assert_called_once()

    def test_context_resolved_followup_passes_history_not_as_evidence(self):
        session = self.make_session()
        self.ask(session, 'Explain Granite')
        result = self.ask(session, 'What are its limitations?')['result']
        history = self.gate.call_args_list[2].kwargs['history']
        self.assertEqual(history[0]['content'], 'Explain Granite')
        self.assertEqual(self.summary.call_args.kwargs['history'], history)
        self.assertEqual(result['evidence'], demo_retrieve('agents', 5))

    def test_missing_evidence_is_not_a_clarification(self):
        session = self.make_session(retrieve=lambda q, k: [])
        result = self.ask(session)['result']
        self.assertEqual(self.gate.call_count, 1)
        self.summary.assert_not_called()
        self.assertEqual(result['summary']['status'], 'insufficient_evidence')

    def test_nonempty_irrelevant_evidence_can_abstain(self):
        session = self.make_session()
        self.summary.side_effect = lambda q, ps, **kw: {
            'query': q, 'status': 'insufficient_evidence', 'claims': [],
            'limitations': ['Evidence does not address the question.']}
        self.assertEqual(self.ask(session)['result']['summary']['status'], 'insufficient_evidence')
        self.assertEqual(self.gate.call_count, 2)

    def test_cross_context_client_history_and_overlapping_request_rejected(self):
        session = self.make_session([clarify()])
        with self.assertRaisesRegex(ValueError, 'Context changed'):
            session.ask({'query': 'agents'}, context_id='corpus-B')
        with self.assertRaisesRegex(ValueError, 'session-owned'):
            self.ask(session, history=[])
        self.ask(session)
        with self.assertRaisesRegex(ValueError, 'pending'):
            self.ask(session)
        with self.assertRaisesRegex(ValueError, 'Context changed'):
            session.resume('Granite', context_id='corpus-B')
        self.retrieve.assert_not_called()

    def test_invalid_or_ungrounded_options_fail_closed(self):
        passage = demo_retrieve('agents', 5)[0]
        for support in ([], [{'chunk_id': 'unknown', 'quote': passage['text']}],
                        [{'chunk_id': passage['chunk_id'], 'quote': 'Fabricated source quotation.'}]):
            decision = clarify()
            decision['options'] = [{'text': 'Choice', 'support': support}]
            session = self.make_session([proceed(), decision])
            with self.subTest(support=support), self.assertRaises(PipelineError):
                self.ask(session)
            self.summary.assert_not_called()
        decision = proceed()
        decision['question'] = 'Unexpected question'
        with self.assertRaises(ValueError):
            validate_decision(decision, phase='pre', passages=[])

    def test_post_cannot_rewrite_question_without_new_retrieval(self):
        session = self.make_session([proceed(), proceed('different question')])
        with self.assertRaisesRegex(PipelineError, 'changed the question'):
            self.ask(session)
        self.summary.assert_not_called()

    def test_failures_are_distinct_from_clarification_and_sanitized(self):
        for where in ('gate', 'retrieval'):
            session = self.make_session()
            target = self.gate if where == 'gate' else self.retrieve
            target.side_effect = RuntimeError('SECRET provider body')
            with self.subTest(where=where), self.assertRaises(PipelineError) as cm:
                self.ask(session)
            self.assertNotIn('SECRET', str(cm.exception))
            self.summary.assert_not_called()

    def test_history_is_bounded_and_mutating_adapter_cannot_change_state(self):
        session = self.make_session()
        for number in range(10):
            self.ask(session, f'Question {number}')
        self.assertEqual(len(self.summary.call_args.kwargs['history']), 12)
        self.assertEqual(self.summary.call_args.kwargs['history'][0]['content'], 'Question 3')
        def mutate(**kwargs):
            kwargs['history'].clear()
            kwargs['passages'].clear()
            return proceed(kwargs['query'])
        self.gate.side_effect = mutate
        result = self.ask(session)['result']
        self.assertEqual(len(result['evidence']), 2)
        self.assertEqual(len(self.summary.call_args.kwargs['history']), 12)

    def test_prompted_adapter_schema_capability_and_context(self):
        generate = Mock(return_value=json.dumps(proceed()))
        generate.supports_response_schema = True
        value = clarification_with_generation(phase='pre', query='agents', history=[],
                                              passages=[], generate=generate)
        self.assertEqual(value, proceed())
        self.assertIn('response_schema', generate.call_args.kwargs)
        self.assertIn('NOT source evidence', generate.call_args.args[0])
        for raw in ('not json', '{"decision":"continue","decision":"clarify"}',
                    json.dumps({**proceed(), 'approved': True})):
            with self.subTest(raw=raw), self.assertRaises(PipelineError):
                clarification_with_generation(phase='pre', query='agents', history=[],
                    passages=[], generate=lambda prompt: raw)

    def test_retry_keeps_pending_on_provider_failure(self):
        session = self.make_session([clarify(), RuntimeError('SECRET'),
                                     proceed('Granite'), proceed('Granite')])
        self.ask(session)
        with self.assertRaises(PipelineError):
            session.resume('Granite', context_id='corpus-config-A')
        self.assertEqual(session.resume('Granite', context_id='corpus-config-A')['status'], 'complete')

    def test_answer_bounds_and_no_pending(self):
        session = self.make_session()
        for answer in ('', 'a' * 6001, '\ud800'):
            with self.assertRaises(ValueError):
                session.resume(answer, context_id='corpus-config-A')
        with self.assertRaisesRegex(ValueError, 'No pending'):
            session.resume('Granite', context_id='corpus-config-A')

    def test_clarification_round_limit(self):
        session = self.make_session([clarify()] * 4)
        self.ask(session)
        for _ in range(2):
            self.assertEqual(session.resume('Method', context_id='corpus-config-A')['status'],
                             'clarification_required')
        with self.assertRaisesRegex(ValueError, 'limit reached'):
            session.resume('Method', context_id='corpus-config-A')
        self.retrieve.assert_not_called()

    def test_development_cases_and_report_error_accounting(self):
        from scripts.evaluate_clarification import evaluate
        cases = json.loads((Path(__file__).parent / 'fixtures/clarification/development.json').read_text())
        from src.research_contracts import validate_evidence
        for case in cases:
            validate_evidence(case['passages'])
        # A fixed fake classifier exercises reporting only, not classification quality.
        report = evaluate(cases, lambda **kw: proceed(kw['query']))
        self.assertEqual(report['total'], 8)
        self.assertEqual(report['correct'], 5)
        self.assertEqual(report['missed_ambiguities'], 3)
        self.assertEqual(report['errors'], 0)
        report = evaluate(cases, Mock(side_effect=RuntimeError('SECRET')))
        self.assertEqual(report['errors'], 8)
        self.assertEqual(report['correct'], 0)
        self.assertNotIn('SECRET', json.dumps(report))


if __name__ == '__main__':
    unittest.main()

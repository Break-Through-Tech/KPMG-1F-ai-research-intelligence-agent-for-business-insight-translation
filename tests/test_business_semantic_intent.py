"""Semantic intent classifier: validation, isolation, single attempt and resolution order (offline)."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.brief_store import BriefStore
from src.business_demo import automatic_offer, research_business_flags
from src.business_insights import automatic_business_context, resolve_business_intent
from src.business_intent import SCHEMA, VERSION, build_prompt, classify, trusted_value, validate
from tests.test_downstream_business import result_for

ROOT = Path(__file__).resolve().parents[1]
PILOT = json.loads((ROOT / 'tests/fixtures/business/semantic-pilot-v1.json').read_text(encoding='utf-8'))['rows']
ACCOUNTING = 'Our accounting team spends hours checking invoices for mistakes. Could AI agents help without increasing the number of errors?'
BOARD = "Our board keeps asking about AI and I honestly don't know where to begin. Where should we even start thinking about it?"


def output(**value):
    base = {'is_business': True, 'industry': 'accounting', 'workflow': 'checking invoices for mistakes',
            'decision': 'Could AI agents help without increasing the number of errors', 'confidence': 'high'}
    return json.dumps({'business_context': {**base, **value}})


def record(question, **value):
    return classify(question, Mock(return_value=output(**value)))


class ValidationTests(unittest.TestCase):
    def test_prompt_is_the_piloted_text_and_schema(self):
        prompt = build_prompt('Freight dispatch mistakes eat margin. Automate it?')
        self.assertTrue(prompt.startswith('Classify the QUESTION below.'))
        self.assertIn('"question": "Freight dispatch mistakes eat margin. Automate it?"', prompt)
        self.assertEqual(SCHEMA['required'], ['business_context'])

    def test_spans_must_be_verbatim_and_unknown_values_fail(self):
        clean = validate(output(), ACCOUNTING)
        self.assertEqual(clean['workflow'], 'checking invoices for mistakes')
        invented = validate(output(workflow='automated invoice reconciliation'), ACCOUNTING)
        self.assertEqual((invented['workflow'], invented['workflow_rejected']), ('', True))
        for bad in (output(industry='fintech'), output(confidence='certain'),
                    json.dumps({'business_context': {'is_business': True}}), 'not json'):
            with self.subTest(bad=bad[:40]):
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    validate(bad, ACCOUNTING)


class IsolationTests(unittest.TestCase):
    def test_one_attempt_and_failures_are_recorded_not_raised(self):
        class QuotaExhausted(Exception):
            pass
        for error, reason in ((RuntimeError('503'), 'provider'), (QuotaExhausted(), 'local_budget')):
            generate = Mock(side_effect=error)
            result = classify(ACCOUNTING, generate)
            self.assertEqual((result['status'], result['reason']), ('unavailable', reason))
            generate.assert_called_once()
        self.assertEqual(classify(ACCOUNTING, Mock(return_value='{"x":1}'))['status'], 'invalid')

    def test_server_wrapper_never_blocks_or_changes_research(self):
        sys.path.insert(0, str(ROOT / 'experiments/render-staging'))
        import server
        answer = {'mode': 'indexed', 'result': {'summary': {'status': 'ok'}}}
        execute = Mock(return_value=dict(answer))
        budget = Mock()
        wrapped = server.semantic_intent(execute, Mock(side_effect=RuntimeError('provider down')), budget)
        response = wrapped({'query': ACCOUNTING}, session_id='s')
        execute.assert_called_once_with({'query': ACCOUNTING}, session_id='s')
        self.assertEqual(response['result'], answer['result'])
        self.assertEqual(response['business_intent']['status'], 'unavailable')
        budget.reserve.assert_called_once()
        generate = Mock(return_value=output())
        response = server.semantic_intent(Mock(return_value=dict(answer)), generate, Mock())({'query': ACCOUNTING})
        self.assertEqual(response['business_intent']['status'], 'ok')
        generate.assert_called_once()
        self.assertEqual(generate.call_args.kwargs['response_schema']['required'], ['business_context'])
        # A slow classifier cannot hold up the answer beyond the bounded wait.
        server.INTENT_WAIT_SECONDS, saved = 0.05, server.INTENT_WAIT_SECONDS
        try:
            release = threading.Event()
            slow = Mock(side_effect=lambda *a, **k: release.wait(5) or output())
            response = server.semantic_intent(Mock(return_value=dict(answer)), slow, Mock())({'query': ACCOUNTING})
            self.assertEqual(response['business_intent'], {'status': 'unavailable', 'reason': 'timeout'})
            release.set()
        finally:
            server.INTENT_WAIT_SECONDS = saved


class ResolutionTests(unittest.TestCase):
    def test_semantic_is_primary_and_corrects_the_rules(self):
        resolved = resolve_business_intent(ACCOUNTING, record(ACCOUNTING))
        self.assertEqual(resolved['source'], 'semantic')
        self.assertEqual(resolved['context']['workflow'], 'checking invoices for mistakes')  # rules: wrong span
        self.assertNotEqual(automatic_business_context(ACCOUNTING)['workflow'], resolved['context']['workflow'])
        board = resolve_business_intent(BOARD, record(BOARD, industry='unspecified', workflow='', decision=''))
        self.assertIsNone(board['context'])  # rules would auto-dispatch this vague question
        self.assertIsNotNone(automatic_business_context(BOARD))
        self.assertEqual(board['hint']['missing'], ['workflow'])
        academic = 'Has any paper benchmarked a legal research product against a plain frontier model?'
        self.assertEqual(resolve_business_intent(academic, record(academic, is_business=False, workflow='', decision='')),
                         {'source': 'semantic', 'context': None, 'hint': None})

    def test_low_confidence_or_rejected_span_asks_instead_of_dispatching(self):
        for value in ({'confidence': 'low'}, {'workflow': 'invoice automation'}):
            with self.subTest(value=value):
                resolved = resolve_business_intent(ACCOUNTING, record(ACCOUNTING, **value))
                self.assertIsNone(resolved['context'])
                self.assertEqual(resolved['hint']['industry'], 'accounting')

    def test_explicit_research_only_wins_and_rules_are_only_a_fallback(self):
        question = ACCOUNTING + ' Research only, no business insights.'
        self.assertEqual(resolve_business_intent(question, record(question))['source'], 'research_only')
        for unusable in (None, {'status': 'unavailable'}, {'status': 'ok', 'version': 'other', 'value': {}},
                         {'status': 'ok', 'version': VERSION, 'value': {'is_business': 'yes'}}):
            with self.subTest(record=unusable):
                self.assertEqual(resolve_business_intent(ACCOUNTING, unusable)['source'], 'rules')

    def test_stored_records_are_revalidated(self):
        tampered = record(ACCOUNTING)
        tampered['value'] = {**tampered['value'], 'workflow': 'approve all supplier payments'}
        self.assertEqual(trusted_value(tampered, ACCOUNTING)['workflow'], '')
        self.assertIsNone(resolve_business_intent(ACCOUNTING, tampered)['context'])

    def test_recorded_pilot_outputs_resolve_as_measured(self):
        for row in PILOT:
            with self.subTest(q=row['q'][:50]):
                rec = classify(row['q'], Mock(return_value=json.dumps(row['model_output'])))
                resolved = resolve_business_intent(row['q'], rec)
                if row['label'] != 'business':
                    self.assertIsNone(resolved['context'])
                elif resolved['context']:
                    self.assertIn(resolved['context']['workflow'].casefold(), ' '.join(row['q'].split()).casefold())
        auto = sum(bool(resolve_business_intent(r['q'], classify(r['q'], Mock(return_value=json.dumps(r['model_output']))))['context'])
                   for r in PILOT if r['label'] == 'business')
        self.assertEqual(auto, sum(r['label'] == 'business' for r in PILOT))


class DispatchTests(unittest.TestCase):
    def test_saved_classification_drives_offer_hint_and_one_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            store = BriefStore(Path(directory) / 'briefs.sqlite3')

            def saved(question, intent):
                body = store.save({'mode': 'indexed', 'submitted_request': {'query': question}, 'result': result_for(),
                                   'business_intent': intent})
                return {**body, 'library': {**body['library'], 'replayed': False}}
            fresh = saved(ACCOUNTING, record(ACCOUNTING))
            self.assertTrue(research_business_flags(fresh)['business_auto'])
            reopened = store.load(fresh['library']['brief']['id'])
            self.assertEqual(reopened['business_intent']['status'], 'ok')  # persisted with the answer
            self.assertFalse(automatic_offer({**fresh, 'library': {**fresh['library'], 'replayed': True}}))
            hinted = research_business_flags(saved(BOARD, record(BOARD, industry='unspecified', workflow='', decision='')))
            self.assertNotIn('business_auto', hinted)
            self.assertEqual(hinted['business_hint']['missing'], ['workflow'])


if __name__ == '__main__':
    unittest.main()

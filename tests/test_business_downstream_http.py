"""Local fake-provider endpoint checks; never contact a research engine/model."""
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import Mock

from src.brief_store import BriefStore
from src.business_demo import BusinessHandler, automatic_offer
from src.business_insights import automatic_business_context, derive_business_context
from src.research_demo import DemoHandler
from tests.test_downstream_business import CONTEXT, business, result_for


class BusinessHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BriefStore(Path(self.tmp.name) / 'briefs.sqlite3')
        self.saved = self.store.save({'mode': 'indexed', 'scenario': 'summary-only',
            'result': result_for(), 'error': None})
        self.generator = Mock(return_value=json.dumps(business()))
        self.handler = type('IsolatedBusinessHandler', (BusinessHandler,), {
            'library': self.store, 'business_generate': staticmethod(self.generator),
            'business_metadata': {'execution': 'injected_fixture'}, 'research': None})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), self.handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True); self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.tmp.cleanup()

    def payload(self):
        return {'brief_id': self.saved['library']['brief']['id'],
            'expected_version': self.saved['library']['version']['id'],
            'fingerprint': self.saved['result']['review_fingerprint'], 'context': CONTEXT}

    def request(self, path='/api/business', payload=None, headers=None, method='POST'):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request(method, path, body=json.dumps(self.payload() if payload is None else payload) if method == 'POST' else None,
                     headers=headers or {'Content-Type': 'application/json'})
        response = conn.getresponse(); data = json.loads(response.read()); conn.close()
        return response.status, data

    def test_one_translation_saves_a_new_version_and_stale_retry_spends_no_call(self):
        original = self.saved['result']
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['result']['business_insight']['status'], 'ok')
        self.assertEqual(data['result']['summary'], original['summary'])
        self.assertEqual(data['library']['version']['number'], 2)
        self.assertEqual(self.request()[0], 409)
        self.assertEqual(self.generator.call_count, 1)

    def test_rejects_stale_fingerprint_context_and_client_supplied_evidence(self):
        for change in ({'fingerprint': 'stale'}, {'context': {}}, {'result': result_for()}):
            self.assertEqual(self.request(payload={**self.payload(), **change})[0], 400)
        self.generator.assert_not_called()

    def test_failure_keeps_research_in_new_snapshot(self):
        self.generator.side_effect = RuntimeError('SECRET')
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['error']['stage'], 'business')
        self.assertEqual(data['result']['summary'], self.saved['result']['summary'])
        self.assertNotIn('SECRET', json.dumps(data))

    def test_origin_and_capability_boundaries(self):
        self.assertEqual(self.request(payload={}, headers={'Content-Type': 'application/json', 'Origin': 'https://external.invalid'})[0], 403)
        status, config = self.request('/api/config', method='GET')
        self.assertEqual(status, 200)
        self.assertTrue(config['business_translation'])
        self.assertIsNone(self.handler.research)
        self.assertFalse(hasattr(DemoHandler, 'business_generate'))
        self.generator.assert_not_called()

    def test_fixture_identity_survives_translation(self):
        self.saved = self.store.save({'mode': 'fixture', 'fixture_file': 'synthetic-source',
            'scenario': 'summary-only', 'result': result_for(), 'error': None})
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['mode'], 'fixture')
        self.assertEqual(data['result']['provenance']['business_translation']['research_input']['fixture_file'], 'synthetic-source')

    def test_model_generation_on_fixture_research_is_not_handwritten_output(self):
        self.saved = self.store.save({'mode': 'fixture', 'fixture_file': 'synthetic-source',
            'scenario': 'summary-only', 'result': result_for(), 'error': None})
        # Simulated provider metadata only: the generator is still the same Mock.
        self.handler.business_metadata = {'provider': 'simulated_model'}
        status, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(data['mode'], 'saved-real-result')
        self.assertIsNone(data['fixture_file'])
        info = data['result']['provenance']['business_translation']
        self.assertEqual(info['research_input']['kind'], 'fixture')
        self.assertEqual(info['generation_kind'], 'model')

    def test_repeat_translation_retains_prior_review_and_original_version(self):
        _, first = self.request()
        reviewed = self.store.review(first['library']['brief']['id'],
            version_id=first['library']['version']['id'], fingerprint=first['library']['version']['fingerprint'],
            reviewer='Automated offline fixture QA', decision='approve', notes='Synthetic only')
        self.saved = reviewed
        status, second = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(second['library']['version']['number'], 3)
        self.assertEqual(second['library']['reviews'], [])
        self.assertFalse(second['result']['approved'])
        old = self.store.load(first['library']['brief']['id'], first['library']['version']['id'])
        self.assertEqual(old['library']['reviews'][0]['decision'], 'approve')
        self.assertEqual(second['result']['summary'], first['result']['summary'])


    def test_automatic_context_uses_saved_question_and_only_one_business_call(self):
        question = ('The review board has been shown tool-call success logs. '
                    'What should it ask for before relying on the assistant to explain invoice mismatches?')
        result = result_for()
        self.saved = self.store.save({'mode': 'indexed', 'scenario': 'summary-only',
                                      'submitted_request': {'query': question}, 'result': result, 'error': None})
        self.generator.return_value = json.dumps({**business(), 'industry': 'Industry unspecified'})
        status, response = self.request(payload={**self.payload(), 'context': {}})
        self.assertEqual(status, 200)
        context = response['result']['provenance']['business_translation']['context']
        self.assertEqual(context['industry'], 'Industry unspecified')
        self.assertEqual(context['workflow'], 'the assistant to explain invoice mismatches')
        self.assertEqual(context['decision'], question)
        self.assertEqual(response['submitted_request']['query'], question)
        self.assertEqual(response['result']['summary'], result['summary'])
        self.assertEqual(response['result']['evidence'], result['evidence'])
        self.generator.assert_called_once()

    def test_customize_missing_application_without_a_call(self):
        status, response = self.request(payload={**self.payload(), 'context': {'industry': 'banking'}})
        self.assertEqual(status, 400)
        self.assertIn('Add a business workflow', response['error'])
        self.generator.assert_not_called()

    def test_automatic_offer_and_saved_financial_services_context(self):
        question = 'What are the business implications of AI model routing in financial services?'
        source = {'mode': 'indexed', 'submitted_request': {'query': question}, 'result': result_for()}
        self.assertFalse(automatic_offer(source))
        self.saved = self.store.save(source)
        just_saved = {**self.saved, 'library': {**self.saved['library'], 'replayed': False}}
        self.assertTrue(automatic_offer(just_saved))
        self.assertFalse(automatic_offer({**self.saved, 'library': {**self.saved['library'], 'replayed': True}}))
        self.assertFalse(automatic_offer({**just_saved, 'result': {**source['result'], 'evidence': []}}))
        self.generator.return_value = json.dumps({**business(), 'industry': 'financial services'})
        payload = {**self.payload(), 'context': {}, 'automatic': True}
        self.assertEqual(self.request(payload={**payload, 'context': CONTEXT})[0], 400)
        status, translated = self.request(payload=payload)
        self.assertEqual(status, 200)
        self.assertEqual(translated['result']['business_insight']['industry'], 'financial services')
        self.assertEqual(translated['result']['summary'], source['result']['summary'])
        self.assertEqual(translated['result']['evidence'], source['result']['evidence'])
        self.assertEqual(self.request(payload=payload)[0], 409)
        self.generator.assert_called_once()

    def test_automatic_mode_leaves_technical_or_unclear_questions_optional(self):
        for question in ('How does AI model routing work?', 'Summarize model routing research in financial services.',
                         'What are the business implications?',
                         'How should we use model routing in banking? Research only, no business insights.'):
            with self.subTest(question=question):
                self.assertIsNone(automatic_business_context(question))
                self.saved = self.store.save({'mode': 'indexed', 'submitted_request': {'query': question},
                                              'result': result_for()})
                self.assertFalse(automatic_offer(self.saved))
                self.assertEqual(self.request(payload={**self.payload(), 'context': {}, 'automatic': True})[0], 400)
        self.generator.assert_not_called()

    def test_automatic_intent_recognizes_industry_and_objective_variations(self):
        cases = (
            ('banking', 'In banking, how should teams evaluate automation before using it for credit-risk review?', 'credit-risk review'),
            ('financial services', 'How can AI model routing help financial services firms reduce operational costs '
             'without compromising response quality, and what evidence should decision-makers require before '
             'investing in such a system?', 'AI model routing'),
            ('financial services', 'Assess how financial services firms can cut operating costs through document extraction.', 'document extraction'),
            ('logistics', 'We are reviewing dispatch in logistics. What evidence should we require before investing?', 'dispatch'),
            ('healthcare', 'Healthcare providers want to reduce operating costs. How should we evaluate patient intake workflow?', 'patient intake'),
            ('retail', 'Compare automation for customer returns across retail operations.', 'customer returns'),
            ('insurance', 'Which checks should insurers run before using AI for claims triage?', 'claims triage'),
            ('banking', 'What evidence should banks collect to compare model routing costs before adopting it?', 'model routing'),
            ('insurance', 'Assess whether to deploy AI for claims processing. Industry: insurance.', 'claims processing'),
        )
        for sector, question, workflow in cases:
            with self.subTest(question=question):
                context = automatic_business_context(question)
                self.assertIsNotNone(context)
                self.assertEqual(context['industry'], sector)
                self.assertIn(workflow, context['workflow'])
                self.assertIn(context['workflow'], question)
                self.assertEqual(context['decision'], question)
        for question in (
                'How can model routing improve benchmark accuracy in healthcare?',
                'Compare model routing ablation results in financial services papers.',
                'What does the banking model-routing paper report about accuracy?',
                'How does dynamic programming choose a route?',
                'What are the business implications of model routing in retail? Academic only.'):
            with self.subTest(question=question):
                self.assertIsNone(automatic_business_context(question))

    def test_context_derivation_and_explicit_overrides(self):
        question = 'In banking, what should we measure before using invoice routing?'
        self.assertEqual(derive_business_context(question, {}),
                         {'industry': 'banking', 'workflow': 'invoice routing', 'decision': question})
        self.assertEqual(derive_business_context(question, {'workflow': 'manual triage'})['workflow'],
                         'manual triage')
        self.assertEqual(derive_business_context('What did the study measure?', {'workflow': 'invoice triage'}),
                         {'industry': 'Industry unspecified', 'workflow': 'invoice triage',
                          'decision': ''})
        with self.assertRaises(ValueError):
            derive_business_context(question, {'internal_system': 'invented'})
        for applied in (
            'Which routing decisions are worth examining for multilingual grant enquiries?',
            'What additional evidence should staffing require before using the assistant in planning meetings?',
            'Can the image-compression result inform a decision about sending fewer bytes from field sites?',
            'Which release-review questions follow from combining coverage checks with clean rerun evaluation?',
        ):
            with self.subTest(applied=applied):
                context = derive_business_context(applied, {})
                self.assertIn(context['workflow'], applied)
                self.assertEqual(context['decision'], applied)
                self.assertEqual(context['industry'], 'Industry unspecified')


if __name__ == '__main__': unittest.main()

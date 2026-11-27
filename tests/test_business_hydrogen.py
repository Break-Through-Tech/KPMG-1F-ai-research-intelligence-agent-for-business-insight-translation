"""Hydrogen business generator configuration, bounded 503 retry and recorded-output replay. No model calls."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

from src.business_generation import (BusinessTranslationUnavailable, GEMINI_ENDPOINT, MODEL,
                                     RETRY_DELAY_SECONDS, TIMEOUT_MS, business_config,
                                     create_business_generate)
from src.business_handoff import accepted_research
from src.business_insights import translate_result
from src.research_pipeline import PipelineError

ROOT = Path(__file__).resolve().parents[1]
RECORDED = json.loads((ROOT / 'tests/fixtures/business/hydrogen-validated-v1.json').read_text(encoding='utf-8'))
ENV = {'BUSINESS_TRANSLATION_ENABLED': '1', 'BUSINESS_TRANSLATION_API_KEY': 'business-key',
       'GOOGLE_API_KEY': 'research-key'}


class Error503(Exception):
    code = 503


class Error400(Exception):
    code = 400


def fake_client(*effects):
    client = Mock()
    client.models.generate_content.side_effect = list(effects)
    return client


def reply(text='{"ok": true}'):
    return Mock(text=text)


class ConfigTests(unittest.TestCase):
    def test_disabled_by_default_and_hydrogen_only(self):
        with self.assertRaises(PipelineError): business_config({})
        self.assertEqual(business_config(ENV)['model'], MODEL)
        with self.assertRaises(PipelineError):
            business_config({**ENV, 'BUSINESS_TRANSLATION_MODEL': 'gemini-3.1-flash-lite'})

    def test_dedicated_key_never_a_research_key(self):
        with self.assertRaises(PipelineError):
            business_config({**ENV, 'BUSINESS_TRANSLATION_API_KEY_ENV': 'GOOGLE_API_KEY'})
        with self.assertRaises(PipelineError):
            business_config({**ENV, 'BUSINESS_TRANSLATION_API_KEY': 'research-key'})
        with self.assertRaises(PipelineError):
            business_config({k: v for k, v in ENV.items() if k != 'BUSINESS_TRANSLATION_API_KEY'})

    def test_request_uses_validated_settings(self):
        client = fake_client(reply())
        generate, metadata = create_business_generate(ENV, client=client)
        generate('prompt')
        kwargs = client.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs['model'], 'gemini-4-hydrogen')
        config = kwargs['config']
        self.assertEqual(config.temperature, 0)
        self.assertEqual(config.response_mime_type, 'application/json')
        self.assertEqual(config.thinking_config.thinking_level.value, 'HIGH')
        self.assertEqual(metadata['model'], 'gemini-4-hydrogen')
        self.assertNotIn('business-key', json.dumps(metadata))

    def test_rejects_endpoint_and_vertex_overrides_before_creating_client(self):
        for name, value in (
                ('GOOGLE_GEMINI_BASE_URL', 'https://example.invalid'),
                ('GOOGLE_VERTEX_BASE_URL', 'https://example.invalid'),
                ('GOOGLE_GENAI_USE_VERTEXAI', 'true'),
                ('GOOGLE_GENAI_USE_ENTERPRISE', '1')):
            with self.subTest(name=name), patch('google.genai.Client') as factory:
                with self.assertRaises(PipelineError):
                    create_business_generate({**ENV, name: value})
                factory.assert_not_called()

    def test_pins_endpoint_and_disables_sdk_fallback_and_retries(self):
        with patch('google.genai.Client', return_value=fake_client(reply())) as factory:
            generate, _ = create_business_generate(ENV)
            generate('prompt')
        kwargs = factory.call_args.kwargs
        self.assertEqual(kwargs['api_key'], ENV['BUSINESS_TRANSLATION_API_KEY'])
        self.assertIs(kwargs['vertexai'], False)
        options = kwargs['http_options']
        self.assertEqual(options.base_url, GEMINI_ENDPOINT)
        self.assertEqual(options.timeout, TIMEOUT_MS)
        self.assertEqual(options.retry_options.attempts, 1)
        self.assertEqual(options.client_args, {'follow_redirects': False, 'trust_env': False})


class RetryTests(unittest.TestCase):
    def test_one_retry_on_503_then_success(self):
        sleep = Mock()
        generate, _ = create_business_generate(ENV, client=fake_client(Error503(), reply('{"a":1}')), sleep=sleep)
        self.assertEqual(generate('p'), '{"a":1}')
        self.assertEqual(generate.provider_attempts, 2)
        sleep.assert_called_once_with(RETRY_DELAY_SECONDS)

    def test_two_503s_are_unavailable_without_fallback(self):
        client = fake_client(Error503(), Error503(), reply())
        generate, _ = create_business_generate(ENV, client=client, sleep=Mock())
        with self.assertRaises(BusinessTranslationUnavailable): generate('p')
        self.assertEqual(client.models.generate_content.call_count, 2)
        models = {c.kwargs['model'] for c in client.models.generate_content.call_args_list}
        self.assertEqual(models, {'gemini-4-hydrogen'})

    def test_non_503_errors_are_not_retried(self):
        client = fake_client(Error400(), reply())
        generate, _ = create_business_generate(ENV, client=client, sleep=Mock())
        with self.assertRaises(Error400): generate('p')
        self.assertEqual(client.models.generate_content.call_count, 1)

    def test_unavailable_state_preserves_research(self):
        from tests.test_downstream_business import CONTEXT, result_for
        generate, metadata = create_business_generate(ENV, client=fake_client(Error503(), Error503()), sleep=Mock())
        source = result_for()
        envelope = translate_result(source, context=CONTEXT, generate=generate, metadata=metadata)
        self.assertEqual(envelope['error']['code'], 'business_unavailable')
        self.assertIn('temporarily unavailable', envelope['error']['message'])
        self.assertEqual(envelope['result']['summary'], source['summary'])
        self.assertNotIn('business_insight', envelope['result'])
        info = envelope['result']['provenance']['business_translation']
        self.assertEqual((info['status'], info['attempted_calls'], info['provider_attempts']), ('unavailable', 1, 2))


class RecordedOutputReplay(unittest.TestCase):
    """The 9 blind-scored Hydrogen responses must pass the retained structural checks unchanged."""

    def test_original_outputs_preserved_except_for_accepted_limitations(self):
        self.assertEqual(len(RECORDED['cases']), 9)
        for case in RECORDED['cases']:
            with self.subTest(case=case['case']):
                archived_packet = subprocess.check_output(
                    ['git', '-C', str(ROOT), 'show', '928bdd3f364ef5f8ac4c3f0afdbf024f33f9773b:' + case['packet']]
                )
                packet = json.loads(archived_packet)
                raw = case['raw_response']
                self.assertEqual(sha256(raw.encode('utf-8')).hexdigest(), case['raw_sha256'])
                generate = Mock(return_value=raw)
                envelope = translate_result(packet['result'], context=packet['context'], generate=generate,
                                            metadata={'provider': 'injected_test'})
                self.assertIsNone(envelope['error'])
                prompt = generate.call_args.args[0]
                self.assertEqual(sha256(prompt.encode()).hexdigest(), case['prompt_sha256'])
                published = envelope['result']['business_insight']
                expected = json.loads(raw)
                accepted, _, _ = accepted_research(packet['result']['summary'], packet['result']['evidence'])
                expected['limitations'] = list(dict.fromkeys([*accepted['limitations'], *expected['limitations']]))
                self.assertEqual(published, expected)


if __name__ == '__main__':
    unittest.main()

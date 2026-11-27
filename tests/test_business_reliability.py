"""Provider-error classification, bounded retries and sanitized diagnostics (offline, no calls)."""
import contextlib
import io
import json
import unittest
from unittest.mock import Mock

from src.business_generation import (RETRY_DELAY_SECONDS, BusinessProviderError, BusinessTranslationUnavailable,
                                     classify_provider_error, create_business_generate)
from src.business_insights import translate_result
from tests.test_business_hydrogen import ENV, fake_client, reply
from tests.test_downstream_business import CONTEXT, business, result_for

SECRET = 'request echo: user question text and key AIzaFAKEFAKEFAKE'


class ProviderError(Exception):
    """Shaped like google.genai.errors.APIError: code, status, details; message may echo content."""

    def __init__(self, code, status=None, details=None):
        super().__init__(SECRET)
        self.code, self.status, self.message = code, status, SECRET
        self.details = {'error': {'code': code, 'status': status, 'message': SECRET, 'details': details or []}}


def quota(quota_id, delay=None):
    entries = [{'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaId': quota_id}]}]
    if delay:
        entries.append({'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': delay})
    return ProviderError(429, 'RESOURCE_EXHAUSTED', entries)


class ReadTimeout(Exception):
    pass


class ClassificationTests(unittest.TestCase):
    def test_categories(self):
        cases = [
            (ProviderError(500, 'INTERNAL'), 'temporary'), (ProviderError(502), 'temporary'),
            (ProviderError(503, 'UNAVAILABLE'), 'temporary'), (ProviderError(504, 'DEADLINE_EXCEEDED'), 'temporary'),
            (ReadTimeout(), 'temporary'),
            (quota('GenerateRequestsPerMinutePerProjectPerModel-FreeTier', '7s'), 'rate_limited'),
            (quota('GenerateRequestsPerDayPerProjectPerModel-FreeTier', '30s'), 'quota_exhausted'),
            (ProviderError(401, 'UNAUTHENTICATED'), 'authentication'),
            (ProviderError(403, 'PERMISSION_DENIED'), 'authentication'),
            (ProviderError(400, 'INVALID_ARGUMENT', [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo',
                                                     'reason': 'API_KEY_INVALID'}]), 'authentication'),
            (ProviderError(400, 'INVALID_ARGUMENT'), 'invalid_request'),
            (ProviderError(404, 'NOT_FOUND'), 'invalid_request'),
            (RuntimeError('boom'), 'unknown'),
        ]
        for error, category in cases:
            with self.subTest(error=type(error).__name__, code=getattr(error, 'code', None)):
                classified = classify_provider_error(error)
                self.assertEqual(classified.category, category)
                self.assertNotIn(SECRET, json.dumps(classified.diagnostics()) + str(classified))

    def test_rate_limit_keeps_provider_delay(self):
        self.assertEqual(classify_provider_error(quota('PerMinute', '12.5s')).retry_after, 12.5)


class RetryPolicyTests(unittest.TestCase):
    def run_generate(self, *effects):
        client, sleep = fake_client(*effects), Mock()
        generate, _ = create_business_generate(ENV, client=client, sleep=sleep)
        return generate, client, sleep

    def test_temporary_failures_retry_once_then_succeed(self):
        for error in (ProviderError(500), ProviderError(504), ReadTimeout()):
            with self.subTest(error=type(error).__name__):
                generate, client, sleep = self.run_generate(error, reply('{"a":1}'))
                self.assertEqual(generate('p'), '{"a":1}')
                self.assertEqual(client.models.generate_content.call_count, 2)
                sleep.assert_called_once_with(RETRY_DELAY_SECONDS)
                self.assertEqual([entry['category'] for entry in generate.attempt_log], ['temporary', 'ok'])

    def test_two_temporary_failures_are_unavailable(self):
        generate, client, _ = self.run_generate(ProviderError(500), ProviderError(502), reply())
        with self.assertRaises(BusinessTranslationUnavailable) as raised:
            generate('p')
        self.assertEqual(raised.exception.category, 'temporary')
        self.assertEqual(client.models.generate_content.call_count, 2)

    def test_short_rate_limit_waits_provider_delay_once(self):
        generate, client, sleep = self.run_generate(quota('PerMinute', '9s'), reply('{"a":1}'))
        self.assertEqual(generate('p'), '{"a":1}')
        sleep.assert_called_once_with(9.0)
        self.assertEqual(client.models.generate_content.call_count, 2)

    def test_long_rate_limit_is_reported_not_slept(self):
        generate, client, sleep = self.run_generate(quota('PerMinute', '45s'), reply())
        with self.assertRaises(BusinessTranslationUnavailable) as raised:
            generate('p')
        self.assertEqual((raised.exception.category, raised.exception.retry_after), ('rate_limited', 45.0))
        sleep.assert_not_called()
        self.assertEqual(client.models.generate_content.call_count, 1)

    def test_permanent_failures_are_never_retried(self):
        for error, category in ((quota('PerDay', '60s'), 'quota_exhausted'),
                                (ProviderError(401, 'UNAUTHENTICATED'), 'authentication'),
                                (ProviderError(400, 'INVALID_ARGUMENT'), 'invalid_request')):
            with self.subTest(category=category):
                generate, client, sleep = self.run_generate(error, reply())
                with self.assertRaises(BusinessProviderError) as raised:
                    generate('p')
                self.assertNotIsInstance(raised.exception, BusinessTranslationUnavailable)
                self.assertEqual(raised.exception.category, category)
                self.assertEqual(client.models.generate_content.call_count, 1)
                sleep.assert_not_called()


class EnvelopeTests(unittest.TestCase):
    def translate(self, *effects, generate=None):
        if generate is None:
            generate, metadata = create_business_generate(ENV, client=fake_client(*effects), sleep=Mock())
        else:
            metadata = {'provider': 'injected_test'}
        source, log = result_for(), io.StringIO()
        with contextlib.redirect_stderr(log):
            envelope = translate_result(source, context=CONTEXT, generate=generate, metadata=metadata)
        self.assertEqual(envelope['result']['summary'], source['summary'])
        self.assertEqual(envelope['result']['evidence'], source['evidence'])
        self.assertNotIn('business_insight', envelope['result'])
        dumped = json.dumps(envelope) + log.getvalue()
        self.assertNotIn(SECRET, dumped)
        self.assertNotIn('AIza', dumped)
        return envelope, envelope['result']['provenance']['business_translation'], log.getvalue()

    def test_error_codes_and_retry_offers(self):
        cases = (
            ((ProviderError(500), ProviderError(500)), 'business_unavailable', True, 'temporary', 2),
            ((quota('PerMinute', '45s'),), 'business_rate_limited', True, 'rate_limited', 1),
            ((quota('PerDay'),), 'business_quota_exhausted', False, 'quota_exhausted', 1),
            ((ProviderError(403, 'PERMISSION_DENIED'),), 'business_configuration', False, 'authentication', 1),
            ((ProviderError(400, 'INVALID_ARGUMENT'),), 'business_request_rejected', False, 'invalid_request', 1),
        )
        for effects, code, retryable, category, attempts in cases:
            with self.subTest(code=code):
                envelope, info, log = self.translate(*effects)
                self.assertEqual((envelope['error']['code'], envelope['error']['retryable']), (code, retryable))
                self.assertEqual((info['failure']['category'], info['provider_attempts'], info['attempted_calls']),
                                 (category, attempts, 1))
                self.assertIn(f'business-failure category={category}', log)
        envelope, _, _ = self.translate(quota('PerMinute', '45s'))
        self.assertEqual(envelope['error']['retry_after_seconds'], 45.0)

    def test_validation_failures_name_the_check_and_stay_strict(self):
        cases = (('not json', 'malformed_json'),
                 (json.dumps({**business(), 'risks': ['r'] * 5}), 'caveat_limits'),
                 (json.dumps({**business(), 'industry': 'another industry'}), 'industry_mismatch'))
        for raw, check in cases:
            with self.subTest(check=check):
                envelope, info, log = self.translate(generate=Mock(return_value=raw))
                self.assertEqual((envelope['error']['code'], envelope['error']['retryable']), ('business_failed', True))
                self.assertEqual(info['failure'], {'category': 'validation', 'check': check})
                self.assertIn(f'check={check}', log)


if __name__ == '__main__':
    unittest.main()

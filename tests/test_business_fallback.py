"""Muse Wonder fallback: triggers, time budget, spend cap, provenance and isolation (offline)."""
import io
import json
import tempfile
import threading
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock

from src.business_fallback import (MODEL, FallbackBudgetExhausted, SpendLedger, create_muse_generate,
                                   fallback_from_environment, with_fallback, worst_case_cost)
from src.business_generation import BusinessProviderError, BusinessTranslationUnavailable
from src.business_insights import translate_result
from tests.test_downstream_business import CONTEXT, business, result_for


def reply(content, tokens_in=1500, tokens_out=2400, reasoning=1900):
    body = json.dumps({'choices': [{'message': {'content': content}, 'finish_reason': 'stop'}],
                       'usage': {'prompt_tokens': tokens_in, 'completion_tokens': tokens_out,
                                 'completion_tokens_details': {'reasoning_tokens': reasoning}}}).encode()
    return io.BytesIO(body)


def primary_failing(category):
    def primary(prompt):
        primary.provider_attempts = 2 if category == 'temporary' else 1
        raise (BusinessTranslationUnavailable(category=category) if category in {'temporary', 'rate_limited'}
               else BusinessProviderError(category, http_status=429 if category == 'quota_exhausted' else 400))
    return primary


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = SpendLedger(Path(self.dir.name) / 'muse-spend.sqlite3', 5.0)

    def tearDown(self):
        self.dir.cleanup()

    def muse(self, *responses):
        opener = Mock(side_effect=list(responses))
        return create_muse_generate('meta-test-key', self.ledger, opener=opener), opener


class TriggerTests(Base):
    def test_falls_back_only_for_quota_rate_and_temporary(self):
        for category in ('quota_exhausted', 'rate_limited', 'temporary'):
            with self.subTest(category=category):
                muse, opener = self.muse(reply(json.dumps(business())))
                generate = with_fallback(primary_failing(category), muse)
                self.assertEqual(json.loads(generate('p')), business())
                self.assertEqual(generate.generator_used['model'], MODEL)
                self.assertEqual(generate.generator_used['fallback_reason'], category)
                body = json.loads(opener.call_args.args[0].data)
                self.assertEqual((body['reasoning_effort'], body['max_completion_tokens']), ('high', 16000))
        for category in ('authentication', 'invalid_request', 'unknown'):
            with self.subTest(category=category):
                muse, opener = self.muse()
                with self.assertRaises(BusinessProviderError):
                    with_fallback(primary_failing(category), muse)('p')
                opener.assert_not_called()

    def test_success_never_calls_fallback_and_missing_key_disables_it(self):
        muse, opener = self.muse()
        generate = with_fallback(Mock(return_value='{"ok": 1}'), muse)
        self.assertEqual(generate('p'), '{"ok": 1}')
        self.assertEqual(generate.generator_used, {'model': 'gemini-4-hydrogen'})
        opener.assert_not_called()
        self.assertIsNone(fallback_from_environment(self.dir.name, {}))
        self.assertIsNone(fallback_from_environment(self.dir.name, {'META_MODEL_API_KEY': 'k',
                                                                    'BUSINESS_FALLBACK_ENABLED': '0'}))
        self.assertIsNotNone(fallback_from_environment(self.dir.name, {'META_MODEL_API_KEY': 'k'}))

    def test_insufficient_time_skips_fallback(self):
        muse, opener = self.muse()
        times = iter([0.0, 140.0])
        generate = with_fallback(primary_failing('temporary'), muse, clock=lambda: next(times))
        with self.assertRaises(BusinessTranslationUnavailable):
            generate('p')
        opener.assert_not_called()
        self.assertEqual(generate.fallback_failure, {'category': 'skipped', 'reason': 'insufficient_time'})

    def test_muse_failure_is_reported_unavailable_without_retry(self):
        error = urllib.error.HTTPError('u', 503, 'x', {}, io.BytesIO(b'secret text'))
        muse, opener = self.muse(error)
        generate = with_fallback(primary_failing('quota_exhausted'), muse)
        with self.assertRaises(BusinessTranslationUnavailable):
            generate('p')
        self.assertEqual(opener.call_count, 1)
        self.assertEqual(generate.fallback_failure, {'category': 'temporary', 'http_status': 503})
        self.assertEqual(self.ledger.spent_today(), 0.0)  # rejected request settled at zero


class SpendCapTests(Base):
    def test_cap_refuses_before_calling_and_settles_actual_cost(self):
        muse, opener = self.muse(reply('{}', 1000, 2000))
        muse('p', 30)
        self.assertAlmostEqual(self.ledger.spent_today(), 1000 * 4e-6 + 2000 * 20e-6, places=6)
        tight = SpendLedger(Path(self.dir.name) / 'tight.sqlite3', worst_case_cost('p') * 1.5)
        muse_tight = create_muse_generate('k', tight, opener=Mock(side_effect=[reply('{}', 0, 0), reply('{}')]))
        tight.reserve(worst_case_cost('p'))  # an in-flight call holds its worst case
        with self.assertRaises(FallbackBudgetExhausted):
            muse_tight('p', 30)

    def test_concurrent_reservations_never_exceed_the_cap(self):
        ledger = SpendLedger(Path(self.dir.name) / 'race.sqlite3', worst_case_cost('p') * 3.5)
        granted, refused, start = [], [], threading.Barrier(12)

        def worker():
            start.wait()
            try:
                granted.append(ledger.reserve(worst_case_cost('p')))
            except FallbackBudgetExhausted:
                refused.append(1)
        threads = [threading.Thread(target=worker) for _ in range(12)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual((len(granted), len(refused)), (3, 9))
        self.assertLessEqual(ledger.spent_today(), ledger.cap)


class EnvelopeTests(Base):
    def test_provenance_records_actual_model_reason_usage_and_cost(self):
        muse, _ = self.muse(reply(json.dumps(business()), 1600, 2500, 2000))
        source = result_for()
        envelope = translate_result(source, context=CONTEXT, generate=with_fallback(primary_failing('quota_exhausted'), muse),
                                    metadata={'provider': 'gemini', 'model': 'gemini-4-hydrogen', 'fallback_model': MODEL})
        self.assertIsNone(envelope['error'])
        info = envelope['result']['provenance']['business_translation']
        used = info['generator_used']
        self.assertEqual((used['model'], used['fallback_from'], used['fallback_reason']),
                         (MODEL, 'gemini-4-hydrogen', 'quota_exhausted'))
        self.assertEqual((used['usage']['input_tokens'], used['usage']['output_tokens'], used['usage']['reasoning_tokens']),
                         (1600, 2500, 2000))
        self.assertAlmostEqual(used['usage']['estimated_cost_usd'], 1600 * 4e-6 + 2500 * 20e-6, places=6)
        self.assertEqual(info['generator']['fallback_model'], MODEL)
        self.assertEqual(envelope['result']['summary'], source['summary'])
        self.assertNotIn('meta-test-key', json.dumps(envelope))

    def test_validation_failure_is_never_regenerated_by_the_fallback(self):
        muse, opener = self.muse()
        source = result_for()
        envelope = translate_result(source, context=CONTEXT, generate=with_fallback(Mock(return_value='not json'), muse),
                                    metadata={'provider': 'gemini'})
        self.assertEqual(envelope['error']['code'], 'business_failed')
        opener.assert_not_called()
        self.assertEqual(envelope['result']['summary'], source['summary'])

    def test_both_models_unavailable_keeps_research_and_says_so(self):
        muse, _ = self.muse(urllib.error.URLError('down'))
        source = result_for()
        envelope = translate_result(source, context=CONTEXT, generate=with_fallback(primary_failing('quota_exhausted'), muse),
                                    metadata={'provider': 'gemini'})
        self.assertEqual(envelope['error']['code'], 'business_unavailable')
        self.assertIn('temporarily unavailable', envelope['error']['message'])
        self.assertEqual(envelope['result']['summary'], source['summary'])
        self.assertEqual(envelope['result']['provenance']['business_translation']['fallback_failure'], {'category': 'temporary'})


if __name__ == '__main__':
    unittest.main()

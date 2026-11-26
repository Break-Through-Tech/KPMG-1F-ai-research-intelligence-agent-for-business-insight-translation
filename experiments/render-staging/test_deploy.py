from contextlib import closing
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from jsonschema import ValidationError
from server import REPLY_ALLOWANCE, Budget, QuotaExhausted, quota_generate, reservation, wire_schema
from src.research_chat import synthesis_schema


class DeploymentUnitTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'usage.sqlite3'
        self.now = 1_000_000
        self.clock = lambda: self.now

    def attempts(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]

    def test_rate_limit_survives_restart(self):
        budget = Budget(self.path, clock=self.clock)
        for _ in range(6):
            budget.reserve(4096)
        with self.assertRaises(QuotaExhausted):
            Budget(self.path, clock=self.clock).reserve(4096)
        self.now += 61
        Budget(self.path, clock=self.clock).reserve(4096)
        self.assertEqual(7, self.attempts())

    def test_token_limit_and_clock_rollback(self):
        budget = Budget(self.path, clock=self.clock)
        budget.reserve(159_000)
        with self.assertRaises(QuotaExhausted):
            budget.reserve(4096)
        self.now -= 1
        with self.assertRaises(QuotaExhausted):
            budget.reserve(1)
        self.assertEqual(1, self.attempts())

    def test_daily_limit(self):
        budget = Budget(self.path, clock=self.clock)
        for _ in range(60):
            budget.reserve(1)
            self.now += 61
        with self.assertRaises(QuotaExhausted):
            budget.reserve(1)

    def test_s2_drafting_and_review_fit_one_minute_budget(self):
        # Measured payloads of the hosted request that failed at review (26 Nov 18:58): drafting 35,640 B, review
        # 41,325 B. The former 2-tokens-per-byte estimate reserved 162,122 for the pair, over the 160k minute budget.
        budget = Budget(self.path, clock=self.clock)
        budget.reserve(reservation(35_640))
        budget.reserve(reservation(41_325))
        budget.reserve(reservation(35_640))
        budget.reserve(reservation(41_325))
        self.assertEqual(4, self.attempts())

    def test_reservation_stays_conservative(self):
        # Measured 7,651 input tokens for a 28,338-byte payload; the reservation must still exceed it with margin.
        self.assertGreater(reservation(28_338), 1.5 * 7_651 + 976)
        self.assertEqual(reservation(0), REPLY_ALLOWANCE)

    def test_oversized_request_is_still_refused(self):
        with self.assertRaises(QuotaExhausted):
            Budget(self.path, clock=self.clock).reserve(reservation(400_000))
        self.assertEqual(0, self.attempts())

    def test_failure_is_reserved_and_not_retried(self):
        provider = Mock(side_effect=TimeoutError)
        call = quota_generate(provider, Budget(self.path, clock=self.clock))
        with self.assertRaises(TimeoutError):
            call('input')
        provider.assert_called_once()
        self.assertEqual(1, self.attempts())

    def test_wire_relaxation_cannot_publish_unknown_citation(self):
        schema = synthesis_schema(['allowed'])
        wire = wire_schema(schema)
        item = wire['properties']['claims']['items']['properties']['support']['items']
        self.assertNotIn('enum', item['properties']['chunk_id'])
        self.assertTrue(item['required'])
        self.assertEqual(['allowed'], schema['properties']['claims']['items']['properties']['support']
                         ['items']['properties']['chunk_id']['enum'])
        invalid = json.dumps({'status': 'ok', 'claims': [{'text': 'finding', 'kind': 'finding',
            'support': [{'chunk_id': 'other', 'quote': 'Original source has exact content.'}]}],
            'limitations': []})
        call = quota_generate(Mock(return_value=invalid), Budget(self.path, clock=self.clock))
        with self.assertRaises(ValidationError):
            call('input', response_schema=schema)

    def test_budget_refusal_prevents_provider_call(self):
        provider = Mock()
        call = quota_generate(provider, Budget(self.path, clock=self.clock))
        with self.assertRaises(QuotaExhausted):
            call('z' * 100_000)
        provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()


class PersistentSmokeTests(unittest.TestCase):
    def test_attempt_cap_survives_failures_restart_and_concurrency(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'smoke.sqlite3'
            provider = Mock(side_effect=TimeoutError('scripted'))
            guarded = quota_generate(provider, Budget(path, lambda: 100, smoke=True))
            for _ in range(5):
                with self.assertRaises(TimeoutError):
                    guarded('fixture')

            def attempt(_):
                restarted = Budget(path, lambda: 200, smoke=True)
                try:
                    restarted.reserve(1)
                    return True
                except QuotaExhausted:
                    return False

            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(attempt, range(8))), 5)
            self.assertEqual(provider.call_count, 5)
            with self.assertRaises(QuotaExhausted):
                Budget(path, lambda: 100000, smoke=True).reserve(1)

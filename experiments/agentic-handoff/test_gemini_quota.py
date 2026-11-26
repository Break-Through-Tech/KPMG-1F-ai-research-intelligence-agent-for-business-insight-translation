from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gemini_quota import GeminiQuota, QuotaRefused


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "attempts.sqlite3"
        self.now = 1000
        self.quota = GeminiQuota(self.path, clock=lambda: self.now)

    def observe(self, rpm=0, tpm=0, rpd=0):
        self.quota.observe(minute_requests=rpm, minute_input_tokens=tpm,
                           day_requests=rpd, valid_until=self.now + 60)

    def test_unknown_or_stale_usage_stops(self):
        with self.assertRaises(QuotaRefused):
            self.quota.reserve("generation", 1)
        self.observe()
        self.now += 60
        with self.assertRaises(QuotaRefused):
            self.quota.reserve("generation", 1)

    def test_token_and_request_accounting(self):
        self.observe(rpm=8, tpm=199_000)
        self.quota.reserve("generation", 800)
        with self.assertRaisesRegex(QuotaRefused, "Minute"):
            self.quota.reserve("generation", 201)
        self.quota.reserve("metadata", 0)
        with self.assertRaisesRegex(QuotaRefused, "Minute"):
            self.quota.reserve("metadata", 0)

    def test_daily_and_restart(self):
        self.observe(rpd=399)
        self.quota.reserve("generation", 1)
        reopened = GeminiQuota(self.path, clock=lambda: self.now)
        with self.assertRaisesRegex(QuotaRefused, "Daily"):
            reopened.reserve("generation", 1)

    def test_atomic_concurrent_reservations(self):
        self.observe(rpm=9)
        def reserve(_):
            try:
                return self.quota.reserve("generation", 1)
            except QuotaRefused:
                return None
        with ThreadPoolExecutor(max_workers=8) as workers:
            self.assertEqual(sum(r is not None for r in workers.map(reserve, range(8))), 1)

    def test_session_cap_includes_attempts_even_without_receipts(self):
        for _ in range(9):
            self.observe()
            for _ in range(10):
                self.quota.reserve("generation", 1)
            self.now += 61
        self.observe()
        with self.assertRaisesRegex(QuotaRefused, "attempt cap"):
            self.quota.reserve("generation", 1)

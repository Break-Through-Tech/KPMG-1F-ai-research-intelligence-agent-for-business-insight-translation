"""Opt-in transient retry in the Gemini adapter, at the HTTP boundary. No network."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx

from gemini_paired import RETRYING, STAGED, GeminiRun
from gemini_quota import GeminiQuota

OK = {"modelVersion": "fixture", "usageMetadata": {"promptTokenCount": 10},
      "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "{}"}]}}]}


def run(statuses, *, retries, timeout_first=False):
    """Replay one generate call against scripted statuses; returns (result or error, receipts, pauses, generations)."""
    replies = list(statuses)
    pauses = []

    def handler(request):
        if request.url.path.endswith(":countTokens"):
            return httpx.Response(200, json={"totalTokens": 10})
        status = replies.pop(0)
        if status == "timeout":
            raise httpx.ReadTimeout("fixture", request=request)
        return httpx.Response(status, json=OK if status == 200 else {"error": {"status": "UNAVAILABLE", "message": "busy"}})

    with TemporaryDirectory() as temp:
        root = Path(temp)
        now = [1000]
        quota = GeminiQuota(root / "a.sqlite3", clock=lambda: now[0])
        quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=0, valid_until=2000, exclusive=True)
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            live = GeminiRun(http, quota, root, pause=lambda s: (pauses.append(s), now.__setitem__(0, now[0] + s)),
                             transient_retries=retries)
            try:
                outcome = live("Fixture only", response_schema={"type": "object"})
            except RuntimeError as error:
                outcome = error
        receipts = [json.loads(p.read_text()) for p in sorted(root.glob("*-http.json"))]
        generations = sum(r["kind"] == "generation" for r in receipts)
    return outcome, receipts, [p for p in pauses if p != 61], generations


class Retry(unittest.TestCase):
    def test_default_is_unchanged_one_503_stops(self):
        outcome, receipts, pauses, generations = run([503], retries=0)
        self.assertIsInstance(outcome, RuntimeError)
        self.assertIn("503", str(outcome))
        self.assertEqual((generations, pauses), (1, []))

    def test_503_then_success_recovers_and_keeps_both_receipts(self):
        outcome, receipts, pauses, generations = run([503, 200], retries=2)
        self.assertEqual(outcome, "{}")
        self.assertEqual([r["status"] for r in receipts if r["kind"] == "generation"], [503, 200])
        self.assertEqual((generations, pauses), (2, [60]))  # the retry is a counted, reserved attempt

    def test_timeout_is_retried(self):
        outcome, _, pauses, generations = run(["timeout", 200], retries=2)
        self.assertEqual((outcome, generations, pauses), ("{}", 2, [60]))

    def test_retries_are_bounded(self):
        outcome, _, pauses, generations = run([503, 503, 503], retries=2)
        self.assertIsInstance(outcome, RuntimeError)
        self.assertEqual((generations, pauses), (3, [60, 120]))

    def test_other_errors_are_never_retried(self):
        for status in (400, 429, 500):
            with self.subTest(status=status):
                outcome, _, pauses, generations = run([status, 200], retries=2)
                self.assertIsInstance(outcome, RuntimeError)
                self.assertEqual((generations, pauses), (1, []))

    def test_only_the_v7_label_retries(self):
        self.assertEqual(RETRYING, {"policy_stage_b_retry": 2})
        self.assertEqual(STAGED["policy_stage_b_retry"][1:], STAGED["policy_stage_b"][1:])  # same questions and switches
        self.assertNotEqual(STAGED["policy_stage_b_retry"][0], STAGED["policy_stage_b"][0])


if __name__ == "__main__":
    unittest.main()

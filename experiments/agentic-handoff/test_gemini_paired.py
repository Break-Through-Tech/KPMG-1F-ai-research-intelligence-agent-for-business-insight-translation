"""Exercise the paired runner and quota at the HTTP boundary offline."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx

from gemini_paired import GeminiRun, replay_pair
from gemini_quota import GeminiQuota
from test_handoff import LIMIT, METHODS, METHOD_CLAIMS, QUERY, ReplayProvider


class PairedTests(unittest.TestCase):
    def test_both_arms_share_one_plan_and_reserve_every_http_attempt(self):
        scripts = [ReplayProvider(*METHOD_CLAIMS, LIMIT) for _ in range(2)]
        calls = []
        arm = 0

        def handler(request):
            nonlocal arm
            self.assertEqual(request.url.host, "generativelanguage.googleapis.com")
            body = json.loads(request.content)
            calls.append(request.url.path)
            if request.url.path.endswith(":countTokens"):
                return httpx.Response(200, json={"totalTokens": 120})
            prompt = body["contents"][0]["parts"][0]["text"]
            role = scripts[arm].role(prompt)
            if arm == 0 and len(scripts[0].calls) == 5:
                arm = 1
            result = scripts[arm](prompt, body["generationConfig"]["responseJsonSchema"])
            return httpx.Response(200, json={
                "modelVersion": "fixture-fixed", "usageMetadata": {"promptTokenCount": 120},
                "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": result}]}}],
            })

        with TemporaryDirectory() as temp:
            root = Path(temp)
            now = [1000]
            quota = GeminiQuota(root / "attempts.sqlite3", clock=lambda: now[0])
            quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=0,
                          valid_until=2000, exclusive=True)
            with httpx.Client(transport=httpx.MockTransport(handler)) as http:
                live = GeminiRun(http, quota, root, pause=lambda seconds: now.__setitem__(0, now[0] + seconds))
                results = replay_pair(root, QUERY, lambda q, _: [METHODS["second method" in q]],
                                      lambda: {"indexed_records_sha256": "fixture"}, live, ("current", "handoff"))
            self.assertEqual(len(calls), 18)
            self.assertEqual(sum(c.endswith(":generateContent") for c in calls), 9)
            self.assertEqual(len(list(root.glob("*-usage.json"))), 9)
            self.assertTrue((root / "shared-plan.json").is_file())
            self.assertEqual([a["result"]["summary"]["answer_scope"] for a in results.values()],
                             ["partial", "full"])
            def packet(arm):
                return json.loads((root / arm / "synthesis-1.evidence.json").read_bytes())
            self.assertEqual(packet("current"), packet("handoff"))

    def test_rate_limit_stops_and_never_dispatches_second_attempt(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            quota = GeminiQuota(root / "attempts.sqlite3", clock=lambda: 1000)
            quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=0, valid_until=1060)
            calls = []
            def handler(request):
                calls.append(request.url.path)
                return httpx.Response(429, json={})
            with httpx.Client(transport=httpx.MockTransport(handler)) as http:
                live = GeminiRun(http, quota, root)
                for _ in range(2):
                    with self.assertRaisesRegex(RuntimeError, "429"):
                        live("Fixture only", response_schema={"type": "object"})
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(list(root.glob("*-http.json"))), 1)

    def test_bad_request_records_sanitized_google_message_and_field_details(self):
        key = "fixture-secret-never-save"
        body = {"error": {
            "status": "INVALID_ARGUMENT",
            "message": f"Malformed schema for '{key}'. Bearer private-test-token",
            "details": [
                {"@type": "type.googleapis.com/google.rpc.BadRequest", "fieldViolations": [
                    {"field": "generation_config.response_json_schema",
                     "description": 'Invalid value "echoed request text".'},
                ]},
                {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "INVALID_SCHEMA",
                 "metadata": {"ignored": "private request payload"}},
            ],
        }}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            quota = GeminiQuota(root / "attempts.sqlite3", clock=lambda: 1000)
            quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=0, valid_until=1060)
            def handler(request):
                if request.url.path.endswith(":countTokens"):
                    return httpx.Response(200, json={"totalTokens": 5})
                return httpx.Response(400, json=body)
            with httpx.Client(transport=httpx.MockTransport(handler),
                              headers={"x-goog-api-key": key}) as http:
                live = GeminiRun(http, quota, root)
                with self.assertRaisesRegex(RuntimeError, "HTTP 400"):
                    live("Offline fixture", response_schema={"type": "object"})
            raw = (root / "002-http.json").read_text(encoding="utf-8")
            detail = json.loads(raw)["google_error"]
            self.assertEqual(detail["status"], "INVALID_ARGUMENT")
            self.assertIn("Malformed schema", detail["message"])
            self.assertEqual(detail["details"][0]["fieldViolations"][0]["field"],
                             "generation_config.response_json_schema")
            self.assertEqual(detail["details"][1]["reason"], "INVALID_SCHEMA")
            for secret in (key, "private-test-token", "private request payload", "echoed request text"):
                self.assertNotIn(secret, raw)

    def test_real_table_packets_share_small_wire_schema_and_keep_full_validation(self):
        from copy import deepcopy
        from gemini_paired import ROOT, gemini_synthesis_schema
        from jsonschema import Draft202012Validator
        from src.research_chat import synthesis_schema, synthesize

        history = ROOT / "data/processed"
        paths = [
            history / "gemini-handoff-paired-v1-recovery/F01/handoff/synthesis-1.evidence.json",
            history / "gemini-handoff-paired-v1-recovery/F02/handoff/synthesis-1.evidence.json",
            history / "gemini-handoff-paired-v1-f03-f10/F03/current/synthesis-1.evidence.json",
        ]
        if not all(p.is_file() for p in paths):
            self.skipTest("Saved development evidence packets are not available")
        wires = []
        for path in paths:
            packet = json.loads(path.read_bytes())
            tables = [row for row in packet if row.get("table_id")]
            self.assertTrue(tables)
            full = synthesis_schema(sorted(row["chunk_id"] for row in packet))
            original = deepcopy(full)
            wire = gemini_synthesis_schema(full)
            Draft202012Validator.check_schema(wire)
            self.assertEqual(full, original)
            wires.append(wire)

            row = tables[0]
            quote = row["text"].splitlines()[-1][:1200]
            statement = {"text": "A table reports a result.", "kind": "finding",
                         "support": [{"chunk_id": row["chunk_id"], "quote": quote}]}
            valid = {"status": "ok", "claims": [statement], "limitations": []}
            unknown_id = deepcopy(valid)
            unknown_id["claims"][0]["support"][0]["chunk_id"] = "invented-id"
            short_quote = deepcopy(valid)
            short_quote["claims"][0]["support"][0]["quote"] = "tiny"
            wrong_quote = deepcopy(valid)
            wrong_quote["claims"][0]["support"][0]["quote"] = "This quote does not appear in the paper."
            too_many = {**valid, "claims": [statement] * 9}
            for answer, error in ((valid, None), (unknown_id, "invalid structured output"),
                                  (short_quote, "invalid structured output"),
                                  (too_many, "invalid structured output"), (wrong_quote, "quote is absent")):
                with self.subTest(packet=str(path.parent.parent.name), error=error), TemporaryDirectory() as temp:
                    root = Path(temp)
                    now = [1000]
                    quota = GeminiQuota(root / "attempts.sqlite3", clock=lambda: now[0])
                    quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=0,
                                  valid_until=2000, exclusive=True)
                    def handler(request):
                        if request.url.path.endswith(":countTokens"):
                            return httpx.Response(200, json={"totalTokens": 100})
                        sent = json.loads(request.content)["generationConfig"]["responseJsonSchema"]
                        self.assertEqual(sent, wire)
                        self.assertTrue(Draft202012Validator(sent).is_valid(answer))
                        return httpx.Response(200, json={
                            "modelVersion": "fixture-fixed", "usageMetadata": {"promptTokenCount": 100},
                            "candidates": [{"finishReason": "STOP",
                                "content": {"parts": [{"text": json.dumps(answer)}]}}],
                        })
                    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                        live = GeminiRun(client, quota, root, pause=lambda seconds: now.__setitem__(0, now[0] + seconds))
                        if error:
                            with self.assertRaisesRegex((RuntimeError, ValueError), error):
                                synthesize("What result is reported?", packet, generate=live)
                        else:
                            summary = synthesize("What result is reported?", packet, generate=live)
                            self.assertEqual(summary["claims"][0]["chunk_ids"], [row["chunk_id"]])
        self.assertEqual(wires[0], wires[1])
        self.assertEqual(wires[1], wires[2])

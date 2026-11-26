"""Gemini request and full research-path replay with intercepted HTTP only."""
import json
from unittest.mock import patch
import unittest

import httpx

from agents import OrchestratorAgent
from handoff import EvidenceHandoffOrchestrator
from src.generation import create_generate
from src.generation_config import GenerationConfig
from test_handoff import LIMIT, METHODS, METHOD_CLAIMS, QUERY, ReplayProvider

MODEL = "gemini-3.1-flash-lite"


class GeminiReplayTests(unittest.TestCase):
    def run_path(self, arm, provider_error=None):
        script = ReplayProvider(*METHOD_CLAIMS, LIMIT)
        requests = []

        def intercept(_client, request, **_kwargs):
            self.assertEqual(request.url.scheme, "https")
            self.assertEqual(request.url.host, "generativelanguage.googleapis.com")
            self.assertTrue(request.url.path.endswith(f"/models/{MODEL}:generateContent"))
            self.assertEqual(request.method, "POST")
            body = json.loads(request.content)
            options = body["generationConfig"]
            self.assertEqual(options["responseMimeType"], "application/json")
            self.assertEqual(options["temperature"], 0)
            self.assertNotIn("tools", body)
            schema = options["responseJsonSchema"]
            prompt = body["contents"][0]["parts"][0]["text"]
            requests.append((script.role(prompt), schema))
            if provider_error is not None and len(requests) == 1:
                return httpx.Response(provider_error, request=request,
                    json={"error": {"code": provider_error, "message": "offline failure", "status": "RESOURCE_EXHAUSTED"}})
            reply = script(prompt, schema)
            return httpx.Response(200, request=request, json={"candidates": [{
                "content": {"role": "model", "parts": [{"text": reply}]}, "finishReason": "STOP",
            }]})

        with patch.object(httpx.Client, "send", intercept), patch.object(
            httpx.AsyncClient, "send", side_effect=AssertionError("Unexpected async transport")
        ):
            generate, metadata = create_generate(GenerationConfig("gemini", MODEL, "fixture-only-key"))
            self.assertEqual(metadata["model"], MODEL)
            engine = arm(
                generate=generate,
                retrieve=lambda query, _: [METHODS["second method" in query]],
                top_k=8, max_calls=5,
                **({"research_only": True} if arm is OrchestratorAgent else {}),
            )
            return engine.run(QUERY), requests

    def test_shared_provider_settings_and_native_schema_across_both_paths(self):
        runs = [self.run_path(arm) for arm in (OrchestratorAgent, EvidenceHandoffOrchestrator)]
        self.assertEqual([r["summary"]["answer_scope"] for r, _ in runs], ["partial", "full"])
        for result, requests in runs:
            self.assertEqual([role for role, _ in requests], ["plan", "research", "verify", "research", "verify"])
            self.assertEqual(result["model_calls"]["used"], 5)
            self.assertEqual(requests[1][1]["properties"]["claims"]["maxItems"], 8)
            self.assertNotIn("uniqueItems", requests[-1][1]["properties"]["verdicts"]["items"]["properties"]["issues"])

    def test_rate_limit_is_one_attempt_and_never_falls_back(self):
        for arm in (OrchestratorAgent, EvidenceHandoffOrchestrator):
            with self.subTest(arm=arm):
                result, requests = self.run_path(arm, 429)
                self.assertEqual(result["status"], "execution_error")
                self.assertEqual(len(requests), 1)
                self.assertIsNone(result["summary"])

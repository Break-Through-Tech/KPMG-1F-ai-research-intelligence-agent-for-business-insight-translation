import asyncio
import json
import os
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from adapter import MODEL, format_answer, ingest, settings

os.environ["LITELLM_OFFLINE_MODE"] = "True"


class OfflineTests(unittest.TestCase):
    def test_corpus_retrieval_and_native_citations(self):
        from lmi import LLMResult
        from paperqa.utils import get_citation_ids

        class FixtureModel:
            calls = 0

            async def call_single(self, *, messages, **kwargs):
                self.calls += 1
                keys = get_citation_ids(messages[-1].content)
                return LLMResult(model="fixture", text=f"A scripted answer ({keys[0]}).")

        async def replay():
            rows = json.loads(Path(os.environ["PAPERQA_PILOT_COPY"]).read_text(encoding="utf-8"))["records"]
            config = settings()
            docs, sources = await ingest(rows, config)
            self.assertEqual(len(docs.texts), len(rows))
            self.assertEqual(len(docs.docs), 2)
            fake = FixtureModel()
            session = await docs.aquery("What benchmark evaluates travel planning?", settings=config,
                                        llm_model=fake, summary_llm_model=fake)
            self.assertEqual(fake.calls, 1)
            result = format_answer(session, sources)
            self.assertEqual(result["status"], "ok")
            citation, = result["citations"]
            expected = sources[citation["marker"]]
            self.assertEqual(citation["source_url"], expected["source_url"])
            self.assertEqual(citation["arxiv_id"], expected["arxiv_id"])
            self.assertEqual(citation["text"], expected["text"])
            session.raw_answer += " (pqac-ffffffff)"
            with self.assertRaisesRegex(ValueError, "Unknown raw"):
                format_answer(session, sources)

        with asyncio.Runner() as runner:
            runner.get_loop()
            with patch.object(socket, 'getaddrinfo', side_effect=AssertionError('DNS prohibited')), patch.object(socket.socket, 'connect', side_effect=AssertionError('Network prohibited')):
                runner.run(replay())

    def test_subscription_provider_routing_without_auth(self):
        import litellm

        with patch("litellm.llms.chatgpt.authenticator.Authenticator.get_access_token", return_value="fixture"):
            route = litellm.get_llm_provider(MODEL)
        self.assertEqual(route[:2], ("gpt-6.1-sol", "chatgpt"))


if __name__ == "__main__":
    unittest.main()

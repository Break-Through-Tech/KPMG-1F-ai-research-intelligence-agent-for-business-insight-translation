import json
import unittest
from unittest.mock import patch

from src import agent


def passages():
    return [
        {"chunk_id": "html-1", "text": "Evaluate agents on their intended tasks.",
         "title": "Agent evaluation", "arxiv_id": "fixture-a", "source": "html",
         "page_number": None, "pdf_url": "https://example.com/paper.pdf",
         "html_url": "https://example.com/paper#results",
         "source_url": "https://example.com/paper#results", "section": "results"},
        {"chunk_id": "pdf-2", "text": "Human verification is necessary.",
         "title": "Source checks", "arxiv_id": "fixture-b", "source": "pdf",
         "page_number": 2, "pdf_url": "https://example.com/checks.pdf",
         "source_url": "https://example.com/checks.pdf#page=2"},
    ]


def generated_summary(_prompt):
    return json.dumps({"status": "ok", "claims": [
        {"text": "Evaluate intended tasks.", "chunk_ids": ["html-1"]},
        {"text": "Verify sources.", "chunk_ids": ["pdf-2"]}], "limitations": []})


class BaselineAgentTests(unittest.TestCase):
    def test_shared_provider_and_source_locations_in_full_workflow(self):
        settings = {"provider": "openai", "model": "configured-model"}
        with patch.object(agent, "create_generate", return_value=(generated_summary, settings)) as factory:
            result = agent.ask_question("How should agents be evaluated?", retrieve=lambda q, k: passages())
        factory.assert_called_once_with()
        self.assertFalse(result["approved"])
        self.assertEqual(result["human_review"]["status"], "pending")
        self.assertEqual(result["provenance"]["generation"]["model"], "configured-model")
        self.assertIn("https://example.com/paper#results", result["answer"])
        self.assertIn("p.2", result["answer"])
        self.assertNotIn("p.None", result["answer"])
        self.assertEqual(result["sources"][0]["source"], "html")
        self.assertEqual(result["sources"][0]["section"], "results")
        self.assertIsNone(result["sources"][0]["page"])

    def test_empty_retrieval_needs_no_provider_or_key(self):
        with patch.object(agent, "create_generate") as factory:
            result = agent.ask_question("Unanswerable", retrieve=lambda q, k: [])
        factory.assert_not_called()
        self.assertEqual(result["summary"]["status"], "insufficient_evidence")
        self.assertEqual(result["sources"], [])
        self.assertFalse(result["approved"])

    def test_unknown_citation_rejected_not_rendered_as_answer(self):
        def fabricated(_prompt):
            return json.dumps({"status": "ok", "claims": [
                {"text": "Unsupported answer", "chunk_ids": ["unknown"]}], "limitations": []})
        result = agent.ask_question("Question", retrieve=lambda q, k: passages(), generate=fabricated)
        self.assertEqual(result["summary"]["status"], "insufficient_evidence")
        self.assertEqual(result["sources"], [])
        self.assertNotIn("Unsupported answer", result["answer"])
        self.assertEqual(result["summary"]["error"], "invalid_citations")

    def test_display_does_not_invent_an_html_page(self):
        context = agent.format_context(passages())
        self.assertIn("https://example.com/paper#results (results)", context)
        self.assertNotIn("p.None", context)
        self.assertIn("p.2", context)

    def test_invalid_query_does_not_retrieve_or_initialize_provider(self):
        with patch.object(agent, "create_generate") as factory:
            with self.assertRaises(ValueError):
                agent.ask_question(" ", retrieve=lambda q, k: self.fail("must not retrieve"))
        factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()

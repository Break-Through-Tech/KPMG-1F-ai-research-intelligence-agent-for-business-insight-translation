import http.client
from http.server import ThreadingHTTPServer
import json
from threading import Thread
import unittest
from unittest.mock import Mock, patch

from src.experimental.arxiv_fallback import ArxivDiscovery, arxiv_clause, html_passages, search_terms
from src.indexed_research import IndexedResearch
from src.research_demo import DemoHandler

QUESTION = "What fraction of customer support requests did the benchmark resolve?"
LIBRARY = "The existing study reports a latency of 40 seconds for data processing."
FINDING = "The support benchmark resolved 62 percent of simulated customer requests."
FEED = b"""<feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
 <opensearch:totalResults>2</opensearch:totalResults>
 <entry><id>https://arxiv.org/abs/2601.12345v2</id><title>Support Benchmark</title>
 <summary>Evaluation of simulated support tasks.</summary><published>2026-01-01</published></entry>
 <entry><id>https://arxiv.org/abs/2601.12345v2</id><title>Support Benchmark</title>
 <summary>Duplicate version.</summary><published>2026-01-01</published></entry></feed>"""
HTML = (f'<div>arXiv:2601.12345v2</div><section class="ltx_section" id="S1">'
        f'<h2 class="ltx_title">Results</h2><p class="ltx_para">{FINDING} '
        'The study measured tasks in a simulator under fixed policies. This '
        'benchmark used a fixed collection of test requests rather than live traffic.'
        '</p></section>').encode()


def passage(text):
    return {"chunk_id": "local", "source": "synthetic", "title": "Library study",
            "text": text, "page_number": None, "arxiv_id": None,
            "pdf_url": None, "source_url": None}


class ArxivEndpointTests(unittest.TestCase):
    def post(self, *, library=LIBRARY, external_answers=True, timeout=False, provider_error=False, broaden=False):
        def generate(prompt):
            if prompt.startswith("Choose one to three"):
                terms = ["customer support benchmark", "retail"] if broaden else ["customer support benchmark"]
                return json.dumps({"terms": terms})
            if provider_error:
                raise RuntimeError("provider failed")
            payload = json.loads(prompt.rsplit("\n", 1)[-1])
            self.assertEqual(payload["question"], QUESTION)
            row = payload["paper_passages"][0]
            external = row.get("arxiv_id") == "2601.12345v2"
            support = {"chunk_id": row["chunk_id"], "quote": row["text"]}
            if (external and external_answers) or row["text"] == FINDING:
                return json.dumps({"status": "ok", "claims": [
                    {"kind": "finding", "text": FINDING, "support": [support]}],
                    "limitations": []})
            return json.dumps({"status": "insufficient_evidence", "claims": [],
                               "limitations": [{"text": "The supplied evidence cannot answer the question.",
                                                "support": [support]}]})

        search = ArxivDiscovery(generate)
        service = IndexedResearch(retrieve=lambda q, k: [passage(library)], identity=lambda: {"count": 1},
                                  generate=generate, metadata={"provider": "fixture"}, index_path="fixture",
                                  arxiv_search=search)
        class Handler(DemoHandler):
            research = service
            library = None
            presentation_generate = None
            def log_message(self, *args):
                pass

        empty = FEED.split(b"<entry>", 1)[0].replace(b">2<", b">0<") + b"</feed>"
        responses = [empty, FEED, HTML] if broaden else [FEED, HTML]
        if timeout == "after_one":
            prefix, tail = FEED.rsplit(b"<entry>", 1)
            responses = [prefix + b"<entry>" + tail.replace(b"2601.12345v2", b"2601.12346v1"),
                         HTML, TimeoutError("fixture after first extraction")]
        fetch = Mock(side_effect=TimeoutError("fixture") if timeout is True else responses)
        with patch("src.experimental.arxiv_fallback.read_public", fetch), \
             patch("src.experimental.arxiv_fallback.sleep"), \
             ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                conn.request("POST", "/api/research",
                             json.dumps({"query": QUESTION, "context_id": service.context_id}),
                             {"Content-Type": "application/json"})
                response = conn.getresponse()
                body = json.loads(response.read())
                self.assertEqual(response.status, 200)
                conn.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
        return body, fetch

    def test_supported_library_answer_skips_arxiv(self):
        body, fetch = self.post(library=FINDING)
        self.assertEqual(body["result"]["summary"]["status"], "ok")
        self.assertNotIn("arxiv_search", body["result"]["provenance"])
        fetch.assert_not_called()

    def test_abstention_triggers_versioned_discovery_and_cited_answer(self):
        body, fetch = self.post()
        self.assertIsNone(body["error"])
        result = body["result"]
        self.assertEqual(result["summary"]["status"], "ok")
        self.assertEqual(result["provenance"]["arxiv_search"]["status"], "answered")
        self.assertEqual(result["evidence"][0]["source_url"], "https://arxiv.org/html/2601.12345v2#S1")
        self.assertEqual(result["summary"]["claims"][0]["chunk_ids"], [result["evidence"][0]["chunk_id"]])
        self.assertEqual(fetch.call_count, 2)

    def test_readable_candidate_still_cannot_answer(self):
        body, _ = self.post(external_answers=False)
        result = body["result"]
        self.assertEqual(result["summary"]["status"], "insufficient_evidence")
        self.assertEqual(result["provenance"]["arxiv_search"]["status"], "insufficient_evidence")

    def test_timeout_preserves_original_evidence_and_abstention(self):
        body, _ = self.post(timeout=True)
        result = body["result"]
        self.assertEqual(result["summary"]["status"], "insufficient_evidence")
        self.assertEqual(result["evidence"], [passage(LIBRARY)])
        self.assertEqual(result["provenance"]["arxiv_search"]["status"], "timeout")

    def test_provider_failure_does_not_trigger_external_search(self):
        body, fetch = self.post(provider_error=True)
        self.assertEqual(body["error"]["stage"], "summary")
        self.assertIsNone(body["result"])
        fetch.assert_not_called()

    def test_empty_conjunction_retries_first_phrase_before_reading_papers(self):
        body, fetch = self.post(broaden=True)
        self.assertEqual(body["result"]["provenance"]["arxiv_search"]["status"], "answered")
        self.assertEqual(fetch.call_count, 3)
        self.assertIn('AND all:"retail"', fetch.call_args_list[0].kwargs["params"]["search_query"])
        self.assertEqual(fetch.call_args_list[1].kwargs["params"]["search_query"],
                         'all:"customer" AND all:"support" AND all:"benchmark"')

    def test_claude_question_preserves_library_result_in_both_timeout_variants(self):
        question = ("Do the AI legal research tools that law firms buy still make things up, "
                    "even though they look up real sources?")
        with patch(__name__ + ".QUESTION", question):
            for timeout, fetched, extracted in ((True, 1, 0), ("after_one", 3, 1)):
                with self.subTest(timeout=timeout), patch(
                    "src.experimental.arxiv_fallback.html_passages", wraps=html_passages
                ) as extract:
                    body, fetch = self.post(timeout=timeout)
                    result = body["result"]
                    self.assertEqual(body["submitted_request"]["query"], question)
                    self.assertEqual(result["summary"]["query"], question)
                    self.assertEqual(result["summary"]["status"], "insufficient_evidence")
                    self.assertEqual(result["evidence"], [passage(LIBRARY)])
                    self.assertEqual(result["provenance"]["arxiv_search"]["status"], "timeout")
                    self.assertEqual(fetch.call_count, fetched)
                    self.assertEqual(extract.call_count, extracted)

    def test_real_planner_outputs_are_safe_and_searchable(self):
        terms = ["retrieval-augmented legal research hallucinations",
                 "commercial legal AI citation accuracy"]
        planned = search_terms("Legal research question", lambda _: json.dumps({"terms": terms}))
        self.assertEqual(planned, terms)
        self.assertIn('all:"legal" AND all:"research"', arxiv_clause(planned[0]))
        terms = [chr(964) + "-bench retail agent reliability pass^8"]
        planned = search_terms("Retail benchmark question", lambda _: json.dumps({"terms": terms}))
        query = arxiv_clause(planned[0])
        self.assertNotIn("^", query)
        self.assertIn('all:"8"', query)


class ResearchCitationTests(unittest.TestCase):
    def test_real_quote_with_an_invented_number_is_rejected(self):
        from src.research_chat import attach_validated_citations, validate_reported_numbers
        source = passage("The measured success rate was 62% in 2024.")
        claim = {"kind": "finding", "text": "The success rate was 72% in 2024.",
                 "support": [{"chunk_id": "local", "quote": source["text"]}]}
        attach_validated_citations([claim], [source])
        with self.assertRaisesRegex(ValueError, "number absent"):
            validate_reported_numbers([claim])

    def test_partial_quote_cannot_support_both_values(self):
        from src.research_chat import validate_reported_numbers
        item = {"kind": "finding", "text": "The two groups scored 0.75 and 0.84.",
                "support": [{"quote": "The first group scored .75 on the benchmark."}]}
        with self.assertRaises(ValueError):
            validate_reported_numbers([item])
        item["support"].append({"quote": "The second group scored 0.84 on the benchmark."})
        validate_reported_numbers([item])

    def test_incorrect_source_does_not_pass_even_if_number_matches(self):
        from src.research_chat import attach_validated_citations
        item = {"kind": "finding", "text": "The reported score was 62%.",
                "support": [{"chunk_id": "local", "quote": "A different paper scored 62%."}]}
        with self.assertRaisesRegex(ValueError, "absent from"):
            attach_validated_citations([item], [passage("The measured success rate was 62% in 2024.")])

    def test_companion_adds_relevant_results_within_budget(self):
        from src.experimental.evidence_coverage import with_result_coverage
        hits = [dict(passage("Agent benchmark tasks and models."), chunk_id=str(i),
                     arxiv_id="same") for i in range(3)]
        results = dict(passage("Agent benchmark success rates were 62% and 71%."),
                       chunk_id="results", arxiv_id="same", section="Results")
        unrelated = dict(results, chunk_id="other", arxiv_id="different")
        retrieve = with_result_coverage(lambda q, k: hits, hits + [unrelated, results])
        self.assertEqual(retrieve("How often did agents succeed?", 3), hits[:2] + [results])
        self.assertEqual(retrieve("What is the benchmark?", 3), hits)

    def test_scope_passage_is_from_the_retrieved_study(self):
        from src.experimental.evidence_coverage import with_study_scope
        hits = [dict(passage("The benchmark evaluated agents."), chunk_id=str(i),
                     arxiv_id="same") for i in range(2)]
        dates = dict(passage("The queries were run from March 22 to April 22, 2024."),
                     chunk_id="dates", arxiv_id="same", section="Methodology", subsection="Query execution")
        self.assertEqual(with_study_scope("Do tools still make mistakes?", hits, [dates]),
                         [hits[0], dates])
        self.assertEqual(with_study_scope("What were the findings?", hits, [dates]), hits)

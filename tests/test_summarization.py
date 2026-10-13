"""Offline tests for src.summarization. Run from the repo root: python -m pytest tests/test_summarization.py"""

import json
from pathlib import Path

import pytest

from src import summarization as S
from src.summarization import summarize

FIXTURES = Path(__file__).parent / "fixtures" / "summarization"


class FakeGenerate:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if self.exc:
            raise self.exc
        return self.response


def passage(chunk_id, text="Some evidence text.", **extra):
    base = {
        "chunk_id": chunk_id,
        "text": text,
        "distance": 0.3,
        "arxiv_id": "0000.00009",
        "title": "Synthetic Title",
        "pdf_url": "https://example.org/p.pdf",
        "source": "pdf",
        "source_url": "https://example.org/p.pdf",
        "page_number": 1,
    }
    base.update(extra)
    return base


def ok_response(*claims, limitations=()):
    return json.dumps(
        {
            "status": "ok",
            "claims": [{"text": t, "chunk_ids": ids} for t, ids in claims],
            "limitations": list(limitations),
        }
    )


# --- supported output -------------------------------------------------------

def test_supported_output_with_mixed_html_pdf_sources():
    passages = [
        passage("h1", source="html", page_number=None, html_url="https://example.org/h", section="Results"),
        passage("p1", page_number=7),
    ]
    gen = FakeGenerate(ok_response(("Claim A.", ["h1"]), ("Claim B.", ["p1", "h1"]), limitations=["Small sample."]))
    result = summarize("q?", passages, generate=gen)

    assert result["status"] == "ok"
    assert result["error"] is None
    assert result["claims"] == [
        {"text": "Claim A.", "chunk_ids": ["h1"]},
        {"text": "Claim B.", "chunk_ids": ["p1", "h1"]},
    ]
    assert result["limitations"] == ["Small sample."]
    mapping = {c["chunk_id"]: c for c in result["included_chunks"]}
    assert mapping["h1"]["page_number"] is None and mapping["h1"]["html_url"] == "https://example.org/h"
    assert mapping["p1"]["page_number"] == 7
    assert "confidence" not in json.dumps(result).lower()
    assert "distance" not in mapping["h1"]


def test_prompt_contains_query_and_chunk_ids_but_not_distance():
    gen = FakeGenerate(ok_response(("Claim.", ["a"])))
    summarize("what is x?", [passage("a")], generate=gen)
    prompt = gen.prompts[0]
    assert "what is x?" in prompt and "[chunk_id: a]" in prompt
    assert "distance" not in prompt.lower()


def test_fenced_json_and_duplicate_citations_are_normalized():
    raw = "```json\n" + ok_response(("Claim.", ["a", "a"])) + "\n```"
    result = summarize("q", [passage("a")], generate=FakeGenerate(raw))
    assert result["status"] == "ok"
    assert result["claims"][0]["chunk_ids"] == ["a"]


# --- empty evidence ---------------------------------------------------------

@pytest.mark.parametrize("passages", [[], None, [passage("a", text="   ")], ["not a dict"], [{"text": "no id"}]])
def test_empty_or_unusable_evidence_skips_generation(passages):
    gen = FakeGenerate(ok_response(("x", ["a"])))
    result = summarize("q", passages, generate=gen)
    assert result["status"] == S.STATUS_INSUFFICIENT
    assert result["claims"] == []
    assert result["limitations"]
    assert gen.prompts == []


def test_duplicate_chunk_ids_are_dropped_and_noted():
    gen = FakeGenerate(ok_response(("Claim.", ["a"])))
    result = summarize("q", [passage("a"), passage("a", text="other")], generate=gen)
    assert [c["chunk_id"] for c in result["included_chunks"]] == ["a"]
    assert any("ignored" in note for note in result["limitations"])


# --- hallucinated IDs -------------------------------------------------------

def test_hallucinated_chunk_id_rejects_entire_response():
    gen = FakeGenerate(ok_response(("Good.", ["a"]), ("Bad.", ["a", "ghost"])))
    result = summarize("q", [passage("a")], generate=gen)
    assert result["status"] == S.STATUS_INSUFFICIENT
    assert result["claims"] == []
    assert result["error"] == S.ERROR_INVALID_CITATIONS
    assert "ghost" in " ".join(result["limitations"])


def test_citing_passage_omitted_by_context_limit_is_rejected():
    passages = [passage("a", text="x" * 150), passage("b", text="y" * 150)]
    gen = FakeGenerate(ok_response(("Claim.", ["b"])))
    result = summarize("q", passages, generate=gen, max_context_chars=300)
    assert result["omitted_chunk_ids"] == ["b"]
    assert result["error"] == S.ERROR_INVALID_CITATIONS


# --- malformed responses ----------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    [
        "not json at all",
        "",
        None,
        42,
        "[1, 2]",
        json.dumps({"claims": []}),
        json.dumps({"status": "maybe", "claims": []}),
        json.dumps({"status": "ok"}),
        json.dumps({"status": "ok", "claims": []}),
        json.dumps({"status": "ok", "claims": ["just text"]}),
        json.dumps({"status": "ok", "claims": [{"text": "x"}]}),
        json.dumps({"status": "ok", "claims": [{"text": "x", "chunk_ids": []}]}),
        json.dumps({"status": "ok", "claims": [{"text": "", "chunk_ids": ["a"]}]}),
        json.dumps({"status": "ok", "claims": [{"text": "x", "chunk_ids": "a"}]}),
        json.dumps({"status": "ok", "claims": [{"text": "x", "chunk_ids": ["a"]}], "limitations": "nope"}),
        json.dumps({"status": "insufficient_evidence", "claims": [{"text": "x", "chunk_ids": ["a"]}]}),
    ],
)
def test_malformed_response_never_fabricates(raw):
    result = summarize("q", [passage("a")], generate=FakeGenerate(raw))
    assert result["status"] == S.STATUS_INSUFFICIENT
    assert result["claims"] == []
    assert result["error"] == S.ERROR_MALFORMED_RESPONSE
    assert result["limitations"]


def test_model_reported_insufficient_evidence_is_not_an_error():
    raw = json.dumps({"status": "insufficient_evidence", "claims": [], "limitations": []})
    result = summarize("q", [passage("a")], generate=FakeGenerate(raw))
    assert result["status"] == S.STATUS_INSUFFICIENT
    assert result["error"] is None
    assert result["limitations"]


# --- generation failure -----------------------------------------------------

def test_generation_failure_returns_insufficient_evidence():
    result = summarize("q", [passage("a")], generate=FakeGenerate(exc=TimeoutError("secret-key-123")))
    assert result["status"] == S.STATUS_INSUFFICIENT
    assert result["claims"] == []
    assert result["error"] == S.ERROR_GENERATION_FAILED
    assert "TimeoutError" in result["limitations"][0]
    assert "secret-key-123" not in json.dumps(result)  # never echo exception text
    assert [c["chunk_id"] for c in result["included_chunks"]] == ["a"]


# --- deterministic context bound -------------------------------------------

def test_context_is_bounded_ordered_and_deterministic():
    passages = [passage(f"c{i}", text=f"text {i} " * 40) for i in range(10)]
    runs = []
    for _ in range(2):
        gen = FakeGenerate(ok_response(("Claim.", ["c0"])))
        result = summarize("q", passages, generate=gen, max_context_chars=1000)
        runs.append((gen.prompts[0], result))
    assert runs[0] == runs[1]

    prompt, result = runs[0]
    included = [c["chunk_id"] for c in result["included_chunks"]]
    omitted = result["omitted_chunk_ids"]
    assert included + omitted == [f"c{i}" for i in range(10)]  # order preserved, nothing lost
    assert omitted and included
    evidence = prompt.split("Passages:\n", 1)[1]
    assert len(evidence) <= 1000
    assert all(f"[chunk_id: {i}]" in evidence for i in included)
    assert not any(f"[chunk_id: {i}]" in evidence for i in omitted)
    assert any("Context limit reached" in n for n in result["limitations"])


def test_long_passage_is_truncated_and_flagged():
    gen = FakeGenerate(ok_response(("Claim.", ["a"])))
    result = summarize("q", [passage("a", text="word " * 1000)], generate=gen, max_passage_chars=100)
    assert result["included_chunks"][0]["truncated"] is True
    assert S.TRUNCATION_MARKER in gen.prompts[0]
    assert any("shortened" in n for n in result["limitations"])


def test_first_oversized_passage_is_shrunk_to_fit_budget():
    gen = FakeGenerate(ok_response(("Claim.", ["a"])))
    result = summarize("q", [passage("a", text="z" * 5000)], generate=gen, max_context_chars=400, max_passage_chars=5000)
    evidence = gen.prompts[0].split("Passages:\n", 1)[1]
    assert len(evidence) <= 400
    assert result["included_chunks"][0]["truncated"] is True and result["status"] == "ok"


# --- input validation -------------------------------------------------------

@pytest.mark.parametrize("query", ["", "   ", None, 5])
def test_blank_query_raises(query):
    with pytest.raises(ValueError):
        summarize(query, [passage("a")], generate=FakeGenerate("{}"))


def test_bad_arguments_raise():
    with pytest.raises(TypeError):
        summarize("q", [passage("a")], generate="not callable")
    with pytest.raises(ValueError):
        summarize("q", [passage("a")], generate=FakeGenerate("{}"), max_context_chars=10)
    with pytest.raises(ValueError):
        summarize("q", [passage("a")], generate=FakeGenerate("{}"), max_passage_chars=1)


# --- committed fixtures -----------------------------------------------------

@pytest.mark.parametrize("name", sorted(p.name for p in FIXTURES.glob("*.json")))
def test_fixture_examples(name):
    fx = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    gen = FakeGenerate(json.dumps(fx["model_response"]))
    result = summarize(fx["query"], fx["passages"], generate=gen)
    exp = fx["expected"]
    assert result["status"] == exp["status"]
    assert result["error"] == exp["error"]
    assert [c["chunk_id"] for c in result["included_chunks"]] == exp["included_chunk_ids"]
    assert result["omitted_chunk_ids"] == exp["omitted_chunk_ids"]
    assert [c["chunk_ids"] for c in result["claims"]] == exp["claim_chunk_ids"]
    assert result["limitations"] == exp["limitations"]


def test_at_least_two_fixture_examples_exist():
    assert len(list(FIXTURES.glob("*.json"))) >= 2
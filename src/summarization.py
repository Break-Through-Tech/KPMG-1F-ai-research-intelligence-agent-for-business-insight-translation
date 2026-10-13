"""Grounded research summaries from retrieved passages (Week 5, Lane A).

``summarize(query, passages, *, generate)`` turns the passages returned by
``src.retrieval.search`` into a ``ResearchSummary`` dictionary (working
interface v1). The model is injected as ``generate(prompt) -> str`` so the
module needs no live API and is fully testable offline.

Guarantees:
  * Findings are restricted to the supplied passages; every claim cites chunk
    IDs that were actually shown to the model. Any unknown ID rejects the
    whole response (no partial salvage, no fabricated answers).
  * Empty or unusable evidence, generation failures, and malformed responses
    all yield ``status="insufficient_evidence"`` with no claims. Failures set
    the additive ``error`` field so callers can tell them from a genuine
    "the evidence does not answer this" result.
  * Context size is bounded deterministically (input order is preserved, no
    reranking) and the result maps back to the chunks that were included.

Syntactically valid citations still need human support checks. ``distance``
is never converted into a confidence score.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template
from typing import Any, Callable, Iterable, Mapping, Optional

STATUS_OK = "ok"
STATUS_INSUFFICIENT = "insufficient_evidence"
VALID_STATUSES = (STATUS_OK, STATUS_INSUFFICIENT)

ERROR_GENERATION_FAILED = "generation_failed"
ERROR_MALFORMED_RESPONSE = "malformed_response"
ERROR_INVALID_CITATIONS = "invalid_citations"

DEFAULT_MAX_CONTEXT_CHARS = 12_000
DEFAULT_MAX_PASSAGE_CHARS = 2_500
MIN_MAX_CONTEXT_CHARS = 200
MIN_MAX_PASSAGE_CHARS = 50
TRUNCATION_MARKER = " [truncated]"

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts" 
PROMPT_FILE = "research_summary.txt"

# Source fields carried into the included-chunk mapping (distance is omitted on
# purpose: it is a retrieval score, not a confidence).
_MAPPING_FIELDS = (
    "arxiv_id",
    "title",
    "source",
    "source_url",
    "pdf_url",
    "html_url",
    "page_number",
    "section",
    "subsection",
)

_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL | re.IGNORECASE)


class SummaryResponseError(ValueError):
    """A model response failed parsing or validation. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------
# Evidence handling
# --------------------------------------------------------------------------

def _normalize_passages(passages: Optional[Iterable[Any]]) -> tuple[list[dict], int]:
    """Keep usable passages in input order; drop malformed and duplicate chunk IDs."""
    seen: set[str] = set()
    usable: list[dict] = []
    dropped = 0
    for passage in passages or []:
        if not isinstance(passage, Mapping):
            dropped += 1
            continue
        chunk_id = passage.get("chunk_id")
        text = passage.get("text")
        if (
            not isinstance(chunk_id, str)
            or not chunk_id.strip()
            or not isinstance(text, str)
            or not text.strip()
        ):
            dropped += 1
            continue
        chunk_id = chunk_id.strip()
        if chunk_id in seen:
            dropped += 1
            continue
        seen.add(chunk_id)
        usable.append({**passage, "chunk_id": chunk_id, "text": text.strip()})
    return usable, dropped


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - len(TRUNCATION_MARKER)].rstrip() + TRUNCATION_MARKER


def _metadata_line(passage: Mapping[str, Any]) -> str:
    parts = []
    if passage.get("title"):
        parts.append(f"title: {passage['title']}")
    parts.append(f"source: {passage.get('source') or 'unknown'}")
    where = " > ".join(str(passage[k]) for k in ("section", "subsection") if passage.get(k))
    if where:
        parts.append(f"section: {where}")
    page = passage.get("page_number")
    if isinstance(page, int) and not isinstance(page, bool) and page > 0:
        parts.append(f"page: {page}")  # HTML passages have page_number=None
    return " | ".join(parts)


def _render_block(passage: Mapping[str, Any], text: str) -> str:
    return f"[chunk_id: {passage['chunk_id']}]\n{_metadata_line(passage)}\n{text}\n\n"


def _build_context(
    passages: list[dict], max_context_chars: int, max_passage_chars: int
) -> tuple[str, list[tuple[dict, bool]], list[str]]:
    """Greedily include passages in input order until the budget is spent.

    Returns (context, [(passage, was_truncated)], omitted_chunk_ids). Stops at
    the first passage that does not fit so ranking order is respected. Only the
    first passage may be shrunk to fit; later ones are omitted whole.
    """
    remaining = max_context_chars
    blocks: list[str] = []
    included: list[tuple[dict, bool]] = []
    omitted: list[str] = []

    for index, passage in enumerate(passages):
        text = passage["text"]
        truncated = False
        if len(text) > max_passage_chars:
            text = _truncate(text, max_passage_chars)
            truncated = True
        block = _render_block(passage, text)

        if len(block) > remaining:
            if blocks:
                omitted = [p["chunk_id"] for p in passages[index:]]
                break
            room = remaining - len(_render_block(passage, ""))
            if room < len(TRUNCATION_MARKER) + 20:
                omitted = [p["chunk_id"] for p in passages[index:]]
                break
            text = _truncate(passage["text"], room)
            truncated = True
            block = _render_block(passage, text)

        blocks.append(block)
        remaining -= len(block)
        included.append((passage, truncated))

    return "".join(blocks).rstrip(), included, omitted


# --------------------------------------------------------------------------
# Prompt and response parsing
# --------------------------------------------------------------------------

def build_prompt(query: str, context: str, template: Optional[str] = None) -> str:
    if template is None:
        template = (PROMPT_DIR / PROMPT_FILE).read_text(encoding="utf-8")
    return Template(template).substitute(query=query, evidence=context)


def parse_response(raw: Any, allowed_ids: Iterable[str]) -> tuple[str, list[dict], list[str]]:
    """Parse and validate a model response.

    Returns (status, claims, limitations). Raises SummaryResponseError with code
    ``malformed_response`` for structural problems or ``invalid_citations`` when
    any cited chunk ID was not shown to the model.
    """
    allowed = set(allowed_ids)
    if not isinstance(raw, str) or not raw.strip():
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "response is empty or not text")

    text = raw.strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, f"response is not valid JSON: {exc.msg}")
    if not isinstance(data, dict):
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "response JSON must be an object")

    status = data.get("status")
    if status not in VALID_STATUSES:
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "status must be 'ok' or 'insufficient_evidence'")

    raw_limitations = data.get("limitations", [])
    if not isinstance(raw_limitations, list) or not all(isinstance(x, str) for x in raw_limitations):
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "limitations must be a list of strings")
    limitations = [x.strip() for x in raw_limitations if x.strip()]

    raw_claims = data.get("claims")
    if not isinstance(raw_claims, list):
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "claims must be a list")

    if status == STATUS_INSUFFICIENT:
        if raw_claims:
            raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "insufficient_evidence must not include claims")
        return status, [], limitations

    if not raw_claims:
        raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, "status 'ok' requires at least one claim")

    claims: list[dict] = []
    unknown: list[str] = []
    for position, claim in enumerate(raw_claims):
        if not isinstance(claim, dict):
            raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, f"claim {position} must be an object")
        claim_text = claim.get("text")
        if not isinstance(claim_text, str) or not claim_text.strip():
            raise SummaryResponseError(ERROR_MALFORMED_RESPONSE, f"claim {position} has no text")
        ids = claim.get("chunk_ids")
        if (
            not isinstance(ids, list)
            or not ids
            or not all(isinstance(i, str) and i.strip() for i in ids)
        ):
            raise SummaryResponseError(
                ERROR_MALFORMED_RESPONSE, f"claim {position} needs a non-empty list of chunk_ids"
            )
        deduped = list(dict.fromkeys(i.strip() for i in ids))
        unknown.extend(i for i in deduped if i not in allowed)
        claims.append({"text": claim_text.strip(), "chunk_ids": deduped})

    if unknown:
        shown = ", ".join(sorted(set(unknown)))
        raise SummaryResponseError(ERROR_INVALID_CITATIONS, f"cited chunk IDs were not supplied: {shown}")

    return status, claims, limitations


# --------------------------------------------------------------------------
# Public boundary
# --------------------------------------------------------------------------

def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _result(
    query: str,
    status: str,
    claims: list[dict],
    limitations: list[str],
    included: list[tuple[dict, bool]],
    omitted: list[str],
    error: Optional[str] = None,
) -> dict:
    return {
        "status": status,
        "query": query,
        "claims": claims,
        "limitations": _dedupe(limitations),
        # Additive fields (interface v1 prefers additive changes):
        "included_chunks": [
            {"chunk_id": p["chunk_id"], **{k: p.get(k) for k in _MAPPING_FIELDS if k in p}, "truncated": t}
            for p, t in included
        ],
        "omitted_chunk_ids": list(omitted),
        "error": error,
    }


def summarize(
    query: str,
    passages: Optional[Iterable[Mapping[str, Any]]],
    *,
    generate: Callable[[str], str],
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    max_passage_chars: int = DEFAULT_MAX_PASSAGE_CHARS,
) -> dict:
    """Produce a cited ``ResearchSummary`` from retrieved passages.

    Args:
        query: the research question (non-empty), preserved exactly in the output.
        passages: ``EvidencePassage`` dicts as returned by ``src.retrieval.search``.
        generate: ``prompt text -> response text``; injected so tests use fakes.
        max_context_chars: hard cap on the evidence section of the prompt.
        max_passage_chars: cap on any single passage's text.

    Programmer errors (blank query, non-callable ``generate``, bad size limits)
    raise. Runtime problems (no evidence, generation failure, bad model output)
    return ``insufficient_evidence`` with explanatory limitations instead.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not callable(generate):
        raise TypeError("generate must be callable")
    if not isinstance(max_context_chars, int) or max_context_chars < MIN_MAX_CONTEXT_CHARS:
        raise ValueError(f"max_context_chars must be an int >= {MIN_MAX_CONTEXT_CHARS}")
    if not isinstance(max_passage_chars, int) or max_passage_chars < MIN_MAX_PASSAGE_CHARS:
        raise ValueError(f"max_passage_chars must be an int >= {MIN_MAX_PASSAGE_CHARS}")

    usable, dropped = _normalize_passages(passages)
    notes: list[str] = []
    if dropped:
        notes.append(f"{dropped} passage(s) were ignored because they were malformed, empty, or duplicated.")

    if not usable:
        return _result(
            query,
            STATUS_INSUFFICIENT,
            [],
            ["No usable evidence passages were supplied; no summary was generated."] + notes,
            [],
            [],
        )

    context, included, omitted = _build_context(usable, max_context_chars, max_passage_chars)
    if omitted:
        notes.append(
            f"Context limit reached: {len(omitted)} passage(s) were not shown to the summarizer "
            f"({', '.join(omitted)})."
        )
    shortened = [p["chunk_id"] for p, t in included if t]
    if shortened:
        notes.append(f"Passage text was shortened before summarizing: {', '.join(shortened)}.")

    prompt = build_prompt(query, context)
    try:
        raw = generate(prompt)
    except Exception as exc:  # noqa: BLE001 - any generator failure must not crash the workflow
        return _result(
            query,
            STATUS_INSUFFICIENT,
            [],
            [f"Summary generation failed ({type(exc).__name__}); no findings were produced."] + notes,
            included,
            omitted,
            ERROR_GENERATION_FAILED,
        )

    try:
        status, claims, limitations = parse_response(raw, [p["chunk_id"] for p, _ in included])
    except SummaryResponseError as exc:
        return _result(
            query,
            STATUS_INSUFFICIENT,
            [],
            [f"The model response was rejected ({exc}); no findings were produced."] + notes,
            included,
            omitted,
            exc.code,
        )

    if status == STATUS_INSUFFICIENT and not limitations:
        limitations = ["The supplied passages do not support an answer to the query."]
    return _result(query, status, claims, limitations + notes, included, omitted)
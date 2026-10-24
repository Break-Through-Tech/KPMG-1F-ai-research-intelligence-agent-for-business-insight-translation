"""Optional presentation adapter; structural checks are not semantic approval."""
from copy import deepcopy
from hashlib import sha256
import json

from src.research_contracts import validate_result


def result_identity(result):
    return sha256(json.dumps(result, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":")).encode()).hexdigest()


def plain_language_view(result, candidate=None):
    """Bind an all-or-nothing summary rewrite to the exact unmodified result.

    Business actions, assumptions, gaps, limitations and review remain original.
    Provider callers must catch generation errors and supply status=failed.
    """
    validate_result(result)
    if candidate is None:
        return {"status": "unavailable", "reason": "Plain-language generation is not configured. The original answer is retained."}
    try:
        if candidate.get("status") == "failed":
            return {"status": "failed", "reason": "Simplification failed. The original answer is retained."}
        if (candidate["version"] != "1.0" or candidate["status"] != "available"
                or candidate["result_identity"] != result_identity(result)
                or candidate["semantic_review"] != "pending"
                or not isinstance(candidate["fixture"], bool)):
            raise ValueError("Invalid presentation identity/status")
        claims = result["summary"]["claims"]
        rewrites = candidate["claims"]
        if not isinstance(rewrites, list) or len(rewrites) != len(claims):
            raise ValueError("Every original claim must be retained")
        passages = {p["chunk_id"]: p for p in result["evidence"]}
        def text(value):
            return isinstance(value, str) and 0 < len(value.strip()) <= 6000
        def support(items, allowed):
            if not isinstance(items, list) or not items:
                raise ValueError("Support required")
            for item in items:
                if (item["chunk_id"] not in allowed or not text(item["quote"])
                        or item["quote"] not in passages[item["chunk_id"]]["text"]):
                    raise ValueError("Quote must belong to cited evidence")
            if {s["chunk_id"] for s in items} != set(allowed):
                raise ValueError("Every citation needs support")
        for index, (original, rewrite) in enumerate(zip(claims, rewrites)):
            if (rewrite["claim_index"] != index or not text(rewrite["text"])
                    or rewrite["chunk_ids"] != original["chunk_ids"]):
                raise ValueError("Claim mapping/citations changed")
            support(rewrite["support"], original["chunk_ids"])
        definitions = candidate["definitions"]
        if not isinstance(definitions, list):
            raise ValueError("Definitions must be a list")
        for definition in definitions:
            if not text(definition["term"]):
                raise ValueError("Term required")
            if definition["status"] == "unavailable":
                if not text(definition["reason"]):
                    raise ValueError("Unavailable reason required")
            elif definition["status"] == "supported" and text(definition["text"]):
                ids = definition["chunk_ids"]
                if not isinstance(ids, list) or not ids or any(i not in passages for i in ids):
                    raise ValueError("Definition citation missing")
                support(definition["support"], ids)
            else:
                raise ValueError("Unsupported definition status")
        return deepcopy(candidate)
    except (KeyError, TypeError, ValueError, AttributeError):
        return {"status": "failed", "reason": "Simplification contract validation failed. The original answer is retained."}


def fixture_view(result):
    """Hand-authored demonstration only; never called for live/saved results."""
    rewrites = {
        "Synthetic agents need task-specific evaluation.": "Synthetic agents need to be tested for the specific task.",
        "Synthetic evidence requires human checks.": "People need to check synthetic evidence.",
    }
    claims = []
    for index, claim in enumerate(result["summary"]["claims"]):
        if claim["text"] not in rewrites:
            return plain_language_view(result)
        claims.append({"claim_index": index, "text": rewrites[claim["text"]],
                       "chunk_ids": claim["chunk_ids"], "support": [
                           {"chunk_id": id, "quote": claim["text"]} for id in claim["chunk_ids"]]})
    quote = "Task-specific evaluation means testing an agent on the particular task it is intended to perform."
    passage = next((p for p in result["evidence"] if quote in p["text"]), None)
    definition = ({"term": "Task-specific evaluation", "status": "supported",
                   "text": "Testing an agent on the particular task it is intended to perform.",
                   "chunk_ids": [passage["chunk_id"]],
                   "support": [{"chunk_id": passage["chunk_id"], "quote": quote}]}
                  if passage else {"term": "Task-specific evaluation", "status": "unavailable",
                                   "reason": "The available passages do not define this term."})
    return plain_language_view(result, {"version": "1.0", "status": "available",
        "result_identity": result_identity(result), "fixture": True,
        "semantic_review": "pending", "claims": claims, "definitions": [definition]})

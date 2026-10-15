"""Human review bridge for research results (Issue #81)."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Callable, Dict, Optional

_REVIEW_KEYS = {"human_review", "approved", "review_fingerprint"}
_ALLOWED_DECISIONS = {"approve", "revise", "reject"}

def _fingerprint(result: Dict[str, Any]) -> str:
    """Bind review to every JSON-compatible result/context field, not review metadata."""
    content = {key: value for key, value in result.items() if key not in _REVIEW_KEYS}
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()

def _require_dict(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a dictionary")
    return value

def make_review_packet(result: Dict[str, Any]) -> Dict[str, Any]:
    """Copy a result into a pending packet; prior approval is never carried forward."""
    _require_dict(result, "result")
    packet = deepcopy(result)
    packet["human_review"] = {"status": "pending", "reviewer": None, "notes": None}
    packet["approved"] = False
    packet["review_fingerprint"] = _fingerprint(packet)
    return packet

def _regulatory_verdict(result: Dict[str, Any]) -> Optional[str]:
    checkpoint = result.get("regulatory_checkpoint")
    if checkpoint is None:
        return None
    if not isinstance(checkpoint, dict):
        return "unresolved"
    assessment = checkpoint.get("assessment")
    if not isinstance(assessment, dict):
        return "unresolved"
    return assessment.get("verdict", "unresolved")

def record_human_decision(result: Dict[str, Any], *, reviewer: str, decision: str,
                          notes: Optional[str] = None) -> Dict[str, Any]:
    """Return a reviewed copy. Conflicting/unresolved regulatory gates cannot be approved."""
    _require_dict(result, "result")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("reviewer must be non-empty text")
    if not isinstance(decision, str) or decision.lower() not in _ALLOWED_DECISIONS:
        raise ValueError("decision must be one of: approve, revise, reject")
    decision = decision.lower()
    if notes is not None and not isinstance(notes, str):
        raise TypeError("notes must be text or None")
    updated = deepcopy(result)
    if updated.get("review_fingerprint") is not None:
        require_current_review(updated)
    if decision == "approve":
        verdict = _regulatory_verdict(updated)
        if verdict is not None and verdict != "potentially_feasible":
            raise ValueError("Resolve conflicting or insufficient regulatory evidence before approval")
    updated["human_review"] = {"status": decision, "reviewer": reviewer.strip(), "notes": notes}
    updated["approved"] = decision == "approve"
    updated["review_fingerprint"] = _fingerprint(updated)
    return updated

def require_current_review(result: Dict[str, Any]) -> None:
    """Reject edited content/context and inconsistent human approval metadata."""
    _require_dict(result, "result")
    review = result.get("human_review")
    if result.get("review_fingerprint") != _fingerprint(result):
        raise ValueError("Research inputs, outputs, or review context changed; obtain a new human review")
    if not isinstance(review, dict) or review.get("status") not in ({"pending"} | _ALLOWED_DECISIONS):
        raise ValueError("Human review record is missing or invalid")
    if bool(result.get("approved")) != (review.get("status") == "approve"):
        raise ValueError("Approval flag does not match the explicit human decision")

def _draft_insight(draft: Dict[str, Any]) -> str:
    business = draft.get("business_insight")
    if not isinstance(business, dict):
        return ""
    implications = business.get("implications", [])
    if not isinstance(implications, list):
        return ""
    return " ".join(item["text"].strip() for item in implications
                     if isinstance(item, dict) and isinstance(item.get("text"), str)
                     and item["text"].strip())

def review_adapter(draft: Dict[str, Any], *, retrieve_regulations_fn: Optional[Callable] = None,
                   assess_insight_fn: Optional[Callable] = None, industry: Optional[str] = None,
                   jurisdiction: Optional[str] = None, insight: Optional[str] = None,
                   as_of: Optional[str] = None) -> Dict[str, Any]:
    """Return a separate advisory regulatory bundle; it is never human approval.

    Injected functions follow human_checkpoint.retrieve_regulations(client, *, ...)
    and assess_insight(client, evidence). Paper evidence remains separate.
    """
    _require_dict(draft, "draft")
    if (retrieve_regulations_fn is None) != (assess_insight_fn is None):
        raise ValueError("Provide both regulatory retrieval and assessment functions")
    request = draft.get("request", {})
    if not isinstance(request, dict):
        request = {}
    industry = industry or request.get("industry")
    jurisdiction = jurisdiction or request.get("jurisdiction")
    insight = insight or _draft_insight(draft)
    result = {"schema_version": "1.0", "evidence_namespace": "regulatory",
              "approved": False, "status": "pending", "industry": industry,
              "jurisdiction": jurisdiction,
              "summary": "Human review required; regulatory assessment is advisory only.",
              "regulatory_evidence": None, "assessment": None,
              "human_review": {"status": "pending", "reviewer": None, "notes": None}}
    if retrieve_regulations_fn is None:
        result["reason"] = "No regulatory assessment requested."
        return result
    values = {"industry": industry, "jurisdiction": jurisdiction, "insight": insight}
    if any(not isinstance(value, str) or not value.strip() for value in values.values()):
        result["reason"] = "Industry, insight, and jurisdiction are required for regulatory assessment."
        return result
    kwargs = {"industry": industry, "insight": insight, "jurisdiction": jurisdiction}
    if as_of is not None:
        kwargs["as_of"] = as_of
    evidence = retrieve_regulations_fn(None, **kwargs)
    if not isinstance(evidence, dict) or not isinstance(evidence.get("sources"), list) or not isinstance(evidence.get("evidence"), list):
        raise ValueError("Regulatory retrieval must return a source-backed evidence dictionary")
    assessment_bundle = assess_insight_fn(None, deepcopy(evidence))
    if not isinstance(assessment_bundle, dict):
        raise ValueError("Regulatory assessment must return a dictionary")
    assessment = assessment_bundle.get("assessment")
    result["regulatory_evidence"] = deepcopy(evidence)
    result["assessment"] = deepcopy(assessment) if isinstance(assessment, dict) else None
    result["assessment_bundle"] = deepcopy(assessment_bundle)
    if isinstance(assessment, dict) and assessment.get("verdict") in {"potentially_feasible", "conflicts", "insufficient_evidence"}:
        result["status"] = "assessed"
        result["summary"] = assessment.get("summary", result["summary"])
    else:
        result["reason"] = "Assessment is unresolved; human approval remains blocked."
    return result

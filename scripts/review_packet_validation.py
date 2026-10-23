"""Issue #124 validation helper for review packets and contract handoffs.

This script is intentionally offline and uses the existing repository fixtures to
exercise the review bridge without making any external calls.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable

from src import research_review as rr
from src.regulatory_validation import validate_assessment_data
from tests.research_review_fixtures import demo_result


def _regulatory_checkpoint(verdict: str = "potentially_feasible") -> Dict[str, Any]:
    evidence = {
        "industry": "banking",
        "jurisdiction": "US",
        "sources": [{"source_id": 1, "url": "https://example.org/reg"}],
        "evidence": [{"text": "Synthetic rule", "source_ids": [1]}],
    }
    statuses = ["supported"] * 4
    if verdict == "conflicts":
        statuses[1] = "conflicts"
    elif verdict == "insufficient_evidence":
        statuses[2] = "unknown"

    assessment = {"verdict": verdict, "summary": "Synthetic advisory", "risks": []}
    for name, status in zip(
        ("regulatory_compliance", "legal_constraints", "governance", "operational_feasibility"),
        statuses,
    ):
        assessment[name] = {
            "status": status,
            "explanation": "Synthetic finding",
            "source_ids": [] if status == "unknown" else [1],
        }
    return {"assessment": assessment, "regulatory_evidence": evidence}


def _material_edit_invalidates_review(packet: Dict[str, Any]) -> None:
    stale = deepcopy(packet)
    stale["summary"]["claims"][0]["text"] = "Edited after approval"
    try:
        rr.require_current_review(stale)
    except ValueError:
        return
    raise AssertionError("Stale packet should fail current-review validation")


def _check_packet_flow() -> None:
    source = demo_result()
    packet = rr.make_review_packet(source)
    assert packet["human_review"]["status"] == "pending"
    assert packet["approved"] is False
    assert packet["review_fingerprint"]

    revised = rr.record_human_decision(
        packet, reviewer="Reviewer A", decision="revise", notes="Needs আরও source support"
    )
    assert revised["human_review"]["status"] == "revise"
    assert revised["approved"] is False
    rr.require_current_review(revised)

    rejected = rr.record_human_decision(
        packet,
        reviewer="Reviewer B",
        decision="reject",
        notes="Not suitable for delivery",
    )
    assert rejected["human_review"]["status"] == "reject"
    assert rejected["approved"] is False

    valid_checkpoint = _regulatory_checkpoint("potentially_feasible")
    valid_result = deepcopy(source)
    valid_result["regulatory_checkpoint"] = valid_checkpoint
    approved = rr.record_human_decision(
        rr.make_review_packet(valid_result), reviewer="Reviewer C", decision="approve", notes="Synthetic approval check"
    )
    assert approved["approved"] is True
    rr.require_current_review(approved)

    _material_edit_invalidates_review(approved)


def _check_regulatory_boundary() -> None:
    evidence = {"industry": "banking", "jurisdiction": "US",
                "sources": [{"source_id": 1, "url": "https://example.org/reg"}],
                "evidence": [{"text": "Synthetic rule", "source_ids": [1]}]}
    assessment = {
        "verdict": "potentially_feasible",
        "summary": "Synthetic advisory",
        "risks": [],
        "regulatory_compliance": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
        "legal_constraints": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
        "governance": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
        "operational_feasibility": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
    }
    validate_assessment_data(assessment, evidence)

    bad_assessment = deepcopy(assessment)
    bad_assessment["legal_constraints"] = {**bad_assessment["legal_constraints"], "source_ids": [99]}
    try:
        validate_assessment_data(bad_assessment, evidence)
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown regulatory citation should have been rejected")

    result = demo_result()
    result["regulatory_checkpoint"] = {"assessment": bad_assessment, "regulatory_evidence": evidence}
    try:
        rr.record_human_decision(rr.make_review_packet(result), reviewer="Reviewer", decision="approve")
    except ValueError:
        pass
    else:
        raise AssertionError("Approval should be blocked when regulatory evidence is invalid")


def _check_handoff_adapter() -> None:
    client = object()
    seen: Dict[str, Any] = {}

    def retrieve(actual_client, **kwargs):
        assert actual_client is client
        seen.update(kwargs)
        return {
            "industry": "banking",
            "jurisdiction": "US",
            "sources": [{"source_id": 1, "url": "https://example.org/reg"}],
            "evidence": [{"text": "Synthetic rule", "source_ids": [1]}],
        }

    def assess(actual_client, supplied):
        assert actual_client is client
        assert supplied["sources"][0]["source_id"] == 1
        return {
            "assessment": {
                "verdict": "potentially_feasible",
                "summary": "Synthetic advisory",
                "risks": [],
                "regulatory_compliance": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
                "legal_constraints": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
                "governance": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
                "operational_feasibility": {"status": "supported", "explanation": "Synthetic finding", "source_ids": [1]},
            }
        }

    packet = rr.review_adapter(
        demo_result(),
        retrieve_regulations_fn=retrieve,
        assess_insight_fn=assess,
        client=client,
        as_of="2026-10-14",
    )
    assert packet["evidence_namespace"] == "regulatory"
    assert packet["status"] == "assessed"
    assert packet["approved"] is False
    assert seen["as_of"] == "2026-10-14"


def run_validation_suite() -> Iterable[str]:
    """Run the offline validation checks and report the outcomes."""
    checks = [
        ("packet flow", _check_packet_flow),
        ("regulatory boundary", _check_regulatory_boundary),
        ("adapter handoff", _check_handoff_adapter),
    ]
    results: list[str] = []
    for name, fn in checks:
        try:
            fn()
            results.append(f"PASS: {name}")
        except Exception as exc:  # pragma: no cover - script-level verification
            results.append(f"FAIL: {name}: {type(exc).__name__}: {exc}")
    return results


if __name__ == "__main__":
    for line in run_validation_suite():
        print(line)

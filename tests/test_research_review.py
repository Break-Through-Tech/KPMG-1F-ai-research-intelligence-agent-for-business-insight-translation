import unittest
from copy import deepcopy
from src import research_review as rr
from src.regulatory_validation import validate_assessment_data
from src.research_pipeline import (
    content_fingerprint, require_current_review as require_pipeline_review, run_research,
)
from tests import research_fixtures as pipeline_fixture
from tests.research_review_fixtures import demo_result


def regulatory_data(verdict="potentially_feasible"):
    evidence = {"industry": "banking", "jurisdiction": "US",
                "sources": [{"source_id": 1, "url": "https://example.org/reg"}],
                "evidence": [{"text": "Synthetic rule", "source_ids": [1]}]}
    statuses = ["supported"] * 4
    if verdict == "conflicts":
        statuses[1] = "conflicts"
    elif verdict == "insufficient_evidence":
        statuses[2] = "unknown"
    assessment = {"verdict": verdict, "summary": "Synthetic advisory", "risks": []}
    for name, status in zip(("regulatory_compliance", "legal_constraints", "governance", "operational_feasibility"), statuses):
        assessment[name] = {"status": status, "explanation": "Synthetic finding", "source_ids": [] if status == "unknown" else [1]}
    return evidence, assessment


class ReviewTests(unittest.TestCase):
    def test_packet_is_pending_copy_and_resets_prior_approval(self):
        source = demo_result(); source["approved"] = True
        packet = rr.make_review_packet(source)
        self.assertIsNot(packet, source)
        self.assertFalse(packet["approved"])
        self.assertEqual(packet["human_review"]["status"], "pending")
        self.assertIn("review_fingerprint", packet)
        self.assertTrue(source["approved"])

    def test_named_approve_revise_reject_are_explicit(self):
        for decision, expected in (("approve", True), ("revise", False), ("reject", False)):
            with self.subTest(decision=decision):
                updated = rr.record_human_decision(rr.make_review_packet(demo_result()), reviewer="Reviewer", decision=decision, notes="Checked")
                self.assertEqual(updated["human_review"]["status"], decision)
                self.assertEqual(updated["human_review"]["reviewer"], "Reviewer")
                self.assertEqual(updated["approved"], expected)
                rr.require_current_review(updated)

    def test_pipeline_and_bridge_share_fingerprint_in_both_directions(self):
        draft = run_research({"query": "agents", "industry": "banking", "jurisdiction": "US"},
                             retrieve=pipeline_fixture.demo_retrieve, summarize_fn=pipeline_fixture.demo_summary)
        direct = rr.record_human_decision(draft, reviewer="Reviewer", decision="approve", notes="Verified")
        require_pipeline_review(direct)
        packet_decision = rr.record_human_decision(rr.make_review_packet(draft), reviewer="Reviewer", decision="approve", notes="Verified")
        require_pipeline_review(packet_decision)
        rr.require_current_review(direct)

    def test_legacy_saved_fingerprint_remains_valid_and_upgrades_on_decision(self):
        result = demo_result()
        # Version 1 used a fixed projection with null defaults for absent fields.
        result["review_fingerprint"] = content_fingerprint(result)
        rr.require_current_review(result)
        changed = deepcopy(result)
        changed["evidence"][0]["text"] = "edited"
        with self.assertRaises(ValueError):
            rr.require_current_review(changed)
        upgraded = rr.record_human_decision(
            result, reviewer="Reviewer", decision="revise")
        self.assertEqual(upgraded["review_fingerprint_version"], 2)
        rr.require_current_review(upgraded)

    def test_extra_review_context_is_fingerprinted(self):
        packet = rr.make_review_packet({**demo_result(), "review_context": {"as_of": "2026-10-14"}})
        packet["review_context"]["as_of"] = "2026-10-15"
        with self.assertRaisesRegex(ValueError, "changed"):
            rr.require_current_review(packet)

    def test_invalid_reviewer_and_decision_rejected(self):
        with self.assertRaises(ValueError): rr.record_human_decision(demo_result(), reviewer=" ", decision="approve")
        with self.assertRaises(ValueError): rr.record_human_decision(demo_result(), reviewer="A", decision="maybe")

    def test_edits_to_inputs_and_context_invalidate(self):
        for key, edit in (("evidence", lambda x: x[0].update(text="Edited")), ("request", lambda x: x.update(jurisdiction="CA")), ("summary", lambda x: x.update(status="insufficient_evidence")), ("business_insight", lambda x: x.update(status="insufficient_evidence")), ("provenance", lambda x: x.update(run="2"))):
            with self.subTest(key=key):
                packet = rr.make_review_packet(demo_result()); edit(packet[key])
                with self.assertRaisesRegex(ValueError, "changed"):
                    rr.require_current_review(packet)

    def test_invalid_regulatory_checkpoints_block_approval(self):
        evidence, supported = regulatory_data()
        invalid_cases = [
            {"assessment": {"verdict": None}, "regulatory_evidence": evidence},
            {"assessment": {**supported, "legal_constraints": {**supported["legal_constraints"], "source_ids": [99]}}, "regulatory_evidence": evidence},
            {"assessment": {**supported, "legal_constraints": {**supported["legal_constraints"], "status": "conflicts"}}, "regulatory_evidence": evidence},
        ]
        for checkpoint in invalid_cases:
            result = demo_result(); result["regulatory_checkpoint"] = checkpoint
            with self.subTest(checkpoint=checkpoint), self.assertRaisesRegex(ValueError, "Resolve"):
                rr.record_human_decision(rr.make_review_packet(result), reviewer="Reviewer", decision="approve")

    def test_unresolved_assessment_cannot_be_marked_currently_approved(self):
        result = rr.make_review_packet(demo_result())
        result["human_review"] = {"status": "approve", "reviewer": "Forged", "notes": ""}
        result["approved"] = True
        result["regulatory_checkpoint"] = {"assessment": {"verdict": None}}
        result["review_fingerprint"] = content_fingerprint(result)
        with self.assertRaisesRegex(ValueError, "blocks approval"):
            rr.require_current_review(result)

    def test_shared_checkpoint_validator_rejects_conflict_and_invalid_citation(self):
        evidence, assessment = regulatory_data()
        validate_assessment_data(assessment, evidence)
        for edit in ("conflict", "citation"):
            bad = deepcopy(assessment)
            if edit == "conflict":
                bad["legal_constraints"] = {**assessment["legal_constraints"], "status": "conflicts"}
            else:
                bad["legal_constraints"] = {**assessment["legal_constraints"], "source_ids": [99]}
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                validate_assessment_data(bad, evidence)

    def test_adapter_forwards_real_client_and_separates_evidence(self):
        seen = {}; evidence, assessment = regulatory_data(); client = object()
        def retrieve(actual_client, **kwargs):
            self.assertIs(actual_client, client); seen.update(kwargs); return evidence
        def assess(actual_client, supplied):
            self.assertIs(actual_client, client); self.assertEqual(supplied, evidence)
            return {"assessment": assessment, "approved": True}
        draft = demo_result()
        packet = rr.review_adapter(draft, retrieve_regulations_fn=retrieve, assess_insight_fn=assess,
                                   client=client, as_of="2026-10-14")
        self.assertEqual(seen["industry"], "banking"); self.assertEqual(seen["jurisdiction"], "US")
        self.assertEqual(seen["as_of"], "2026-10-14"); self.assertIn("Implication A", seen["insight"])
        self.assertEqual(packet["evidence_namespace"], "regulatory")
        self.assertEqual(draft["evidence"][0]["chunk_id"], "c1")
        self.assertEqual(packet["regulatory_evidence"]["sources"][0]["source_id"], 1)
        self.assertFalse(packet["approved"])
        self.assertEqual(packet["human_review"]["status"], "pending")

    def test_adapter_requires_client_and_complete_assessment(self):
        evidence, assessment = regulatory_data()
        retrieve = lambda client, **kwargs: evidence
        assess = lambda client, supplied: {"assessment": assessment}
        with self.assertRaisesRegex(ValueError, "client is required"):
            rr.review_adapter(demo_result(), retrieve_regulations_fn=retrieve, assess_insight_fn=assess)
        with self.assertRaisesRegex(ValueError, "both"):
            rr.review_adapter(demo_result(), retrieve_regulations_fn=retrieve)
        bad_assessment = {**assessment, "verdict": None}
        with self.assertRaisesRegex(ValueError, "verdict"):
            rr.review_adapter(demo_result(), retrieve_regulations_fn=retrieve,
                              assess_insight_fn=lambda c, e: {"assessment": bad_assessment}, client=object())

    def test_adapter_missing_context_stays_pending_and_skips_call(self):
        called = []; client = object()
        packet = rr.review_adapter({"request": {"query": "x"}}, retrieve_regulations_fn=lambda *a, **k: called.append("retrieve"),
                                   assess_insight_fn=lambda *a: called.append("assess"), client=client)
        self.assertEqual(packet["status"], "pending"); self.assertFalse(packet["approved"]); self.assertEqual(called, [])


if __name__ == "__main__": unittest.main()

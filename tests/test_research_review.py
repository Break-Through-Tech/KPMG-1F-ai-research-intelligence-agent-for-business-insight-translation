import unittest
from copy import deepcopy
from src import research_review as rr
from tests.research_review_fixtures import demo_result

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

    def test_invalid_reviewer_and_decision_rejected(self):
        with self.assertRaises(ValueError): rr.record_human_decision(demo_result(), reviewer=" ", decision="approve")
        with self.assertRaises(ValueError): rr.record_human_decision(demo_result(), reviewer="A", decision="maybe")

    def test_edits_to_all_review_inputs_and_context_invalidate(self):
        for key, edit in (("evidence", lambda x: x[0].update(text="Edited")), ("request", lambda x: x.update(jurisdiction="CA")), ("summary", lambda x: x.update(status="insufficient_evidence")), ("business_insight", lambda x: x.update(status="insufficient_evidence")), ("provenance", lambda x: x.update(run="2"))):
            with self.subTest(key=key):
                packet = rr.make_review_packet(demo_result()); edit(packet[key])
                with self.assertRaisesRegex(ValueError, "changed"):
                    rr.require_current_review(packet)

    def test_model_or_conflicting_regulatory_verdict_cannot_approve(self):
        for verdict in ("conflicts", "insufficient_evidence", "pending_human_review"):
            result = demo_result(); result["regulatory_checkpoint"] = {"assessment": {"verdict": verdict}}
            with self.subTest(verdict=verdict), self.assertRaisesRegex(ValueError, "Resolve"):
                rr.record_human_decision(rr.make_review_packet(result), reviewer="A", decision="approve")

    def test_adapter_uses_existing_functions_and_separate_namespace(self):
        seen = {}; evidence = {"industry": "banking", "jurisdiction": "US", "sources": [{"source_id": 1}], "evidence": [{"text": "Rule", "source_ids": [1]}]}
        def retrieve(client, **kwargs): seen.update(kwargs); return evidence
        def assess(client, supplied): return {"assessment": {"verdict": "potentially_feasible", "summary": "Advisory"}, "approved": False}
        draft = demo_result(); packet = rr.review_adapter(draft, retrieve_regulations_fn=retrieve, assess_insight_fn=assess, as_of="2026-10-14")
        self.assertEqual(seen["industry"], "banking"); self.assertEqual(seen["jurisdiction"], "US")
        self.assertEqual(seen["as_of"], "2026-10-14"); self.assertIn("Implication A", seen["insight"])
        self.assertEqual(packet["evidence_namespace"], "regulatory")
        self.assertEqual(draft["evidence"][0]["chunk_id"], "c1")
        self.assertEqual(packet["regulatory_evidence"]["sources"][0]["source_id"], 1)
        self.assertFalse(packet["approved"])
        self.assertEqual(packet["human_review"]["status"], "pending")

    def test_adapter_missing_context_stays_pending_and_skips_model(self):
        called = []
        packet = rr.review_adapter({"request": {"query": "x"}}, retrieve_regulations_fn=lambda *a, **k: called.append("retrieve"), assess_insight_fn=lambda *a: called.append("assess"))
        self.assertEqual(packet["status"], "pending"); self.assertFalse(packet["approved"]); self.assertEqual(called, [])

    def test_adapter_requires_both_callables_and_traceable_shape(self):
        with self.assertRaises(ValueError): rr.review_adapter(demo_result(), retrieve_regulations_fn=lambda *a, **k: {})
        with self.assertRaisesRegex(ValueError, "source-backed"):
            rr.review_adapter(demo_result(), retrieve_regulations_fn=lambda *a, **k: {}, assess_insight_fn=lambda *a: {})

if __name__ == "__main__": unittest.main()

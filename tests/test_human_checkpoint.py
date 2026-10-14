import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai import errors, types

from src import human_checkpoint as checkpoint


def grounded_response():
    return types.GenerateContentResponse(
        candidates=[types.Candidate(
            content=types.Content(parts=[types.Part(text="A reviewer is required.")]),
            grounding_metadata=types.GroundingMetadata(
                grounding_chunks=[types.GroundingChunk(web=types.GroundingChunkWeb(
                    uri="https://regulator.example/rule", title="Rule"
                ))],
                grounding_supports=[types.GroundingSupport(
                    segment=types.Segment(text="A reviewer is required."),
                    grounding_chunk_indices=[0],
                )],
            ),
        )]
    )


def assessment(status="supported", verdict="potentially_feasible"):
    finding = {"status": status, "explanation": "See source 1.", "source_ids": [1]}
    return {"verdict": verdict, "summary": "Advisory assessment.", "risks": [],
            **{key: dict(finding) for key in (
                "regulatory_compliance", "legal_constraints", "governance",
                "operational_feasibility")}}


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.client = SimpleNamespace(models=Mock())
        self.client.models.generate_content.return_value = grounded_response()
        self.context = dict(industry="finance", insight="Automate reporting",
                            jurisdiction="United States", as_of="2026-10-05")

    def retrieve(self):
        return checkpoint.retrieve_regulations(self.client, **self.context)

    def validate(self, data=None):
        self.client.models.generate_content.return_value = grounded_response()
        evidence = self.retrieve()
        self.client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(data if data is not None else assessment()))
        return checkpoint.assess_insight(self.client, evidence)

    def test_key_is_required_before_client_initialization(self):
        with patch.object(checkpoint, "load_dotenv"), patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "GOOGLE_API_KEY"):
                checkpoint.create_client()

    def test_client_receives_key_without_network_call(self):
        with patch.object(checkpoint, "load_dotenv"), \
             patch.dict("os.environ", {"GOOGLE_API_KEY": "test-only-key"}), \
             patch.object(checkpoint.genai, "Client") as factory:
            self.assertIs(checkpoint.create_client(), factory.return_value)
            factory.assert_called_once_with(api_key="test-only-key")

    def test_search_tool_and_traceable_evidence(self):
        evidence = self.retrieve()
        config = self.client.models.generate_content.call_args.kwargs["config"]
        self.assertIsNotNone(config.tools[0].google_search)
        self.assertEqual(evidence["sources"][0]["source_id"], 1)
        self.assertEqual(evidence["evidence"][0]["source_ids"], [1])
        self.assertIn("United States", self.client.models.generate_content.call_args.kwargs["contents"])

    def test_missing_jurisdiction_does_not_call_api(self):
        self.context["jurisdiction"] = " "
        with self.assertRaisesRegex(ValueError, "jurisdiction"):
            self.retrieve()
        self.client.models.generate_content.assert_not_called()

    def test_ungrounded_generation_is_rejected(self):
        self.client.models.generate_content.return_value = types.GenerateContentResponse(
            candidates=[types.Candidate(content=types.Content(
                parts=[types.Part(text="Unsupported assertion")]))])
        with self.assertRaisesRegex(ValueError, "No cited Search evidence"):
            self.retrieve()

    def test_source_without_grounded_segment_is_rejected(self):
        response = grounded_response()
        response.candidates[0].grounding_metadata.grounding_supports = []
        self.client.models.generate_content.return_value = response
        with self.assertRaisesRegex(ValueError, "No cited Search evidence"):
            self.retrieve()

    def test_invalid_source_index_is_rejected(self):
        response = grounded_response()
        response.candidates[0].grounding_metadata.grounding_supports[0].grounding_chunk_indices = [9]
        self.client.models.generate_content.return_value = response
        with self.assertRaisesRegex(ValueError, "no traceable evidence"):
            self.retrieve()

    def test_model_output_remains_pending_until_human_review(self):
        result = self.validate()
        self.assertFalse(result["approved"])
        self.assertEqual(result["human_review"]["status"], "pending")
        config = self.client.models.generate_content.call_args.kwargs["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertIsNone(config.tools)
        reviewed = checkpoint.record_human_review(
            result, decision="approve", reviewer="Test reviewer", notes="Verified sources and applicability.")
        self.assertTrue(reviewed["approved"])
        self.assertFalse(result["approved"])

    def test_unknown_or_conflicting_assessment_cannot_be_approved(self):
        for status, verdict in [("unknown", "insufficient_evidence"), ("conflicts", "conflicts")]:
            with self.subTest(status=status):
                result = self.validate(assessment(status, verdict))
                with self.assertRaisesRegex(ValueError, "Resolve"):
                    checkpoint.record_human_review(result, decision="approve", reviewer="Test", notes="Reviewed")
                for decision in ["revise", "reject"]:
                    self.assertFalse(checkpoint.record_human_review(
                        result, decision=decision, reviewer="Test", notes="Reviewed")["approved"])

    def test_invalid_or_missing_citations_are_rejected(self):
        for ids in [[42], []]:
            data = assessment()
            data["legal_constraints"]["source_ids"] = ids
            with self.subTest(ids=ids), self.assertRaisesRegex(ValueError, "source ID|without cited"):
                self.validate(data)

    def test_contradictory_verdict_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contradicts"):
            self.validate(assessment("unknown", "potentially_feasible"))

    def test_model_cannot_inject_approval_field(self):
        data = assessment()
        data["approved"] = True
        with self.assertRaises(ValueError):
            self.validate(data)

    def test_review_revalidates_edited_findings_and_citations(self):
        for edit in ["conflict", "citation", "schema"]:
            result = self.validate()
            if edit == "conflict":
                result["assessment"]["legal_constraints"]["status"] = "conflicts"
            elif edit == "citation":
                result["assessment"]["legal_constraints"]["source_ids"] = [99]
            else:
                del result["assessment"]["governance"]
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                checkpoint.record_human_review(
                    result, decision="approve", reviewer="Test", notes="Reviewed")

    def test_assessment_owns_evidence_snapshot(self):
        evidence = self.retrieve()
        self.client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(assessment()))
        result = checkpoint.assess_insight(self.client, evidence)
        evidence["sources"][0]["url"] = "https://changed.example"
        evidence["evidence"][0]["text"] = "Changed claim"
        self.assertEqual(result["sources"][0]["url"], "https://regulator.example/rule")
        self.assertEqual(result["evidence"][0]["text"], "A reviewer is required.")

    def test_context_guard_rejects_each_changed_input(self):
        evidence = self.retrieve()
        checkpoint.require_current_context(evidence, self.context)
        for key in self.context:
            context = {**self.context, key: "Changed"}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Inputs changed"):
                checkpoint.require_current_context(evidence, context)

    def test_review_requires_identity_notes_and_valid_decision(self):
        result = self.validate()
        for decision, reviewer, notes in [("approve", "", "Reviewed"),
                                          ("approve", "Test", ""), ("maybe", "Test", "Reviewed")]:
            with self.subTest(decision=decision, reviewer=reviewer, notes=notes), self.assertRaises(ValueError):
                checkpoint.record_human_review(result, decision=decision, reviewer=reviewer, notes=notes)

    def test_api_failure_is_actionable_and_has_no_approval(self):
        self.client.models.generate_content.side_effect = errors.ClientError(
            403, {"error": {"message": "Access denied", "status": "PERMISSION_DENIED"}})
        with self.assertRaisesRegex(RuntimeError, "HTTP 403.*No assessment was approved"):
            self.retrieve()

    def test_notebook_runs_top_to_bottom_offline_and_clears_stale_review(self):
        notebook = json.loads((Path(__file__).resolve().parents[1] /
                               "notebooks/Human_in_Loop_Checkpoint.ipynb").read_text())
        cells = ["".join(cell["source"]) for cell in notebook["cells"]
                 if cell["cell_type"] == "code"]
        self.client.models.generate_content.side_effect = [
            grounded_response(), SimpleNamespace(text=json.dumps(assessment()))]
        namespace = {}
        with patch.object(checkpoint, "create_client", return_value=self.client), \
             patch("builtins.input", side_effect=["approve", "Test reviewer", "Checked sources"]), \
             redirect_stdout(StringIO()):
            for index, source in enumerate(cells):
                exec(compile(source, f"notebook-cell-{index}", "exec"), namespace)
        self.assertTrue(namespace["reviewed_checkpoint"]["approved"])
        self.assertFalse(namespace["checkpoint"]["approved"])
        # Editing an input without rerunning its cell must block both later paths.
        namespace["insight_data"]["insight"] = "A different proposal"
        with self.assertRaisesRegex(ValueError, "Inputs changed"):
            exec(compile(cells[4], "review-stale-input", "exec"), namespace)
        self.assertIsNone(namespace["reviewed_checkpoint"])
        with self.assertRaisesRegex(ValueError, "Inputs changed"):
            exec(compile(cells[3], "assessment-stale-input", "exec"), namespace)
        self.assertIsNone(namespace["checkpoint"])
        self.client.models.generate_content.side_effect = errors.ClientError(
            403, {"error": {"message": "Denied"}})
        with self.assertRaises(RuntimeError):
            exec(compile(cells[2], "retrieval-rerun", "exec"), namespace)
        self.assertIsNone(namespace["checkpoint"])
        self.assertIsNone(namespace["reviewed_checkpoint"])


if __name__ == "__main__":
    unittest.main()

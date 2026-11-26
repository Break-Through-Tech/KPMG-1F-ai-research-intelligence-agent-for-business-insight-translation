"""Model-free evidence, shadow, trial, and application-envelope regressions."""
from copy import deepcopy
import gzip
from hashlib import sha256
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_trial import ARCHIVE, replay
from structured_trial import claim_digest, observe
from trial_fixtures import fresh_tables, record_for, trial_cases
from bound_fixtures import MEASURE, PIN, TABLES, load, read
from test_verify import SourceCells


class TrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents, cls.findings = load()
        cls.fresh = fresh_tables(cls.parents)
        cls.cases = list(trial_cases(cls.parents, cls.fresh))
        cls.results = replay()

    def test_shadow_preserves_ordinary_answers_and_never_displays_previews(self):
        stage = self.results["stage_2"]
        self.assertTrue(stage["passed"])
        self.assertEqual(len(stage["archives"]), 11)
        self.assertTrue(all(row["answer_preserved"] and row["previews"] == 0 for row in stage["archives"]))
        self.assertEqual(stage["archive_counts"], {"linked": 2, "review": 8})
        self.assertEqual(len(stage["controls"]), 8)
        self.assertTrue(all(row["passed"] and row["preview"] is None for row in stage["controls"]))

    def test_fresh_trial_shows_only_pending_canonical_comparisons(self):
        stage = self.results["stage_3"]
        self.assertEqual(stage["status"], "passed_offline")
        self.assertEqual(stage["outcomes"], {"linked": 3, "reject": 6, "review": 6})
        previews = [case["preview"] for case in stage["cases"] if case["preview"]]
        self.assertTrue(all(case["passed"] and case["answer_preserved"] for case in stage["cases"]))
        self.assertEqual(len(previews), 3)
        self.assertTrue(all(p["human_review"] == "pending" for p in previews))
        self.assertIn("86.2–89.8", previews[0]["text"])
        self.assertIn("15.2–36.6", previews[0]["text"])
        self.assertIn("-6.2272", previews[1]["text"])
        self.assertIn("-7.2174–-4.6767", previews[2]["text"])

    def test_archived_original_html_matches_trial_cell_ids_and_headers(self):
        tables = {(row["arxiv_id"], row["table_id"]): row for row in read(TABLES)["records"]}
        for name, finding in self.fresh.items():
            with self.subTest(finding=name):
                first = finding.citations[0]
                table = tables[first.paper, first.table_id]
                source = Path(table["source_file"])
                data = source.read_bytes()
                raw = gzip.decompress(data) if source.suffix == ".gz" else data
                self.assertIn(first.source_sha256, {
                    sha256(raw).hexdigest(), sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
                })
                expected = {ref.locator.selector: ref.source_text for ref in finding.citations}
                expected.update({ref.header_cell_id: ref.header_path[-1] for ref in finding.citations})
                parser = SourceCells(expected)
                parser.feed(raw.decode("utf-8"))
                observed = {sid: "".join(parts) for sid, parts in parser.values.items()}
                self.assertEqual(
                    {sid: "".join(text.split()) for sid, text in observed.items()},
                    {sid: "".join(text.split()) for sid, text in expected.items()},
                )

    def test_invalid_record_cannot_render_or_remove_existing_answer(self):
        _, _, envelope, valid = self.cases[0]
        variants = [
            valid | {"schema_version": True}, valid | {"text": "invented evidence"},
            valid | {"before": valid["before"] | {"lower": "NaN"}},
            valid | {"before": valid["before"] | {"locators": valid["before"]["locators"] * 2}},
        ]
        for invalid in variants:
            with self.subTest(record=invalid):
                before = claim_digest(envelope)
                observed = observe(envelope, {0: invalid}, self.parents, self.fresh, trial=True)
                self.assertEqual(observed["checks"][0]["status"], "review")
                self.assertEqual(observed["trial_comparisons"], [])
                self.assertEqual(claim_digest(observed["answer"]), before)

    def test_only_canonical_comparison_can_appear_in_trial_preview(self):
        _, _, original, record = self.cases[0]
        alternative = deepcopy(original)
        claim = alternative["result"]["summary"]["claims"][0]
        claim["text"] = "Unsupported wording about real-world incident rates."
        record = record | {"claim_sha256": claim_digest(claim)}
        result = observe(alternative, {0: record}, self.parents, self.fresh, trial=True)
        self.assertIn("real-world incident rates", result["answer"]["result"]["summary"]["claims"][0]["text"])
        preview, = result["trial_comparisons"]
        self.assertNotIn("incident rates", preview["text"])
        self.assertEqual(preview["human_review"], "pending")

    def test_legacy_link_cannot_enable_the_structured_trial(self):
        saved = read(ARCHIVE)["recorded"][0]
        envelope = {"result": {"summary": saved["summary"], "evidence": saved["evidence"],
                               "provenance": {"index": {"indexed_records_sha256": PIN}}}}
        result = observe(envelope, {}, self.parents, self.findings, trial=True)
        self.assertEqual(result["checks"][0]["status"], "linked")
        self.assertEqual(result["checks"][0]["path"], "legacy")
        self.assertEqual(result["trial_comparisons"], [])

    def test_actual_agentic_output_stays_sealed_with_scripted_replies(self):
        checkout = MEASURE.parent.parent
        sys.path.insert(0, str(checkout))
        sys.path.insert(0, str(checkout / "experiments/agentic"))
        from test_agentic import Provider, draft, plan, verdicts
        from agents import OrchestratorAgent
        from envelope import to_envelope
        from src.research_contracts import validate_result
        from src.research_pipeline import require_current_review

        old = read(ARCHIVE)["recorded"][0]["summary"]["claims"][0]
        claim = {key: old[key] for key in ("text", "kind", "support")}
        chunk = claim["support"][0]["chunk_id"]
        limitation = {"text": "The comparison concerns mathematical reasoning benchmarks.",
                      "support": [{"chunk_id": chunk, "quote": "On mathematical reasoning benchmarks"}]}
        fake = Provider(plan=[plan()], research=[draft(claim, limits=[limitation])],
                        verify=[verdicts(("supported", []))])
        agent = OrchestratorAgent(generate=fake, retrieve=lambda *_: [self.parents[chunk]], top_k=4)
        built = agent.run("What did the training study report for strategy selection?")
        self.assertEqual(built["status"], "ok")
        self.assertEqual(fake.calls, ["plan", "research", "verify"])
        envelope = to_envelope(built, top_k=4, provenance={"index": {"indexed_records_sha256": PIN}},
                               context_id="offline-trial")
        claim, = envelope["result"]["summary"]["claims"]
        record = record_for(claim, self.findings["cu"], ("35", "46"), ("68", "78"), "percent")
        original = claim_digest(envelope)
        for mode in (False, True):
            with self.subTest(trial=mode):
                observed = observe(envelope, {0: record}, self.parents, self.findings, trial=mode)
                self.assertEqual(observed["checks"][0]["status"], "linked")
                self.assertEqual(len(observed["trial_comparisons"]), int(mode))
                self.assertEqual(claim_digest(observed["answer"]), original)
                result = observed["answer"]["result"]
                validate_result(result)
                require_current_review(result)
                self.assertFalse(result["approved"])
        self.assertEqual(fake.calls, ["plan", "research", "verify"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

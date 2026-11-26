import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from diagnose import diagnose, read_saved, score_saved


def point(*anchors, draft=None, final=None):
    return {"anchors": [list(a) for a in anchors], "draft": draft, "final": final}


class TraceDiagnosticsTests(unittest.TestCase):
    def test_multi_source_requires_all_anchors_or_a_complete_alternative(self):
        points = {"comparison": point(("a-v1", "b-v2"), ("review-v1",))}
        for evidence, count in [(["a-v1", "b-v1"], 0), (["a-v1", "b-v2"], 1), (["review-v1"], 1)]:
            with self.subTest(evidence=evidence):
                result = diagnose(points, evidence, [], [], [], 0)
                self.assertEqual(result["evidence_coverage"], [count, 1])

    def test_factual_prose_omission_is_distinct_from_gate_hold(self):
        points = {"method": point(("a",)), "result": point(("b",), draft=0)}
        outcome = diagnose(points, ["a", "b"], ["a supported result"], [],
                           ["a supported result"], 0)
        self.assertTrue(outcome["false_abstention"])
        self.assertEqual(
            {k: v["stage"] for k, v in outcome["point_decisions"].items()},
            {"method": "draft_omission", "result": "held_by_gate"},
        )

    def test_numerical_claim_losing_publication_without_a_hold_is_unexplained(self):
        result = diagnose({"negative_interval": point(("row",), draft=0)}, ["row"],
                          ["-4 to -1"], [], [], 0)
        self.assertEqual(result["point_decisions"]["negative_interval"]["stage"],
                         "unexplained_publication_loss")

    def test_partial_evidence_abstention_and_execution_failure_are_separate(self):
        points = {"method": point(("a",)), "result": point(("b",))}
        partial = diagnose(points, ["a"], [], [], [], 0)
        error = diagnose(points, ["a", "b"], [], [], [], 0, execution_error=True)
        self.assertTrue(partial["partial_evidence_abstention"])
        self.assertFalse(partial["false_abstention"])
        self.assertFalse(error["abstained"])
        self.assertTrue(all(row["stage"] == "execution_error"
                            for row in error["point_decisions"].values()))

    def test_unreviewed_and_unsupported_publish_blocks_complete_score(self):
        points = {"one": point(("a",), draft=0, final=0),
                  "two": point(("a",), draft=0, final=0)}
        complete = diagnose(points, ["a"], ["correct"], ["supported"], [], 1)
        extra = diagnose(points, ["a"], ["correct"],
                         ["supported", "unsupported", "unreviewed"], [], 3)
        self.assertTrue(complete["complete"])
        self.assertFalse(extra["complete"])
        self.assertEqual(extra["unsupported_published"], 1)
        self.assertEqual(extra["unreviewed_published"], 1)
        self.assertEqual(extra["published_point_coverage"], [2, 2])

    def test_tampered_trace_is_refused(self):
        with TemporaryDirectory() as workdir:
            folder = Path(workdir)
            for name in ("result.json", "synthesis.response.json", "synthesis-evidence.json"):
                (folder / name).write_text(json.dumps({"fixture": True}), encoding="utf-8")
            names = ("result.json", "synthesis.response.json", "synthesis-evidence.json")
            hashes = [read_saved(folder / name)[1] for name in names]
            (folder / names[-1]).write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "artifacts changed"):
                score_saved(folder, {"sha256": hashes})

    @unittest.skipUnless(Path("data/processed/controlled-live-three-arm/accuraterag-C/result.json").is_file(),
                         "Saved development artifacts unavailable")
    def test_saved_development_traces(self):
        root = Path("data/processed/controlled-live-three-arm")
        labels = json.loads(Path(__file__).with_name("development-labels.json").read_text(encoding="utf-8"))
        results = {case: score_saved(root / case, reference) for case, reference in labels.items()}
        self.assertEqual(results["accuraterag-C"]["evidence_coverage"], [2, 2])
        self.assertEqual(results["accuraterag-C"]["point_decisions"]["raft_row"]["stage"], "held_by_gate")
        self.assertEqual(results["travelplanner-C"]["point_decisions"]["travel_setting"]["stage"],
                         "missing_delivered_evidence")
        self.assertEqual(results["travelplanner-C"]["point_decisions"]["comparison_caveat"]["stage"], "held_by_gate")
        self.assertEqual(sum(r["reviewed_published"] for r in results.values()), 7)


if __name__ == "__main__":
    unittest.main()

"""Model-free regressions for automatic source linkage."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage1_replay import ARCHIVE, replay
from source_links import bind, context_from_saved
from bound_fixtures import ABSTRACT, load, read


class StageOneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents, cls.findings = load()
        cls.saved = read(ARCHIVE)["recorded"][0]
        cls.claim = cls.saved["summary"]["claims"][0]
        cls.context = context_from_saved(cls.saved["evidence"], cls.parents)

    def test_the_two_archived_comparisons_link_to_exact_spans(self):
        result = replay()
        self.assertEqual(len(result["snapshots"]), 11)
        self.assertEqual(sum(row["claims"] for row in result["snapshots"]), 17)
        self.assertEqual(len(result["archive"]), 10)
        linked = [case for case in result["archive"] if case["status"] == "linked"]
        self.assertEqual(len(linked), 2)
        for case in linked:
            for role, text in (("before", "35–46%"), ("after", "68–78%")):
                with self.subTest(version=case["version"], role=role):
                    ref, = case["operands"][role]["source_links"]
                    start, end = ref["locator"]["selector"]
                    self.assertEqual(ref["locator"]["chunk_id"], ABSTRACT)
                    self.assertEqual(self.parents[ABSTRACT]["text"][start:end], text)
        self.assertTrue(all(case["status"] != "linked" for case in result["earlier_cases"]
                            if case["expected"] == "reject"))

    def test_matched_numbers_cannot_override_scope_or_add_a_second_claim(self):
        text = self.claim["text"]
        mutations = (
            text.replace("mathematical reasoning benchmarks", "French elementary tasks"),
            text.replace("strategy-selection accuracy", "preference accuracy"),
            text.replace("seven base models", "eight base models"),
            text.replace("improved", "did not improve"),
            text + " The model also prevents incidents in production.",
            text.replace("35", "³⁵"),
        )
        for altered in mutations:
            with self.subTest(claim=altered):
                result = bind(self.claim | {"text": altered}, self.context, self.findings)
                self.assertEqual(result.status, "review")
                self.assertIsNone(result.comparison)

    def test_swapped_regrouped_or_collapsed_ranges_fail_with_complete_scope(self):
        text = self.claim["text"]
        for values in ("68–78% to 35–46%", "35–78% to 46–68%", "35% to 78%"):
            with self.subTest(values=values):
                claim = self.claim | {"text": text.replace("35–46% to 68–78%", values)}
                result = bind(claim, self.context, self.findings)
                self.assertEqual(result.status, "reject")
                self.assertIsNone(result.comparison)

    def test_explicit_wrong_direction_is_rejected(self):
        claim = self.claim | {"text": self.claim["text"].replace("improved", "decreased")}
        self.assertIn("direction", bind(claim, self.context, self.findings).reason)
        self.assertEqual(bind(claim, self.context, self.findings).status, "reject")

    def test_unjustified_extra_decimal_precision_is_not_rounded_away(self):
        shifted = "35." + "0" * 45 + "1"
        text = self.claim["text"].replace("35–46%", shifted + "–46%")
        self.assertEqual(bind(self.claim | {"text": text}, self.context, self.findings).status, "reject")

    def test_quote_must_cover_both_operands_and_their_scope(self):
        original = self.claim["support"][0]["quote"]
        for partial in ("35–46%", "35–46% to 68–78%", original.replace("CU- DPO", "other method")):
            with self.subTest(quote=partial):
                cite = {"chunk_id": ABSTRACT, "quote": partial}
                self.assertEqual(bind(self.claim | {"support": [cite]}, self.context, self.findings).status,
                                 "review")

    def test_saved_passage_must_be_present_exact_and_unique(self):
        original = next(p for p in self.saved["evidence"] if p["chunk_id"] == ABSTRACT)
        for evidence in ([], [original | {"text": original["text"][:-1]}],
                         [original | {"arxiv_id": "2602.00931v1"}], [original, original]):
            with self.subTest(rows=len(evidence)):
                context = context_from_saved(evidence, self.parents)
                self.assertNotIn(ABSTRACT, context)
                self.assertEqual(bind(self.claim, context, self.findings).status, "review")

    def test_ambiguous_source_finding_is_withheld(self):
        candidates = self.findings | {"duplicate": self.findings["cu"]}
        self.assertEqual(bind(self.claim, self.context, candidates).status, "review")

    def test_labeled_table_claims_link_to_exact_cells_with_native_sign_and_scale(self):
        cases = {case["name"]: case for case in replay()["table_controls"]}
        for name, count in (("APIBench labeled ranges", 6), ("equivalent percent representation", 4),
                            ("signed fairness scores", 2)):
            with self.subTest(name=name):
                case = cases[name]
                self.assertEqual(case["status"], "linked")
                refs = [ref for role in case["operands"].values() for ref in role["source_links"]]
                self.assertEqual(len(refs), count)
                for ref in refs:
                    loc = ref["locator"]
                    row = self.parents[loc["chunk_id"]]
                    cell, = (cell for cell in row["table_cells"] if cell["source_id"] == loc["selector"])
                    self.assertEqual(ref["source_text"], cell["text"])
                    self.assertTrue(any(header["source_id"] == ref["header_cell_id"]
                                        for header in row["table_headers"]))
        for name in ("flipped sign", "swapped range endpoints", "percentage points in place of levels"):
            with self.subTest(attack=name):
                self.assertEqual(cases[name]["status"], "reject")

    def test_matching_table_values_without_row_and_header_proof_are_withheld(self):
        case = next(case for case in replay()["table_controls"] if case["name"] == "APIBench labeled ranges")
        claim = case["claim"]
        context = {cite["chunk_id"]: self.parents[cite["chunk_id"]] for cite in claim["support"]}
        partial = deepcopy(claim)
        partial["support"][0]["quote"] = "74.00"
        self.assertEqual(bind(partial, context, self.findings).status, "review")
        context.pop(claim["support"][0]["chunk_id"])
        self.assertEqual(bind(claim, context, self.findings).status, "review")


if __name__ == "__main__":
    unittest.main(verbosity=2)

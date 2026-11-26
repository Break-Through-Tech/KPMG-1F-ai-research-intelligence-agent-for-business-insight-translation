"""Regression checks for evidence-bound comparison and the frozen replay."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import gzip
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bound_fixtures import ABSTRACT, TABLES, load, read
from bound_replay import replay, replay_retained, with_values
from bound_verify import Locator, render, verify


class SourceCells(HTMLParser):
    """Read only explicitly named cells from the archived HTML."""
    def __init__(self, ids):
        super().__init__()
        self.ids = ids
        self.open_cell = None
        self.values = {}

    def handle_starttag(self, tag, attrs):
        cell = dict(attrs).get("id")
        if tag in {"td", "th"} and cell in self.ids:
            if cell in self.values:
                raise ValueError(f"duplicate source cell: {cell}")
            self.open_cell = cell
            self.values[cell] = []

    def handle_endtag(self, tag):
        if tag in {"td", "th"}:
            self.open_cell = None

    def handle_data(self, data):
        if self.open_cell:
            self.values[self.open_cell].append(data)


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = replay()
        cls.cases = cls.result["cases"]

    def test_frozen_ranges_reproduce_failures_and_preserve_valid_answer(self):
        cases = [row for row in self.cases if row["cohort"] == "frozen range"]
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(row["current"] == "accept" for row in cases))
        self.assertEqual(sum(row["candidate"] == "reject" for row in cases), 3)
        correct, = (row for row in cases if row["name"] == "correct paired ranges")
        self.assertEqual(correct["candidate"], "accept")
        self.assertIn("35–46%", correct["rendered"])
        self.assertIn("68–78%", correct["rendered"])

    def test_metric_and_setting_binding_boundary_replay(self):
        cases = {row["name"]: row for row in self.cases if row["cohort"] == "existing boundary draft"}
        for name in ("different setting", "metric assigned in a separate sentence"):
            with self.subTest(name=name):
                self.assertEqual(cases[name]["current"], "accept")
                self.assertEqual(cases[name]["previous_adapter"], "accept")
                self.assertEqual(cases[name]["candidate"], "reject")
                self.assertIsNone(cases[name]["rendered"])
        self.assertEqual(cases["equivalent range wording"]["candidate"], "accept")

    def test_all_twenty_nine_non_range_outcomes_stay_unchanged(self):
        controls = [row for row in self.cases if row["cohort"] == "frozen non-range"]
        self.assertEqual(len(controls), 29)
        self.assertTrue(all(row["current"] == row["candidate"] for row in controls))

    def test_source_checked_transfer_cases(self):
        cases = [row for row in self.cases if row["cohort"] == "transfer draft"]
        self.assertEqual(len(cases), 12)
        self.assertEqual(sum(row["candidate"] == "accept" for row in cases), 4)
        self.assertTrue(all(row["candidate"] == row["expected"] for row in cases))
        self.assertTrue(all(not row["reviewed"] for row in cases))
        self.assertEqual(self.result["gate_mismatches"], [])

    def test_two_retained_baseline_answers_are_preserved_with_matching_archive(self):
        results = replay_retained()
        self.assertEqual(results["counts"], {"accept": 2})
        self.assertEqual(results["gate_mismatches"], [])
        self.assertTrue(all(row["current"] == "review" for row in results["cases"]))


class BindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents, cls.findings = load()

    def test_altered_source_or_version_cannot_authorize_claim(self):
        finding = self.findings["cu"]
        record = self.parents[ABSTRACT]
        for key, value in (("arxiv_id", "2602.00931v1"),
                           ("source_url", "https://arxiv.org/html/2602.00931v1"),
                           ("text", record["text"].replace("35", "36")),
                           ("source_sha256", "0" * 64)):
            with self.subTest(key=key):
                context = {ABSTRACT: record | {key: value}}
                self.assertEqual(verify(finding, finding.comparison, context).status, "review")

    def test_missing_endpoint_row_and_altered_cells_are_withheld(self):
        finding = self.findings["accuraterag"]
        first, second = sorted({ref.locator.chunk_id for ref in finding.citations})
        partial = {first: self.parents[first]}
        self.assertEqual(verify(finding, finding.comparison, partial).status, "review")
        modified = deepcopy(self.parents[second])
        modified["table_cells"][3]["text"] = "99.99"
        partial[second] = modified
        self.assertIsNone(render(finding, finding.comparison, partial))

    def test_equal_number_with_different_cell_id_is_rejected(self):
        finding = self.findings["acdc"]
        claim = finding.comparison
        same_value_other_row = Locator("2604.00324v1_table_99d7ef000b02b530_3", "A1.T1.5.4.3")
        locators = frozenset({same_value_other_row}) | frozenset(
            loc for loc in claim.before.locators if loc.chunk_id.endswith("_1")
        )
        candidate = replace(claim, before=replace(claim.before, locators=locators))
        decision = verify(finding, candidate, self.parents)
        self.assertEqual(decision.status, "reject")
        self.assertIn("source locators", decision.reason)

    def test_no_free_text_ambiguous_or_incomplete_binding_is_certified(self):
        finding = self.findings["cu"]
        claim = finding.comparison
        partial = replace(claim, scope={"metric": claim.scope["metric"]})
        extra_scope = replace(claim, scope=claim.scope | {"direction": "decrease"})
        for candidate in (partial, extra_scope, "35–46% to 68–78%", replace(claim, scope=None)):
            with self.subTest(candidate=candidate):
                self.assertEqual(verify(finding, candidate, self.parents).status, "review")
        ambiguous = replace(finding, ambiguity="multiple candidate header paths")
        self.assertEqual(verify(ambiguous, claim, self.parents).status, "review")

    def test_real_table_cell_references_and_canonical_render(self):
        finding = self.findings["accuraterag"]
        self.assertEqual({ref.table_id for ref in finding.citations}, {"S2.T2"})
        self.assertEqual({ref.header_path for ref in finding.citations}, {("HF",), ("Torch Hub",), ("TF Hub",)})
        self.assertEqual(len({ref.locator for ref in finding.citations}), 6)
        result = render(finding, finding.comparison, self.parents)
        self.assertIn("RAFT with GPT-4 CoT range was 74.00–86.86", result)
        self.assertIn("AccurateRAG range was 68.36–88.71", result)

    def test_transfer_values_and_headers_match_original_archived_html(self):
        tables = {(t["arxiv_id"], t["table_id"]): t for t in read(TABLES)["records"]}
        for name in ("accuraterag", "agreemate"):
            with self.subTest(name=name):
                citations = self.findings[name].citations
                first = citations[0]
                source = Path(tables[first.paper, first.table_id]["source_file"])
                raw = gzip.decompress(source.read_bytes())
                self.assertIn(first.source_sha256, {
                    sha256(raw).hexdigest(), sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
                })
                cells = {item.locator.selector: item.source_text for item in citations}
                cells.update({item.header_cell_id: item.header_path[-1] for item in citations})
                parser = SourceCells(cells)
                parser.feed(raw.decode("utf-8"))
                observed = {cell: "".join(parts) for cell, parts in parser.values.items()}
                self.assertEqual(
                    {cell: "".join(text.split()) for cell, text in observed.items()},
                    {cell: "".join(text.split()) for cell, text in cells.items()},
                )

    def test_percent_conversion_does_not_round_incorrect_values_into_agreement(self):
        finding = self.findings["cu"]
        claim = finding.comparison
        perturbation = "35." + "0" * 45 + "1"
        changed = with_values(claim, (perturbation, "46"), ("68", "78"), "percent")
        self.assertEqual(verify(finding, changed, self.parents).status, "reject")
        bad_value = replace(claim.before.value, lower=Decimal("NaN"))
        malformed = replace(claim, before=replace(claim.before, value=bad_value))
        self.assertEqual(verify(finding, malformed, self.parents).status, "review")


if __name__ == "__main__":
    unittest.main(verbosity=2)

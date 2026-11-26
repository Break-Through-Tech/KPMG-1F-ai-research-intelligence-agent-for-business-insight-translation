"""Replay saved live prose and challenge its table bindings without generation."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from workflow_shadow import NumericalShadow, propose
from bound_fixtures import PARENTS, PIN, TABLES, digest, read, rows

ARCHIVE = HERE.parents[2] / "data/processed/numerical-shadow-codex"


class TableClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if digest(PARENTS) != PIN:
            raise ValueError("the demo-100 source index changed")
        cls.shadow = NumericalShadow({row["chunk_id"]: row for row in rows(PARENTS)}, read(TABLES)["records"])

    def case(self, name):
        return (read(ARCHIVE / name / "research-response.json")["claims"][0],
                read(ARCHIVE / name / "synthesis-evidence.json"))

    def check(self, claim, packet):
        observation, = self.shadow.check(self.shadow.produce([claim], packet), packet, [])
        return observation

    def test_saved_claims_bind_exact_versioned_cells(self):
        for name, expected in (
            ("agreemate", {"S6.T3.2.5.2", "S6.T3.2.5.3"}),
            ("training-counts", {"S3.T1.2.4.2", "S3.T1.2.3.2"}),
        ):
            with self.subTest(case=name):
                result = self.check(*self.case(name))
                self.assertEqual(result["status"], "accept", result)
                self.assertEqual({ref["locator"]["selector"] for ref in result["source_links"]}, expected)
                self.assertEqual(result["comparison_kind"], "categorical")
                self.assertEqual(set(result["proposal"]), {"scope", "left", "right"})
                labels = ({"With CoT", "Without CoT"} if name == "agreemate"
                          else {"SQL task conversations", "Entity (account) extraction tasks"})
                self.assertEqual({label.lower() for label in labels},
                                 {label.lower() for label in result["source_role_labels"].values()})
                claim, packet = self.case(name)
                first, second = ("-0.4385", "0.3021") if name == "agreemate" else ("11,000", "4,000")
                temporal = dict(claim, text=f"The measured value increased over time from {first} to {second}.")
                self.assertEqual(self.check(temporal, packet)["status"], "review")

    def range_case(self):
        recovery = read(HERE.parent / "accuraterag-table-retrieval/results.json")
        packet = [self.shadow.pinned_parents[key] for key in recovery["after_packet"]["ids"]]
        question = read(ARCHIVE / "run.json")["questions"]["accuraterag"]
        self.assertEqual(len(packet), 14)
        support = [dict(chunk_id=p["chunk_id"], quote=p["text"].rsplit("\n", 1)[-1]) for p in packet
                   if p["chunk_id"] in recovery["after_packet"]["matched"]]
        self.assertEqual(len(support), 2)
        text = ("With fine-tuned Llama-2-7B, AST-match score ranges across the three APIBench subsets "
                "were 68.36–88.71 for AccurateRAG and 74.00–86.86 for RAFT with GPT-4 CoT.")
        return question, packet, dict(text=text, kind="finding", support=support)

    def test_multicolumn_ranges_replay_at_fixed_budget(self):
        from test_workflow_shadow import run_case

        question, packet, claim = self.range_case()
        self.assertEqual(read(ARCHIVE / "accuraterag/research-response.json")["claims"], [])
        context = {p["chunk_id"]: p for p in packet}
        sources = {key: source for key, p in context.items() if (source := self.shadow.source_for(p))}
        self.assertEqual(propose(claim, context, sources).status, "review")
        observed, payload = run_case("accuraterag", packet, claim, self.shadow, question=question)
        control, control_payload = run_case("accuraterag", packet, claim, question=question)
        round_result, = observed.pop("numerical_shadow")
        result, = round_result["claims"]
        self.assertEqual(observed, control)
        self.assertEqual(payload, control_payload)
        self.assertEqual(payload["question"], question)
        self.assertEqual([p["chunk_id"] for p in payload["paper_passages"]], list(context))
        self.assertEqual(round_result["evidence"], payload["paper_passages"])
        self.assertEqual(result["status"], "accept", result)
        self.assertEqual((result["current_decision"], result["current_numeric"]), ("accepted", "uncertain"))
        self.assertEqual(observed["result"]["summary"]["status"], "ok")
        self.assertEqual(observed["result"]["summary"]["claims"][0]["text"], claim["text"])
        self.assertEqual(result["comparison_kind"], "categorical")
        self.assertEqual(result["proposal"]["scope"]["metric"], "AST-match")
        self.assertEqual(result["proposal"]["scope"]["configuration"], "llama-2-7b")
        self.assertEqual(result["proposal"]["scope"]["subsets"], "HF, Torch Hub, TF Hub")
        self.assertEqual(result["source_role_labels"], {"left": "raft with gpt-4 cot", "right": "accuraterag"})
        for role, row, endpoints in (("left", 4, ("74.00", "86.86")), ("right", 5, ("68.36", "88.71"))):
            operand = result["proposal"][role]
            self.assertEqual((operand["lower"], operand["upper"]), endpoints)
            self.assertEqual({loc["selector"] for loc in operand["locators"]},
                             {f"S2.T2.2.1.{row}.{i}" for i in (4, 5, 6)})
        self.assertEqual({ref["paper"] for ref in result["source_links"]}, {"2510.02243v2"})
        self.assertEqual({ref["header_path"][-1] for ref in result["source_links"]},
                         {"HF", "Torch Hub", "TF Hub"})
        self.assertEqual({ref["source_text"] for ref in result["source_links"]},
                         {"74.00", "84.95", "86.86", "68.36", "88.71", "88.03"})
        self.assertFalse(result["scope_provenance"]["in_synthesis_packet"])
        self.assertEqual(result["scope_provenance"]["chunk_id"], "2510.02243v2_c0015")

    def test_multicolumn_ranges_fail_closed(self):
        _, packet, claim = self.range_case()
        for original, changed, expected in (
            ("68.36–88.71 for AccurateRAG and 74.00–86.86 for RAFT with GPT-4 CoT",
             "74.00–86.86 for RAFT with GPT-4 CoT and 68.36–88.71 for AccurateRAG", "accept"),
            ("68.36–88.71 for AccurateRAG and 74.00–86.86 for RAFT with GPT-4 CoT",
             "74.00–86.86 for AccurateRAG and 68.36–88.71 for RAFT with GPT-4 CoT", "reject"),
            ("68.36–88.71", "45.71–88.71", "reject"),
            ("68.36–88.71", "88.71–68.36", "reject"),
            ("68.36–88.71", "68.36–88.03", "reject"),
            ("Llama-2-7B", "Llama-3-8B", "reject"),
            ("with GPT-4 CoT", "without GPT-4 CoT", "reject"),
            ("AST-match", "F1", "reject"),
            ("APIBench", "BioBench", "reject"),
            (" with GPT-4 CoT", "", "review"),
        ):
            with self.subTest(changed=changed):
                result = self.check(dict(claim, text=claim["text"].replace(original, changed)), packet)
                self.assertEqual(result["status"], expected, result)
        self.assertEqual(self.check(dict(claim, support=claim["support"][:1]), packet)["status"], "review")
        changed = deepcopy(packet)
        row = next(p for p in changed if p["chunk_id"] == claim["support"][0]["chunk_id"])
        row["table_cells"][5]["source_id"] = "foreign-cell"
        self.assertEqual(self.check(claim, changed)["status"], "review")
        tables = [dict(table, status="unverified") for table in self.shadow.tables.values()]
        shadow = NumericalShadow(self.shadow.pinned_parents, tables)
        result, = shadow.check(shadow.produce([claim], packet), packet, [])
        self.assertEqual(result["status"], "review")

    def test_same_table_can_bind_the_other_raft_configuration(self):
        _, packet, claim = self.range_case()
        original = claim["support"][0]["chunk_id"]
        recovery = read(HERE.parent / "accuraterag-table-retrieval/results.json")
        other = next(case for case in recovery["cases"] if case["name"] == "RAFT opposite condition")
        alternative_id, = set(other["expected"]) - {s["chunk_id"] for s in claim["support"]}
        alternative = self.shadow.pinned_parents[alternative_id]
        packet = [alternative if p["chunk_id"] == original else p for p in packet]
        support = [dict(chunk_id=alternative["chunk_id"], quote=alternative["text"].rsplit("\n", 1)[-1]),
                   claim["support"][1]]
        correct = dict(claim, support=support, text=claim["text"].replace(
            "74.00–86.86 for RAFT with GPT-4 CoT", "59.07–86.56 for RAFT without GPT-4 CoT"))
        result = self.check(correct, packet)
        self.assertEqual(result["status"], "accept", result)
        self.assertEqual(result["source_role_labels"]["left"], "raft without gpt-4 cot")
        mislabeled = dict(correct, text=correct["text"].replace("without GPT-4 CoT", "with GPT-4 CoT"))
        self.assertEqual(self.check(mislabeled, packet)["status"], "reject")

    def test_wrong_conditions_values_and_directions_are_rejected(self):
        claim, packet = self.case("agreemate")
        for original, wrong in (("-0.4385", "0.4385"), ("without CoT had", "with CoT had"),
                                ("-0.4385 with chain-of-thought (CoT) and 0.3021 without CoT",
                                 "0.3021 with chain-of-thought (CoT) and -0.4385 without CoT")):
            with self.subTest(wrong=wrong):
                self.assertEqual(self.check(dict(claim, text=claim["text"].replace(original, wrong)),
                                            packet)["status"], "reject")
        claim, packet = self.case("training-counts")
        self.assertEqual(self.check(dict(claim, text=claim["text"].replace("11,000", "12,000")),
                                    packet)["status"], "reject")

    def test_missing_or_changed_evidence_and_unsupported_scope_require_review(self):
        claim, packet = self.case("training-counts")
        self.assertEqual(self.check(dict(claim, support=claim["support"][:1]), packet)["status"], "review")
        partial = deepcopy(claim)
        partial["support"][1]["quote"] = "Count: 4,000"
        self.assertEqual(self.check(partial, packet)["status"], "review")
        self.assertEqual(self.check(dict(claim, text=claim["text"].replace("synthetic", "production")),
                                    packet)["status"], "review")
        packet = deepcopy(packet)
        row = next(p for p in packet if p["chunk_id"] == claim["support"][0]["chunk_id"])
        row["table_cells"][1]["source_id"] = "wrong-cell"
        self.assertEqual(self.check(claim, packet)["status"], "review")

    def test_same_initials_alone_do_not_support_an_expanded_label(self):
        claim, packet = self.case("agreemate")
        invented = dict(claim, text=claim["text"].replace("chain-of-thought", "cats-of-today"))
        self.assertEqual(self.check(invented, packet)["status"], "review")

    def test_actual_agent_keeps_diagnostics_separate_from_answer(self):
        from test_workflow_shadow import run_case

        for case in ("agreemate", "training-counts"):
            with self.subTest(case=case):
                claim, packet = self.case(case)
                observed, payload = run_case(case, packet, claim, self.shadow)
                original, control_payload = run_case(case, packet, claim)
                round_result, = observed.pop("numerical_shadow")
                decision, = round_result["claims"]
                self.assertEqual(decision["status"], "accept")
                self.assertEqual(round_result["evidence"], payload["paper_passages"])
                self.assertEqual(payload, control_payload)
                self.assertEqual(observed, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)

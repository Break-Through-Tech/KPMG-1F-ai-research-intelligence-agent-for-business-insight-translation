"""Test an offline budget, the application paths, blinding, and the decision gates."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from offline_harness import HERE, OfflineSession, STAGES, SEPARATOR, blind, exercise, read, summarize
from test_agentic import CORPUS, X, draft, plan, verdicts


class HarnessTests(unittest.TestCase):
    rules = read(HERE / "rules.json")

    def test_every_reserved_stage_and_restart_guard(self):
        calls = []
        prompts = {stage: prefix for prefix, stage in STAGES.items()}
        prompts["synthesis"] += SEPARATOR + json.dumps({"paper_passages": [{"chunk_id": "one"}]})
        schedule = [{"id": f"fixture{i}", "order": ["A", "B"]} for i in range(20)]
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "one-shot"
            session = OfflineSession(root, schedule, self.rules)
            with self.assertRaises(ValueError):
                session.cell("fixture0", "B", None)
            for qid, arm in session.sequence:
                cell = session.cell(qid, arm, lambda prompt, **_: calls.append(prompt))
                for stage in self.rules["stage_slots"][arm]:
                    cell(prompts[stage], response_schema={})
                with self.assertRaises(ValueError):
                    cell(prompts[stage], response_schema={})
            self.assertEqual(len(calls), 100)
            self.assertEqual(len(list(root.glob("*/*.attempt.json"))), 100)
            with self.assertRaises(ValueError):
                session.cell("fixture0", "A", None)
            with self.assertRaises(FileExistsError):
                OfflineSession(root, schedule, self.rules)
            with self.assertRaises(ValueError):
                OfflineSession(Path(tmp) / "other", schedule + [{"id": "extra", "order": ["A"]}], self.rules)

    def test_failed_stage_counts_and_retries_refused(self):
        def failed(*_args, **_kwargs):
            raise TimeoutError()

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "one-shot"
            cell = OfflineSession(root, [{"id": "fixture", "order": ["A"]}], self.rules).cell("fixture", "A", failed)
            prompt = "Synthesize an answer" + SEPARATOR + json.dumps({"paper_passages": [{"chunk_id": "one"}]})
            with self.assertRaises(TimeoutError):
                cell(prompt, response_schema={})
            with self.assertRaises(ValueError):
                cell(prompt, response_schema={})
            self.assertEqual(len(list(root.glob("*/*.attempt.json"))), 1)

    def test_oversized_packet_refused_before_adapter(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "one-shot"
            cell = OfflineSession(root, [{"id": "fixture", "order": ["A"]}], self.rules).cell("fixture", "A", None)
            prompt = "Synthesize an answer" + SEPARATOR + json.dumps(
                {"paper_passages": [{"chunk_id": str(i)} for i in range(9)]})
            with self.assertRaisesRegex(ValueError, "Invalid synthesis packet"):
                cell(prompt, response_schema={})
            self.assertFalse(list(root.glob("*/*.attempt.json")))

    def test_application_paths_and_blinding(self):
        def fake(prompt, **_):
            stage, = [stage for prefix, stage in STAGES.items() if prompt.startswith(prefix)]
            replies = {"plan": plan(), "synthesis": draft(X, limits=[]),
                       "verification": verdicts(("supported", [])),
                       "quality-review": dict(coverage="full", gap="", retained_claim_indices=[0], limitations=[],
                                              decisions=[dict(index=0, supported=True, relevant=True, reason="fixture")])}
            return json.dumps(replies[stage])

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "one-shot"
            session = OfflineSession(root, [{"id": "f", "order": ["A", "B"]}], self.rules)
            results = []
            for arm in "AB":
                ticket = session.cell("f", arm, fake)
                result = exercise("What accuracy did Model X reach?", arm,
                                  identity={"indexed_records_sha256": "a" * 64},
                                  retrieve=lambda *_: [CORPUS["A1"]], stage=ticket)
                self.assertEqual(result["result"]["summary"]["claims"][0]["text"], X["text"])
                self.assertEqual(ticket.used, self.rules["stage_slots"][arm])
                results.append(dict(id="f", arm=arm, answer=result))
            review, mapping = blind(results, "fixture-secret")
            self.assertEqual(set(mapping.values()), {("f", "A"), ("f", "B")})
            self.assertTrue(all("arm" not in x and "verification" not in x["claims"][0] for x in review))

    def test_decision_thresholds_and_missing_pairs(self):
        arm = dict(attempted=True, complete=False, unsupported=False, seconds=20, calls=2)
        pairs = [dict(id=str(i), category="fact" if i % 2 else "table", A=arm.copy(),
                      B=arm | {"complete": i < 3, "seconds": 40, "calls": 3}) for i in range(20)]
        self.assertTrue(summarize(pairs, self.rules)["default_eligible"])
        pairs[0]["B"]["unsupported"] = True
        self.assertFalse(summarize(pairs, self.rules)["default_eligible"])
        pairs[0]["B"]["attempted"] = False
        self.assertIn("inconclusive", summarize(pairs, self.rules))


if __name__ == "__main__":
    unittest.main()

"""Replay untouched live replies through the application publication path."""
from copy import deepcopy
import json
import unittest

from run import ARCHIVE, BUNDLE, OLD, ROOT, PIN, read, rows, agents, patch
from envelope import to_envelope
from test_agentic import Provider, draft, plan, verdicts

LIVE = ROOT / "data/processed/controlled-live-three-arm"


def replay(question, packet, saved_draft, review, saved_plan=None):
    provider = Provider(plan=[saved_plan or plan()], research=[saved_draft], verify=[review])
    with patch.object(agents, "MAX_EVIDENCE", len(packet)), patch.object(agents, "MAX_RETRIEVAL_ROUNDS", 1):
        result = agents.OrchestratorAgent(generate=provider, retrieve=lambda *_: deepcopy(packet), top_k=8,
                                          index_sha256=PIN, research_only=True).run(question)
    assert provider.calls == ["plan", "research", "verify"]
    prompt = next(prompt for role, prompt in provider.prompts if role == "research")
    assert json.loads(prompt.split("Return only JSON matching the supplied schema.\n", 1)[1])["paper_passages"] == packet
    return to_envelope(result, top_k=8, provenance={"index": {"indexed_records_sha256": PIN}},
                       context_id="publication-gate-replay")["result"]["summary"]


def saved(name):
    folder = LIVE / name
    meta = read(folder / "result.json")
    evidence = read(folder / "synthesis-evidence.json")
    # Tie the packet to the corresponding final historical envelope, not a rebuilt fixture.
    assert evidence == (meta["answer"]["result"])["evidence"]
    return (meta["question"], evidence,
            read(folder / "synthesis.response.json"), read(folder / "verification.response.json"),
            read(folder / "plan.response.json"))


class PublicationGateTests(unittest.TestCase):
    def test_both_original_accuraterag_ranges_publish(self):
        source = saved("accuraterag-C")
        final = replay(*source)
        self.assertEqual([c["text"] for c in final["claims"]], [c["text"] for c in source[2]["claims"]],
                         [(c["text"], c["verification"]["held_reason"]) for c in final["held_claims"]])

    def test_original_travelplanner_caveats_publish(self):
        for arm in ("B", "C"):
            with self.subTest(arm=arm):
                source = saved(f"travelplanner-{arm}")
                final = replay(*source)
                self.assertEqual([c["text"] for c in final["claims"]], [c["text"] for c in source[2]["claims"]])
                self.assertTrue(final["claims"][-1]["verification"]["needs_human_number_check"])

    def test_ambiguous_caveat_requires_supported_model_verdict(self):
        q, packet, original, review, saved_plan = saved("travelplanner-C")
        withheld = deepcopy(review)
        withheld["verdicts"][-1].update(verdict="unsupported", issues=["missing_support"])
        withheld.update(coverage="partial", missing_aspects=["comparison of metrics"])
        final = replay(q, packet, original, withheld, saved_plan)
        self.assertEqual(len(final["claims"]), 3)
        self.assertIn("verifier judged unsupported", final["held_claims"][0]["verification"]["held_reason"])

    def test_raft_claim_with_wrong_configuration_is_held(self):
        q, packet, original, review, saved_plan = saved("accuraterag-C")
        for old, new in (("and GPT-4 Chain-of-Thought", "without GPT-4 CoT"),
                         ("Llama-2-7B and GPT-4", "Llama-3-8B and GPT-4"),
                         ("and GPT-4", "and GPT-5")):
            with self.subTest(configuration=new):
                altered = deepcopy(original)
                target = altered["claims"][1]
                target["text"] = target["text"].replace(old, new)
                self.assertNotEqual(target, original["claims"][1])
                final = replay(q, packet, altered, review, saved_plan)
                self.assertEqual(len(final["claims"]), 1)
                self.assertEqual(final["held_claims"][0]["text"], target["text"])

    def test_cu_dpo_range_mutations_stay_unpublished(self):
        row = next(r for r in read(OLD / "saved-traces.json")["recorded"]
                   if r["version"] == "e5a8c4c460134444ad0b3e7da476fa44")
        parents = {p["chunk_id"]: p for p in rows(BUNDLE / "parents.jsonl")}
        packet = [parents[p["chunk_id"]] for p in row["evidence"]]
        claim, = row["summary"]["claims"]
        review = verdicts(("supported", []))
        for new in ("35–46% to 68–78%", "68–78% to 35–46%", "35–78% to 46–68%", "35% to 78%"):
            with self.subTest(range=new):
                candidate = dict(text=claim["text"].replace("35–46% to 68–78%", new),
                                 kind=claim["kind"], support=claim["support"])
                final = replay(row["question"], packet, draft(candidate, limits=[]), review)
                self.assertEqual(bool(final["claims"]), new == "35–46% to 68–78%")
                if not final["claims"]:
                    self.assertIn("range_binding_mismatch", final["held_claims"][0]["verification"]["held_reason"])

    def test_agreemate_valid_and_swapped_configurations(self):
        folder = ARCHIVE / "agreemate"
        question = read(folder / "result.json")["question"]
        packet = read(folder / "synthesis-evidence.json")
        original = read(folder / "research-response.json")
        review = read(ARCHIVE.parent / "numerical-shadow-agreemate-verification-replay/verify-response.json")
        self.assertEqual(len(replay(question, packet, original, review)["claims"]), 1)
        swapped = deepcopy(original)
        swapped["claims"][0]["text"] = swapped["claims"][0]["text"].replace(
            "-0.4385 with chain-of-thought (CoT) and 0.3021 without CoT",
            "0.3021 with chain-of-thought (CoT) and -0.4385 without CoT")
        self.assertNotEqual(swapped, original)
        self.assertFalse(replay(question, packet, swapped, review)["claims"])


if __name__ == "__main__":
    unittest.main()

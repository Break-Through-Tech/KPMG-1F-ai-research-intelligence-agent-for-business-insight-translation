import json
from pathlib import Path
import unittest

from agents import OrchestratorAgent, VERIFIER_PROMPT
from envelope import to_envelope
from handoff import EvidenceHandoffOrchestrator, SYNTHESIS_SEPARATOR
from test_agentic import Provider, claim, draft, passage, plan, verdicts

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = Path("D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100")
ARMS = (OrchestratorAgent, EvidenceHandoffOrchestrator)
QUERY = "Compare the two methodologies and report the available results and scope."


class ReplayProvider(Provider):
    """Scripted stage replies and verdicts; no provider or model is called."""

    def __init__(self, first, second, limitation, *, rejected=None, second_packet=True):
        self.first, self.second, self.rejected = first, second, rejected
        request = {"needed": True, "query": "Find the second method result", "reason": "One part is missing"}
        self.first_review = verdicts(("supported", []), coverage="partial", request=request)
        self.verification_payloads = []
        self.synthesis_packets = []
        limit = [limitation] if limitation else []
        first_draft = draft(*([first] if first else []), status="ok" if first else "insufficient_evidence", limits=limit)
        super().__init__(plan=[plan(("Find the first method result",))],
                         research=[first_draft, draft(second, limits=limit)] if second_packet else [first_draft])

    def __call__(self, prompt, response_schema=None):
        role = self.role(prompt)
        if role == "research":
            self.synthesis_packets.append(json.loads(prompt.split(SYNTHESIS_SEPARATOR, 1)[1]))
        if role == "verify":
            payload = json.loads(prompt[len(VERIFIER_PROMPT):])
            self.verification_payloads.append(payload)
            if len(self.verification_payloads) == 1:
                self.scripts["verify"] = [self.first_review]
            else:
                items = [("contradicted", ["contradiction"]) if c["text"] == self.rejected
                         else ("supported", []) for c in payload["claims"]]
                # An intentionally permissive scripted verdict also lets the
                # deterministic checks be exercised on numerical controls.
                supported = [c["text"] for c, v in zip(payload["claims"], items) if v[0] == "supported"]
                complete = all(c["text"] in supported for c in (self.first, self.second))
                self.scripts["verify"] = [verdicts(*items, coverage="full" if complete else "partial" if supported else "none")]
        return super().__call__(prompt, response_schema)


def replay(arm, first, second, findings, limit=None, *, question=QUERY, **kwargs):
    provider = ReplayProvider(first, second, limit, **kwargs)
    def retriever(query, cap):
        return [findings[1]] if "second method" in query and kwargs.get("second_packet", True) else [findings[0]]
    engine = arm(generate=provider, retrieve=retriever, top_k=8, index_sha256="fixture", max_calls=5,
                 **({"research_only": True} if arm is OrchestratorAgent else {}))
    result = engine.run(question)
    final = to_envelope(result, top_k=8, provenance={"index": {"indexed_records_sha256": "fixture"}},
                        context_id="handoff-replay")
    return result, final["result"]["summary"], provider


METHODS = (
    passage("method-one", "The first evaluation used annotated interviews in one city."),
    passage("method-two", "The second evaluation used blinded document review on the same question types."),
)
METHOD_CLAIMS = (claim(METHODS[0]["text"], "method-one", METHODS[0]["text"]),
                 claim(METHODS[1]["text"], "method-two", METHODS[1]["text"]))
LIMIT = {"text": "The first evaluation was limited to one city.",
         "support": [{"chunk_id": "method-one", "quote": METHODS[0]["text"]}]}


class ArchitectureTests(unittest.TestCase):
    def test_two_partial_drafts_methodology_and_scope(self):
        runs = [replay(arm, *METHOD_CLAIMS, METHODS, LIMIT) for arm in ARMS]
        self.assertEqual([summary["answer_scope"] for _, summary, _ in runs], ["partial", "full"])
        self.assertEqual([run["model_calls"]["used"] for run, _, _ in runs], [5, 5])
        self.assertEqual([summary["limitation_support"][0]["text"] for _, summary, _ in runs], [LIMIT["text"]] * 2)
        old, new = [provider for _, _, provider in runs]
        for a, b in zip(old.synthesis_packets, new.synthesis_packets, strict=True):
            self.assertEqual(a["paper_passages"], b["paper_passages"])
        handoff = new.synthesis_packets[1]["research_handoff"]
        self.assertEqual(handoff["question_parts"][0]["query"], "Find the first method result")
        self.assertEqual(handoff["prior_verified_claims"][0]["support"], METHOD_CLAIMS[0]["support"])
        self.assertEqual(handoff["prior_cited_limitations"][0]["support"], LIMIT["support"])

    def test_later_verdict_can_reject_earlier_claim(self):
        earlier = METHOD_CLAIMS[0]
        result, summary, _ = replay(ARMS[1], *METHOD_CLAIMS, METHODS, LIMIT, rejected=earlier["text"])
        self.assertEqual([c["text"] for c in summary["claims"]], [METHOD_CLAIMS[1]["text"]])
        self.assertEqual(summary["held_claims"][0]["text"], earlier["text"])
        self.assertEqual(result["selected_round"], 2)

    def test_no_new_evidence_needs_no_new_call(self):
        for arm in ARMS:
            result, summary, _ = replay(arm, *METHOD_CLAIMS, METHODS, LIMIT, second_packet=False)
            self.assertEqual(result["model_calls"]["used"], 3)
            self.assertEqual(summary["answer_scope"], "partial")

    def test_insufficient_evidence_does_not_publish(self):
        for arm in ARMS:
            result, summary, _ = replay(arm, None, METHOD_CLAIMS[1], METHODS, LIMIT, second_packet=False)
            self.assertEqual(result["model_calls"]["used"], 2)
            self.assertEqual(summary["status"], "insufficient_evidence")
            self.assertEqual(summary["claims"], [])
            self.assertEqual(summary["limitation_support"][0]["support"], LIMIT["support"])

    def test_swapped_numerical_values_stay_blocked(self):
        source = "Accuracy was 72% without caching and 81% with caching."
        packet = (METHODS[0], passage("conditions", source))
        wrong = claim("Accuracy was 81% without caching and 72% with caching.", "conditions", source)
        for arm in ARMS:
            result, summary, _ = replay(arm, METHOD_CLAIMS[0], wrong, packet, LIMIT)
            self.assertNotIn(wrong["text"], [c["text"] for c in summary["claims"]])
            verdict = result["verification"][-1]["verification"]["claims"][-1]
            self.assertEqual(verdict["decision"], "held")

    def test_fabricated_quote_remains_rejected(self):
        wrong = claim("The second method was perfect.", "method-two", "This quote was never in the passage.")
        result, summary, _ = replay(ARMS[1], METHOD_CLAIMS[0], wrong, METHODS, LIMIT)
        self.assertEqual(result["model_calls"]["used"], 4)
        self.assertEqual(summary["claims"], [])
        self.assertEqual(summary["abstention"], "synthesis_rejected")

    def test_fresh_gaia_table_transcription(self):
        # Independently checked against original GAIA v1 Table 3. These compact
        # row renderings are fixture excerpts, not outputs of the frozen index.
        rows = [
            ("gaia-valid-1", "Valid Level 1 questions: 75%.", "Valid Level 1 questions: 75%."),
            ("gaia-valid-3", "Valid Level 3 questions: 47%.", "Valid Level 3 questions: 47%."),
        ]
        packet = [{**passage(cid, row, "2311.12983v1"), "table_id": "GAIA Table 3"} for cid, row, _ in rows]
        claims = [claim(finding, cid, row) for cid, row, finding in rows]
        question = "In GAIA Table 3, what percentages of newly crafted Level 1 and Level 3 questions were valid?"
        runs = [replay(arm, *claims, packet, question=question) for arm in ARMS]
        self.assertEqual([summary["answer_scope"] for _, summary, _ in runs], ["partial", "full"])
        self.assertEqual([result["model_calls"]["used"] for result, _, _ in runs], [5, 5])
        self.assertEqual([c["text"] for c in runs[1][1]["claims"]], [c["text"] for c in claims])

    @unittest.skipUnless((BUNDLE / "parents.jsonl").is_file(), "Local versioned development corpus unavailable")
    def test_cited_table_rows_and_cross_paper_facts_survive_revision(self):
        case_ids = [
            ("2510.02243v2_table_a61b33c87b34e803_4", "2510.02243v2_table_a61b33c87b34e803_3"),
            ("2412.14470v2_c0000", "2402.01622v4_c0018"),
        ]
        wanted = {key for pair in case_ids for key in pair}
        with (BUNDLE / "parents.jsonl").open(encoding="utf-8-sig") as file:
            parents = {p["chunk_id"]: p for p in map(json.loads, file) if p["chunk_id"] in wanted}
        facts = [
            ("With fine-tuned Llama-2-7B, AccurateRAG scored 68.36 on Hugging Face.",
             "With fine-tuned Llama-2-7B and GPT-4 CoT, RAFT scored 74.00 on Hugging Face."),
            ("Agent-SafetyBench contains 2,000 test cases.",
             "In the two-stage mode, GPT-4-Turbo with ReAct achieved a 0.6% final pass rate."),
        ]
        for keys, texts in zip(case_ids, facts, strict=True):
            with self.subTest(sources=keys):
                packet = [parents[key] for key in keys]
                statements = []
                for p, text in zip(packet, texts, strict=True):
                    # Use original indexed tokens without fabricating excerpt content.
                    if p.get("table_id"):
                        quote = p["text"].splitlines()[-1]
                    elif p["arxiv_id"].startswith("2412."):
                        quote = p["text"].split("Agent-SafetyBench encompasses ", 1)[1].split(", evaluating", 1)[0]
                    else:
                        quote = next(line for line in p["text"].splitlines() if "final pass rate" in line)
                    statements.append(claim(text, p["chunk_id"], quote))
                runs = [replay(arm, *statements, packet) for arm in ARMS]
                self.assertEqual([summary["answer_scope"] for _, summary, _ in runs], ["partial", "full"])
                self.assertEqual([run["model_calls"]["used"] for run, _, _ in runs], [5, 5])
                result, summary, _ = runs[1]
                self.assertEqual([c["chunk_ids"] for c in summary["claims"]], [[key] for key in keys])
                self.assertEqual({p["chunk_id"]: p.get("table_id") for p in result["evidence"]},
                                 {p["chunk_id"]: p.get("table_id") for p in packet})


if __name__ == "__main__":
    unittest.main()

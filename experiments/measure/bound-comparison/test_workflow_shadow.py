"""Exercise the real agent path using ordinary scripted prose and pinned source passages."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT), str(ROOT / "experiments/agentic")]
from workflow_shadow import NumericalShadow
from bound_fixtures import MEASURE, PARENTS, PIN, TABLES, digest, read, rows
from agents import OrchestratorAgent
from envelope import to_envelope
from test_agentic import Provider, draft, plan, verdicts
from src.research_contracts import validate_result
from src.research_pipeline import require_current_review


def fixtures(parents):
    saved = read(MEASURE / "run-02/saved-traces.json")["recorded"]
    for i in (0, 4):
        yield f"saved-{i}", saved[i]["summary"]["claims"][0], "accept", True, None
    cu = saved[0]["summary"]["claims"][0]
    for name, old, new, expected in (
        ("reversed", "35–46% to 68–78%", "68–78% to 35–46%", "reject"),
        ("mixed", "35–46% to 68–78%", "35–78% to 46–68%", "reject"),
        ("collapsed", "35–46% to 68–78%", "35% to 78%", "reject"),
        ("metric", "strategy-selection accuracy", "preference accuracy", "review"),
        ("setting", "mathematical reasoning benchmarks", "clinical deployment", "review"),
        ("unit", "68–78%", "68–78 percentage points", "reject"),
    ):
        yield name, dict(cu, text=cu["text"].replace(old, new)), expected, False, None
    brief = dict(cu, support=[dict(cu["support"][0], quote="35–46% to 68–78%")])
    yield "short-quote", brief, "review", True, None
    table_specs = (
        ("fairness", "2412.18690v1", ["Fairness", "-0.4385", "0.3021"],
         "For Fairness (AgreeMate: Teaching LLMs to Haggle, Table 3: Comparison of Metrics for Combinations with and without COT), With COT was -0.4385 and Without COT was 0.3021."),
        ("auc", "2604.00324v1", ["IOI", "0.95", "0.50"],
         "For AUC (The Persistent Vulnerability of Aligned AI Systems, Table A.1 : AUC results for random baseline experiments, IOI), ACDC AUC was 95% and Random AUC was 50%."),
    )
    for name, paper, cells, text in table_specs:
        p = next(row for row in parents.values() if row["arxiv_id"] == paper
                 and [c["text"] for c in row.get("table_cells", ())] == cells)
        claim = dict(text=text, kind="finding", support=[dict(chunk_id=p["chunk_id"], quote=p["text"])])
        yield name, claim, "accept", True, None
        if name == "fairness":
            yield "sign", dict(claim, text=text.replace("-0.4385", "0.4385")), "reject", False, None
            altered = deepcopy(p)
            altered["table_cells"][1]["source_id"] = "foreign-cell"
            yield "wrong-cell", claim, "review", False, altered
            yield "wrong-version", claim, "review", False, dict(p, arxiv_id="2412.18690v2")
            yield "ambiguous-audit", claim, "review", True, None


def run_case(name, packet, claim, adapter=None, *, question=None):
    draft_claim = {key: claim[key] for key in ("text", "kind", "support")}
    limitation = dict(text="This comparison is scoped to the supplied source.", support=[
        dict(chunk_id=draft_claim["support"][0]["chunk_id"], quote=draft_claim["support"][0]["quote"][:60])
    ])
    fake = Provider(plan=[plan()], research=[draft(draft_claim, limits=[limitation])],
                    verify=[verdicts(("supported", []))])
    agent = OrchestratorAgent(generate=fake, retrieve=lambda *_: deepcopy(packet), index_sha256=PIN,
                              clock=lambda: 0, numerical_shadow=adapter)
    with patch("contracts.time.time", return_value=0):
        result = agent.run(question or f"What numerical comparison is supported for {packet[0]['title']}?")
    env = to_envelope(result, top_k=8, provenance={"index": {"indexed_records_sha256": PIN}},
                      context_id="offline")
    assert fake.calls == ["plan", "research", "verify"], (name, fake.calls, result["trace"])
    prompt = next(prompt for role, prompt in fake.prompts if role == "research")
    payload = json.loads(prompt.split("Return only JSON matching the supplied schema.\n", 1)[1])
    return env, payload


def replay():
    assert digest(PARENTS) == PIN
    parents = {p["chunk_id"]: p for p in rows(PARENTS)}
    audit = read(TABLES)["records"]
    results = []
    for name, claim, expected, valid, override in fixtures(parents):
        packet = [override or parents[key] for key in dict.fromkeys(s["chunk_id"] for s in claim["support"])]
        tables = audit if name != "ambiguous-audit" else [dict(row, status="unverified") for row in audit]
        env, payload = run_case(name, packet, claim, NumericalShadow(parents, tables))
        original, original_payload = run_case(name, packet, claim)
        observed, = env.pop("numerical_shadow")
        item, = observed["claims"]
        assert observed["evidence"] == payload["paper_passages"] and payload == original_payload, name
        assert env == original, name
        validate_result(env["result"])
        require_current_review(env["result"])
        assert item["status"] == expected, (name, item)
        results.append(dict(name=name, expected=expected, human_reviewed=False,
                            valid=valid, original_unchanged=True, question=payload["question"],
                            claim=claim["text"], observation=observed))
    statuses = Counter(r["observation"]["claims"][0]["status"] for r in results)
    return dict(provider_calls=0, outcomes=dict(statuses), cases=results)


class WorkflowTests(unittest.TestCase):
    def test_producer_through_real_agent_workflow(self):
        result = replay()
        self.assertEqual(len(result["cases"]), 15)
        self.assertEqual(result["outcomes"].get("accept"), 4)
        self.assertTrue(all(row["valid"] for row in result["cases"]
                            if row["observation"]["claims"][0]["status"] == "accept"))

    def test_shadow_failure_cannot_change_the_answer(self):
        class Broken:
            def produce(self, claims, passages):
                claims[0]["text"] = "This change must stay isolated."
                passages[0]["text"] = "This change must stay isolated."
                raise ValueError("fixture failure")

        parents = {p["chunk_id"]: p for p in rows(PARENTS)}
        _, claim, _, _, _ = next(fixtures(parents))
        packet = [parents[claim["support"][0]["chunk_id"]]]
        env, _ = run_case("broken", packet, claim, Broken())
        clean, _ = run_case("clean", packet, claim)
        self.assertEqual(env.pop("numerical_shadow")[0]["error"], "ValueError")
        self.assertEqual(env, clean)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--snapshot":
        result = replay()
        with (HERE / "workflow-shadow-results.json").open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
    else:
        unittest.main(verbosity=2)

"""Replay frozen desktop research paths with local retrieval and in-process replies only."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
MEASURE = HERE.parent
ROOT = MEASURE.parents[1]
sys.path[:0] = [str(ROOT), str(MEASURE), str(MEASURE / "bound-comparison"), str(ROOT / "experiments/agentic")]

import agents
from bound_fixtures import TABLES
from common import BUNDLE, ENCODER, PIN, RERANKER, digest, read, rows
from numeric_checks import ground_claim
from src.answer_quality import POLICY
from src.experimental.b2 import open_b2
from src.indexed_research import IndexedResearch
from test_agentic import plan, verdicts
from workflow_shadow import NumericalShadow

ARCHIVE = ROOT / "data/processed/numerical-shadow-codex"
AGREE_REVIEW = ARCHIVE.parent / "numerical-shadow-agreemate-verification-replay"
OLD = MEASURE / "run-02"
TOP_K = 8


def exact(parents, cid, text, quote=None):
    source = parents[cid]["text"]
    quote = quote or source.rsplit("\n", 1)[-1]
    assert quote in source
    return dict(kind="finding", text=text, support=[dict(chunk_id=cid, quote=quote)])


def archived_draft(folder):
    return read(folder / "research-response.json")["claims"]


def cases_for(parents, spec, recorded):
    previous = read(MEASURE / "accuraterag-table-retrieval/results.json")
    for name in ("agreemate", "accuraterag", "training-counts"):
        folder = ARCHIVE / name
        record = read(folder / "result.json")
        ids = [row["chunk_id"] for row in record["source_targets"]["rows"]]
        claims = archived_draft(folder)
        if not claims:
            text = ("With fine-tuned Llama-2-7B, AST-match score ranges across the three APIBench subsets "
                    "were 68.36–88.71 for AccurateRAG and 74.00–86.86 for RAFT with GPT-4 CoT.")
            claims = [dict(text=text, kind="finding", support=[exact(parents, cid, text)["support"][0] for cid in ids])]
        yield dict(id=name, question=record["question"], claims=claims, targets=[[cid] for cid in ids],
                   plan=read(folder / "plan-response.json"),
                   origin="saved real draft" if name != "accuraterag" else "source-checked scripted draft")
    cu = next(row for row in recorded if row["version"] == "e5a8c4c460134444ad0b3e7da476fa44")
    yield dict(id="CU-DPO", question=spec["Q3"]["text"], claims=cu["summary"]["claims"],
               targets=[p["source_chunks"] for p in spec["Q3"]["required_points"]], plan=plan(),
               origin="saved final Baseline claim, reused as draft")
    q2 = spec["Q2"]
    safety, travel = "2412.14470v2_c0000", "2402.01622v4_c0000"
    yield dict(id="TravelPlanner", question=q2["text"],
               targets=[p["source_chunks"] for p in q2["required_points"]],
               plan=plan(("How does Agent-SafetyBench evaluate LLM agents and what safety scores does it report?",
                          "How does TravelPlanner evaluate LLM agents and what success rates does it report?")),
               claims=[
                   exact(parents, safety, "Agent-SafetyBench covers 349 interaction environments and 2,000 test cases across 8 categories of safety risks and 10 failure modes. None of the 16 evaluated agents achieved a safety score above 60%.",
                         "Agent-SafetyBench encompasses" + parents[safety]["text"].split(
                             "Agent-SafetyBench encompasses", 1)[1].split("60%.", 1)[0] + "60%."),
                   exact(parents, travel, "TravelPlanner provides a travel-planning sandbox with tools accessing nearly four million records and includes 1,225 curated planning intents with reference plans. GPT-4 achieved a success rate of 0.6%.",
                         parents[travel]["text"].splitlines()[2] + "\n" + parents[travel]["text"].splitlines()[3]),
               ], origin="source-checked scripted draft; planned search also scripted")
    acdc = next(c for c in previous["cases"] if c["name"] == "ACDC tasks")
    acdc_claims = []
    for cid in acdc["expected"]:
        row, score, _ = (c["text"] for c in parents[cid]["table_cells"])
        acdc_claims.append(exact(parents, cid, f"The ACDC AUC for {row} was {score}."))
    yield dict(id="ACDC", question=acdc["question"], plan=plan(), claims=acdc_claims,
               targets=[[cid] for cid in acdc["expected"]], origin="source-checked scripted draft")
    atlas = next(c for c in read(OLD / "eligibility.json")["selected"] if c["id"] == "ev06")
    cid = "2602.00933v3_c0001"
    yield dict(id="MCP-Atlas", question=atlas["question"], plan=plan(),
               claims=[exact(parents, cid, "MCP-Atlas measures tool-use competency against production MCP servers and contains 1,000 tasks spanning 36 servers and 220 tools.",
                             parents[cid]["text"].split("220 tools.", 1)[0] + "220 tools.")],
               targets=[p["gold"] for p in atlas["parts"][:2]], origin="source-checked scripted draft")
    willow = next(row for row in recorded if row["version"] == "af4e65d7d7074dd98a1bdfd8f1617073")
    yield dict(id="Willow", question=willow["question"], plan=plan(), claims=[],
               targets=[[]], origin="scripted abstention; expected source not indexed")


class Reply:
    """Only emit archived or specified fixture claims whose exact citations are available."""
    supports_response_schema = True

    def __init__(self, case, saved_verdict=None):
        self.case, self.saved_verdict = case, saved_verdict
        self.calls, self.sent, self.packet, self.synthesis_bytes = [], [], [], 0
        self.verify_sha256 = None

    def __call__(self, prompt, *, response_schema=None):
        if prompt.startswith(agents.ORCHESTRATOR_PROMPT):
            self.calls.append("plan")
            response = self.case["plan"]
        elif prompt.startswith("Synthesize an answer"):
            self.calls.append("synthesis")
            self.synthesis_bytes = len(prompt.encode())
            self.packet = json.loads(prompt.split("Return only JSON matching the supplied schema.\n", 1)[1])["paper_passages"]
            ids = {p["chunk_id"] for p in self.packet}
            self.sent = [
                {key: deepcopy(c[key]) for key in ("kind", "text", "support")}
                for c in self.case["claims"] if all(ref["chunk_id"] in ids for ref in c["support"])
            ]
            limits = []
            if not self.sent:
                first = self.packet[0]
                limits = [dict(text="The supplied passages lack the anchored evidence required by this fixture.",
                               support=[dict(chunk_id=first["chunk_id"], quote=first["text"][:100].strip())])]
            response = dict(status="ok" if self.sent else "insufficient_evidence", claims=self.sent, limitations=limits)
        elif prompt.startswith(POLICY):
            self.calls.append("review")
            coverage = "full" if len(self.sent) == len(self.case["claims"]) else "partial"
            response = dict(coverage=coverage, gap="" if coverage == "full" else "Comparison is incomplete.",
                            retained_claim_indices=list(range(len(self.sent))), limitations=[],
                            decisions=[dict(index=i, supported=True, relevant=True, reason="Permissive fixture.")
                                       for i in range(len(self.sent))])
        elif prompt.startswith(agents.VERIFIER_PROMPT):
            self.calls.append("verify")
            self.verify_sha256 = sha256(prompt.encode()).hexdigest()
            coverage = "full" if len(self.sent) == len(self.case["claims"]) else "partial"
            response = self.saved_verdict or verdicts(*[("supported", []) for _ in self.sent], coverage=coverage)
        else:
            raise AssertionError("unexpected provider stage")
        return json.dumps(response)


def execute(arm, case, retrieve, identity, cap, *, shadow=None, saved_verdict=None):
    provider = Reply(case, saved_verdict)
    searches = []

    def traced(query, top_k):
        found = retrieve(query, top_k)
        searches.append(dict(query=query, ids=[p["chunk_id"] for p in found]))
        return found

    verification, observations = [], []
    if arm == "A":
        indexed = IndexedResearch(retrieve=traced, identity=identity, generate=provider,
                                  metadata={"provider": "offline fixture"}, index_path=str(BUNDLE),
                                  top_k=TOP_K, quality_check=True)
        env = indexed.execute(dict(query=case["question"], context_id=indexed.context_id, interpret_context=False))
        assert env["result"], env.get("error")
        summary = env["result"]["summary"]
        verification = summary.get("quality_review", {}).get("decisions", [])
    else:
        with patch.object(agents, "MAX_EVIDENCE", cap):
            result = agents.OrchestratorAgent(generate=provider, retrieve=traced, top_k=TOP_K, max_calls=5,
                                              index_sha256=PIN, research_only=True, numerical_shadow=shadow).run(case["question"])
        assert not result.get("error"), result.get("error")
        summary = result["summary"]
        verification = [row for rnd in result["verification"] for row in (rnd.get("verification") or {}).get("claims", [])]
        observations = [row for rnd in result.get("numerical_shadow", []) for row in rnd.get("claims", [])]
    ids = [p["chunk_id"] for p in provider.packet]
    assert provider.calls.count("synthesis") == 1 and 0 < len(ids) <= cap
    published = [c["text"] for c in summary["claims"]]
    assert set(published) <= {c["text"] for c in provider.sent}
    mutation = case.get("unsupported", False)
    return dict(arm=arm, evidence_cap=cap, context_ids=ids, synthesis_bytes=provider.synthesis_bytes,
                covered=[bool(set(group).intersection(ids)) for group in case["targets"]],
                searches=searches, provider_calls=0, replay_stages=provider.calls, drafts=provider.sent,
                verify_prompt_sha256=provider.verify_sha256,
                draft_correctness=("unsupported" if mutation else "source-supported") if provider.sent else "no draft",
                review_source="saved model verdict" if saved_verdict else "permissive fixture when called",
                verification=verification, shadow=observations, summary_status=summary["status"],
                published=published, unsupported_published=len(published) if mutation else 0,
                completion=("unsupported published" if mutation else
                            "full" if len(published) == len(case["claims"]) else "partial") if published
                           else ("appropriate abstention" if case["id"] == "Willow" else "no answer"))


def historical(recorded):
    records = []
    for name in ("agreemate", "accuraterag", "training-counts"):
        folder = ARCHIVE / name
        record = read(folder / "result.json")
        packet = read(folder / "synthesis-evidence.json")
        answer = record["answer"].get("result") or {}
        receipts = read(folder / "provider-attempts.json")
        records.append(dict(id=name, arm="historical Multi-Agent", origin="saved provider run", question=record["question"],
                            context_ids=[p["chunk_id"] for p in packet],
                            source_rows=record["source_targets"]["rows"], evidence=record["retrieval"],
                            provider_attempts=len(receipts), failures=sum(r["status"] == "failed" for r in receipts),
                            scenario=record["answer"]["scenario"], error=record["answer"].get("error"),
                            draft=read(folder / "research-response.json"), final=answer.get("summary")))
    for row in recorded:
        if row["version"] not in {"e5a8c4c460134444ad0b3e7da476fa44", "39b20c7e451a4d2b9c5579a6b3767d34",
                                  "af4e65d7d7074dd98a1bdfd8f1617073"}:
            continue
        assert row["index"] == PIN
        records.append(dict(id="CU-DPO" if row["summary"]["status"] == "ok" else "Willow", arm="retained Baseline",
                            origin="saved published answer", version=row["version"], question=row["question"],
                            context_ids=[p["chunk_id"] for p in row["evidence"]], final=row["summary"],
                            timings=row["timings"], provider_attempts=None))
    record = read(AGREE_REVIEW / "result.json")
    inputs = read(AGREE_REVIEW / "inputs.json")["sha256"]
    assert all(digest(ARCHIVE / "agreemate" / name) == checksum for name, checksum in inputs.items())
    return records, record


def verifier_controls(parents):
    snapshot = read(OLD / "verification.json")
    out = []
    for row in snapshot["cases"]:
        claim = row["claim"]
        ident = row["source_chunk_id"]
        evidence = parents.get(ident) or dict(chunk_id=ident, text=claim["support"][0]["quote"])
        old = row["results"]["numeric_strict_reject_only"]
        out.append(dict(name=row["name"], expected_supported=row["expected_supported"], reviewed=row["reviewed"],
                        previous={k: old[k] for k in ("status", "contradictions")},
                        current=ground_claim(claim, {ident: evidence})))
    return dict(historical_checker_sha256=snapshot["checker_sha256"],
                current_checker_sha256=digest(ROOT / "experiments/agentic/numeric_checks.py"), cases=out)


def run():
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer

    torch.set_num_threads(4)
    manifest = read(BUNDLE / "manifest.json")
    assert all(digest(BUNDLE / filename) == checksum for filename, checksum in manifest["artifact_sha256"].items())
    assert digest(BUNDLE / "parents.jsonl") == PIN
    parents = {p["chunk_id"]: p for p in rows(BUNDLE / "parents.jsonl")}
    encoder = SentenceTransformer(str(ENCODER), local_files_only=True, device="cpu")
    reranker = CrossEncoder(str(RERANKER), local_files_only=True, device="cpu")
    original, original_identity, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                              encoder=encoder, reranker=reranker)
    improved, improved_identity, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                              encoder=encoder, reranker=reranker, table_comparisons=True)
    assert original_identity()["indexed_records_sha256"] == improved_identity()["indexed_records_sha256"] == PIN
    spec = read(ROOT / "experiments/agentic/ab_questions.json")
    assert spec["corpus"]["parents_sha256"] == PIN
    recorded = read(OLD / "saved-traces.json")["recorded"]
    saved, agree_review = historical(recorded)
    shadow = NumericalShadow(parents, read(TABLES)["records"])
    cases = list(cases_for(parents, spec["questions"], recorded))
    from jsonschema import Draft202012Validator
    from src.research_chat import synthesis_schema
    for case in cases:
        claims = [{key: c[key] for key in ("kind", "text", "support")} for c in case["claims"]]
        ids = sorted({ref["chunk_id"] for claim in claims for ref in claim["support"]})
        Draft202012Validator(synthesis_schema(ids)).validate(
            dict(status="ok" if claims else "insufficient_evidence", claims=claims, limitations=[]))

    def cache(retrieve):
        data = {}

        def lookup(query, top_k):
            key = (query, top_k)
            if key not in data:
                data[key] = retrieve(query, top_k)
            return deepcopy(data[key])
        return lookup

    original, improved = cache(original), cache(improved)
    output = {}
    for case in cases:
        records = [execute("A", case, original, original_identity, 8)]
        for cap in (8, agents.MAX_EVIDENCE):
            records.append(execute("B", case, original, original_identity, cap))
            records.append(execute("C", case, improved, improved_identity, cap, shadow=shadow))
        output[case["id"]] = dict(question=case["question"], targets=case["targets"], draft_origin=case["origin"], arms=records)
        print(case["id"], [(r["arm"], len(r["context_ids"]), sum(r["covered"]), r["completion"]) for r in records], flush=True)
    agree = next(c for c in cases if c["id"] == "agreemate")
    archived_packet = read(ARCHIVE / "agreemate/synthesis-evidence.json")
    exact_replay = execute("C", agree | {"plan": plan()}, lambda *_: archived_packet,
                           improved_identity, agents.MAX_EVIDENCE, shadow=shadow,
                           saved_verdict=read(AGREE_REVIEW / "verify-response.json"))
    assert exact_replay["context_ids"] == [p["chunk_id"] for p in archived_packet]
    assert exact_replay["verify_prompt_sha256"] == agree_review["prompt_sha256"]
    cu = next(c for c in cases if c["id"] == "CU-DPO")
    challenges = {}
    for name, altered in (("reversed", "68–78% to 35–46%"), ("regrouped", "35–78% to 46–68%"),
                          ("collapsed", "35% to 78%")):
        claim, = deepcopy(cu["claims"])
        claim["text"] = claim["text"].replace("35–46% to 68–78%", altered)
        assert claim != cu["claims"][0]
        mutation = cu | {"claims": [claim], "unsupported": True}
        challenges[name] = [execute(arm, mutation, retr, identity, 8, shadow=adapter)
                            for arm, retr, identity, adapter in (("A", original, original_identity, None),
                                ("B", original, original_identity, None), ("C", improved, improved_identity, shadow))]
    assert all(m not in sys.modules for m in ("src.codex_generation", "capped_codex_ui", "call_ledger"))
    return dict(corpus=PIN, corpus_parents=len(parents), provider_calls=0,
                code_hashes={str(p.relative_to(ROOT)): digest(p) for p in (
                    ROOT / "experiments/agentic/agents.py", ROOT / "experiments/agentic/numeric_checks.py",
                    ROOT / "src/experimental/b2.py", ROOT / "src/experimental/balanced_retriever.py",
                    ROOT / "src/indexed_research.py", ROOT / "src/research_chat.py",
                    ROOT / "experiments/agentic/ab_questions.json", MEASURE / "bound-comparison/workflow_shadow.py",
                    MEASURE / "bound-comparison/range_claim_links.py")},
                native_agentic_cap=agents.MAX_EVIDENCE, historical=saved, historical_agree_verdict=agree_review,
                exact_agree_replay=exact_replay, cases=output, unsupported_challenges=challenges,
                verifier_controls=verifier_controls(parents))


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) == 2 else Path("results.json")
    if destination.name != str(destination) or destination.suffix != ".json" or (HERE / destination).exists():
        raise SystemExit("Supply a new JSON filename in the diagnostic directory.")
    results = run()
    with (HERE / destination).open("x", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

"""Offline B2 comparison at unchanged retrieval and synthesis budgets."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE.parent), str(ROOT / "experiments/agentic")]
from common import BUNDLE, ENCODER, RERANKER, PIN, digest, read, rows
from agents import MAX_EVIDENCE, OrchestratorAgent
from test_agentic import Provider
from src.experimental.b2 import open_b2

RUN = ROOT / "data/processed/numerical-shadow-codex"
TOP_K = 8


def packet_for(retrieve, saved, plan):
    # Force a locally scripted abstention. The outgoing synthesis prompt is the
    # measurement target; this reply provides no evidence of answer quality.
    draft = {"status": "insufficient_evidence", "claims": [], "limitations": []}
    provider = Provider(plan=[deepcopy(plan)], research=[draft])
    agent = OrchestratorAgent(generate=provider, retrieve=retrieve, top_k=TOP_K,
                              max_calls=3, index_sha256=PIN, research_only=True)
    agent.run(saved["question"])
    assert provider.calls == ["plan", "research"]
    _, synthesis = provider.prompts[1]
    payload = json.loads(synthesis.split("Return only JSON matching the supplied schema.\n", 1)[1])
    assert payload["question"] == saved["question"]
    return [p["chunk_id"] for p in payload["paper_passages"]]


def locate(parents, paper, table, labels):
    return {p["chunk_id"] for p in parents if p["arxiv_id"] == paper and p.get("table_id") == table
            and p["row_label"] in labels}


def run():
    from sentence_transformers import CrossEncoder, SentenceTransformer

    corpus = BUNDLE / "parents.jsonl"
    assert digest(corpus) == PIN
    parents = list(rows(corpus))
    encoder = SentenceTransformer(str(ENCODER), local_files_only=True, device="cpu")
    reranker = CrossEncoder(str(RERANKER), local_files_only=True, device="cpu")
    before, before_id, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                   encoder=encoder, reranker=reranker)
    after, after_id, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                 encoder=encoder, reranker=reranker, table_comparisons=True)
    assert before_id()["indexed_records_sha256"] == after_id()["indexed_records_sha256"] == PIN
    result = {"top_k": TOP_K, "synthesis_budget": MAX_EVIDENCE, "provider_calls": 0,
              "index": PIN, "cases": [], "identities": [before_id(), after_id()]}

    saved = read(RUN / "accuraterag/result.json")
    plan = read(RUN / "accuraterag/plan-response.json")
    expected = {row["chunk_id"] for row in saved["source_targets"]["rows"]}
    cases = [
        ("saved AccurateRAG", saved["question"], expected),
        ("ACDC tasks", "Compare the ACDC AUC scores for IOI and Docstring in the random baseline experiment.",
         locate(parents, "2604.00324v1", "A1.T1", {"IOI", "Docstring"})),
        ("Agent-SafetyBench models", "In Agent-SafetyBench, compare the M1 and M2 safety scores of Claude-3-Opus and Claude-3.5-Sonnet.",
         locate(parents, "2412.14470v2", "S4.T6", {"Claude-3-Opus", "Claude-3.5-Sonnet"})),
        ("RAFT opposite condition", saved["question"].replace("RAFT with GPT-4 CoT", "RAFT without GPT-4 CoT"),
         locate(parents, "2510.02243v2", "S2.T2", {
             "Our AccurateRAG [w/ FT Llama-2-7B ]", "RAFT [w/ FT Llama-2-7B ] w/o GPT-4 CoT"})),
    ]
    for control in ("agreemate", "training-counts"):
        prior = read(RUN / control / "result.json")
        cases.append((control, prior["question"], {row["chunk_id"] for row in prior["source_targets"]["rows"]}))

    cached = [{}, {}]

    def cached_retrieve(index, retrieve, query, top_k):
        key = (query, top_k)
        if key not in cached[index]:
            cached[index][key] = retrieve(query, top_k)
        return deepcopy(cached[index][key])

    for name, question, gold in cases:
        assert gold, name
        case = {"name": name, "question": question, "expected": sorted(gold)}
        for i, (key, retrieve) in enumerate((("before", before), ("after", after))):
            ids = [p["chunk_id"] for p in cached_retrieve(i, retrieve, question, TOP_K)]
            assert len(ids) == TOP_K
            case[key] = {"ids": ids, "matched": sorted(gold.intersection(ids))}
        result["cases"].append(case)
        print(name, len(case["before"]["matched"]), "->", len(case["after"]["matched"]), flush=True)

    for i, (key, retrieve) in enumerate((("before", before), ("after", after))):
        def route(query, top_k):
            return cached_retrieve(i, retrieve, query, top_k)
        packet = packet_for(route, saved, plan)
        assert len(packet) <= MAX_EVIDENCE
        result[key + "_packet"] = {"ids": packet, "matched": sorted(expected.intersection(packet))}
        result[key + "_searches"] = [{
            "query": item["query"],
            "ids": [p["chunk_id"] for p in route(item["query"], TOP_K)],
        } for item in saved["searches"]]
    assert result["before_packet"]["ids"] == [
        p["chunk_id"] for p in read(RUN / "accuraterag/synthesis-evidence.json")]
    assert all(new["ids"] == [hit["chunk_id"] for hit in old["hits"]]
               for new, old in zip(result["before_searches"], saved["searches"], strict=True))
    assert not result["before_packet"]["matched"]
    assert set(result["after_packet"]["matched"]) == expected
    assert all(len(case["after"]["matched"]) >= len(case["before"]["matched"]) for case in result["cases"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.name != str(args.output):
        parser.error("provide a new filename in the replay directory")
    result = run()
    if args.output:
        with (HERE / args.output).open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
    print(json.dumps({key: result[key] for key in ("before_packet", "after_packet")}, indent=2))

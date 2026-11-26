"""Isolated three-question OpenAI shadow evaluation. Default mode sends no requests."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(HERE.parent), str(ROOT), str(ROOT / "experiments/agentic")]
from attempts import AttemptBudget, PER_QUESTION, QUESTION_IDS, TOTAL, question_client
from workflow_shadow import NumericalShadow
from bound_fixtures import PARENTS, PIN, TABLES, digest, read, rows
from common import BUNDLE, ENCODER, RERANKER
from tables import canonical, local_source, plain
from agents import OrchestratorAgent
from envelope import to_envelope
from src.generation import create_generate
from src.generation_config import GenerationConfig

MODEL = "gpt-4.1"
TOP_K = 8
OUTPUT = ROOT / "data/processed/numerical-shadow-live"
QUESTIONS = dict(zip(QUESTION_IDS, (
    "In AgreeMate, what fairness scores did the researchers report with and without chain-of-thought, "
    "and which condition had the higher score?",
    "With fine-tuned Llama-2-7B, what score ranges did AccurateRAG and RAFT with GPT-4 CoT achieve "
    "across the three APIBench subsets?",
    "How many SQL task conversations and entity-extraction tasks were in the synthetic training dataset, "
    "and which group was larger?",
), strict=True))
TARGETS = {
    "agreemate": ("2412.18690v1", "S6.T3", ("Fairness",), ("With COT", "Without COT")),
    "accuraterag": ("2510.02243v2", "S2.T2",
                    ("Our AccurateRAG [w/ FT Llama-2-7B ]", "RAFT [w/ FT Llama-2-7B ] w/ GPT-4 CoT"),
                    ("HF", "Torch Hub", "TF Hub")),
    "training-counts": ("2506.23273v2", "S3.T1",
                        ("SQL Task Conversations", "Entity (Account) Extraction Tasks"), ("Count",)),
}
PROMPT_SEPARATOR = "Return only JSON matching the supplied schema.\n"


def source_targets(audit, parents):
    """Check answer anchors against original HTML. These never enter agent prompts."""
    results = {}
    for question, (paper, table_id, row_names, column_names) in TARGETS.items():
        table, = (t for t in audit if (t["arxiv_id"], t["table_id"]) == (paper, table_id))
        if table["status"] != "structural_agreement" or not table["audit_original_rows_identical"]:
            raise ValueError(f"source audit for {question} is incomplete")
        _, dom = local_source(paper, table["source_sha256"])
        if dom is None:
            raise ValueError(f"original source for {question} is unavailable")

        def checked_cell(meta):
            node = dom.find(id=meta["source_id"])
            if node is None or canonical(plain(node)) != canonical(meta["text"]):
                raise ValueError(f"original source differs for {question}")
            return {"id": meta["source_id"], "text": plain(node)}

        headers = []
        for column in column_names:
            header, = (h for h in table["headers"] if h["indexed"]["text"] == column and h["status"] == "agrees")
            headers.append(header["indexed"])
        source_rows = []
        for label in row_names:
            row, = (r for r in table["rows"] if r["cells"][0]["indexed"]["text"] == label)
            parent = parents[row["chunk_id"]]
            if (parent["arxiv_id"], parent["table_id"], parent["source_sha256"]) != (
                    paper, table_id, table["source_sha256"]):
                raise ValueError(f"index and source differ for {question}")
            items = [{
                "header": checked_cell(header),
                "value": checked_cell(row["cells"][header["column"]]["indexed"]),
            } for header in headers]
            for header in headers:
                col = header["column"]
                if (row["cells"][col]["status"] != "agrees"
                        or parent["table_cells"][col] != row["cells"][col]["indexed"]
                        or parent["table_headers"][col] != header):
                    raise ValueError(f"numeric cell binding differs for {question}")
            source_rows.append({"chunk_id": row["chunk_id"],
                                "label": checked_cell(row["cells"][0]["indexed"]), "cells": items})
        results[question] = {"paper": paper, "table_id": table_id, "source_url": table["source_url"],
                             "source_sha256": table["source_sha256"], "caption": table["caption"],
                             "rows": source_rows}
    return results


def retrieval_outcome(target, searches, packets):
    expected = {row["chunk_id"] for row in target["rows"]}
    retrieved = {hit["chunk_id"] for search in searches for hit in search.get("hits", ())}
    delivered = {row["chunk_id"] for packet in packets for row in packet}
    return {
        "target_rows_retrieved": sorted(expected & retrieved),
        "target_rows_never_retrieved": sorted(expected - retrieved),
        "target_rows_delivered": sorted(expected & delivered),
        "target_rows_dropped_before_synthesis": sorted((expected & retrieved) - delivered) if packets else [],
        "synthesis_invoked": bool(packets),
        "search_errors": [s["error"] for s in searches if "error" in s],
    }


def summarize_shadow(observations):
    checks = [{"round": entry["round"], **row} for entry in observations for row in entry.get("claims", ())]
    status = Counter(row["status"] for row in checks)
    return {
        "eligible_claims": len(checks),
        "structured_proposals": sum("proposal" in row for row in checks),
        "accepted": status["accept"], "referred": status["review"], "rejected": status["reject"],
        "disagreements": [
            {key: row.get(key) for key in ("round", "claim_index", "current_decision", "status", "reason")}
            for row in checks if (row["status"], row.get("current_decision")) in {
                ("accept", "held"), ("reject", "accepted"), ("review", "accepted")
            }
        ],
        "errors": [entry["error"] for entry in observations if "error" in entry],
    }


def run_question(qid, budget, config, retrieve, identity, shadow, target, *, inner=None):
    searches, packets = [], []

    def traced_retrieve(query, top_k):
        try:
            result = retrieve(query, top_k)
        except Exception as error:
            searches.append({"query": query, "error": type(error).__name__})
            raise
        searches.append({"query": query, "hits": [
            {key: p.get(key) for key in ("chunk_id", "arxiv_id", "table_id")} for p in result
        ]})
        return result

    with question_client(budget, qid, inner=inner) as client:
        generate, metadata = create_generate(config, http_client=client)

        def traced_generate(prompt, *, response_schema=None):
            if prompt.startswith("Synthesize an answer"):
                packets.append(json.loads(prompt.split(PROMPT_SEPARATOR, 1)[1])["paper_passages"])
            return generate(prompt, response_schema=response_schema)

        traced_generate.supports_response_schema = True
        agent = OrchestratorAgent(generate=traced_generate, retrieve=traced_retrieve, max_calls=PER_QUESTION,
                                  top_k=TOP_K, index_sha256=PIN, numerical_shadow=shadow, research_only=True)
        result = agent.run(QUESTIONS[qid])
    envelope = to_envelope(result, top_k=TOP_K, provenance={"index": identity, "generation": metadata},
                           context_id="isolated-numerical-shadow")
    return {
        "question": QUESTIONS[qid], "source_targets": target, "answer": envelope,
        "current_verification": result["verification"], "searches": searches, "synthesis_evidence": packets,
        "retrieval": retrieval_outcome(target, searches, packets),
        "shadow": summarize_shadow(result.get("numerical_shadow", [])),
        "attempts": [row for row in budget.records() if row["question"] == qid],
    }


def write(path, data):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def preflight():
    from src.experimental.b2 import open_b2
    if digest(PARENTS) != PIN:
        raise ValueError("the demo-100 parent digest differs")
    parents = {r["chunk_id"]: r for r in rows(PARENTS)}
    audit = read(TABLES)["records"]
    targets = source_targets(audit, parents)
    retrieve, identity_fn, _, _ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER)
    identity = identity_fn()
    if identity.get("indexed_records_sha256") != PIN:
        raise ValueError("B2 is using a different index")
    return retrieve, identity, NumericalShadow(parents, audit), targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="enable the single API run after approval")
    args = parser.parse_args()
    config = None
    if args.execute:
        config = GenerationConfig("openai", MODEL, os.getenv("OPENAI_API_KEY", "").strip())
        if OUTPUT.exists():
            parser.error("run directory already exists, including any interrupted run")
    retrieve, identity, shadow, targets = preflight()
    brief = {"index": PIN, "model": MODEL, "total_attempt_limit": TOTAL,
             "attempt_limit_per_question": PER_QUESTION, "questions": QUESTIONS}
    if not args.execute:
        print(json.dumps({**brief, "checked_original_sources": sorted(targets), "provider_attempts": 0}, indent=2))
        return
    OUTPUT.mkdir(parents=True, exist_ok=False)
    budget = AttemptBudget.create(OUTPUT / "attempts.sqlite3")
    write(OUTPUT / "run.json", brief)
    for qid in QUESTIONS:
        record = run_question(qid, budget, config, retrieve, identity, shadow, targets[qid])
        write(OUTPUT / f"{qid}.json", record)
        print(json.dumps({"question_id": qid, "scenario": record["answer"]["scenario"],
                          "retrieval": record["retrieval"], "shadow": record["shadow"],
                          "attempts": len(record["attempts"])}), flush=True)
    print(f"Saved {len(budget.records())} HTTP attempts in {OUTPUT}")


if __name__ == "__main__":
    main()

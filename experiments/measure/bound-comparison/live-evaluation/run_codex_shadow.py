"""One-shot three-question run using the existing subscription generator."""
import argparse
import json
import os
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_live import (
    OrchestratorAgent, PIN, PROMPT_SEPARATOR, QUESTIONS, ROOT, TOP_K, preflight,
    retrieval_outcome, summarize_shadow, to_envelope, write,
)
from src.codex_generation import create_codex_generate

OUTPUT = ROOT / "data/processed/numerical-shadow-codex"
MODEL = "gpt-6.1-sol"
BINARY = Path.home() / "AppData/Local/OpenAI/Codex/bin/f71a721e0e6193a9/codex.exe"
STAGES = {
    "plan": "You are the planning orchestrator",
    "research": "Synthesize an answer",
    "verify": "You are an independent evidence verifier",
}


class QuestionGenerator:
    supports_response_schema = True

    def __init__(self, folder, inner):
        self.folder, self.inner = folder, inner
        self.packets = []

    def __call__(self, prompt, *, response_schema=None):
        stage, = (stage for stage, prefix in STAGES.items() if prompt.startswith(prefix))
        # No other stage or repeated stage may start a CLI invocation.
        with (self.folder / f"{stage}-started.json").open("x", encoding="utf-8") as handle:
            json.dump({"stage": stage}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        if stage == "research":
            packet = json.loads(prompt.split(PROMPT_SEPARATOR, 1)[1])["paper_passages"]
            self.packets.append(packet)
            write(self.folder / "synthesis-evidence.json", packet)
        response = self.inner(prompt, response_schema=response_schema)
        write(self.folder / f"{stage}-response.json", json.loads(response))
        return response


def run_question(folder, qid, inner, metadata, retrieve, identity, shadow, target):
    folder.mkdir()
    searches = []
    generate = QuestionGenerator(folder, inner)

    def traced_retrieve(query, top_k):
        started = perf_counter()
        try:
            passages = retrieve(query, top_k)
        except Exception as error:
            searches.append({"query": query, "error": type(error).__name__})
            raise
        searches.append({"query": query, "seconds": round(perf_counter() - started, 3),
                         "hits": [{field: p.get(field) for field in ("chunk_id", "arxiv_id", "table_id")}
                                  for p in passages]})
        return passages

    agent = OrchestratorAgent(generate=generate, retrieve=traced_retrieve, max_calls=len(STAGES),
                              top_k=TOP_K, index_sha256=PIN, numerical_shadow=shadow, research_only=True)
    result = agent.run(QUESTIONS[qid])
    envelope = to_envelope(result, top_k=TOP_K, provenance={"index": identity, "generation": metadata},
                           context_id="isolated-codex-numerical-shadow")
    return {
        "question": QUESTIONS[qid], "source_targets": target, "answer": envelope,
        "current_verification": result["verification"], "searches": searches,
        "retrieval": retrieval_outcome(target, searches, generate.packets),
        "shadow": summarize_shadow(result.get("numerical_shadow", [])),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="allow the one authorized subscription run")
    args = parser.parse_args()
    if args.execute and OUTPUT.exists():
        parser.error("the one-shot run directory already exists")
    receipts = []
    inner, metadata = create_codex_generate(model=MODEL, binary=BINARY, effort="low", timeout=300,
                                            receipts=receipts)
    retrieve, identity, shadow, targets = preflight()
    if not args.execute:
        print(json.dumps({"generation": metadata, "index": PIN, "source_checks": sorted(targets),
                          "provider_calls": len(receipts)}, indent=2))
        return

    OUTPUT.mkdir(parents=True)
    write(OUTPUT / "run.json", {"questions": QUESTIONS, "generation": metadata, "index": PIN,
                               "question_attempts": 1, "maximum_cli_invocations_per_question": len(STAGES)})
    for qid, question in QUESTIONS.items():
        start = len(receipts)
        folder = OUTPUT / qid
        print(f"Starting {qid}: {question}", flush=True)
        try:
            record = run_question(folder, qid, inner, metadata, retrieve, identity, shadow, targets[qid])
            write(folder / "result.json", record)
            print(json.dumps({"question_id": qid, "scenario": record["answer"]["scenario"],
                              "retrieval": record["retrieval"], "shadow": record["shadow"]}), flush=True)
        finally:
            write(folder / "provider-attempts.json", receipts[start:])
            print(f"{qid}: {len(receipts) - start} CLI invocations", flush=True)


if __name__ == "__main__":
    main()

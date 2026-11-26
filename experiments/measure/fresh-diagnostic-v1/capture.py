"""Capture the existing research path. Import-only until a live run is approved."""
import json
import os
from pathlib import Path
from time import perf_counter

from prepare import ROOT
import sys

sys.path.insert(0, str(ROOT / "experiments/agentic"))
from agents import OrchestratorAgent, ORCHESTRATOR_PROMPT, VERIFIER_PROMPT
from envelope import to_envelope

STAGES = ("plan", "synthesis-1", "verification-1", "synthesis-2", "verification-2")
SEPARATOR = "Return only JSON matching the supplied schema.\n"


def write(path, data):
    with path.open("x", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


class CaptureError(RuntimeError):
    pass


class Capture:
    supports_response_schema = True

    def __init__(self, directory, generate):
        directory.mkdir()  # reserve this question once, including a crash
        self.directory, self.generate = directory, generate
        self.used, self.failed, self.violation = [], False, False

    def refuse(self):
        self.violation = True
        raise CaptureError("Unexpected stage or exhausted diagnostic budget")

    def __call__(self, prompt, *, response_schema=None):
        if self.failed or len(self.used) == len(STAGES) or response_schema is None:
            self.refuse()
        stage = STAGES[len(self.used)]
        prefix = {"plan": ORCHESTRATOR_PROMPT, "synthesis": "Synthesize an answer",
                  "verification": VERIFIER_PROMPT}[stage.split("-")[0]]
        if not prompt.startswith(prefix):
            self.refuse()
        if stage.startswith("synthesis"):
            packet = json.loads(prompt.split(SEPARATOR, 1)[1])["paper_passages"]
            if not 1 <= len(packet) <= 14 or len({p["chunk_id"] for p in packet}) != len(packet):
                self.refuse()
            write(self.directory / f"{stage}.evidence.json", packet)
        write(self.directory / f"{stage}.attempt.json", {"stage": stage})
        self.used.append(stage)
        started = perf_counter()
        try:
            raw = self.generate(prompt, response_schema=response_schema)
        except Exception as exc:
            self.failed = True
            write(self.directory / f"{stage}.error.json",
                  {"category": type(exc).__name__, "seconds": perf_counter() - started})
            raise
        write(self.directory / f"{stage}.reply.json",
              {"provider_text": raw, "seconds": perf_counter() - started})
        return raw


def run_question(parent, question, retrieve, generate, identity, receipts):
    """Question input is only its ID and text. References stay outside this function."""
    directory = parent / question["id"]
    provider = Capture(directory, generate)
    before = len(receipts)
    expected_identity = identity()
    searches = []

    def observed(query, top_k):
        if top_k != 8 or identity() != expected_identity:
            provider.refuse()
        start = perf_counter()
        try:
            found = retrieve(query, top_k)
            if len(found) > 8:
                provider.refuse()
        except Exception as exc:
            searches.append({"query": query, "seconds": perf_counter() - start,
                             "error": type(exc).__name__})
            raise
        searches.append({"query": query, "seconds": perf_counter() - start,
                         "chunk_ids": [p["chunk_id"] for p in found]})
        return found

    started = perf_counter()
    row = {"id": question["id"], "question": question["question"], "searches": searches}
    try:
        agent = OrchestratorAgent(generate=provider, retrieve=observed, top_k=8,
                                  max_calls=5, research_only=True,
                                  index_sha256=expected_identity["indexed_records_sha256"])
        result = agent.run(question["question"])
        write(directory / "agentic.json", result)
        row["answer"] = to_envelope(result, top_k=8, provenance={"index": expected_identity},
                                    context_id="fresh-diagnostic-v1")
    except Exception as exc:
        row["path_error"] = type(exc).__name__
    row.update(seconds=perf_counter() - started, attempts=provider.used,
               receipts=receipts[before:], integrity_violation=provider.violation)
    write(directory / "result.json", row)
    return row

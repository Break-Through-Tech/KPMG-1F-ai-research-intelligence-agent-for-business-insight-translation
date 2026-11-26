"""Model-free application replay, durable stage control, and scoring helpers."""
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from statistics import median
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments/agentic")]
import agents
from envelope import to_envelope
from src.answer_quality import POLICY
from src.indexed_research import IndexedResearch

STAGES = {agents.ORCHESTRATOR_PROMPT: "plan", "Synthesize an answer": "synthesis",
          POLICY: "quality-review", agents.VERIFIER_PROMPT: "verification"}
SEPARATOR = "Return only JSON matching the supplied schema.\n"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())


def verify_seal():
    seal = read(HERE / "seal.json")
    for name, checksum in seal["files"].items():
        if sha256((HERE / name).read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Sealed input changed: {name}")
    snapshot_file = HERE.parent / "generalization-preselection-snapshot.json"
    if sha256(snapshot_file.read_bytes()).hexdigest() != seal["preselection_snapshot"]:
        raise ValueError("Preselection manifest changed")
    snapshot = read(snapshot_file)
    for name, checksum in snapshot["runtime_sha256"].items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Frozen runtime changed: {name}")
    for name, checksum in snapshot["corpus"]["artifact_sha256"].items():
        with (Path(snapshot["corpus"]["path"]) / name).open("rb") as f:
            if __import__("hashlib").file_digest(f, "sha256").hexdigest() != checksum:
                raise ValueError(f"Corpus artifact changed: {name}")
    for asset, checksum in read(HERE / "execution-assets.json")["sha256"].items():
        with Path(asset).open("rb") as f:
            if __import__("hashlib").file_digest(f, "sha256").hexdigest() != checksum:
                raise ValueError(f"Execution asset changed: {Path(asset).name}")
    return seal


class OfflineSession:
    """A new root and distinct cells are mandatory. Restart cannot reuse them."""
    def __init__(self, root, schedule, rules):
        self.root, self.rules = root, rules
        self.sequence = [(row["id"], arm) for row in schedule for arm in row["order"]]
        allowance = sum(len(rules["stage_slots"][arm]) for _, arm in self.sequence)
        if len(set(self.sequence)) != len(self.sequence) or allowance > rules["max_application_invocations"]:
            raise ValueError("Schedule exceeds its authorization")
        root.mkdir(exist_ok=False)
        write(root / "schedule.json", schedule)
        self.position = 0

    def cell(self, qid, arm, fake):
        if self.position >= len(self.sequence) or self.sequence[self.position] != (qid, arm):
            raise ValueError("Out of order or unscheduled run")
        slot = self.root / f"{qid}-{arm}"
        slot.mkdir(exist_ok=False)
        self.position += 1
        return FixtureStages(slot, self.rules["stage_slots"][arm], self.rules["synthesis_passages"], fake)


class FixtureStages:
    supports_response_schema = True

    def __init__(self, slot, allowed, cap, fake):
        self.slot, self.allowed, self.cap, self.fake = slot, allowed, cap, fake
        self.used, self.failed, self.violation = [], False, None

    def refuse(self, message):
        self.violation = message
        raise ValueError(message)

    def __call__(self, prompt, *, response_schema=None):
        candidates = [stage for prefix, stage in STAGES.items() if prompt.startswith(prefix)]
        index = len(self.used)
        if (self.failed or response_schema is None or len(candidates) != 1 or index >= len(self.allowed)
                or candidates[0] != self.allowed[index]):
            self.refuse("Overspend, unexpected stage, or retry")
        stage, = candidates
        if stage == "synthesis":
            packet = json.loads(prompt.split(SEPARATOR, 1)[1])["paper_passages"]
            if not 1 <= len(packet) <= self.cap or len({p["chunk_id"] for p in packet}) != len(packet):
                self.refuse("Invalid synthesis packet")
            write(self.slot / "synthesis-evidence.json", packet)
        write(self.slot / f"{stage}.attempt.json",
              {"stage": stage, "prompt_bytes": len(prompt.encode()), "prompt_sha256": sha256(prompt.encode()).hexdigest()})
        self.used.append(stage)
        try:
            return self.fake(prompt, response_schema=response_schema)
        except Exception:
            self.failed = True
            raise


def exercise(question, arm, *, identity, retrieve, stage, shadow=None):
    """Call the frozen application paths with an in-process replay adapter."""
    cap = stage.cap
    if arm == "A":
        engine = IndexedResearch(retrieve=retrieve, identity=lambda: identity, generate=stage,
                                 metadata={"provider": "fixture"}, index_path="fixture",
                                 top_k=cap, quality_check=True)
        return engine.execute(dict(query=question, context_id=engine.context_id, interpret_context=False))
    with patch.object(agents, "MAX_EVIDENCE", cap), patch.object(agents, "MAX_RETRIEVAL_ROUNDS", 1):
        result = agents.OrchestratorAgent(generate=stage, retrieve=retrieve, top_k=cap, max_calls=3,
                                          index_sha256=identity["indexed_records_sha256"], research_only=True,
                                          numerical_shadow=shadow).run(question)
    return to_envelope(result, top_k=cap, provenance={"index": identity}, context_id="fixture")


def blind(results, secret):
    """Return independent review records and a separate restricted answer mapping."""
    masked, mapping = [], {}
    for item in results:
        label = sha256(f"{secret}:{item['id']}:{item['arm']}".encode()).hexdigest()[:20]
        summary = ((item["answer"] or {}).get("result") or {}).get("summary") or {}
        keys = ("kind", "text", "support")
        masked.append(dict(id=item["id"], label=label,
                           claims=[{k: deepcopy(claim[k]) for k in keys} for claim in summary.get("claims", [])],
                           limitations=deepcopy(summary.get("limitations", [])),
                           limitation_support=[{"text": x["text"], "support": deepcopy(x.get("support", []))}
                                               for x in summary.get("limitation_support", [])],
                           answer_lead=summary.get("answer_lead"),
                           scope=summary.get("answer_scope")))
        if label in mapping:
            raise ValueError("Duplicate blinded result")
        mapping[label] = (item["id"], item["arm"])
    return sorted(masked, key=lambda row: row["label"]), mapping


def summarize(pairs, rules):
    """Aggregate locked, adjudicated judgements, never drafts."""
    if len(pairs) != rules["pairs"] or len({p["id"] for p in pairs}) != len(pairs):
        raise ValueError("Missing or duplicate scheduled pairs")
    if any(not p[arm]["attempted"] for p in pairs for arm in ("A", "B")):
        return {"default_eligible": False, "inconclusive": "not all scheduled arms attempted"}
    if any(p[arm]["complete"] is None or p[arm]["unsupported"] is None for p in pairs for arm in ("A", "B")):
        return {"default_eligible": False, "inconclusive": "unresolved review; apply prespecified sensitivity bounds"}
    categories = {}
    for p in pairs:
        categories[p["category"]] = categories.get(p["category"], 0) + p["B"]["complete"] - p["A"]["complete"]
    net = sum(categories.values())
    added_unsupported = sum(p["B"]["unsupported"] - p["A"]["unsupported"] for p in pairs)
    latency = median([p["B"]["seconds"] - p["A"]["seconds"] for p in pairs])
    p90 = sorted(p["B"]["seconds"] for p in pairs)[math.ceil(0.9 * len(pairs)) - 1]
    calls = sum(p["B"]["calls"] - p["A"]["calls"] for p in pairs)
    cost = max(0, calls) / net if net > 0 else None
    eligible = (net >= rules["minimum_net_complete_successes"]
                and added_unsupported <= rules["maximum_net_unsupported_answer_cases"]
                and sum(v > 0 for v in categories.values()) >= rules["minimum_categories_with_positive_net_successes"]
                and latency <= rules["maximum_incremental_median_paired_seconds"]
                and p90 <= rules["maximum_improved_p90_seconds"]
                and cost <= rules["maximum_extra_actual_invocations_per_net_complete_success"])
    return dict(net=net, category_net=categories, additional_unsupported=added_unsupported,
                incremental_median_seconds=latency, improved_p90_seconds=p90, extra_calls_per_net_success=cost,
                default_eligible=eligible)


if __name__ == "__main__":
    verify_seal()
    print("Seal, runtime, and corpus verified. Offline only.")

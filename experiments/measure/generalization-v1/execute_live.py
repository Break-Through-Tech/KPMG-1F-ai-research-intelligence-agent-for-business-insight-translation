"""Run the authorized sealed schedule once and export blinded review artifacts."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import secrets
import sys
from time import perf_counter
from unittest.mock import patch

from offline_harness import HERE, ROOT, IndexedResearch, OfflineSession, agents, blind, read, to_envelope, verify_seal, write
from src.codex_generation import create_codex_generate
from src.experimental.b2 import open_b2
from src.research_chat import attach_validated_citations

sys.path.insert(0, str(HERE.parent / "bound-comparison"))
from bound_fixtures import TABLES
from workflow_shadow import NumericalShadow

OUT = ROOT / "data/processed/generalization-v1-execution"
SYSTEMIC = {"configuration", "forbidden_tool_output", "authentication", "rate_limited", "upstream_unavailable"}


def prepare():
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer

    verify_seal()
    machine = read(HERE.parent / "generalization-preselection-snapshot.json")
    for package, version in machine["packages"].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f"Dependency differs: {package}")
    expected = machine["proposed"]
    if expected["provider"] != "existing ChatGPT subscription" or expected["model"] != "gpt-6.1-sol":
        raise ValueError("Unexpected provider configuration")
    settings = read(HERE / "rules.json")
    schedule = read(HERE / "schedule.json")
    questions = {q["id"]: q["text"] for q in read(HERE / "questions.json")}
    if (len(questions) != 20 or len(schedule) != 20 or {r["id"] for r in schedule} != set(questions)
            or Counter(tuple(r["order"]) for r in schedule) != {("A", "B"): 10, ("B", "A"): 10}
            or settings["max_application_invocations"] != 100 or settings["application_retries"] != 0
            or settings["synthesis_passages"] != 8 or settings["top_k_per_query"] != 8
            or settings["synthesis_rounds"] != 1):
        raise ValueError("Unexpected schedule or budget")
    assets = read(HERE / "execution-assets.json")
    catalog = read(Path.home() / ".codex/models_cache.json")
    if not any(m["slug"] == expected["model"] and m.get("visibility") == "list" for m in catalog["models"]):
        raise ValueError("Model missing from existing subscription catalog")
    receipts = []
    generate, metadata = create_codex_generate(model=expected["model"], binary=assets["cli"],
          effort=expected["effort"], timeout=expected["timeout_seconds"], receipts=receipts)
    bundle = Path(machine["corpus"]["path"])
    pin = machine["corpus"]["artifact_sha256"]["parents.jsonl"]
    torch.set_num_threads(4)
    encoder = SentenceTransformer(assets["encoder"], local_files_only=True, device="cpu")
    reranker = CrossEncoder(assets["reranker"], local_files_only=True, device="cpu")
    modes = {}
    for arm, experimental in (("A", False), ("B", True)):
        route, identity, *_ = open_b2(bundle, encoder_path=assets["encoder"], reranker_path=assets["reranker"],
                                     encoder=encoder, reranker=reranker, table_comparisons=experimental)
        ident = identity()
        if ident["indexed_records_sha256"] != pin or bool(ident.get("table_comparisons")) != experimental:
            raise ValueError("Retrieval identity or option changed")
        modes[arm] = (route, identity)
    with (bundle / "parents.jsonl").open(encoding="utf-8-sig") as f:
        parents = {p["chunk_id"]: p for p in map(json.loads, f)}
    shadow = NumericalShadow(parents, read(TABLES)["records"])
    return settings, schedule, questions, generate, receipts, metadata, modes, shadow, machine


def execute_cell(session, qid, arm, question, generate, receipts, metadata, modes, shadow, check):
    saved = len(receipts)

    def wrapped(prompt, *, response_schema):
        stage_name = stage.used[-1]
        if len(receipts) >= 100:
            raise RuntimeError("Invocation ceiling")
        try:
            raw = generate(prompt, response_schema=response_schema)
            write(stage.slot / f"{stage_name}.response.json", json.loads(raw))
            return raw
        finally:
            if len(receipts) > saved + len(stage.used) - 1:
                write(stage.slot / f"{stage_name}.receipt.json", receipts[-1])

    check()
    stage = session.cell(qid, arm, wrapped)
    route, identity = modes[arm]
    ident = identity()
    cap = 8
    searches = []
    start = perf_counter()
    path_error = None
    answer = None

    def retrieve(query, k):
        if k != cap or identity() != ident:
            stage.refuse("Changed retrieval identity or cap")
        tick = perf_counter()
        try:
            passages = route(query, k)
            if len(passages) > cap:
                stage.refuse("Retrieval exceeded cap")
            searches.append(dict(query=query, ids=[p["chunk_id"] for p in passages], seconds=perf_counter() - tick))
            return passages
        except Exception as err:
            searches.append(dict(query=query, error=type(err).__name__, seconds=perf_counter() - tick))
            raise

    try:
        if arm == "A":
            engine = IndexedResearch(retrieve=retrieve, identity=identity, generate=stage, metadata=metadata,
                                     index_path="sealed demo-100", top_k=cap, quality_check=True)
            answer = engine.execute(dict(query=question, context_id=engine.context_id, interpret_context=False))
        else:
            with patch.object(agents, "MAX_EVIDENCE", cap), patch.object(agents, "MAX_RETRIEVAL_ROUNDS", 1):
                result = agents.OrchestratorAgent(generate=stage, retrieve=retrieve, top_k=cap, max_calls=3,
                           index_sha256=ident["indexed_records_sha256"], research_only=True,
                           numerical_shadow=shadow).run(question)
            write(stage.slot / "agentic.json", result)
            answer = to_envelope(result, top_k=cap, provenance={"index": ident, "generation": metadata},
                                 context_id="sealed-generalization")
    except Exception as err:
        path_error = type(err).__name__
    used = receipts[saved:]
    row = dict(id=qid, arm=arm, answer=answer, seconds=round(perf_counter()-start, 3),
               path_error=path_error, stage_violation=stage.violation, attempted_stages=stage.used,
               receipts=used, searches=searches)
    write(stage.slot / "result.json", row)
    categories = [r.get("diagnostic", {}).get("category") for r in used]
    unsafe = (stage.violation or len(used) != len(stage.used)
              or any(c in SYSTEMIC for c in categories)
              or any(r.get("diagnostic", {}).get("provider_code") in {"model_not_found", "insufficient_quota"} for r in used))
    return row, bool(unsafe)


def export(public, restricted, outputs, questions, schedule, stop):
    labels, mapping = blind(outputs, secrets.token_hex(32))
    by_key = {(r["id"], r["arm"]): r for r in outputs}
    evidence = []
    review = []
    inputs = Counter()
    failures = Counter()
    attempts = 0
    for item in labels:
        key = mapping[item["label"]]
        row = by_key[key]
        slot = restricted / f"{key[0]}-{key[1]}"
        path = slot / "synthesis-evidence.json"
        packet = read(path) if path.exists() else []
        essay = ((row["answer"] or {}).get("result") or {}).get("summary") or {}
        citation_status = "no published claims"
        if essay.get("claims"):
            try:
                attach_validated_citations(deepcopy(essay["claims"]), packet)
                citation_status = "quotes matched"
            except (ValueError, KeyError):
                citation_status = "quote or locator check failed"
        attempts += len(row["receipts"])
        for receipt in row["receipts"]:
            for usage in receipt.get("usage", []):
                inputs.update(usage)
            if receipt["status"] != "ok":
                failures[receipt.get("diagnostic", {}).get("category", receipt["status"])] += 1
            if not receipt.get("usage"):
                inputs["attempts_without_usage"] += 1
        envelope = row["answer"] or {}
        state = ("execution failure" if row["path_error"] or envelope.get("error")
                 else "answer" if essay.get("claims") else "abstention")
        review.append(item | {"question": questions[item["id"]], "final_state": state, "quote_check": citation_status,
                              "score": dict(required_points=None, citation_support=None, unsupported=None, complete=None,
                                            false_refusal=None, dispute=None, reviewer=None, human_verified=False)})
        evidence.append({"label": item["label"], "packet": packet})
    write(restricted / "unblind-after-review.json", mapping)
    write(public / "review.json", review)
    write(public / "synthesis-evidence.json", evidence)
    write(public / "coverage.json", {"stop": stop, "scheduled": 2 * len(schedule), "attempted": len(outputs),
          "not_attempted": 2 * len(schedule) - len(outputs), "applications": attempts, "usage": dict(inputs),
          "failures": dict(failures), "envelope_failures": sum(1 for r in review if r["final_state"] == "execution failure"),
          "output_states": dict(Counter(r["final_state"] for r in review)),
          "held_claims": sum(len((((r["answer"] or {}).get("result") or {}).get("summary") or {}).get("held_claims", []))
                             for r in outputs),
          "overlap_clearance": "No available authorized custodian. Sealed benchmark content was not opened.",
          "scores_locked": False, "winner": None})


def main():
    if sys.argv[1:] != ["--approved-once"] or OUT.exists():
        raise SystemExit("Explicit one-time execution flag and a new fixed output directory are required")
    started = perf_counter()
    settings, schedule, questions, generate, receipts, metadata, modes, shadow, machine = prepare()
    frozen_paths = {ROOT / k: v for k, v in machine["runtime_sha256"].items()}
    seal = read(HERE / "seal.json")
    frozen_paths.update({HERE / k: v for k, v in seal["files"].items()})
    for checked_file in (HERE / "execute_live.py", HERE / "seal.json", HERE.parent / "generalization-preselection-snapshot.json", TABLES):
        frozen_paths[checked_file] = sha256(checked_file.read_bytes()).hexdigest()
    assets = [Path(asset) for asset in read(HERE / "execution-assets.json")["sha256"]]
    assets += [Path(machine["corpus"]["path"]) / name for name in machine["corpus"]["artifact_sha256"]]
    stamps = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in assets}

    def check():
        if (any(sha256(path.read_bytes()).hexdigest() != value for path, value in frozen_paths.items())
                or any((path.stat().st_size, path.stat().st_mtime_ns) != stamp for path, stamp in stamps.items())):
            raise RuntimeError("Frozen file identity changed")

    check()
    OUT.mkdir(exist_ok=False)
    restricted, public = OUT / "restricted", OUT / "blinded"
    session = OfflineSession(restricted, schedule, settings)
    public.mkdir()
    write(restricted / "execution.json", {"metadata": metadata, "startup_seconds": perf_counter() - started,
                                          "launcher_sha256": frozen_paths[HERE / "execute_live.py"],
                                          "shadow_audit_sha256": frozen_paths[TABLES],
                                          "seal_sha256": frozen_paths[HERE / "seal.json"]})
    print("Preflight passed. Starting sealed schedule.", flush=True)
    outputs, stop = [], None
    try:
        for qid, arm in session.sequence:
            result, unsafe = execute_cell(session, qid, arm, questions[qid], generate, receipts, metadata, modes, shadow, check)
            outputs.append(result)
            print(f"{len(outputs)}/40 stored; {len(receipts)}/100 invocations", flush=True)
            if unsafe:
                stop = "Integrity, isolation or systemic provider stop condition"
                break
        check()
        verify_seal()
    except Exception as error:
        stop = f"Execution stopped: {type(error).__name__}"
    finally:
        export(public, restricted, outputs, questions, schedule, stop)
        print(f"Finished with {len(outputs)} stored runs and {len(receipts)} invocations. Stop: {stop}", flush=True)


if __name__ == "__main__":
    main()

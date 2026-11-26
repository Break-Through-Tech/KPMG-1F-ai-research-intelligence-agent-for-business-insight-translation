"""One-shot, capped subscription comparison on two fixed questions."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

from run import (ARCHIVE, BUNDLE, ENCODER, MEASURE, OLD, PIN, ROOT, RERANKER, TABLES,
                 IndexedResearch, NumericalShadow, POLICY, agents, digest, open_b2, patch, read, rows)
from envelope import to_envelope
from src.codex_generation import create_codex_generate
from tables import canonical, local_source, plain

MODEL = "gpt-6.1-sol"
BINARY = Path.home() / "AppData/Local/OpenAI/Codex/bin/f71a721e0e6193a9/codex.exe"
OUTPUT = ROOT / "data/processed/controlled-live-three-arm"
QUESTIONS = ("accuraterag", "travelplanner")
TICKETS = {"A": ("synthesis", "quality-review"), "B": ("plan", "synthesis", "verification"),
           "C": ("plan", "synthesis", "verification")}
PREFIXES = {agents.ORCHESTRATOR_PROMPT: "plan", "Synthesize an answer": "synthesis",
            POLICY: "quality-review", agents.VERIFIER_PROMPT: "verification"}
LIMIT = 16
CAP = 8
SEPARATOR = "Return only JSON matching the supplied schema.\n"


def save(path, data):
    with path.open("x", encoding="utf-8") as out:
        json.dump(data, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())


class ControlError(RuntimeError):
    pass


class Run:
    supports_response_schema = True

    def __init__(self, root, qid, arm, generate):
        if qid not in QUESTIONS or arm not in TICKETS:
            raise ControlError("No authorized run slot")
        self.path = root / f"{qid}-{arm}"
        self.path.mkdir(exist_ok=False)
        self.root, self.arm, self.generate = root, arm, generate
        self.used, self.failed = [], False
        self.violation = None

    def __call__(self, prompt, *, response_schema=None):
        stages = [stage for prefix, stage in PREFIXES.items() if prompt.startswith(prefix)]
        if (self.failed or len(stages) != 1 or len(self.used) >= len(TICKETS[self.arm])
                or stages[0] != TICKETS[self.arm][len(self.used)]):
            self.violation = "Out-of-order, repeated, or unauthorized provider stage refused"
            raise ControlError(self.violation)
        stage, = stages
        if response_schema is None or len(list(self.root.glob("*/*.attempt.json"))) >= LIMIT:
            self.violation = "Missing schema or budget exhausted"
            raise ControlError(self.violation)
        if stage == "synthesis":
            packet = json.loads(prompt.split(SEPARATOR, 1)[1])["paper_passages"]
            if not 1 <= len(packet) <= CAP or len({p["chunk_id"] for p in packet}) != len(packet):
                self.violation = "Synthesis evidence cap or uniqueness check failed"
                raise ControlError(self.violation)
            save(self.path / "synthesis-evidence.json", packet)
        save(self.path / f"{stage}.attempt.json", {"stage": stage, "prompt_sha256": sha256(prompt.encode()).hexdigest()})
        self.used.append(stage)
        try:
            reply = self.generate(prompt, response_schema=response_schema)
        except Exception:
            self.failed = True
            raise
        save(self.path / f"{stage}.response.json", json.loads(reply))
        return reply


def test_cap():
    packet = json.dumps({"paper_passages": [{"chunk_id": "one"}]})
    prompts = {stage: prefix for prefix, stage in PREFIXES.items()}
    prompts["synthesis"] += SEPARATOR + packet
    assert sum(map(len, TICKETS.values())) * len(QUESTIONS) == LIMIT
    calls = []

    def fake(prompt, *, response_schema):
        calls.append(prompt)
        return "{}"

    def must_refuse(fn, errors):
        try:
            fn()
        except errors:
            return
        raise AssertionError("Budget guard did not refuse")

    with TemporaryDirectory(prefix="three-arm-dry-") as temp:
        root = Path(temp)
        for qid in QUESTIONS:
            for arm in TICKETS:
                scoped = Run(root, qid, arm, fake)
                for stage in TICKETS[arm]:
                    scoped(prompts[stage], response_schema={})
                must_refuse(lambda: scoped(prompts["synthesis"], response_schema={}), ControlError)
                must_refuse(lambda: Run(root, qid, arm, fake), FileExistsError)
        assert len(calls) == len(list(root.glob("*/*.attempt.json"))) == LIMIT
    with TemporaryDirectory(prefix="three-arm-dry-") as temp:
        root = Path(temp)

        def timeout(prompt, *, response_schema):
            raise TimeoutError("fixture")

        scoped = Run(root, QUESTIONS[0], "A", timeout)
        must_refuse(lambda: scoped(prompts["synthesis"], response_schema={}), TimeoutError)
        must_refuse(lambda: scoped(prompts["synthesis"], response_schema={}), ControlError)
        assert len(list(root.glob("*/*.attempt.json"))) == 1
        oversized = Run(root, QUESTIONS[1], "A", fake)
        prompt = prompts["synthesis"].split(SEPARATOR)[0] + SEPARATOR + json.dumps(
            {"paper_passages": [{"chunk_id": str(i)} for i in range(CAP + 1)]})
        must_refuse(lambda: oversized(prompt, response_schema={}), ControlError)
        assert len(calls) == LIMIT


def source_packet(parents, audit):
    recorded = read(ARCHIVE / "accuraterag/result.json")
    table = recorded["source_targets"]
    _, dom = local_source(table["paper"], table["source_sha256"])
    assert dom is not None
    audited, = (r for r in audit if (r["arxiv_id"], r["table_id"]) == (table["paper"], table["table_id"]))
    assert audited["status"] == "structural_agreement" and audited["audit_original_rows_identical"]
    for row in table["rows"]:
        labels = [row["label"]]
        for pair in row["cells"]:
            labels.extend(pair.values())
        for label in labels:
            assert canonical(plain(dom.find(id=label["id"]))) == canonical(label["text"])
        assert parents[row["chunk_id"]]["source_sha256"] == table["source_sha256"]
    checked = read(OLD / "source-and-fake-replay.json")["source_anchor_checks"]
    abstracts = {}
    for version, required in (("2412.14470v2", ("349", "2,000", "8 categories", "10 common failure modes", "16 popular", "60%")),
                              ("2402.01622v4", ("sandbox", "four million", "1,225", "GPT-4", "0.6%"))):
        chunk = version + "_c0000"
        found = next(r for r in checked if r["chunk_id"] == chunk)
        _, paper = local_source(version, found["source_sha256"])
        assert paper is not None
        excerpt = plain(paper.find(id="abstract1"))
        assert all(canonical(x) in canonical(excerpt) for x in required)
        assert all(canonical(x) in canonical(parents[chunk]["text"]) for x in required)
        abstracts[version] = {"source_sha256": found["source_sha256"], "abstract": excerpt,
                              "source_url": found["source_url"], "chunk_id": chunk}
        if version == "2402.01622v4":
            raw = paper.find(id="S4")
            if raw is not None:
                abstracts[version]["experiment_section"] = plain(raw)
    return {"accuraterag": table, "travelplanner": abstracts}


def fingerprint():
    files = ("experiments/agentic/ab_questions.json", "experiments/agentic/numeric_checks.py",
             "experiments/agentic/agents.py", "experiments/agentic/contracts.py",
             "experiments/agentic/envelope.py", "src/codex_generation.py",
             "src/indexed_research.py", "src/research_chat.py", "src/answer_quality.py",
             "src/experimental/b2.py", "src/experimental/balanced_retriever.py",
             "experiments/measure/bound-comparison/workflow_shadow.py",
             "experiments/measure/bound-comparison/range_claim_links.py")
    return {name: digest(ROOT / name) for name in files}


def preflight():
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer

    if not __debug__:
        raise ControlError("Preflight requires assertions")
    test_cap()
    frozen = fingerprint()
    prior = read(MEASURE / "end-to-end-diagnostic/results.json")
    assert all(frozen.get(p.replace("\\", "/")) == sha for p, sha in prior["code_hashes"].items())
    assert read(ARCHIVE / "run.json")["generation"]["model"] == MODEL
    model_cache = read(Path.home() / ".codex/models_cache.json")
    assert any(m["slug"] == MODEL and m.get("visibility") == "list" for m in model_cache["models"])
    receipts = []
    generate, metadata = create_codex_generate(model=MODEL, binary=BINARY, effort="low", timeout=300, receipts=receipts)
    cli = subprocess.run([str(BINARY), "--version"], check=True, capture_output=True, text=True, timeout=15).stdout.strip()
    manifest = read(BUNDLE / "manifest.json")
    assert all(digest(BUNDLE / name) == sha for name, sha in manifest["artifact_sha256"].items())
    assert digest(BUNDLE / "parents.jsonl") == PIN
    parents = {p["chunk_id"]: p for p in rows(BUNDLE / "parents.jsonl")}
    assert len(parents) == 7667 and len({p["arxiv_id"] for p in parents.values()}) == 100
    spec = read(ROOT / "experiments/agentic/ab_questions.json")
    assert spec["corpus"]["parents_sha256"] == PIN
    assert frozen["experiments/agentic/ab_questions.json"] == "86828ce949f5c7708bd10770597215e6c31ba8aea030e3409df453b895b49668"
    questions = {"accuraterag": read(ARCHIVE / "run.json")["questions"]["accuraterag"],
                 "travelplanner": spec["questions"]["Q2"]["text"]}
    audit = read(TABLES)["records"]
    sources = source_packet(parents, audit)
    torch.set_num_threads(4)
    encoder = SentenceTransformer(str(ENCODER), local_files_only=True, device="cpu")
    reranker = CrossEncoder(str(RERANKER), local_files_only=True, device="cpu")
    routes, identities = {}, {}
    for arm in ("A", "C"):
        routes[arm], identity, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                           encoder=encoder, reranker=reranker, table_comparisons=(arm == "C"))
        identities[arm] = identity()
        assert identities[arm]["indexed_records_sha256"] == PIN
        assert bool(identities[arm].get("table_comparisons")) == (arm == "C")
    routes["B"], identities["B"] = routes["A"], identities["A"]
    assert metadata["auth"] == "existing_chatgpt_login" and not receipts
    return (dict(questions=questions, generation=metadata, cli_version=cli, identities=identities,
                 frozen=frozen, cap=CAP, budget=LIMIT, stage_slots=TICKETS,
                 source_sha256={k: v for k, v in manifest["artifact_sha256"].items()}),
            sources, generate, receipts, NumericalShadow(parents, audit), routes)


def run_cell(root, conf, qid, arm, inner, receipts, shadow, retrieve):
    stage = Run(root, qid, arm, inner)
    question, identity = conf["questions"][qid], conf["identities"][arm]
    start, lesson = perf_counter(), len(receipts)
    searches = []

    def logged(query, top_k):
        if top_k != CAP:
            stage.violation = "Retrieval cap differs from the fixed limit"
            raise ControlError(stage.violation)
        time = perf_counter()
        found = retrieve(query, top_k)
        if len(found) > CAP:
            stage.violation = "Retrieved too many passages"
            raise ControlError(stage.violation)
        searches.append({"query": query, "seconds": round(perf_counter() - time, 3),
                         "ids": [p["chunk_id"] for p in found]})
        return found

    envelope = None
    artifact_error = None
    try:
        if arm == "A":
            engine = IndexedResearch(retrieve=logged, identity=lambda: identity, generate=stage,
                                     metadata=conf["generation"], index_path=str(BUNDLE),
                                     top_k=CAP, quality_check=True)
            envelope = engine.execute(dict(query=question, context_id=engine.context_id, interpret_context=False))
        else:
            with patch.object(agents, "MAX_EVIDENCE", CAP), patch.object(agents, "MAX_RETRIEVAL_ROUNDS", 1):
                result = agents.OrchestratorAgent(generate=stage, retrieve=logged, top_k=CAP,
                                                  max_calls=3, index_sha256=PIN, research_only=True,
                                                  numerical_shadow=shadow if arm == "C" else None).run(question)
            save(stage.path / "agentic.json", result)
            envelope = to_envelope(result, top_k=CAP, provenance={"index": identity, "generation": conf["generation"]},
                                   context_id="isolated-live-comparison")
    except Exception as error:
        artifact_error = type(error).__name__
    usage = receipts[lesson:]
    record = dict(question=question, arm=arm, seconds=round(perf_counter() - start, 3), searches=searches,
                  attempted_stages=stage.used, receipts=usage, application_invocations=len(usage),
                  answer=envelope, artifact_error=artifact_error, isolation_violation=stage.violation)
    save(stage.path / "result.json", record)
    unsafe = {"configuration", "forbidden_tool_output", "authentication", "rate_limited"}
    if (stage.violation or artifact_error or len(usage) != len(stage.used)
            or any((r.get("diagnostic") or {}).get("category") in unsafe
                   or (r.get("diagnostic") or {}).get("provider_code") in {"model_not_found", "insufficient_quota"}
                   for r in usage)):
        raise ControlError("Live run stopped to preserve isolation or provider authorization")
    final = (envelope or {}).get("result") or {}
    print(qid, arm, "calls", len(usage), "result", (envelope or {}).get("scenario"),
          "claims", len(final.get("summary", {}).get("claims", [])), "seconds", record["seconds"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if OUTPUT.exists():
        raise SystemExit("One-shot output already exists. Reruns are disabled.")
    conf, sources, inner, receipts, shadow, routes = preflight()
    print(f"Preflight passed: {MODEL}, ChatGPT login, {PIN}, {CAP} passages, {LIMIT} fixed stage slots.", flush=True)
    if not args.execute:
        return
    OUTPUT.mkdir(exist_ok=False)
    save(OUTPUT / "preflight.json", conf)
    save(OUTPUT / "source-review.json", sources)
    complete = []
    try:
        for qid in QUESTIONS:
            for arm in TICKETS:
                if fingerprint() != conf["frozen"]:
                    raise ControlError("Frozen code changed")
                print("Starting", qid, arm, flush=True)
                run_cell(OUTPUT, conf, qid, arm, inner, receipts, shadow, routes[arm])
                complete.append(f"{qid}-{arm}")
    finally:
        save(OUTPUT / "experiment.json", dict(completed=complete, receipts=len(receipts),
             reserved=len(list(OUTPUT.glob("*/*.attempt.json"))), cap=LIMIT, frozen=fingerprint() == conf["frozen"]))


if __name__ == "__main__":
    main()

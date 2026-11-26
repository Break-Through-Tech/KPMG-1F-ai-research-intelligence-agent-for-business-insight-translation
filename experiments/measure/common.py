"""Shared paths and write-once outputs for the offline desktop study."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent.parent
MAIN = Path(os.getenv("KPMG_MEASURE_MAIN", r"C:\Users\ngkho\KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation"))
DATA = Path(os.getenv("KPMG_MEASURE_DATA", "D:/KPMG-demo-corpus"))
EXPORT = DATA / "main-727b0b3"
BUNDLE = EXPORT / "data/processed/demo-bundles/demo-100"
AUDIT = DATA / "table-endpoint-exp/table-audit-demo-100.json"
LEDGER = DATA / "table-endpoint-exp/codex-authorization-40.ledger.sqlite3"
ENCODER = Path.home() / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
RERANKER = MAIN / "data/processed/model-cache/models--cross-encoder--ms-marco-MiniLM-L6-v2/snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a"
PIN = "78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def rows(path):
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)

def save(out, name, data):
    if out.parent.resolve() != HERE or not out.is_dir():
        raise ValueError("Use a new output directory directly inside experiments/measure.")
    with (out / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

def pinned():
    manifest = read(BUNDLE / "manifest.json")
    audit = read(AUDIT)
    spec = read(WORK / "experiments/agentic/ab_questions.json")
    assert PIN == spec["corpus"]["parents_sha256"] == audit["index_sha256"]
    for name, expected in manifest["artifact_sha256"].items():
        assert digest(BUNDLE / name) == expected, name
    parents = list(rows(BUNDLE / "parents.jsonl"))
    assert len(parents) == manifest["parent_count"]
    assert len({p["arxiv_id"] for p in parents}) == 100
    return manifest, audit, spec, parents


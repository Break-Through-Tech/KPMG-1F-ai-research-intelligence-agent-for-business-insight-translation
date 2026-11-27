"""Freeze source material and configuration. Offline only."""
from collections import Counter
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE.parent)]

from common import BUNDLE, ENCODER, PIN, RERANKER, digest, read, rows, save
from tables import canonical, local_source, plain

CLI = Path.home() / "AppData/Local/OpenAI/Codex/bin/f71a721e0e6193a9/codex.exe"


def freeze():
    candidates = read(HERE / "cases.json")
    manifest = read(BUNDLE / "manifest.json")
    for name, sha in manifest["artifact_sha256"].items():
        if digest(BUNDLE / name) != sha:
            raise ValueError(f"Frozen bundle mismatch: {name}")
    if digest(BUNDLE / "parents.jsonl") != PIN:
        raise ValueError("Unexpected corpus")
    parents = {p["chunk_id"]: p for p in rows(BUNDLE / "parents.jsonl")}
    # Metadata only: no locked questions, expected points, answers or run traces are emitted or used.
    prior = read(HERE.parent / "generalization-v1/references.json")
    excluded = {p.split("v")[0] for item in prior for p in item["papers"]}
    excluded.update("2402.01622 2510.02243 2412.14470 2412.18690 2506.23273 2602.00931 2602.00933".split())
    prior_questions = [r["question"] for r in read(HERE.parent / "run-02/saved-traces.json")["recorded"]]
    prior_questions += [r["query"] for r in read(ROOT / "evaluation/benchmark_cases.json")]
    normalize_q = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
    sources = {}
    packet = []
    for qid, category, question, points in candidates:
        words = normalize_q(question)
        if any(len(words & normalize_q(q)) / len(words | normalize_q(q)) >= 0.6 for q in prior_questions):
            raise ValueError(f"Development question overlaps: {qid}")
        required = []
        for number, (answer, chunk, anchors) in enumerate(points, 1):
            row = parents[chunk]
            paper = row["arxiv_id"]
            if paper.split("v")[0] in excluded:
                raise ValueError(f"Excluded paper: {paper}")
            if paper not in sources:
                path, dom = local_source(paper, row["source_sha256"])
                if path is None:
                    raise ValueError(f"No hash-matched original HTML: {paper}")
                sources[paper] = dom
            dom = sources[paper]
            if isinstance(anchors, str):
                locators = []
                table = dom.find(id=row["table_id"])
                for cell_id in anchors.split():
                    cell = table.find(id=cell_id)
                    if cell is None or cell.name not in ("td", "th"):
                        raise ValueError(f"No table cell: {cell_id}")
                    value = plain(cell)
                    if canonical(value) not in canonical(row["text"]):
                        raise ValueError(f"Cell absent from indexed table row: {cell_id}")
                    locators.append({"original_id": cell_id, "original_text": value})
            else:
                locators = []
                for phrase in anchors:
                    if canonical(phrase) not in canonical(row["text"]):
                        raise ValueError(f"Absent from indexed passage: {chunk} / {phrase}")
                    block = next((p for p in dom.find_all("p") if canonical(phrase) in canonical(plain(p))), None)
                    if block is None:
                        raise ValueError(f"Absent from original: {chunk} / {phrase}")
                    locators.append({"original_id": block.get("id") or block.parent.get("id"),
                                     "phrase": phrase, "original_text": plain(block)})
            required.append({
                "point_id": f"{qid}.{number}", "expected": answer, "anchors": [[chunk]],
                "paper": paper, "source_sha256": row["source_sha256"], "source_url": row["source_url"],
                "table_id": row.get("table_id"), "original_anchors": locators,
            })
        packet.append({"id": qid, "category": category, "question": question,
                       "required_points": required, "human_verified": False})
    if len(packet) != 10 or len({q["id"] for q in packet}) != 10:
        raise ValueError("Expected ten distinct question IDs")
    return packet, {"category_counts": dict(Counter(q["category"] for q in packet)),
                    "paper_count": len(sources), "nonsealed_questions_compared": len(prior_questions),
                    "locked_check": "paper ID metadata only, version-independent exact exclusion"}


def seal():
    packet, exclusions = freeze()
    save(HERE, "references.json", packet)
    save(HERE, "questions.json", [{key: q[key] for key in ("id", "category", "question")} for q in packet])
    excluded_names = {"references.json", "questions.json", "seal.json", "offline-retrieval.json"}
    inputs = sorted([p for p in HERE.iterdir() if p.is_file() and p.name not in excluded_names]
                    + [HERE / "references.json", HERE / "questions.json"]
                    + list((ROOT / "src").rglob("*.py"))
                    + list((ROOT / "experiments/agentic").glob("*.py"))
                    + [HERE.parent / "common.py", HERE.parent / "tables.py",
                       HERE.parent / "trace-diagnostics/diagnose.py"])
    snap = {
        "files": {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs},
        "bundle": {"path": str(BUNDLE), "artifact_sha256": read(BUNDLE / "manifest.json")["artifact_sha256"]},
        "local_assets": {
            role: {"path": str(path), "sha256": {
                p.name: digest(p) for p in sorted(path.iterdir()) if p.is_file()
            }}
            for role, path in (("encoder", ENCODER), ("reranker", RERANKER))
        } | {"cli": {"path": str(CLI), "sha256": digest(CLI)}},
        "exclusion_audit": exclusions,
        "reference_points": sum(len(q["required_points"]) for q in packet),
    }
    save(HERE, "seal.json", snap)


if __name__ == "__main__":
    seal()

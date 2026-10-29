"""Read the retained pilot without changing it; curate extraction-only artifacts.

Run with the pilot's ingestion Python environment (pymupdf/pandas installed).
No model calls, downloads, ingestion reruns, or final-test task generation.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    return " ".join(text.split())


def select_quote(text, start, end):
    """Select one unambiguous raw source substring using whitespace-tolerant anchors."""
    pattern = lambda value: r"\s+".join(re.escape(s) for s in value.split())
    starts = list(re.finditer(pattern(start), text))
    if len(starts) != 1:
        raise ValueError(f"Ambiguous/missing start: {start!r}")
    first = starts[0].start()
    ends = list(re.finditer(pattern(end), text[starts[0].end():]))
    if len(ends) != 1:
        raise ValueError(f"Ambiguous/missing end: {end!r}")
    return text[first:starts[0].end() + ends[0].end()]


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=BASE / "artifacts/prepared-v1")
    args = parser.parse_args()
    pilot = args.pilot.resolve()
    old = pilot / "experiments/qwen-specialization/artifacts"
    selections = json.loads((BASE / "targets.json").read_text())
    manifest = json.loads((old / "source_manifest.json").read_text())
    papers = {r["arxiv_id"]: r for r in manifest["papers"]}
    from src.data_ingestion.pdf_pipeline import extract_and_clean_pdf

    artifacts = {}
    datasets = {}
    seen_ids, families = set(), {}
    for split in ["train", "dev"]:
        path = old / f"review_queue.{split}.jsonl"
        artifacts[str(path)] = sha(path)
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        datasets[split] = []
        for row in rows:
            if row["task"] != "extraction":
                continue
            pick = selections["cases"][row["id"]]
            chunk = row["evidence"][pick["chunk"]]
            quote = select_quote(chunk["text"], pick["start"], pick["end"])
            for evidence in row["evidence"]:
                paper = papers[evidence["arxiv_id"]]
                assert paper["split"] == split, "Split drift"
                assert families.setdefault(paper["family"], split) == split
                pdf = pilot / "data/pdfs" / (evidence["arxiv_id"] + ".pdf")
                assert sha(pdf) == paper["pdf_sha256"], "PDF hash drift"
                pages = {p["page"]: p["text"] for p in extract_and_clean_pdf(str(pdf))}
                assert evidence["text"] in pages[evidence["page_number"]], "Evidence/page drift"
            assert quote in chunk["text"]
            assert row["id"] not in seen_ids
            seen_ids.add(row["id"])
            # Raw quote retains line-break hyphenation; normalization changes whitespace only.
            target = f'"{norm(quote)}" [{chunk["chunk_id"]}]'
            curated = dict(row, target=target, review_status="ai_source_checked_not_human_reviewed",
                           eligible_for_training=False,
                           eligible_for_compatibility_smoke=(split == "train"),
                           selected_quote=quote, selected_chunk_id=chunk["chunk_id"],
                           review={"reviewer": selections["reviewer"], "rationale": pick["rationale"],
                                   "checks": ["source PDF hash", "all evidence in cited cleaned PDF pages",
                                              "literal quote in supplied chunk", "AI method relevance review"],
                                   "limits": "LLM target acceptance and source-family relatedness review are separate gates"})
            datasets[split].append(curated)
    assert seen_ids == set(selections["cases"]), "Selection coverage changed"
    # Retain historical extraction outputs unchanged, with exact hashes, never overwrite runs.
    outputs = []
    for path in sorted(old.glob("untuned-*.jsonl")):
        artifacts[str(path)] = sha(path)
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        header = rows[0]
        assert header["dev_sha256"] == sha(old / "review_queue.dev.jsonl")
        for row in rows[1:]:
            if row["task"] == "extraction":
                outputs.append({"run": header, "output": row, "source_sha256": sha(path)})
    args.output.mkdir(parents=True, exist_ok=False)
    for split, rows in datasets.items():
        (args.output / f"extraction.{split}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    write_json(args.output / "retained-baselines.json", outputs)
    write_json(args.output / "provenance.json", {
        "created": datetime.now(timezone.utc).isoformat(), "source_pilot": str(pilot),
        "source_artifact_sha256": artifacts, "source_manifest_sha256": sha(old / "source_manifest.json"),
        "selection_sha256": sha(BASE / "targets.json"), "prepare_sha256": sha(Path(__file__)),
        "counts": {split: len(rows) for split, rows in datasets.items()},
        "review": selections["reviewer"], "test_families_accessed_for_tasks": False,
        "training_eligible": False, "scope": "AI-reviewed compatibility preparation, not final supervision",
        "remaining": ["LLM-only target evaluation", "LLM related-family/near-duplicate split review",
                      "broader training dataset and held-out evaluation"]})
    print(json.dumps({"output": str(args.output), "counts": {s: len(v) for s, v in datasets.items()}}))


if __name__ == "__main__":
    main()

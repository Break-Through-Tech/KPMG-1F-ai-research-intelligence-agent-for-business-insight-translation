"""Read-only attribution of missing reference points in saved research runs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter


def diagnose(points, delivered, draft, published, held, published_claim_count, *, execution_error=False):
    """Labels use reviewed passage alternatives and zero-based claim positions.

    Each passage alternative is a complete set of anchors for the point.
    A published claim can cover multiple points. Claim counts are independent
    of point coverage. Unreviewed claims prevent a complete score.
    """
    if any(label not in {"supported", "unsupported", "unreviewed"} for label in published):
        raise ValueError("Unknown published claim label")
    if len(published) != published_claim_count:
        raise ValueError("Published claims do not match the adjudication")
    delivered = set(delivered)
    held = set(held)
    rows = {}
    for key, point in points.items():
        alternatives = point["anchors"]
        if not alternatives or any(not group for group in alternatives):
            raise ValueError(f"Missing source anchors for {key}")
        draft_index, final_index = point["draft"], point["final"]
        for index, claim_list in ((draft_index, draft), (final_index, published)):
            if index is not None and (type(index) is not int or not 0 <= index < len(claim_list)):
                raise ValueError(f"Invalid claim index for {key}")
        has_evidence = any(set(group) <= delivered for group in alternatives)
        if final_index is not None:
            if published[final_index] != "supported":
                raise ValueError(f"Published reference point {key} needs a supported claim")
            stage = "published"
        elif execution_error:
            stage = "execution_error"
        elif not has_evidence:
            stage = "missing_delivered_evidence"
        elif draft_index is None:
            stage = "draft_omission"
        elif draft[draft_index] in held:
            stage = "held_by_gate"
        else:
            stage = "unexplained_publication_loss"
        rows[key] = {"evidence": has_evidence, "stage": stage}
    if not rows:
        raise ValueError("No required reference points")
    supported = sum(r["stage"] == "published" for r in rows.values())
    abstained = not execution_error and published_claim_count == 0
    return {
        "point_decisions": rows,
        "evidence_coverage": [sum(r["evidence"] for r in rows.values()), len(rows)],
        "published_point_coverage": [supported, len(rows)],
        "complete": supported == len(rows) and all(x == "supported" for x in published),
        "abstained": abstained,
        "false_abstention": abstained and all(r["evidence"] for r in rows.values()),
        "partial_evidence_abstention": abstained and 0 < sum(r["evidence"] for r in rows.values()) < len(rows),
        "unsupported_published": published.count("unsupported"),
        "unreviewed_published": published.count("unreviewed"),
        "reviewed_published": published_claim_count - published.count("unreviewed"),
    }


def read_saved(path):
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


def score_saved(folder, labels):
    """Read native envelopes, including the original synthesis and held claims."""
    run, run_hash = read_saved(folder / "result.json")
    draft, draft_hash = read_saved(folder / "synthesis.response.json")
    packet, packet_hash = read_saved(folder / "synthesis-evidence.json")
    if [run_hash, draft_hash, packet_hash] != labels["sha256"]:
        raise ValueError(f"Saved artifacts changed for {folder.name}")
    result = run["answer"]["result"]
    summary = result["summary"]
    if packet != result["evidence"]:
        raise ValueError(f"Synthesis and final evidence differ for {folder.name}")
    if len(labels["published"]) != len(summary["claims"]):
        raise ValueError(f"Published claim labels missing for {folder.name}")
    output = diagnose(labels["points"], [r["chunk_id"] for r in packet],
                      [c["text"] for c in draft["claims"]], labels["published"],
                      [c["text"] for c in summary.get("held_claims", [])], len(summary["claims"]))
    return {
        **output, "question": run["question"], "summary_status": summary["status"],
        "historical_seconds": run["seconds"],
        "historical_invocations": run["application_invocations"],
        "historical_hold_reasons": [c.get("verification", {}).get("held_reason")
                                    for c in summary.get("held_claims", [])],
        "sha256": labels["sha256"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("development_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    labels = json.loads(Path(__file__).with_name("development-labels.json").read_text(encoding="utf-8"))
    started = perf_counter()
    runs = {key: score_saved(args.development_dir / key, label) for key, label in labels.items()}
    report = {"runs": runs, "diagnostic_seconds": round(perf_counter() - started, 6),
              "added_provider_invocations": 0}
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

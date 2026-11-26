"""Produce reviewer worksheets and operational totals without unblinding."""
from collections import Counter
import math
import secrets
from statistics import median

from offline_harness import HERE, ROOT, read, verify_seal, write

OUT = ROOT / "data/processed/generalization-v1-execution"


def main():
    verify_seal()
    blinded = OUT / "blinded"
    review = read(blinded / "review.json")
    coverage = read(blinded / "coverage.json")
    packets = {item["label"]: item["packet"] for item in read(blinded / "synthesis-evidence.json")}
    keys = {item["id"]: item for item in read(HERE / "references.json")}
    worksheets = []
    for item in review:
        key = keys[item["id"]]
        ids = {p["chunk_id"] for p in packets[item["label"]]}
        rows = [dict(number=i, requirement=point["point"], source_url=point["source_url"],
                     expected_chunk_id=point["chunk_id"], indexed_excerpt=point["indexed_excerpt"],
                     original_locator=point["original_locator"], original_anchor=point.get("original_anchor"),
                     source_cells=point.get("cells"), exact_required_chunk_in_packet=point["chunk_id"] in ids,
                     point_score=None, reviewer_comment=None)
                for i, point in enumerate(key["required_points"], 1)]
        worksheets.append(dict(label=item["label"], id=item["id"], category=key["category"],
            expected_disposition=key["expected"], second_reference_reviewer=key["second_human_review"],
            human_verified=False, reference_dispute=None, points=rows,
            alternative_sufficient_evidence=None, unsupported_claims=None, false_refusal=None,
            citation_semantic_support=None, complete=None))
    write(blinded / "scoring-worksheets.json", worksheets)

    # Operational IDs are independent of the answer labels. No label map is read.
    operations, stages, errors = [], Counter(), Counter()
    for path in (OUT / "restricted").glob("*/result.json"):
        row = read(path)
        receipts = row["receipts"]
        usage = Counter()
        for role, receipt in zip(row["attempted_stages"], receipts):
            stages[role] += 1
            for observed in receipt.get("usage", []):
                usage.update(observed)
            if receipt.get("status") != "ok":
                diagnostic = receipt.get("diagnostic") or {}
                errors[diagnostic.get("category", receipt.get("status", "unknown"))] += 1
        envelope = row.get("answer") or {}
        operations.append(dict(operation_id=secrets.token_hex(12), seconds=row["seconds"],
            attempts=len(receipts), usages=dict(usage),
            stage_receipts=[{k: item[k] for k in ("status", "elapsed_seconds", "diagnostic", "usage") if k in item}
                            for item in receipts],
            errors=envelope.get("error"), path_error=row.get("path_error"), stage_violation=row.get("stage_violation")))
    assert len(operations) == coverage["attempted"] and sum(r["attempts"] for r in operations) == coverage["applications"]
    latencies = sorted(r["seconds"] for r in operations)
    write(OUT / "usage-and-failures.json", coverage | {
        "median_seconds": round(median(latencies), 3) if latencies else None,
        "p90_seconds": latencies[math.ceil(len(latencies) * 0.9) - 1] if latencies else None,
        "stage_invocations": dict(stages), "receipt_failure_categories": dict(errors),
        "operations": sorted(operations, key=lambda r: r["operation_id"]),
        "internal_http_attempts": "not observable",
    })
    print(f"{len(worksheets)} blinded worksheets and {len(operations)} operational records exported.")


if __name__ == "__main__":
    main()

"""Run the shadow gate, then enable the isolated preview on a fresh fixture cohort."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from structured_trial import claim_digest, observe
from trial_fixtures import fresh_tables, shadow_controls, trial_cases
from bound_fixtures import MEASURE, PIN, digest, load, read

CHECKER = MEASURE.parent / "agentic/numeric_checks.py"
sys.path.insert(0, str(CHECKER.parent))
from numeric_checks import ground_claim

ARCHIVE = MEASURE / "run-02/saved-traces.json"
ARCHIVE_SHA256 = "cb7c0625b23b09f9c0656efe81f6c17eba8c82c27d7dd5024b9a773bb33871a5"
CHECKER_SHA256 = "9a8f8df61d7780ae7e27958caaa5e5dda669f94055ccd78bcfea7d81afe99051"


def archive_replay(parents, trusted):
    for saved in read(ARCHIVE)["recorded"]:
        envelope = {"result": {
            "summary": saved["summary"], "evidence": saved["evidence"],
            "provenance": {"index": {"indexed_records_sha256": saved["index"]}},
        }}
        original = claim_digest(envelope)
        observed = observe(envelope, {}, parents, trusted)
        yield {
            "version": saved["version"], "answer_preserved": original == claim_digest(observed["answer"]),
            "previews": len(observed["trial_comparisons"]),
            "checks": [
                {"current_numeric_checker": ground_claim(saved["summary"]["claims"][item["claim_index"]])["status"],
                 **item} for item in observed["checks"]
            ],
        }


def replay_cases(cases, parents, trusted, *, trial):
    for name, expected, envelope, record in cases:
        original = claim_digest(envelope)
        observed = observe(envelope, {0: record}, parents, trusted, trial=trial)
        claim = envelope["result"]["summary"]["claims"][0]
        check, = observed["checks"]
        previews = observed["trial_comparisons"]
        preserved = original == claim_digest(observed["answer"])
        correct_preview = (len(previews) == 1 and previews[0]["human_review"] == "pending"
                           if trial and expected == "linked" else len(previews) == 0)
        yield {
            "case": name, "expected": expected, "reviewed": False,
            "source_papers": sorted({row["arxiv_id"] for row in envelope["result"]["evidence"]}),
            "claim": claim, "record": record, "answer_preserved": preserved,
            "current_numeric_checker": ground_claim(claim)["status"],
            "observation": check if trial else {key: value for key, value in check.items() if key != "preview"},
            "preview": previews[0] if previews else None,
            "passed": check["status"] == expected and preserved and correct_preview,
        }


def replay():
    for path, expected in ((ARCHIVE, ARCHIVE_SHA256), (CHECKER, CHECKER_SHA256)):
        if digest(path) != expected:
            raise ValueError(f"study input changed: {path.name}")
    parents, trusted = load()
    saved = list(archive_replay(parents, trusted))
    shadow = list(replay_cases(shadow_controls(parents, trusted), parents, trusted, trial=False))
    archive_counts = Counter(item["status"] for row in saved for item in row["checks"])
    gate = (
        archive_counts == {"linked": 2, "review": 8}
        and len(saved) == 11
        and all(row["answer_preserved"] and row["previews"] == 0 for row in saved)
        and len(shadow) == 8 and all(row["passed"] for row in shadow)
    )
    if gate:
        fresh = fresh_tables(parents)
        trial = list(replay_cases(trial_cases(parents, fresh), parents, fresh, trial=True))
    else:
        trial = []
    return {
        "python": sys.version.split()[0], "provider_calls": 0, "index": PIN,
        "archive_sha256": ARCHIVE_SHA256, "current_checker_sha256": CHECKER_SHA256,
        "stage_2": {"passed": gate, "archive_counts": dict(archive_counts), "archives": saved, "controls": shadow},
        "stage_3": {
            "status": "passed_offline" if trial and all(row["passed"] for row in trial)
                      else "failed" if trial else "gate_closed",
            "outcomes": dict(Counter(row["observation"]["status"] for row in trial)),
            "cases": trial,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new JSON filename in this experiment")
    args = parser.parse_args()
    if args.output and (args.output.name != str(args.output) or args.output.suffix != ".json"):
        parser.error("use a new JSON filename without directories")
    result = replay()
    if args.output:
        with (HERE / args.output).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps({"shadow": result["stage_2"]["passed"],
                      "archive_counts": result["stage_2"]["archive_counts"],
                      "trial": result["stage_3"]["status"], "outcomes": result["stage_3"]["outcomes"]}, indent=2))
    return int(result["stage_3"]["status"] != "passed_offline")


if __name__ == "__main__":
    raise SystemExit(main())

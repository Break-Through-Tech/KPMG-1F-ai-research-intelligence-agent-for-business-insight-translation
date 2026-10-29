"""Summarize retained LLM-only development evaluations without dropping failures."""
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARTIFACTS = BASE / "artifacts"


def read(name):
    return json.loads((ARTIFACTS / name).read_text())


def percentile(values, fraction):
    values = sorted(values)
    index = (len(values) - 1) * fraction
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def main():
    initial = read("target-judge-v1/evaluation.json")
    judged = read("baseline-judge-v2/evaluation.json")
    adjudication = read("adjudication-v1/adjudication.json")
    smoke = read("lora-smoke-v1/smoke.json")
    assert initial["status"] == judged["status"] == "complete"
    assert smoke["status"] == "passed"
    output = {"scope": "LLM-only real-source extraction development pilot; no final-test evaluation or quality winner",
              "target_review": {}, "judge_anchor_agreement": [], "models": {}, "pairwise": [],
              "training_smoke": {k: smoke[k] for k in ["status", "trainable_parameters", "settings", "base_weights_unchanged", "adapter_sha256", "scope"]},
              "limits": ["Three dev families; repeated deterministic decoding is not six independent research cases",
                         "Quote checks normalize whitespace only; dehyphenation failures are not factual hallucinations",
                         "A conceptual mechanism definition exposed ambiguity in method relevance; uncertain judgments fail closed",
                         "All reviewers use the same model alias in separate contexts, not statistically independent models",
                         "No human judge, human-labeled calibration or team-review requirement",
                         "MLX peak is not total system memory; 27B run coincided with increased system swap",
                         "Three smoke steps on quote-only evidence do not constitute a trained quality candidate"],
              "next": ["Refine and version the method-versus-phenomenon rubric, then rejudge these dev cases",
                       "Run a prompt-only control on identical evidence before attributing failures to training",
                       "LLM-review source-family grouping, expand nontrivial extraction/abstention coverage, and freeze a larger development comparison",
                       "Only then run meaningful adapter training and a predeclared tuned/untuned comparison; keep final-test families untouched"]}
    for split in ["train", "dev"]:
        rows = [r for r in initial["rows"] if r["kind"] == f"target_{split}"]
        output["target_review"][split] = {"passed": sum(r["pass"] for r in rows), "total": len(rows)}
    for name, report in [("target-judge-v1", initial), ("baseline-judge-v2", judged)]:
        anchors = [r for r in report["rows"] if r["kind"] == "synthetic_anchor"]
        output["judge_anchor_agreement"].append({"run": name, "correct": sum(r["judge"]["verdict"] == r["expected"] for r in anchors), "total": len(anchors), "scope": "synthetic sanity checks, not calibrated TPR/TNR"})
    for label in ["untuned-9b", "untuned-27b"]:
        run = read(f"baseline-{'9b' if label.endswith('9b') else '27b'}-v1/run.json")
        rows = [r for r in judged["rows"] if r.get("label") == label]
        outcomes = []
        for row in rows:
            verdict = "pass" if row["pass"] else "fail"
            later = [a for a in adjudication["results"] if a["case_id"] == row["case_id"] and a["label"] == label and a["answer"] == row["answer"]]
            if later:
                # Same candidate bytes on both deterministic repeats: reuse its adjudication,
                # never pretend this is a new independent judgment or a new source case.
                verdict = later[0]["verdict"] if row["deterministic"]["pass"] else "fail"
            outcomes.append({"case_id": row["case_id"], "repeat": row["repeat"], "verdict": verdict})
        latencies = [a["seconds"] for a in run["attempts"]]
        successes = sum(o["verdict"] == "pass" for o in outcomes)
        families = {r["case_id"] for r in rows}
        output["models"][label] = {
            "attempts": len(rows), "families": len(families), "pointwise_passes_before_adjudication": sum(r["pass"] for r in rows),
            "final_verdict_counts": dict(Counter(o["verdict"] for o in outcomes)),
            "cases_passing_every_repeat": sum(all(o["verdict"] == "pass" for o in outcomes if o["case_id"] == case) for case in families),
            "category_failures_before_adjudication": dict(Counter(d for r in rows for d in ["quote_fidelity", "citation_valid", "method_relevance", "scope_and_qualifiers"] if not r["judge"][d])),
            "generation_seconds_total": sum(latencies), "generation_seconds_p50": statistics.median(latencies),
            "generation_seconds_p95_linear_interpolation": percentile(latencies, .95),
            "generation_seconds_per_confirmed_success": sum(latencies)/successes if successes else None,
            "cost_per_success_note": "undefined (zero confirmed successes)" if not successes else "generation time only; load/judge/training costs recorded separately",
            "load_seconds": run["load_seconds"], "mlx_peak_gib": max(a["mlx_peak_gib"] for a in run["attempts"]),
            "swap_observations": list(dict.fromkeys(a["swap"] for a in run["attempts"])), "outcomes": outcomes}
    for case in sorted({p["case_id"] for p in judged["pairwise"]}):
        pairs = [p for p in judged["pairwise"] if p["case_id"] == case]
        winners = [p[p["winner"]] if p["winner"] in ["A", "B"] else p["winner"] for p in pairs]
        output["pairwise"].append({"case_id": case, "mapped_verdicts": winners, "order_consistent": len(winners) == 2 and winners[0] == winners[1],
                                   "counted_verdict": winners[0] if len(winners) == 2 and winners[0] == winners[1] else "inconclusive"})
    receipts = initial["receipts"] + judged["receipts"] + adjudication["receipts"]
    output["judge_resources"] = {"calls": len(receipts), "elapsed_seconds": sum(r["elapsed_seconds"] for r in receipts),
        "usage": dict(sum((Counter({k: v for usage in r.get("usage", []) for k, v in usage.items() if isinstance(v, (int, float))}) for r in receipts), Counter())),
        "monetary_cost": None, "route": "existing ChatGPT subscription, no API-key provider"}
    output["artifact_sha256"] = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ARTIFACTS.rglob("*.json")) if p.is_file()}
    destination = BASE / "results.json"
    with destination.open("x") as file:
        file.write(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"results": str(destination), "verdicts": {label: value["final_verdict_counts"] for label, value in output["models"].items()}}))


if __name__ == "__main__":
    main()

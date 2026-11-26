"""Run frozen and transfer comparisons offline. Saved results are write-once."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
from decimal import Decimal
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bound_fixtures import ABSTRACT, BOUNDARIES, FROZEN, MEASURE, PARENTS, PIN, TABLES, digest, load, read
from bound_verify import Comparison, Quantity, render, verify

CHECKER = MEASURE.parent / "agentic/numeric_checks.py"
SAVED = MEASURE / "run-02/saved-traces.json"
SAVED_SHA256 = "cb7c0625b23b09f9c0656efe81f6c17eba8c82c27d7dd5024b9a773bb33871a5"
SAVED_CU_VERSIONS = {"e5a8c4c460134444ad0b3e7da476fa44", "39b20c7e451a4d2b9c5579a6b3767d34"}
sys.path.insert(0, str(CHECKER.parent))
from numeric_checks import ground_claim

STATUSES = {"grounded": "accept", "no_numbers": "accept",
            "contradicted": "reject", "uncertain": "review"}


def with_values(claim, left, right, unit):
    def number(values):
        return Quantity(Decimal(values[0]), Decimal(values[-1]), unit,
                        "point" if len(values) == 1 else "range")

    return replace(claim, before=replace(claim.before, value=number(left)),
                   after=replace(claim.after, value=number(right)))


def scope_change(claim, **changes):
    return replace(claim, scope=claim.scope | changes)


def typed_input(claim):
    if not isinstance(claim, Comparison):
        return None

    def operand(item):
        locations = sorted(item.locators, key=lambda loc: (loc.chunk_id, repr(loc.selector)))
        return {"value": asdict(item.value), "locators": [asdict(loc) for loc in locations]}

    return {"scope": claim.scope, "before": operand(claim.before), "after": operand(claim.after)}


def assess(name, cohort, expected, finding, claim, legacy_claim, context, reviewed=False):
    baseline = ground_claim(legacy_claim)
    decision = verify(finding, claim, context)
    return dict(
        name=name, cohort=cohort, reviewed=reviewed, expected=expected,
        original_claim=legacy_claim, typed_claim=typed_input(claim),
        current=STATUSES[baseline["status"]], current_detail=baseline,
        candidate=decision.status, reason=decision.reason,
        delivered_chunk_ids=sorted(context), rendered=render(finding, claim, context),
    )


def frozen_cases(parents, finding):
    snapshot = read(FROZEN)
    if digest(CHECKER) != snapshot["checker_sha256"]:
        raise ValueError("current numerical checker changed")
    claim = finding.comparison
    pairs = {
        "correct paired ranges": (("35", "46"), ("68", "78")),
        "reversed ranges": (("68", "78"), ("35", "46")),
        "regrouped endpoints": (("35", "78"), ("46", "68")),
        "collapsed endpoints": (("35",), ("78",)),
    }
    cases = []
    for row in snapshot["cases"]:
        if row["origin"] != "established audit":
            continue
        legacy = row["claim"]
        old = {key: value for key, value in row["results"]["numeric_strict_reject_only"].items()
               if key != "accepted"}
        if ground_claim(legacy) != old:
            raise ValueError(f"frozen checker result changed: {row['name']}")
        expected = "accept" if row["expected_supported"] else "reject"
        if row["source_chunk_id"] == ABSTRACT:
            left, right = pairs[row["name"]]
            result = assess(row["name"], "frozen range", expected, finding,
                            with_values(claim, left, right, "percent"), legacy,
                            {ABSTRACT: parents[ABSTRACT]}, row["reviewed"])
        else:
            status = STATUSES[old["status"]]
            result = dict(name=row["name"], cohort="frozen non-range", expected=expected,
                          original_claim=legacy, reviewed=row["reviewed"], current=status,
                          current_detail=old, candidate=status, reason="existing checker path")
        cases.append(result)
    return cases


def boundary_cases(parents, finding):
    claim = with_values(finding.comparison, ("35", "46"), ("68", "78"), "percent")
    variants = (
        ("different setting", scope_change(claim, setting="French elementary tasks"), "reject"),
        ("metric assigned in a separate sentence", scope_change(claim, metric="preference accuracy"), "reject"),
        ("clinical context transfer", scope_change(claim, setting="clinical deployment"), "reject"),
        ("equivalent range wording", claim, "accept"),
    )
    results = []
    for row, (name, binding, expected) in zip(read(BOUNDARIES), variants, strict=True):
        result = assess(name, "existing boundary draft", expected, finding, binding, row["claim"],
                        {ABSTRACT: parents[ABSTRACT]})
        if result["current"] != row["baseline"]:
            raise ValueError(f"boundary baseline changed: {name}")
        result["previous_adapter"] = row["adapter"]["status"]
        results.append(result)
    return results


def transfer_cases(findings):
    h = with_values(findings["hammer"].comparison, ("25.3", "36.3"), ("31.0", "39.3"), "score")
    a = with_values(findings["acdc"].comparison, ("50", "50"), ("92", "95"), "percent")
    r = with_values(findings["accuraterag"].comparison, ("74.00", "86.86"), ("68.36", "88.71"), "score")
    g = with_values(findings["agreemate"].comparison, ("0.3021",), ("-0.4385",), "score")
    yield "hammer", "accept", h, "Qwen3-1.7B-DAPO pass@1 on AIME 2024 and 2025 at k=100 ranged from 25.3–36.3 for the baseline and 31.0–39.3 for HAMMER."
    yield "hammer", "reject", scope_change(h, qualifier="k=32"), "At k=32, Qwen3-1.7B-DAPO pass@1 on AIME 2024 and 2025 ranged from 25.3–36.3 for the baseline and 31.0–39.3 for HAMMER."
    yield "hammer", "reject", scope_change(h, metric="pass@10"), "At k=100, Qwen3-1.7B-DAPO pass@10 on AIME 2024 and 2025 ranged from 25.3–36.3 for the baseline and 31.0–39.3 for HAMMER."
    yield "acdc", "accept", a, "Across IOI and Docstring, random-baseline AUC ranged from 50–50% and ACDC AUC ranged from 92–95%."
    yield "acdc", "reject", scope_change(a, population="IOI and Greater-Than"), "Across IOI and Greater-Than, random-baseline AUC ranged from 50–50% and ACDC AUC ranged from 92–95%."
    yield "acdc", "reject", with_values(a, ("50", "50"), ("92", "95"), "percentage_points"), "Across IOI and Docstring, random-baseline AUC ranged from 50–50 percentage points and ACDC AUC ranged from 92–95 percentage points."
    yield "accuraterag", "accept", r, "With fine-tuned Llama-2-7B on the three APIBench subsets, AST-match scores ranged from 74.00–86.86 for RAFT with GPT-4 CoT and 68.36–88.71 for AccurateRAG."
    yield "accuraterag", "reject", scope_change(r, subject="fine-tuned Llama-3-8B"), "With fine-tuned Llama-3-8B on the three APIBench subsets, AST-match scores ranged from 74.00–86.86 for RAFT with GPT-4 CoT and 68.36–88.71 for AccurateRAG."
    yield "accuraterag", "reject", scope_change(r, setting="PubMedQA"), "With fine-tuned Llama-2-7B on PubMedQA, AST-match scores ranged from 74.00–86.86 for RAFT with GPT-4 CoT and 68.36–88.71 for AccurateRAG."
    yield "accuraterag", "reject", replace(r, before=r.after, after=r.before), "With fine-tuned Llama-2-7B on the three APIBench subsets, AST-match scores ranged from 68.36–88.71 for RAFT with GPT-4 CoT and 74.00–86.86 for AccurateRAG."
    yield "agreemate", "accept", g, "AgreeMate's fairness score was 0.3021 without CoT and -0.4385 with CoT."
    yield "agreemate", "reject", with_values(g, ("0.3021",), ("0.4385",), "score"), "AgreeMate's fairness score was 0.3021 without CoT and 0.4385 with CoT."


def replay():
    parents, findings = load()
    cases = frozen_cases(parents, findings["cu"]) + boundary_cases(parents, findings["cu"])
    for index, (key, expected, claim, text) in enumerate(transfer_cases(findings), start=1):
        finding = findings[key]
        ctx = {ref.locator.chunk_id: parents[ref.locator.chunk_id] for ref in finding.citations}
        original = dict(text=text, kind="finding", support=[
            {"chunk_id": chunk, "quote": parent["text"]} for chunk, parent in ctx.items()
        ])
        cases.append(assess(f"{key}-{index:02d}", "transfer draft", expected, finding, claim, original, ctx))
    reasons = Counter((case["cohort"], case["candidate"]) for case in cases)
    mismatches = [
        case["name"] for case in cases
        if case["candidate"] != (case["current"] if case["cohort"] == "frozen non-range" else case["expected"])
    ]
    counts = dict(sorted((f"{group} / {status}", count) for (group, status), count in reasons.items()))
    return dict(
        python=sys.version.split()[0], provider_calls=0,
        input_sha256={path.name: digest(path) for path in (FROZEN, BOUNDARIES, TABLES, PARENTS, CHECKER)},
        cases=cases, counts=counts, gate_mismatches=mismatches,
        findings={name: {
            "comparison": typed_input(item.comparison), "before_label": item.before_label,
            "after_label": item.after_label, "citations": [asdict(ref) for ref in item.citations],
        } for name, item in findings.items()},
    )


def replay_retained():
    """Shadow-check two archived Baseline findings with explicit claim annotations."""
    if digest(SAVED) != SAVED_SHA256:
        raise ValueError("saved trace changes require a fresh source review")
    parents, findings = load()
    parent = parents[ABSTRACT]
    finding = findings["cu"]
    claim = with_values(finding.comparison, ("35", "46"), ("68", "78"), "percent")
    cases = []
    for row in read(SAVED)["recorded"]:
        if row["version"] not in SAVED_CU_VERSIONS:
            continue
        saved, = (p for p in row["evidence"] if p["chunk_id"] == ABSTRACT)
        if row["index"] != PIN or any(saved.get(key) != parent.get(key) for key in (
            "chunk_id", "arxiv_id", "source_url", "table_id", "text"
        )):
            raise ValueError(f"archived evidence identity changed: {row['version']}")
        original, = (c for c in row["summary"]["claims"] if
                     any(s["chunk_id"] == ABSTRACT for s in c["support"])
                     and all(ref.source_text in c["text"] for ref in finding.citations))
        if not any(s["chunk_id"] == ABSTRACT and s["quote"] in saved["text"] for s in original["support"]):
            raise ValueError("saved claim quote differs from the archived passage")
        cases.append(assess(row["version"], "retained Baseline range", "accept", finding,
                            claim, original, {ABSTRACT: parent}))
    if {case["name"] for case in cases} != SAVED_CU_VERSIONS or len(cases) != len(SAVED_CU_VERSIONS):
        raise ValueError("archived comparison set differs")
    return dict(
        archive_sha256=SAVED_SHA256, parents_sha256=PIN, provider_calls=0, cases=cases,
        counts=dict(Counter(case["candidate"] for case in cases)),
        gate_mismatches=[case["name"] for case in cases if case["candidate"] != case["expected"]],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new JSON filename inside this experiment")
    parser.add_argument("--retained", action="store_true", help="check the two archived CU-DPO answers")
    args = parser.parse_args()
    if args.output and (args.output.name != str(args.output) or args.output.suffix != ".json"):
        parser.error("use a new JSON filename without directories")
    results = replay_retained() if args.retained else replay()
    if args.output:
        with (HERE / args.output).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(results, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
    print(json.dumps({"counts": results["counts"], "gate_mismatches": results["gate_mismatches"]}, indent=2))
    return int(bool(results["gate_mismatches"]))


if __name__ == "__main__":
    raise SystemExit(main())

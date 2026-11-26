"""Run unchanged citation and number validators on the same frozen cases."""
from collections import Counter
from copy import deepcopy
import sys

from common import WORK, digest, save

def run(out, data):
    _, _, _, parents = data
    sys.path[:0] = [str(WORK), str(WORK / "experiments/agentic")]
    import numeric_checks as numeric
    import test_audit3
    import test_audit5
    from src.research_chat import attach_validated_citations, validate_reported_numbers
    from jsonschema import Draft202012Validator, ValidationError
    from src.research_chat import synthesis_schema
    p = next(p for p in parents if p["chunk_id"] == "2602.00931v2_c0000")
    cue = "On mathematical reasoning benchmarks,"
    quote = cue + p["text"].split(cue, 1)[1]
    established = []
    for name, text, source, status, _issue in test_audit3.FIXTURES:
        if status in {"grounded", "contradicted"}:
            established.append((name, text, source, status == "grounded", "audit3 fixture", status, None))
    for name, text, source, status, _outcome, _issue in test_audit5.CASES:
        if status in {"grounded", "contradicted"}:
            established.append((name, text, source, status == "grounded", "audit5 fixture", status, None))
    for name, comparison, supported in [
        ("correct paired ranges", "35–46% to 68–78%", True),
        ("reversed ranges", "68–78% to 35–46%", False),
        ("regrouped endpoints", "35–78% to 46–68%", False),
        ("collapsed endpoints", "35% to 78%", False),
    ]:
        established.append((name, f"Strategy selection accuracy improved from {comparison} across seven base models.",
                            quote, supported, "CU-DPO range", None, p))
    established.append(("equivalent under-18 qualifier", "Accuracy reached 78% only for participants under age 18.",
                        "Accuracy reached 78% only for minors under age 18.", True, "population paraphrase", None, None))
    drafts = [
        ("percent vs percentage points", "Accuracy increased by 10% on the benchmark.",
         "Accuracy increased by 10 percentage points on the benchmark.", False, "units", None, None),
        ("different denominator", "78% of all cases passed.", "78% of the 30 English cases passed.", False, "denominator/condition", None, None),
        ("valid phrasing with unit", "Latency was 60 seconds per run.", "Latency was one minute (1 minute) per run.", True, "unit conversion", None, None),
        ("unsupported setting with missing benchmark word", "Model X reached 78% accuracy in clinical deployment.",
         "Model X reached 78% accuracy on simulated cases.", False, "setting", None, None),
        ("negative sign", "Model X's performance changed by -5%.", "Model X's performance changed by +5%.", False, "sign", None, None),
        ("reference range paraphrase", "Across seven models, strategy selection accuracy went from 35–46% to 68–78%.", quote, True, "CU-DPO range", None, p),
        ("different setting, right range", "Strategy selection accuracy in hospitals went from 35–46% to 68–78%.",
         quote, False, "CU-DPO setting", None, p),
        ("wrong metric, same figure", "Downstream reasoning gains were 68–78% across seven base models.", quote, False, "CU-DPO metric", None, p),
        ("wrong comparison interpretation", "Strategy selection accuracy was 68–78 percentage points higher.", quote, False, "CU-DPO units", None, p),
        ("count outside numerical token parser", "Across nine base models, strategy selection accuracy reached 68–78%.", quote, False, "CU-DPO model count", None, p),
    ]
    records = []
    for origin, cases in [("established audit", established), ("draft", drafts)]:
        for name, text, source, expected, category, fixture_status, parent in cases:
            indexed = parent or dict(chunk_id="frozen-audit-" + str(len(records)+1),text=source)
            claim = dict(text=text, kind="finding", support=[dict(chunk_id=indexed["chunk_id"],quote=source)])
            results = {}
            for method, func in [
                ("quote_membership", lambda c: attach_validated_citations([c], [indexed])),
                ("literal_numbers", lambda c: validate_reported_numbers([c])),
                ("schema", lambda c: Draft202012Validator(synthesis_schema([indexed["chunk_id"]])).validate(
                    dict(status="ok", claims=[c], limitations=[])))
            ]:
                try:
                    func(deepcopy(claim))
                except (KeyError, ValueError, ValidationError) as e:
                    results[method] = dict(accepted=False, reason=str(e))
                else:
                    results[method] = dict(accepted=True)
            grounding = numeric.ground_claim(claim,{indexed["chunk_id"]:indexed})
            results["numeric_strict_reject_only"] = dict(accepted=grounding["status"]!="contradicted", **grounding)
            results["numeric_grounded_only"] = dict(accepted=grounding["status"] in {"grounded","no_numbers"})
            groups = {
                "sign": ("sign", "unsigned", "-3.2", "decrease"),
                "unit conversion": ("seconds","million","ms against"),
                "negation": ("negat",),
                "scope or condition": ("condition","lead-in","population","english"),
                "setting or subject": ("hospital","clinical","benchmark","contrast","elliptical"),
            }
            if category.endswith("fixture"):
                category = next((group for group,tokens in groups.items() if any(t in name.lower() for t in tokens)), "other")
            records.append(dict(origin=origin, reviewed=origin!="draft", human_adjudicated=False, name=name,
                                category=category, expected_supported=expected, source_chunk_id=indexed["chunk_id"],
                                source_url=indexed.get("source_url"), frozen_fixture_expected_status=fixture_status,
                                claim=claim, results=results))
    totals = {}
    for origin in {r["origin"] for r in records}:
        subset = [r for r in records if r["origin"] == origin]
        supported = sum(r["expected_supported"] for r in subset)
        counts = {}
        for key in subset[0]["results"]:
            false_accept = [r for r in subset if not r["expected_supported"] and r["results"][key]["accepted"]]
            false_reject = [r for r in subset if r["expected_supported"] and not r["results"][key]["accepted"]]
            counts[key] = dict(false_acceptances=len(false_accept), unsupported=len(subset)-supported,
                               false_rejections=len(false_reject), supported=supported,
                               false_accept_categories=dict(Counter(r["category"] for r in false_accept)),
                               false_reject_categories=dict(Counter(r["category"] for r in false_reject)))
        totals[origin]=counts
    save(out,"verification.json",dict(cases=records,totals=totals,
         checker_sha256=digest(WORK/"experiments/agentic/numeric_checks.py"),
         literal_sha256=digest(WORK/"src/research_chat.py"),
         design="All quotes are real within their pinned source or frozen synthetic fixture. This intentionally tests membership versus semantic support. Previously reviewed means established engineering audit decisions, not human adjudication."))


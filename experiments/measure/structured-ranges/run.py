"""Replay the frozen checker and experimental range adapter without touching the ledger."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from adapter import parse_roles, verify
from fixtures import ABSTRACT, ALIASES, UNIT, MEASURE, digest, new_cases, read, source_inputs

WORK=MEASURE.parent.parent
FROZEN=MEASURE/"run-02/verification.json"
CHECKER=WORK/"experiments/agentic/numeric_checks.py"
sys.path.insert(0,str(CHECKER.parent))
from numeric_checks import ground_claim

def reference_status(grounding):
    return {"contradicted":"reject","uncertain":"review","grounded":"accept","no_numbers":"accept"}[grounding["status"]]

def count(items,key):
    supported=[r for r in items if r["expected_supported"] is True]
    unsupported=[r for r in items if r["expected_supported"] is False]
    return dict(total=len(items), supported=len(supported), unsupported=len(unsupported),
                unadjudicated_semantics=len(items)-len(supported)-len(unsupported),
                correct_acceptances=sum(r[key]=="accept" for r in supported),
                wrong_acceptances=sum(r[key]=="accept" for r in unsupported),
                wrong_rejections=sum(r[key]=="reject" for r in supported),
                supported_referred=sum(r[key]=="review" for r in supported),
                rejected_unsupported=sum(r[key]=="reject" for r in unsupported),
                review=sum(r[key]=="review" for r in items), outcomes=dict(Counter(r[key] for r in items)))

def check_source_quotes(claim,parents):
    for item in claim["support"]:
        p=parents.get(item["chunk_id"])
        if p is not None:
            assert " ".join(item["quote"].split()) in " ".join(p["text"].split()), item["chunk_id"]

def run():
    frozen=read(FROZEN)
    assert digest(CHECKER)==frozen["checker_sha256"]
    parents,sources=source_inputs(frozen["cases"])
    results=[]
    for row in frozen["cases"]:
        claim=row["claim"]
        check_source_quotes(claim,parents)
        result=dict(name=row["name"],cohort=row["origin"],category=row["category"],
                    reviewed=row["reviewed"],expected_supported=row["expected_supported"],claim=claim)
        current=ground_claim(claim)
        assert current=={k:v for k,v in row["results"]["numeric_strict_reject_only"].items() if k!="accepted"}, row["name"]
        result.update(baseline=reference_status(current),baseline_detail=current,adapter=reference_status(current))
        if row["source_chunk_id"]==ABSTRACT:
            decision, scope, roles=verify(sources["cu"],claim,ALIASES["cu"],UNIT["cu"])
            result.update(adapter=decision.status,reason=decision.reason, source="cu", applied=True,
                          parsed_scope={k:sorted(v) for k,v in scope.items()},
                          parsed_roles={k:asdict(v) for k,v in roles.items()} if roles else None)
        else:
            result.update(applied=False,reason="non-range control; unchanged checker")
        results.append(result)
    for case in new_cases(sources):
        source=case["source"]
        claim=case["claim"]
        check_source_quotes(claim,parents)
        current=ground_claim(claim)
        decision, scope, roles=verify(sources[source],claim,ALIASES[source],UNIT[source])
        results.append(dict(case,cohort="new source-grounded draft",baseline=reference_status(current),
                            baseline_detail=current,adapter=decision.status,reason=decision.reason,applied=True,
                            parsed_scope={k:sorted(v) for k,v in scope.items()},
                            parsed_roles={k:asdict(v) for k,v in roles.items()} if roles else None))
    old=[r for r in results if r["cohort"]=="established audit"]
    assert (len(old),count(old,"baseline")["wrong_acceptances"],count(old,"baseline")["wrong_rejections"])==(33,3,1)
    for title,expectation in [("correct paired ranges","accept"),("reversed ranges","reject"),
                              ("regrouped endpoints","reject"),("collapsed endpoints","reject")]:
        case=next(r for r in old if r["name"]==title)
        assert case["adapter"]==expectation, case
    assert all(r["baseline"]==r["adapter"] for r in results if not r["applied"])
    assert all(r["adapter"]==r["expected"] for r in results if "expected" in r)
    # Alternate sentence order rendered from audited cells, never passed off as
    # verbatim original prose. Verify both projections bind to identical roles.
    layouts={}
    for label in ("hammer","auc"):
        record=sources[label]
        a,b=(record.roles[name] for name in ("before","after"))
        before=f"Before: [{a.lower},{a.upper}]."
        after=f"After: [{b.lower},{b.upper}]."
        forms=[before+" "+after,after+" "+before]
        parsed=[parse_roles(text,UNIT[label]) for text in forms]
        assert parsed[0]==parsed[1]==record.roles
        layouts[label]={"projected_sources":forms,"same_bindings":True,
                        "original_chunk_ids":[r["chunk_id"] for r in record.citations],
                        "kind":"derived sentence-order stress test"}
    groups={group:{k:count([r for r in results if r["cohort"]==group],k) for k in ("baseline","adapter")}
            for group in sorted({r["cohort"] for r in results})}
    selected_controls=[r for r in old if not r["applied"] and r["expected_supported"]]
    hashes={str(p):digest(p) for p in (FROZEN,CHECKER,MEASURE/"run-02/tables-dom-normalized.json",
                                      WORK/"experiments/agentic/ab_questions.json",
                                      HERE/"adapter.py",HERE/"fixtures.py",HERE/"run.py")}
    assert not any("codex_generation" in name or "capped_codex" in name for name in sys.modules)
    return dict(branch=subprocess.check_output(["git","branch","--show-current"],cwd=WORK,text=True).strip(),
                head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=WORK,text=True).strip(),
                python=sys.version,platform=platform.platform(),input_hashes=hashes,
                provider_calls=0,ledger_access="none",cohorts=groups,
                supported_nonrange_controls={k:count(selected_controls,k) for k in ("baseline","adapter")},
                source_findings={k:asdict(v) for k,v in sources.items()},source_order_checks=layouts,cases=results)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSON filename under the experiment directory")
    args=parser.parse_args()
    if Path(args.output).name!=args.output or not args.output.endswith(".json"):
        parser.error("supply a new .json filename without directories")
    out=HERE/args.output
    result=run()
    with out.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(result,f,ensure_ascii=False,indent=2,default=str)
        f.write("\n")
    print(json.dumps(result["cohorts"],indent=2))
if __name__=="__main__":
    main()


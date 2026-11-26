"""Adversarial boundary probes and typed-comparator invariants."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from adapter import compare, parse_roles, verify
from run import FROZEN, read, ground_claim, reference_status
from fixtures import ALIASES, UNIT, source_inputs

def shake(source, case, wording, expected_supported):
    claim=deepcopy(case["claim"])
    claim["text"]=wording
    decision, matches, comparison=verify(source,claim,ALIASES["cu"],UNIT["cu"])
    current=ground_claim(claim)
    return dict(claim=claim,reviewed=False,expected_supported=expected_supported,
                adapter=asdict(decision),baseline=reference_status(current),baseline_detail=current,
                matches={k:sorted(v) for k,v in matches.items()},parsed=comparison is not None)

def probes(cases, sources):
    base=next(r for r in cases if r["name"]=="correct paired ranges")
    return [
        shake(sources["cu"],base,
              "On French elementary tasks, strategy selection accuracy improved from 35–46% to 68–78% across seven base models.",False),
        shake(sources["cu"],base,
              "Preference accuracy improved from 35–46% to 68–78%. Strategy selection accuracy was discussed across seven base models.",False),
        shake(sources["cu"],base,
              "Strategy selection accuracy improved from 35–46% to 68–78% across seven base models during clinical deployment.",False),
        shake(sources["cu"],base,
              "Strategy selection accuracy ranged from 35% to 46% before training and from 68% to 78% afterward across seven base models.",True),
    ]

class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=read(FROZEN)["cases"]
        _,cls.sources=source_inputs(cls.cases)

    def test_structured_roles_bind_regardless_of_field_order(self):
        x=self.sources["hammer"]
        reversed_roles=dict(reversed(list(x.roles.items())))
        claim_scope={key:{x.scope[key]} for key in x.required_scope}
        self.assertEqual(compare(x,reversed_roles,claim_scope).status,"accept")

    def test_swapped_roles_reject(self):
        x=self.sources["hammer"]
        swaps={"before":x.roles["after"],"after":x.roles["before"]}
        self.assertEqual(compare(x,swaps,{key:{x.scope[key]} for key in x.required_scope}).status,"reject")

    def test_ambiguous_source_refers_to_review(self):
        x=replace(self.sources["hammer"],ambiguity=("unresolved column header",))
        self.assertEqual(compare(x,x.roles,{key:{x.scope[key]} for key in x.required_scope}).status,"review")

    def test_source_span_must_be_bound(self):
        x=self.sources["cu"]
        case=deepcopy(next(c for c in self.cases if c["name"]=="correct paired ranges"))
        case["claim"]["support"][0]["chunk_id"]="different-paper"
        self.assertEqual(verify(x,case["claim"],ALIASES["cu"],UNIT["cu"])[0].status,"review")

    def test_unit_scales_project_equivalent_proportions(self):
        a=parse_roles("from [0.50,0.50] to [0.92,0.95]","proportion")
        b=parse_roles("from 50–50% to 92–95%","proportion")
        self.assertEqual([q.canonical() for q in a.values()],[q.canonical() for q in b.values()])

    def test_percent_and_percentage_points_have_distinct_units(self):
        a=parse_roles("from 50–50% to 92–95%","proportion")
        b=parse_roles("from 50–50 percentage points to 92–95 percentage points","proportion")
        self.assertNotEqual([q.canonical() for q in a.values()],[q.canonical() for q in b.values()])

if __name__=="__main__":
    target=Path(sys.argv.pop()) if len(sys.argv)>1 else None
    if target:
        assert target.name==str(target) and target.suffix==".json"
        cases=read(FROZEN)["cases"]
        _,sources=source_inputs(cases)
        results=probes(cases,sources)
        with (HERE/target.name).open("x",encoding="utf-8",newline="\n") as f:
            json.dump(results,f,ensure_ascii=False,indent=2,default=str)
            f.write("\n")
    unittest.main(verbosity=2)


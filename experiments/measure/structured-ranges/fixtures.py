"""Source bindings for the structured range experiment.

The supported semantics are declared here; none are inferred from an answer key.
Existing source text, claims and audited cell values remain unchanged.
"""
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import sys

from adapter import Quantity, SourceFinding, parse_roles

MEASURE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(MEASURE))
from common import BUNDLE, PIN, digest, read, rows

ABSTRACT="2602.00931v2_c0000"
ANCHOR="On mathematical reasoning benchmarks,"
DIRECTION={"increase":("improved","improves","increased","went up","rose"),
           "decrease":("decreased","fell","dropped","declined")}

def ref(p,text,cell_ids=(), span=None):
    return dict(chunk_id=p["chunk_id"], source_url=p["source_url"], source_text=text,
                source_sha256=p.get("source_sha256"), cell_ids=list(cell_ids), span=span)

def table_source(parents, normalized, paper, table_id, row_labels, role_columns, scope, unit):
    table=next(t for t in normalized if (t["arxiv_id"],t["table_id"]) == (paper,table_id))
    assert table["status"]=="structural_agreement" and table["audit_original_rows_identical"] is True
    for column, expected_header in role_columns.values():
        assert table["headers"][column]["status"]=="agrees"
        assert table["headers"][column]["indexed"]["text"]==expected_header
    selected=[]
    collect=defaultdict(list)
    refs=[]
    width, = {len(labels) for labels in row_labels}
    for row in table["rows"]:
        if tuple(row["cells"][i]["indexed"]["text"] for i in range(width)) not in row_labels:
            continue
        parent=parents[row["chunk_id"]]
        assert parent["arxiv_id"]==paper and parent["table_id"]==table_id and parent["source_sha256"]==table["source_sha256"]
        cells=[]
        for role,(column,_header) in role_columns.items():
            cell=row["cells"][column]
            assert cell["status"]=="agrees" and cell["indexed"]==parent["table_cells"][column]
            collect[role].append(Decimal(cell["indexed"]["text"]))
            cells.append(cell["indexed"]["source_id"])
        selected.append(row["chunk_id"])
        refs.append(ref(parent,parent["text"],cells))
    if set(collect)!={"before","after"} or len(selected)!=len(row_labels):
        raise ValueError("missing or duplicate source rows")
    roles={name:Quantity(min(values),max(values),unit,"range") for name,values in collect.items()}
    if all(a<b for a,b in zip((roles["before"].lower,roles["before"].upper),(roles["after"].lower,roles["after"].upper))):
        scope=scope | {"direction":"increase"}
    return SourceFinding(paper,table["source_url"],"derived min/max over explicitly named, audited table rows",
                         tuple(refs),scope,roles,tuple(k for k in ("subject","metric","population","qualifier") if k in scope),())

def source_inputs(frozen):
    assert digest(BUNDLE/"parents.jsonl")==PIN
    parents={p["chunk_id"]:p for p in rows(BUNDLE/"parents.jsonl")}
    p=parents[ABSTRACT]
    start=p["text"].index(ANCHOR)
    quote=p["text"][start:]
    assert "CU- DPO improves strategy selection accuracy" in quote
    assert "across seven base models" in quote
    exact=next(case["claim"]["support"][0]["quote"] for case in frozen if case["name"]=="correct paired ranges")
    assert exact==quote
    cu=SourceFinding(p["arxiv_id"],p["source_url"],"exact abstract finding and declared scope",
         (ref(p,quote,span=[start,len(p["text"])]),),
         dict(subject="CU-DPO",metric="strategy_selection_accuracy",setting="math_benchmark",population="seven_models",
              direction="increase"), {},
         ("metric","population"), ())
    cu=SourceFinding(**(vars(cu) | {"roles":parse_roles(quote,"percent")}))
    normalized=read(MEASURE/"run-02/tables-dom-normalized.json")["records"]
    hammer=table_source(parents,normalized,"2509.25240v1","S5.T1",
        {("Qwen3-1.7B-DAPO","AIME 2024"),("Qwen3-1.7B-DAPO","AIME 2025")},
        {"before":(2,"pass@1 / B"),"after":(3,"pass@1 / H")},
        dict(subject="Qwen3-1.7B-DAPO",metric="pass@1",setting="benchmark",population="aime_two_years",
             qualifier="k=100"),"score")
    auc=table_source(parents,normalized,"2604.00324v1","A1.T1",{("IOI",),("Docstring",)},
        {"before":(2,"Random AUC"),"after":(1,"ACDC AUC")},
        dict(subject="ACDC",metric="auc",setting="random_baseline_experiment",population="ioi_docstring"),"proportion")
    return parents,{"cu":cu,"hammer":hammer,"auc":auc}

ALIASES={
 "cu":{
    "subject":{"CU-DPO":("CU-DPO",),"binary_DPO":("binary DPO",)},
    "metric":{"strategy_selection_accuracy":("strategy selection accuracy","strategy-selection accuracy"),
              "downstream_reasoning":("downstream reasoning",),"other_metric":("pass@1",)},
    "setting":{"math_benchmark":("mathematical reasoning benchmarks",),"hospital":("hospitals","clinical deployment")},
    "population":{"seven_models":("seven base models","seven models","7 base models"),
                  "nine_models":("nine base models","9 base models"),"eight_models":("eight base models","8 base models")},
    "direction":DIRECTION},
 "hammer":{
    "subject":{"Qwen3-1.7B-DAPO":("Qwen3-1.7B-DAPO",),"other_model":("DeepSeek-R1",)},
    "metric":{"pass@1":("pass@1",),"pass@10":("pass@10",)},
    "setting":{"benchmark":("benchmark",)},
    "population":{"aime_two_years":("AIME 2024 and AIME 2025","AIME 2025 and AIME 2024"),
                  "aime_other":("AIME 2024 and AMC 2023",)},
    "qualifier":{"k=100":("k=100",),"k=32":("k=32",)},
    "direction":DIRECTION},
 "auc":{
    "subject":{"ACDC":("ACDC",)},
    "metric":{"auc":("AUC",),"accuracy":("accuracy",)},
    "population":{"ioi_docstring":("IOI and Docstring","Docstring and IOI"),
                  "ioi_greater_than":("IOI and Greater-Than",)},
    "direction":DIRECTION},
}
UNIT={"cu":"percent","hammer":"score","auc":"proportion"}

def new_cases(sources):
    drafts=[]
    def add(name,source,text,expected,*,support=None,note=None):
        target=sources[source]
        result=dict(name=name,source=source,expected=expected,reviewed=False,note=note,
                    expected_supported=(True if note else {"accept":True,"reject":False,"review":None}[expected]))
        citations=target.citations if support is None else support
        result["claim"]=dict(text=text,kind="finding",support=[{"chunk_id":r["chunk_id"],"quote":r["source_text"]}
                                                               for r in citations])
        drafts.append(result)
    h="Qwen3-1.7B-DAPO pass@1 for AIME 2024 and AIME 2025 (k=100)"
    add("HAMMER brackets, treatment named first","hammer",h+"; treatment: [31.0,39.3]; baseline: [25.3,36.3].","accept",
        support=tuple(reversed(sources["hammer"].citations)))
    add("HAMMER from/to with an alternate population order","hammer",
        "Qwen3-1.7B-DAPO pass@1 for AIME 2025 and AIME 2024 (k=100) increased from 25.3–36.3 to 31.0–39.3.","accept")
    add("HAMMER reversed roles","hammer",h+"; treatment: [25.3,36.3]; baseline: [31.0,39.3].","reject")
    add("HAMMER misplaced range endpoint","hammer",h+"; baseline: [25.3,39.3]; treatment: [31.0,36.3].","reject")
    add("HAMMER omitted dataset pair","hammer","Qwen3-1.7B-DAPO pass@1 ranged from 25.3–36.3 to 31.0–39.3.","review")
    add("HAMMER omitted required sampling condition","hammer",h.replace(" (k=100)","")+" increased from 25.3–36.3 to 31.0–39.3.","review")
    add("HAMMER alternate reporting condition","hammer",h.replace("k=100","k=32")+" increased from 25.3–36.3 to 31.0–39.3.","reject")
    add("HAMMER missing cited endpoint row","hammer",h+" increased from 25.3–36.3 to 31.0–39.3.","review",
        support=sources["hammer"].citations[:1])
    add("HAMMER both measures named","hammer",h.replace("pass@1","pass@1 and pass@10")+" increased from 25.3–36.3 to 31.0–39.3.","review")
    add("HAMMER wrong reported direction","hammer",h+" decreased from 25.3–36.3 to 31.0–39.3.","reject")
    add("AUC closed intervals","auc","ACDC AUC across IOI and Docstring changed from [0.50,0.50] to [0.92,0.95].","accept")
    add("AUC consistent scale conversion","auc","ACDC AUC across IOI and Docstring changed from 50–50% to 92–95%.","accept")
    add("AUC levels expressed as a percentage-point delta","auc",
        "ACDC AUC across IOI and Docstring changed from 50–50 percentage points to 92–95 percentage points.","reject")
    add("AUC different task cohort","auc","ACDC AUC across IOI and Greater-Than changed from [0.50,0.50] to [0.92,0.95].","reject")
    add("AUC one comparison with two possible cohorts","auc",
        "ACDC AUC for IOI and Docstring or IOI and Greater-Than changed from [0.50,0.50] to [0.92,0.95].","review")
    add("AUC out-of-grammar inequality","auc","ACDC AUC across IOI and Docstring changed from [0.50,0.50] to under 0.95.","review")
    add("AUC source-preserving wording outside grammar","auc","ACDC AUC across IOI and Docstring was 0.50 for both tasks at baseline; the ACDC scores spanned 0.92–0.95.","review",
        note="Supported prose, but an unsupported parse form; remains a review referral.")
    return drafts


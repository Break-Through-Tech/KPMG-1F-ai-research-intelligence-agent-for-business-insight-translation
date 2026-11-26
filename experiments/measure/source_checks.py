"""Extra source and fake-verifier checks for the diagnostic cases."""
from collections import defaultdict
from pathlib import Path
import sys

from common import HERE, WORK, pinned, read, save
from retrieval import norm
from tables import local_source, plain

def run(out):
    _,_,_,parents=pinned()
    selected=read(out/"eligibility.json")["selected"]
    index={p["chunk_id"]:p for p in parents}
    by_doc=defaultdict(list)
    for p in parents:
        by_doc[p["arxiv_id"]].append(p)
    cache={}
    records=[]
    for case in selected:
        for part in case["parts"]:
            for ident in part["gold"]:
                parent=index[ident]
                version=parent["arxiv_id"]
                sha=parent.get("source_sha256")
                hashes=[sha] if sha else sorted({r["source_sha256"] for r in by_doc[version] if r.get("source_sha256")})
                if version not in cache:
                    candidates=[(s,*local_source(version,s)) for s in hashes]
                    cache[version]=next((x for x in candidates if x[2] is not None),(None,None,None))
                source_sha,path,dom=cache[version]
                snippet=parent.get("source_anchor") or parent.get("paragraph_id") or parent.get("table_id")
                section=dom.find(id=snippet) if dom and snippet else None
                terms=part.get("anchors") or [q for q in part.get("quotes",[]) if norm(q) in norm(parent["text"])]
                text=norm(plain(section or dom)) if dom else ""
                records.append(dict(question=case["id"],point=part["id"],chunk_id=ident,source_url=parent.get("source_url"),
                                    origin_path=str(path) if path else None,source_sha256=source_sha,
                                    anchor=snippet,scope="indexed DOM locator" if section else "whole paper" if dom else None,
                                    literal_terms=[dict(text=t,found=norm(t) in text) for t in terms],
                                    exact_indexed_text_present_in_source=norm(parent["text"]) in text if text else None,
                                    reviewed=False))
    sys.path[:0]=[str(WORK),str(WORK/"experiments/agentic")]
    from test_audit5 import run as replay
    supported_cases={"equivalent under-18 qualifier","correct paired ranges","reversed ranges","regrouped endpoints","collapsed endpoints"}
    runs=[]
    for case in read(out/"verification.json")["cases"]:
        if case["name"] in supported_cases:
            claim=case["claim"]
            result=replay(claim["text"],claim["support"][0]["quote"])
            summary=result["summary"]
            runs.append(dict(case=case["name"],pinned_source=case["source_chunk_id"],expected_supported=case["expected_supported"],
                             held=not bool(summary["claims"]),retained=[c["text"] for c in summary["claims"]],
                             provider="permissive deterministic fake",reviewed=case["reviewed"]))
    save(out,"source-and-fake-replay.json",dict(source_anchor_checks=records,fake_verifier_replay=runs))
if __name__=="__main__":
    run(HERE/sys.argv[1])


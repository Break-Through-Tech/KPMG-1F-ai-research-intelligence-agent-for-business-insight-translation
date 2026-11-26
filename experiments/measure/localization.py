"""Read saved research envelopes and local lifecycle artifacts without opening a server."""
from collections import defaultdict
import importlib.metadata
import os
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

from common import AUDIT, BUNDLE, DATA, ENCODER, EXPORT, LEDGER, RERANKER, WORK, digest, read, rows, save

def git(*args):
    return subprocess.check_output(["git","--no-optional-locks",*args],cwd=WORK,text=True).splitlines()

def saved(out, data):
    manifest, audit, spec, parents=data
    sys.path.insert(0,str(WORK / "experiments/table-endpoint"))
    from evidence_compaction import compact_prompt
    import json
    ids={p["chunk_id"]:p for p in parents}
    recorded=[]
    dbs=[DATA/"fable-live-briefs.sqlite3",DATA/"table-endpoint-exp/ui-consult-live-briefs.sqlite3"]
    for db in dbs:
        with sqlite3.connect(db.as_uri()+"?mode=ro&immutable=1",uri=True) as c:
            for version,raw in c.execute("select id,envelope_json from brief_versions"):
                env=json.loads(raw)
                result=env.get("result") or {}
                request=result.get("request") or env.get("submitted_request",{})
                question=request.get("query","")
                # These are retained desktop demos, not evaluation answer keys.
                prov=result.get("provenance") or {}
                evidence=result.get("evidence",[])
                prompt=json.dumps(dict(question=question,passages=evidence),ensure_ascii=False)
                trimmed,compaction=compact_prompt(prompt)
                reconstructed=json.loads(trimmed).get("passages",[])
                recorded.append(dict(database=str(db),version=version,question=question,scenario=env.get("scenario"),
                                     pipeline=(prov.get("retrieval") or {}).get("method"),index=(prov.get("index") or {}).get("indexed_records_sha256"),
                                     error=env.get("error"),timings=prov.get("timings_seconds"),stages=prov.get("stages"),
                                     summary=result.get("summary"),evidence=[{
                                         "chunk_id":p["chunk_id"],"arxiv_id":p.get("arxiv_id"),"title":p.get("title"),
                                         "source_url":p.get("source_url"),"table_id":p.get("table_id"),"row_label":p.get("row_label"),
                                         "same_parent_text":p["chunk_id"] in ids and p.get("text")==ids[p["chunk_id"]].get("text"),
                                         "text":p.get("text")
                                     } for p in evidence],
                                     compaction_replay=dict(compaction,all_ids_and_text_preserved=
                                         [(p["chunk_id"],p["text"]) for p in evidence]==[(p["chunk_id"],p["text"]) for p in reconstructed])))
    timeout_log=[]
    for path in sorted((DATA/"table-endpoint-exp").glob("live-calls*.jsonl")):
        for r in rows(path):
            if (r.get("seconds") or 0)>=300 or r.get("prompt_chars")==24066:
                timeout_log.append(dict(path=str(path),**{k:r.get(k) for k in ("call","at","seconds","prompt_chars","outcome")},
                                        cause_type=(r.get("cause") or {}).get("type")))
    save(out,"saved-traces.json",dict(recorded=recorded, timeout_entries=timeout_log,
          prior_diagnostics=[str(WORK/"docs/issue-122-retrieval-diagnostics.md"),str(WORK/"ui-consult/design/INTEGRATION-AND-QA.md")],
          prior_reports=[dict(path=str(p),tag=read(p).get("tag"),questions=read(p).get("questions"),errors=read(p).get("errors"))
                         for p in sorted((DATA/"results").glob("query-*-run1.json"))]))
    views=read(BUNDLE/"views.json")
    match_ids={c for q in spec["questions"].values() for point in q["required_points"] for c in point["source_chunks"]}
    match_ids.update(p["chunk_id"] for p in parents if p["arxiv_id"]=="2604.00319v1" and
                     (p.get("table_id")=="S5.T1" or p["chunk_id"]=="2604.00319v1_c0019"))
    boundary=[]
    for ident in sorted(match_ids):
        p=ids.get(ident)
        if p is None:
            boundary.append(dict(chunk_id=ident,indexed=False))
            continue
        anchors=sorted({a for q in spec["questions"].values() for n in q["required_points"]
                        if ident in n["source_chunks"] for a in n["anchors"] if a in p["text"]})
        pviews=[v for v in views if v["parent_chunk_id"]==ident]
        boundary.append(dict(chunk_id=ident,indexed=True,arxiv_id=p["arxiv_id"],source_url=p.get("source_url"),
                             table_id=p.get("table_id"),row_label=p.get("row_label"),text=p["text"],anchors=anchors,
                             view_ids=[v["view_id"] for v in pviews],
                             anchors_absent_from_every_view=[a for a in anchors if not any(a in v["text"] for v in pviews)],
                             at_least_one_view_with_all_anchors=bool(anchors) and any(all(a in v["text"] for a in anchors) for v in pviews)))
    save(out,"chunk-boundaries.json",boundary)

def historical_retrieval(out,data):
    _,_,spec,parents=data
    sys.path.insert(0,str(EXPORT))
    import torch
    from src.experimental.b2 import open_b2
    torch.set_num_threads(4)
    retrieve, identity, _, _=open_b2(BUNDLE,encoder_path=ENCODER,reranker_path=RERANKER)
    qs={
      "laptop_xgboost":"How does XGBoost compare with LLM-based AI agents for fault detection in terms of accuracy, precision, recall, and speed?",
      "laptop_critics":"What criteria do AI critics use to evaluate agent responses?",
      "Q3":spec["questions"]["Q3"]["text"],
      "saved_CU-DPO_chart":"Compare the seven base models' performance before and after CU-DPO. Show a chart using the paper's original numerical results table, with citations for each value.",
    }
    # Replay exact saved wording, using the retained requests rather than brief titles.
    for record in read(out/"saved-traces.json")["recorded"]:
        if record["version"] in {"a964786bd4fe48bbab643c0272f44421","08ca414c98754b068a44222c9d498c9f","b2a9bd0559d04dad93327fb584f06352"}:
            qs["saved_"+record["version"]] = record["question"]
    sys.path.insert(0,str(WORK/"experiments/table-endpoint"))
    from chart_preview import preview
    from evidence_tables import TableIndex
    tables=TableIndex(BUNDLE/"parents.jsonl",AUDIT)
    result={}
    for label,query in qs.items():
        hits=retrieve(query,20)
        result[label]=dict(question=query,evidence=[dict(rank=i,chunk_id=p["chunk_id"],arxiv_id=p["arxiv_id"],source_url=p.get("source_url"),table_id=p.get("table_id"),row_label=p.get("row_label")) for i,p in enumerate(hits,1)])
        if label=="saved_CU-DPO_chart":
            result[label]["current_chart_preview"]=preview(query,hits[:8],tables,identity()["indexed_records_sha256"])
            # Known-correct rows isolate table reconstruction from retrieval.
            rows_for_selection=[p for p in parents if p.get("table_id")=="S3.T2" and p["arxiv_id"]=="2602.00931v2"]
            result[label]["known_table_chart_preview"]=preview("Chart before and after strategy-selection accuracy from CU-DPO Table 2.", rows_for_selection, tables, identity()["indexed_records_sha256"])
    cases={}
    for paper,sections in [("2604.00319",()),("2408.13687",()),("2508.03553",("conclusion",)),
                           ("2602.07294",("conclusion",)),("2402.12713",("prompt","mitigation","conclusion"))]:
        supplied=[p for p in parents if p["arxiv_id"].startswith(paper)]
        cases[paper]=dict(parent_count=len(supplied),versions=sorted({p["arxiv_id"] for p in supplied}),
                          source_passages=[{k:p.get(k) for k in ("chunk_id","section","subsection","source_url","text")}
                                           for p in supplied if any(s in (p.get("section","")+" "+p.get("subsection","")).lower()
                                                                    for s in sections)])
    save(out,"historical-retrieval.json",dict(identity=identity(),results=result,source_inventory=cases))

def environment(out,before,executed,data):
    manifest,audit,_,_=data
    with sqlite3.connect(LEDGER.as_uri()+"?mode=ro&immutable=1",uri=True) as c:
        ledger=dict(integrity=c.execute("pragma integrity_check").fetchone()[0],
                    outcomes=c.execute("select state,outcome,count(*) from calls group by state,outcome").fetchall(),
                    caps=c.execute("select count(*) from caps").fetchone()[0],
                    locked=c.execute("select value from meta where key='locked_experiment'").fetchone())
    after=digest(LEDGER)
    assert before==after
    paths=[BUNDLE/"manifest.json",AUDIT,WORK/"experiments/agentic/ab_questions.json",
           WORK/"experiments/agentic/numeric_checks.py",ENCODER/"config.json",RERANKER/"config.json"]
    metadata=dict(python=sys.version,executable=sys.executable,os=platform.platform(),branch=git("branch","--show-current"),
                  head=git("rev-parse","HEAD"),worktree=str(WORK),tracked_modified=git("ls-files","-m"),
                  staged=git("diff","--cached","--name-only"),
                  untracked=[p for p in git("ls-files","--others","--exclude-standard") if not p.startswith("experiments/measure/")],
                  corpus_path=str(BUNDLE),corpus=manifest,hashes={str(p):digest(p) for p in paths},encoder=str(ENCODER),
                  reranker=str(RERANKER), model_weight_hashes={str(p):digest(p) for base in (ENCODER,RERANKER)
                        for p in base.glob("*.safetensors")},audit_count=len(audit["tables"]),
                  packages={n:importlib.metadata.version(n) for n in ("numpy","torch","sentence-transformers","beautifulsoup4","jsonschema")},
                  ledger=dict(path=str(LEDGER),before=before,after=after,**ledger),executed=executed,
                  provider_modules_loaded=[m for m in sys.modules if "codex_generation" in m or "capped_codex" in m],
                  no_generation_provider_calls=True)
    assert not metadata["provider_modules_loaded"]
    save(out,"environment.json",metadata)


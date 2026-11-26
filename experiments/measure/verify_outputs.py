"""Aggregate and check a completed offline measurement run."""
from collections import Counter
import sys
from common import HERE, digest, read, save

def run(out):
    def get(name):
        return read(out/(name+".json"))
    results=get("retrieval")
    table_data=get("tables-dom-normalized")
    env=get("environment")
    assert results["q2_baseline_parity"] and not env["provider_modules_loaded"]
    assert env["ledger"]["before"]==env["ledger"]["after"]
    assert len(table_data["records"])==50
    totals={}
    for k in ("8","14"):
        totals[k]={}
        for arm in "ABCD":
            total=Counter()
            for row in results["cases"]:
                counts = row["arms"][arm]["scores"][k]
                assert counts["returned"]==int(k)
                total.update(counts)
            totals[k][arm]=dict(total)
    row_match=Counter()
    alignment_problems=[]
    counts_by_col=Counter()
    for t in table_data["records"]:
        for row in t["rows"]:
            positions=[{r for r,c in cell["DOM_coordinates"] if c==cell["indexed"]["column"]} for cell in row["cells"]]
            joint=set.intersection(*positions) if positions else set()
            status="unverified" if not positions or any(not p for p in positions) else "linked_to_same_row" if joint else "mixed_dom_rows"
            row_match[status]+=1
            if status!="linked_to_same_row":
                alignment_problems.append(dict(arxiv_id=t["arxiv_id"],table_id=t["table_id"],chunk_id=row["chunk_id"],status=status))
        if t.get("targeted_q3"):
            for row in t["rows"]:
                for cell in row["cells"]:
                    counts_by_col[(t["table_id"],cell["status"])]+=1
    assert all(not p.startswith("experiments/measure/") for p in env["tracked_modified"])
    save(out,"study-summary.json",dict(retrieval_totals=totals,table_row_alignment=dict(row_match),alignment_problems=alignment_problems,
                q3_cell_status=[dict(table=key[0],status=key[1],count=n) for key,n in counts_by_col.items()],
                input_files={p.name:digest(p) for p in sorted(out.glob("*.json"))}))
if __name__=="__main__":
    run(HERE/sys.argv[1])


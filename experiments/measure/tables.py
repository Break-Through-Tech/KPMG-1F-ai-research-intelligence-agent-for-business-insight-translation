"""Compare audited indexed table cells with hash-matched original DOM structure."""
from collections import Counter, defaultdict
import gzip
import hashlib
from pathlib import Path
import re
import unicodedata
from bs4 import NavigableString, Tag

from bs4 import BeautifulSoup

from common import MAIN, save

HTML_ROOTS = (MAIN / "data/html", Path("D:/KPMG-library-data/html-cache"))
IS_NUMERIC = re.compile(r"^[+−–-]?[0-9][0-9.,]*(?:[%×x]|[–-][0-9.,]+%?)?$")

def canonical(text):
    text = unicodedata.normalize("NFKC", text).replace("−","-")
    return re.sub(r"\s+", "", text).casefold()

def plain(tag):
    parts = []
    for child in tag.descendants:
        if isinstance(child, Tag) and child.name == "math":
            alt = child.get("alttext") or child.find("annotation", encoding="application/x-tex")
            parts.append(str(alt) if isinstance(alt,str) else alt.get_text() if alt else child.get_text(" ",strip=True))
        elif isinstance(child, NavigableString) and not child.find_parent("math"):
            if child.strip():
                parts.append(child.strip())
    return " ".join(parts)

def local_source(arxiv, expected):
    for base in HTML_ROOTS:
        for suffix in (".html", ".html.gz"):
            path = base / (arxiv + suffix)
            if not path.is_file():
                continue
            raw = path.read_bytes()
            if path.suffix == ".gz":
                raw = gzip.decompress(raw)
            for data in (raw, raw.replace(b"\r\n", b"\n")):
                if hashlib.sha256(data).hexdigest() == expected:
                    return path, BeautifulSoup(data.decode("utf-8"),"html.parser")
    return None, None

def grid(table):
    entries = {}
    rows = [r for r in table.find_all("tr") if r.find_parent("table") is table]
    for y, row in enumerate(rows):
        x = 0
        for cell in row.find_all(["td","th"],recursive=False):
            while (y,x) in entries:
                x += 1
            span_x = max(1,int(cell.get("colspan","1")))
            span_y = max(1,int(cell.get("rowspan","1")))
            for j in range(y,y+span_y):
                for i in range(x,x+span_x):
                    entries[j,i] = cell
            x += span_x
    return rows,entries

def locate(table_id, group, dom):
    locator = dom.find(id=table_id)
    if locator:
        candidates = [locator] if locator.name=="table" else locator.find_all("table")
        if len(candidates)==1:
            return candidates[0]
    else:
        candidates = []
    anchor_counts = Counter()
    anchors = {c.get("source_id") for p in group for c in p["table_cells"] if c.get("source_id")}
    for sid in anchors:
        cell = dom.find(id=sid)
        table = cell.find_parent("table") if cell else None
        if table and (not candidates or any(table is t for t in candidates)):
            anchor_counts[id(table)] += 1
            candidates += [] if any(table is t for t in candidates) else [table]
    ranked = sorted(candidates,key=lambda c:-anchor_counts[id(c)])
    if ranked and anchor_counts[id(ranked[0])] and (len(ranked)==1 or anchor_counts[id(ranked[0])]>anchor_counts[id(ranked[1])]):
        return ranked[0]
    return None

def inspect(key, group, audit, cache):
    arxiv, table_id = key.split("#",1)
    first = group[0]
    sha = first["source_sha256"]
    if (arxiv,sha) not in cache:
        cache[arxiv,sha] = local_source(arxiv,sha)
    path, dom = cache[arxiv,sha]
    result = dict(arxiv_id=arxiv, table_id=table_id, source_url=first["source_url"], source_sha256=sha,
                  source_file=str(path) if path else None, header_provenance=first.get("header_provenance"),
                  audit_status=audit.get("status"), audit_original_rows_identical=audit.get("rows_identical_to_bundle"),
                  caption=first.get("caption"), reviewed=False, headers=[],rows=[],unindexed_numeric_cells=[])
    if dom is None:
        return dict(result,status="unverified",reason="No hash-matched local source.")
    table = locate(table_id,group,dom)
    if table is None:
        return dict(result,status="unverified",reason="No unambiguous source table locator.")
    trs, g = grid(table)
    header_rows = set()
    for pos, tr in enumerate(trs):
        tags=tr.find_all(["th","td"],recursive=False)
        if tr.find_parent("thead") or (tags and all(c.name=="th" or "ltx_th" in c.get("class",[]) for c in tags)):
            header_rows.add(pos)
        else:
            break
    positions = defaultdict(list)
    for (row,col), tag in g.items():
        if tag.get("id"):
            positions[tag["id"]].append((row,col))
    for header in first["table_headers"]:
        column, sid = header["column"], header.get("source_id")
        coords = positions.get(sid,[])
        cells = list({id(g[r,column]):g[r,column] for r in header_rows if (r,column) in g}.values())
        path_labels = [plain(tag) for tag in cells if plain(tag)]
        tag = g[coords[0]] if coords else g.get((0,column))
        if tag is None:
            status="unverified_locator"
        elif canonical(header["text"]) not in {canonical(plain(tag)),canonical(" ".join(path_labels)),canonical(" / ".join(path_labels))}:
            status="mismatch"
        elif coords and not any(col==column for row,col in coords):
            status="mismatch_column"
        elif not header_rows or not any(row in header_rows for row,_ in coords):
            status="text_agrees_role_unverified"
        elif any(IS_NUMERIC.fullmatch(canonical(label)) for label in path_labels) and len(path_labels)>1:
            status="numeric_in_grouped_header_review"
        elif len(set(path_labels))>1 and canonical(header["text"]) not in {canonical(" ".join(path_labels)),canonical(" / ".join(path_labels))}:
            status="text_agrees_group_path_unverified"
        else:
            status="agrees"
        result["headers"].append(dict(indexed=header,dom_text=plain(tag) if tag else None,
                                      DOM_header_path=path_labels,DOM_coordinates=coords,status=status))
    indexed_ids = {c.get("source_id") for row in group for c in row["table_cells"]}
    result["unindexed_numeric_rows"] = []
    verified_rows = set()
    for indexed in group:
        entries = []
        for cell in indexed["table_cells"]:
            sid=cell.get("source_id")
            coords=positions.get(sid,[])
            tag=g[coords[0]] if coords else None
            if tag is None:
                status="unverified_locator"
            elif not any(col==cell["column"] for row,col in coords):
                status="mismatch_column"
            elif canonical(cell["text"])!=canonical(plain(tag)):
                status="mismatch_text"
            else:
                status="agrees"
                verified_rows.update(row for row,col in coords)
            entries.append(dict(indexed=cell,DOM_coordinates=coords,DOM_text=plain(tag) if tag else None,status=status))
        first_cell = entries[0]
        row_label = "agrees" if first_cell["status"]=="agrees" and canonical(indexed["row_label"])==canonical(first_cell["DOM_text"]) else "unverified_or_different"
        result["rows"].append(dict(chunk_id=indexed["chunk_id"], row=indexed["table_row"],row_label=indexed["row_label"],
                                   row_label_status=row_label,cells=entries))
    for (y,x),tag in g.items():
        sid=tag.get("id")
        if y in verified_rows and sid and sid not in indexed_ids and (y,x)==positions[sid][0] and IS_NUMERIC.fullmatch(canonical(plain(tag))):
            result["unindexed_numeric_cells"].append(dict(source_id=sid,row=y,col=x,text=plain(tag)))
    for y in range(len(trs)):
        if y in verified_rows or y in header_rows:
            continue
        numeric = [dict(source_id=tag.get("id"),column=x,text=plain(tag)) for (row,x),tag in g.items()
                   if row==y and IS_NUMERIC.fullmatch(canonical(plain(tag))) and tag.get("id") not in indexed_ids]
        if numeric:
            result["unindexed_numeric_rows"].append(dict(row=y,cells=numeric))
    result["DOM_table_id"]=table.get("id")
    result["DOM_markup_header_rows"]=sorted(header_rows)
    result["DOM_rows"]=len(trs)
    statuses=[h["status"] for h in result["headers"]]+[c["status"] for row in result["rows"] for c in row["cells"]]
    result["status"]="mismatch" if any(s.startswith("mismatch") for s in statuses) else (
        "structural_agreement" if statuses and all(s=="agrees" for s in statuses) else "unverified")
    return result

def run(out,data):
    _,audit,_,parents=data
    by_table=defaultdict(list)
    for p in parents:
        if p.get("representation")=="linearized_table":
            by_table[p["arxiv_id"]+"#"+p["table_id"]].append(p)
    strata=defaultdict(list)
    for key, group in by_table.items():
        if key in audit["tables"]:
            strata[group[0]["header_provenance"]].append(key)
    # Deterministic sample by SHA-256 rank within each provenance stratum, with targeted Q3 tables included.
    targets={"2602.00931v2#S3.T2","2602.00931v2#S4.T4.fig1"}
    caps={"latexml_guessed":24,"first_row_assumed":23,"html_th_markup":3}
    selected=[]
    for name,keys in sorted(strata.items()):
        mandatory=sorted(set(keys)&targets)
        rest=sorted(set(keys)-targets,key=lambda k:hashlib.sha256(("kpmg-header-v1/"+k).encode()).hexdigest())
        selected.extend(mandatory+rest[:max(0,caps.get(name,0)-len(mandatory))])
    cache={}
    records=[]
    for key in selected:
        record=inspect(key,by_table[key],audit["tables"][key],cache)
        record["targeted_q3"]=key in targets
        records.append(record)
    totals={}
    for name in strata:
        cohort=[r for r in records if r["header_provenance"]==name]
        totals[name]=dict(population=len(strata[name]),sampled=len(cohort),
                          tables=dict(Counter(r["status"] for r in cohort)),
                          headers=dict(Counter(h["status"] for r in cohort for h in r["headers"])),
                          cells=dict(Counter(c["status"] for r in cohort for row in r["rows"] for c in row["cells"])),
                          labels=dict(Counter(row["row_label_status"] for r in cohort for row in r["rows"])),
                          unindexed_numeric_cells_on_located_rows=sum(len(r["unindexed_numeric_cells"]) for r in cohort),
                          unindexed_numeric_rows=sum(len(r.get("unindexed_numeric_rows",[])) for r in cohort))
    save(out,"tables-dom-normalized.json",dict(totals=totals,records=records,
        method="Structural DOM comparison only. Rendered MathML and its duplicate TeX annotation are represented once; grouped header paths follow DOM spans. Header roles without semantic markup and composite path ambiguities stay unverified. No human adjudication."))


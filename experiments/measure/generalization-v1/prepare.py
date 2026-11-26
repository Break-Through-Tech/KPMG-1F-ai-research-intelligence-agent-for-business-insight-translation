"""Verify local original sources and reproducibly seal a source-first sample."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import BUNDLE, ENCODER, PIN, RERANKER, WORK, digest, read, rows
from tables import canonical, grid, local_source, plain

# Known open debugging and evaluation material. No sealed questions/answers are inputs.
EXCLUDED = set("2602.00931 2412.18690 2510.02243 2402.01622 2412.14470 "
               "2506.23273 2602.00933 2602.07294 2508.03553 2402.12713 "
               "2604.00324 2402.08416 2408.13687 2603.00829 2605.00276".split())


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write("\n")


def anchors(text, value):
    return canonical(value.replace("’", "'")) in canonical(text.replace("’", "'"))


def check_point(parent, selector, expected, dom):
    locator = urlsplit(parent["source_url"]).fragment
    source = dom.find(id=locator)
    if source is None:
        raise ValueError(f"Missing original section {locator}")
    if not parent.get("table_id"):
        if not anchors(parent["text"], selector) or not anchors(plain(source), selector):
            raise ValueError(f"Unmatched indexed/original anchor {selector}")
        return dict(point=expected, chunk_id=parent["chunk_id"], original_locator=locator,
                    source_url=parent["source_url"], source_sha256=parent["source_sha256"],
                    indexed_excerpt=parent["text"], original_anchor=selector)
    table = source if source.name == "table" else source.find("table")
    if not table:
        raise ValueError("Missing original table")
    _, cells = grid(table)
    identities = {}
    for (row, col), cell in cells.items():
        identities.setdefault(cell.get("id"), set()).add((row, col))
    headers, row = parent["table_headers"], parent["table_cells"]
    columns = [i for i, col in enumerate(headers) if col["text"] in selector.split("|")]
    if len(columns) != len(selector.split("|")):
        raise ValueError("Missing table header")
    group = {}
    for i in [0, *columns]:
        cell = row[i]
        header = headers[i]
        value_node = dom.find(id=cell["source_id"])
        hs = header.get("source_ids", [header["source_id"]])
        header_path = " / ".join(plain(dom.find(id=ref)) for ref in hs)
        if not anchors(plain(value_node), cell["text"]) or not anchors(cell["text"], plain(value_node)):
            raise ValueError(f"Value differs at {cell['source_id']}")
        if canonical(header_path) != canonical(header["text"]):
            raise ValueError(f"Header differs at {hs}")
        if not any(all(any(x == col and y < ordinal for y, x in identities.get(ref, ())) for ref in hs)
                   for ordinal, col in identities.get(cell["source_id"], ())):
            raise ValueError("Header and value are not in the same source column")
        group[header["text"]] = dict(value=cell["text"], cell_id=cell["source_id"], header_ids=hs)
    anchor_row = identities.get(row[0]["source_id"], set())
    if not all(any(y == z for y, _ in anchor_row for z, _ in identities[group[headers[i]["text"]]["cell_id"]])
               for i in columns):
        raise ValueError("Row label and value are not in the same source row")
    return dict(point=expected, chunk_id=parent["chunk_id"], source_url=parent["source_url"],
                source_sha256=parent["source_sha256"], original_locator=locator,
                indexed_excerpt=parent["text"], cells=group)


def build():
    rules = read(HERE / "rules.json")
    snapshot = read(HERE.parent / "generalization-preselection-snapshot.json")
    if any(digest(WORK / name) != sha for name, sha in snapshot["runtime_sha256"].items()):
        raise ValueError("Runtime differs from preselection snapshot")
    if digest(BUNDLE / "parents.jsonl") != PIN:
        raise ValueError("Unexpected corpus")
    parents = {r["chunk_id"]: r for r in rows(BUNDLE / "parents.jsonl")}
    paper_hashes = {}
    for r in parents.values():
        if r.get("source_sha256"):
            paper_hashes.setdefault(r["arxiv_id"], set()).add(r["source_sha256"])
    pool = list(rows(HERE / "candidates.jsonl"))
    seed = rules["seed"]
    papers, audit, available = {}, [], []
    for candidate in pool:
        sources = [parents[cid] for cid, _, _ in candidate["points"]]
        ids = sorted({r["arxiv_id"] for r in sources})
        stability = [candidate["type"], ids, sorted({(r["chunk_id"], p[1])
                     for r, p in zip(sources, candidate["points"], strict=True)})]
        rank = hashlib.sha256((seed + json.dumps(stability, separators=(",", ":"))).encode()).hexdigest()
        entry = dict(id=rank[:16], rank_sha256=rank, category=candidate["type"], papers=ids,
                     source_ids=[s["chunk_id"] for s in sources], status="reserve")
        audit.append(entry)
        try:
            if {re.sub(r"v\d+$", "", ident) for ident in ids} & EXCLUDED:
                raise ValueError("Known open development paper")
            verified = []
            for parent, (_, selector, expected) in zip(sources, candidate["points"], strict=True):
                if not parent.get("source_sha256"):
                    known = paper_hashes.get(parent["arxiv_id"], set())
                    if len(known) != 1:
                        raise ValueError(f"Source digest is ambiguous or absent for {parent['arxiv_id']}")
                    parent = parent | {"source_sha256": next(iter(known))}
                key = (parent["arxiv_id"], parent["source_sha256"])
                if key not in papers:
                    papers[key] = local_source(*key)[1]
                if papers[key] is None:
                    raise ValueError(f"No hash-matched local original for {key[0]}")
                verified.append(check_point(parent, selector, expected, papers[key]))
            available.append((entry, candidate, verified))
        except ValueError as error:
            entry.update(status="excluded", reason=str(error))
    selected, used, counts = [], set(), Counter()
    for _ in range(max(rules["quotas"].values())):
        for category, quota in rules["quotas"].items():
            if counts[category] == quota:
                continue
            options = [x for x in available if x[0]["category"] == category and x[0]["status"] == "reserve"]
            for entry, candidate, verified in sorted(options, key=lambda x: x[0]["rank_sha256"]):
                if used.intersection(entry["papers"]):
                    entry.update(status="excluded", reason="Paper already selected")
                    continue
                entry["status"] = "selected"
                used.update(entry["papers"])
                selected.append((entry, candidate, verified))
                counts[category] += 1
                break
    return rules, audit, counts, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    rules, audit, counts, selected = build()
    print(json.dumps(dict(counts=counts, totals=Counter(x["status"] for x in audit),
                          excluded=[x for x in audit if x["status"] == "excluded"]), indent=2))
    if not args.seal:
        return
    if dict(counts) != rules["quotas"]:
        raise SystemExit("Quotas are incomplete; no seal produced")
    order = sorted(selected, key=lambda x: hashlib.sha256(
        (rules["seed"] + ":order:" + x[0]["id"]).encode()).hexdigest())
    question_rows, references, sequence = [], [], []
    for i, (row, candidate, points) in enumerate(order, 1):
        qid = f"G{i:02}"
        question_rows.append(dict(id=qid, text=candidate["q"]))
        required = row["category"] in {"conflict", "refusal", "table"}
        references.append(dict(id=qid, category=row["category"], papers=row["papers"],
                               expected="refusal" if row["category"] == "refusal" else "answer",
                               required_points=points, local_original_checked=True, human_verified=False,
                               second_human_review="pending" if required else "not_requested",
                               audit_id=row["id"]))
        sequence.append(dict(id=qid, order=["A", "B"] if i % 2 else ["B", "A"]))
    save("questions.json", question_rows)
    save("references.json", references)
    save("sampling-audit.json", dict(pool=audit, excluded_known_open=sorted(EXCLUDED), selected_counts=counts,
                                     sealed_benchmark_access=False))
    save("schedule.json", sequence)
    binary = Path.home() / "AppData/Local/OpenAI/Codex/bin/f71a721e0e6193a9/codex.exe"
    environment = {"encoder": str(ENCODER), "reranker": str(RERANKER), "cli": str(binary),
                   "sha256": {str(path): digest(path) for base in (ENCODER, RERANKER)
                              for path in sorted(base.iterdir()) if path.is_file()}}
    environment["sha256"][str(binary)] = digest(binary)
    save("execution-assets.json", environment)
    saved = ["questions.json", "references.json", "sampling-audit.json", "schedule.json", "rules.json",
             "candidates.jsonl", "prepare.py", "offline_harness.py", "test_harness.py", "execution-assets.json"]
    save("seal.json", dict(schema=1, files={name: digest(HERE / name) for name in saved},
                           preselection_snapshot=digest(HERE.parent / "generalization-preselection-snapshot.json"),
                           corpus_parent_sha256=PIN, provider_invocations=0))


if __name__ == "__main__":
    main()

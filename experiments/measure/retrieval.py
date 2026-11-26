"""Matched four-arm, no-generation retrieval study."""
import importlib
import re
import sys
from collections import defaultdict
from time import perf_counter

from common import AUDIT, BUNDLE, ENCODER, EXPORT, MAIN, RERANKER, digest, pinned, read, rows, save

def norm(text):
    return " ".join(text.split())

def questions(spec, parents):
    ids = {p["chunk_id"]: p for p in parents}
    by_paper = defaultdict(list)
    for p in parents:
        by_paper[p["arxiv_id"]].append(p)
    q2 = spec["questions"]["Q2"]
    qparts = []
    for part in q2["required_points"]:
        candidates = [ids[i] for i in part["source_chunks"]]
        # A source ID is counted as gold only when every literal anchor matches that passage.
        anchored = [p for p in candidates if all(a in p["text"] for a in part["anchors"])]
        assert anchored, part["id"]
        qparts.append(dict(id=part["id"], papers=sorted({p["arxiv_id"] for p in anchored}),
                           gold=[p["chunk_id"] for p in anchored], anchors=part["anchors"]))
    eligible = [dict(id="Q2", question=q2["text"], parts=qparts, label="pinned reviewed source anchors")]
    dev = read(MAIN / "evaluation/evidence_eval_v1/development.json")
    eligibility = []
    for case in dev["cases"]:
        assert case["split"] == "development"
        parts = []
        for fact in case["required_facts"]:
            matches = []
            papers = set()
            for option in fact["support_options_any_of"]:
                paper, quote = option["arxiv_id"], norm(option["quote"])
                papers.add(paper)
                matches.extend(p["chunk_id"] for p in by_paper[paper] if quote in norm(p["text"]))
            parts.append(dict(id=fact["fact_id"], papers=sorted(papers), gold=sorted(set(matches)),
                              original_ids=[o["chunk_id"] for o in fact["support_options_any_of"]],
                              quotes=[o["quote"] for o in fact["support_options_any_of"]]))
        supported = bool(parts) and all(part["gold"] for part in parts)
        eligibility.append(dict(id=case["query_id"], eligible=supported, question=case["query"], parts=parts,
                                papers_absent=sorted({p for item in parts for p in item["papers"] if not by_paper[p]}),
                                reason=None if supported else "At least one fact lacks a literal same-version demo passage, or no facts are asserted."))
        if supported:
            for part in parts:
                part["papers"] = sorted({ids[i]["arxiv_id"] for i in part["gold"]})
            eligible.append(dict(id=case["query_id"], question=case["query"], parts=parts,
                                 label="development; source anchors rechecked; provisional"))
    # Only paper metadata is projected. KIR is an independent evaluation set, so its questions
    # and answer contents are excluded from development and never passed to retrieval.
    kir = MAIN / "evaluation/independent-research-100/answer-key.jsonl"
    kir_meta = [(r["id"], tuple(r["expected_relevant_papers"])) for r in rows(kir)]
    all_papers = {p for _, papers in kir_meta for p in papers}
    overlap = dict(records=len(kir_meta), expected_papers=len(all_papers),
                   exact_version_overlap=sorted(all_papers & set(by_paper)),
                   base_id_overlap=sorted({re.sub(r"v\d+$", "", p) for p in all_papers}
                                          & {re.sub(r"v\d+$", "", p) for p in by_paper}),
                   complete_overlap_questions=sum(bool(ps) and set(ps) <= set(by_paper) for _, ps in kir_meta),
                   selected=0, reason="Independent benchmark has no authorized development split. Paper metadata only.")
    return eligible, eligibility, overlap

def instrument(module, replacements):
    source = module.__file__
    text = open(source, encoding="utf-8").read()
    for old, new in replacements:
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    exec(compile(text, source, "exec"), module.__dict__)

def paper_queries(query, parents):
    # Build names from index titles only. Never use rubric names, chunk IDs or answers.
    names = defaultdict(set)
    for p in parents:
        title = p["title"]
        head = re.split(r"[:\u2013\u2014]", title, maxsplit=1)[0].strip()
        candidates = [title, head] if len(head.split()) <= 4 else [title]
        candidates += [word for word in re.findall(r"[A-Za-z][A-Za-z0-9-]+", head)
                       if re.search(r"[a-z][A-Z]|[A-Z]{2}|[A-Za-z]-[A-Za-z]", word)]
        for name in candidates:
            if len(name) >= 5:
                names[name].add(p["arxiv_id"])
    found = []
    for name, papers in sorted(names.items(), key=lambda item: (-len(item[0]), item[0].casefold())):
        match = re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", query, re.I)
        if match and len(papers) == 1:
            paper = next(iter(papers))
            if paper not in {item[2] for item in found}:
                found.append((match.start(), match.end(), paper, query[match.start():match.end()]))
    found.sort()
    if len(found) < 2:
        return [query]
    # Keep question wording, constrain each search to one named target by removing the other names.
    split = []
    for paper in found[:3]:
        masked = query
        for other in reversed(found):
            if other != paper:
                masked = masked[:other[0]] + " " + masked[other[1]:]
        masked = re.sub(r"\bcompare\s+(.+?)\s+and\s*(?=[,?.]|$)", r"\1", masked, flags=re.I)
        masked = re.sub(r"\bcompare\s+and\s+", "", masked, flags=re.I)
        split.append(f"{paper[3]}. {norm(masked)}")
    return [query, *split[:2]]

def merge(orders):
    seen, result = set(), []
    for rank in range(max(map(len, orders))):
        for order in orders:
            if rank < len(order) and order[rank] not in seen:
                result.append(order[rank])
                seen.add(order[rank])
    return result

def metrics(case, returned, ids):
    required = {p for part in case["parts"] for p in part["papers"]}
    gold = {i for part in case["parts"] for i in part["gold"]}
    kept = set(returned)
    return dict(required_papers=len(required), papers_found=len(required & {ids[i]["arxiv_id"] for i in returned}),
                gold_passages=len(gold), gold_found=len(gold & kept),
                parts=len(case["parts"]), parts_found=sum(bool(kept.intersection(part["gold"])) for part in case["parts"]),
                returned=len(returned), off_target_paper=sum(ids[i]["arxiv_id"] not in required for i in returned),
                unlabelled_passages=len(kept - gold))

def run(out, data):
    manifest, audit, spec, parents = data
    cases, eligibility, overlap = questions(spec, parents)
    save(out, "eligibility.json", dict(development=eligibility, kir=overlap, selected=cases))
    print("Retrieval questions:", [x["id"] for x in cases], flush=True)
    sys.path.insert(0, str(EXPORT))
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from src.experimental.search_index import SearchViewIndex
    from src.experimental.b2 import open_b2
    from src.experimental import retriever, balanced_retriever
    torch.set_num_threads(4)
    encoder = SentenceTransformer(str(ENCODER), local_files_only=True, device="cpu")
    cross = CrossEncoder(str(RERANKER), local_files_only=True, device="cpu")
    deployed, identity, _, _ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, encoder=encoder, reranker=cross)
    baseline_q2 = [p["chunk_id"] for p in deployed(cases[0]["question"], 14)]
    original_identity = identity()
    # Only the shortlist constant changes. Two debug fields are captured without changing the order.
    instrument(retriever, [("docs=sorted(docscore,key=lambda d:(-docscore[d],d))[:3]",
                            "all_docs=sorted(docscore,key=lambda d:(-docscore[d],d));docs=all_docs[:MEASURE_CAP]"),
                           ("'paper_candidates':docs}", "'paper_candidates':docs,'paper_order':all_docs}")])
    instrument(balanced_retriever, [("        selected=[order[0]]", "        fused_order=order.copy()\n        selected=[order[0]]"),
                                   ("'balanced_prefix':selected}", "'balanced_prefix':selected,'hybrid_order':hybrid,'paper_order':debug['paper_order'],'fused_order':fused_order}")])
    engine = balanced_retriever.FacetRetriever(SearchViewIndex(BUNDLE, model=encoder), cross, encoder)
    ids = engine.byid
    cache = {}
    def rank(query, cap):
        key = (query, cap)
        if key not in cache:
            started = perf_counter()
            retriever.MEASURE_CAP = cap
            vector = np.asarray(encoder.encode([query], show_progress_bar=False), dtype=np.float32)[0]
            order, debug = engine.rank_facets(query, vector)
            cache[key] = dict(query=query, cap=cap, order=order, seconds=perf_counter()-started, **debug)
        return cache[key]
    assert rank(cases[0]["question"], 3)["order"][:14] == baseline_q2
    results = []
    for case in cases:
        split = paper_queries(case["question"], parents)
        row = dict(id=case["id"], question=case["question"], split=split, arms={})
        for label, cap, decompose in [("A",3,False),("B",6,False),("C",3,True),("D",6,True)]:
            searches = [rank(q,cap) for q in (split if decompose else [case["question"]])]
            output = merge([s["order"] for s in searches])
            row["arms"][label] = dict(query_count=len(searches), searches=[(s["query"],s["cap"]) for s in searches],
                                     rank_1_to_14=output[:14],
                                     scores={k:metrics(case, output[:k],ids) for k in (8,14)})
        print("Completed",case["id"],flush=True)
        results.append(row)
    save(out,"retrieval.json",dict(identity=original_identity, encoder=str(ENCODER), reranker=str(RERANKER),
                                  export=str(EXPORT), q2_baseline_parity=True, cases=results,
                                  searches=list(cache.values()),
                                  evidence_catalog={i:{k:ids[i].get(k) for k in ("arxiv_id","title","section","source_url")}
                                                    for row in results for a in row["arms"].values() for i in a["rank_1_to_14"]}))


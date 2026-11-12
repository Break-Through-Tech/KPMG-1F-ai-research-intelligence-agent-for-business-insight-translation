import re

from .retriever import Lexical

NUMBERS = re.compile(r"\b\d+(?:\.\d+)?\s*(?:\\?%|percent\b)", re.I)
RESULTS = re.compile(r"\b(results?|evaluation|experiments?|experimental|performance|methods?|methodology)\b", re.I)


def result_companion(question, hits, parents):
    """Find a quantitative results passage from the strongest retrieved paper."""
    if len(hits) < 3 or not re.search(r"\b(how often|success rate|pass rate|accuracy|benchmark scores?)\b", question, re.I):
        return None
    paper = hits[0].get("arxiv_id")
    if sum(hit.get("arxiv_id") == paper for hit in hits[:3]) < 2:
        return None
    used = {hit["chunk_id"] for hit in hits}
    candidates = [p for p in parents if p.get("arxiv_id") == paper
                  and p["chunk_id"] not in used
                  and RESULTS.search(p.get("section", "") + " " + p.get("subsection", ""))
                  and NUMBERS.search(p["text"])]
    if not candidates:
        return None
    scores = Lexical([p["text"] for p in candidates]).score(question)
    best = max(range(len(candidates)),
               key=lambda i: scores[i] * (1 + min(5, len(NUMBERS.findall(candidates[i]["text"]))) / 10))
    return candidates[best] if scores[best] > 0 else None


def with_result_coverage(retrieve, parents):
    """Keep the evidence budget while reserving one slot for benchmark results."""
    def search(question, top_k):
        hits = retrieve(question, top_k)
        companion = result_companion(question, hits, parents)
        if companion is None:
            return hits
        return hits[:top_k-1] + [companion]
    return search

DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,|\s)", re.I)


def with_study_scope(question, hits, parents):
    """For present-day comparisons, retain an experimental date when available."""
    if len(hits) < 2 or not re.search(r"\b(still|currently|current|today|latest|now)\b", question, re.I):
        return hits
    paper = hits[0].get("arxiv_id")
    candidates = [p for p in parents if p.get("arxiv_id") == paper and DATE.search(p["text"])
                  and re.search(r"\b(query|queries|tested|testing|ran|run|evaluated|evaluation)\b", p["text"], re.I)
                  and RESULTS.search(p.get("section", "") + " " + p.get("subsection", ""))]
    if not candidates:
        return hits
    best = max(candidates, key=lambda p: len(DATE.findall(p["text"])))
    if best["chunk_id"] in {p["chunk_id"] for p in hits}:
        return hits
    return hits[:-1] + [best]

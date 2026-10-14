"""Baseline compatibility entry point using the shared, unapproved research pipeline.

Run from the repository root: ``python -m src.agent --query '...'``.
Provider configuration is the same as main.py; imports never create a client.
"""
import argparse
import json

from src.generation import create_generate
from src.research_pipeline import run_research
from src.summarization import prompt_provenance, summarize


def source_location(hit):
    """Retain the actual retrieved source; HTML has sections, not PDF pages."""
    if hit.get("source") == "html":
        url = hit.get("source_url") or hit.get("html_url")
        section = " / ".join(str(hit[k]) for k in ("section", "subsection") if hit.get(k))
        return f"{url}" + (f" ({section})" if section else "")
    page = hit.get("page_number")
    url = hit.get("source_url") or hit.get("pdf_url")
    return f"{url}" + (f" (p.{page})" if page is not None else "")


def format_context(hits):
    """Readable evidence display; generation uses the shared bounded prompt."""
    return "\n\n".join(
        f"[Source: {hit['title']} (arXiv:{hit['arxiv_id']}) — {source_location(hit)}]\n{hit['text']}"
        for hit in hits
    )


def ask_question(question: str, top_k: int = 5, *, retrieve=None, generate=None,
                 industry=None) -> dict:
    """Return a cited draft plus the full workflow, never automatic approval.

    Optional injected adapters support offline verification. Business translation
    requires explicit industry context; provider construction is deferred until
    nonempty evidence actually needs generation.
    """
    if retrieve is None:
        from main import persistent_retrieve
        retrieve = persistent_retrieve
    provenance = {"entry_point": "src.agent", "generation": None}
    active_generate = generate

    def get_generate():
        nonlocal active_generate
        if active_generate is None:
            active_generate, settings = create_generate()
            provenance["generation"] = {**settings, **prompt_provenance()}
        elif provenance["generation"] is None:
            provenance["generation"] = {"execution": "injected_adapter", **prompt_provenance()}
        return active_generate

    def summary(query, passages):
        return summarize(query, passages, generate=get_generate())

    request = {"query": question, "top_k": top_k}
    translation = None
    if industry is not None:
        request["industry"] = industry
        from src.business_translation import translate
        def translation(summary_result, passages, *, industry):
            return translate(summary_result, passages, industry=industry, generate=get_generate())

    result = run_research(request, retrieve=retrieve, summarize_fn=summary,
                          translate_fn=translation, provenance=provenance)
    evidence = {hit["chunk_id"]: hit for hit in result["evidence"]}
    claims = result["summary"]["claims"]
    answer = []
    cited = []
    for claim in claims:
        labels = []
        for chunk_id in claim["chunk_ids"]:
            hit = evidence[chunk_id]
            labels.append(f"{hit['title']} — {source_location(hit)}")
            if chunk_id not in cited:
                cited.append(chunk_id)
        answer.append(f"{claim['text']} [{'; '.join(labels)}]")
    if not answer:
        answer = result["summary"]["limitations"] or ["Insufficient evidence to answer."]
    result["answer"] = "\n\n".join(answer)
    result["sources"] = [{**evidence[chunk_id], "page": evidence[chunk_id].get("page_number")}
                         for chunk_id in cited]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Baseline cited draft using shared provider settings")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--industry", help="Explicit business context for optional translation")
    args = parser.parse_args(argv)
    result = ask_question(args.query, args.top_k, industry=args.industry)
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(bool(result["summary"].get("error")))


if __name__ == "__main__":
    raise SystemExit(main())

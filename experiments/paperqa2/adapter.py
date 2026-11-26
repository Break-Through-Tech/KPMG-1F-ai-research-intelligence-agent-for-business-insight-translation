"""Standalone PaperQA2 pilot over copies of versioned KPMG passages."""
from argparse import ArgumentParser
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

PIN = "78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa"
MODEL = "chatgpt/gpt-6.1-sol"
LABEL = re.compile(r"\bKPMG\d+ chunk \d+\b")


def copy_corpus(parents, out, papers):
    data = parents.read_bytes()
    if sha256(data).hexdigest() != PIN:
        raise ValueError("Unexpected demo-100 corpus")
    selected = [row for row in map(json.loads, data.decode("utf-8-sig").splitlines())
                if row["arxiv_id"] in papers]
    if {row["arxiv_id"] for row in selected} != set(papers):
        raise ValueError("Missing exact paper version")
    with out.open("x", encoding="utf-8") as file:
        json.dump(dict(parent_sha256=PIN, records=selected), file, ensure_ascii=False)


def settings():
    from paperqa import Settings

    return Settings(llm=MODEL, summary_llm=MODEL, embedding="sparse",
                    answer={"evidence_k": 3, "answer_max_sources": 3, "evidence_skip_summary": True})


async def ingest(rows, config):
    from paperqa import Docs
    from paperqa.types import Doc, Text

    groups = defaultdict(list)
    for row in rows:
        groups[row["arxiv_id"]].append(row)
    docs, sources = Docs(), {}
    for i, (version, group) in enumerate(sorted(groups.items()), 1):
        doc = Doc(docname=f"KPMG{i}", dockey=version, citation=f"{group[0]['title']} (arXiv:{version})")
        texts = []
        for j, row in enumerate(group, 1):
            name = f"{doc.docname} chunk {j}"
            texts.append(Text(text=row["text"], name=name, doc=doc))
            sources[name] = row
        if not await docs.aadd_texts(texts, doc, settings=config):
            raise ValueError(f"Duplicate document {version}")
    return docs, sources


def format_answer(session, sources):
    from paperqa.prompts import CANNOT_ANSWER_PHRASE
    from paperqa.utils import get_citation_ids

    answer = session.answer.strip()
    if not answer or CANNOT_ANSWER_PHRASE.casefold() in answer.casefold():
        return {"query": session.question, "status": "insufficient_evidence", "answer": "", "citations": []}
    delivered = {context.text.name: context.text for context in session.contexts}
    context_ids = {context.id for context in session.contexts}
    if set(get_citation_ids(session.raw_answer)) - context_ids:
        raise ValueError("Unknown raw PaperQA citation")
    names = list(dict.fromkeys(LABEL.findall(answer)))
    if not names or any(name not in sources or name not in delivered for name in names):
        raise ValueError("No resolvable citations or citation outside supplied contexts")
    for name in names:
        row, text = sources[name], delivered[name]
        if text.doc.dockey != row["arxiv_id"] or text.text != row["text"]:
            raise ValueError("Citation content or version changed")
    return {"query": session.question, "status": "ok", "answer": answer, "citations": [
        {"marker": name, **{key: sources[name][key] for key in
         ("chunk_id", "arxiv_id", "source_url", "text")}} for name in names]}


async def ask(question, rows, *, llm_model, summary_llm_model=None):
    config = settings()
    docs, sources = await ingest(rows, config)
    session = await docs.aquery(question, settings=config, llm_model=llm_model,
                                summary_llm_model=summary_llm_model or llm_model)
    return format_answer(session, sources)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("parents", type=Path)
    parser.add_argument("copy", type=Path)
    parser.add_argument("papers", nargs="+")
    args = parser.parse_args()
    copy_corpus(args.parents, args.copy, args.papers)

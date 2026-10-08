from langchain_text_splitters import RecursiveCharacterTextSplitter
from urllib.parse import quote
from .pdf_parser import split_into_sections

# Sections most useful for business insight; others are kept but flagged
HIGH_VALUE = {"abstract", "introduction", "results", "result", "evaluation",
              "discussion", "limitations", "limitation", "conclusion",
              "conclusions", "future work", "applications", "application",
              "case study"}

VALUE_KW = ("abstract", "introduction", "result", "evaluation", "discussion", "limitation",
            "conclusion", "future", "application", "case study", "implication", "finding")


def chunk_html_sections(sections: list[dict], arxiv_id: str, title: str = "") -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800, chunk_overlap=250, separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks, idx = [], 0
    for sec in sections:
        anchor = sec.get("subsection_id") or sec.get("section_id") or ""
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        if anchor:
            html_url += "#" + quote(anchor, safe="")
        for piece in splitter.split_text(sec["text"]):
            body = piece.strip()
            if len(body) < 150:
                continue
            chunks.append({
                "chunk_id": f"{arxiv_id}_c{idx:04d}",
                "arxiv_id": arxiv_id,
                "page_number": None,                      # HTML has no pages
                "html_url": html_url,
                "section": sec["section"],
                "subsection": sec["subsection"],
                "high_value": any(k in sec["section"] or k in sec["subsection"] for k in VALUE_KW),
                "text": body,
                "text_with_context": f"{title} | {sec['section'].title()}"
                                     + (f" > {sec['subsection'].title()}" if sec["subsection"] else "")
                                     + f"\n\n{body}",
            })
            idx += 1
    return chunks


def chunk_document(pages_data, arxiv_id, title=""):
    sections, offsets = split_into_sections(pages_data)
    page_ranges = [(start, start + len(page["text"]), page["page"])
                   for (start, _), page in zip(offsets, pages_data)]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800, chunk_overlap=250,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks, idx = [], 0
    for sec in sections:
        if len(sec["text"].strip()) < 150:
            continue
        # Split each section at its original page boundaries before chunking.
        # Overlap stays within a page; short tails of a retained section survive.
        for page_start, page_end, page_number in page_ranges:
            start, end = max(sec["start"], page_start), min(sec["end"], page_end)
            if start >= end:
                continue
            page_text = sec["text"][start - sec["start"]:end - sec["start"]]
            for piece in splitter.split_text(page_text):
                body = piece.strip()
                if not body:
                    continue
                chunks.append({
                    "chunk_id": f"{arxiv_id}_c{idx:04d}",
                    "arxiv_id": arxiv_id,
                    "page_number": page_number,
                    "section": sec["section"],
                    "high_value": sec["section"] in HIGH_VALUE,
                    "text": body,
                    "text_with_context": f"{title} | {sec['section'].title()}\n\n{body}",
                })
                idx += 1
    return chunks

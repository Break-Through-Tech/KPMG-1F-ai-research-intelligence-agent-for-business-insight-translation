from langchain_text_splitters import RecursiveCharacterTextSplitter
from .pdf_parser import split_into_sections, page_for

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
        for piece in splitter.split_text(sec["text"]):
            body = piece.strip()
            if len(body) < 150:
                continue
            chunks.append({
                "chunk_id": f"{arxiv_id}_c{idx:04d}",
                "arxiv_id": arxiv_id,
                "page_number": None,                      # HTML has no pages
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
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800, chunk_overlap=250,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    chunks, idx = [], 0
    for sec in sections:
        for doc in splitter.create_documents([sec["text"]]):
            body = doc.page_content.strip()
            if len(body) < 150:       # drop tiny fragments
                continue
            abs_offset = sec["start"] + doc.metadata["start_index"]
            chunks.append({
                "chunk_id": f"{arxiv_id}_c{idx:04d}",
                "arxiv_id": arxiv_id,
                "page_number": page_for(abs_offset, offsets),
                "section": sec["section"],
                "high_value": sec["section"] in HIGH_VALUE,
                "text": body,
                # use this field for embedding: adds context to each chunk
                "text_with_context": f"{title} | {sec['section'].title()}\n\n{body}",
            })
            idx += 1
    return chunks
 
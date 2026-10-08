"""Validate the locked arXiv corpus: python -m tests.validate_ingestion_sample.

Unlike the offline CI fixtures, this downloads any missing sample PDFs. Run from
the repository root after installing requirements.txt. No embedding model or API
key is needed. A failure raises and exits nonzero.
"""

import hashlib
import json

import pandas as pd
import pymupdf

from src import retrieval
from src.data_ingestion import pdf_pipeline as data_ingestion


def validate_sample():
    metadata = pd.DataFrame(data_ingestion.load_metadata())
    metadata["base_id"] = metadata["arxiv_id"].str.replace(r"v\d+$", "", regex=True)
    latest = metadata.sort_values("updated").drop_duplicates("base_id", keep="last")
    frame = data_ingestion.run_pipeline()
    stored = retrieval.load_chunks()
    pd.testing.assert_frame_equal(frame, stored)
    assert set(stored["arxiv_id"]) == set(latest["arxiv_id"]), "Incomplete sample coverage"
    assert not stored.isna().any().any(), "Missing chunk or source fields"
    assert stored["chunk_id"].is_unique, "Duplicate chunk IDs"
    assert stored["text"].str.len().between(1, 2000).all(), "Invalid chunk sizes"

    papers = []
    for row in latest.to_dict("records"):
        paper = stored[stored["arxiv_id"] == row["arxiv_id"]]
        for field in ("title", "authors", "abstract", "categories", "published", "updated", "pdf_url"):
            assert set(paper[field]) == {row[field]}, f"Metadata mismatch: {row['arxiv_id']} / {field}"
        path = data_ingestion.resolve_pdf_path(row["arxiv_id"])
        with pymupdf.open(path) as document:
            page_count = len(document)
        assert paper["page_number"].between(1, page_count).all(), f"Invalid page: {row['arxiv_id']}"
        pages = {page["page"]: page["text"] for page in data_ingestion.extract_and_clean_pdf(str(path))}
        for chunk in paper.to_dict("records"):
            assert chunk["text"] in pages[chunk["page_number"]], f"Source text mismatch: {chunk['chunk_id']}"
        papers.append({
            "arxiv_id": row["arxiv_id"], "pdf_pages": page_count, "chunks": len(paper),
            "pdf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })

    rerun = data_ingestion.run_pipeline()
    pd.testing.assert_frame_equal(rerun, stored)
    pd.testing.assert_frame_equal(retrieval.load_chunks(), stored)
    report = {
        "papers": len(papers), "chunks": len(stored),
        "checks": ["complete latest-version sample", "unique chunk IDs", "nonempty fields",
                   "chunk size <= 2000", "metadata matches snapshot", "valid PDF page citations",
                   "chunk text matches cited cleaned page", "Parquet readback", "identical rerun"],
        "sample": papers,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    validate_sample()

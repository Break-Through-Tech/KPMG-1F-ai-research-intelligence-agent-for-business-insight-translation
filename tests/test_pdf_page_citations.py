import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pymupdf

from src import retrieval
from src.data_ingestion import config, pipeline
from src.data_ingestion.chunking import chunk_document
from src.data_ingestion.pdf_parser import extract_pages


class PdfPageCitationTests(unittest.TestCase):
    def assert_source_pages(self, pages, chunks):
        source = {page["page"]: page["text"] for page in pages}
        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertIn(chunk["text"], source[chunk["page_number"]])

    def test_section_crossing_two_pages_has_only_page_local_chunks(self):
        pages = [
            {"page": 2, "text": "Methods\n" + "First-page agent evidence. " * 20},
            {"page": 3, "text": "Second-page business evidence. " * 20},
        ]
        chunks = chunk_document(pages, "2601.00001v1", "Research")
        self.assert_source_pages(pages, chunks)
        self.assertEqual({chunk["page_number"] for chunk in chunks}, {2, 3})
        self.assertEqual({chunk["section"] for chunk in chunks}, {"methods"})

    def test_short_page_tail_is_retained_without_cross_page_overlap(self):
        pages = [
            {"page": 5, "text": "Results\n" + "Supporting evidence for agent evaluation. " * 80},
            {"page": 7, "text": "Unique short tail belongs on page seven."},
        ]
        chunks = chunk_document(pages, "2601.00001v1")
        self.assert_source_pages(pages, chunks)
        self.assertTrue(any(chunk["page_number"] == 7 and "Unique short tail" in chunk["text"]
                            for chunk in chunks))
        self.assertTrue(all(len(chunk["text"]) <= 1800 for chunk in chunks))
        self.assertEqual(len({chunk["chunk_id"] for chunk in chunks}), len(chunks))

    def test_reference_cutoff_still_applies_after_page_splitting(self):
        pages = [{"page": 1, "text": "Discussion\n" + "Useful agent evidence. " * 20},
                 {"page": 2, "text": "References\nUnwanted bibliography."}]
        chunks = chunk_document(pages, "2601.00001v1")
        self.assert_source_pages(pages, chunks)
        self.assertFalse(any("Unwanted bibliography" in chunk["text"] for chunk in chunks))

    def test_real_pdf_parquet_index_and_query_cite_the_supporting_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdfs, html = root / "pdfs", root / "html"
            pdfs.mkdir()
            html.mkdir()
            aid = "2601.00001v1"
            path = pdfs / f"{aid}.pdf"
            with pymupdf.open() as document:
                document.new_page()  # Blank first page must not shift citations.
                for text in (
                    "Methods\n" + "First page explains agent evaluation evidence.\n" * 12,
                    "Second page explains distinct business implications.\n" * 12,
                ):
                    page = document.new_page(width=612, height=1200)
                    page.insert_text((40, 90), text, fontsize=10)
                document.save(path)
            row = dict(arxiv_id=aid, title="Research", categories="cs.AI", authors="Author",
                       abstract="Research abstract", published="2026-01-01", updated="2026-01-02",
                       pdf_url=f"https://arxiv.org/pdf/{aid}")
            output = root / "chunks.parquet"
            with patch.object(config, "PDF_DIR", pdfs), patch.object(config, "HTML_DIR", html):
                frame = pipeline.process_and_store([row], output)
            pd.testing.assert_frame_equal(frame, pd.read_parquet(output))
            self.assert_source_pages(extract_pages(str(path)), frame.to_dict("records"))
            self.assertEqual(set(frame["page_number"]), {2, 3})
            # Deterministic vectors isolate citation transport from relevance quality.
            import numpy as np
            class CitationModel:
                def encode(self, texts):
                    return np.array([[1.0, 0.0]] * len(texts))

            model = CitationModel()
            with patch.object(retrieval, "CHROMA_DIR", root / "index"):
                retrieval.store_embeddings(frame, np.array([[1.0, 0.0]] * len(frame)))
                hits = retrieval.search("agent", top_k=len(frame), model=model)
            for hit in hits:
                self.assertIn(hit["text"], {page["page"]: page["text"] for page in extract_pages(str(path))}
                              [hit["page_number"]])
                self.assertEqual(hit["source_url"], f"{row['pdf_url']}#page={hit['page_number']}")

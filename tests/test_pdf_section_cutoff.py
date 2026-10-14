import tempfile
import unittest
from pathlib import Path

import pymupdf

from src.data_ingestion.chunking import chunk_document
from src.data_ingestion.pdf_parser import extract_pages, split_into_sections


class PdfSectionCutoffTests(unittest.TestCase):
    def pages(self, heading):
        return [
            {"page": 1, "text": "Discussion\n" + "Useful business research evidence. " * 20},
            {"page": 2, "text": heading + "\n" + "BACK_MATTER_SHOULD_BE_SKIPPED source listing. " * 20},
        ]

    def assert_cutoff(self, pages):
        sections, _ = split_into_sections(pages)
        self.assertTrue(sections)
        self.assertFalse(any("BACK_MATTER_SHOULD_BE_SKIPPED" in section["text"] for section in sections))
        chunks = chunk_document(pages, "2601.00001v1", "Research")
        self.assertTrue(chunks)
        self.assertFalse(any("BACK_MATTER_SHOULD_BE_SKIPPED" in chunk["text"] for chunk in chunks))

    def test_references_and_bibliography_heading_variants_are_cut(self):
        for heading in ("References", "Bibliography", "3 Bibliography", "VII. Bibliography", "BIBLIOGRAPHY"):
            with self.subTest(heading=heading):
                self.assert_cutoff(self.pages(heading))

    def test_appendix_and_appendices_heading_variants_are_cut(self):
        for heading in ("Appendix", "Appendix A", "Appendices", "4 Appendices", "APPENDICES"):
            with self.subTest(heading=heading):
                self.assert_cutoff(self.pages(heading))

    def test_body_mentions_of_back_matter_are_retained(self):
        text = "Discussion\n" + ("Our bibliography and appendices support the business evidence. " * 20)
        sections, _ = split_into_sections([{"page": 1, "text": text}])
        self.assertEqual(len(sections), 1)
        self.assertIn("Our bibliography and appendices", sections[0]["text"])

    def test_real_pdf_extraction_and_chunking_apply_new_cutoff_headings(self):
        with tempfile.TemporaryDirectory() as directory:
            for heading in ("Bibliography", "Appendices"):
                with self.subTest(heading=heading):
                    path = Path(directory) / f"{heading}.pdf"
                    with pymupdf.open() as document:
                        for text in (
                            "Discussion\n" + "Useful business research evidence.\n" * 20,
                            heading + "\n" + "BACK_MATTER_SHOULD_BE_SKIPPED source listing.\n" * 20,
                        ):
                            page = document.new_page(width=612, height=1200)
                            page.insert_text((40, 90), text, fontsize=10)
                        document.save(path)
                    self.assert_cutoff(extract_pages(str(path)))

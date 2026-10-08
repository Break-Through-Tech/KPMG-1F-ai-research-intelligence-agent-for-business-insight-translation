import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data_ingestion import config, pipeline
from src.data_ingestion.chunking import chunk_html_sections
from src.data_ingestion.html_parser import parse_html_sections


class HtmlIngestionTests(unittest.TestCase):
    def test_direct_figure_caption_is_preserved_and_body_is_removed(self):
        sections = parse_html_sections('''
            <section class="ltx_section" id="S1">
              <h2 class="ltx_title">Results</h2>
              <div class="ltx_para">The evaluation supports the business use case.</div>
              <figure><div>Unwanted numeric figure body</div>
                <figcaption class="ltx_caption">Unique caption evidence.</figcaption>
              </figure>
            </section>''')
        self.assertIn("Unique caption evidence.", sections[0]["text"])
        self.assertNotIn("Unwanted numeric figure body", sections[0]["text"])

    def test_caption_inside_paragraph_is_not_duplicated(self):
        sections = parse_html_sections('''
            <section class="ltx_section"><h2 class="ltx_title">Results</h2>
              <div class="ltx_para">Before the figure.
                <figure><figcaption class="ltx_caption">Unique caption evidence.</figcaption></figure>
                After the figure.
              </div>
            </section>''')
        self.assertEqual(sections[0]["text"].count("Unique caption evidence."), 1)

    def test_chunk_citation_uses_actual_subsection_anchor(self):
        html = '''<section class="ltx_section" id="S1">
            <h2 class="ltx_title">Results</h2>
            <section class="ltx_subsection" id="S1.S2"><h3 class="ltx_title">Business impact</h3>
              <div class="ltx_para">''' + ("Agent evidence supports this business insight. " * 10) + '''
              </div></section></section>'''
        chunks = chunk_html_sections(parse_html_sections(html), "2601.00001v1", "Research")
        self.assertEqual(chunks[0]["html_url"], "https://arxiv.org/html/2601.00001v1#S1.S2")
        self.assertIsNone(chunks[0]["page_number"])

    def test_cached_html_to_parquet_retains_citation_and_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html_dir = root / "html"
            html_dir.mkdir()
            aid = "2601.00001v1"
            html = "".join(
                f'<section class="ltx_section" id="S{index}"><h2 class="ltx_title">Results {index}</h2>'
                '<div class="ltx_para">' + ("Agent evidence supports this business insight. " * 10) + '</div></section>'
                for index in range(6)
            )
            (html_dir / f"{aid}.html").write_text(html)
            row = dict(arxiv_id=aid, title="Research", categories="cs.AI", authors="Author",
                       abstract="Research abstract", published="2026-01-01", updated="2026-01-02",
                       pdf_url=f"https://arxiv.org/pdf/{aid}")
            output = root / "chunks.parquet"
            with patch.object(config, "HTML_DIR", html_dir):
                pipeline.process_and_store([row], output)
            stored = pd.read_parquet(output)
            self.assertEqual(len(stored), 6)
            self.assertTrue(stored["page_number"].isna().all())
            self.assertTrue(stored["html_url"].str.contains("#S").all())
            self.assertEqual(set(stored["section"]), {f"results {index}" for index in range(6)})

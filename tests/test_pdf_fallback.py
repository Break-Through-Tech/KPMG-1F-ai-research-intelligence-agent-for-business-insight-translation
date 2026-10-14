import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pymupdf

from src.data_ingestion import config, pipeline


class PdfFallbackTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.pdf_dir = self.root / "pdfs"
        self.pdf_dir.mkdir()
        self.html_dir = self.root / "html"
        self.html_dir.mkdir()
        self.output = self.root / "processed" / "chunks.parquet"
        for name, path in (("PDF_DIR", self.pdf_dir), ("HTML_DIR", self.html_dir),
                           ("PROCESSED_DIR", self.output.parent)):
            patcher = patch.object(config, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.rows = [self.row("2601.00001v1"), self.row("2601.00002v1")]
        for row in self.rows:
            self.make_pdf(self.pdf_dir / f"{row['arxiv_id']}.pdf")

    @staticmethod
    def row(aid):
        return dict(arxiv_id=aid, title="Research", categories="cs.AI", authors="Author",
                    abstract="Research abstract", published="2026-01-01", updated="2026-01-02",
                    pdf_url=f"https://arxiv.org/pdf/{aid}")

    @staticmethod
    def make_pdf(path, blank=False):
        with pymupdf.open() as document:
            page = document.new_page(width=612, height=1200)
            if not blank:
                text = "\n".join("Agent evaluation evidence supports business decisions." for _ in range(40))
                page.insert_text((40, 90), text, fontsize=10)
            document.save(path)

    def previous_output(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_bytes(b"previous successful corpus")
        return self.output.read_bytes()

    def assert_failure_preserves_output(self, message):
        previous = self.previous_output()
        with self.assertRaisesRegex(RuntimeError, message):
            pipeline.process_and_store(self.rows)
        self.assertEqual(self.output.read_bytes(), previous)
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_corrupt_pdf_blocks_partial_publication(self):
        (self.pdf_dir / "2601.00002v1.pdf").write_bytes(b"not a PDF")
        self.assert_failure_preserves_output("2601.00002v1")

    def test_missing_pdf_blocks_partial_publication(self):
        (self.pdf_dir / "2601.00002v1.pdf").unlink()
        self.assert_failure_preserves_output("2601.00002v1.*no usable HTML or local PDF")

    def test_blank_pdf_blocks_partial_publication(self):
        self.make_pdf(self.pdf_dir / "2601.00002v1.pdf", blank=True)
        self.assert_failure_preserves_output("2601.00002v1.*no extractable text")

    def test_empty_metadata_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "No papers selected"):
            pipeline.process_and_store([])

    def test_parquet_write_failure_preserves_previous_output(self):
        previous = self.previous_output()

        def fail_write(frame, path, **_kwargs):
            Path(path).write_bytes(b"partial write")
            raise OSError("disk write failed")

        with patch.object(pd.DataFrame, "to_parquet", fail_write):
            with self.assertRaisesRegex(OSError, "disk write failed"):
                pipeline.process_and_store(self.rows)
        self.assertEqual(self.output.read_bytes(), previous)
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_success_uses_runtime_output_path_and_is_repeatable(self):
        frame = pipeline.process_and_store(self.rows)
        stored = pd.read_parquet(self.output)
        pd.testing.assert_frame_equal(frame, stored)
        self.assertEqual(set(stored["arxiv_id"]), {row["arxiv_id"] for row in self.rows})
        self.assertEqual(set(stored["source"]), {"pdf"})
        pd.testing.assert_frame_equal(pipeline.process_and_store(self.rows), stored)

    def test_html_success_does_not_require_a_usable_pdf(self):
        aid = self.rows[0]["arxiv_id"]
        html = "".join(
            '<section class="ltx_section"><h2 class="ltx_title">Results</h2><div class="ltx_para">'
            + ("Agent evidence supports this business insight. " * 10) + '</div></section>'
            for _ in range(6)
        )
        (self.html_dir / f"{aid}.html").write_text(html)
        (self.pdf_dir / f"{aid}.pdf").write_bytes(b"corrupt but unused")
        frame = pipeline.process_and_store(self.rows)
        self.assertEqual(set(frame["arxiv_id"]), {row["arxiv_id"] for row in self.rows})
        self.assertEqual(set(frame["source"]), {"html", "pdf"})

    def test_cli_failure_returns_nonzero_and_preserves_previous_output(self):
        project = self.root / "cli-project"
        project.mkdir()
        source = Path(config.__file__).parent.parent
        shutil.copytree(source, project / "src", ignore=shutil.ignore_patterns("__pycache__"))
        metadata = project / "data" / "metadata"
        metadata.mkdir(parents=True)
        row = self.rows[0]
        pd.DataFrame([row]).to_csv(metadata / config.FULL_METADATA_FILE.name, index=False)
        pd.DataFrame({"arxiv_id": [row["arxiv_id"]]}).to_csv(metadata / config.SAMPLE_FILE.name, index=False)
        pdfs = project / "data" / "pdfs"
        pdfs.mkdir()
        self.make_pdf(pdfs / f"{row['arxiv_id']}.pdf", blank=True)
        html = project / "data" / "html"
        html.mkdir()
        (html / f"{row['arxiv_id']}.nohtml").touch()
        output = project / "data" / "processed" / "chunks.parquet"
        output.parent.mkdir()
        output.write_bytes(b"previous successful corpus")
        result = subprocess.run([sys.executable, "-m", "src.data_ingestion.pipeline"],
                                cwd=project, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no extractable text", result.stderr)
        self.assertEqual(output.read_bytes(), b"previous successful corpus")

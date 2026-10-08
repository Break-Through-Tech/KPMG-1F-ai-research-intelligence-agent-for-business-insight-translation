from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import subprocess
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pymupdf

from src.data_ingestion import pdf_pipeline as data_ingestion


class MetadataSnapshotTests(unittest.TestCase):
    def test_missing_sample_id_fails_instead_of_silent_partial_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = root / "metadata.csv"
            sample = root / "sample.csv"
            pd.DataFrame({"arxiv_id": ["paper-a"], "title": ["A"]}).to_csv(metadata, index=False)
            pd.DataFrame({"arxiv_id": ["paper-a", "paper-b"]}).to_csv(sample, index=False)
            with patch.object(data_ingestion, "FULL_METADATA_FILE", metadata), \
                 patch.object(data_ingestion, "SAMPLE_FILE", sample):
                with self.assertRaisesRegex(ValueError, "paper-b"):
                    data_ingestion.load_metadata()


class IngestionPipelineTests(unittest.TestCase):
    """Exercise real HTTP downloads, real PDFs, and real Parquet in isolation."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "http"
        self.source.mkdir()
        self.pdf_dir = self.root / "pdfs"
        self.output = self.root / "processed" / "chunks.parquet"
        self.requests = []
        requests = self.requests

        class Handler(SimpleHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                super().do_GET()

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(Handler, directory=str(self.source))
        )
        thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        self.rows = [self.row("2601.00001v1", server.server_port, "2026-01-01"),
                     self.row("2601.00001v2", server.server_port, "2026-01-02"),
                     self.row("2601.00002v1", server.server_port, "2026-01-01")]
        self.long_text = "\n".join(
            f"Evidence item {index:03d} explains agent evaluation and business research."
            for index in range(100)
        )
        for row in self.rows:
            self.make_pdf(self.source / f"{row['arxiv_id']}.pdf", [
                "",  # Preserve PDF page numbering when an initial page is blank.
                "arXiv:2601.00001v2 [cs.AI] 2 Jan 2026\n\n" + self.long_text + "\n2",
                "Business    implications\n\nSource evidence remains on the third PDF page.\n3",
            ])
        self.metadata_file = self.root / "metadata.csv"
        self.sample_file = self.root / "sample.csv"
        pd.DataFrame(self.rows + [self.row("2601.99999v1", server.server_port, "2026-01-01")]).to_csv(
            self.metadata_file, index=False
        )
        pd.DataFrame({"arxiv_id": [row["arxiv_id"] for row in self.rows]}).to_csv(
            self.sample_file, index=False
        )
        for name, value in {
            "FULL_METADATA_FILE": self.metadata_file,
            "SAMPLE_FILE": self.sample_file,
            "PDF_DIR": self.pdf_dir,
            "PROCESSED_DIR": self.output.parent,
        }.items():
            patcher = patch.object(data_ingestion, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # Avoid arXiv's request delay for this local HTTP fixture.
        sleep = patch.object(data_ingestion.time, "sleep")
        sleep.start()
        self.addCleanup(sleep.stop)

    @staticmethod
    def row(arxiv_id, port, updated):
        return {
            "arxiv_id": arxiv_id, "title": f"Research {arxiv_id}",
            "authors": "Sample Author", "abstract": "Agent evaluation evidence.",
            "categories": "cs.AI", "published": "2026-01-01", "updated": updated,
            "pdf_url": f"http://127.0.0.1:{port}/{arxiv_id}.pdf",
        }

    @staticmethod
    def make_pdf(path, pages):
        with pymupdf.open() as document:
            for text in pages:
                page = document.new_page(width=612, height=1600)
                if text:
                    page.insert_text((40, 40), text, fontsize=10)
            document.save(path)

    def assert_previous_output_preserved(self, action, message):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"previous": ["successful corpus"]}).to_parquet(self.output, index=False)
        previous = self.output.read_bytes()
        with self.assertRaisesRegex(RuntimeError, message):
            action()
        self.assertEqual(self.output.read_bytes(), previous)
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_download_to_parquet_and_downstream_load_with_repeatable_rerun(self):
        frame = data_ingestion.run_pipeline()
        stored = pd.read_parquet(self.output)
        pd.testing.assert_frame_equal(frame, stored)
        self.assertEqual(len(self.requests), 3)  # Unselected metadata is never fetched.
        self.assertEqual(set(stored["arxiv_id"]), {"2601.00001v2", "2601.00002v1"})
        self.assertGreater(len(stored), 4)
        self.assertTrue(stored["chunk_id"].is_unique)
        self.assertEqual(set(stored["page_number"]), {2, 3})
        self.assertTrue(stored["text"].str.len().between(1, 2000).all())
        self.assertFalse(stored["text"].str.contains("arXiv:").any())
        self.assertFalse(stored["text"].str.contains(r"(?m)^\s*\d+\s*$").any())
        self.assertTrue(stored["text"].str.contains("Business implications").any())
        self.assertFalse(stored.isna().any().any())
        for row in self.rows[1:]:
            paper = stored[stored["arxiv_id"] == row["arxiv_id"]]
            for field in ("title", "authors", "abstract", "categories", "published", "updated", "pdf_url"):
                self.assertEqual(set(paper[field]), {row[field]})
            passages = paper[paper["page_number"] == 2]["text"].tolist()
            for index in range(100):
                self.assertTrue(any(f"Evidence item {index:03d}" in text for text in passages))
            # Neighboring chunks retain shared context on the same page.
            for left, right in zip(passages, passages[1:]):
                shared = max(size for size in range(201) if left.endswith(right[:size]))
                self.assertGreater(shared, 0)

        from src import retrieval
        with patch.object(retrieval, "CHUNKS_FILE", self.output):
            pd.testing.assert_frame_equal(retrieval.load_chunks(), stored)
        pd.testing.assert_frame_equal(data_ingestion.run_pipeline(), stored)
        self.assertEqual(len(self.requests), 3)  # A rerun uses the PDF cache.

    def test_missing_pdf_prevents_partial_output(self):
        data_ingestion.download_pdfs(self.rows, delay=0)
        (self.pdf_dir / "2601.00002v1.pdf").unlink()
        self.assert_previous_output_preserved(
            lambda: data_ingestion.process_and_store(self.rows), "2601.00002v1: no local PDF"
        )

    def test_corrupt_pdf_prevents_partial_output(self):
        data_ingestion.download_pdfs(self.rows, delay=0)
        (self.pdf_dir / "2601.00002v1.pdf").write_bytes(b"not a PDF")
        self.assert_previous_output_preserved(
            lambda: data_ingestion.process_and_store(self.rows), "2601.00002v1"
        )

    def test_blank_pdf_requires_text_or_ocr_before_publishing(self):
        self.make_pdf(self.source / "2601.00002v1.pdf", [""])
        self.assert_previous_output_preserved(data_ingestion.run_pipeline, "2601.00002v1: no extractable text")

    def test_http_failure_is_reported_and_preserves_output(self):
        (self.source / "2601.00002v1.pdf").unlink()
        self.assert_previous_output_preserved(data_ingestion.run_pipeline, "2601.00002v1.*404")
        self.assertFalse((self.pdf_dir / "2601.00002v1.pdf").exists())

    def test_non_pdf_response_is_rejected_and_not_cached(self):
        (self.source / "2601.00002v1.pdf").write_text("<html>Unavailable</html>")
        self.assert_previous_output_preserved(data_ingestion.run_pipeline, "2601.00002v1: response is not a PDF")
        self.assertFalse((self.pdf_dir / "2601.00002v1.pdf").exists())

    def test_all_missing_pdfs_raise_instead_of_success_without_output(self):
        with self.assertRaises(RuntimeError) as raised:
            data_ingestion.process_and_store(self.rows)
        self.assertIn("2601.00001v2: no local PDF", str(raised.exception))
        self.assertIn("2601.00002v1: no local PDF", str(raised.exception))
        self.assertFalse(self.output.exists())

    def test_empty_metadata_raises_instead_of_success_without_output(self):
        with self.assertRaisesRegex(ValueError, "No papers selected"):
            data_ingestion.process_and_store([])
        self.assertFalse(self.output.exists())

    def test_parquet_write_failure_preserves_previous_output(self):
        data_ingestion.download_pdfs(self.rows, delay=0)

        def fail_write(frame, path, **_kwargs):
            Path(path).write_bytes(b"incomplete parquet bytes")
            raise RuntimeError("disk write failed")

        with patch.object(pd.DataFrame, "to_parquet", fail_write):
            # Create the previous valid output before injecting the write failure.
            self.output.parent.mkdir(parents=True, exist_ok=True)
            self.output.write_bytes(b"previous output")
            with self.assertRaisesRegex(RuntimeError, "disk write failed"):
                data_ingestion.process_and_store(self.rows)
        self.assertEqual(self.output.read_bytes(), b"previous output")
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_cli_failure_returns_nonzero_exit_and_preserves_output(self):
        # Copy the actual CLI into an isolated project with a selected cached
        # blank PDF, so this test exercises __main__ without accessing arXiv.
        src = self.root / "src"
        src.mkdir()
        script = src / "data_ingestion.py"
        package = Path(data_ingestion.__file__).parent
        shutil.copytree(package, src / "data_ingestion", ignore=shutil.ignore_patterns("__pycache__"))
        script.write_text((package.parent / "data_ingestion.py").read_text())
        metadata_dir = self.root / "data" / "metadata"
        metadata_dir.mkdir(parents=True)
        pd.DataFrame([self.rows[-1]]).to_csv(metadata_dir / "arxiv_csAI_100_metadata.csv", index=False)
        pd.DataFrame({"arxiv_id": [self.rows[-1]["arxiv_id"]]}).to_csv(
            metadata_dir / "arxiv_csAI_25_pdf_sample.csv", index=False
        )
        cache = self.root / "data" / "pdfs"
        cache.mkdir()
        self.make_pdf(cache / "2601.00002v1.pdf", [""])
        output = self.root / "data" / "processed" / "chunks.parquet"
        output.parent.mkdir()
        output.write_bytes(b"previous output")
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("2601.00002v1: no extractable text", result.stderr)
        self.assertEqual(output.read_bytes(), b"previous output")


if __name__ == "__main__":
    unittest.main()

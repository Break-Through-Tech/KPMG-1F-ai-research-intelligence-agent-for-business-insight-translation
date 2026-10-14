from contextlib import redirect_stdout
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from src import evaluation_retrieval


class BaselineCaptureTests(unittest.TestCase):
    def test_versioned_cli_captures_full_drafts_without_human_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "frozen-run"
            with redirect_stdout(io.StringIO()):
                code = evaluation_retrieval.main([
                    "--demo", "--mode", "summary", "--output", str(output)])
            self.assertEqual(code, 0)
            artifact = json.loads((output / "run.json").read_text())
            self.assertEqual(len(artifact["cases"]), 10)
            ids = [row["case"]["query_id"] for row in artifact["cases"]]
            self.assertEqual(ids, [f"alesha-v1-q{i:02d}" for i in range(1, 11)])
            for row in artifact["cases"]:
                self.assertEqual(row["case"]["benchmark_version"], "alesha-baseline-v1")
                self.assertFalse(row["result"]["approved"])
                self.assertEqual(row["result"]["human_review"]["status"], "pending")
                self.assertTrue(row["result"]["evidence"])
                self.assertTrue(row["result"]["summary"]["claims"])
            self.assertEqual(artifact["provenance"]["corpus_mode"], "synthetic")
            with (output / "review.csv").open(newline="") as file:
                reviews = list(csv.DictReader(file))
            self.assertTrue(reviews)
            self.assertTrue(all(row["reviewer"] == row["passage_rating"] == "" for row in reviews))
            self.assertIn("https://example.com/fixture#results", [row["source_url"] for row in reviews])


if __name__ == "__main__":
    unittest.main()

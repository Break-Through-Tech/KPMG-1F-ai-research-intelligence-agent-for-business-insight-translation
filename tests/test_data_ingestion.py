import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src import data_ingestion


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


if __name__ == "__main__":
    unittest.main()

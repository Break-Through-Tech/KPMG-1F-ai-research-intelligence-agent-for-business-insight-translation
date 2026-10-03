import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chromadb
import numpy as np
import pandas as pd

from src import retrieval


class FakeModel:
    def encode(self, texts, **_kwargs):
        return np.array([[1.0, 0.0] if "agent" in text.lower() else [0.0, 1.0]
                         for text in texts], dtype=float)


def chunks(*ids):
    return pd.DataFrame([{
        "chunk_id": chunk_id,
        "text": "Agent research" if chunk_id == "a" else "Other research",
        "arxiv_id": f"paper-{chunk_id}",
        "title": f"Paper {chunk_id}",
        "page_number": 2 if chunk_id == "a" else 3,
        "pdf_url": f"https://arxiv.org/pdf/paper-{chunk_id}",
    } for chunk_id in ids])


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path_patch = patch.object(retrieval, "CHROMA_DIR", Path(self.temp.name))
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.client = chromadb.PersistentClient(path=self.temp.name)
        self.model = FakeModel()

    def index(self, *ids):
        frame = chunks(*ids)
        return retrieval.store_embeddings(frame, self.model.encode(frame["text"].tolist()))

    def test_index_and_query_return_citation_from_chroma(self):
        self.index("a", "b")
        hits = retrieval.search("agent", top_k=1, client=self.client, model=self.model)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["chunk_id"], "a")
        self.assertEqual(hits[0]["arxiv_id"], "paper-a")
        self.assertEqual(hits[0]["page_number"], 2)
        self.assertEqual(hits[0]["pdf_url"], "https://arxiv.org/pdf/paper-a")

    def test_rerun_updates_metadata_and_removes_stale_chunks(self):
        self.index("a", "b")
        frame = chunks("a")
        frame.loc[0, "title"] = "Corrected title"
        collection = retrieval.store_embeddings(frame, self.model.encode(frame["text"].tolist()))
        self.assertEqual(collection.count(), 1)
        self.assertEqual(collection.get()["ids"], ["a"])
        self.assertEqual(retrieval.search("agent", client=self.client, model=self.model)[0]["title"],
                         "Corrected title")

    def test_invalid_inputs_do_not_mutate_index(self):
        self.index("a")
        with self.assertRaisesRegex(ValueError, "Duplicate chunk IDs"):
            frame = chunks("a", "a")
            retrieval.store_embeddings(frame, self.model.encode(frame["text"].tolist()))
        with self.assertRaisesRegex(ValueError, "non-empty"):
            retrieval.search(" ", client=self.client, model=self.model)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            retrieval.search("agent", top_k=0, client=self.client, model=self.model)
        self.assertEqual(self.client.get_collection(retrieval.COLLECTION_NAME).count(), 1)

    def test_legacy_index_requires_reindex_before_query(self):
        collection = self.client.get_or_create_collection(retrieval.COLLECTION_NAME)
        collection.add(ids=["old"], documents=["Agent"], embeddings=[[1.0, 0.0]])
        with self.assertRaisesRegex(ValueError, "rerun indexing"):
            retrieval.search("agent", client=self.client, model=self.model)


if __name__ == "__main__":
    unittest.main()

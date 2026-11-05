"""Offline regressions for the opt-in semantic chunker."""
import unittest
from src.semantic_chunking import semantic_chunk_text, semantic_chunk_document

class DeterministicEmbedder:
    """Small deterministic substitute for SentenceTransformer in unit tests."""

    def encode(self, sentences, *, show_progress_bar=False, convert_to_numpy=True):
        vectors = []
        for sentence in sentences:
            lowered = sentence.lower()
            if "clinical" in lowered or "patient" in lowered:
                vectors.append((0.0, 1.0))
            else:
                vectors.append((1.0, 0.0))
        return vectors


class SemanticChunkingTests(unittest.TestCase):
    def setUp(self):
        self.embedder = DeterministicEmbedder()

    def test_related_sentences_group_and_topic_change_splits(self):
        text = (
            "Agent planning improves tool selection. "
            "Agent planning reduces unnecessary calls. "
            "Clinical outcomes improved for patients. "
            "Clinical measures remained stable."
        )

        chunks = semantic_chunk_text(
            text,
            arxiv_id="2601.00001v1",
            title="Research",
            section="results",
            embedder=self.embedder,
        )

        self.assertEqual(len(chunks), 2)
        self.assertIn("Agent planning improves tool selection.", chunks[0]["text"])
        self.assertIn("Agent planning reduces unnecessary calls.", chunks[0]["text"])
        self.assertIn("Clinical outcomes improved for patients.", chunks[1]["text"])
        self.assertIn("Clinical measures remained stable.", chunks[1]["text"])

    def test_document_chunks_keep_page_and_section_citations(self):
        pages = [
            {"page": 2, "text": "Methods\n" + "Agent planning evidence. " * 12},
            {"page": 3, "text": "Results\n" + "Clinical patient evidence. " * 12},
        ]

        chunks = semantic_chunk_document(
            pages, "2601.00001v1", "Research", self.embedder
        )

        self.assertTrue(chunks)
        self.assertEqual({chunk["page_number"] for chunk in chunks}, {2, 3})
        self.assertEqual({chunk["section"] for chunk in chunks}, {"methods", "results"})
        self.assertEqual(len({chunk["chunk_id"] for chunk in chunks}), len(chunks))
        self.assertTrue(all(chunk["high_value"] == (chunk["section"] == "results")
                            for chunk in chunks))
        for chunk in chunks:
            page_text = next(page["text"] for page in pages
                             if page["page"] == chunk["page_number"])
            self.assertIn(chunk["text"], page_text)
            self.assertIn(f"Page {chunk['page_number']}", chunk["text_with_context"])

    def test_maximum_character_limit_also_handles_long_sentences(self):
        text = "Agent planning " + ("preserves important source detail " * 8) + "."

        chunks = semantic_chunk_text(
            text,
            arxiv_id="2601.00001v1",
            title="Research",
            section="methods",
            embedder=self.embedder,
            max_chars=40,
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk["text"]) <= 40 for chunk in chunks))
        compact = lambda value: "".join(value.split())
        self.assertEqual(compact("".join(chunk["text"] for chunk in chunks)), compact(text))

    def test_empty_input_returns_no_chunks(self):
        chunks = semantic_chunk_text(
            "  ",
            arxiv_id="2601.00001v1",
            title="Research",
            section="results",
            embedder=self.embedder,
        )

        self.assertEqual(chunks, [])

    def test_invalid_embedding_count_is_reported(self):
        class InvalidEmbedder:
            def encode(self, sentences, **kwargs):
                return []

        with self.assertRaisesRegex(ValueError, "one vector per sentence"):
            semantic_chunk_text(
                "A sentence.",
                arxiv_id="2601.00001v1",
                title="Research",
                section="results",
                embedder=InvalidEmbedder(),
            )

    def test_zero_embedding_is_reported(self):
        class ZeroEmbedder:
            def encode(self, sentences, **kwargs):
                return [(0.0, 0.0)] * len(sentences)

        with self.assertRaisesRegex(ValueError, "non-zero length"):
            semantic_chunk_text(
                "First sentence. Second sentence.",
                arxiv_id="2601.00001v1",
                title="Research",
                section="results",
                embedder=ZeroEmbedder(),
            )


if __name__ == "__main__":
    unittest.main()

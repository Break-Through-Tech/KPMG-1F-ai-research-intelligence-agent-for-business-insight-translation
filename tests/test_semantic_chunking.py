"""Test-only semantic chunker prototype shaped for the PDF ingestion pipeline.

The chunker is deliberately not imported by production code. It accepts a
SentenceTransformer-compatible embedder, so it can later use the project's
``all-MiniLM-L6-v2`` model without making these tests download model weights.

For an integration experiment, construct the model once and pass extracted PDF
pages to the document-level function::

    from sentence_transformers import SentenceTransformer
    from src.retrieval import EMBEDDING_MODEL

    model = SentenceTransformer(EMBEDDING_MODEL)
    chunks = semantic_chunk_document(pages, arxiv_id, title, model)

The output follows the current PDF chunk record shape and keeps chunks within
page citations. The unit tests use a deterministic fake embedder instead.
"""

import math
import re
import unittest
from collections.abc import Sequence
from typing import Optional, Protocol

from src.data_ingestion.pdf_parser import split_into_sections


class SentenceEmbedder(Protocol):
    def encode(
        self,
        sentences: list[str],
        *,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
    ) -> Sequence[Sequence[float]]:
        ...


HIGH_VALUE_SECTIONS = {
    "abstract", "introduction", "results", "result", "evaluation",
    "discussion", "limitations", "limitation", "conclusion",
    "conclusions", "future work", "applications", "application",
    "case study",
}


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimensions")
    if not left:
        raise ValueError("Embedding vectors must not be empty")
    if any(not math.isfinite(float(value)) for value in (*left, *right)):
        raise ValueError("Embedding vectors must contain finite values")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Embedding vectors must have non-zero length")
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _split_sentences(text: str, max_chars: int) -> list[str]:
    """Split at sentence ends, then hard-bound unusually long sentences."""
    pieces = re.split(r"(?<=[.!?])(?=\s|$)", text)
    sentences = []
    for piece in pieces:
        start = 0
        while len(piece) - start > max_chars:
            end = start + max_chars
            boundary = max(
                piece.rfind(separator, start, end)
                for separator in (" ", "\t", "\n")
            )
            if boundary > start:
                end = boundary + 1
            sentences.append(piece[start:end])
            start = end
        if piece[start:]:
            sentences.append(piece[start:])
    return [sentence for sentence in sentences if sentence.strip()]


def semantic_chunk_text(
    text: str,
    *,
    arxiv_id: str,
    title: str,
    section: str,
    embedder: SentenceEmbedder,
    page_number: Optional[int] = None,
    similarity_threshold: float = 0.72,
    max_chars: int = 1800,
) -> list[dict]:
    """Group adjacent sentences by embedding similarity within one source page."""
    if not -1 <= similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be between -1 and 1")
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    sentences = _split_sentences(text, max_chars)
    if not sentences:
        return []

    vectors = embedder.encode(
        [sentence.strip() for sentence in sentences],
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    if len(vectors) != len(sentences):
        raise ValueError("The embedder must return one vector per sentence")
    vector_size = len(vectors[0])
    if vector_size == 0:
        raise ValueError("Embedding vectors must not be empty")
    for vector in vectors:
        if len(vector) != vector_size:
            raise ValueError("Embedding vectors must have the same dimensions")
        values = [float(value) for value in vector]
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Embedding vectors must contain finite values")
        if not any(value != 0 for value in values):
            raise ValueError("Embedding vectors must have non-zero length")

    groups: list[list[int]] = [[0]]
    for index, sentence in enumerate(sentences[1:], start=1):
        current_group = groups[-1]
        group_text = "".join(sentences[group_index] for group_index in current_group)
        candidate = (group_text + sentence).strip()
        centroid = [
            sum(vectors[group_index][dimension] for group_index in current_group)
            / len(current_group)
            for dimension in range(len(vectors[index]))
        ]
        similarity = _cosine_similarity(centroid, vectors[index])
        if similarity < similarity_threshold or len(candidate) > max_chars:
            groups.append([index])
        else:
            current_group.append(index)

    chunks = []
    for index, group_indices in enumerate(groups):
        body = "".join(sentences[group_index] for group_index in group_indices).strip()
        context = f"{title} | {section.title()}"
        if page_number is not None:
            context += f" | Page {page_number}"
        chunks.append({
            "chunk_id": f"{arxiv_id}_c{index:04d}",
            "arxiv_id": arxiv_id,
            "page_number": page_number,
            "section": section,
            "high_value": section in HIGH_VALUE_SECTIONS,
            "text": body,
            "text_with_context": f"{context}\n\n{body}",
        })
    return chunks


def semantic_chunk_document(
    pages_data: list[dict],
    arxiv_id: str,
    title: str,
    embedder: SentenceEmbedder,
    *,
    similarity_threshold: float = 0.72,
    max_chars: int = 1800,
) -> list[dict]:
    """Chunk extracted PDF pages using the same page/section boundaries as ingestion."""
    sections, offsets = split_into_sections(pages_data)
    page_ranges = [
        (start, start + len(page["text"]), page["page"])
        for (start, _), page in zip(offsets, pages_data)
    ]

    chunks = []
    for section in sections:
        if len(section["text"].strip()) < 150:
            continue
        for page_start, page_end, page_number in page_ranges:
            start = max(section["start"], page_start)
            end = min(section["end"], page_end)
            if start >= end:
                continue
            page_text = section["text"][start - section["start"]:end - section["start"]]
            page_chunks = semantic_chunk_text(
                page_text,
                arxiv_id=arxiv_id,
                title=title,
                section=section["section"],
                embedder=embedder,
                page_number=page_number,
                similarity_threshold=similarity_threshold,
                max_chars=max_chars,
            )
            for chunk in page_chunks:
                chunk["chunk_id"] = f"{arxiv_id}_c{len(chunks):04d}"
                chunks.append(chunk)
    return chunks


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

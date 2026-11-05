"""Opt-in source/model adapters. No downloads, index writes or default changes.

Input is shared-contract evidence, not an unnormalised Parquet row. Rechunking
stays inside each original passage; parent IDs and source locators are retained.
"""
from copy import deepcopy
import math

from src.research_contracts import validate_evidence
from src.semantic_chunking import _cosine_similarity, _split_sentences


class EmbeddingAdapter:
    """Wrap an already loaded SentenceTransformer-compatible encoder.

    E5 uses query-prefix embeddings for symmetric sentence grouping, but distinct
    query/passage prefixes for retrieval. Always index and query with the same
    adapter. The semantic threshold is NOT calibrated across model families.
    """
    PROFILES = {
        'sentence-transformers/all-MiniLM-L6-v2': ('', '', ''),
        'BAAI/bge-small-en-v1.5': (
            'Represent this sentence for searching relevant passages: ', '', ''),
        'intfloat/e5-small-v2': ('query: ', 'passage: ', 'query: '),
    }

    def __init__(self, encoder, model_id):
        if model_id not in self.PROFILES:
            raise ValueError('Choose an explicitly supported embedding model profile')
        self.encoder = encoder
        self.model_id = model_id
        self.query_prefix, self.passage_prefix, self.sentence_prefix = self.PROFILES[model_id]

    def _encode(self, texts, prefix, **kwargs):
        if isinstance(texts, str):
            raise TypeError('Provide a sequence of texts, not a single string')
        kwargs['normalize_embeddings'] = True
        return self.encoder.encode([prefix + text for text in texts], **kwargs)

    def encode(self, texts, **kwargs):
        """Sentence similarity interface consumed by both chunking functions."""
        return self._encode(texts, self.sentence_prefix, **kwargs)

    def encode_queries(self, texts, **kwargs):
        return self._encode(texts, self.query_prefix, **kwargs)

    def encode_passages(self, texts, **kwargs):
        return self._encode(texts, self.passage_prefix, **kwargs)

    def provenance(self):
        return dict(model=self.model_id, normalized=True,
                    query_prefix=self.query_prefix, passage_prefix=self.passage_prefix,
                    sentence_prefix=self.sentence_prefix)


def _units(text, max_chars, tex=False):
    """Original byte-for-byte text slices plus offsets; math/literals are atomic."""
    if tex:
        from src.data_ingestion.tex_chunking import math_spans
        spans = math_spans(text)
    else:
        spans = []
    result = []

    def prose(start, end):
        cursor = start
        for piece in _split_sentences(text[start:end], max_chars):
            # The splitter only removes whitespace-only pieces. Search forward,
            # never relocate a repeated sentence to an earlier source line.
            position = text.index(piece, cursor, end)
            result.append((position, position + len(piece)))
            cursor = position + len(piece)

    cursor = 0
    for start, end in spans:
        prose(cursor, start)
        result.append((start, end))
        cursor = end
    prose(cursor, len(text))
    return result


def chunk_passages(passages, embedder, *, similarity_threshold=0.72, max_chars=1800):
    """Rechunk validated PDF/HTML/TeX evidence without crossing source boundaries.

    TeX line ranges are recomputed from original passage offsets. Recognized
    equations and literals may exceed max_chars and are marked oversized_math.
    Bundled figure evidence stays whole, retaining its asset-page/scope metadata.
    No TeX interpretation, embedding truncation fix or performance claim is made.
    """
    if type(max_chars) is not int or max_chars < 1:
        raise ValueError('max_chars must be a positive integer')
    if (type(similarity_threshold) not in (int, float)
            or not math.isfinite(similarity_threshold)
            or not -1 <= similarity_threshold <= 1):
        raise ValueError('similarity_threshold must be finite and between -1 and 1')
    parents = deepcopy(passages)
    validate_evidence(parents)
    output = []
    for parent in parents:
        source = parent['source']
        if source == 'synthetic':
            raise ValueError('This adapter requires real source locations')
        if source == 'tex_figure':
            output.append(parent)
            continue
        text = parent['text']
        tex = source == 'tex'
        if tex and parent['line_end'] != parent['line_start'] + text.count('\n'):
            raise ValueError('TeX passage text must preserve its original line layout')
        units = _units(text, max_chars, tex)
        vectors = embedder.encode([text[a:b].strip() for a, b in units],
                                  show_progress_bar=False, convert_to_numpy=True)
        if len(vectors) != len(units):
            raise ValueError('The embedder must return one vector per unit')
        vectors = [list(map(float, vector)) for vector in vectors]
        width = len(vectors[0]) if vectors else 0
        for vector in vectors:
            if (not width or len(vector) != width
                    or not all(math.isfinite(x) for x in vector)
                    or not any(x != 0 for x in vector)):
                raise ValueError('Embedding vectors must be finite, nonzero and equal-width')
        groups = []
        for i, (start, end) in enumerate(units):
            if not groups:
                groups.append([i])
                continue
            group = groups[-1]
            centroid = [sum(vectors[j][d] for j in group) / len(group) for d in range(width)]
            # Valid opposite vectors can cancel. A zero centroid is a boundary,
            # not an invalid source and not permission to discard content.
            similar = any(centroid) and _cosine_similarity(centroid, vectors[i]) >= similarity_threshold
            if end - units[group[0]][0] > max_chars or not similar:
                groups.append([i])
            else:
                group.append(i)
        for i, group in enumerate(groups):
            start, end = units[group[0]][0], units[group[-1]][1]
            raw = text[start:end]
            start += len(raw) - len(raw.lstrip())
            body = raw.strip()
            child = deepcopy(parent)
            # A parent retrieval distance does not score a newly split child.
            child.pop('distance', None)
            child.update(chunk_id=f"{parent['chunk_id']}::semantic:{i}",
                         parent_chunk_id=parent['chunk_id'], text=body,
                         parent_text_start=start, parent_text_end=start + len(body))
            if tex:
                first = parent['line_start'] + text.count('\n', 0, start)
                last = first + body.count('\n')
                child.update(line_start=first, line_end=last, oversized_math=len(body) > max_chars)
                location = f"{parent['source_file']}:{first}-{last}"
            else:
                location = f"Page {parent['page_number']}" if source == 'pdf' else parent.get('subsection') or parent.get('section', '')
            child['text_with_context'] = f"{parent['title']} | {location}\n\n{body}"
            output.append(child)
    # Reject pathological parent-ID collisions with generated child IDs too.
    validate_evidence(output)
    return output

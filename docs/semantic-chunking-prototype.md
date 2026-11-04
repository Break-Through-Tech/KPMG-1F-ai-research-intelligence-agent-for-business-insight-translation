# Opt-in semantic chunking adapters

PR #170's PDF prototype is importable from `src.semantic_chunking`; its six
original tests still exercise the same functions. Production ingestion and
retrieval defaults are unchanged. This is an experimental adapter, not a measured
retrieval improvement or a new default.

## Source and model boundaries

`src.semantic_chunking_adapter.chunk_passages` accepts shared-contract evidence
records (see [research contracts](research-contracts.md)), not raw mixed-source
Parquet rows with pandas nulls. It validates input and output, returns detached
copies, and never merges separate input passages, pages, HTML sections, source
files or archive versions. It cannot recover context already lost by ingestion.

- PDF children retain the original PDF page and URL.
- HTML children retain heading anchors, section/subsection and retained original
  source structure. Retained `source_html` is whole-parent context, not a newly
  extracted child-specific DOM fragment.
- TeX uses the existing recognized math/literal spans, never the plain sentence
  splitter inside an equation. Child file/line ranges are computed from original
  text offsets. Text must retain its original line layout. Atomic math/literals
  can exceed the soft character bound and are marked `oversized_math`.
- Bundled figure evidence remains whole, preserving its distinct asset-page and
  whole-asset scope. It is not relabeled as a paper PDF page.
- Children have derived IDs, `parent_chunk_id` and half-open parent-text offsets.
  Parent retrieval distances are removed: new children must be embedded and
  searched again. Source validation/quote membership is not semantic entailment.

The current application selects **HTML → optional TeX → PDF**, not TeX-first.
This adapter does not change that order, download sources or write an index.
It rechunks already selected evidence, rather than changing source acquisition.

## Example

Load the encoder explicitly. Local-only mode avoids an accidental weight download:

```python
from sentence_transformers import SentenceTransformer
from src.semantic_chunking_adapter import EmbeddingAdapter, chunk_passages

model_id = 'intfloat/e5-small-v2'
encoder = SentenceTransformer(model_id, local_files_only=True)
model = EmbeddingAdapter(encoder, model_id)
# evidence: a list of validated PDF/HTML/TeX evidence dictionaries.
children = chunk_passages(evidence, model, max_chars=1800, similarity_threshold=0.72)
doc_vectors = model.encode_passages([c['text'] for c in children])
query_vectors = model.encode_queries(['What did the study find?'])
```

For existing ingestion DataFrames, use the existing citation metadata conversion
before this boundary, selecting finite contract fields rather than forwarding
all nullable pandas columns:

```python
from src.retrieval import citation_metadata

evidence = [dict(chunk_id=row['chunk_id'], text=row['text'], title=row['title'],
                 **citation_metadata(row)) for row in frame.to_dict('records')]
```

The metadata helper lives in the existing retrieval module and has its normal
retrieval dependencies. If original structured-source fields are needed, carry
those finite, source-backed fields as well; the adapter preserves supplied fields.
Do not manufacture source locations for unknown sources.

## Supported embedding profiles

| Profile | Sentence grouping | Retrieval queries | Retrieved passages |
| --- | --- | --- | --- |
| `sentence-transformers/all-MiniLM-L6-v2` | No prefix | No prefix | No prefix |
| `BAAI/bge-small-en-v1.5` | No prefix | `Represent this sentence for searching relevant passages: ` | No prefix |
| `intfloat/e5-small-v2` | `query: ` | `query: ` | `passage: ` |

All wrapper outputs are normalized. E5's grouping is a symmetric similarity task,
not an asymmetric retrieval task. Injected encoders must accept the normal
SentenceTransformer `encode` keywords including `normalize_embeddings`.
`provenance()` returns the selected profile/prefixes for run records.

Always rebuild embeddings and use matching query/passages profiles when changing
models. Never mix embedding models in an existing collection. Neither this class
nor its name alone selects a production retrieval model.

The same 0.72 threshold has very different effects across model families; it is
an experimental setting, not a calibrated default. These adapters also do not
fix encoder token truncation: `max_chars` is not a token limit. Check the loaded
model's actual token limit and validate performance on representative sources.

## Offline checks

```sh
python -m unittest tests.test_semantic_chunking tests.test_semantic_chunking_adapter tests.test_research_contracts
```

These checks use deterministic fake embeddings, real TeX source parsing, source
location checks and model-prefix spies. They do not download weights or measure
retrieval quality. Real-model comparisons must be reported separately with their
corpus, questions, model snapshot, prefixes and adverse results.

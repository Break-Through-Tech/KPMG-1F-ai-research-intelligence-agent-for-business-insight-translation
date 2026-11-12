# Persistent research library (1,000 papers)

The research library is a local arXiv collection with a tested 1,000-paper build. It uses a separate directory from the fixed evaluation corpus and its index. Keep the library database, downloaded papers, caches, embeddings, logs, and generated bundles outside the checkout.

The pipeline produces a standard B2 search-view bundle. The research demo accepts the library directory and follows its CURRENT pointer.

## Pipeline

| Step | Module | What it does |
|---|---|---|
| Seed | `src/library/index.py:seed_from_bundle` | Imports an existing B2 bundle's papers and reuses their exact vectors. |
| Discover | `src/library/discovery.py` | Runs 7 topic queries (LLMs, RAG, agents, healthcare, finance, security, governance). Searches a fixed 2024–2026 submission window and filters to relevant categories. Each fetched page is recorded, so a rerun skips it. |
| Deduplicate | `src/library/store.py` | One row per arXiv base ID. A paper found by several topics keeps every topic. Every version seen is recorded. A newer version of an indexed paper is marked `update_available` and re-ingested. |
| Ingest | `src/library/ingest.py` | Downloads exact-version HTML at one request per 3.5 s. It backs off on 429/5xx, honoring `Retry-After`, and stops cleanly if the limit persists. It extracts passages with the same HTML parser as the arXiv fallback. Each paper commits on its own, so runs are resumable. Raw HTML is cached gzip-compressed. Papers without HTML, or with fewer than 5 passages, are `skipped`, with the reason recorded. |
| Index | `src/library/index.py:build` | Builds a new bundle from every ready paper. Each paper keeps cached views and vectors keyed by its passage hash, model and view settings, so only new or changed papers are embedded. The bundle is validated with the engine's own loader before the `CURRENT` pointer switches. One previous bundle is kept for rollback. |
| Verify | `src/library/verify.py` | Integrity check plus a known-item search of every paper by title (titles are not in the indexed passage text), and a sample through the full engine path with latency. |
| Dashboard | `src/library/dashboard.py` | Read-only live page: indexed totals, categories, recent papers, failures, builds and activity. |

## Commands

Install the optional retrieval dependencies and point the commands at existing
local encoder and reranker directories. Use a library directory outside the
checkout. Replace the example model paths as needed.

```powershell
python -m pip install -r requirements-experimental.txt
$env:KPMG_LIBRARY = Join-Path $HOME 'kpmg-research-library-data/library'
$encoder = './local-models/encoder'
$reranker = './local-models/reranker'

python -m src.library discover --per-topic 200
python -m src.library ingest --target 1000
python -m src.library index --encoder $encoder
python -m src.library verify --encoder $encoder --reranker $reranker
python -m src.library dashboard --port 8790
```

Optionally run `python -m src.library seed --bundle ./existing-b2-bundle` before
discovery to reuse a compatible bundle. The number of indexed papers depends
on candidate availability and readable arXiv HTML.

Increasing `--per-topic` lets discovery request additional pages. Recorded pages
are skipped, so rerunning the same search does not refresh earlier results.
Ingestion resumes unfinished work and processes newer versions when discovery
finds them. Indexing reuses cached embeddings for unchanged papers.

To serve the library through the research engine, use an existing generator
factory and choose a free port. The demo resolves the current bundle at startup.

```powershell
python -m src.experimental.demo --bundle $env:KPMG_LIBRARY --encoder $encoder --reranker $reranker --generator-factory 'your_adapter:create' --arxiv-fallback --port 8787
```

The arXiv fallback skips exact paper versions already in the loaded bundle.

## Tests

Run `python -m pytest tests/test_research_library.py -q`. Discovery and HTML
downloads use fixtures. The incremental indexing test requires the local
MiniLM snapshot specified in the test.

## Limits

- **Coverage is HTML-only.** Papers without arXiv HTML are skipped; they are not parsed from PDF.
- **Topic labels come from search queries,** not a classifier. A paper can be relevant to more than one topic.
- **Each build rewrites the full bundle files.** Embedding is incremental, but files are not appended in place. At about 1,000 papers this takes minutes and roughly 0.5 GB per bundle.
- **No human review yet.** Relevance and extraction quality of library papers have not been checked by a person.

# Experimental B2 evidence retrieval

This opt-in package combines bounded dense search views, lexical discovery,
document routing, table expansion, a local cross-encoder, and balanced evidence
selection. It is experimental and has not been promoted to the default retrieval
path. Importing it does not replace the original demo or rebuild an index.

## Setup

From the repository root, install into your project environment:

```sh
python -m pip install -r requirements-experimental.txt
```

Supply existing local directories for `all-MiniLM-L6-v2` and
`ms-marco-MiniLM-L6-v2`. The adapter uses CPU models and `local_files_only=True`;
startup will fail rather than downloading models or selecting another retriever.
If models are not cached, download them separately before running the demo:

```sh
python -c "from huggingface_hub import snapshot_download; snapshot_download('sentence-transformers/all-MiniLM-L6-v2', local_dir='data/processed/models/encoder'); snapshot_download('cross-encoder/ms-marco-MiniLM-L6-v2', local_dir='data/processed/models/reranker')"
```

Downloads are explicit setup actions, not automatic demo behavior. Keep all
weights, indexes and outputs local. Existing compatible cache snapshot directories
can be passed directly instead of downloading again.

## Locate or rebuild an isolated bundle

Pass a local bundle containing `manifest.json`, `parents.jsonl`, `views.json` and
`vectors.npy`. It must declare `bounded_search_views_v1`, `token224_parent`,
384-dimensional `all-MiniLM-L6-v2` embeddings, squared L2, and pending human
acceptance. Artifact hashes, source-parent hashes, token bounds and complete-text
coverage are validated. A different or incomplete bundle fails closed.

To build a NEW bundle from your own source-evidence JSONL:

```sh
python -m src.experimental.build_bundle --parents data/processed/local-input/parents.jsonl --html-sources data/processed/local-input/html-sources.json --encoder data/processed/models/encoder --output data/processed/b2-bundles/team-demo
```

The parents file is one complete evidence record per line using
[the source contract](../../docs/research-contracts.md). It can be an existing local
complete-parent export from the ingestion/index workflow. No source corpus is
bundled with this package. For an existing compatible bundle, pass that directory
directly and skip rebuilding. `--html-sources` is optional if the parents already
contain supplementary evidence. When supplied, it is a local list of objects with
`arxiv_id`, `title` and `html_path` (relative to the manifest). Use the exact
versioned paper ID corresponding to each cached HTML file.

The builder adds source-bound table/appendix evidence using the existing validated
extractor and creates 224-token views with 32-token overlap. Complete parents are
returned to synthesis, not rewritten snippets. It uses local embeddings only,
never modifies an existing output, and refuses production-index locations.
Rebuilding from a different corpus creates a different experimental bundle; it
does not reproduce a frozen evaluation automatically.

## Non-generation retrieval preflight

```sh
python -m src.experimental.demo --bundle data/processed/b2-bundles/team-demo --encoder data/processed/models/encoder --reranker data/processed/models/reranker --check-only
```

Confirm `retrieval.method` and `index.candidate_algorithm` both report
`document-table-balanced-facets-v1`. Preflight loads local models and validates the
bundle, but does not execute a query, initialize generation or call a provider.
There is no semantic-only fallback.

## Existing frontend, separate experimental server

Use the same arguments without `--check-only`, explicitly choosing an existing
generation factory. For the repository's configured-provider factory:

```sh
python -m src.experimental.demo --bundle data/processed/b2-bundles/team-demo --encoder data/processed/models/encoder --reranker data/processed/models/reranker --generator-factory src.generation:create_generate --library data/briefs/b2-demo.sqlite3 --port 8785
```

Keep the provider/model configuration local. `--generator-options` accepts a local
JSON object of keyword arguments for a different existing factory. Do not commit
that file or credentials. No adapter/model is silently substituted. Preserve the
same explicit factory options when comparing runs. Factory initialization may
perform its own authentication and compatibility checks; only manual Research
submission initiates a question. Run from your normal terminal if a provider needs
access to user-level runtime state.

The launcher subclasses the existing HTTP handler, serves the existing frontend
assets without copying or injecting UI, and connects Research to B2. Its startup
message and `/api/config` index identity identify the experimental method. The
optional library is separate; no original library is selected by default. The
original launcher remains available and unchanged.

## Scope and review behavior

The package shares the current retained-answer quality checks: accepted claim and
limitation sources stay together, removed draft claims do not establish coverage,
and an evidence gap is not declared absent from an entire paper. These are the
existing generation fixes accompanying this retrieval path; no new prompt tuning
was performed for packaging. Quality review remains optional in the original
launcher and enabled in this experimental launcher. Draft outputs and table
heading interpretations still require review. Source/quote membership is not a
semantic correctness guarantee.

Known limitations include similar-table/dataset row confusion, omitted comparison
details, heuristic source-role selection and reranker latency. These methods were
selected on development data; no general accuracy or scaling claim is made here.

## Offline tests

```sh
python -m pytest tests/test_experimental_html_evidence.py tests/test_experimental_b2_retrieval.py tests/test_experimental_b2_integration.py tests/test_development_validation.py tests/test_answer_quality.py tests/test_business_evidence_handoff.py
```

Tests use synthetic evidence and mocked generation. Evaluation questions are never
used inside parser or ranking modules. Original data, models, execution snapshots,
notebooks and private evaluation materials remain untracked.

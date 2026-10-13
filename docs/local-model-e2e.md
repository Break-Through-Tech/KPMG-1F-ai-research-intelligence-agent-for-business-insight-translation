# Local-model summary end-to-end checks

This branch builds on draft provider PR #94 and merged summarizer PR #99.
It reuses `openai_compatible`; it does not introduce another provider or alter
the provider draft. Both the CLI and benchmark summary mode now default to
`src.summarization:summarize`. Generation provenance records the actual adapter,
template version and SHA-256, replacing the interim prompt label. Explicit
external adapters retain an unknown prompt version rather than borrowing that hash.

## Prerequisites and execution

Install `requirements.txt` in Python 3.12. Build a local index with the existing
ingestion/retrieval commands, or copy a previously validated corpus/index into
an isolated checkout. Never overwrite a teammate's index. Retrieve with the
same MiniLM weights used to build that index. Ollama must be serving the named
model locally; `ollama pull llama3.2:1b` downloads weights, not a paid API call.
Other installed JSON-capable local models may be selected explicitly.

```sh
export RESEARCH_PROVIDER=openai_compatible
export RESEARCH_MODEL=llama3.2:1b
export RESEARCH_BASE_URL=http://127.0.0.1:11434/v1
export RESEARCH_API_KEY_ENV=KPMG_LOCAL_DUMMY_KEY
export KPMG_LOCAL_DUMMY_KEY=ollama
# Ollama ignores this dummy credential; never reuse a cloud credential.

KPMG_LOCAL_E2E=1 python -m pytest tests/test_local_model_e2e.py -q
python -m evaluation.run_benchmarks --mode summary --output /tmp/new-local-summary-run
python -m evaluation.reviews.score_reviews \
  --run /tmp/new-local-summary-run/run.json \
  --reviews evaluation/reviews/empty_reviews.json \
  --output /tmp/new-local-summary-unscored.json
```

For cached embeddings, `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` ensures no
embedding download. The opt-in test requires an explicitly configured loopback
compatible provider and runs actual persistent retrieval, local inference,
the merged summarizer, the pipeline, CLI, and JSON/CSV export. It never mocks
embeddings or model replies. Default CI skips it because model/index availability
is an operator prerequisite. Offline regression tests cover the join separately.

The original ten questions remain unchanged. `--summary-adapter module:function`
can override the default in live benchmark summary mode. Demo/retrieval/full
research-adapter modes reject a conflicting summary override.

## Observable results and limits

The benchmark reports query execution failures and `summary_failed` separately.
Malformed responses, invented citations and provider errors remain frozen in
the export as empty, unapproved insufficient-evidence summaries; they also
produce a nonzero exit status in both benchmark and CLI. The review CSV includes
the summary error and limitations; aggregation counts those failures separately
from query execution failures and includes them in `failed_queries`. Older frozen
outputs without the additive error field remain compatible.
Ordinary abstention without an error is not an
execution failure. A small local model may fail this contract: don't weaken
validation, relabel a rejected response as successful, or manufacture scores.

Record the selected model's Ollama digest, local package versions, exact Git
head and template hash with the run. The generic runner's input Parquet hashes
are not proof of the index contents. Before claiming reconciled corpus provenance,
check every stored ID/document/citation row against the audited Parquet and
preserve the index/content, validation, and embedding-weight hashes alongside
the frozen run ID. The separate validator/capture stack #95–#97 remains unmerged.

Passing the E2E check establishes pipeline operation and structural citation
validation, not semantic support or answer quality. Business generation is not
bound by this summary-only run. All output remains `approved=false`; #65 still
needs actual human source checks, ratings, double-review and disagreement handling.

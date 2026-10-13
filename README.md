# KPMG AI Research Intelligence Agent for Business Insight Translation

Break Through Tech AI Studio project with KPMG. The current prototype ingests a fixed sample of public arXiv papers and supports **local, citation-bearing passage retrieval**. A draft research workflow and JSON CLI are available; business translation and review accept independently developed adapters. A user interface and human-scored evaluation remain planned work. Search results are not generated answers.

## Current pipeline

1. The PDF-only compatibility entrypoint `src/data_ingestion.py`, backed by `src/data_ingestion/pdf_pipeline.py`, selects the 25 IDs in `data/metadata/arxiv_csAI_25_pdf_sample.csv` from `data/metadata/arxiv_csAI_100_metadata.csv`, downloads missing PDFs, extracts page text with PyMuPDF, and writes page-associated chunks to `data/processed/chunks.parquet`.
2. `src/retrieval.py` embeds those chunks locally with SentenceTransformers `all-MiniLM-L6-v2` and stores text, vectors, and citation metadata in persistent Chroma (`data/chroma_db/`). Reindexing updates records and removes chunks no longer in the input corpus.
3. The same script can embed a question and return ranked passages with arXiv ID, title, PDF URL, and **PDF page number**. Chroma distances are returned as distances, not calibrated relevance or confidence scores.

The first model run may download its weights. An OpenAI API key is **not** needed for ingestion, indexing, or retrieval. Draft generation uses the existing Gemini dependency only when selected; retrieval-only and synthetic demo execution need no generation key.

For source-specific cleaning, chunk settings, caches, stored fields, and validation
boundaries, see [Data preparation](docs/data-preparation.md).

For snapshot-bound findings, observed PDF layout losses, and prioritized
remediation, see [Data quality findings](docs/data-quality-findings.md) and the
[locked-sample PDF assessment](docs/pdf-layout-assessment.md).

## Run locally

Use Python 3.10 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/data_ingestion.py
python src/retrieval.py
python src/retrieval.py --query "How are AI agents evaluated?" --top-k 5
python -m unittest discover -s tests -v
```

The PDF-only ingestion command downloads papers not already in `data/pdfs/`; expect network use and a delay between requests. It fails if the locked sample IDs are absent from the metadata snapshot, a required PDF fails to download or parse, or a selected paper has no extractable text. A failed run preserves the previous `chunks.parquet`; a complete run replaces it atomically. Check the named paper IDs in any error and repair the inputs before rerunning. Blank or scanned PDFs may need OCR, which this pipeline does not perform. `data/pdfs/`, `data/processed/`, and `data/chroma_db/` are local generated artifacts and are ignored by Git. The five PDFs already tracked in `data/` belong to the earlier EDA notebook and are not used by this script's `data/pdfs/` cache.

To validate the entire locked sample, run `python -m tests.validate_ingestion_sample`.
This checks sample coverage, source metadata, page citations, chunk text against the
cited cleaned pages, Parquet readback, and an identical rerun. It downloads missing
PDFs, so it is separate from the offline CI tests. See the recorded
[ingestion validation results](docs/ingestion-validation.md).

For HTML-first ingestion, run `python -m src.data_ingestion.pipeline`. Its modules
separate metadata, download, HTML/PDF parsing, chunking, and storage. The HTML cache
lives in `data/html/`. HTML chunks carry `source="html"`, section/subsection labels,
and an `html_url` with the source heading anchor when available. Indexing and search
use that HTML citation through `source_url`; `page_number` is `null` for HTML.
PDF citations retain their 1-based page number and a PDF page link. Existing PDF-only
indexes remain readable. Reindex after changing ingestion mode to replace old chunks
and populate the new citation fields. The locked-sample validator above exercises
the stable PDF-only mode; it does not establish HTML extraction or retrieval quality.
PDF fallback chunks are split within section and original page boundaries, so their
text comes from the page cited by `page_number`. Overlap does not cross pages.
PDF fallback stops at References, Bibliography, Appendix, or Appendices headings,
including numbered and uppercase forms, to keep back matter out of research chunks.
The HTML-first command also refuses to publish an incomplete corpus when a required
PDF fallback is missing, corrupt, or produces no chunks. It reports the affected IDs,
exits nonzero, and preserves the previous Parquet file, including on write failure.
Compact papers with usable HTML chunks remain HTML-backed even when their PDF is
missing or corrupt. PDF fallback is used only when HTML produces no usable chunks.

Example search result fields: `chunk_id`, `text`, `distance`, `arxiv_id`, `title`, `page_number`, `pdf_url`. Page numbers are 1-based PDF pages, which may differ from page labels printed in a paper. If an older Chroma index lacks citation/model metadata, rerun `python src/retrieval.py` to refresh it before querying. Rebuild the collection when changing embedding models; vectors from different models must not be mixed.

## Research workflow (draft interface v1)

Run an entirely offline, synthetic end-to-end example (standard library only):

```bash
python main.py --demo --query "How are AI agents evaluated?"
python main.py --demo --query "How are AI agents evaluated?" --mode business --industry banking --jurisdiction US
python -m unittest tests.test_research_pipeline -v
```

`--demo` uses explicitly synthetic HTML/PDF fixtures and fake summary/business
adapters. It does not measure actual retrieval relevance, model accuracy, or
industry usefulness. For persistent retrieval, build the index as above, then:

```bash
python main.py --query "How are AI agents evaluated?" --top-k 5 --mode retrieval
# Copy .env.example to a local .env and set GOOGLE_API_KEY before generation.
python main.py --query "How are AI agents evaluated?" --top-k 5 --mode summary
```

Summary is the default mode. Generation uses Gemini (`GOOGLE_MODEL`, default
`gemini-2.5-flash`, temperature 0, JSON output). The small interim prompt is
`workflow-summary-v1`; it is not a substitute for #77's final summarizer acceptance.
Importing the workflow/CLI does not import a model, download weights, or call an API.
Missing index/credentials and unavailable stages exit nonzero with JSON errors on
stderr; successful JSON is on stdout. Provider exception payloads are not echoed.

The shared module boundary is `run_research(request, *, retrieve, summarize_fn,
translate_fn=None, review_fn=None, provenance=None)` in `src/research_pipeline.py`.
Retrieval accepts `(query, top_k)`; bound summary accepts `(query, passages)`;
translation accepts `(summary, passages, *, industry)`. Retrieval returns a list of passage dictionaries; summary and translation return
plain JSON-compatible dictionaries with citations to retrieved chunk IDs. The pipeline defensively copies
adapter inputs and preserves retrieval fields exactly, including source locations
and distances (never confidence). No-hit runs abstain without generation.

When independent lanes land, select their callable without editing this entrypoint:

```bash
# Replace module:function placeholders with the actual installed adapter names.
python main.py --query "Your question" --summary-adapter module:function
python main.py --query "Your question" --mode business --industry banking --jurisdiction US --translation-adapter module:function --review-adapter module:function
```

CLI summary/translation adapters additionally receive the injected `generate(prompt)`
callable. Business mode requires an explicit industry and a translation adapter
(#80); the optional review adapter (#81) receives the complete draft, including
jurisdiction, and returns a separate `regulatory_checkpoint`. It may wrap the
standalone checkpoint but never merges regulatory source IDs into paper citations.
`--demo` cannot be combined with live adapters.

Every new run has `approved=false` and pending human review, even if a checkpoint
returns an approval recommendation. `review_fingerprint` binds review to request,
evidence, generated outputs, checkpoint, and execution provenance;
`require_current_review` rejects material edits. It detects stale content, not a
reviewer's identity or authorization. Explicit human approval remains #81's work.
Citations are structurally validated; human checking must still establish that
passages actually support claims and suggested actions.

Provenance identifies fixture vs persistent execution, embedding/generation models,
settings, prompt version and adapter names. `input_file_sha256` identifies the current
local Parquet file when present; `corpus_sha256` stays null because indexed-corpus
identity has not been verified. The input hash is **not proof that the current
Chroma index matches it**; corpus/index
reconciliation is #82. Versioned benchmark-run capture (repo SHA/time, frozen corpus
and actual outputs) remains #64. No real corpus/model result is claimed by the demo.

## Scope and next work

The standalone [human-in-the-loop checkpoint](docs/human-checkpoint.md) notebook
accepts an industry, insight, and jurisdiction, uses Gemini Search-grounded regulatory
evidence, and produces a structured advisory assessment followed by explicit human
review. It requires a local `GOOGLE_API_KEY` and is not yet integrated with the paper
pipeline. Cited sources and applicability still require human verification.

The 25-paper set is a prototype baseline, not a claim of full 100-paper coverage. Chunking is character-based: PDF-only uses 2,000 characters with 200 overlap; HTML-first and its PDF fallback use 1,800 with 250 overlap. Their source filters differ, and omitted source content or extraction noise may degrade results; see [Data preparation](docs/data-preparation.md). Before scaling, define benchmark questions and evaluate passage relevance and citation correctness. Then connect retrieval to source-grounded summarization and business-implication generation, with separate checks that generated claims actually cite supporting passages. No such end-to-end accuracy result is claimed yet.

## Team

Jenna Hunte (AI Studio Coach); Alesha Rafi, Latifa Abdraimova, Teegawende Segrado, Jooheon Lee, Khoi Nguyen, James Zhu (team members). Thanks to Challenge Advisor Agnieszka (AJ) Jeter and the KPMG team.

## License

No project license has been selected in this repository. Confirm one with the Challenge Advisor before describing the code as open-source or redistributable.

# KPMG AI Research Intelligence Agent for Business Insight Translation

Break Through Tech AI Studio project with KPMG. The current prototype ingests a fixed sample of public arXiv papers and supports **Azure AI Search passage retrieval with source citations**. Summarization, business translation, a user interface, and evaluation are still planned work; search results are not generated answers.

## Current pipeline

1. The PDF-only compatibility entrypoint `src/data_ingestion.py`, backed by `src/data_ingestion/pdf_pipeline.py`, selects the 25 IDs in `data/metadata/arxiv_csAI_25_pdf_sample.csv` from `data/metadata/arxiv_csAI_100_metadata.csv`, downloads missing PDFs, extracts page text with PyMuPDF, and writes page-associated chunks to `data/processed/chunks.parquet`.
2. `src/retrieval.py` embeds chunks locally with MiniLM `all-MiniLM-L6-v2` (384 dimensions) and stores text, vectors, and source metadata in the shared Azure AI Search index `arxiv-papers`.
3. Queries return ranked passages with HTML section links or PDF page citations. Azure `score` is a ranking score, not calibrated confidence.

The first model run may download its weights. An OpenAI API key is **not** needed for ingestion, indexing, or retrieval. OpenAI packages remain in `requirements.txt` for future answer-generation work; no answer generator is wired up here.

For source-specific cleaning, chunk settings, caches, stored fields, and validation
boundaries, see [Data preparation](docs/data-preparation.md).

## Run locally

Use Python 3.10 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/data_ingestion.py
# Configure .env from .env.example before querying the existing Azure index.
python src/retrieval.py --query "How are AI agents evaluated?" --top-k 5
python -m unittest discover -s tests -v
```

The PDF-only ingestion command downloads papers not already in `data/pdfs/`; expect network use and a delay between requests. It fails if the locked sample IDs are absent from the metadata snapshot, a required PDF fails to download or parse, or a selected paper has no extractable text. A failed run preserves the previous `chunks.parquet`; a complete run replaces it atomically. Check the named paper IDs in any error and repair the inputs before rerunning. Blank or scanned PDFs may need OCR, which this pipeline does not perform. `data/pdfs/` and `data/processed/` are local generated artifacts and are ignored by Git. The five PDFs already tracked in `data/` belong to the earlier EDA notebook and are not used by this script's `data/pdfs/` cache.

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
data remains supported. An explicit index rebuild after changing ingestion mode replaces old chunks
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

Example result fields: `chunk_id` (Azure-encoded key), `text`, `score`, `arxiv_id`, `title`, `authors`, `categories`, `source`, `page_number`, `pdf_url`, `html_url`, `source_url`, `section`, `subsection`, `high_value`. PDF pages are 1-based; HTML page numbers are null. Never mix embeddings from different models in one index.

## Azure retrieval interface

Set `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`, and `AZURE_SEARCH_QUERY_KEY`
in your local `.env`. Teammates need only a query key; the admin key is optional for
retrieval and is needed only for writes. Keep `GOOGLE_API_KEY` for the separate Gemini
checkpoint. Do not commit keys.

```python
from src.retrieval import search_chunks
hits = search_chunks("How are AI agents evaluated?", top_k=5, hybrid=False)
```

`search()` is also a public entry point to the same Azure backend. `hybrid=True`
combines keyword and vector search. Both APIs return validated source citations and
accept optional `client` and `model` arguments for offline testing.

The existing shared index does not need rebuilding to run queries. For a future,
intentional corpus replacement only, the index owner can use
`python src/retrieval.py --rebuild`. This **deletes and recreates the shared index**;
coordinate downtime first. Input and embeddings are validated before deletion,
but a later service/upload failure requires a retry. Ordinary `store_embeddings()`
uploads do not remove stale IDs. Running the script without arguments makes no writes.

Automated tests use mocked Azure clients and embedding models, never live Azure
requests. They verify transport, validation, citations, and failure behavior, not
live relevance or service availability. The Gemini checkpoint remains a standalone
regulatory workflow; its model-generated insight is not yet wired to paper retrieval.

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

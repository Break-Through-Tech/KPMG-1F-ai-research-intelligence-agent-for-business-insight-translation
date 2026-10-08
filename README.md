# KPMG AI Research Intelligence Agent for Business Insight Translation

Break Through Tech AI Studio project with KPMG. The current prototype ingests a fixed sample of public arXiv papers and supports **local, citation-bearing passage retrieval**. Summarization, business translation, a user interface, and evaluation are still planned work; search results are not generated answers.

## Current pipeline

1. The PDF-only compatibility entrypoint `src/data_ingestion.py`, backed by `src/data_ingestion/pdf_pipeline.py`, selects the 25 IDs in `data/metadata/arxiv_csAI_25_pdf_sample.csv` from `data/metadata/arxiv_csAI_100_metadata.csv`, downloads missing PDFs, extracts page text with PyMuPDF, and writes page-associated chunks to `data/processed/chunks.parquet`.
2. `src/retrieval.py` embeds those chunks locally with SentenceTransformers `all-MiniLM-L6-v2` and stores text, vectors, and citation metadata in persistent Chroma (`data/chroma_db/`). Reindexing updates records and removes chunks no longer in the input corpus.
3. The same script can embed a question and return ranked passages with arXiv ID, title, PDF URL, and **PDF page number**. Chroma distances are returned as distances, not calibrated relevance or confidence scores.

The first model run may download its weights. An OpenAI API key is **not** needed for ingestion, indexing, or retrieval. OpenAI packages remain in `requirements.txt` for future answer-generation work; no answer generator is wired up here.

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
Compact papers with usable HTML chunks remain HTML-backed even when their PDF is
missing or corrupt. PDF fallback is used only when HTML produces no usable chunks.

Example search result fields: `chunk_id`, `text`, `distance`, `arxiv_id`, `title`, `page_number`, `pdf_url`. Page numbers are 1-based PDF pages, which may differ from page labels printed in a paper. If an older Chroma index lacks citation/model metadata, rerun `python src/retrieval.py` to refresh it before querying. Rebuild the collection when changing embedding models; vectors from different models must not be mixed.

## Scope and next work

The standalone [human-in-the-loop checkpoint](docs/human-checkpoint.md) notebook
accepts an industry, insight, and jurisdiction, uses Gemini Search-grounded regulatory
evidence, and produces a structured advisory assessment followed by explicit human
review. It requires a local `GOOGLE_API_KEY` and is not yet integrated with the paper
pipeline. Cited sources and applicability still require human verification.

The 25-paper set is a prototype baseline, not a claim of full 100-paper coverage. Current chunking is character-based (2,000 characters, 200 overlap); figures, reference lists, and PDF extraction noise may degrade results. Before scaling, define benchmark questions and evaluate passage relevance and citation correctness. Then connect retrieval to source-grounded summarization and business-implication generation, with separate checks that generated claims actually cite supporting passages. No such end-to-end accuracy result is claimed yet.

## Team

Jenna Hunte (AI Studio Coach); Alesha Rafi, Latifa Abdraimova, Teegawende Segrado, Jooheon Lee, Khoi Nguyen, James Zhu (team members). Thanks to Challenge Advisor Agnieszka (AJ) Jeter and the KPMG team.

## License

No project license has been selected in this repository. Confirm one with the Challenge Advisor before describing the code as open-source or redistributable.

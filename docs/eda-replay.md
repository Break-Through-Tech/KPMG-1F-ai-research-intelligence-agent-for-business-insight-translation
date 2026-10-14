# Replaying the committed EDA snapshot

The EDA notebook defaults to `REFRESH_METADATA=False` and
`DOWNLOAD_MISSING_PDFS=False`. It reads the committed metadata CSV and the locked
25-paper manifest, preserves the source files, and requires the corresponding
PDFs in `data/pdfs/` before the PDF-analysis cells. Recollection is an explicit
option and changes the dataset; it is not needed to replay these findings.

Use the repository Python environment, plus `matplotlib` for charts, to open
`notebooks/KPMG_Arxiv_EDA.ipynb` from the repository root or `notebooks/` and run
all cells. Optional live metadata collection additionally requires `arxiv`.
Populate missing PDFs explicitly with `python src/data_ingestion.py` before
replay; that separate ingestion command may use the network.

The October 7, 2026 replay executed all **37 code cells** successfully against
cached PDFs and the committed CSV. Both collection flags stayed disabled, and
the metadata, sample-manifest, and all 25 PDF hashes were unchanged afterward.
The PDFs matched the hashes in `ingestion-validation.json`.

Metadata SHA-256: `3530e739bb76f4d72813771e5dc2dc18e9eeffe3e3e46ff22d67aad16b2c008a`.

The saved outputs and prose now agree on 100 records, eight base metadata fields,
27 category labels, no missing/blank fields, and no duplicate arXiv IDs. The leading
co-category counts are cs.LG 31, cs.CL 22, and cs.CV 12. The 25 PDFs span 693 pages
(mean 27.72; median 23); all yielded text under the notebook's OCR heuristic.
Text presence does not establish layout/table fidelity or every page's OCR needs.

Replay environment: Python 3.14.7, pandas 3.0.6, PyMuPDF 1.28.2, matplotlib 3.11.2,
and scikit-learn 1.9.1. Stored notebook outputs are snapshot evidence, not a fresh
live-arXiv link check, ingestion-quality evaluation, or retrieval benchmark.

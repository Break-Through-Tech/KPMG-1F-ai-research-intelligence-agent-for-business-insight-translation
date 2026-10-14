"""Compatibility API for the stable PDF-only ingestion pipeline.

The HTML-first pipeline is available through src.data_ingestion.pipeline.
"""

from .pdf_pipeline import (
    chunk_document, download_pdfs, extract_and_clean_pdf, load_metadata,
    process_and_store, resolve_pdf_path, run_pipeline,
)

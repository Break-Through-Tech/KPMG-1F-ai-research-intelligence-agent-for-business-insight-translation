# Ingestion validation for issue #50

Validated on October 7, 2026, against the locked 25-paper sample and full metadata
snapshot in this repository. This covers ingestion through stored Parquet and the
retrieval module's chunk loader.

## Problems reproduced and fixed

- Missing local PDFs were silently skipped. When every PDF was missing,
  `process_and_store` returned successfully without writing a dataset.
- Download errors were printed without failing the run, allowing partial output.
- A PDF with no extractable text could be omitted from the stored corpus.
- Writing directly to `chunks.parquet` could damage the previous successful
  dataset if the write failed.

The pipeline now raises with affected paper IDs when downloads or extraction fail,
rejects empty input and papers with no extracted text, and publishes only a complete
latest-version corpus. It writes to a temporary file beside the destination before
replacing the previous dataset. Failed writes remove the temporary file and preserve
the previous dataset. PDF documents close even when extraction raises.

## Automated integration tests

Run from the repository root after installing `requirements.txt`:

```sh
python -m unittest discover -s tests -v
```

**Result: 33 tests passed**, including 10 new ingestion tests and the existing
metadata, retrieval, and human-checkpoint tests.

The new ingestion tests generate real PDFs, serve them from a local HTTP server,
download them with Requests, and extract, clean, chunk, and store them as actual
Parquet. Only the request delay is bypassed for the local server. The successful
integration test checks sample filtering, latest-version deduplication, blank-page
number preservation, cleaning, bounded chunks with shared context, source metadata,
unique IDs, the retrieval loader, cache reuse, and identical reruns. Failure tests
cover missing and corrupt PDFs, blank PDFs, HTTP 404, non-PDF responses, empty input,
interrupted Parquet writes, and a nonzero CLI exit. Failed runs preserve prior output.

## Complete sample run

```sh
python src/data_ingestion.py
python -m tests.validate_ingestion_sample
```

| Check | Result |
| --- | --- |
| Selected and processed papers | 25 / 25 |
| Total PDF pages | 693 |
| Stored chunks | 1,671 |
| Largest chunk | 2,000 characters |
| Duplicate chunk IDs | 0 |
| Null source or chunk fields | 0 |
| Source metadata matches selected snapshot | Passed for every chunk |
| PDF page numbers within actual source page count | Passed for every chunk |
| Chunk text appears on its cited cleaned source page | Passed for every chunk |
| Parquet readback through retrieval loader | Passed |
| Rerun frame equals first stored frame | Passed |

The machine-readable [per-paper report](ingestion-validation.json) records chunk
counts, PDF page counts, and SHA-256 hashes for all 25 PDFs. The validator prints
this report after all checks succeed and exits nonzero on a failed check.

The full sample used locally cached PDFs from the prior sample run, copied into
this isolated checkout. **Fresh downloads from live arXiv were not tested in this
run.** Download behavior was exercised through the local HTTP integration tests.

Environment: macOS, Python 3.12.9, a fresh virtual environment installed from
`requirements.txt`; pandas 3.0.6, PyMuPDF 1.28.2, PyArrow 25.0.1, Requests 2.34.2,
and langchain-text-splitters 1.1.3. Counts and PDF hashes describe this specific
sample; different PDFs or dependency versions may change chunk counts.

This validates ingestion completeness and source linkage. It does not evaluate
OCR, layout or table fidelity, semantic retrieval relevance, embeddings, answer
generation, or business usefulness.

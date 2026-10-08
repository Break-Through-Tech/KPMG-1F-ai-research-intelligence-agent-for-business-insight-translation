# Data preparation and source-specific ingestion

The prototype selects a fixed 25-paper sample from the committed 100-paper metadata
snapshot, extracts research text, attaches source metadata, and publishes
`data/processed/chunks.parquet` for local indexing. It offers a PDF-only compatibility
path and an HTML-first path with PDF fallback. Their cleaning and chunk settings differ.

## Inputs and reproducible EDA

`data/metadata/arxiv_csAI_100_metadata.csv` stores arXiv ID/version, title, authors,
abstract, categories, publication/update timestamps, and PDF URL. The 25 IDs in
`arxiv_csAI_25_pdf_sample.csv` select the prototype corpus. Both ingestion loaders
reject sample IDs absent from the metadata snapshot. Processing groups versions by
base arXiv ID and keeps the row with the latest sorted update timestamp.

The EDA notebook defaults to reading the committed CSV and cached sample PDFs, with
metadata refresh and PDF downloads disabled. It prints the metadata SHA-256 so the
saved analysis can be tied to its input. The current snapshot contains 100 records,
eight fields, 27 distinct category labels, no missing/blank fields, and no duplicate
IDs. Recollecting metadata is an explicit notebook option and changes the dataset;
review the locked sample and rerun the analysis before using new findings.

## Source to cleaned text to chunks to storage

| Path | Source and extraction | Chunk size / overlap | Citation location |
| --- | --- | --- | --- |
| PDF-only: `python src/data_ingestion.py` | Cached/downloaded PDF; page text from PyMuPDF | 2,000 / 200 characters, within each original page | Positive 1-based PDF page |
| HTML-first: `python -m src.data_ingestion.pipeline` | Cached arXiv HTML; abstract and section/subsection text | 1,800 / 250 characters, within each extracted section/subsection | HTML heading anchor when available; PDF page is null |
| PDF fallback inside HTML-first | PDF blocks after layout heuristics, organized into retained sections and original page ranges | 1,800 / 250 characters; split at original page boundaries before chunking | Positive 1-based PDF page |

These are character limits, not token counts. Each path uses a recursive character
splitter with successively smaller separators. PDF-only uses paragraph, newline,
space, then character boundaries; HTML-first and PDF fallback additionally use a
sentence boundary. Overlap cannot carry PDF text across a cited page boundary.

The compatibility entrypoint delegates to `src/data_ingestion/pdf_pipeline.py`.
HTML-first separates selection, download/cache, HTML/PDF parsing, chunking, and
publication across `src/data_ingestion/` modules.

## Cleaning in PDF-only mode

PyMuPDF extracts each original page's text. Cleanup removes matching arXiv stamp
strings and standalone numeric page-number lines, collapses runs of spaces/tabs,
reduces excessive blank lines, and trims whitespace. Pages with no remaining text
are omitted while later pages retain their original page numbers. Chunking stays
within one page. A document producing more than 200 chunks emits a warning; this
does not change its chunk size or remove it from the corpus.

This path does not perform table detection, multi-column reading-order correction,
OCR, or the HTML-first fallback's reference/appendix cutoff. Figures, numeric labels,
and references can still appear in its text.

## Cleaning in HTML-first mode

The HTML parser preserves figure/table captions and removes figure/table bodies. It
removes bibliography, appendix, display-equation, proof, section-number, and navigation
elements identified by the parser's selectors. Inline math becomes its LaTeX alt-text.
The abstract is extracted separately without repeating it in section output.

Normal papers retain section/subsection labels; thesis/book structures use chapter
and section labels, skipping specified front/back matter such as acknowledgments,
contents, lists, bibliography, references, dedication, and declaration. Nested paragraph
containers are handled without duplicating their text. Available HTML IDs provide
heading anchors. Labels remain free text rather than a standardized taxonomy.

After splitting a section/subsection, HTML pieces shorter than 150 characters are
discarded. If HTML produces no usable chunks, processing attempts PDF fallback.
Consequently, a compact source can fall back even when HTML was downloaded.

## Cleaning in the HTML-first PDF fallback

The PDF parser uses text blocks and page geometry. Full-width blocks separate bands;
within a band, left-column blocks precede right-column blocks. It identifies image,
large vector-drawing, and table regions, and normally excludes text blocks mostly
inside those regions while retaining recognized figure/table captions. Page-sized
regions are ignored by that exclusion heuristic. Drawing/table detection failures
leave those regions unidentified rather than stopping extraction.

Blocks wholly in the top or bottom 5% of a page are excluded as headers/footers.
The parser dehyphenates a hyphen followed by a line break and lowercase letter,
recognizes short known section headings, removes matching arXiv stamps, normalizes
spaces, and joins retained lines. Outside recognized captions, it filters very short
lines, lines with a numeric-character ratio of at least 0.35, and short non-heading
blocks. These rules can omit meaningful numeric results or atypical layouts.

Recognized section headings partition the document. Text from References,
Bibliography, Appendix, or Appendices onward is excluded, including recognized
numbered/uppercase forms. Retained sections shorter than 150 characters are skipped.
Each remaining section is intersected with its original page ranges before splitting;
nonempty short page tails survive and overlap stays within that original page.

These are extraction heuristics, not proof of layout/table fidelity. Omitted table,
figure, equation, proof, appendix, or numeric content may include useful findings;
consult the original source during claim review. Scanned or otherwise non-extractable
PDFs require a separate OCR decision; the pipeline does not run OCR.

## Cache, fallback, and publication behavior

PDF caches live in `data/pdfs/`; HTML caches live in `data/html/`. Existing files are
reused. An HTML 404 creates a `.nohtml` marker, which also prevents a new HTML request
on later runs. Cached content/markers therefore do not establish fresh source health.
The five PDFs tracked directly under `data/` are earlier EDA assets, not this cache.

The HTML-first command attempts PDF and HTML downloads, then prefers usable HTML
chunks. PDF fallback is selected only when HTML yields none. A missing/corrupt PDF
that is not needed because usable HTML exists does not make that paper fail.

Both processing paths require every selected latest-version paper to produce text
chunks. Missing, corrupt, or unextractable required PDFs cause an incomplete-corpus
error naming affected IDs. Downloads and caches alone do not establish successful
processing. Parquet is written beside its destination to a temporary file and replaced
only on a complete successful write. Failed processing or writes preserve the previous
published dataset.

## Stored fields and retrieval handoff

Chunks retain `chunk_id`, arXiv ID, original text, paper metadata, PDF URL, and source
location. HTML-first output additionally records `source`, section labels,
`text_with_context`, and `high_value`; HTML also carries `html_url` and a null
`page_number`. Its PDF fallback carries an original PDF page number. PDF-only output
uses its PDF page number and does not require the newer source/section fields.

`src/retrieval.py` embeds and stores **`text`** with local `all-MiniLM-L6-v2` vectors
in Chroma. It does not currently embed `text_with_context` or apply `high_value` as
ranking logic. Stored citations retain arXiv ID, title, PDF URL, source mode, and
available section/subsection labels. `source_url` is an HTML heading link or a PDF
`#page=` link. HTML has no invented PDF page. Search returns these fields and Chroma
distance; distance is not calibrated confidence.

After changing ingestion mode or corpus, rerun `python src/retrieval.py`. Upsert
refreshes texts/metadata, including reused chunk IDs; IDs absent from the new corpus
are removed. Keep the embedding model consistent with the collection, or rebuild
it rather than mixing incompatible vectors.

## Validation boundaries

[Recorded ingestion validation](ingestion-validation.md) and its machine-readable
per-paper report cover the PDF-only locked sample: 25 PDFs, 693 pages, and 1,671
chunks, with source linkage and identical reruns. Those counts do not describe the
HTML-first corpus. `python -m tests.validate_ingestion_sample` exercises PDF-only
mode and may download missing PDFs.

Fixture tests cover HTML parsing, mixed-source citation transport, PDF fallback
failures/page boundaries, and back-matter cutoffs. Full HTML-first sample validation
is tracked in [#82](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/82).
Sample layout assessment and remediation synthesis are
[#40](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/40)
and [#43](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/43).
Extraction/transport checks do not establish semantic relevance, generated claim
support, summary quality, or business usefulness; those require separate evaluation.

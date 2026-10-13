# Locked-sample PDF layout assessment (#40)

Assessed October 13, 2026 on main `77ab62ba55ff0ad784c1d3b95ad7e56ad4c50114`.
The [machine-readable triage](pdf-layout-assessment.json) binds all 25 locked IDs
to PDF hashes and records page-level geometry, labels, text presence, and raw versus
HTML-first PDF-fallback text counts. All PDF hashes match the earlier
[PDF-only validation](ingestion-validation.json). Twenty-two files came from matching
local caches; `2605.00292v2`, `2606.01498v1`, and `2607.00274v1` were freshly
downloaded from their manifest PDF URLs. This is not a full live-link audit.

## Method and coverage

All original pages were machine-triaged; **not all were visually inspected**.
Two-column signals require substantial narrow blocks on both sides of the page;
table/figure labels may include prose cross-references, and missing labels do not
prove absence. Raster-image counts miss vector figures. Text presence and counts
do not measure OCR, reading-order, equation, or table fidelity. Long documents and
back-matter signals are visible per paper/page in the JSON.

Deeper visual comparison covered five deliberately varied examples below, using
rendered original pages and `pdf_parser.extract_pages` output. These include
two-column technical text/equations, a wide comparison table, a formal mathematical
document, a diagram plus two-column numeric table, and a single-column figure.
This subset is diagnostic, not a statistical quality estimate. For PDF-only mode,
raw PyMuPDF extraction is the comparison baseline; this run does not recompute its
cleaning/chunks. No HTML source or full HTML-first ingestion was evaluated.

Reproduce against matching cached files (dependencies: `requirements.txt`):

```sh
python -m tests.assess_pdf_layout --pdf-dir data/pdfs --output docs/pdf-layout-assessment.json
```

The command is read-only for PDFs and fails if a locked input is unavailable or
unreadable; it never silently selects a smaller subset. Its `source_sha` identifies
the checkout used, not a live publication version. Page numbers below are PDF
pages, not printed article pagination. Source links use the locked manifest URLs.

## Observed comparisons

| Locked paper and inspected page | Original / raw extraction | Fallback extraction | Severity and downstream consequence |
|---|---|---|---|
| [2602.00931v2 p3](https://arxiv.org/pdf/2602.00931v2#page=3) | Two columns; utility mean `0.295 (min 0.050, max 0.889)` appears in left-column prose; displayed mathematics and a footnote | Left-column prose precedes right-column prose, but the mean/range phrase becomes `has a mean of range > 0.3`; numbers between are lost. Equation symbols are flattened into lines | High for quantitative claims: intact prose around missing numbers can produce an incomplete or misleading finding. Reading-order success on this page is not a document-wide pass |
| [2602.00933v3 p3](https://arxiv.org/pdf/2602.00933v3#page=3) | Wide Table 1 has aligned benchmark rows, #S/#T/#Tasks and checkmarks | Caption survives; flattened text contains `Benchmark #Tasks Cross-Server ...` and merged benchmark names. Nearby prose still contains `1,000`, `36`, `220` | High for cross-benchmark comparison: prose numerals surviving do not preserve table row/column associations |
| [2603.00824v2 p3](https://arxiv.org/pdf/2603.00824v2#page=3) | Single-column prose, Related work, definitions, inline formulae | `Definition 2.1` and prose survive; mathematical representation is plain extracted text, not verified notation | Medium/unverified for formal claims: confirm definitions and equations in the original; no mathematical fidelity verdict |
| [2605.00276v1 p6](https://arxiv.org/pdf/2605.00276v1#page=6) | Large Fig. 4 with workflow text; Table III shows overall `77.4%`, `23.6%`, `30.4%`; two-column narrative | Fig. 4 caption survives but interior workflow text is excluded. Table title/headings remain; all three overall percentages are absent. Raw 3,663 characters versus fallback 1,752 | High for performance comparisons and mechanism descriptions: captions/headings alone cannot support the omitted results or diagram steps |
| [2609.39199v1 p3](https://arxiv.org/pdf/2609.39199v1#page=3) | Single-column Fig. 1 architecture followed by prose with encoder scores `0.767 and 0.737` | Figure caption remains but interior labels such as `Audio Input` do not. Prose becomes `two highest overall scores of Despite its strong performance` | High for score claims; medium for architectural detail. Source omission is not evidence of a negative result |

Short excerpts above are observed source-to-extraction comparisons, not generated
answers or evidence that retrieval/model quality passed. Figure exclusion and
numeric-line filtering are implemented heuristics; these examples demonstrate
their costs. HTML table/figure-body exclusion has similar *potential* costs, but
was not measured here. The PDF-only path retains more raw content but has no
layout-aware table reconstruction or multi-column correction.

## Back matter, headings, and remediation handoff

The fallback section splitter intentionally cuts at recognized references,
bibliography, or appendix headings. Unrecognized domain-specific headings can
leave large sections, so section labels are not a verified taxonomy. The triage
report records back-matter signals before section cutoff; it does not claim those
pages reach retrieval. Existing heading/page-citation regression tests establish
specific fixture behavior, not fidelity on every real document.

Route the quantitative omission, table associations, and diagram gaps to the
[#43 remediation account](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/43).
Before quoting a table number, equation, or diagram step, reviewers must inspect
the original page and retain that locator. Prefer deliberate structured extraction
with page/region provenance over inserting guessed values into prose. Add real
page-derived regressions before changing numeric filters or column ordering.
OCR should be considered only after per-page image/text comparison; no blanket
OCR requirement follows from this sample. #82 owns actual HTML-first corpus and
citation-transport validation; this assessment does not complete that lane.

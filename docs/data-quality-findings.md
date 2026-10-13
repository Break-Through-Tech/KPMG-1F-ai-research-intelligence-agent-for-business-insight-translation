# Data quality findings and remediation (#43)

October 13, 2026 synthesis for Tasks 3.1-3.4. Source implementation is main
`77ab62ba55ff0ad784c1d3b95ad7e56ad4c50114`; the accompanying #40 assessment
supplies new page-level observations. This report is an assessment, not a claim
that all limitations have been repaired or that answer quality has passed.

## Evidence and snapshot

- Recounted committed metadata: 100 rows, eight fields, zero missing/blank values,
  zero duplicate IDs. Metadata SHA-256:
  `3530e739bb76f4d72813771e5dc2dc18e9eeffe3e3e46ff22d67aad16b2c008a`.
- Recounted locked manifest: 25 rows, zero missing/blank values, zero duplicate IDs.
  Manifest SHA-256:
  `9567dd1eea3cf04d8bea3939a8efe8f4e1c48bf94f776d1042d532b3746d9dd4`.
- [#40 PDF assessment](pdf-layout-assessment.md) and its
  [JSON](pdf-layout-assessment.json): all 25 PDFs / 693 pages, all source hashes
  match the earlier report. Twenty-two matching caches plus three fresh matching
  downloads. Five representative original pages visually compared to fallback
  extraction. Every page has at least 100 raw extracted characters, with zero
  U+FFFD replacement characters across this extraction. Neither fact proves
  complete OCR, encoding, reading-order, or table fidelity.
- Historical [PDF-only validation](ingestion-validation.md): 1,671 chunks and
  complete source/page transport under its recorded October 7 environment.
  Those are **not newly measured HTML-first counts**.
- [EDA replay](eda-replay.md): prior 37-cell cached replay; the saved metadata
  correction agrees with today's recount. #34 is closed following `e194ef6`.
- Current offline suite: `python -m unittest discover -s tests -v`, **57 tests
  passed** on this candidate's unchanged runtime. This does not rerun EDA or
  establish live download, actual embeddings, generated claims, or business value.

## Category status

| Category | Status / affected IDs or pages | Evidence and boundary |
|---|---|---|
| Missing/blank metadata and duplicate IDs (3.1) | Checked; none found in 100-row metadata or 25-row manifest | Direct CSV recount. Completeness is not factual correctness of titles, dates, or abstracts |
| Column order, tables, figures, captions (3.2) | Issue found; `2602.00931v2` p3, `2602.00933v3` p3, `2605.00276v1` p6, `2609.39199v1` p3 | #40 original-page comparisons. Numeric/table/diagram information loss in PDF fallback; caption survival does not imply table/figure preservation |
| Mathematical / unusual layouts (3.2) | Checked subset; fidelity not established | `2603.00824v2` p3 definition/inline formula text; full real-document formal notation check not performed |
| Malformed/noisy extraction (3.3) | Issue found in numeric prose/table associations; full semantic fidelity not checked | `has a mean of range > 0.3` and `two highest overall scores of Despite...` in #40. Missing values can leave plausible broken prose |
| OCR needs (3.3) | Text presence checked on all 693 pages; per-page OCR necessity not fully checked | All pages produce >=100 raw characters. Only five visual comparisons; image text can still be absent. No observed whole-file scan-only PDF; no blanket OCR clearance |
| Encoding (3.4) | U+FFFD screen checked; no replacement characters found; glyph fidelity not fully checked | All raw page text screened. Mathematical glyphs/ligatures, nulls and flattened notation need source comparison; no universal encoding pass |
| Broken PDF links (3.4) | Three fresh URLs checked; other 22 live URLs not checked | Fresh successful PDFs: `2605.00292v2`, `2606.01498v1`, `2607.00274v1`; all historical hashes match. Cached files and local HTTP tests do not prove current arXiv link health |
| Corrupted/missing files (3.4) | Checked current 25-file assessment inputs; all open and match hashes | Three inaccessible historical-cache files were replaced only in the isolated assessment cache with hash-matching downloads. Inaccessibility is not proof of source corruption |
| References/appendices and noise | Implemented filtering; corpus-wide correctness not measured | Fallback section cutoff plus existing fixture tests. Back-matter signals in triage precede cutoff; unsupported headings can leave broad sections. PDF-only has no equivalent cutoff |
| HTML-first source quality | Not checked in this report | #82 owns all-ID HTML-first extraction, omission/citation/source-mode and transport validation. PDF observations cannot substitute for HTML checks |

The closed #41/#42 issues and merged defensive runtime are prior implementation
evidence, not proof that every real source is flawless. The current findings
extend their assessment rather than undoing the existing missing/corrupt-file,
atomic-publication, page-citation, or back-matter safeguards.

## Remediation map

| Priority / disposition | Recommendation and rationale | Owning surface / handoff |
|---|---|---|
| P1, remaining fix | Add page-derived regression cases for numeric prose lost by filtering; preserve legitimate quantitative findings without admitting chart-label noise | `pdf_parser.py`; #40 observations are reproducible inputs for a focused parser fix; implementation owner not assigned by this report |
| P1, accepted limitation until deliberate extraction exists | Do not generate numerical comparisons from flattened tables. Require original page/region review or structured rows/columns with provenance. A caption cannot justify omitted percentages | Translator/reviewer handoff #80/#81; future table extraction needs a separately scoped runtime change |
| P1, accepted limitation | Treat diagram interiors, equations, proofs and appendix results as potentially omitted. If necessary to answer, inspect original source and abstain until adequate evidence is captured | #77 summary / #80 business translation / #81 explicit human review; never silently reconstruct omitted evidence |
| P1, already merged | Reject incomplete required inputs; preserve prior Parquet via atomic publication; retain original PDF page boundaries/citations and stale-index handling | Existing ingestion, PDF fallback, and retrieval tests; do not duplicate these safeguards |
| P2, conditional remaining work | OCR only pages where visual evidence requires missing image text; preserve original PDF, record OCR tool/version and page provenance, revalidate before indexing | No OCR owner assigned; not part of current runtime. Avoid blanket OCR that may degrade born-digital equations |
| P2, remaining verification | Audit fresh URL status, returned content type and actual PDF parse separately; do not erase a good cached corpus because a transient request failed | #82 source-validation lane; future full live-link audit must state timing and all-ID coverage |
| P2, already merged plus remaining proof | Reference/appendix cutoff and column heuristics have fixture coverage. Compare real cutoff points, unusual headings and mixed full-width/column pages before further changes | #40 diagnostics / #82 corpus report; record omission explicitly, do not label the heuristics universally correct |
| P2, already reconciled | Retain snapshot-bound EDA outputs; refresh only intentionally and recheck all dependent counts/hashes | Closed #34 and [EDA replay](eda-replay.md); #49 owns preparation-method documentation |
| P1, remaining verification | Run complete HTML-first sample, preserve HTML anchors and null PDF pages, verify persistent transport, and measure semantic retrieval separately | Open #82; no implied new commitment for its assignee |

Priorities here are remediation recommendations, not measured error rates or
GitHub severity labels. No teammate is newly assigned by this document. Suggested
runtime changes remain unimplemented; this PR does not assert they were fixed.

## Downstream use

Use the current corpus for citation-bearing passage retrieval with the above
limits. Before generated claims use numeric/table/figure evidence, reviewers
must compare the original located page and preserve the check. Report source
mode and missing content in run artifacts. Keep research support, regulatory
grounding, and named human approval separate. Final Week 7.5/8 relevance and
business scoring still needs frozen runs and actual independent reviewers.

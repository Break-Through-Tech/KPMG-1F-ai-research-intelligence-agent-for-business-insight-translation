# Issue #82: HTML-first corpus and citation handoff

## 1. Executive summary

Retained-passage validation: **PASS**. 25 locked papers; 877 HTML chunks; 0 executed corpus/transport check failures.
Completeness review: **follow-up required**. 114 paragraphs are automatically flagged for possible nested-wrapper omissions across 10 papers. Correct retained citations do not establish complete extraction.
Chroma temporary persistence and reruns: 877 reopened records verified. MiniLM smoke: COMPLETED; expected paper present for 3/3 questions. Original cached PDF fallback: PASS.

## 2. Scope and objectives

Audit the locked corpus, source text, heading anchors, Chroma transport, public search contract, and rerun safety. Production ingestion/retrieval are unchanged. No shared index, cloud service, or API credentials are used.
Storage/search use `src/retrieval.py` and Chroma. `python -m src.data_ingestion.pipeline` is HTML-first; the compatibility entrypoint `python src/data_ingestion.py` remains PDF-only.
`main.py` only initializes the environment. The Gemini human-checkpoint notebook/module is standalone and is not connected to arXiv search; no end-to-end Gemini handoff is claimed.

## 3. Environment and reproducibility

Run UTC: `2026-10-11T00:58:57.000753+00:00`. Branch: `khoi-issue-82-chroma-validation`. HEAD/base: `77ab62ba55ff0ad784c1d3b95ad7e56ad4c50114`.
Python 3.14.2; Chroma 1.5.9; SentenceTransformers 6.1.0.
Uncommitted implementation hashes, all source/corpus hashes, dependency versions, query records, and complete omission evidence are in [the companion JSON](html-ingestion-validation.json). Cached sources only; no downloads or fresh availability checks.
Fresh-checkout prerequisites: install `python -m pip install -r requirements.txt pytest`. The exact audited `data/processed/chunks.parquet`, 25 locked `data/html/<arxiv_id>.html` caches, and any cached PDFs listed under `source_hashes` in JSON are ignored by Git and must be supplied separately at those repository-relative paths. Compare their SHA-256 values with JSON. A code-only clone cannot reproduce the cached-corpus audit; downloading newer sources is a different run.
No `.env` file, Azure credentials, personal Git branches, or existing vector database is needed. Run the base audit with `python -m tests.validate_html_sample --cached-pdf --report-dir audit-output`. Optional semantic checks additionally require an already cached MiniLM model; use new local output paths and regenerate semantic evidence whenever implementation hashes change.
On this Windows run, `TEMP` and `TMP` point to the writable test directory recorded in JSON. Chroma workers exit before their temporary storage is removed.

Run from the repository root (replace angle-bracket placeholders with local output paths). Exact execution commands remain in JSON.
```text
python -m tests.validate_html_sample --cached-pdf --semantic-evidence <temporary-results.json> --test-results <test-results.json>
```

Semantic worker reproduction (set HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1; use a new temporary directory):
```text
python -m tests.html_transport data/processed/chunks.parquet <temporary-index> <temporary-results.json> --semantic
```

## 4. Corpus validation results

PASS: persisted == regenerated == second run. Sources unchanged: True; original corpus and PDF baseline unchanged: True.
The following section coverage counts distinct section labels. Full section/subsection coverage, anchors, source URLs, filtering counts, and excluded section text are retained per paper in JSON.

| Paper | Mode | Chunks | Sections | Source example | Omission candidates | Check failures |
|---|---|---:|---:|---|---:|---:|
| 2602.00937v3 | html | 34 | 8 | [cached anchor](https://arxiv.org/html/2602.00937v3#S1) | 5 | 0 |
| 2602.00933v3 | html | 23 | 7 | [cached anchor](https://arxiv.org/html/2602.00933v3#S1) | 0 | 0 |
| 2602.00931v2 | html | 27 | 8 | [cached anchor](https://arxiv.org/html/2602.00931v2#S1) | 8 | 0 |
| 2603.00829v2 | html | 32 | 10 | [cached anchor](https://arxiv.org/html/2603.00829v2#S1) | 0 | 0 |
| 2603.00824v2 | html | 41 | 13 | [cached anchor](https://arxiv.org/html/2603.00824v2#S1) | 20 | 0 |
| 2603.00823v2 | html | 26 | 9 | [cached anchor](https://arxiv.org/html/2603.00823v2#S1) | 0 | 0 |
| 2604.00324v1 | html | 145 | 8 | [cached anchor](https://arxiv.org/html/2604.00324v1#Ch1) | 42 | 0 |
| 2604.00319v1 | html | 47 | 7 | [cached anchor](https://arxiv.org/html/2604.00319v1#S1) | 22 | 0 |
| 2604.00314v1 | html | 22 | 6 | [cached anchor](https://arxiv.org/html/2604.00314v1#S1) | 5 | 0 |
| 2605.00292v2 | html | 34 | 8 | [cached anchor](https://arxiv.org/html/2605.00292v2#S1) | 7 | 0 |
| 2605.00276v1 | html | 27 | 8 | [cached anchor](https://arxiv.org/html/2605.00276v1#S1) | 2 | 0 |
| 2605.00273v2 | html | 35 | 11 | [cached anchor](https://arxiv.org/html/2605.00273v2#S1) | 0 | 0 |
| 2606.01502v1 | html | 45 | 9 | [cached anchor](https://arxiv.org/html/2606.01502v1#S1) | 25 | 0 |
| 2606.01498v1 | html | 24 | 6 | [cached anchor](https://arxiv.org/html/2606.01498v1#S1) | 2 | 0 |
| 2606.01494v1 | html | 32 | 14 | [cached anchor](https://arxiv.org/html/2606.01494v1#S1) | 20 | 0 |
| 2607.00276v1 | html | 67 | 10 | [cached anchor](https://arxiv.org/html/2607.00276v1#S1) | 2 | 0 |
| 2607.00275v1 | html | 23 | 8 | [cached anchor](https://arxiv.org/html/2607.00275v1#S1) | 8 | 0 |
| 2607.00274v1 | html | 18 | 9 | [cached anchor](https://arxiv.org/html/2607.00274v1#S1) | 22 | 0 |
| 2608.00345v1 | html | 21 | 6 | [cached anchor](https://arxiv.org/html/2608.00345v1#Sx1) | 7 | 0 |
| 2608.00339v1 | html | 10 | 5 | [cached anchor](https://arxiv.org/html/2608.00339v1#S1) | 43 | 0 |
| 2608.00335v1 | html | 25 | 7 | [cached anchor](https://arxiv.org/html/2608.00335v1#Sx1) | 4 | 0 |
| 2609.00498v1 | html | 36 | 11 | [cached anchor](https://arxiv.org/html/2609.00498v1#S1) | 5 | 0 |
| 2609.00495v1 | html | 23 | 6 | [cached anchor](https://arxiv.org/html/2609.00495v1#S1) | 9 | 0 |
| 2609.39215v1 | html | 42 | 6 | [cached anchor](https://arxiv.org/html/2609.39215v1#S1) | 1 | 0 |
| 2609.39199v1 | html | 18 | 5 | [cached anchor](https://arxiv.org/html/2609.39199v1#S1) | 5 | 0 |

## 5. ChromaDB persistence and retrieval verification

Deterministic transport: 877 indexed, 877 after identical rerun, 877 reopened in a fresh process. Original IDs and stored passage/citation linkage checked for every record; one exact-text query per paper.
Public `search(query, top_k=5)` returns `chunk_id`, `text`, `distance`, `arxiv_id`, `title`, `pdf_url`, `source`, `source_url`, and nullable `page_number`; available section/subsection fields survive. Distances remain distances. No ID encoding or score substitution is used.
Existing metadata updated; one stale row removed (876 remain). Invalid citation rejection and a failure injected before upsert preserve the previous data.
A failure injected after upsert at stale deletion demonstrates partial updates: new metadata is visible and the stale record remains searchable. A successful retry repairs it. **Atomic corpus rollback and process-crash recovery are not guaranteed or demonstrated.** Production also leaves Chroma client lifecycle to callers; temporary-test cleanup explicitly releases its systems.

### Actual MiniLM smoke test

Status: COMPLETED. Model: `all-MiniLM-L6-v2`, 384 dimensions, CPU, cached weights only. Indexed records: 877.
Expected papers/evidence were selected before search. The three questions are content-informed smoke probes, not held-out evaluation. MiniLM is configured for 256 tokens, so long character-based chunks can be truncated during embedding.

| Question | Expected paper | Top result | Section | Distance | Review |
|---|---|---|---|---:|---|
| How can we evaluate agents using realistic multi-step workflows across external tool servers? | 2602.00933v3 | `2602.00933v3_c0002` | introduction | 0.7888 | Pending human inspection |
| How can point clouds and action information improve three-dimensional robotic manipulation pretraining? | 2602.00937v3 | `2602.00937v3_c0000` | abstract | 0.6883 | Pending human inspection |
| Can Fourier transforms replace attention to reduce the cost of processing long sequences? | 2605.00292v2 | `2605.00292v2_c0009` | related work | 0.6078 | Pending human inspection |

## 6. Citation verification

All retained HTML passages are checked against the cited parsed section and ordered source words in the original cached DOM. Actual section/subsection headings (ignoring formatting whitespace) and source anchors are checked independently. HTML page numbers must be null.
Original cached PDF fallback: PASS; paper `2602.00937v3`; 28 chunks checked against their original cleaned PDF pages and transported through temporary Chroma with `#page=N` citations.
The main 25-paper corpus remains HTML-only. This separate fallback run uses an original cached PDF; automated PDF fixtures remain synthetic. Neither check establishes visual table fidelity, OCR quality, or complete extraction.

## 7. Omission candidate findings

Reproduced candidates: **264**. Categories use paragraph-level filter projections and exact normalized comparisons; they do not certify scientific completeness.

| Category | Candidates |
|---|---:|
| false_positive_review_candidate | 34 |
| intentionally_excluded_low_value_or_back_matter | 24 |
| parser_chunking_needs_investigation | 5 |
| potentially_missing_meaningful_text | 113 |
| scientific_detail_filtered | 88 |

The structural flag overlaps the primary categories: {'potentially_missing_meaningful_text': 113, 'scientific_detail_filtered': 1}. Structural candidates comprise the primary-category counts above; in this corpus, 113 are potentially missing meaningful text and one is scientific-detail filtering (`2609.00495v1` / `S2.SS0.SSS0.Px1.p1`, containing four filtered equations). Equation/proof filtering takes precedence in the primary category; the structural flag independently detects absent projected prose. These are automated detections, not 114 individually human-verified defects.
The manually inspected examples below were checked against cached DOM, parser output, and persisted text during the original audit; their automated absence checks are rerun here. Confirmed behavioral examples are the manually inspected ClawHub scanner-disagreement, gauge-theory dual-use-risk, and jailbreak-definition passages below: their projected prose is absent from the parser and persisted corpus. This does not confirm the other candidate passages. Zero executed check failures concerns retained text/citations and transport, not extraction completeness.

Manually inspected examples (limited to the examples listed below; not all automated candidates):

- `2604.00324v1` / `Chx2.p1`: **intentionally_excluded_low_value_or_back_matter**. A PhD is long and challenging. It doesn’t get done in isolation, and I have innumerable people to thank. I want to flag attention to those who have been especially important, but there are many who do Projected prose retained: False; automated structural candidate: False.
- `2602.00937v3` / `S3.SS2.p4`: **scientific_detail_filtered**. Contrastive Loss. The encoders are trained to minimize a SigLIP-style loss [ 61 ] over the three modality pairs: image-text, image-action, and text-action. Projected prose retained: True; automated structural candidate: False.
- `2606.01494v1` / `S1.SS0.SSS0.Px3.p1`: **potentially_missing_meaningful_text**. We anticipated that three scanners applied to the same 67,453 skills would yield substantial overlap; the actual overlap is minimal (Section 6 ). Any two scanners agree on fewer than one in ten of the Projected prose retained: False; automated structural candidate: True.
- `2603.00824v2` / `S12.SS0.SSSx1.p2`: **potentially_missing_meaningful_text**. As with most interpretability work, these tools are dual-use. They can be used to audit, debug, and improve model transparency, but they may also help an adversary identify representation regimes with Projected prose retained: False; automated structural candidate: True.
- `2609.00498v1` / `Thmdefinition1.p1`: **potentially_missing_meaningful_text**. The operational criterion requires (1) relevance to the harmful intent; (2) factual correctness against reliable task-appropriate evidence; (3) ordering compliance for executable dependencies; and (4) Projected prose retained: False; automated structural candidate: True.
- False-positive example `S2.SS4.SSS0.Px2.p1`: projection is fully present after harmless tag normalization; raw paragraph mismatch alone would overstate missing content.

Parsed sections without chunks: **7**. Their exact section/subsection/anchor association is checked; a different subsection cannot satisfy coverage.

- `2603.00824v2` / `S7.SS1` / stability and concentration: result d > why conditioning matters: polar factor perturbation: 129 characters. Below 150-character HTML threshold. Excerpt: Let T be nonsingular with \sigma_{\min}(T)\geq s>0 and \/\Delta T\/_{2}\leq s/2 . Then for a universal constant C Higham (1986) .
- `2603.00824v2` / `S8.SS1` / atlas method (pipeline) > pipeline summary: 35 characters. Below 150-character HTML threshold. Excerpt: Atlas Method (post-hoc cartography)
- `2604.00319v1` / `S7` / acknowledgement > : 136 characters. Below 150-character HTML threshold. Excerpt: This work is partially supported by SheQAI Research and the University of Alberta-Huawei Joint Innovation Centre (project number Z
- `2605.00276v1` / `S4` / agentic system for trip planning > : 144 characters. Below 150-character HTML threshold. Excerpt: In this section, we introduce our Agentic AI system as well as the method that improves the performance for the trip planning opti
- `2606.01494v1` / `S11` / threats to validity > : 66 characters. Below 150-character HTML threshold. Excerpt: We follow measurement-study practice and state threats explicitly.
- `2609.00498v1` / `Sx1` / acknowledgments > : 118 characters. Below 150-character HTML threshold. Excerpt: Funding granted by Capital One Illinois Center for Generative AI Safety, Knowledge Systems, and Cyber Security (ASKS).
- `2609.00495v1` / `Sx1` / acknowledgments > : 91 characters. Below 150-character HTML threshold. Excerpt: This work has been supported by an ONR grant N00014-23-1-2137 and an NSF award CNS-2442976.

## 8. Tests and results

- `python -m pytest tests/test_html_sample_validation.py tests/test_retrieval.py tests/test_pdf_page_citations.py -q` — 22 passed, 1 warning, 24 subtests passed in 102.17s (0:01:42); exit 0.
- `python -m pytest -q` — 69 passed, 2 warnings, 56 subtests passed in 112.98s (0:01:52); exit 0.

Warnings: Python 3.14 dependency deprecations in Chroma (`asyncio.iscoroutinefunction`) and Google GenAI (`_UnionGenericAlias`). They do not indicate failed citation/storage checks. No warnings are suppressed and no dependency upgrade is attempted.

## 9. Known limitations

The inspected examples demonstrate nested-wrapper gaps; the remaining candidates need individual review. Source coverage also has and intentional equation/table/proof/back-matter exclusions. Short sections below 150 characters can still contain meaningful caveats. No visual layout evaluation, fresh-source check, paid Gemini call, full answer-generation handoff, held-out retrieval benchmark, process-kill test, or atomic rollback test was performed.
Production citation metadata omits `high_value`, authors, and categories; those remain in Parquet but are not part of the current public search contract. The retrieval module has no Azure dependency or credential requirement; private `.env` settings are irrelevant to backend selection.

## 10. Follow-up recommendations for #40 and #43

**#40:** reproduce direct child `ltx_paragraph`, `ltx_subsubsection`, and theorem-wrapper omissions. Traverse substantive wrappers while retaining the correct heading and avoiding nested duplicates. Prioritize ClawHub scanner disagreements, gauge-theory dual-use risks, and jailbreak validity criteria. Add owner-reviewed real-source regression cases before regenerating the corpus.
**#43:** record the source IDs/excerpts and risk, decide whether equations, scientific tables, and short caveats should be retained, and track remediation/revalidation. Keep acknowledgement/credit exclusions separate from substantive evidence loss. No comments were posted automatically.
Issue #82 can submit this validation evidence with explicit findings; it must not be presented as proof of complete corpus extraction. Production changes require ingestion-owner review.

### Executed check failures

None. Completeness findings above remain open.

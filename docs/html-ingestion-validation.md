# HTML-first ingestion validation — October 13, 2026

**Passed source/citation transport checks: 25 locked papers, 877 chunks, all HTML.**
This is not semantic relevance, generated-answer correctness, visual fidelity or
human/stakeholder approval. Preserve the [PDF-only baseline](ingestion-validation.md):
its 1,671 chunks do not describe this HTML corpus.

## Inputs and provenance

- Source runtime baseline: `eaaf0e819b5c7aeb9a78be08924a506c10620666`.
- Validator commit: `348d7dca5b3a4751733b23dca772283284f75997`; validator SHA-256 in the [JSON report](html-ingestion-validation.json).
- All 25 arXiv HTML files were **freshly downloaded** in this recovery using the
  existing `download_html` helper, with successful download lines for every ID.
  Validation itself reads cached snapshots; it does not silently re-fetch sources.
- All 25 recovered PDF caches were retained. The forced fallback probe uses cached
  original PDF `2602.00931v2` with a recorded hash.
- Per-paper HTML/PDF source hashes, source URLs, section names, anchor counts,
  intentional omissions, metadata/manifest hashes and Parquet hash are in the JSON.
- Commands execute with the repository's requirements in an isolated Python 3.12
  environment. Actual embedding run package versions are frozen separately.

## Checks and limits

- Every manifest ID yields usable chunks; unique IDs, required metadata and chunk
  lengths are checked. All 877 normal-corpus chunks have existing HTML anchors
  and null PDF page numbers.
- Every chunk is a contiguous span of its cited **cleaned parsed section**.
  A separate original-DOM check verifies lexical tokens in order within that
  exact anchor scope after documented math substitutions and omissions. This
  allows omitted headings/labels between paragraphs; it does **not** establish
  a verbatim uninterrupted raw-source quotation or semantic correctness.
- Figure/table bodies, display equations/proofs, references and appendices are
  intentionally excluded. Seven parsed sections have no emitted chunk, recorded
  per paper: short content under the 150-character HTML chunk threshold can be
  lost. No table, equation, diagram or numerical-fidelity clearance is claimed.
- Exact Parquet readback and an identical ingestion rerun pass.
- Deterministic vectors exercise a real persistent Chroma index: every stored
  document/metadata row matches input, reopen/search preserves citations, and
  repeated upsert removes an injected stale record. These vectors are labeled
  `deterministic-citation-transport-v1-not-semantic`, never as MiniLM embeddings.
- The separate forced-PDF diagnostic verifies 19
  chunks against cleaned text from their original PDF pages. Its mixed HTML/PDF
  diagnostic index contains 869
  chunks; it also passes full stored-row reconciliation, reopen/search, rerun and
  stale cleanup. This diagnostic **does not** replace the normal 877-chunk corpus.
  It is not a full 25-paper fallback or visual-layout audit.

| Locked ID | Normal source | Chunks | Anchored chunks | Parsed sections without chunks |
|---|---|---:|---:|---:|
| 2603.00824v2 | html | 41 | 41 | 2 |
| 2603.00823v2 | html | 26 | 26 | 0 |
| 2604.00314v1 | html | 22 | 22 | 0 |
| 2604.00319v1 | html | 47 | 47 | 1 |
| 2604.00324v1 | html | 145 | 145 | 0 |
| 2602.00931v2 | html | 27 | 27 | 0 |
| 2605.00276v1 | html | 27 | 27 | 1 |
| 2602.00937v3 | html | 34 | 34 | 0 |
| 2605.00292v2 | html | 34 | 34 | 0 |
| 2602.00933v3 | html | 23 | 23 | 0 |
| 2603.00829v2 | html | 32 | 32 | 0 |
| 2606.01494v1 | html | 32 | 32 | 1 |
| 2606.01498v1 | html | 24 | 24 | 0 |
| 2606.01502v1 | html | 45 | 45 | 0 |
| 2605.00273v2 | html | 35 | 35 | 0 |
| 2607.00274v1 | html | 18 | 18 | 0 |
| 2607.00275v1 | html | 23 | 23 | 0 |
| 2607.00276v1 | html | 67 | 67 | 0 |
| 2608.00335v1 | html | 25 | 25 | 0 |
| 2608.00339v1 | html | 10 | 10 | 0 |
| 2608.00345v1 | html | 21 | 21 | 0 |
| 2609.00495v1 | html | 23 | 23 | 1 |
| 2609.00498v1 | html | 36 | 36 | 1 |
| 2609.39199v1 | html | 18 | 18 | 0 |
| 2609.39215v1 | html | 42 | 42 | 0 |

## Real embedding capture — execution proof, unscored

Frozen [run](../evaluation/runs/2026-10-13-html-first-retrieval/run.json),
[blank worksheet](../evaluation/runs/2026-10-13-html-first-retrieval/review.csv),
[unscored report](../evaluation/runs/2026-10-13-html-first-retrieval/unscored.json).

- Real `all-MiniLM-L6-v2` embeddings for all 877 normal-corpus chunks.
- All persisted text/citation metadata reconciled to the validated Parquet before
  capture; metadata, corpus, indexed-content and model-weight hashes are recorded.
- All ten original benchmark questions executed with **zero failures**.
- Run ID: `a8bb871d261d4ab0345ab32015fab93c2a160cdd56a89476c1553246fa44a92d`.
- Capture commit: `aafc034471b120d954c4798b77fee10e0a915d64`. The capture records dirty state
  because the report/documentation handoff was being prepared; the executable
  capture script is separately SHA-256 bound. No runtime patch is hidden by this.
- No generation call was made; no key was configured. No real business adapter
  or actual human scores were supplied. Summary placeholders explicitly state
  generation was not requested; they are not judgments of corpus answerability.
- Empty review input produces null quality metrics, no target pass and
  `approved=false`. Successful queries are not measured Precision@5.

## Reproduce without overwriting frozen evidence

Fetch absent sources once using existing helpers, then run the dedicated validator:

```sh
python -c 'from src.data_ingestion.metadata import load_metadata; from src.data_ingestion.download import download_html, download_pdfs; m=load_metadata(); download_html(m); download_pdfs(m)'
python -m tests.validate_html_sample --output /tmp/new-html-validation.json
python -m evaluation.capture_validated_retrieval --validation /tmp/new-html-validation.json --output /tmp/new-frozen-retrieval
python -m unittest discover -s tests
```

The validator uses cached sources; the explicit download command can contact
arXiv and the capture can download public embedding weights. Neither calls a
billable generation API. Different source/package/model snapshots may change
counts or rankings; compare hashes, not filenames alone. Frozen outputs refuse
overwrite. Failed validation must be resolved or reported, not bypassed for a
quality claim.

## Handoff and issue status

The source/corpus and transport deliverables for #82 are implemented in this
candidate. Keep #82 open until review/merge. #64/#65 still need actual combined
generation/business outputs and named human scoring; #57 still needs team pilot,
allocation and confirmed answerability. See [acceptance reconciliation](issue-reconciliation.md).

Empirical short-section omissions and intentional table/diagram/notation losses
are routed to #43 and #40 as additional evidence, not a duplicate broad cleaning
issue. No newly confirmed runtime bug or semantic failure is inferred from an
unscored run.

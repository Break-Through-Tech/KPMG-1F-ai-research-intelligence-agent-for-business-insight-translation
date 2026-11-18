# Evidence visualization spec: tables and charts

Status: **implemented in the isolated prototype (2026-11-17).**

| Part | Where |
|---|---|
| Model | `ui-consult/evidence.js` (§3–§7) |
| Rendering | `ui-consult/app.js` (`renderEvidenceTable`, `chartView`, `renderStudies`) |
| Read-only endpoint (§8) | `D:\KPMG-demo-corpus\table-endpoint-exp\` (outside both checkouts) |

**Differences from the proposal below:**
1. **Charts.** Rule C2 is met only through the endpoint. The chart is a dot plot, or a paired dot plot when rows pair cleanly. Scale ends are labelled with the actual min and max cell text instead of computed ticks, so every chart label is either a cell value, a column header or a category label from the table. Bar charts were not needed.
2. **Endpoint request.** The endpoint takes `chunk_id` and `index`, the answer's `provenance.index.indexed_records_sha256`. A complete table that disagrees with the answer's own rows on index, source hash, caption, headers or any cell is refused (`mergeComplete`).
3. **Column eligibility.** A column is considered for charting only if at least one cell parses as a plain number. Text and symbol columns are skipped rather than reported as non-numeric.

The original proposal follows, unchanged. It was written from a read-only audit of:
- the Fable worktree `khoi/ui-redesign-prototype` @ `74efcb4`;
- the demo backend export `D:\KPMG-demo-corpus\main-727b0b3` (`src/experimental/html_evidence.py`);
- the 100-paper bundle `demo-bundles/demo-100/parents.jsonl`;
- four local recordings from live research on the 100-paper demo bundle, captured on 2026-11-17.

## 1. What the data already gives us

### 1.1 Table rows are already structured

Every table row that retrieval returns arrives in `result.evidence[]` with `representation: "linearized_table"` and these fields. They come from the deterministic HTML extractor `html-evidence-v2.1-stage-a`, with no LLM involved:

| Field | Example (real, CU-DPO brief) | Use |
|---|---|---|
| `arxiv_id`, `title` | `2602.00931v2` | Paper identity |
| `table_id` / `source_anchor` | `S3.T2` | Groups rows into one table |
| `caption` | "Table 2: In-distribution strategy selection. Comparison between prompt-only baselines and …" | Context, units and conditions, **verbatim** |
| `table_headers[]` | `{column, text: "Acc.", source_id: "S3.T2.8.1.3"}` | Column labels with a source ID per header |
| `table_cells[]` | `{row: 4, column: 2, text: "0.76", source_id: "S3.T2.8.5.2"}` | **Values as recorded**, with a source ID per cell |
| `merged_from_previous_row` | `true` on "DeepSeek-R1 (8B)" | Row-span awareness |
| `table_row`, `row_label`, `row_group` | `4`, "DeepSeek-R1 (8B)" | Row identity and grouping |
| `header_provenance` | `latexml_guessed` / `first_row_assumed` / `html_th_markup` | How headers were found |
| `header_review` | `pending_human_verification` (always, today) | Header validation status |
| `source_notes[]` | footnotes resolved from the HTML | Footnotes (0 of 436 tables in demo-100 have any) |
| `html_url`, `pdf_url`, `source_sha256`, `extractor_version` | `…/html/2602.00931v2#S3.T2` | Deep link and provenance |

The extractor rejects tables rather than guess. It refuses:
- nested tables or figures;
- image cells;
- footer rows;
- ambiguous super- or subscripts;
- partial colspans in the body;
- duplicate or empty headers;
- duplicate rows.

It keeps empty cells as empty and never fills them.

**Fidelity check (done, model-free):** the retrieved cells in the live brief are byte-identical to the bundle's cells for the same rows (both tables, 6 rows).

### 1.2 What is missing

**1. Whole tables.** An answer carries only the rows retrieval chose, and it does not record how many rows the table has.
- The live CU-DPO answer has rows 4, 10, 14 and 16 of table `S3.T2`.
- Those are **only the "+ CU-DPO" rows; all 8 baseline rows are absent.**
- A chart drawn from what the answer carries would show the improved models with no baseline. That is exactly the misleading comparison this spec must prevent.

**2. Units, datasets and metric definitions are not structured.** They exist only as prose in the caption ("Pass@1, %") or as abbreviations in headers ("DM", "HM2", "PN").

**3. The headers are not verified by a person.** `header_review` is `pending_human_verification` everywhere. In the 436 tables of demo-100:

| Header source | Tables | Share |
|---|---|---|
| `latexml_guessed` | 246 | 56% |
| `first_row_assumed` | 187 | 43% |
| `html_th_markup` | 3 | under 1% |

**4. Values come in mixed formats.** Profile of the numeric cells across all 436 tables:

| Format | Count | Examples |
|---|---|---|
| Plain number | 12,271 | `0.76`, `34.8` |
| Percent | 603 | `78.0%` |
| Value with error | 473 | `27.8 \pm 9.6` |
| Value with arrow | 189 | `56.0 \uparrow 4.0` |
| Value with parenthesised delta | 372 | `26.97 (-10.45)` |
| Several values in one cell | — | `29.5 / 50.0 / 20.5` |
| Empty | 188 | — |
| Not applicable | — | `–` |
| TeX marks | — | `\bm{\checkmark}` |

## 2. Data flow

```
paper HTML (arXiv, pinned by source_sha256)
  → html_evidence.py: deterministic extraction (existing, unchanged)
  → retrieval puts selected rows in result.evidence[] (existing, unchanged)
  → [frontend] group rows by (arxiv_id, table_id) → EvidenceTable
  → [frontend] round-trip check: rebuild "Header: value; …" from cells and compare with passage.text
  → [optional backend, NEEDS APPROVAL] fetch the complete table, read-only from the loaded bundle
  → [frontend] strict numeric parse per cell (display is always the verbatim text)
  → [frontend] chart eligibility decision, with a stated reason
  → consultant view: table / chart / "why no chart"
  → source inspector: cell source_id, table anchor, paper link
```

Rules that hold at every step:
- No LLM ever produces, corrects or completes a value.
- The existing citation and numeric validation rules are not changed.
- A visualization never alters what the answer cites.

## 3. Normalized frontend model

This model is built in the browser from data the app already has. It is not a new API.

```
EvidenceTable {
  key                  "2602.00931v2#S3.T2"
  arxiv_id, paper_title, table_id, caption
  html_url, pdf_url, source_sha256, extractor_version
  header_provenance    latexml_guessed | first_row_assumed | html_th_markup
  header_review        pending_human_verification | verified | <other, shown verbatim>
  headers[]            { column, text, source_ids[] }
  rows[]               { table_row, row_label, row_group?, chunk_id,
                         cited_by[]  (citation numbers of claims, limitations and insights that cite this chunk),
                         cells[] { column, text, source_id, merged_from_previous_row?,
                                   parsed: { value, percent, decimals } | null } }
  notes[]              source_notes, verbatim
  completeness         "retrieved_rows_only" | "complete_from_index"
  fidelity             "round_trip_ok" | "round_trip_mismatch"
  caveats[]            generated from the fields above, never from a model
}
```

Fields the spec asks for that **are not available**:

| Field | Status | How it is shown |
|---|---|---|
| unit | Only `%` inside a cell is structural | Otherwise the caption is shown verbatim next to the axis; no unit is inferred |
| dataset or population | Only when a header, row group or caption names it, shown verbatim | No mapping from abbreviations (e.g. "DM → DeepMath") unless the caption itself spells it out, and then only as a quoted caption |
| metric definition | Not available | Header text verbatim, plus the caption |
| experimental condition | Caption and `row_group`, verbatim | — |

The tables and charts display these as "Not stated in the extracted table". They are never left blank silently.

## 4. Table reconstruction rules

1. **Grouping:** rows are grouped by `(arxiv_id, table_id)` only; rows from different tables are never merged.
2. **Order:** rows appear in `table_row` order (the source order); columns in `column` order.
3. **Values:** every cell shows `text` exactly as recorded.
   - TeX in a cell is rendered by the existing `math.js` (KaTeX), with the raw text available on hover.
   - An empty cell shows "empty in source", in muted text with an accessible label. It is never `0` and never `–`.
4. **Row spans:** a cell marked `merged_from_previous_row` is shown once per group with `rowspan`, and the underlying data still carries the value on each row.
5. **Highlighting:** rows cited by the answer are marked with the claim's citation number (the same badge style as citations). Other rows are labelled "retrieved, not cited".
6. **Completeness:**
   - **`retrieved_rows_only`:** the header reads "Showing N rows retrieved for this answer. The paper's table may contain more rows." It never says "Table 2" alone.
   - **`complete_from_index`:** "All N rows from the indexed table."
7. **Header status:** the status is always visible as text plus an icon, never colour alone.

   | `header_provenance` | Label |
   |---|---|
   | `latexml_guessed` | "Column labels inferred from the paper's HTML. Not checked by a person." |
   | `first_row_assumed` | "First row assumed to be the column labels. Not checked by a person." |
   | `html_th_markup` | "Column labels from the paper's header markup. Not checked by a person." |

   "Verified" appears **only** when `header_review === "verified"`.
8. **Round-trip fidelity:** the app rebuilds `"<header>: <cell>; …"` from `table_headers` and `table_cells` and compares it with the last line of `passage.text`, the citation-check text the backend validated. On a mismatch, the reconstructed grid is withheld for that table and the source text is shown instead, with "The structured cells did not match the cited text, so only the source text is shown." This guards against a reconstruction that disagrees with what was cited.
9. **Sorting:** sorting is only by user action, on a column header (`aria-sort`). It sorts by the parsed value; unparseable cells sort last and keep their text. "Source order" is always one click away. There is no default ranking and no "best" highlight, because the direction (higher or lower is better) is not in the data.
10. **Overflow:**
    - The table sits in a horizontally scrollable region (`tabindex=0` and labelled) with sticky column headers and a sticky first column.
    - The region can be wider than the 800px reading column, up to the main area's width.
11. **Source navigation:**
    - Each cell is a button with an accessible label such as "Acc., DeepSeek-R1 (8B): 0.76", and opens the inspector on its row passage.
    - The inspector shows the cell's `source_id` and a link to the table anchor (`html_url`).
    - "Open the paper's table" always links to `html_url`; the PDF link is kept.
12. **Export:** the table is copied as TSV with a provenance footer (paper, table, `html_url`, completeness and header status). The existing `answer-export.js` is not changed; the HTML and Markdown exports keep their current content.

## 5. Chart eligibility rules (deterministic)

A chart is offered (View as table / View as chart) **only if every rule passes**. Otherwise the chart button is replaced with the first failing reason, in plain words.

| # | Rule | Reason shown when it fails |
|---|---|---|
| C1 | One table only (same `arxiv_id` and `table_id`) | "These values come from different tables, so they are not shown on one chart." |
| C2 | `completeness === "complete_from_index"`, OR the chart uses only rows the answer itself compares | "This answer retrieved N rows of a larger table. A chart could leave out baselines or comparison rows." |
| C3 | `fidelity === "round_trip_ok"` | "Structured cells did not match the cited text." |
| C4 | At least one value column where **every** non-empty cell parses strictly (§6) and the column has no empty cells | "Column X has values that are not plain numbers (e.g. ±, arrows, ranges, '–')." |
| C5 | All charted cells in a column agree on `%` or no `%` | "Column X mixes percentages and plain numbers." |
| C6 | At least 2 rows and a non-empty, unique `row_label` per row (plus a `Setting`-style column when labels repeat) | "Rows cannot be told apart without merging." |
| C7 | Different columns go on **separate** axes (small multiples), never one shared axis | n/a: enforced by construction |

The C2 escape hatch: for "only rows the answer itself compares", v1 allows **no exceptions**, so C2 effectively requires the complete table. That is why the read-only endpoint in §8 matters.

Chart forms, chosen deterministically:
- **Dot plot**, one panel per value column (the default). The axis is drawn from the data's own min and max with sensible padding, so there is no truncated-bar illusion.
- **Paired dot plot ("dumbbell")**, when the row labels repeat across exactly 2 values of one categorical column (e.g. "Baseline" vs "+ CU- DPO"). The two values are taken **verbatim** from that column. No difference is computed or drawn as a number unless the table itself has a delta column.
- **Bar chart**, only when every value is ≥ 0, the column is a percentage or count, and the axis starts at 0.
- **Line chart:** never in v1. The tables give no evidence that their rows form a genuine ordered series.

Every chart carries:
- the paper title;
- the table ID and the caption, verbatim;
- the axis title, which is the header text verbatim;
- the completeness and header-status lines;
- the cited-row markers;
- a "View as table" toggle;
- an "Open the paper's table" link.

Hovering or focusing a point shows the cell's verbatim text and `source_id`. Clicking it opens the inspector.

## 6. Strict numeric parse

```
^(?<sign>[+\-−])?(?<int>\d{1,3}(?:,\d{3})*|\d+)(?:\.(?<dec>\d+))?\s*(?<pct>%)?$
```

- The parsed value is used **only** for positioning and sorting.
- Labels always show the cell's verbatim text, so decimal precision (`0.70` stays `0.70`) is preserved.
- These are **not** numbers for charting:
  - `±` / `\pm`, `\uparrow`, `\downarrow`, `(…)`;
  - `/`-separated values, ranges, `x`/`×`;
  - scientific notation, TeX, empty cells, `–`;
  - any letters.
- No arithmetic is ever done on values: no deltas, means, normalization or unit conversion.

## 7. Multi-paper comparison

The live cross-study question abstained correctly, because one paper's passage lacked conclusions. The comparison view must therefore never manufacture a comparison.

- **"What each study measured" matrix:**
  - One row per paper in the evidence.
  - Columns: tables retrieved (caption, verbatim), value column headers (verbatim), the dataset or condition text (only where the caption, row group or header states it) and citations.
- **No shared axis across papers:** values from different papers are never placed on one axis and never ranked against each other. The matrix says: "Measured in different tables under different conditions. Not directly comparable." That holds unless both tables have identical header text **and** identical caption-stated dataset and metric, which no automatic check confirms today. So v1 never claims comparability.

## 8. Isolated full-table endpoint

Rule C2 cannot be met from the answer alone. The experimental backend provides a **read-only, model-free** endpoint over preloaded index rows. The response envelope, citation rules, fingerprints and research generation stay unchanged.

```
GET /api/evidence-table?chunk_id=<table-row chunk ID>&index=<parents.jsonl SHA-256>
200 {
  "arxiv_id", "table_id", "caption", "html_url", "pdf_url",
  "source_sha256", "extractor_version", "header_provenance", "header_review",
  "headers": [...table_headers...],
  "rows": [ { "chunk_id", "table_row", "row_label", "row_group"?, "cells": [...table_cells...] } ],
  "source_notes": [...],
  "complete": true,              // every row the extractor emitted for this table
  "index_sha256": "<parents.jsonl SHA-256>",
  "row_count": <count>,
  "extractor_rows_emitted": <independently audited count>,
  "completeness_check": "extractor_table_audit_v1"
}
404 { "code": "table_not_in_index" }
```

- The experimental handler reads preloaded index rows and checks the extractor audit before responding.
- The consultant UI proxy forwards this route as GET only.
- **Saved briefs:**
  - A fetched table is **not** part of the reviewed snapshot.
  - The table is labelled "Loaded from the current index, not part of the saved brief".
  - It is shown only when its `source_sha256` equals the snapshot rows' `source_sha256`; otherwise "The indexed paper differs from the saved evidence."
- **Without the endpoint** (404, or the mock): `completeness = retrieved_rows_only`, and charts stay off by C2.

## 9. Failure handling

| Situation | Behaviour |
|---|---|
| No table rows in the evidence | No table section. Nothing is synthesized from prose numbers. |
| Prose passage with numbers (e.g. "35–46% to 68–78%") | Shown as a cited quote only. **Never** tabulated or charted ("narrative estimate"). |
| Round-trip mismatch | Source text only, with the reason |
| Unparseable column | Shown in the table; that column cannot be charted, with the reason |
| `header_review` missing | Treated as not checked |
| Endpoint error or timeout | Retrieved rows only, with "Full table unavailable" and a retry |
| Theme, print, screenshot | SVG uses CSS tokens; patterns and shapes differ by series; legible at 1280px |

## 10. Tests required before any chart ships (deterministic, model-free)

**Fixtures:** the real recorded evidence arrays from the 2026-11-17 briefs, plus bundle rows for S3.T2 and S4.T4.fig1, labelled "recorded live data".

1. **Grouping:** 6 rows give 2 tables; row and column order is preserved.
2. **Cell → source mapping:** every rendered cell's `data-source-id` equals the fixture `source_id` (all cells).
3. **Round trip:** rendered text equals fixture `text` for every cell; a mutated cell flips `fidelity` to mismatch and hides the grid.
4. **C2:** the retrieved-only S3.T2 (4/16 rows) produces **no chart**, with the baseline reason.
5. **C4:** S4.T4.fig1's Δ column (`–` in baseline rows) is not chartable; DM, HM2 and PN are, once complete.
6. **C1:** passages from two papers or tables never produce one chart.
7. **Strict parse table:** `27.8 \pm 9.6`, `56.0 \uparrow 4.0`, `26.97 (-10.45)`, `29.5 / 50.0 / 20.5`, `–`, `""` all → `null`; `0.70` keeps 2 decimals in labels.
8. **No computed values:** the chart's DOM text set ⊆ the cell text set plus the header and caption text.
9. **Header label:** `latexml_guessed` never renders the word "verified".

Run the browser tests using the fixture setup in [Integration and QA](INTEGRATION-AND-QA.md).

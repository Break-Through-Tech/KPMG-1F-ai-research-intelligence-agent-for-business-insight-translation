# Consultant research workspace: redesign

Status: **implemented as an isolated prototype** in `ui-consult/` (2026-11-17).

- **Rollback:** the six-fix Fable prototype stays untouched in `ui-next/` (commit `74efcb4`).
- **Direction:** a **redesign**, not a refinement. Fable is the quality baseline, not a layout to keep.

## 1. Who it is for

A KPMG consultant preparing an evidence-backed recommendation for a client or a partner. They know the business domain, not ML papers. They work on a 1280–1440px laptop or monitor, share their screen, and paste numbers into decks.

The page answers, in reading order:

| Consultant question | Where the page answers it |
|---|---|
| What is the answer? | **Answer**: the lead sentence in large serif, with the status column beside it |
| What are the main findings? | **Findings**: one finding per row, each with its citation |
| Which numbers support them? | **The numbers behind the findings**: tables rebuilt from the papers, with a chart only where valid |
| How do the studies compare? | **How the studies compare**: what each paper's evidence actually covers (only when 2+ papers) |
| What does it mean for the client? | **What it could mean for <industry>**: implication, suggested action, assumptions |
| What are the risks and limits? | **Risks and limitations**: two plain columns |
| What needs a person? | **Before you rely on this**: one checklist, each item tied to the field it comes from, plus the review state |
| Where did this come from? | **Sources** table, and the source drawer opened from any citation, table cell or chart point |

## 2. Information architecture

```
┌ top bar 64: brand · Research | Library · question title · mode · Sources · prefs · theme · New research ┐
├ rail 256 (232 ≤1360px) ┬ document (padding clamp(32px,5vw,80px), max 1088px) ─────────────┬ drawer 540 ┐
│ In this brief          │ status line · question (serif 42)                                │ Sources /  │
│  Answer                │ Answer lead (serif 24) + trust line   │ Status column 300       │ Table row /│
│  Findings              │                                        │ Status · Evidence mix   │ Brief and  │
│  Numbers               │                                        │ Industry · Open checks  │ review     │
│  Comparison            │                                        │ Source · Save / Review  │ (overlay;  │
│  Implications          │ ── Findings (720 prose) ──                                       │ never      │
│  Risks & limits        │ ── The numbers behind the findings (wide, up to 1088) ──         │ squeezes   │
│  Before you rely on it │ ── How the studies compare (wide) ──                             │ the page)  │
│  Sources               │ ── Implications · Risks · Before you rely on this · Sources ──   │            │
│  Export & details      │ ── Export, audio and run details · Ask a follow-up ──           │            │
│ This session           │                                                                  │            │
└────────────────────────┴──────────────────────────────────────────────────────────────────┴────────────┘
```

Changes from Fable, and why:

- **One brief on screen at a time.** Fable stacked every answer in one endless thread. Here each answer is a document; "This session" in the rail switches between them.
- **Contents rail instead of section pills.** A persistent outline with the current section highlighted. Sections appear only when they have content (Numbers only with tables, Comparison only with 2+ papers).
- **Composer is not pinned.** On the home page it is the main object. In a brief it sits at the end as "Ask a follow-up", so it never covers reading. The same form element is moved, never duplicated, so the research and clarification state machines are unchanged.
- **Status column beside the answer.** Review state, evidence mix ("1 paper, 2 tables (6 rows), 2 text passages", counted from the evidence, never estimated), industry, the number of open checks (a link to the checklist), the provenance, plus **Save as brief / Review** and **Inspect sources**. This is a typographic definition list, not KPI tiles.
- **Library is a page, not a modal.** Rows show title, review state (icon and words), version, kind and date.
- **Brief and review is a drawer.** Versions, Review and Manage moved from a panel under the answer into a right drawer that opens on the Review tab. The source inspector uses the same drawer frame; opening one closes the other.
- **Removed:**
  - the sticky follow-up dock;
  - the per-answer pill bar;
  - eyebrow labels in capitals;
  - 01/02/03 numbering on insights (they are not a sequence);
  - the bottom tool row as the only path to saving.

## 3. Visual direction

**Operate mode, editorial voice.** A working research tool with the reading quality of a consulting report. The signature move is **source-anchored numbers**: every number in a table or chart is a control that opens its exact source cell (cell ID, row, table caption, paper link).

| Aspect | Rules |
|---|---|
| Type | Serif (Iowan Old Style / Palatino Linotype) for the question, answer lead, section titles and table names; system sans for everything else; mono only for IDs and field names. Prose measure ≤ 720px; line height 1.65 (follows the reading-spacing preference). |
| Colour | Cool paper ground `#f4f5f7`, white surfaces, ink `#13161c`, one accent `#2343b8` (dark: `#91a7ff`). Status colours only where they carry meaning, **always with an icon and words**. No gradients, glass or glow. Not KPMG's proprietary blue or branding. |
| Data | Tabular numerals, numbers right-aligned, sticky header row and sticky label column. The baseline series is a hollow ring and the comparison series a filled dot: shape and colour both differ. |
| Motion | Hover and toggles 150–250ms; drawers 420ms; table/chart cross-fade 300ms (opacity and transform only). No pulsing indicators: Impeccable flagged one and it was removed. `prefers-reduced-motion` turns all of it off. |
| Themes | Light, dark, system and both high-contrast themes from the existing reading preferences. |

## 4. Spacing system

Base scale **4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96**, exposed as `--s1 … --s9`. New CSS uses only these values (the one exception is 10px vertical table-cell padding, for row density).

| Context | Value |
|---|---|
| Inside controls, chip gaps | 4–8 |
| Related controls (table toolbar, status-column actions) | 8 |
| Table cells | 10 × 16 |
| Status rows under a table caption | 8 apart; 16 below the caption |
| Rows in findings, checklist and brief lists | 16–24 vertical, hairline separators instead of cards |
| Section title to content | 24; intro paragraph to content 32 |
| Between sections | 64, with 32 to the hairline rule |
| Answer column to status column | 64 (48 at ≤1360px) |
| Between table figures | 64 |
| Home | 96 top; hero to composer 48; composer to industry chips 24; to examples 48; to recent briefs 64 |

Cards are used only where they carry meaning: the composer, the suggested action, the interpretation, table and chart frames, and the clarification card. Lists use hairline rules. There are no nested cards.

## 5. Components

| Component | Behaviour |
|---|---|
| Evidence table | Caption (table name, paper, caption verbatim); status rows (completeness, column-label check, round-trip check); Table / Chart switch with the reason a chart is unavailable; Copy (TSV with a source footer); Open in paper; scrollable table with sticky header and label column; sort by any column (asc → desc → source order); row marks: citation numbers for cited rows, a ring for retrieved-not-cited rows, unmarked for rows loaded from the index |
| Evidence chart | One SVG with shared row labels and one independent scale per column; scale ends labelled with the actual min and max cell text (no computed ticks); every point focusable and openable; the legend uses the table's own category labels |
| Study matrix | Study · what the retrieved evidence covers · values reported (column labels verbatim) · citations; ends with the explicit "not placed on one scale or ranked" note |
| Verification list | Generated by `EvidenceModel.verificationItems` from recorded fields only; each item shows "From <field>" |
| Drawers | Sources (the existing source reader plus a "Table row as extracted" grid with the selected cell outlined) and Brief and review |

## 6. Not added, on purpose

- KPI tiles, confidence percentages, scores, progress rings, sparklines.
- React, React Bits, shadcn/ui, GSAP, Lenis or Motion: the app is vanilla JS under a `script-src 'self'` CSP, and CSS plus View Transitions cover the motion.
- Webfonts and icon packages: system fonts and the existing inline icon set, extended with four icons (table, chart, copy, info) in the same stroke.

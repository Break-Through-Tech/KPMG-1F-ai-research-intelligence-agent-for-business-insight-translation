# Research-publication redesign (2026-11-26)

Supersedes the layout in `CONSULTANT-DASHBOARD-DESIGN.md`. Frontend only: same API contracts,
same reliability rules, no backend or model changes. Screenshots: `redesign-2026-11-26/before`
and `/after` (mock data, `?mock=1`; desktop only).

## Principle

The answer is the product. Everything else is one click away, in this order:

| Layer | Where | Contents |
|---|---|---|
| 1 Answer | Answer view | Question, one line of cited papers, the recorded lead and findings as serif prose with inline citations, a chart beside the finding that cites its table, requested implications, and one line for each material uncertainty (partial answer, failed stage, unresolved discrepancy) |
| 2 Research notes | Folded under the answer | How the answer was checked (quotations, claim support, completeness, human approval, each in plain words), what it does not cover, discrepancies, limitations, business risks, other notes |
| 3 Evidence | Evidence view | Every statement with its exact quotes, source tables (table/chart), comparison of papers, the checklist with field origins, review state |
| 4 Diagnostics | Bottom of Evidence, folded | Run details, provenance, agent trace, arXiv candidates, raw JSON |

Sources view: one entry per paper (cited first), with its passages, each marked "Cited by n
statements" or "Retrieved, not cited". Citations open the inspector, which docks beside the
reading column at ≥1280px so the sentence being checked stays visible.

## Rules the renderer follows

- No text is written or reworded by the page. Headings in long answers are the cited paper's own
  title, used only when consecutive findings form 2–4 runs of two or more per paper; order never changes.
- A partial answer's `answer_lead` that equals one of its coverage gaps (evidence-led pipeline) is shown
  as "Partial answer. <gap>", never as a headline.
- Features that were not requested are not announced ("Business translation was not requested" is gone).
- Numbers are bolded in place, inside their sentence; standalone KPI tiles are no longer rendered.
- A chart is placed in the answer only when a finding cites a row of that table; otherwise it stays in Evidence.

## Tokens

Inter (UI) and Source Serif 4 (prose), local only under the CSP; fallbacks are Segoe UI and Sitka Text
(lining figures), then Georgia. Colour (KPMG theme): default light theme has a KPMG-blue (#00338D) sidebar
and top bar with white text and the KPMG logo (white, `kpmg-logo-white.png`) at the top left; the reading
area is white with black text. Dark theme is KPMG blue throughout with white text. Text is only black or
white, whichever contrasts more with its background; status colour (ok / warn / bad) appears only in icons.
Blues ramp (#DEEBF7 … #08306B) for surfaces, rules and chart series. Prose 20px / 1.65, lead 22px,
question 26px, column 800px.

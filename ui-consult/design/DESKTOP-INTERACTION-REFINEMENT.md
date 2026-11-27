# Proofline desktop interaction refinement

The reader work on `khoi/azure-ux-refinement` through `ed15a63` is carried forward on `khoi/proofline-integrated-ux`, based on `877300c`. The KPMG-blue shell, white reader, bundled Inter, and four research views carry forward as well.

## Integrated Business insight

Workspace shows the cited interpretation and suggested action before controls to generate an update. Assumptions, risks, source limitations, and additional interpretations are available in disclosures. The notice about the limits of applying study results stays visible. Research notes still contains its original checks and warnings.

The Answer footer retains the one-click action for eligible saved research and a shortcut to an existing insight. In `app.js`, `renderBusinessForm` and the Workspace render change presentation and focus. The capability flag, eligibility check, request body, automatic context behavior, timeout, and error handling keep the integrated contract. The reader-only changes still need the staged copies and pins described below.

## Browser review

| Pass | Finding | Refinement |
| --- | --- | --- |
| 1 · before and after the reading pass | The saved home offered industry controls without an editable query. Opening the inspector at source 5 could leave its selected marker outside the visible strip. Research notes rendered `null` where sections were absent. | Aligned the saved home to the reader, hid inactive industry controls, centered the selected source when necessary, and kept the four verification facts in one divided panel. |
| 2 · interaction and contrast pass | The chart opened in a dense multi-metric view and buried the metric controls. A fading composer mask could cover evidence and focus. The animated view switch made the timing of keyboard focus depend on a page snapshot. | Open one metric by default, place metric controls above the plot, and retain the all-metrics view. Give the follow-up composer its own space below Answer. Commit navigation state immediately and animate only the selected tab marker. |

The local browser journey uses recorded CU-DPO and Fin-RATE results, including a separately labeled CU-DPO demo with examples added from source tables. It compares the displayed finding text with the fixture, then checks cited rows, quote disclosures, chart keyboard selection, the sidebar, large text, reduced motion, and returning focus after closing the inspector. A second deterministic fixture exercises the loading, follow-up, settings, and recoverable error workflow. Those fixtures test presentation and interaction. They do not measure live research quality.

## `app.js` reconciliation with the integration branch

- **Answer reading layout.** `syncTopbar` now uses the Sources tab count and keeps Save or Review in the header. `renderBrief` shows Research notes and More actions in a single footer. The footer disclosure mounts the existing read-aloud controls on demand and contains the existing exports and optional explanation control. The demo label and material model-count caveat remain visible. If the integration touches `renderBrief`, retain its Business insight and saved-state handling while accepting the new Answer footer. The topbar markup change removes only the duplicate paper-count button from `index.html`.
- **`placeDock`, `setView`, `setTab`, `moveIndicator`.** Use the existing view state and navigation guard synchronously, keep per-tab scroll memory, and move the underline using a single CSS transform. Home and End now join the arrow keys. The composer uses the natural document layout beneath Answer.
- **`syncSettingsSummary`, `loadRecentBriefs`, `loadQuestionEntry`.** Hide the inline industry shortcuts in recorded-only mode and use read-only library copy on that home screen. Preserve the integration branch’s business-translation controls, configuration reads, and request handling when resolving nearby changes.
- **`showEvidence`.** Scroll the existing passage strip to the selected source and avoid replaying an entrance animation on each selection. Source identity, claim linkage, and quote rendering use the same records and helpers.
- **`paragraphs`, `renderBrief`.** Group recorded findings into shorter paragraphs without reordering or editing them. Skip absent DOM sections in Research notes. Keep the integration branch’s interpretation, save, and review logic in this area.
- **`chartView`, `viewBody`.** Start on a single metric, expose the existing selector and optional glossary, and show one selected state through `aria-checked`. Plot generation, eligibility, original scales, and cell inspection remain on the existing paths.

Rebuild the hosted copy from the reconciled `ui-consult/app.js` and `consult.css`. Verify the corresponding files under `onboarding/frontend/ui-consult/design/merge-with-codex/`, the frontend manifest in `onboarding/assets.json`, and the check in `experiments/render-staging/stage.py`. The two frontend source files and their staged counterparts are intended to be byte-identical after LF normalization.

## Final product polish

The four tabs share the same reading column and typography. Sources keeps papers and passage links together, Evidence keeps the tables and charts, and Workspace holds business interpretation, research notes, and review. The separate inline Business insight change is at `36709f76c9a1dac27119bbc6f76c5ab4f6d336cf` on `integration/proofline-business-hydrogen`. During reconciliation, place its `.answer-business` section after the findings and before the reading footer. Its existing interpretation, action and disclosure markup uses the new reader styles. Retain the integration branch’s generation, pending states, and form behavior.

This polish changes three presentation areas in `app.js`: `setInspector` marks the table row that opened the inspector, `renderBrief` shows four compact verification disclosures with the original explanations, and `sourceRow` presents table row context beneath the row label. Research notes retains the visible discrepancy and original review limitations.

## Design references and decisions

- [Impeccable](https://impeccable.style/) supplied the critique, audit, and simplification criteria. Findings were checked against the browser rather than estimated from code. The review used the local reference text and existing fixture tooling.
- [Apple Design](https://github.com/dickwu/apple-design-skill) supplied desktop layout, focus, contrast, and material principles. A subtle material remains on the temporary citation preview, with an opaque reduced-transparency treatment. The reader, dock, and inspector use opaque surfaces.
- [Emil Design Engineering](https://github.com/emilkowalski/skills) supplied timing and interruption principles. Short control feedback and the tab indicator remain. Large entrances, repeated skeleton motion, and width animation on the docked inspector were removed.
- [Vercel Web Interface Guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) informed keyboard, visible focus, contrast, and form checks. [Linear](https://linear.app/docs/display-options) and [Perplexity](https://www.perplexity.ai/help-center/en/articles/10352903-what-is-pro-search) served as interaction and reading references.
- [Taste Skill](https://github.com/Leonxlnx/taste-skill) and [Uizze](https://uizze.com/) were reviewed for art direction. The existing product identity and research density made custom illustration, a marketing-style hero, and reference-service automation a poor fit.

The approved white appearance remains the default and only color theme in Display preferences. The existing 100%, 125%, and 150% reading sizes and spacing settings remain available. Desktop browser checks used Chromium. Hosted verification used synthetic local data.

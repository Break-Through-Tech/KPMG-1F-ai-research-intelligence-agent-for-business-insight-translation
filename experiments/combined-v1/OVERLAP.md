# Paper reuse and overlap (fresh-business-v1)

All 13 papers (2501.17755v2, 2503.05773v1, 2505.15753v1, 2406.06622v1, 2402.08416v1, 2510.02833v4, 2403.13313v1, 2402.09742v4, 2508.08345v2, 2506.23273v2, 2602.16977v1, 2601.17692v1, 2606.28456v1) appear in **no** earlier question, reference, label, case, benchmark, build or fixture file. That covers F01–F10, H01–H10, C01–C15, the tests and the evaluation folders (strict scan: 0 files each).

**Broad scan** (saved run outputs under `data/processed`):

- Seven of the papers appear as retrieved distractor passages in 3–10 earlier run files. No earlier question targeted them.
- 2505.15753v1, 2406.06622v1, 2402.08416v1, 2403.13313v1 and 2602.16977v1 appear nowhere.

**The questions are new.** No model has seen them.

**Known limitation:** the evidence budget is selected offline on these same questions (see SELECTION-RULE.md), so the live evaluation is preliminary.

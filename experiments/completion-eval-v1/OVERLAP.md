# Paper reuse and overlap (completion-eval-v1)

| | Papers |
|---|---|
| Never used in any prior question, reference, label, test or live-run file | 2506.10022v1 (MalwareBench), 2505.14607v3 (sudoLLM), 2405.19358v2 (Ctrl), 2601.07754v1 (KG financial reasoning), 2412.21154v1 (Aviary), 2602.11351v2 (BAO), 2508.19097v1 (medical reasoning survey) |
| Not in F01–F10 or H01–H10 | 2508.03553v1 (MultiRAG), 2502.06864v1 (KG²RAG), 2402.12713v2 (FBI), 2511.08621v1 (LLM Pro Finance), 2401.11641v5 (finance overview), 2506.23123v1 (FMTI) |
| **Overlap with the held-out set** | 2510.24402v1 (metadata-driven financial RAG), used in H01 and H04 |

**Overlap detail for 2510.24402v1.** C14 targets a different aspect: the latency column of Table 1 and the authors' own business-implication discussion (c0045). However, the F1 values in C14.1 (44.4) and C14.2 (43.2) also appear in H01.2. The answer for C14 may therefore reflect prior familiarity at the question-design level only. No model has seen these questions.

**Scans run:**

- A broad scan (any evaluation artifact) found the six papers in the second row mentioned in 1–3 evaluation files (e.g. retrieval logs).
- A strict scan (question, reference, label, case and benchmark files, excluding corpus-wide listings) found none of them.
- No prior question targets the aspects used here.

**Excluded:** papers in F01–F10, plus H01–H10 papers other than 2510.24402v1.

# fresh-v3 answer key: review record

| Step | Date | Who | Outcome |
|---|---|---|---|
| Draft (authored from bundle passages only; no engine run on the questions) | 2026-11-25 | Claude (AI-assisted) | 8 questions, 38 points; every anchor group, alternatives included, checked against all required facts |
| Focused independent review (one round) | 2026-11-25 | Fresh-context Claude reviewer (**AI, not human**; no access to the conversation, engine code, scores or results) | CHANGES: 7 substantive errors. Each was verified against the corpus by Claude and corrected (below). Borderline cases were frozen in `AMBIGUITIES.md` |
| Seal | 2026-11-25 | Claude | Sealed once after the corrections (`seal.json`, via `seal_v3.py`) |
| Human sign-off | pending | Project lead | — |

**Corrections:**

1. **J01.3:** anchored the 15–20% variant (c0002) and the conclusion that calls it a target (c0020).
2. **J04.3:** added c0003, which states the BERT classifier.
3. **J05.1:** added c0003, which states "4-bit".
4. **J07.3:** added c0003, which gives the BERT and GPT-2 examples.
5. **J02.2:** added c0000, which states "learn affinity metrics".
6. **J02.4 and J08.4:** the authors' switching rule is Tanimoto > 0.2, not 0.3. "Non-RAG below 0.3" scores 0.5 at most.
7. **J08.2:** replaced the DFT-refinement figure, which does not isolate retrieval, with the no-RAG ablation (stability 23% without retrieval vs 82% with; c0018, or c0020 as an alternative).

**Checks the reviewer confirmed:**

- **Evidence limits:** J05.5, J06.4 and J07.6 are genuinely not established anywhere in their papers.
- **Misleading probes:** J04.4 and J04.5 are correct (c0012 calls Med-CoDE "comparable", about 207 vs 190 of 265), and the J01.3 ruling is sound once the anchor fix is applied.

**Unchanged:** the question wording, the 38-point total and the acceptance criteria. No further review round is planned.

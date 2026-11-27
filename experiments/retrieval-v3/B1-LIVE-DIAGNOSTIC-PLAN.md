# S2 + B1 (opt-in paper balance): implementation status and live diagnostic plan

**Status:**

- **Plan only.** No live calls; nothing is wired into the shared application; nothing is committed.
- **Git coordination:** all files are in `experiments/retrieval-v3/`, and no git operations were performed, so Codex's checkpoint and push work is unaffected.

## Implementation (done, 0 calls)

`s2_paper_balance.py` provides `S2Research(paper_balance=False|True)`, which subclasses the frozen V2 engine.

**Default (`paper_balance=False`):** exactly frozen S2. This is verified by test.

**Flag on:** only evidence selection changes, and only when two or more papers named in the question are in S2's top-120. Everything else is the frozen code:

- synthesis, review and publication gates;
- the 6,000-token budget, the C2 allowance and the passage cap;
- the 2-call structure, with no extra searches.

The packet records `paper_balance: {enabled, requested_papers, applied}` for audit.

**Tests:** `test_s2_paper_balance.py`, 11 tests; all pass, together with the 40 S3 tests.

| Area | What is covered |
|---|---|
| Paper resolution | two named papers; overlapping titles (FooNet vs FooNet-2: whole-word only); model names (GPT-4o never resolves a paper); missing paper (named but not retrieved, so no balancing); unnamed subject |
| Selection | single-paper questions byte-identical to S2; two papers balanced in S2's own order; base tokens ≤ 6,000; passages ≤ cap; table groups kept whole |
| Engine flag | flag off reproduces frozen S2 evidence; flag on records and applies the balance |
| Reproduction | the engine matches the offline B1 coverage exactly on all 6 triggered development questions |

## Proposed live diagnostic (needs your approval)

| Item | Plan |
|---|---|
| Questions | fresh-v3 **J03** (demo-100 index) and fresh-v4 **K05**, **K07** (validation index): the three cases where B1 recovered evidence |
| Arm | S2 + B1 only. The comparison is the **saved** S2 outputs for the same questions (same provider, gpt-6.1-sol low), with no S2 rerun |
| Calls | 6 expected (2 per question), **hard cap 8**, persistent ledger, one resume per question |
| Scoring | the existing sealed keys; a blind A/B packet (saved S2 vs B1) for a fresh Codex scorer; my check of every flag; your adjudication |
| Measures | answer points per question, citation-grounding and misleading flags, latency (B1 median vs saved S2), actual input tokens (B1 vs saved S2) |
| Expectations, not targets | about +2–3 points in total across the three questions, safety unchanged, latency and tokens within about ±5% of S2 |

**Caveat:** these are development cases, so the test confirms that recovered evidence turns into answer points. It is **not** evidence of generalization.

## Integration validation (later, during production testing)

- **Fresh named questions:** add 3–5 previously unseen cross-paper questions that name two papers, written against the production corpus during integration testing. Run them on S2 with the flag off and on.
- **Measures:** completeness, citation safety, latency and input tokens.
- **No new benchmark:** this is not a new benchmark cycle; the questions join the integration test set.

## Execution, once approved

I will add a small runner `run_b1_diagnostic.py`, which reuses the fresh-v4 runner's ledger and guard pattern, before you run anything. You then run one command for J03 and one for K05 and K07.

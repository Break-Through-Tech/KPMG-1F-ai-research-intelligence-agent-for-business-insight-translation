# S2 paper-balanced retrieval: offline investigation (0 model calls)

**Scope:** isolated in `paper_balance.py` and `eval_paper_balance.py`; results in `paper-balance.json`. The S2 demo engine and the shared app are untouched.

## Diagnosis (automated reviewer’s finding verified)

On fresh-v4 K05 and K07, the first named paper fills all 30 window slots: HaloGuard and RAG-TRACE take 30 of 30. The second paper's best passage ranks just outside the window:

| Question | Second paper | Best rank |
|---|---|---|
| K05 | PGuard | 42 |
| K07 | ECGJev | 31 |

Both papers are in the candidate pool. S3's component searches ranked PGuard first for two parts of K05, but S3 discarded those results with its original-top-30 paper filter.

## Rule (fixed before measurement; no paper IDs, questions or answers)

1. **Requested papers:** a paper is requested when a named term from the question appears as a whole word in its title and the paper has a passage in S2's top-120. Named terms use the existing extractor; generic acronyms and GPT-* names are excluded.
2. **Two or more requested papers:** the 30-candidate window is filled round-robin across those papers, each in S2's own order, up to 30/n each, then the rest of S2's top-30. The frozen 6,000-token skip-fit, the C2 allowance and the passage cap are unchanged.
3. **Otherwise:** exactly frozen S2.
4. **B2:** as B1, but each paper's candidates also come from paper-scoped component searches.

**Prior work:** this is not the failed decomposition, MMR or diversity work. It adds no queries in B1 and no general diversity penalty. It only stops a single paper from crowding out an explicitly named second paper.

## Results (packed anchored coverage)

Frozen S2 reproduces exactly: 10/10 against the live fresh-v4 S2 packets, and 8/8 on fresh-v3 earlier.

| Set | Points | S2 | B1 | B2 | Triggered |
|---|---|---|---|---|---|
| heldout-v1 | 27 | 27 | 27 | 27 | 0 |
| completion-eval-v1 | 41 | 34 | 34 | 34 | 0 |
| combined-v1 | 44 | 30 | 30 | 30 | 0 |
| fresh-v2 | 36 | 28 | 28 | 28 | 2 |
| fresh-v3 | 38 | 23 | **25** | 23 | 2 |
| fresh-v4 | 50 | 36 | **40** | 41 | 2 |
| **Total** | **236** | **178** | **184 (+6)** | 183 | 6 |

### B1

- **Recovered:** J03 +2, K05 +2, K07 +2.
- **Displaced:** none, in any set.
- **False triggers:** the rule fired only on cross-paper questions. All single-paper, unnamed-subject and evidence-limit questions are byte-identical to S2.
- **Tokens:** within the same 6k budget (5,980–6,140 incl. C2 versus 5,865–6,119 for S2).
- **Latency:** no added searches or latency.

### B2

- **Recovered:** one more point on K07.
- **Displaced:** H03.5 and J04.1.
- **Cost:** adds component searches, about 3–10 s.
- **Verdict:** **rejected**.

## Limits

- **Coverage of cross-paper questions:** 8 of 14 never trigger, because they describe papers without the title names (e.g. "the catalyst-discovery study", C15, G03–G05, H04, J08). The rule cannot help those.
- **Not generalization evidence:** every gain is on known development cases. K05 and K07 produced the diagnosis itself. There is no untouched held-out test. Treat +6 as development evidence only.
- **Coverage is a proxy:** answer points will gain less than coverage. With about 80% conversion, fresh-v4 would be roughly +3 points (74% → about 80%), and it is unverified live.

## Recommendation

- **Adopt B1** as a small, opt-in change to the S2 demo engine for integration. It has zero displacement, zero cost and zero effect on single-paper questions.
- **Validation path:** validate it inside normal production testing; there is no separate engine evaluation.
- **Do not adopt B2.**
- **Expected effect:** B1 is a narrow fix for named multi-paper questions only. It does not raise S2's general completeness.

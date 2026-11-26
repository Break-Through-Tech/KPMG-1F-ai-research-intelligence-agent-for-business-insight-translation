# B1 live diagnostic: results

**Questions and status:** J03, K05 and K07, all complete. 6 of the 8 allowed calls were used and nothing was rerun.

**Development cases:** these three questions are development cases, not independent evidence of generalization.

## Answer completeness

Blind A/B scoring by a fresh Codex session ("GPT-6"), against the saved S2 answers. The packet hash matches the key.

| Question | Saved S2 | B1 |
|---|---|---|
| J03 | 2.5 | 3.0 |
| K05 | 2.0 | 3.5 |
| K07 | 1.5 | 4.0 |
| **Total** | **6.0 / 15** | **10.5 / 15 (+4.5)** |

**Gained points:**
- J03.2: 0 → 0.5.
- K05.3: 0 → 1. This is PGuard accuracy, the starved paper.
- K05.4: 0 → 1. PGuard overhead.
- K07.1: 0 → 1. ECGJev design.
- K07.2: 0 → 1. ECGJev results.
- K07.3: 0 → 0.5.

**Lost point:** K05.2 (HaloGuard accuracy versus dedicated guards) fell from 1 to 0.5. B1 cited the 83.6 figure but omitted the comparison with dedicated guards and the parameter advantage.

**Conclusion:** the recovered evidence clearly translated into answer points, all of them from the previously starved second paper.

## Safety

- **Blind scorer:** no citation-grounding, misleading or numerical flags.
- **Programmatic audit:** 43 published items, with 0 inexact quotes and 0 number-recall failures.
- **Absence guard:** no uncited absence claim in the answer leads.
- **Claude review:** confirmed no flagged items. The scorer raised none.

## Latency and tokens

| | Retrieval | Synthesis | Review | Output tokens | Input tokens |
|---|---|---|---|---|---|
| J03 S2 → B1 | 6.6 → 13.1 s | 47.0 → 53.6 s | 36.3 → 33.3 s | 3,792 → 3,996 | 41,218 → 42,142 |
| K05 S2 → B1 | 13.9 → 13.9 s | 51.2 → 78.4 s | 33.7 → 47.5 s | 3,933 → 5,975 | 43,274 → 44,726 |
| K07 S2 → B1 | 9.9 → 4.0 s | 35.7 → 60.6 s | 17.3 → 44.2 s | 2,327 → 4,947 | 43,098 → 43,162 |

**Retrieval:**
- No systematic overhead: the times are mixed, with a median of 9.9 s for S2 and 13.1 s for B1. B1 adds no searches.
- The variation is consistent with run-to-run differences in local CPU retrieval.

**Generation:** almost all of the extra time.
- On K05 and K07, B1 wrote 1.5–2.1× more output tokens: its answers cover both papers.
- Generation time scales with output, so this part **is a real consequence of B1**: more evidence, so longer answers.
- Provider-side variance between sessions also contributes. Three questions cannot separate the two.

**Input tokens:** 1.02×. The selection budget is unchanged.

## Frozen criteria

| Criterion | Result |
|---|---|
| At least +2 answer points | **pass** (+4.5) |
| Zero new safety issues | **pass** |
| No loss of previously correct points | **fail** (K05.2: 1 → 0.5) |
| Latency at most 1.10× and tokens at most 1.10× | **fail** on latency (median 1.21×); tokens pass (1.02×) |

## Verdict

**B1 does not pass the frozen diagnostic.** It fails on one lost point and on latency.

**Frozen S2 stays the default**, as decided in advance.

**What the test does show:**
- **Effectiveness:** B1 is effective, at +4.5 points on these named two-paper questions with no safety cost.
- **Cost:** it is slower on those questions, because the answers are longer.

**For later:** whether a 20–70 s longer answer on named two-paper questions is acceptable for the product is a product decision. It is not a reason to start another optimization cycle.

## Decision (project lead, 2026-11-25)

B1 failed the frozen diagnostic and is **not** qualified. Frozen S2 stays the default and fallback. B1 is retained as an **experimental, opt-in paper-aware retrieval option**, for validation on unseen multi-paper questions during integration testing. No further optimization cycle is planned.

## Retrospective fresh-v4 estimate (NOT independent validation)

**Scoring consistency.** Two independent blind scorers re-scored the saved S2 answers to K05 and K07:
- the fresh-v4 scorer;
- the B1-diagnostic scorer.

They gave **identical point-level scores on all 10 points**:

| Point | Score |
|---|---|
| K05.1 | 0.5 |
| K05.2 | 1 |
| K05.3 | 0 |
| K05.4 | 0 |
| K05.5 | 0.5 |
| K07.1 | 0 |
| K07.2 | 0 |
| K07.3 | 0 |
| K07.4 | 1 |
| K07.5 | 0.5 |

Substituting B1's K05 and K07 scores is therefore consistent at the scoring level.

**Estimate:** S2 fresh-v4 37.0 − (2.0 + 1.5) + (3.5 + 4.0) = **41.0 / 50 = 82%**, against 74% for S2.

**Caveats:**
- **Retrospective:** B1 was designed after observing K05 and K07, so these are development cases.
- **Unrun questions:** the other 8 questions are assumed unchanged. Their B1 evidence packets are byte-identical to S2's offline, but they were not rerun, and generation varies between runs.
- **Not a qualification result:** this does not change the historical fresh-v4 result. S2 74% and S3 74%, and neither qualified.

## Summary

| | |
|---|---|
| Effectiveness | +4.5 answer points on the 3 named two-paper questions; all from the previously starved paper |
| Safety | no flags (blind scorer, programmatic audit of 43 items) |
| Cost | no extra searches; input tokens 1.02x; output tokens 1.5–2.1x on K05/K07, so 20–70 s longer generation |
| Lost point | K05.2: 1 → 0.5. HaloGuard's comparison with dedicated guards was omitted in a longer two-paper answer |
| Limitations | triggers only when titles are named, so 8 of 14 development cross-paper questions cannot benefit; 3-question live sample; development cases only; latency confounded with provider variance |

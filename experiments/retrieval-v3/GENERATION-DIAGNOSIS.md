# Generation completeness: read-only diagnosis and one proposal

**Date:** 2026-11-26.

**Method:** saved artifacts only, with 0 model calls. Script: `gen_diagnosis.py`; output: `gen-diagnosis.json`.

**Status:** frozen S2 and validated S2-R2 (`1d0e0ae`) are untouched. The unseen set is now development evidence.

**Data:**
- 5 blind-scored runs: fresh-v3 S2, fresh-v4 S2, fresh-v4 S3, unseen S2 and unseen S2-R2.
- 56.5 lost points in total.

**Tracing method:** each lost point is traced through evidence → draft → review → publication, using its anchor passages.

## 1. Where the points were lost

| Run | Lost | Evidence missing | Evidence present, never drafted | Drafted, removed by gate | Published but incomplete | Fact from another passage |
|---|---|---|---|---|---|---|
| fresh-v3 S2 | 13.0 | 8.5 | 0 | 0 | 4.5 | 0 |
| fresh-v4 S2 | 13.0 | 10.0 | 0 | 0 | 2.5 | 0.5 |
| fresh-v4 S3 | 13.0 | 8.0 | 0 | 0 | 4.5 | 0.5 |
| unseen S2 | 11.0 | 9.0 | 0 | 0 | 2.0 | 0 |
| **unseen S2-R2** | **6.5** | **6.0** | 0 | 0 | **0.5** | 0 |
| **Total** | **56.5** | **41.5 (73%)** | **0** | **0** | **14.0 (25%)** | 1.0 |

**Findings:**
- **(1) Missing evidence is the main cause.** Most lost points are still evidence the answer step never received. On the validated R2 run, **6.0 of 6.5** lost points are missing evidence.
- **(2) Drafting never ignored available evidence.** In no case did the drafter fail to cite a passage that held a required point. When the evidence was present, it was always used.
- **(3) Every generation-side loss is a published but incomplete finding.** The item cites the right passage, which contains the missing detail, but the claim omits a sub-component. Typical omissions:
  - a second value or comparator: J01.2, K03.4, U3.3 and U2.3;
  - a condition or qualifier: J07.2, K06.4 and K09.1;
  - a scope element: K06.1 and U6.4;
  - an evidence limit stated only in the uncited answer lead, not as a cited limitation: J05.5, J06.4 and K10.5.
- **(4) The review checks safety, not completeness.** In 7 of the 25 incomplete points, the reviewer still judged coverage "full". In the others, it named a gap but **cannot repair** it: its contract allows only keeping, reducing or rejecting a claim, never adding a fact that the claim's own quotes state.
- **(5) The publication gates did not remove useful findings.** Across the runs, 31 drafted items were withheld (4, 14, 10 and 3 per run), and none of them cited a passage behind a lost point. **No completeness was lost to the gates.**
- **(6) The drafting instructions favour brevity over completeness.**
  - The v2 brevity rules L1 and L2 tell the drafter: quote the "shortest exact span", aim for about 300 characters, and write at most two sentences per finding.
  - The citation rule says: "attach the quote ... or leave the fact out".
  - The safe response to a long quote is therefore to drop sub-facts. This matches finding 3.
- **(7) A component checklist alone did not help.** S3 added an explicit per-component checklist, and its incomplete-finding loss was *higher*: 4.5 points against S2's 2.5 on the same questions. Checking components does not fix incompleteness *within* a finding.

**Honest implication:** on the validated R2 configuration, generation-side completeness loss is small (0.5 of 36). **Reaching 85% depends mainly on evidence**, which is still 6.0 of 6.5 lost points. A generation fix should be expected to add about 1–2 points per 40 on S2-like answers, and less on R2.

## 2. Proposal: reviewer completion within the existing review call

**Problem:**
- Published findings omit sub-facts that their own cited passage states.
- The reviewer can see the omission, but is only allowed to shrink a claim, not complete it.

**Root cause:**
- The review contract (v2) is reduction-only.
- The drafting brevity rules push omissions into the draft.
- No step in the pipeline is allowed to add a supported detail.

**Change (generation only, no extra LLM calls):**
- **What the reviewer can return:** per claim, an optional `completed_text`, which is the claim plus facts from **the claim's own attached quotes, or added support from passages already cited**, that are relevant to the question.
- **Deterministic acceptance:** `completed_text` is accepted only if it passes the **existing** gates unchanged (exact quotes, P4 number recall against its own quotes, P5 attribution flags) **plus** one new check: it must contain every number of the original claim (a superset). This mirrors V1's reduction check.
- **Fallback:** otherwise the original claim is published.
- **Unchanged:** retrieval, drafting, budget, Deep Research and the gates.

**Expected benefit:**
- **Target:** the "published but incomplete" category, 14 of 56.5 lost points across development runs.
- **Estimate:** a realistic recovery of a third to a half: **+1–2 points per 40 on S2**, less on R2 (0.5 of that category remains there).

**Risks:**
- **Safety:** completions could introduce errors. Mitigation: own-quote entailment plus the existing number and attribution gates, the superset rule, and fallback to the original claim.
- **Latency and tokens:** longer review output, so more latency, at about 46 tokens/s.
- **No measurable gain on R2:** possible, because the category is already small there.

**Evaluation strategy:**
1. **Offline:**
   - unit and safety fixtures (an invented number is rejected; a completion with a fact outside its own quotes is held);
   - a replay through the frozen gates with synthetic completions.
   - Offline replay cannot show live benefit.
2. **Live:** on a **new reserved unseen set** (not fresh-v4, not unseen-r2), comparing R2 with R2 + completion.
   - Frozen criteria: at least +2 points (or at least +1 if the set is under 40 points), zero new safety flags, latency within limits.
   - About 32 calls, cap 40, after your approval.

## Alternatives considered and rejected

- **Relaxing the drafting brevity rules:**
  - it is the simplest change, but it lengthens every answer, so higher latency and tokens across the board;
  - it re-opens the v2 token optimizations;
  - it doesn't target the specific omitted fact.
- **Per-component checklist (S3 C):** measured as no better, as finding 7 shows.
- **Routing evidence limits into cited limitations:** about 1.5 points, a subset of the same category. The reviewer completion can carry these through its limitation rebuild.

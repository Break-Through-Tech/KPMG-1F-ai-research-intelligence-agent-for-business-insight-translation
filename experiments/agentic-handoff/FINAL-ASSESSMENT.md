# automated reviewer F01–F10 final assessment

- **Run:** `data/processed/automated reviewer-paired-v1-full`, all 10 pairs complete after resume.
- **Setup:** `gpt-6.1-sol`, effort low, quote grounding and the interpretation policy in both arms.
- **Scope:** automated reviewer only; never compared with Gemini. These are 10 development questions, so nothing here is a general reliability claim.
- **Review:** source review is machine-assisted, not human sign-off.

## Automated (code)

- **Calls:** 64 of the 90-call cap. 59 succeeded; the 5 failures were 300 s CLI timeouts in the first pass, and all five questions were recovered by resume. Failed attempt folders are preserved as `F0x.attempt-1`.
- **Tokens:** 1,159,519 input and 23,398 output.
- **Latency:** median successful call 9.3 s. Arm wall time: median 41.5 s, p90 228 s.
- **Errors:** after resume, no execution errors, no schema failures and no verifier rejections.
- **Report screens.** Automated required-point screen per arm: 14 of 20 arms flagged every point. These screens are *not* the score: they mis-scored F09 and F05.3 (see below).

## Source-reviewed score per arm (both arms identical)

| Q | Points | Result | Notes |
|---|---|---|---|
| F01 | 2/2 | Complete | Table 1 rows |
| F02 | 2/2 | Complete | Table 1 rows |
| F03 | 2/2 | Complete | Table 1 rows |
| F04 | 1 + ½ of 2 | Partial | F04.2: relevance filtering yes, **image captions omitted**. Captions were in the packet, so this is a **draft omission** |
| F05 | 3/3 | Complete | F05.3 stated via the equivalent passages c0000 and c0008 (anchor c0032 not cited) |
| F06 | 3/3 | Complete | Current: 1 interpretation withheld. Handoff: 1 generalization published as a finding |
| F07 | 2/2 | Complete | |
| F08 | 1 + ½ of 2 | Partial | F08.1's "LLM too uniform" passage (c0054) was never retrieved, so that half is **retrieval-limited** |
| F09 | 1/2 | Partial | F09.1, the null result, was **held by the existing number check** (`negation_mismatch`) although the verifier judged it supported and it matches c0000 and c0013. A **false rejection**. The null result appears only inside a limitation |
| F10 | 2/2 | Complete | |

**Totals per arm:**

- Questions: 7 complete, 3 partial, 0 abstentions.
- Required points: 19 of 22 fully published, 2 half-published, 1 missing.
- Unsupported published findings: 0.
- Misleading claims: 1 (F06 handoff; mild, not factually false).

Extra accurate content was also published. For example, F09 limitations noted that the ANOVA's F(3,26) does not match 60 participants.

## Interpretation policy

- **Interpretations drafted:** 2 in 20 arms. automated reviewer rarely drafts them.
- **Withheld:** 2, both in the current arm.
  - F06: an extrapolated rule built from an error analysis. Withholding it was appropriate.
  - F08: a faithful synthesis. This is the policy's cost; it was not a required point.
- **Bypass:** 1 (F06 handoff). The same generalization was labelled as a finding.
- **Explanatory-wording flag:** high recall, low precision. Most flagged findings were faithful author claims (because / cause / lead to).
- **Net:** small benefit, small cost. The real F01-type risk seen under Gemini did not occur with automated reviewer.

## Current vs handoff (10 pairs)

- **Completeness:** 10 ties. Required points are identical, and unsupported claims are 0 vs 0.
- **Policy adherence:** current is better in F06.
- **Caveats:** handoff added a correct limitation in F08, and the F09 limitations differ slightly in wording. Neither changes the score.
- **Calls:** equal (3 per question, or 5 with a second round).
- **Verdict:** no measurable benefit from handoff.

## Remaining failure modes (by earliest stage)

1. **Retrieval:** F08.1.
2. **Draft omission:** F04.2 (captions).
3. **Deterministic number check false rejection:** F09.1, a safeguard defect in `numeric_checks.py` (frozen).
4. **Writer generalization labelled as a finding:** F06 handoff.
5. **Operational:** 5 of 64 calls timed out on the CLI. All were recovered by resume; the computer must stay awake during a run.

## Recommendation

- **Default for KPMG: keep Baseline/B2.**
  - This evaluation did not run Baseline/B2 under the same model and questions, so there is no head-to-head evidence that Multi-Agent answers better.
  - Multi-Agent costs about 3–5 calls and 40–230 s per question.
- **Offer current Multi-Agent (automated reviewer + quote grounding + interpretation policy) as an opt-in "verified research" mode,** with human review. It published 0 unsupported findings across 20 runs and abstained on nothing.
- **Drop handoff.**
- **Before making Multi-Agent the default:**
  1. Fix the number-check negation false rejection under a new label, with tests.
  2. Run one head-to-head of Baseline/B2 vs current Multi-Agent on F01–F10 with the same automated reviewer model.

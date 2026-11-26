# automated reviewer full run (F01–F10): results

Run: `data/processed/automated reviewer-paired-v1-full`.

- **Configuration:** `gpt-6.1-sol`, effort low, 300 s timeout per call, ChatGPT login. Quote grounding and the interpretation policy were on in both arms.
- **Separation:** automated reviewer results only; never compared with the Gemini runs.
- **Scope:** development evidence on 10 frozen questions. It is not a general reliability claim.
- **Review:** source review is machine-assisted, not human sign-off.

## Execution (automated)

- 35 of 90 calls used. 30 succeeded; 5 failed, all on the 300 s CLI timeout, and none on content, schema or quota.
  - Four of the timeouts were on the planner call, which normally takes about 6 s: F02 handoff, F04 handoff, F07 current and F09 current. In F09 the process hung for about 6 hours.
  - The fifth was on the F05 handoff draft.
- Under the runner's design, each failed pair stopped its partner arm. Completed arms: 11 of 20. Execution errors: 5. Unrun: 4 (F02 current, F04 current, F07 handoff, F09 handoff).
- Tokens: 565,202 input and 10,596 output.
- Successful calls took about 6–20 s. Arm wall time over completed arms: median 53 s, p90 289 s.

## Per arm (source-reviewed against the cited passages)

| Q | Current | Handoff | Notes |
|---|---|---|---|
| F01 | Complete 2/2 | Complete 2/2 | Exact Table 1 rows |
| F02 | Unrun | Execution error | Planner timeout |
| F03 | Complete 2/2 | Complete 2/2 | Exact Table 1 rows |
| F04 | Unrun | Execution error | Planner timeout |
| F05 | Complete 3/3 (round 2) | Execution error | F05.3 stated via the equivalent passage c0000, not anchor c0032 |
| F06 | Complete 3/3 (label `partial`: 1 interpretation withheld) | Complete 3/3 | Handoff published one generalization as a finding (below) |
| F07 | Execution error | Unrun | Planner timeout |
| F08 | Partial: F08.2 yes, F08.1 half | Partial, same | F08.1's "LLM behaviour too uniform" passage (c0054) was never retrieved, so that half is **retrieval-limited** |
| F09 | Execution error | Unrun | Planner timeout (hung) |
| F10 | Complete 2/2 | Complete 2/2 | c0023 |

## Findings

- **Unsupported published findings: 0.** Every reviewed number and attribution matches its passage. Examples: F05's 10 advisors, 20 investors and 5,000 / 4,000 / 500 / 500 templates; Bloom 7B trained on 14M Reuters and DPA articles plus 25% of 12M SEC filings.
- **Interpretations withheld (2), both in the current arm:**
  - **F06:** turns the paper's LLM error analysis (c0013) into a rule for classifying responses. It is extrapolated, so withholding is appropriate.
  - **F08:** says the challenges mean distinct identities do not establish realistic variability, so validation is needed. It is a faithful synthesis of c0034 and c0062, so this is a valid explanation withheld (a cost). Neither withheld claim was a required point.
- **Interpretation disguised as a finding: 1, in F06 handoff.** "An acknowledgment alone is not decisive when the response also contains a question" is the same generalization the current arm labelled as an interpretation. Its second sentence faithfully reports c0013. The claim is mild and not factually false, but it shows the policy can be bypassed when the writer labels a generalization as a finding.
- **Explanatory-wording flags.** Most flagged findings are faithful author claims: F10's "cause"/"lead to", F08's "because", F05's "attributes". One is the disguised claim above. The flag has high recall and low precision, so it is useful for review but not for automatic holding.
- **Minor framing (not counted as unsupported).**
  - F08: "computational cost compounds these challenges" is tangential to the question.
  - F06 current: "A question can therefore signal acceptance" is a light inference consistent with c0006.
- **No false abstentions or schema problems.** One F05 round was replaced by a verified round 2. No verifier output was rejected.

## Current vs handoff (completed pairs: F01, F03, F06, F08, F10)

- **Completeness:** 5 ties.
- **Unsupported claims:** 0 vs 0.
- **Policy adherence:** current is better in F06, where handoff published the generalization as a finding.
- **Limitations:** handoff is better in F08, where it added a correct cited limitation about missing quantification.
- **Net:** no meaningful difference.

## Recommendation

automated reviewer with quote grounding and the interpretation policy produced complete or retrieval-limited answers with no unsupported findings on every completed question. The open problems are:

1. **Operational.** 14% of calls hit CLI timeouts, including hangs on trivial planner calls. Resume the 5 failed pairs with the same command. That needs about 25 more calls, within the remaining cap of 55, and requires approval.
2. **Retrieval.** F08.1 shows the evidence ceiling. Policy changes cannot fix it.
3. **Relabelling.** 1 of about 25 published findings carried a writer generalization.

For the KPMG app: adopt the Codex provider with quote grounding and the interpretation policy behind an opt-in flag. Show withheld interpretations as clearly marked unverified commentary. Keep the single-version (current) orchestrator, because handoff added no benefit.

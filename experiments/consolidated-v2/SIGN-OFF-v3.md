# fresh-v3: human sign-off

| Date | Who | Decision |
|---|---|---|
| 2026-11-25 | Project lead (human) | **Accepted** the reviewed and corrected fresh-v3 answer key (38 points; `fresh-v3/seal.json` sha256 407cc13f642936d2…). **Approved** running all four arms (B0, S1, S2, D2) under the frozen acceptance criteria and the persistent 90-call cap. |

- **Frozen:** engines, questions, scoring rules and acceptance thresholds.
- **Execution:** the project lead runs the four arms in sequence.
- **After completion:** mechanical audits and the independent blind-scoring packet (`fresh3_scoring.py audit` and `fresh3_scoring.py blind`), with 0 model calls.
- **Out of scope:** no further engine changes, experiments or deployment. This is the final major evaluation before the delivery decision.
- **Why this is a separate file:** the sealed set, including `fresh-v3/KEY-REVIEW-RECORD.md`, must stay byte-identical.

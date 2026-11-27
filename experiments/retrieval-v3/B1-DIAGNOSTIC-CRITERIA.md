# B1 live diagnostic: frozen acceptance criteria

Recorded 2026-11-25, before execution, as approved by the project lead.

## Setup

- **Questions:** J03, K05 and K07.
- **Arm:** S2 with B1 on.
- **Comparison:** the saved frozen-S2 answers for the same questions, scored blind A/B against the same sealed keys.
- **Development cases:** these three questions are where B1's offline gain was found. **The result is not independent evidence of generalization.**

## B1 passes only if all four hold

1. **Completeness:** at least **+2 answer points** in total across the three questions.
2. **Safety:** **zero new** citation-grounding, numerical, misleading or unsupported claims relative to saved S2.
3. **No losses:** **no point** that saved S2 scored is scored lower for B1. A point counts as lost if it falls from 1 to 0.5 or 0, or from 0.5 to 0.
4. **Latency and tokens:** median total latency at most **1.10×** saved S2 on the same questions, and actual input tokens at most **1.10×** saved S2 on the same questions.

## Budget

- **Calls:** 6 expected, **hard cap 8**.
- **Resumes:** one resume per question.

## Outcome

- **Pass:** proceed to the planned unseen named cross-paper questions during integration testing.
- **Fail:** retain frozen S2, with no further optimization.
- **Default either way:** frozen S2 remains the default and fallback.

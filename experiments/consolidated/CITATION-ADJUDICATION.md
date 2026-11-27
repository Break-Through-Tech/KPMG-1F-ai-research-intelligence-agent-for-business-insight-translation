# fresh-v2 evaluation: consistent citation-grounding adjudication (2026-11-25)

- **Instruction:** applied at the user's direction.
- **Record:** this file is a separate addendum. The independent blind score sheet (`blind-score-sheet.json`) and `FINAL-EVALUATION.md` are **not modified**.

**Rule:** a factually correct statement that is not supported by the evidence attached to that specific published item is a citation-grounding failure. It counts against the safety gate and is distinct from a fabricated or incorrect claim.

| Item | Text | Its only attached quote (c0009) | Status |
|---|---|---|---|
| **Deep H01 L1** (recorded by Codex) | "The evaluation used three-turn conversations and does not establish robustness over longer conversations." | "We acknowledge that longer conversations (5–7 turns) were not evaluated…" | Failure (Codex) |
| **Standard H01 L1** | "The evaluation used three-turn conversations; performance over longer conversations remains untested here." | the same sentence | **Confirmed additional failure** |
| **Deep H07 L2** | "The multi-turn results are bounded to three-turn evaluation; safety over longer interactions remains unestablished by these results." | the same sentence | **Confirmed additional failure** |

In each case "three-turn" is true (c0009 elsewhere: "5 multi-turn conversation samples (3 turns each)"), but it is not stated in the item's own quote.

**Totals after consistent application:**

| | Standard | Deep |
|---|---|---|
| Citation-grounding failures | **1** | **2** |
| Fabricated or misleading claims | 0 | 0 |
| Safety gate | **Fail** | **Fail** |

**Effect on the closed verdict:**

- Deep already failed the frozen rule.
- Standard was not a qualification arm in that evaluation.
- The production default (Original Baseline) is unchanged.

**Engineering follow-up:** consolidated-v2 checks spelled-out counts in limitations and findings (V5). All three items are dropped in replay (`test_v2.V5CitationGrounding`).

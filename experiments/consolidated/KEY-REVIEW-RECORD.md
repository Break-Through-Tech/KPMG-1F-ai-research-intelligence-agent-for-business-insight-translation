# fresh-v2 answer key: review record

| Step | Date | Who | Outcome |
|---|---|---|---|
| Draft | 2026-11-24 | Claude (AI-assisted) | 36 points, sealed |
| Pre-review source check | 2026-11-24 | Claude | H03.4 re-anchored; H08.2 qualifier "mixed"; H05.4 two-component. Resealed |
| Focused independent review (one round) | 2026-11-24 | ChatGPT (**AI-assisted, not human**) | 3 issues and 1 rule, all applied (below). Resealed once |
| Final approval | 2026-11-24 | Human (project lead) | **Approved** the final resealed key (seal.json sha256 b2e19d6cf6c765a1…) and the 50-call live validation. Configurations and scoring rules frozen; the user executes Standard then Deep |

**Corrections from the focused review:**

- **H01.1:** the 50,000+ benchmark conversations are now distinguished from the 2,345 evaluation samples (anchor c0000 + c0009). Conflating them scores 0.5 at most.
- **H06.1:** the second alternative is c0008 + c0007, so instruction tuning is supported in both alternatives.
- **H06.2:** the anchor now has the nine entity-type rows plus the total row, so it establishes both the nine types and the 6,985 entities.
- **Rule:** an alternative anchor earns full credit only when it supports every required component. `build_set.py` checks every group against all must-contain strings, and `rules.json` states the rule.
- **Related fix** under the same rule: H06.4's two alternatives (c0015, c0017) became one group, since each covered only part of the point.

**Unchanged:** the questions (`questions.json` hash identical), the architecture and engine code, the acceptance thresholds and decision rule, and the 50-call cap.

No further review rounds. Remaining borderline cases are in `AMBIGUITIES.md` for adjudication after scoring.

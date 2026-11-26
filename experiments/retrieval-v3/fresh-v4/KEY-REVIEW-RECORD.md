# fresh-v4 answer key: review record

| Step | Who | Outcome |
|---|---|---|
| Draft | Claude, from bundle passages only | 10 questions, 50 points, every anchor and fact machine-checked |
| Independent review (one round) | Fresh-context Claude reviewer (AI, not human); saw only the key, rules and paper passages | CHANGES: 6 errors, 14 missing anchors, 2 unfair, 7 ambiguities (KEY-REVIEW-REPORT.md) |
| Corrections | Claude | Applied in build_set.py and re-verified by the build |
| Seal | Claude | seal.json (seal_s3 --write-set) |
| Human sign-off | Project lead | pending |

## Corrections applied

- **Errors:**
  - K04.3: the LoRA parameter ratio direction.
  - K09.3: dropped the c0020 alternative and added c0000.
  - K06.3: the 2.6 GB figure is now optional.
  - K03.3: the validation figures are now optional.
  - K10.2: added the stress-workload condition.
  - K10.5: dropped the backbone wording and added the c0005 alternative.
- **Missing anchors added:** K01.2, K03.4, K04.2, K05.2 and K08.2. Alternatives that did not contain every required fact were not added; the build check enforces this.
- **Fairness:**
  - K08.5: the simple configurations are required; record-owned dispatch is optional.
  - K02.4: full credit needs the qualitative findings plus at least one figure.
- **Ambiguity rules now written into the expected answers:**
  - K01.3: credit only when tied to the identical-schema comparison.
  - K05.4: any correctly labelled overhead figure scores.
  - K04.1: any correctly attributed parameter-share figure is accepted.
  - K04.3: the Table 1 rows are context only.
- **Not changed:** the remaining reviewer notes (K03.5, K01.4, K08.3/K08.4, K10.1 and K06.4) were reviewed. The existing anchors already support those points, so the additions were not needed and the scorer applies the stated rules.
- **Confirmed by the reviewer:** all four evidence-limit points and all five misleading-claim probe rulings are correct.

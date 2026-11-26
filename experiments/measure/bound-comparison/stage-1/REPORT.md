# Stage 1 — Automatic source links for saved answers

**Result: proof for CU-DPO, limited coverage.** The offline linker recovered the exact two source spans in both archived CU-DPO answers without a claim-by-claim source assignment. Broader saved-answer coverage is 2 of 10 claims containing digits. Application integration remains on hold.

## Saved-answer replay

The frozen archive contains 11 Baseline answer records, 17 retained claims, and 88 evidence rows. All 88 saved rows matched their pinned demo-100 records. Ten claims across six answers contain digits. This is a screening count and includes scalar and compound claims outside the paired-comparison format.

| Outcome | Result |
| --- | --- |
| Linked | Both CU-DPO claims linked 35–46% and 68–78% to their exact offsets in `2602.00931v2_c0000`. |
| Referred for review | Eight other digit-containing claims had no comparison registered for their citations. |
| Unlinked nonnumeric claims | Seven claims fell outside the numeric screen. |

The archive is evidence of two valid phrasings of one finding. No live Multi-Agent answers were used. The prior study matched these same two claims with manually supplied bindings. This run uses the saved claim text, cited quotes and delivered evidence records as input.

## Binding and regression checks

The linker matches a complete comparison frame using the registered subject, metric, setting, population and qualifiers. It checks the before and after operands in order. The cited source must cover the exact span and its scope, or the complete audited table row. The existing typed verifier then checks values, units, roles, and source identity. Ambiguous and incomplete cases are referred without source links.

| Additional cohort | Outcome |
| --- | --- |
| 20 previous range, boundary, and transfer inputs | All were referred. The set included 14 unsupported mutations and six supported cases. The prior controlled fixture inputs lacked the full explicit scope required by this linker's frames or expressed the comparison in a different form. |
| Seven new labeled-table controls | All three valid claims linked to exact cells. Three invalid comparisons were rejected for wrong endpoints, unit, or sign. One invalid comparison was referred for a different benchmark. |

All 10 new regression tests passed. Cases also cover missing or duplicate evidence, a changed paper version, altered quotes, detached scope, extra claims, wrong direction, and decimal precision. The previous verifier's 12 tests passed. Draft transfer cases retain `reviewed=false`. These measurements do not estimate live answer accuracy.

## What Stage 1 established

Automatic linkage works when the archived claim expresses the complete comparison and the source has a trusted finding record. The linker uses five records curated during the previous experiment. The archive result isolates both gaps for wider use. The other eight saved numerical claims lack such records, and even supported comparisons can be referred when prose omits scope or uses a different form.

Before wiring a live shadow check, test a structured claim record carrying the metric, setting, operands and citations alongside ordinary prose. Use a fresh, source-checked set across multiple papers so linkage coverage and mistaken holds can be measured separately from the comparator.

## Reproduce

Use Python 3.11+ in the desktop worktree with the pinned demo-100 parent bundle and prior measurement artifacts. Only the standard library is required for this stage.

```powershell
python -I -B experiments/measure/bound-comparison/stage-1/test_stage1.py
python -I -B experiments/measure/bound-comparison/stage-1/stage1_replay.py
python -I -B experiments/measure/bound-comparison/stage-1/stage1_replay.py --output new-replay.json
```

[Raw replay](results.json) includes each archived numeric claim, outcome, reason and any accepted operand links. All changes are in this directory. The offline replay used zero provider calls.

# Structured numerical range verification experiment

## Decision

**Structured comparison is viable with trustworthy role and scope bindings. The free-text adapter is too permissive for runtime use.** It fixed all three frozen CU-DPO mutations without adding a false rejection in the established 33-case set. Separate boundary probes show it can still incorrectly attach valid ranges to the wrong metric or evaluation setting when the wording falls outside its declared scope.

### Recommendations

| Decision | Result | Basis |
|---|---|---|
| A. Integrate behind a runtime feature flag | **NO-GO** | Two unsupported free-text boundary probes were accepted. An opt-in answer-authorizing path would still have these errors. Continue offline with typed inputs and exact source bindings. |
| B. Expand toward a shared evidence-first layer | **GO for an offline, table-first pilot** | Two independent audited tables supported exact source-cell binding and deterministic role comparisons. Require compatible scope and refuse ambiguity. Validate human-reviewed extraction precision and recall on more papers before extending to text. |
| C. Keep the current checker pending further evidence | **GO as the current fallback** | The adapter has no replacement scalar path and leaves its established scalar false hold unchanged. Keeping the checker does not clear the pinned live experiment or make its range behavior reliable. |

## Frozen baseline and source

The baseline was replayed on all 33 established cases from [verification.json](../run-02/verification.json). The live checker file digest matched the recorded digest and all 43 pre-existing checker outputs, including the 10 earlier draft cases, matched field-for-field. Established engineering expectations are not human-adjudicated gold labels.

The four frozen cases cite `2602.00931v2_c0000`, the abstract of **Continuous-Utility Direct Preference Optimization**. The exact unchanged source span is in [results-final.json](results-final.json) under `source_findings.cu.citations`, including character offsets, paper version, and source URL. It describes mathematical reasoning benchmarks, the strategy-selection metric, pre/post ranges **35–46% → 68–78%**, and seven models. It also includes a separate downstream numerical result. The adapter uses the abstract scope for these cases. It does not merge the abstract's seven-model count with Table 2's eight model pairs or treat Table 4a's downstream reasoning accuracy as the same measure.

| Frozen claim | Existing checker | Adapter |
|---|---|---|
| Correct, 35–46% → 68–78% | Accept | **Accept** |
| Roles reversed, 68–78% → 35–46% | Accept | **Reject** |
| Endpoints regrouped, 35–78% → 46–68% | Accept | **Reject** |
| Collapsed to points, 35% → 78% | Accept | **Reject** |

## What is structured

A source finding carries an exact versioned paper ID, source URL, cited chunk or cell locators, source digest and source text, association method, metric, subject, setting, population, qualifier, before/after roles, and explicit ambiguity. Each quantity is an exact decimal point or closed interval with a declared unit and scale. The comparator consumes typed records. It checks both ordered endpoints and role identity. Percentage levels can be converted to equivalent proportions. Percentage-point deltas remain a different unit. A point cannot stand in for a reported range.

The CU-DPO adapter used one fixed original span. Its scope was declared from the source. A narrow token grammar parsed its literal from/to roles. Table adapters took explicit, audited columns and named row sets, verified their source/chunk IDs, then derived interval extrema from the matching cells. These are min/max calculations over explicitly scoped rows, with no assumption that the source authored the ranges as prose.

Two independent sources were exercised:

- **HAMMER:** `2509.25240v1#S5.T1`, `Qwen3-1.7B-DAPO`, `pass@1`, AIME 2024 and AIME 2025, `k=100`. The selected B/H cells give **25.3–36.3 → 31.0–39.3** on the table's reported score scale.
- **ACDC:** `2604.00324v1#A1.T1`, IOI and Docstring only. The Random/ACDC AUC columns give **0.50–0.50 → 0.92–0.95**. The comparison is between methods, with before/after fields serving as role slots for baseline and treatment. It does not imply a temporal intervention.

Both sources passed a sentence-order stress test using two **derived** projections of each source, one with “Before” first and one with “After” first. These labeled sentences were generated deterministically from the table records. The raw output retains the original cell references and identifies the projections as derived text. It also tests real citation order reversal, closed brackets, alternate population wording, missing cited rows, missing qualifiers, wrong metrics, and percent versus percentage-point units. No independent alternate *original prose* source with the same comparison grammar was tested.

## Results

Accept, reject, and refer for review are reported separately. The existing checker maps `grounded` to accept, `contradicted` to reject, and `uncertain` to review. This measures deterministic behavior with frozen inputs, without a model verifier.

| Cohort | Current wrong accepts | Adapter wrong accepts | Current wrong rejects | Adapter wrong rejects | Adapter referrals |
|---|---:|---:|---:|---:|---:|
| Established engineering cases, 33 | 3/14 | **0/14** | 1/19 | 1/19 | 0 |
| Earlier unreviewed drafts, 10 | 3/8 | 1/8 | 0/2 | 0/2 | 1 |
| New table-grounded drafts, 17 | 0/6 | 0/6 | 5/5 | 0/5 | 7 |

For the 17 new cases, six have intentionally unadjudicated semantic outcomes because their wording or evidence is ambiguous. The adapter accepted four supported claims, rejected all six with a draft unsupported label, and referred the remaining supported claim for review because its form was outside the grammar. Those seven referrals are **not** counted as wrong rejections. If a deployment withholds all referrals, one of five draft supported claims would still be withheld. The baseline rejected all five in this cohort. Some new claim forms introduce syntax, digits or unit scales that the baseline's free-text checker interprets differently. These cases were authored for this experiment and cannot estimate comparative accuracy in production.

All 29 established non-range cases retained their existing checker decisions. Among the 18 supported non-range cases, both approaches retained **17/18**, including grounded scalar and unit-conversion controls. The original age-paraphrase false hold persisted. The existing draft scalar percent-versus-points case still rejected, and the independent AUC interval evaluation additionally rejected percent levels phrased as percentage-point deltas. No runtime change was made.

### Boundary probes held apart from the designed cases

The separate [boundary results](boundary-results.json) contain four independently stated follow-on probes, each marked `reviewed=false`:

- **Unsupported, accepted by both:** added “French elementary tasks,” a setting absent from the scope dictionary.
- **Unsupported, accepted by both:** the comparison is made about preference accuracy in one sentence, while the supported metric is named in another. The adapter finds the right numbers and metric phrase but associates them across sentences.
- **Unsupported, rejected by both:** moved the benchmark claim to explicitly recognized clinical deployment.
- **Supported, referred by the adapter:** verbal before/after ranges used two independent “ranged from X to Y” clauses. The existing checker accepted this form.

These are coverage boundaries rather than defects in typed endpoint comparison. Source binding and claim interpretation can still be wrong even if the comparison itself is correct. Extending the phrase dictionaries would address individual examples and would not establish general extraction. The useful design direction is validated, scoped finding records with provenance, produced deterministically from suitable tables or reviewed as ambiguous. Use typed claim input or a verified claim-to-finding binding before applying the comparator. Broader prose parsing, significance tests, open intervals, derived percentage changes, and source conflicts require separate handling.

## Reproduce

From the authoritative worktree, use the installed Python 3.14 runtime. The commands create fresh raw JSON and refuse to overwrite existing output files.

```powershell
$py = 'C:/Users/ngkho/AppData/Local/Programs/Python/Python314/python.exe'
& $py -I -B experiments/measure/structured-ranges/run.py reproduction.json
& $py -I -B experiments/measure/structured-ranges/test_adapter.py reproduction-boundaries.json
```

The run evaluated **60 fixed cases**, plus four separate boundary probes and six passing model-free unit tests. It also hashed frozen input files and checked the pinned parent digest. [Final raw cases, source records, baselines and hashes](results-final.json) · [Boundary raw records](boundary-results.json). The earlier `results.json` is a retained preliminary run before the extra missing-qualifier case.

Only files in this experiment directory were written. There were zero real provider calls and no access to the authorization ledger. The checker, runtime, source index, and pinned A/B inputs were left intact. No packages were installed.


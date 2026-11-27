# Final Business Insight Translation validation

The candidate is downstream v1.2 at 870ba4991a2ac9f5b58d6627e2da3141a3e6af2b.
This package prepares one new business generation run. It uses the existing
translation entry point with the pinned implementation and provider adapter.
The original frozen package and historical AI judgments remain the permanent
record of the baseline/v1.1 evaluation.

The known-case retest uses the 12 original packets byte for byte. It compares
fresh v1.2 output against the exact saved baseline and v1.1 outputs. Individual
known-case results identify availability transitions, including the five former
v1.1 abstentions, and show common-available paired deltas. Report the original
reference-aligned and generation-held-out groups within the known retest.
Report the five fresh cases separately. They use five papers outside the original
business evaluation, with new workflows and questions authored after the v1.2
implementation pin. The research items are manually accepted and checked against
versioned local primary-source PDFs. These five cases test transfer beyond the
original business evaluation, with limited sample size and one case author.

| Group | Inputs | New v1.2 calls | Saved results |
|---|---:|---:|---:|
| Known reference-aligned | 5 | 5 | 10 |
| Known former held-out | 7, including U7 empty control | 6 | 14 |
| Fresh questions | 5 | 5 | 0 |
| Total | 17 | 16 | 24 |

The hard cap is 16 attempted translation requests, including failed or ambiguous
dispatches. Every attempt is reserved in the ledger before dispatch. U7 exercises
the translation interface and must make zero generator calls. A provider error
stops the remaining requests. Invalid business responses are recorded as failed
cases. SDK attempts are one. The campaign directory locks this one execution.
Use the stop rule even if the run finishes below the cap.

The same dedicated Gemini project, model, temperature, JSON mode, default
thinking configuration and request pacing are pinned in provider.json. Load the
existing encrypted business credential into the live process only, after separate
approval covers the frozen manifest and the new public excerpts and hypothetical
contexts. The existing data-use and model-access receipts record the earlier
authorization and verification. The preflight checks local integrity and settings.
It performs zero requests and spends no quota. The live run starts only through
an explicit --execute command with the user-approved manifest digest.

```powershell
python -B business-evaluation/v1.2-validation/runner.py
# Only after separate approval naming the manifest digest:
. ./business-evaluation/runs/local/load-local.ps1
python -B business-evaluation/v1.2-validation/runner.py --execute --approved-manifest-sha256 <approved-digest>
```

The live executor writes artifacts to the new ignored runs/final-v1.2-live
directory. Send only anonymous-review.zip to two AI reviewers in isolated assistant
contexts. Each archive contains 17 evidence packets and 41 outcomes with freshly
randomized aliases and output letters. A singleton has no historical comparator.
Keep the mapping, provider configuration, raw responses, earlier review, and
the other assessor's ratings out of each reviewer context. Prefer reviewers
with no prior exposure and record reviewer provenance and exposure declarations.
Ask both reviewers to record their evidence citations and notes. These are
workspace assistant assessments. There are no additional paid critic API calls.

```powershell
python -B business-evaluation/v1.2-validation/score.py collect --first <AI-sheet-1.csv> --second <AI-sheet-2.csv>
# Fill all required fields in the blinded adjudication sheet against the evidence.
python -B business-evaluation/v1.2-validation/score.py finalize
```

The observable scores and thresholds use the original rubric. The fresh set uses
its availability and material-defect rate cutoffs with a denominator of five,
which requires five available answers and zero material cases per defect.
The fresh usefulness, fidelity, and limitations means each need 4/5, and no
critical unsupported claims may be detected. There is no paired gain on fresh
cases. The known paired improvement gate compares v1.2 with baseline using the
original threshold and common available pairs. Changes versus v1.1 are descriptive.
Report availability losses beside all paired numbers. New blind AI scores provide
a common comparison for the current run. The prior scores and adjudication stay
untouched. The empty control is tracked separately. Human acceptance stays
unverified. If gates are missed, report the remaining limitations and close
this validation cycle.

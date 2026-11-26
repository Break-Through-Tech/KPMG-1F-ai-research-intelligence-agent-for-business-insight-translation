# Experimental Gemini item recovery

This branch changes the standalone evaluation adapter only. It does not change the provider request, production adapter, engine, retrieval, prompts, benchmark, scoring, or publication gates. The same adapter handles S2 and optimized R2. The previous campaign is permanently aborted and cannot be used with this experiment.

## Contract audit

| Boundary | Recovery and safeguards |
| --- | --- |
| Draft claim or limitation fails its item schema | Drop the entire item. Do not rewrite it, salvage a subgroup of its citations, or manufacture support. Strictly revalidate the remaining response. An empty findings list cannot count as a completed answer. |
| Review limitation fails its item schema | Drop the entire limitation, including the observed empty-support form. Preserve independently valid decisions. |
| Review decision fails its item schema | Drop it only when all decision indices have valid, unique identities. The engine will withhold that claim because it has no valid decision. If a malformed decision has an invalid or ambiguous identity, reject the whole reply. Already shape-valid duplicates still go through the native ambiguity handling. |
| Top-level envelope, missing fields, wrong array type, aggregate bounds, malformed or ambiguous JSON | Reject the whole reply. |
| Provider error, non-STOP completion, missing or over-budget usage | Preserve the existing failure and retry handling. There is no item recovery from a truncated or unreceipted response. |
| Shape-valid item with an inexact quote, unsupported number, or missing entailment | Keep the existing synthesis parser, review, and publication gates. Passing schema does not establish support. |

Audit rows store dispatch ID, stage, field, and item position. They contain no model text or evidence. A recovered review cannot claim full coverage. A draft omission also propagates a neutral coverage notice through the review. The notice and result metadata disclose the omission and leave it for human review. Completed answers still require supported published findings.

The saved U1 review and U2 draft replay unchanged. The rejected U2 review body was never saved. The U2 regression uses the actual draft and evidence with a simulated review carrying the same logged empty-support defect.

Run offline using the evaluation Python environment.

```powershell
# Optional. Point it at a private copy or the read-only aborted campaign for the replay tests.
$env:PROOFLINE_REPLAY_STATE = '<private campaign directory>'
python -B experiments/retrieval-v3/gemini-r2/test_recovery.py
python -B experiments/retrieval-v3/gemini-r2/test_budget.py
```

After separate authorization, use U2 and an unused control such as U7 as a two-question paired compatibility check. Both arms use the same recovery. Use a fresh ledger and pre-register eight expected calls, a ten-call ceiling, the unchanged per-response evidence rules, and checks for completion, valid citations, and transparent coverage. This check does not produce a replacement 36-point result. The current full-campaign entry point is not a two-question launcher.

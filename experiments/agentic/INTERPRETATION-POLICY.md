# Withholding interpretations (opt-in, offline-tested)

Decision (2026-11-23): this mode never publishes interpretation claims as verified. Findings are unchanged.

## Why

The writer labels each claim `finding` or `interpretation`. By the synthesis contract, an interpretation's quotes are premises, not proof, so the model verifier is its only gate.

That gate passed the F01 misattributed interpretation in every live run:

- original wire (v1)
- simplified-v2, where it was hidden by the false abstention
- Stage A v3, in both arms
- Stage A v4 with scope review: Gemini labelled both scopes "MultiFinRAG framework performance" and returned `same`

A model judgment has not been reliable here. The policy is deterministic, so no model label can override it.

## Change

`experiments/agentic/interpretation_policy.py`, enabled with `interpretation_policy.enable(engine)`. It works with both orchestrators and makes no model call.

- After the existing verifier decides, each **accepted** interpretation becomes `held` with the reason "interpretation withheld by policy: explanations are not independently verifiable".
- The verifier's own verdict stays on record. Held claims remain in `held_claims`, so a reviewer can still read them as unverified commentary. Nothing is relabelled as a finding.
- Coverage:
  - If no accepted claim remains, coverage is `none`.
  - Otherwise a withheld interpretation turns `full` into `partial`, with the note "N interpretation(s) withheld by policy; findings are unaffected". The label stays honest for "why" questions. Whether the factual points are complete is reported separately by the required-point check.
- In the handoff arm, a withheld interpretation is not carried into later rounds as a verified claim.
- Unchanged: quote grounding, exact-quote validation, the number checks, the verifier, the gate, the envelope, the comparator and the seal. `src`, `agents.py`, `handoff.py` and `contracts.py` are byte-identical to the automated reviewer worktree.
- Scope review stays available but is not part of this mode.

## Offline results: every live draft replayed through its real orchestrator

| Live draft | Without policy | With policy |
|---|---|---|
| v3 F01 current | 4 published (`full`) | 3 findings published; interpretation held (`partial`). F01.1 and F01.2 kept |
| v3 F01 handoff | 4 published (`full`) | Same as above |
| v4 F01 current (Gemini's real scope fields) | 4 published (`full`) | Same as above |
| v3 F03 current | 2 published (`full`) | 2 published (`full`), unchanged |
| v3 F03 handoff | 2 published (`full`) | 2 published (`full`), unchanged |

- Misleading claims published: from 3 (one per F01 draft) to 0.
- Findings lost: 0. New abstentions: 0.

Tests: `test_interpretation_policy.py` (11 cases) and `test_stage_a.PolicyStageA` (through the Gemini adapter with mocked HTTP). The cases cover:

- the misattribution is held even when the verifier accepts it
- a valid interpretation is also held (the trade-off)
- an interpretation-only answer abstains cleanly
- the same draft without the policy still publishes the interpretation
- number checks still hold a wrong finding
- a two-round handoff does not carry the interpretation forward
- all five live drafts replay as in the table above

Full offline suite: OK (1 skipped).

## Limitations

- **Valid explanations are withheld too.** For example, "the Baseline only embeds text, so it fails on images" is withheld even though c0016 states it. For a question that asks "why", the answer will often be `partial` or an abstention.
- **The policy trusts the writer's label.** An explanation the writer labels as a `finding` is judged as a finding (quote, number and verifier checks). The policy cannot see that the writer is unaware of it, so it gives the writer no incentive to relabel. Mislabelling remains possible. If it shows up, add a causal-language screen for findings.
- **The `partial` label for F01 is the coverage label, not a missing answer.** All four required points are published.

## Optional live check: wired, not run

Mode `gemini_paired.py --run --policy-stage-a`, launched through `gemini_credential.py policy-stage-a`:

- Same settings as Stage A v3, plus quote grounding and the policy in both arms.
- F01 and F03 only, at most 18 generations.
- New one-shot directory `data/processed/gemini-handoff-paired-v5-policy-stage-a`.

The policy itself is deterministic, so this run would only confirm the live drafts and provider behaviour. Expected usage is the same as v3: about 10 generations and about 120k prompt tokens.

## KPMG app integration

In `experiments/table-endpoint/live_backend.py`, where the `--agentic` orchestrator is built, apply `quote_grounding.enable(...)` and `interpretation_policy.enable(...)` behind one opt-in flag. Response and UI contracts are unchanged: withheld interpretations arrive in `held_claims` with their reason.

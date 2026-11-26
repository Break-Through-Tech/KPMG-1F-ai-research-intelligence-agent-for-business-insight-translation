# Downstream business translation v1

## Pre evaluation corrections

The bounded correction pass on top of `bde8959` uses prompt version 1.1.
The downstream path no longer sends the legacy COMPACT_POLICY; `concise=True`
retains schema validation, length bounds and exact duplicate handling separately.
Provenance records both the template hash and the complete rendered prompt hash
at dispatch, with an explicit empty instruction-suffix list.

Safety screening no longer deletes negated spans. It checks each positive match,
exempts only its directly negated predicate or a complete restricted negative
evidence-gap proposition, and rejects ambiguous double negation. The three exact
Claude repros and mixed claims across every business field are regression cases.
Bounded sandbox/prototype/limited-pilot recommendations can pass with explicit
validation conditions; readiness, guarantees and enterprise rollout are still
screened independently. A conditional word alone provides no exemption, nor can
a sandbox in another clause authorize an unbounded deployment action.

Research-input origin/file/content hash and business-generation kind/provider
are separate. A model route over synthetic research is labeled model-generated
business output, with synthetic research disclosed independently. Injected and
canned outputs remain fixtures. Kind is a declaration from the configured route,
not independent proof of provider execution; this pass made no live calls.

Local browser QA verified initial and repeated translation, citation rendering,
version persistence, forced failure and recovery. The suspected review-reset
defect was not reproduced: new versions correctly start pending, and older
reviews and original research remain intact. See
`business-corrections-qa/report.json` and its screenshots. The previous v1 offline
receipt is historical; the correction receipt records the current verification.

The live evaluation must score generic recommendations, workflow parroting,
semantic repetition and excessive pilot reliance explicitly. Reviewers judge
whether the action adds a research-specific decision; the runtime does not infer
semantic quality from an action-verb whitelist. Keep reference-aligned cases
separate from genuinely unseen cases and freeze both before live generation.

Implementation base: `579aca109889516c54c695692f3c8898b334028e`.
Branch: `feat/business-translation-v1`. No model calls or deployment were used
to implement or test this change.

The five KPMG sample insights define the quality target: evidence, business
relevance, and a proportionate implication or action. The runtime prompt contains
this general guidance, not the examples or their answers. Research-specific
decisions, evidence requests, process changes and deferred decisions are useful
outputs; a pilot is only one possible action.

## Architecture and use

`src.business_insights.translate_result` consumes a frozen, fingerprinted result,
explicit industry/capability, workflow and optional decision, and an injected
generator. It never invokes a research engine, retrieval, context extraction,
presentation rewrite or regulatory assessment. It uses the existing translator
with `downstream-v1.1.txt` and the existing BusinessInsight contract. One successful
request attempts one additional generation call, without automatic retry. Research
alone retains its existing call count. Frozen S2/R2 code and research prompts are
unchanged. Combined two-call business generation is deliberately deferred.

The accepted-research projector requires prior review metadata in the new path.
It excludes interpretations, held claims, original drafts and unrelated evidence.
It checks all provided support quotes and sends their union per cited chunk,
retaining source locators. A malformed quote fails instead of exposing a full
passage. A reviewed legacy item without quotes uses its cited passage, with that
weaker boundary recorded explicitly. Accepted caveats and the coverage gap survive
translation. Metadata and fingerprints indicate pipeline review/integrity, not
source authenticity, independent entailment or human approval.

The legacy integrated industry path also uses the clean projector, independently
of `quality_check`. That legacy path still permits unreviewed summaries for
compatibility; it is not the new reviewed downstream entry point. Its existing
baseline prompt/provider behavior is otherwise retained. Do not use it to claim
the new safeguards are applied.

The new stage creates a pending copy. Original summary and evidence are unchanged;
old business output and regulatory assessment are not carried to a new application.
Provenance binds source fingerprint, accepted bundle, business context, evidence
bounds, prompt/implementation/checker hashes, provider/model metadata, attempts,
duration and screening decisions. Raw unsafe statements and provider errors are
not put into that audit. A failure preserves the research, marks only business
failed, and cannot manufacture an abstention or approval. No usable findings skip
generation. A screen withholding all implications produces an explicit abstention.

### Local UI after approval for provider use

The separate opt-in host reads the existing local brief store. It does not start
or change the running research server. Use a copy of the saved-work database for
evaluation and a separate authorized provider configuration; do not share campaign
state or credentials by assumption.

```powershell
python -m src.business_demo --library <evaluation-library.sqlite3> --configured-provider --port 8791
python ui-consult/serve.py 8792 --backend http://127.0.0.1:8791
```

Open a saved answer and expand Business implications. Supply the relevant workflow
and decision. The existing citation/action/assumption/limitation display renders
the result; backend screening/provenance stays in the snapshot. Translation uses
the server's saved version, never browser-supplied research. A stale version or
fingerprint is rejected before generation. Saving uses optimistic versioning;
the original version remains intact. A timeout requires reloading saved work
before retrying, because generation may have completed. The normal and Azure
launchers do not expose this capability. Regulatory assessment remains separate.

### Explicit saved-result command

```powershell
python -m src.business_insights --input <research.json> --output <new-business.json> --industry Advisory --workflow "Documenting onboarding handoffs" --decision "Which missing steps need verification?" --configured-provider
```

The input may be a result or envelope. The output refuses overwrite and can use
the existing JSON import/display/export workflow. `--fixture-response <json>` is
an offline alternative to `--configured-provider`, explicitly marked as a fixture.
Neither command above was run against a live model during implementation.

## Safeguards and usefulness

The versioned prompt separates observed study scope from conditional applications,
requests a meaningful workflow-specific decision, avoids padding and repeated
disclaimers, and explicitly permits cross-industry interpretation with assumptions.
It requests an observable check or decision criterion without inventing acceptance
targets. Risks must be evidence based or labeled potential concerns; missing
information must be labeled as an evidence or transfer gap.

Surface checks reuse the existing dependency-free numerical/premise checker.
They withhold known unsupported financial projections, compliance/readiness claims,
exaggerated benefits, changed numbers and detectable invented factual premises in
any business field. Actions without any source/context connection are withheld;
semantic specificity is evaluated by reviewers, not an action-verb allowlist.
Repeated actions with the same citations and assumptions
are withheld; distinct transfer conditions are retained. Prompt instructions handle
semantic repetition; lexical similarity is not used to merge different findings.

These are conservative heuristics, not a semantic verifier. They can miss subtle
unsupported causal claims, scope changes and formulaic recommendations, or reject
legitimate wording. A valid citation and matching number do not prove entailment.
Business advice remains a draft for source-aware professional review. No independent
business-review model call is added and no model-quality improvement is claimed.

## Offline validation and bounded live evaluation

Tests cover clean/quote-bounded handoff, caveat preservation, review requirements,
fingerprint checks, one-call execution, abstention and provider failures, versioned
storage, fixture identity and selected adversarial statements. Existing research,
business, human-review, HTTP and saved-work regressions must also pass.

`tests/fixtures/business/downstream-reference-v1.json` contains five handwritten
canned cases with synthetic abbreviated evidence aligned to the KPMG examples.
They demonstrate contract compatibility and preservation of useful conditional
actions, not automatic generation or verified scientific claims. Other adversarial
and workflow fixtures are synthetic development cases as well. None are genuinely
unseen evaluation results. Runtime never loads the reference fixture file.

After approval for live provider use, compare baseline and downstream prompts on
the same verified accepted packets. Keep five reference-aligned cases separate
from a reserved set of genuinely unseen business questions authored independently
and frozen before generation. Reconstruct paper evidence for the reference cases;
do not use the synthetic unit-test excerpts as verified research. Include weak,
conflicting and unsupported-benefit cases. Use two independent reviewers on a
shared subset and every critical failure. Score fidelity, business relevance,
specificity, proportionality and limitations separately; track generic/repetitive
advice and useful coverage alongside safety. Proposed gates: no critical invented
financial/compliance/readiness assertions, traceable factual premises, appropriate
abstention, average usefulness >=4/5. Report per-split denominators, failures,
calls/tokens and latency. Stop after one paired comparison and one bounded fix
pass. Seek KPMG review before claiming stakeholder usefulness or acceptance.

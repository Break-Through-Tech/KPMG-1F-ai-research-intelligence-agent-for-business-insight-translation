# Evidence-scope review (opt-in, offline-tested)

Status: implemented and tested offline only. No live calls. Not yet wired into `gemini_paired.py`.

## Why the F01 interpretation passed (from the saved Stage A records)

The claim: "The significant performance gap … on these question types indicates that MultiFinRAG is more effective at retrieving relevant information and integrating it…"

1. **Deterministic checks had nothing to test.** The quote is genuine, so exact-quote membership passed. The claim has no numbers, so the number check reported `passed` trivially. No code check covers population, category or condition for claims without numbers.
2. **The claim's scope was implicit.** "These question types" refers back to other claims (image-based and table-based). The claim itself names no category, so its scope only exists through cross-claim context.
3. **The verifier gives one holistic verdict.** Its prompt lists population and conditions among many things "supported" must cover, but nothing makes it state what each side applies to. Its recorded reason only matched the wording: "The passage explicitly states that the transition … underscores the framework's ability to retrieve…".
4. **The verifier never compared the two scopes.** The sentence ("This improvement underscores …") sits in the paragraph about questions needing both text and image/table reasoning (0% → 40%). For image and table questions, the paper credits the Baseline's text-only embedding and Gemma 3's better descriptions (c0016, c0017).
5. **Contract mismatch.** Synthesis is told that an interpretation's quotes are *premises*, not validation. The verifier still issues `supported` for interpretations under the same rule as findings.

The general pattern is **scope transfer**: a result or explanation stated for one category, dataset, model, condition or subgroup is applied to another, or to an aggregate. It is not specific to this paper. The original-wire v1 run published the same kind of over-attribution (an image-only explanation extended to table questions). Number checks catch scope transfer only when the claim carries numbers.

## Change

`experiments/agentic/scope_review.py`, enabled with `scope_review.enable(engine)`. It works with both orchestrators. It adds no model call and uses the same verifier call and budget.

- The verifier prompt gets a SCOPE CHECK instruction. The wire schema adds four fields per verdict, placed before the verdict:
  - `claim_scope`, with references such as "these results" resolved
  - `evidence_sentence`, verbatim from a cited passage
  - `evidence_scope`, read in the context of the passage
  - `scope_match`: same, narrower, different or unclear
- Code enforces the decision. The verifier's verdict is only ever withheld, never upgraded:
  - `different` → withheld with `overgeneralization`. This applies to any claim.
  - An interpretation whose `evidence_sentence` is not found in a passage it cites → withheld with `missing_support`.
  - An interpretation whose scope is anything other than `same` → withheld. An explanation of a superset, or of an unclear scope, is not established for the subset.
  - A finding with `unclear` or `narrower` keeps its verdict. Exact quotes and the number checks already bind findings to their rows. This avoids new false abstentions.
- A withheld claim becomes `partially_supported`. The existing verifier agent then holds it, and held claims are never published.
- The scope fields are stripped before the existing schema validation. A reply missing them raises, so the existing verifier rejects the review and holds every claim (fail closed). The first test run found that this path published instead, and that was fixed.
- Unchanged: quote grounding, exact-quote validation, number checks, the existing verifier agent, the gate and the envelope. `agents.py`, `handoff.py`, `contracts.py`, `src`, the comparator manifest and the seal all verify unchanged.

## Before/after on the saved Stage A runs (offline)

`experiments/agentic-handoff/replay_scope_review.py` replays the recorded plan, draft, verifier reply and packet through the real orchestrators with grounding on.

"After" adds scope fields to each recorded verdict. These are **source-reviewed labels** that I wrote from the cited passages (the `SCOPE` table in the script). They represent a correct verifier, not Gemini's actual behaviour.

| Arm | Before (= live Stage A) | After |
|---|---|---|
| F01 current | 4 published (3 findings + misattributed interpretation) | 3 findings published; interpretation held (`overgeneralization`). Both required points kept |
| F01 handoff | Same | Same |
| F03 current | 2 published | 2 published (unchanged) |
| F03 handoff | 2 published | 2 published (unchanged) |

New false abstentions: none. Valid claims suppressed: none.

Side effect: the existing coverage rule in the frozen orchestrator relabels F01 `answer_scope` from `full` to `partial`, with the note "1 drafted claim(s) did not pass verification". Every requested value is still published. Only an unrequested interpretation was withheld.

## Tests

`experiments/agentic/test_scope_review.py` has 14 cases, built from verbatim c0016, c0017 and Topo-RAG Table 1 text:

- the F01 misattribution, withheld
- two valid interpretations (image cause from c0016, table cause from c0017), kept and published
- an evidence sentence that is empty, invented, or taken from an uncited passage, withheld
- interpretations with an unclear or narrower scope, withheld
- findings with an unclear or narrower scope, kept
- a dataset transfer (Cora row cited for an Arxiv claim), withheld
- a verifier rejection is never upgraded
- missing scope fields, fail closed
- every claim withheld, a clean abstention
- the Stage A replay
- a documented known gap (below)

Full offline suite: OK (1 skipped), in the Stage A Python 3.14 venv.

## Automated vs needs manual verification

- **Automated and deterministic:** whether the evidence sentence is located in a cited passage; the decision rules; fail-closed handling; the publication outcome.
- **Model-dependent and not measured:** whether Gemini fills `claim_scope`, `evidence_scope` and `scope_match` correctly. **Known gap:** if the verifier labels a mismatch as `same` and quotes a real sentence, code cannot catch it; a test documents this. The F01 benefit shown above assumes a correct label.
- **Manual:** the scope labels in `replay_scope_review.py` came from reading c0012, c0016, c0017 and the Topo-RAG Table 1 rows. The MultiFinRAG Table 1 values were confirmed verbatim on arXiv. The §4.3 category context and the Topo-RAG table came from a summarised fetch that agrees with the indexed passages. A person should confirm them before they are treated as references.

## Limitations

- Interpretations are now withheld unless their scope matches exactly. Some legitimate interpretations that extend a stated result with care will be withheld. This is a deliberate choice of withholding over confident error.
- The verifier schema grows by four string fields. The Gemini schema-state limit hit earlier was on synthesis enums, but service acceptance of the larger verifier schema is unverified.
- Field order is requested by schema position. Whether Gemini writes the scope fields before the verdict is unverified.
- Only one verifier call checks scope. There is no independent second judgment.

## Before Stage B

`gemini_paired.py` needs a new labelled mode that applies `scope_review.enable` alongside quote grounding in both arms, plus one launcher entry. That is not added yet. The cheapest live check is to rerun the Stage A questions (F01, F03) under that label, at most 18 generations. It would show whether Gemini labels the F01 scope `different` without help, before Stage B spends more budget.

## Scoped Stage A rerun: wired, not run

**Mode.** `gemini_paired.py --run --scoped-stage-a`, launched through `gemini_credential.py scoped-stage-a`.

- Identical to the previous Stage A run (same model, temperature 0, simplified-v2 wire, B2 route, budgets, 60 s timeout, frozen arm order, F01 and F03 only, at most 18 generations).
- One addition: `quote_grounding.enable` and `scope_review.enable` are applied to both arms.
- Output goes to the new one-shot directory `data/processed/gemini-handoff-paired-v4-scoped-stage-a`. The v3 Stage A results are untouched.
- No scope labels are supplied. Gemini fills them.

**Report.** `stage_a_report.py` now adds, per arm:

- the scope fields for each claim
- a count of verdicts carrying scope records
- verifier rejections
- an automated pre-check of each required point against the frozen references, read after the run and never used in generation

The pre-check is kept separate from the orchestrator's `answer_scope` label.

**Known behaviour.** If Gemini omits the scope fields, the adapter rejects the reply as invalid structured output. That counts as an execution failure: nothing is published and the paired run stops. `test_stage_a.py` covers this.

### Pass criteria, declared before the run

1. **Independent detection.** In both arms, Gemini's own scope fields withhold the F01 "performance gap … retrieving and integrating" interpretation: `scope_match` is `different`, `narrower` or `unclear`, or the evidence sentence is not in a cited passage. If Gemini says `same` and the claim is published, the criterion fails.
2. **No lost answers.** F01.1, F01.2, F03.1 and F03.2 are published in every arm (automated pre-check plus manual source review).
3. **No new abstentions or false rejections.** Every F03 finding published in v3 is still published. Every F01 finding is still published.
4. **No scope-field gaps.** Every verdict carries scope records, with zero execution failures caused by missing fields.
5. **No misleading claims published,** under manual source review of every published claim.

Interpretation of the outcome:

- An F01 `answer_scope` of `partial` with all four points published is the existing coverage rule reacting to a held claim, not a missing answer.
- A pass is evidence on two questions only. It is not a general accuracy result.

## Scoped Stage A live result (2026-11-23): stopped, partial

Run directory: `data/processed/gemini-handoff-paired-v4-scoped-stage-a`, preserved unchanged. The report is `data/processed/stage-a-scoped-report.json`.

**Why it stopped.** Gemini returned HTTP 503 `UNAVAILABLE` ("This model is currently experiencing high demand…") on the F01 **handoff** synthesis request (receipt 009, 1.3 s). By design, the runner stops on any provider error and does not retry.

It was not:

- a schema rejection: the expanded verifier request (007) returned HTTP 200, and the reply validated with the scope fields written before the verdict;
- a missing scope field: 4 of 4 verdicts carried scope records;
- a research-validation failure.

F01 handoff and F03 (both arms) did not run.

**Usage.** 4 generation attempts (3 succeeded), 9 HTTP requests, 27,849 prompt and 1,697 output tokens reported.

**F01 current.** The evidence packet and the draft are byte-identical to Stage A v3.

| Pass criterion | Result |
|---|---|
| 1. Gemini independently withholds the F01 interpretation | **Failed.** `claim_scope` and `evidence_scope` were both "MultiFinRAG framework performance" and `scope_match` was `same`. "These question types" was not resolved to image and table questions. The interpretation was published |
| 2. Required points published | F01.1 and F01.2 published (automated pre-check) |
| 3. No new abstentions or false rejections | None in F01 current |
| 4. No scope-field gaps | 4 of 4 present; the schema was accepted |
| 5. No misleading claims published | **Failed:** the F01 interpretation, again |

**Conclusion.** This is the "known gap" case. Gemini 3.1 Flash-Lite at temperature 0 described each scope at the system level ("framework performance") rather than at the population level. As a result, the code rule never fired. With one observation, in-verifier scope fields do not fix this failure.

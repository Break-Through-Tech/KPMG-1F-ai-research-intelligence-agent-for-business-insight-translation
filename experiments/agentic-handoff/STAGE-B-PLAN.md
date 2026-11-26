# Stage B: grounding + interpretation policy on F04–F10 (pre-registered, not run)

Recorded on 2026-11-23, before any Stage B generation. Changing these criteria after the run requires a new label.

## Configuration

- **Mode:** `gemini_paired.py --run --policy-stage-b`, launched only through `gemini_credential.py policy-stage-b` with the dedicated Python 3.14 venv.
- **Questions:** frozen F04–F10 from `experiments/measure/fresh-diagnostic-v1/questions.json`, unedited. The frozen alternating arm order is kept: F04, F06, F08, F10 run current first; F05, F07, F09 run handoff first.
- **Arms:** current Multi-Agent (`OrchestratorAgent`, research-only) and evidence handoff. `quote_grounding.enable` and `interpretation_policy.enable` are applied identically to both. Scope review is **off**.
- **Unchanged:**
  - B2 route (pinned index, table comparisons, top-k 8, at most 14 passages)
  - one shared planner reply per question
  - matched initial evidence across arms
  - exact-quote validation, the number checks, the model verifier, the publication gate and the envelope
  - the comparator manifest and the seal, which the runner checks before starting
- **Provider:** `gemini-3.1-flash-lite`, temperature 0, simplified-v2 synthesis wire, 60 s timeout, no retries, no fallback.
- **Budget:** at most 63 generation attempts (7 × 9). Each generation is preceded by a `countTokens` request.
- **Quota safeguards:** the existing SQLite reservation gate (10 RPM, 200k reserved input tokens/min, 400 requests per rolling day). The operator confirms Free tier, billing disabled and exclusive use, and gives a 24-hour bound of at most 200. A 61 s cooldown follows.
- **Output:** the one-shot directory `data/processed/gemini-handoff-paired-v6-policy-stage-b`. It is never overwritten.
- **Stop rule:** any provider or integrity error stops the run. Completed pairs are kept and scored. Unrun questions are reported as unrun, never as failures.

## Retrieval ceiling, known before the run

Offline, original-question-only retrieval (`offline-retrieval.json`) returns the required anchors for:

| Question | Anchors returned |
|---|---|
| F04 | 1/2 |
| F05 | 0/3 |
| F06 | 3/3 |
| F07 | 2/2 |
| F08 | 1/2 |
| F09 | 2/2 |
| F10 | 2/2 |

Planner sub-searches may add more. A point whose anchors never reach a synthesis packet is scored as **retrieval-limited**, separately from draft and policy outcomes, under the frozen `rules.json` point attribution.

## Criteria (frozen `rules.json` definitions apply)

Each criterion is reported per question and per arm, with denominators.

1. **Required-point correctness.** A point counts only if it is published accurately with entailing citations. This comes from manual source review against the cited passages. The automated pre-check (anchor cited, expected numbers present) is only a screen. F04–F10 have few numbers, so for these questions the screen mostly reduces to "anchor cited".
2. **Completeness.** Each case is classified as complete, partial, false abstention, evidence-limited abstention, or retrieval-limited.
3. **Unsupported published claims.** Every published finding and limitation is source-reviewed. Counts are supported / unsupported / unreviewed. Target: 0 unsupported.
4. **Abstentions.** False versus evidence-limited, classified by whether the synthesis packet jointly supported all required points.
5. **Withheld explanations.** Every interpretation held by the policy is listed and judged against its cited passage. It is counted as a *valid explanation withheld* (the policy's cost) or a *bad explanation blocked* (the policy's benefit).
6. **Policy bypass (relabelling).** Each published finding with explanatory or causal wording is flagged automatically (`findings_with_explanatory_wording`). A manual review classifies it as a faithfully reported author claim (allowed) or the writer's own inference labelled as a finding (bypass). The bypass rate is reported.
   - Baseline: across the 11 unique recorded live drafts, 0 of 22 findings use such wording, and 4 of 4 interpretations do.
   - These flagged findings are not held automatically. Qualitative points such as F10.1 ("biased … data may produce biased outputs") are reported author claims that carry causal wording, and auto-holding them would suppress required points.
7. **Provider and execution failures.** Reported separately, by stage, HTTP status and question. They are never scored as abstentions or incorrect answers.
8. **Latency.** Wall time per arm, plus median and p90 across completed arms (including quota pauses). Generation attempts, HTTP requests, and prompt/output tokens from usage receipts.

The arm comparison (current vs handoff) uses paired wins, losses and ties on completeness, and on unsupported claims, over completed pairs only. It is a development signal, not a general accuracy claim. Scoring is machine-assisted unless a person signs off.

## Readiness checks (offline, 2026-11-23)

- The full offline suite passes in the Python 3.14 venv. This includes `test_stage_a.StageBWiring`: the mode covers F04–F10 only, with grounding and the policy, no scope review, a cap of 63 and its own directory.
- The comparator manifest, seal and preflight `verify()` pass. The credential launcher's environment probe passes.
- `src`, `agents.py`, `handoff.py` and `contracts.py` are byte-identical to the automated reviewer worktree.

## Amendment (2026-11-23): v6 stopped; v7 label adds bounded retry

**v6 outcome.** Run `data/processed/gemini-handoff-paired-v6-policy-stage-b` is preserved. It stopped on HTTP 503 `UNAVAILABLE` ("high demand") at the F04 handoff **verification** request (receipt 007). The plan and the synthesis had both succeeded. No pair completed and nothing is scorable. Usage was 3 generation attempts and 7 HTTP requests.

Three of the last four live runs stopped on provider overload or a timeout. Because the runner stops on the first provider error, a 14-arm run is unlikely to finish.

**v7 label.** Mode `--policy-stage-b-retry`, launcher entry `policy-stage-b-retry`, output `data/processed/gemini-handoff-paired-v7-policy-stage-b-retry`. It keeps the same questions, arms, switches, model, settings, cap and safeguards as v6, with one addition:

- On HTTP 503 or a timeout, a request is retried up to 2 times, after 60 s and then 120 s.
- Each retry is a new reserved attempt with its own receipt, counted against the same 63-generation cap and the rate gates.
- 400, 429, 500 and every other error still stop the run immediately.
- At temperature 0 a retry re-sends the identical request, so content-level comparability holds. Retries are reported per question.
- All earlier modes keep zero retries (`test_gemini_retry.py`).

The criteria above apply unchanged. Additional reporting: the count of retried requests, and how many of them succeeded.

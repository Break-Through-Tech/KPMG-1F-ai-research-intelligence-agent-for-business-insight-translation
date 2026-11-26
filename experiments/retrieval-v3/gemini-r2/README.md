# Gemini evaluation handoff

## Verified candidate

The Azure candidate is based on stable application commit a94eb48 and integration checkpoint b88d05b. The optimized retrieval modules match a462275 byte-for-byte. The integration changes are limited to strategy selection, packaging and its tests. Relative to a94eb48, the approved frontend, Azure installer, systemd service, Caddy configuration, asset installer, provider adapter, and saved-brief implementation are unchanged. The local hosted fixture exercised the same handler with R2 active, then switched to S2 using the same signed session cookie and persistent state. Each session and strategy created its own checkpoint. The existing six-call-per-minute limit was observed and allowed to expire during the test. Authentication, origin/host checks, refusal of business analysis, cited answers, review and persistence across restart were exercised. HTTPS termination and Linux service operations remain covered by the existing Azure deployment work.

The real staging manifest records 67 served assets and 93 runtime source files. The existing onboarding manifest pins the exact demo-100 assets, model snapshots and matching table audit. The Azure loader continues to verify and install the same three research files. The S3 code seal (29 entries), B1 code seal (13 entries), fresh-v4 set seal (10 entries), and historical unseen R2 code and set seals (14 and 5 entries) are independent of the new candidate seal. Thirteen paths are pinned against checkout line-ending conversion. The historical B1 CLI preflight also invokes an older diagnostic seal that targets a predecessor of the Azure Gemini adapter. That indirect check reports src/generation.py as changed at the candidate, as expected after the stable Azure changes. No historical seal was rewritten.

The six data-dependent test failures in the clean research suite were reproduced and resolved using the locally archived fresh-v4 parent bundle, fresh-v3 saved S2 stages and rank caches. The full 64-test research suite then passed with those assets. The archived inputs, application state, dataset, model weights and generated snapshots are kept outside the commit.

## Offline verification

Use the existing Python 3.11 runtime and a verified local onboarding asset directory. Prepare the real deployment snapshot offline once the pinned assets are present.

```sh
python -B onboarding/setup.py setup --runtime native --prepare-only
python -B experiments/retrieval-v3/gemini-r2/run.py --assets <asset-dir> --snapshot <staged-context>/snapshot
python -B experiments/retrieval-v3/gemini-r2/test_budget.py
python -B deploy/render/test_hosted_fixture.py --engine s2 --retrieval r2
```

The hosted fixture command uses the synthetic context. Prepare it separately with the existing fixture setup and cached models, then allow loopback access. Without the live opt-in, run.py only verifies the campaign and runtime hashes and that every scoring anchor is in the pinned demo-100 corpus.

## Evaluation after authorization

The eight new questions have 36 points across three named two-paper questions, three unnamed multi-part questions, and two controls. Scoring anchors were checked against the deployed bundle. The paper versions are part of the anchor IDs. Questions and points were cross-checked against earlier keys for repeated facts. Have an independent reviewer confirm the key before dispatch. Keep both scored outputs blind until scores and safety flags are locked.

The standalone runner uses the application Gemini adapter, its native schema and local validation, temperature 0, the 60-second deadline, and the application's retry policy. It uses the same indexed application entry point, pinned models, and evidence budgets in both arms. The model in the stable Azure application source is gemini-3.1-flash-lite. Campaign state must reside in one private, persistent directory. Preserve the whole directory across restarts and never start a fresh ledger to resume. An unexpected exit can leave active.lock in place. Confirm the old process has stopped and inspect dispatch.sqlite3 before clearing that lock. Checkpoints and attempts are partitioned by arm and question.

Start with S2 U1 and U2. Their four expected generation calls are included in the paired run and retained for scoring. Any incomplete smoke question stops the campaign for review. Once both smoke questions pass, run R2 U1/U2 and alternate arm order by question from U3. Allow one resume per arm/question after a minimum five-minute backoff. Expect 32 generation calls with a persistent cap of 40 total and 20 per arm. Reservations are atomic and taken before every SDK send, including transient retries, timeouts and failed attempts.

The campaign reserves up to 1.2 million input tokens and 150,000 output tokens. It reserves input by UTF-8 payload size plus framing headroom, sets max_output_tokens to 3,750 with minimal thinking, counts returned thinking tokens in usage and halts future sends if a reservation is exceeded or a successful response has missing usage. The input ledger reconciles successful receipts and keeps the conservative reservation for failed or unknown sends. These guards are conservative but cannot guarantee an exact hard ceiling for provider-side prompt framing, thinking tokens, or usage from a failed request. The live command requires explicit acceptance of that limitation. At Google's published standard paid rates of USD 0.25 per million text input tokens and USD 1.50 per million output tokens including thinking, consuming the entire reserved amount would cost about USD 0.53. Actual charges depend on provider usage. A Cloud budget alert is a notification. Use an approved isolated project and its permitted request quota. [Google Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite)

After approval, inject GEMINI_EVAL_API_KEY securely in the evaluation process. Use the authorized account and model, quota and spending tier, and confirm permission to send excerpts from these research assets to that provider. Review data-use terms for the selected tier. Azure credentials and state are outside this campaign.

```sh
python -B experiments/retrieval-v3/gemini-r2/run.py --assets <asset-dir> --snapshot <staged-context>/snapshot --state <private-persistent-campaign-dir> --authorized-run --accept-estimated-token-guard
```

Blind-score each required point at 1, 0.5 or 0 and count failed answers as zero. Audit cited chunk/quote grounding, numbers, and misleading or unsupported assertions. Use the saved results, stage timings, attempt records and dispatch ledger to report arm totals, median and nearest-rank p90 latency, per-arm input/output usage, timeout/retry outcomes, and completeness. To recommend R2, require at least 7/8 complete per arm, a score improvement of at least 2/36, zero new safety flags, R2 median at most 1.25 times S2 and at most 120 s, p90 at most 180 s, and R2 input usage at most 1.10 times S2. Report any incomplete usage receipts as a limitation in the comparison.

Separately report absolute answer completeness as blind rubric points earned divided by 36 for each arm. With half-point scoring the first passing score for the 85% target is 31/36 (86.1%). The question completion rate is successful answers out of eight and retains the independent comparative gate of at least 7/8 in each arm.

U2 asks for the five sealed facts about extraction, indexing, encoder placement and measured bitrate. Prefilter smoothing and detail preservation appeared in prior calibration and are outside its scoring key. The revised wording was independently reviewed against its pinned excerpts before any provider call.

Azure leaves the request output cap unset and uses the provider default for thinking. Both evaluation arms explicitly use minimal thinking and a 3,750-token request limit. Long, otherwise valid structured drafts and reviews can exceed that limit. Record output-limit finishes as failures and consider truncation when interpreting the comparison. Provider behavior at the limit remains unmeasured offline.

The evaluation runner screens its complete request body at the SDK boundary for email addresses and a few recognizable sensitive formats and halts before sending a match. It applies the same rule to both arms and retains the pinned corpus. Offline payload inspection can cover questions, evidence and metadata plus a scripted draft. Actual provider-generated drafts become inputs to review, so their contents cannot be certified in advance. Pattern checks cannot establish data-use permission or rule out all sensitive data. Keep dispatch on hold until the project clears the selected tier and the outbound evidence policy. Promotion or deployment requires a separate decision.

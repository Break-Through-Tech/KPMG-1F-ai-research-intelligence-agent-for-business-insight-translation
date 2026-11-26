# Gemini-only autonomous session

Objective: prepare a fair paired comparison of the current Multi-Agent snapshot and evidence handoff, then improve confirmed weaknesses if live evidence is available.

Starting comparator archive SHA-256: 769a7aaa4cfc9c8c8632efb7cfd17b2a5e5066a1765ab2a5a1407770823acf50. The comparison set, references and previous scores remain sealed.

## Credential and billing preflight

Process configuration, the experimental checkout and the main checkout dotenv did not provide a Google/Gemini API key. No secret values were printed. The local application environment already has google-genai 2.33.0, google-auth 2.62.0 and jsonschema 4.26.0. No gcloud command or standard application default credentials file was found. Project billing, model access and remaining quota are therefore unverified. An API key alone would not establish Cloud Billing status. Google documents a separate authenticated billing check or the account's AI Studio project and rate-limit pages.

Live generation count: 0. Initial 90 and subsequent 60 ceilings unspent. No Codex CLI or paid API runtime. No provider attempt ledger was opened or initialized because no live session began.

## Offline transport replay

Added test_gemini_replay.py in the isolated handoff directory. The tests initialize the existing Gemini adapter with a dummy key and intercept every synchronous HTTP request before transport. The actual SDK serializes planner, writer and verifier schemas to the Developer API route. Both arms use the exact same gemini-3.1-flash-lite model string and temperature 0. No grounding tools are attached. Scripted replies exercise both end-to-end paths. The first round is partial, and only evidence handoff retains the earlier verified claim in the revised answer. Each arm invokes the fixture five times. A scripted 429 ends either workflow after one attempt; the current shared adapter exposes a generic failure at that boundary. None of these tests establishes service-side schema acceptance, live answer quality, quota, token usage, or latency.

Google lists standard text generation for Gemini 3.1 Flash-Lite as free on eligible projects. The Gemini API supports a subset of JSON Schema. Continue enforcing the full existing schema locally. Google documents automatic rerouting of the legacy 2.5 Flash model beginning December 1, 2026, so the isolated comparison should pin an explicit model ID and reject a model/configuration change during a paired run.

Suite: 105 offline tests passed, including 2 real-SDK / intercepted-HTTP tests. No new runtime patches were justified by the scripted results. The evidence-handoff prototype remains the candidate and the previous archive remains the comparator.

Reproduce using the existing application Python from the checkout root:

```powershell
$env:PYTHONPATH='.;experiments/agentic;experiments/agentic-handoff;experiments/measure/end-to-end-diagnostic;experiments/measure/trace-diagnostics'
python -B -m unittest test_gemini_replay test_handoff test_agentic test_adversarial test_publication_gate test_diagnose test_audit5 -q
```

Resume only when the existing key is supplied to the isolated process as GOOGLE_API_KEY, with its associated project confirmed Free with billing disabled and its actual quota established in AI Studio. Check the model with metadata-only models.get, then confirm its service-side schema handling under the authorized ceiling and use the same model and settings for both arms. Use only public paper excerpts approved for this usage since Google documents Free-tier inputs being available for product improvement. Before live work, create a separate persistent invocation ledger, reserve before each attempt and stop on any provider-wide error. The 90-attempt initial ceiling is further bounded by the actual free quota and is not a quota estimate.

- [Gemini pricing](https://aistudio.google.com/docs/pricing#gemini-3.1-flash-lite)
- [AI Studio projects](https://aistudio.google.com/projects)
- [AI Studio rate limits](https://aistudio.google.com/rate-limit)
- [Structured output](https://ai.google.dev/gemini-api/docs/structured-output)

## Quota-control checkpoint

Added a standalone SQLite reservation gate and tests. The local limits are 10 requests/minute, 200,000 reserved input tokens/minute, 400 requests in a rolling day, and 90 generation attempts for the paired run. Reservations are atomic and persist even without a response. Expired or absent external usage observations cause refusal. The gate does not discover usage on its own, and it is not wired into a live paired runner yet.

Nine offline tests passed. Verified the frozen evaluation seal and confirmed zero matching local evaluation processes at preflight. The key remains in the user's VS Code terminal. No live generation was attempted. Before a live run the remaining dependencies are a current external-project usage source, a bounded pre-dispatch token estimate and connection through the existing VS Code terminal. Historical usage records and the shared demo are untouched.

## Connected paired-run checkpoint

gemini_paired.py connects the frozen capture path, both existing agents and the SQLite budget to the Gemini Developer API. It reserves each metadata/count/generation HTTP request before dispatch, with no redirects or retries. It uses the larger serialized-payload budget to cover schema and framing, checks the Gemini prompt token estimate before generation, and verifies actual reported prompt usage and model identity afterward. It stores provider HTTP status, timings and actual usage without request headers. It preserves one shared planner response per pair and checks matching initial evidence before the second synthesis request. The coordinator stops on provider or integrity failure. It refuses to restart over any existing output directory.

The Windows launch checks for competing known local evaluation processes. The key is read only from the launching process. AI Studio billing and current external project requests require operator verification because the API key cannot query project-wide billing or quota telemetry. The run requires exclusive use, a verified preceding-24-hour external request upper bound of at most 200 and a 61-second cooldown. The 4-hour confirmation expires. Margins remain 10 RPM, 200,000 reserved input TPM and 400 requests per rolling day. The maximum 181 combined metadata and generation reservations for 90 generation attempts fit within that stated headroom. No live request was made in this session.

Eleven tests passed, including both arms through mocked HTTP with a single shared plan, matched evidence, one reservation per HTTP call, and a stop on a simulated 429. The frozen evaluation seal verified. Live output will be written to data/processed/gemini-handoff-paired-v1 and scored afterward against the existing rules. The shell available to the development agent still lacks the VS Code terminal's key, so launch is pending in that terminal.

## Live launch stopped at model metadata

The retained paired run stopped on HTTP 400 during its first Gemini model metadata GET (receipt 001). No countTokens or generateContent request was sent, and no question ran. The receipt contains status only, so a precise provider reason cannot be reconstructed from it. Preserve the run directory and ledger. The next diagnostic is a single metadata lookup from the same VS Code terminal, recording a sanitized error reason only. Do not rerun the comparison until the cause is verified.

Model access succeeded in the VS Code terminal after the key was reloaded. A fixed recovery option now checks the original SQLite ledger read-only for exactly one metadata reservation and the original HTTP 400 receipt before creating a separate one-shot recovery directory. No original artifact was overwritten.

## Recovery run stopped during F02

The recovery run passed model metadata and completed both F01 arms. Both published the required MultiFinRAG counts and scores, so the single completed pair is tied on required-point completeness. Recorded per-arm wall time including metering and waits was 153.070s current and 127.757s handoff. F02 handoff reached research generation after a successful token count, then Gemini returned HTTP 400 and the runner stopped. The body was not retained, so the specific cause is unconfirmed. F02 current and F03-F10 did not run. Recovery usage: seven generation attempts, six successful, with 55,574 prompt and 2,843 candidate tokens reported on successful requests. This excludes any unreported usage for the failed request and the separate original metadata-only stop. No rerun was launched.

## F02 HTTP 400 offline investigation

Reconstructed initial synthesis from saved packets, shared planner output and the original synthesis/handoff code. Reconstructed byte estimates match the stored reservations exactly (the accounting JSON representation, not HTTP transport bytes).

| Run | Passages | Prompt bytes | JSON Schema bytes | Accounted payload bytes | Reserved input |
| --- | ---: | ---: | ---: | ---: | ---: |
| F01 current | 11 | 41,108 | 1,925 | 45,168 | 94,432 |
| F01 handoff | 11 | 42,269 | 1,925 | 46,355 | 96,806 |
| F02 handoff | 11 | 36,135 | 2,039 | 40,876 | 85,848 |

Model, endpoint, temperature and JSON MIME type were identical. All three schemas pass local Draft 2020-12 schema validation and match structurally after removing chunk-ID enum values. F02 had eight long table IDs versus five for F01. This made its enum longer, but the complete F02 request was smaller. F02 countTokens returned 200 and generateContent returned 400. countTokens did not include the schema in the submitted request. The missing provider body means schema rejection, a request-specific backend condition, or another explanation remains unconfirmed. No request setting was changed.

The isolated runner now saves sanitized Google status, message, reason, and structured field/quota violations on rejected responses. Raw payloads, headers and arbitrary error metadata are not saved. A mocked HTTP 400 regression checks diagnostic persistence and redaction. Twelve offline tests passed and the frozen seal verified. Original receipts, outputs and ledger were not changed. No live calls.

## Separate F01 research-quality finding

Both arms answered 2/2 required numerical points accurately. Both added a causal explanation about the baseline's difficulty with image and table questions. Their cited 2506.20821v1_c0016 excerpt attributes the gap to the baseline extraction method for image questions only. The table-side causal attribution exceeds the cited evidence in both answers. This is separate from the provider error. No architecture change was made.

Do not continue the stopped run while the F02 failure remains unexplained. If later evidence supports a material request change, run a newly labeled comparison for both arms under that configuration. If request settings can remain identical and continuation is approved, leave the F02 pair incomplete and handle only wholly unattempted pairs as a separate continuation, with its selection rule and budget recorded before running.

## Credential Manager launcher

Added gemini_credential.py and test_gemini_credential.py. The launcher uses a local-machine-persistent Windows Generic Credential scoped to the current Windows user, stored under KPMG.Team1F.Gemini.DeveloperAPI. Store reads the already configured terminal variable or accepts a hidden local prompt. Launch reads the credential locally and gives it only to the approved child in its process environment. Other provider credentials are omitted. The only registered live experiment is the previously approved one-shot schema probe, which keeps its quota and billing checks. No generation was called in setup.

Two offline tests passed in the Windows user context. A disposable dummy secret was written and read back through the real store, injected into a Python child, verified absent from command arguments and output, and removed. An unapproved experiment was refused before credential loading. The managed shell returned Windows access denied when accessing Credential Manager without the Windows user context. The real key has not been handled by the development shell. After the user stores it locally, check status through the approved Windows user context, verify the current free-tier conditions and quota, then allow only the single authorized schema probe.

Credential Manager status verified from the Windows user context after the user stored the key. The credential value was not printed and the one-shot probe directory remains absent. Attempted to verify AI Studio usage through desktop/browser controls. Both browser automation entry points failed to initialize their local kernel assets (Windows path not found), so no current usage was observed. The diagnostic was not sent.

## One authorized schema diagnostic completed

AI Studio showed kpmg on Free tier, with 15 requests in the largest visible one-day bucket and one smaller bucket. Used a conservative 30-request upper bound and waited 61 seconds. The launcher retrieved the credential in Windows and passed it to the child process. Exactly one synthetic generateContent request, no other provider calls or retries. HTTP 200 in 2.159 seconds; response passed the synthesis schema. Provider reported 9,634 input and 139 output tokens. F02's HTTP 400 remains unexplained. The synthetic result establishes that Gemini accepts the schema shape and comparable citation-ID counts and lengths on at least one fixture. It does not establish compatibility with the actual F02 request. No request configuration was changed and the paired evaluation remains stopped.

## Approved F03–F10 continuation

Added a fixed continuation mode. It verifies F01 and the original F02 metadata, refuses if any later pair was already attempted, creates a distinct one-shot output directory, and caps generation at 72 without changing the model, prompts, evidence settings, or frozen inputs. The Credential Manager launcher now allows this specific mode. Twelve offline tests passed and the frozen seal verified. The Free-tier dashboard supplied for the immediately preceding probe showed two usage buckets; a 40-request conservative upper bound includes both and the probe. No billing changes were made. F01 and F02 are excluded from execution.

## Continuation outcome

F03 current completed its shared plan, then Gemini rejected synthesis with HTTP 400 INVALID_ARGUMENT. The new receipt records Google's explanation that the structured-output constraint has too many states for serving. This confirms a schema-complexity rejection on F03, but does not retrospectively establish the precise F02 cause. F03 handoff and both arms for F04–F10 were not run. No retry or settings change was made. The continuation used two generation attempts, one successful, and five total HTTP requests. Reported usage on the successful planner was 328 input and 207 output tokens. The failed synthesis generated no usage receipt.

The original F01 pair remains the only completed pair. Under the frozen scoring rules, both arms answered the two required numerical points but are partial overall because the cited passage supports the extra causal explanation for image questions only. The final paired outcome is zero handoff wins, zero losses and one tie. No false abstention occurred in the completed pair. F02 and F03 are incomplete execution failures. Retain handoff as an experimental candidate, withhold promotion pending more completed source-scored pairs under a separately labeled common provider configuration.

## Gemini synthesis wire schema reduction (offline)

The F03 receipt confirmed constrained-decoder state exhaustion, without identifying a specific keyword. The isolated Gemini integration now removes dynamic citation-ID enums and array/string length bounds from the synthesis wire schema only. It retains object fields, required keys, types, and the small status/kind enums. The master local schema, exact quote and ID checking, numerical checks, and publication gates still run unchanged. The original labeled CLI evaluation modes remain bound to the historical wire format. F03's schema fell from 2,095 to 1,001 bytes in diagnostic serialization. F01–F03 archived table packets yielded identical simplified schema shapes despite different citation IDs. A mocked transport validated acceptance of a good fixture and local rejection of invented IDs, undersized quotes, invented quotes, and excess claims. Offline suite passed 19 tests and the frozen seal verified. No live requests made.

Proposed compatibility check: one authorized generation request on a synthetic packet matching F03's 14 passages and six table rows, using the simplified wire schema and original local checks. A successful probe verifies only that fixture. Start any paired comparison under a new label with the same Gemini wire configuration in both arms.

## Simplified Gemini wire schema live probe

Exactly one authorized synthetic generation request ran on Gemini 3.1 Flash-Lite with 14 passages, six synthetic table rows, and the simplified synthesis wire schema. The offline one-shot fixture passed first. The runner used the existing Windows credential, a conservative 50-request prior-use allowance and its 61-second cooldown. The provider returned HTTP 200 in 1.684 seconds with 16,308 prompt tokens and 113 output tokens. The full local JSON schema, exact citation/quote checks and deterministic numerical contradiction check passed. Nothing was published and no verifier call was added. The output directory is data/processed/gemini-f03-simplified-schema-probe-v1. The stopped F02/F03 runs and prior probe remain preserved. This supports testing the simplified wire configuration in a new paired evaluation but does not prove all real packets will succeed. No evaluation or retries were started.

## Simplified v2 paired evaluation and release review

Added a distinct one-shot simplified-v2 label and Credential Manager entry. Both arms share the simplified synthesis wire format, while prior modes and outputs remain original. Thirteen isolated offline tests passed and the frozen seal verified. The initial launch failed before any provider access on a Windows paging-file limit when importing SciPy. Local-only retrieval preflight subsequently loaded the exact pinned encoder and reranker; the same approved run was launched from scratch with no earlier quota consumption. No shared service or system settings were changed.

Read the isolated consultant UI handoff and the existing B2 and fixture launch paths. Ran 60 model-free Baseline/demo/BYOK tests and 35 subtests successfully. Saved BASELINE-DEMO-READINESS.md for automated reviewer’s read-only integration handoff. No UI files changed and no live UI research was submitted.

Simplified-v2 finished with a systemic stop: Gemini synthesis read timeout on F03 handoff, after two complete pairs. F01 was a tie of two false abstentions after exact quote rejection. F02 was a tie of two complete, source-supported answers. F03 current also false-abstained after quote rejection; the handoff timeout is unscorable. F04–F10 were unrun. Actual usage: 11 generation attempts, 10 usage receipts, 97,498 prompt tokens, 3,747 candidate tokens, 23 total HTTP requests. No use of other providers, retries, paid fallback, or further Multi-Agent experiments. See SIMPLIFIED-V2-RESULTS.md. Consultant proxy tests also passed 8/8, with an expected fixture late-write socket exception.

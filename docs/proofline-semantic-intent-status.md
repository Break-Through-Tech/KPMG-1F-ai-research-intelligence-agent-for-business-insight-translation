# Semantic intent and business reliability: status at ff58ca8 (27 Nov 2026)

Development is frozen. `khoi/proofline-semantic-intent` @ `ff58ca8` builds on the reliability fix `2bc0846`
(`khoi/proofline-business-reliability`), which builds on the deployed `2309de9`. Nothing in this branch is deployed.

## Verified
| Check | Evidence |
|---|---|
| Offline suite | 159 passed, 247 subtests; both seals `verified` |
| Browser smoke (staged real index, scripted providers) | default and business modes pass; the business run exercised the fallback to rules |
| Hosted-fixture gate | baseline and S2 pass |
| Live, local, 11 of 12 approved calls | Developer and accounting questions: semantic intent and verbatim context correct (accounting workflow "checking invoices for mistakes", which the rules got wrong); automatic dispatch used the saved classification with no second call; research summary and evidence preserved. Fresh academic question: not business, no dispatch, no prompt. Research citations valid in all three. |
| Reliability fix, live | Hydrogen HTTP 429 RESOURCE_EXHAUSTED classified `quota_exhausted`: one attempt, no retry, no inline retry offered, sanitized log line |
| Not verified | Hydrogen output for the two business questions (the project's quota was exhausted) |

Pilot evidence: on the 16 scored questions, the semantic classifier dispatched 11/11 business questions (rules 7/11) with 0 automatic false positives (rules 1). Extracting context inside the S2 draft dropped logistics findings from 3 to 1, while the unmodified control reproduced production exactly. That is why the classifier is a separate call.

## Open concern 1: shared provider quota
The research pipeline and the semantic classifier use the same research key, so the same Google project.
Their local ledgers are separate on purpose, so the classifier can never use research's local allowance:
- research `provider-usage.sqlite3`: 6 attempts per minute, 60 per day, 160k tokens per minute;
- classifier `intent-usage.sqlite3`: the same limits.

The provider limits are shared:
- **Per minute:** research handles one question at a time, so traffic stays around 3 calls per question.
  That is well under the free tier's ~15 requests per minute (observed: 9 calls in about 4 minutes with no 429).
- **Per day:** not coordinated. The two ledgers allow 120 calls a day together. If the project's daily request
  limit is lower than that, classifier calls can exhaust the quota research needs, and research then fails
  with a provider 429.

Before deployment, confirm the project's daily limit for `gemini-3.1-flash-lite` in Google AI Studio. If it is
below 120 per day, lower the classifier's daily cap or have it skip when research's ledger is near its limit.
That is a small hosting-layer change, not made here.

The Hydrogen project is separate. Its daily quota was exhausted during live testing on 27 Nov. The same
0.2 s 429 explains the earlier 0.2 s "validation" failures seen at `2309de9`.

## Open concern 2: classification is not carried into business versions
The sanitized `business_intent` record is saved with the research answer (version 1) and reused by automatic
dispatch. The business response (version 2 and later) is built by `translate_result` and does not copy it.
- **No effect today:** automatic dispatch only applies to fresh version 1. The inline retry and the Workspace
  form are prefilled from `provenance.business_translation.context`, which holds the semantic context.
- **Gap:** after a business version, the semantic record is only on version 1. Any future feature that needs
  it on the latest version, such as an automatic retry or analytics, would fall back to the rules.
- **Fix when development resumes:** copy `business_intent` from the source envelope in `/api/business`.
  Not done here (frozen).

## Remaining Hydrogen checks (after the quota resets; no research is regenerated)
Saved answers are preserved outside the repo:
`C:\Users\ngkho\src\live-ff58\preserved\briefs-ff58ca8-live-20261127.sqlite3`, with a working copy in
`C:\Users\ngkho\src\live-ff58\state\`.

| Brief | Latest version | Saved semantic context |
|---|---|---|
| Developer code review `9793d214…` | v2 `5f847d9c…` (`business_quota_exhausted`) | software / "reviewing AI-generated code" |
| Accounting invoices `1aca3ff9…` | v2 `05b3035e…` (`business_quota_exhausted`) | accounting / "checking invoices for mistakes" |

Procedure (at most 2 Hydrogen calls each, one retry only for a temporary failure):
1. Start the same local server on the same state folder: `powershell -ExecutionPolicy Bypass -File C:\Users\ngkho\src\live-ff58\run.ps1`.
   Clear `calls.json` first and set a new cap.
2. In the UI, open each brief from Library. Exhausted quota offers no Try again by design, so use Workspace →
   Business insight → Generate. The form is prefilled with the saved semantic context, and submitting makes
   one manual request against the latest version. No research call is made.
3. Verify: an insight is published, its citations point to accepted evidence, research is unchanged, a new
   version is saved, and the inline cards render in the Answer view.

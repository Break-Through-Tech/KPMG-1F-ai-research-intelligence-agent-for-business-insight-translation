# Proofline Windows development handoff

## Start here

The team development build is `integration/proofline-business-hydrogen` at
`e644589848feb83b6e18aac36a75c4c12fcc429e`. This documentation branch contains
the same application code plus this handoff, the setup links, and a local
environment template. The branch names below are independent review points.

| Purpose | GitHub branch or historical pin | Exact commit |
|---|---|---|
| Integrated application | `integration/proofline-business-hydrogen` | `e644589848feb83b6e18aac36a75c4c12fcc429e` |
| Newer reader and evidence polish awaiting reconciliation | `khoi/proofline-integrated-ux` | `9b5af9107e1ac39b4e735c978aceca1efa9401ba` |
| Earlier reader-layout source commits | `khoi/azure-ux-refinement` | `ed15a636445f37d7a8c8563b96f12f9bbc5727ff` |
| Frontend base already integrated | historical parent of the initial integration | `87eea1dc7e16fef0f21015b6ed1e81d39ffd6df3` |
| Standalone validated Hydrogen and frozen business history | `feat/business-translation-v1` | `928bdd3f364ef5f8ac4c3f0afdbf024f33f9773b` |
| Standard S2 review-recovery reference | `integration/azure-r2-candidate` | `40f185c98d55ab406e1b79aedbabcdb1e889da5f` |
| Existing Azure configuration reference | `deploy/azure-vm` and `integration/kpmg-blue-azure` | `a94eb4826348e32924c5d69f37c07018fb3870d0` |

Integration history is `877300cf044e798eee7966b83d4aacfe3b857d4a` (full app),
`36709f76c9a1dac27119bbc6f76c5ab4f6d336cf` (automatic orchestration), then
`e644589848feb83b6e18aac36a75c4c12fcc429e` (natural intent and caveat scope).
The integration already includes the approved Standard S2 behavior, the
four-tab frontend from `87eea1d`, and the validated Hydrogen adapter. The
latest reader polish remains separate. It descends from `877300c` and has
overlap in both `app.js` and `consult.css` copies, including Answer actions,
business presentation, research notes, and evidence/source reading.

## Application architecture

- `deploy/render/start.py` starts the verified staged server in real mode.
  The Azure service uses this same launcher. `experiments/render-staging/server.py`
  serves the frontend and same-origin API, requires local Basic authentication,
  and keeps state in a private SQLite directory. `onboarding/setup.py` and
  `experiments/render-staging/stage.py` create a hash-verified snapshot.
- Standard S2 uses the approved demo-100 index with pinned CPU encoder and
  reranker. Draft and review normally make two calls. Review retains accepted
  findings, exact citations, and applicable caveats. The accepted hosted
  recovery can withhold an uncited review limitation while preserving the
  cited answer. R2 experiments are outside this build.
- `/api/research` retrieves, drafts, reviews, saves, and returns research.
  For an explicit business question with sufficient context and accepted
  evidence, the response offers a downstream request. The browser renders
  research immediately and then invokes `/api/business` for that saved
  version. Academic questions still have a manual option.
- `src/business_demo.py` validates version, fingerprint, intent and context.
  `src/business_handoff.py` projects reviewed findings and exact quote bounds.
  `src/business_insights.py` translates, preserves relevant research caveats,
  records provenance and returns a new saved version. Citation IDs are
  restricted to the supplied accepted evidence. Duplicate same-version
  dispatches are guarded. Provider errors are isolated from the research result.
- Answer shows business status and results inline. Workspace holds context
  customization, alternative interpretations, notes and review. Sources
  and Evidence retain the existing reader and citation inspector. Business
  assumptions and caveats start collapsed. Regulatory assessment is separate.

## Provider configuration

| Stage | Configuration |
|---|---|
| Research | `RESEARCH_ENGINE=s2`, `S2_PAPER_BALANCE=0`, Gemini Developer API `gemini-3.1-flash-lite`, existing schema, provider settings and research quota |
| Business | Opt in with `BUSINESS_TRANSLATION_ENABLED=1`. `gemini-4-hydrogen` only, high thinking, temperature 0, JSON output, official Gemini Developer API endpoint |
| Business credential | `BUSINESS_TRANSLATION_API_KEY` from an approved dedicated project, distinct from `GOOGLE_API_KEY` |
| Prompt | `prompts/business_translation/downstream-v1.2.txt`, SHA-256 `2549eaacd15c6d1a26881cbdfe25898bf9ed22441f005283921e7c251d5634e8` |
| Business failure handling | 75 seconds per attempt, one retry after HTTP 503 with a 5-second delay, 170-second development proxy and 180-second browser budgets. Structural checks gate publication. No model fallback. |

Use an approved project and approved excerpts for live calls. Confirm project
billing and the authorized call budget before each live smoke test. Teammates
use their own approved credentials and secret stores. Windows DPAPI data is
tied to the account and machine that encrypted it. The source-machine
encrypted files stay on that machine.

## Checkout on another Windows computer

Requirements are Git, Python 3.11, and PowerShell 7. GitHub CLI is required
for the private asset-release route. Use a short path to avoid Windows limits.
From PowerShell:

~~~powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\src" | Out-Null
Set-Location "$env:USERPROFILE\src"
git clone https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation.git proofline
Set-Location proofline
git fetch origin integration/proofline-business-hydrogen feat/business-translation-v1 khoi/proofline-integrated-ux docs/proofline-windows-handoff
git switch --track origin/integration/proofline-business-hydrogen
git rev-parse HEAD
git show origin/docs/proofline-windows-handoff:docs/proofline-windows-handoff.md
~~~

Expected application HEAD is `e644589848feb83b6e18aac36a75c4c12fcc429e`.
For a checkout with the same app plus the updated README and environment
template, use `git switch --track origin/docs/proofline-windows-handoff`.
Create a new local development branch from the pinned integration commit
before reconciling frontend changes.

### Offline fixture for every teammate

~~~powershell
py -3.11 onboarding/setup.py setup --runtime native --fixture
py -3.11 onboarding/setup.py start --runtime native --fixture --engine s2
~~~

Open [Proofline localhost](http://127.0.0.1:8821/) as `reviewer` using the
local password printed at startup. Ask the printed fixture question.
The synthetic index and scripted generation exercise hosting without
API credentials or private corpus access. The standard fixture launcher
does not construct a business provider. The staged browser smoke runner
injects one for the orchestration checks below.

### Exact approved research assets for real mode

Keep these together in `.kpmg-onboarding/assets/demo-100/` when using
a previously cleared local copy:

- `parents.jsonl`, the evaluated passage text
- `views.json`, the paired search views
- `vectors.npy`, the paired CPU encoder vectors

The integration checkout supplies the index manifest and table audit, and
`onboarding/assets.json` specifies exact byte sizes and hashes. Setup fetches
and verifies the public pinned `all-MiniLM-L6-v2` encoder and
`ms-marco-MiniLM-L6-v2` reranker. Python libraries are pinned in
`onboarding/requirements-py311.lock.txt`. Node, Playwright and Chrome are
needed only for the browser runner. Downloads and caches remain local.

For distribution, ask the data owner or designated release maintainer for
the approved private `OWNER/REPO` and Read access to `s2-runtime-v1`
or a cleared copy of the existing exact files. Complete GitHub SSO if
required. Follow [the private publication handoff](../onboarding/PUBLISHING.md)
and the repository’s [portable setup guide](../onboarding/README.md).
This handoff publishes code and documentation only. Corpus clearance and
release availability depend on the data owner. Ordinary source reconstruction
has known limitations, including changes to versioned arXiv HTML and missing
legacy supplement extraction. Setup rejects a bundle whose bytes differ.

~~~powershell
gh auth login --hostname github.com --web
$assetRepo = Read-Host 'Approved private asset repository (OWNER/REPO)'
py -3.11 onboarding/setup.py setup --runtime native --asset-repo $assetRepo
~~~

If the exact files are already present in the onboarding cache, omit the
asset repository option. If asset access is pending, use the synthetic
fixture for local work.

### Start the real integrated application

Use the companion branch's [PowerShell environment template](../onboarding/proofline-local.ps1.example).
It sets non-secret defaults in the current process. From the pinned integration
checkout, save a local copy using the following commands:

~~~powershell
$localConfig = Join-Path $env:LOCALAPPDATA 'Proofline\local-env.ps1'
New-Item -ItemType Directory -Force (Split-Path $localConfig) | Out-Null
git show origin/docs/proofline-windows-handoff:onboarding/proofline-local.ps1.example |
    Set-Content -LiteralPath $localConfig -Encoding utf8
. $localConfig

# Set the research key from your approved local secret store or at this hidden prompt.
if (-not $env:GOOGLE_API_KEY) {
    $env:GOOGLE_API_KEY = Read-Host 'Approved research Gemini key' -MaskInput
}
$env:KPMG_GEMINI_DEDICATED_FREE = 'true'  # Set after verifying the project.
$env:KPMG_REVIEW_PASSWORD = Read-Host 'Local login password, 24+ printable ASCII characters' -MaskInput

# Optional Hydrogen opt-in, after authorization for the approved project and data.
$env:BUSINESS_TRANSLATION_ENABLED = '1'
if (-not $env:BUSINESS_TRANSLATION_API_KEY) {
    $env:BUSINESS_TRANSLATION_API_KEY = Read-Host 'Dedicated Hydrogen Gemini key' -MaskInput
}
$workspace = (Resolve-Path '.kpmg-onboarding').Path
$python = py -3.11 -c "import runpy,sys; from pathlib import Path; print(runpy.run_path('onboarding/setup.py')['native_python'](Path(sys.argv[1])))" $workspace
if (-not (Test-Path -LiteralPath $python)) { throw 'Run native real-mode setup first.' }
& $python -B deploy/render/start.py
~~~

Use a clean session without inherited provider endpoint or Vertex overrides.
Open [Proofline localhost](http://127.0.0.1:8821/) with user `reviewer` and the
chosen password. For research-only mode leave the template’s opt-in at `0`.
Stop the server with Ctrl+C and close the terminal to discard its session
credentials. The template keeps SQLite state outside the checkout.

### Offline checks to run before changes or a PR

After setup, use the same `$python` environment shown above. Install pytest
in that environment if needed. The clone must have fetched the standalone
Hydrogen branch because the nine recorded replay tests read its archived
research packets through Git.

~~~powershell
# If you installed only the offline fixture, resolve that environment instead:
# $fixture = (Resolve-Path '.kpmg-onboarding/fixture').Path
# $python = py -3.11 -c "import runpy,sys; from pathlib import Path; print(runpy.run_path('onboarding/setup.py')['native_python'](Path(sys.argv[1])))" $fixture
& $python -m pip install pytest
& $python -B -m pytest -q tests/test_business_hydrogen.py tests/test_downstream_business.py tests/test_business_downstream_http.py tests/test_indexed_research.py experiments/render-staging/test_deploy.py tests/test_research_demo.py tests/test_research_contracts.py tests/test_brief_store.py
~~~

For browser coverage, install Playwright in an approved local tools folder
or a global Node installation. Use the real staged demo-100 context and
a new empty state directory. The runner starts the app and injects scripted
providers. It generates desktop/mobile screenshots without provider calls.

~~~powershell
npm install --global playwright
$stage = (Get-Content .kpmg-onboarding/context.txt -Raw).Trim()
$state = Join-Path $env:TEMP ('pl-smoke-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $state | Out-Null
$playwright = Join-Path (npm root -g) 'playwright'
$chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
node experiments/render-staging/smoke.cjs $python $stage $state $playwright $chrome --business-intent
~~~

## What is validated and what remains

- `928bdd3` standalone Hydrogen passed 9/9 blind AI-assisted validation cases
  (5 development and 4 fresh), 108 offline tests and three live UI smoke
  scenarios (U6, F1 and U5). These are engineering results. Human stakeholder
  acceptance remains open.
- `877300c` integrated hosting passed 124 offline tests and 162 subtests,
  all nine archived Hydrogen replays, desktop Chromium, both baseline and
  S2 synthetic hosting checks, 48 frontend hashes and 68 staged hashes.
- `36709f7` passed 126 tests and 166 subtests plus staged desktop/mobile
  scripted browser checks. The bounded live browser run used four research
  calls and one Hydrogen call. Both accepted research outputs were saved.
  The original financial-services wording missed automatic intent, so it
  used zero Hydrogen calls. The logistics answer took 55.7 s research and
  16.0 s business after an earlier zero-call retrieval failure. Its three
  business citations pointed to accepted evidence, and business generation
  preserved research. The academic fixture dispatched zero business calls.
- `e644589` passed 128 tests and 180 subtests across runs, including all
  nine archived Hydrogen replays. An existing Windows HTTP test reset its
  socket in combined runs and passed in isolation. The original financial
  services question now derives the right sector and model-routing context.
  Replaying its existing saved answer through the automatic endpoint used
  one fixture business dispatch, no research dispatch and no live calls.
  Replaying the saved logistics handoff excluded the separately sourced
  SWRouter method limit while keeping the TravelPlanner findings, citations,
  applicable limits and original research record.
- The `e644589` corrections have offline verification. Live output after
  the intent/caveat correction, final frontend reconciliation and stakeholder
  UX acceptance remain open. Evidence can still be incomplete, as shown by
  the original financial-services answer’s due-diligence focus and limited
  support for routing savings or response quality. The earlier logistics
  retrieval failure remains undiagnosed. The current parser is deterministic
  and leaves ambiguous questions optional.

## Evaluation record and private archives

Fetch `feat/business-translation-v1` to access the original
[Hydrogen handoff](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/blob/928bdd3f364ef5f8ac4c3f0afdbf024f33f9773b/docs/business-translation-hydrogen.md)
and
[historical v1.2 handoff](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/blob/928bdd3f364ef5f8ac4c3f0afdbf024f33f9773b/docs/business-translation-final-handoff.md).
The frozen case manifests and rubrics are in `business-evaluation/v1/` and
`business-evaluation/v1.2-validation/`. Historical implementation pins are
`82702dc5436c8f5b41bdcd8df3bfa0422403ce22` and
`870ba4991a2ac9f5b58d6627e2da3141a3e6af2b`. Historical manifests are
`90ce47ca0033221b44b2de4ef728bbde1efbe47e` and
`1eeb869a6714fa018fc69534605dbe474710c955`. Use their matching adapter
commits to replay those historical protocols.

Historical baseline and heuristic v1.1/v1.2 results remain separate from the
Hydrogen configuration. The archived v1.2 final availability was 3/11 known
and 1/5 fresh, with 12 avoidable withholding cases in the 16 new outputs.
The historical report preserves the comparator scores, losses, and distinctions
between generation errors and heuristic withholding. There is no human
acceptance claim.

On the original computer, historical score sheets, raw responses, source
PDFs and adjudications stay in the local operator archive
`data/processed/business-translation-archive/` in the primary checkout.
Its manifest SHA-256 is
`2ee09bdf54aeb8900340d13b96f0a5ddf33858be864815295bd226f8b8f83e95`.
Hydrogen diagnostic materials are under
`evaluation/business-translation-capability-diagnostic/` there.
Live smoke receipts and screenshots stay in the integration checkout's
`.kpmg-onboarding/36709f7-verification/` directory. Use the approved
private transfer process if an authorized teammate needs those raw files.
The GitHub handoff retains shareable summaries, frozen inputs and replay
fixtures. API keys, encrypted secrets, private state and generated snapshots
stay outside Git.

## Resume order for Claude

1. Clone and pin the integration commit and fetch the reader and standalone
   branches. Run the offline fixture and targeted suite before editing.
2. Create a reconciliation branch from `e644589`. Compare the reader changes
   using `git diff 877300c..origin/khoi/proofline-integrated-ux -- ui-consult onboarding/frontend`.
   Preserve the inline business section after findings, separate status,
   pending and duplicate-request guard, and `demo.business_auto` dispatch.
   Port the newer typography, table-cell inspector, source labels, and
   research verification disclosures into both frontend copies.
3. Regenerate the frontend asset hashes and staging pins together. Exercise the
   local and staged browser runners for academic, eligible business,
   failure, citations, saved versions, and responsive layout. Check the
   exact financial-services wording using its saved research and fixture
   dispatch so verification can avoid a research rerun.
4. Review the reconciled app with the team. Any further live verification
   needs an explicit budget and approved credentials. Azure deployment
   and a main-branch merge are separate decisions.

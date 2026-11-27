# Run Proofline with Hydrogen locally

The full preview serves the staged frontend and API used by the Azure launcher.
Run these commands from the integration worktree with Python 3.11. Use a short
checkout path if Windows reports a path-length error.

## Stage the full app

Use the authorized private asset release or an existing exact demo-100 onboarding
cache. Omit the asset release setting when the full bundle is cached.

    $env:KPMG_ASSET_REPO = Read-Host 'Approved private asset repository (OWNER/REPO)'
    py -3.11 onboarding/setup.py setup --runtime native

Setup verifies the research bundle and approved frontend, then records the staged
path in .kpmg-onboarding/context.txt. The synthetic fixture mode exercises hosting
without a model provider.

## Launch the full app for an authorized local smoke test

In PowerShell 7, use separate keys from approved local research and business
projects. The business project must have access to Gemini 4 Hydrogen.

    $env:KPMG_DEPLOY_MODE = 'real'
    $env:RESEARCH_ENGINE = 's2'
    $env:S2_PAPER_BALANCE = '0'
    $env:KPMG_ORIGIN = 'http://127.0.0.1:8821'
    $env:PORT = '8821'
    $env:KPMG_GEMINI_DEDICATED_FREE = 'true'
    $env:KPMG_STATE_DIR = Join-Path $env:TEMP ('proofline-' + [guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path $env:KPMG_STATE_DIR | Out-Null
    $env:KPMG_REVIEW_PASSWORD = Read-Host 'Local password (24+ printable ASCII characters)' -MaskInput
    $env:GOOGLE_API_KEY = Read-Host 'Dedicated research project key' -MaskInput
    $env:BUSINESS_TRANSLATION_ENABLED = '1'
    $env:BUSINESS_TRANSLATION_API_KEY = Read-Host 'Dedicated Hydrogen business project key' -MaskInput
    $workspace = (Resolve-Path '.kpmg-onboarding').Path
    $python = py -3.11 -c "import runpy,sys; from pathlib import Path; print(runpy.run_path('onboarding/setup.py')['native_python'](Path(sys.argv[1])))" $workspace
    & $python -B deploy/render/start.py

Use a shell without Gemini endpoint, Vertex, or alternate model overrides. Stop the
server with Ctrl+C and remove the keys from the session when finished.

1. Open [Proofline](http://127.0.0.1:8821/) and sign in as **reviewer**.
2. Ask an applied question supported by the approved index, or open a compatible saved
   answer. To use an existing brief library, point KPMG_STATE_DIR at a private copy of
   its state directory before launching.
3. In **Answer**, click **Generate business insights**. You can supply **Industry**,
   **Business Workflow**, or **Decision** under **Workspace → Business insight →
   Customize**. If the workflow cannot be inferred from the original question, Proofline
   opens Customize before making a business call.
4. Review the business citation and check the original research and the new saved
   version. Use public research and non-confidential context for the dedicated
   free-tier business provider.

The application starts in research-only mode when BUSINESS_TRANSLATION_ENABLED is
unset. A future hosted opt-in requires the explicit enable flag, a dedicated
Hydrogen key in the private environment file, and a fresh verified snapshot.

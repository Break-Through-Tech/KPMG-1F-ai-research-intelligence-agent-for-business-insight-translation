# Access and test the private research-QA adapter

## What this is

- Private Hub repository: https://huggingface.co/jjjhenriksen/Qwen3.5-9B-MLX-research-qa-lora-experimental
- Adapter revision: `e674eed689f6b3f86b88059ba16b6f8dad47d951`
- Base: `mlx-community/Qwen3.5-9B-4bit`
- Base revision: `8b2b98c00a6b4d291155e4890773ca8f769aee53`
- Format: **MLX LoRA adapter**, rank 16, selected epoch 2. Not standalone
  weights, not a fused model, and not a Transformers/PEFT adapter.

This is an experimental archive, **not an accepted production model**. Uploading
it did not change the application default or merge anything into the base weights.
The GitHub repository contains instructions, not private weights or access tokens.

## 1. Prerequisites and private access

Use an Apple Silicon Mac with sufficient available unified memory. The retained
run used a 14 GiB MLX peak-memory gate; that is not a guarantee that a 14 GiB machine
has enough total memory. Downloads require several GB of disk and network traffic.
No paid hosted inference endpoint is required.

The owner must grant collaborators access to the private model repository; a link
alone does not grant access. Authenticate locally with an account that has access:

```sh
hf auth login
hf auth whoami
```

If a token is requested, create one at https://huggingface.co/settings/tokens
with read access to this private model. Enter it interactively; do not paste it
into Git, scripts, issues, or chat. Read access is sufficient for downloads/testing.
A `401`, `403`, or private-repository `404` usually calls for checking the signed-in
account and repository permissions, not making the model public.

From the Git repository root, create a separate MLX environment (the project's
CPU/judge `.venv` may not include MLX):

```sh
python3 -m venv .venv-mlx-adapter
source .venv-mlx-adapter/bin/activate
python -m pip install 'mlx==0.32.0' 'mlx-lm==0.31.3' 'transformers==5.15.0' huggingface_hub
python -m mlx_lm generate --help
```

These are the recorded training versions, not a newly tested clean-install lock.
On Jacqueline's existing Mac the working MLX interpreter is
`/Users/jacquelinehenriksen/.openclaw/venvs/mlx-dspark/bin/python`.
Do not commit this environment or downloaded checkpoints.

## 2. Download immutable snapshots and verify the adapter

Run in that environment. Files stay in the Hugging Face cache, outside the Git tree:

```sh
python - <<'PYCODE'
import hashlib, json
from pathlib import Path
from huggingface_hub import snapshot_download
adapter = Path(snapshot_download(
    "jjjhenriksen/Qwen3.5-9B-MLX-research-qa-lora-experimental",
    revision="e674eed689f6b3f86b88059ba16b6f8dad47d951"))
base = snapshot_download("mlx-community/Qwen3.5-9B-4bit",
    revision="8b2b98c00a6b4d291155e4890773ca8f769aee53")
manifest = json.loads((adapter / "provenance.json").read_text())
for name, expected in manifest["files"].items():
    actual = hashlib.sha256((adapter / name).read_bytes()).hexdigest()
    assert actual == expected, f"Checksum mismatch: {name}"
print("BASE:", base)
print("ADAPTER:", adapter)
print("Checksums verified")
PYCODE
```

Copy the printed snapshot paths into the next section. Do not substitute a moving
`main` revision when comparing results.

## 3. Run a baseline/adapter smoke comparison

Replace the two paths below with the printed paths. Run the arms sequentially,
with identical evidence, prompt, decoding settings and token limit:

```sh
BASE='/absolute/path/printed/for/base'
ADAPTER='/absolute/path/printed/for/adapter'
SYSTEM='Answer only from the supplied evidence. Cite supported claims using exact bracketed chunk IDs. Preserve all conditions and qualifiers. Answer supported portions and identify precisely what remains unknown. Absence of evidence is not evidence that a claim is false.'
PROMPT='{"question":"Does repeated window processing establish reporting within one minute?","evidence":[{"chunk_id":"hsmoke001","text":"The system repeatedly processes the next time window. Window duration and end-to-end reporting latency were not measured."}]}'

python -m mlx_lm generate --model "$BASE" \
  --system-prompt "$SYSTEM" --prompt "$PROMPT" \
  --temp 0 --seed 47139 --max-tokens 384

python -m mlx_lm generate --model "$BASE" --adapter-path "$ADAPTER" \
  --system-prompt "$SYSTEM" --prompt "$PROMPT" \
  --temp 0 --seed 47139 --max-tokens 384
```

Expected behavior, **not a promised model output**: acknowledge repeated processing,
cite `[hsmoke001]`, and explain that a one-minute bound is not established without
window-duration/reporting-latency measurements. Do not claim the system cannot
meet one minute, or that the passages contain no information about windows.

Also try a supported factual question, an empty evidence list, and a numeric
comparison with both values supplied. Check citations, units, qualifiers and the
exact evidence gap. Reaching 384 tokens means the answer may be truncated; do not
silently count a truncated answer as a pass. Record both outputs and settings.
These are manual smoke checks, not a new judging or labeling assignment.

This standalone prompt is deliberately illustrative. It does **not** reproduce the
frozen benchmark's full message construction, data release, or scoring policy.
Do not compare its outputs directly to the historical pass counts or treat one
successful answer as acceptance. No retraining, fresh semantic-judge calls, final-
test access, deployment, or paid service is required by these instructions.

## 4. Read the retained evaluation

`evaluation.json` and `provenance.json` in the downloaded adapter snapshot include
aggregate results, gate decisions, file hashes, base revision and training settings.
No training dataset, raw evidence queue, optimizer state or base weights were uploaded.

On November 10, 2026, 144 saved answers across both arms were each AI-reviewed twice:

| Check | Untuned | Adapter |
| --- | ---: | ---: |
| Development | 4/48 | 33/48 |
| No-evidence probes | 8/8 | 8/8 |
| Numeric probes | 13/16 | 16/16 |
| Partial-evidence development cases | 1/10 | 0/10 |

The adapter **failed answerability-status nonregression**, despite its aggregate
improvement. These are development-only AI judgments; the final test remained
sealed. Known weaknesses include dropped qualifiers, unsupported negative
conclusions, missing citations, and incomplete descriptions of missing evidence.
No overall acceptance or production-readiness claim is warranted.

## Troubleshooting and verification boundary

- `No module named mlx_lm`: activate the MLX environment, not the CPU/judge one.
- MLX/Metal load errors: confirm Apple Silicon and available memory. This adapter
  is not directly loadable as PEFT in standard Transformers or on a CUDA server.
- Invalid adapter keys: verify the exact base revision and recorded MLX versions;
  do not fuse or convert the adapter as a workaround without separate validation.
- Generic/no citations: inspect the provided evidence IDs and actual output; this
  is a known quality risk, not necessarily an installation failure.

The upload was verified private and its adapter SHA-256 matched the local selected
checkpoint. The installed MLX CLI flags were checked when writing this guide.
A fresh environment install and the illustrative inference commands have **not**
been executed as part of this documentation change.

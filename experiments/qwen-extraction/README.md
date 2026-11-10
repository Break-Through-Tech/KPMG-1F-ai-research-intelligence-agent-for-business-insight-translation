# Extraction-first Qwen pilot

## Private Hugging Face adapter

See [access and testing instructions](HUGGING-FACE-ADAPTER.md) for the pinned
experimental MLX adapter, private authentication, baseline comparison, and known
acceptance failures. This is not a production-default promotion.

Local work on `fine-tuning-experiments`, October 28, 2026. No application routing,
provider, approval fields, upstream pilot artifacts or base weights were changed.
**LLM judges only.** Neither Jacqueline nor teammates have a judging, labeling,
calibration or experiment-approval queue.

## Completed

- Read the morning evaluation post from dashboard
  `239892dc-c838-47b6-9e5c-120ebc2e0f24` and imported its revised experiment
  protocol into `docs/answer-quality-experiments.md`.
- Selected **17 training and 3 development extraction targets** from the retained
  PDF pilot. Checked PDF hashes, every supplied chunk against its cited cleaned
  page, and contiguous quotation membership. Targets have explicit AI review
  rationales in `targets.json`; they are examples, not exhaustive answer keys.
- All **20/20 targets passed first-pass LLM judging**. The three training targets
  used for the smoke also passed a separate-context LLM review. Six synthetic
  classifier anchors were judged correctly in both evaluation runs. These anchors
  are a sanity check, not statistically calibrated TPR/TNR.
- Ran untuned 9B and 27B sequentially on identical frozen evidence: **3 real-source
  dev cases × 2 attempts × 2 models = 12 attempts**. No provider errors, silent
  retries, truncated inputs or observed output-budget exhaustion.
- Ran blinded binary rubric scoring, three pairwise comparisons in **both orders**,
  and a third-context LLM adjudication for the order-inconsistent case. Critiques,
  raw prompts, raw answers, schema-validated verdicts and usage receipts remain
  inspectable under ignored `artifacts/`.
- Completed **three actual LoRA optimizer updates** on local 4-bit 9B weights:
  rank 4, q/v projections of the last full-attention block, **69,632 trainable
  parameters**, batch 1, assistant-only loss, no truncation. All gradients/losses
  were finite; adapter weights changed, saved and reloaded exactly, and a reloaded
  forward loss was finite. Base weight shard hashes match before/after.

## Evaluation result

| Model | Pointwise passes before adjudication | Final confirmed passes | Inconclusive attempts | p50 generation | MLX peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Untuned 9B | 2/6 | 0/6 | 2/6 | 5.66 s | 5.95 GiB |
| Untuned 27B | 0/6 | 0/6 | 0/6 | 20.73 s | 16.15 GiB |

The other attempts failed the declared rubric. Both repeats used temperature
zero; they produced identical answers and are **not independent source cases**.
Two pairwise cases were order-consistent ties; the remaining case flipped its
preferred model when order was swapped, so it was not counted as a win.

**What failed:** both models sometimes chose a result or artifact description
instead of a method. The 27B selected substantive method statements on two cases
but repaired PDF line-break hyphenation, violating the predeclared literal-quote
rule. Such failures are **not factual hallucinations**. The 9B's apparent passing
case quoted a definition of motivated reasoning, exposing ambiguity in whether
the rubric's word “mechanism” includes the phenomenon being studied. A third LLM
review marked this uncertain; its two identical repeats are not counted as
confirmed successes. Raw pointwise scores are preserved, not retroactively erased.

Three source families are too few to establish a quality winner, confidence in
generalization or a tuned-model selection gate. No final-test tasks were opened,
generated or evaluated. Generation-time cost per confirmed success is undefined
because there were zero confirmed successes; load, judge and training costs are
recorded separately. No GPU purchase or API-key generation route was used.

System swap rose from approximately 1.3 GiB during 9B inference to roughly
7.6–7.9 GiB during 27B inference. MLX allocation is not total system memory;
these sequential observations do not isolate all other system activity and do
not establish comfortable 27B operation.

## What the training smoke proves—and does not

Checkpoint: `artifacts/lora-smoke-v1/adapter/adapters.safetensors`, SHA-256
`c8d3c076b5a83c21fc980bab4570b736e16aa5852c2297945f46c109939befc4`.
Full step/gradient/memory and before/after base-weight receipts:
`artifacts/lora-smoke-v1/smoke.json`.

The smoke uses only the selected quotation as short supplied evidence from three
training-family examples. That makes it a deliberately easy load/loss/gradient/
checkpoint compatibility check, **not a meaningful extraction training run or a
tuned quality candidate**. Losses from different examples are not a learning
curve. The final full-attention block trains while frozen recurrent layers stay
in inference mode. Broader/recurrent-layer LoRA, full-model training, longer
contexts and production integration remain unverified. Nothing was fused into
the base model or configured as an application default.

## Inspectable files

- `protocol.json`: current LLM-only protocol; archived v1 is retained locally.
- `targets.json`: curated source selectors and AI rationale.
- `results.json`: compact result/metric record and raw-artifact hashes.
- `artifacts/prepared-v1/`: frozen source-checked cases and pilot provenance.
- `artifacts/accepted-extraction.{train,dev}.jsonl`: derivative LLM-review labels,
  with no human-review requirement; only three double-reviewed training targets
  are enabled for compatibility smoke. Frozen preparation files are unchanged.
- `artifacts/{target-judge-v1,baseline-judge-v2,adjudication-v1}/`: judge evidence.
- `artifacts/baseline-{9b,27b}-v1/`: full retained generation attempts.
- `artifacts/executed-source/`: executed preparation/training/evaluation source
  snapshots, verified against their recorded hashes. Later terminology cleanup
  does not rewrite historical receipts; historical references to human review
  are superseded by the explicit LLM-only policy.

Raw source excerpts, local paths, generated outputs and model adapters are
ignored rather than added to Git. Runtime weights remain outside the repository.
The original pilot in sibling worktree `nova-crab` was read only, not altered.

## Reproduce

Run from the repository root. Use installed local weights only, and choose new
output directories rather than overwriting retained artifacts. MLX inference
and training must run sequentially. The baseline model card's upstream 27B
lineage remains unverified; the 9B snapshot is explicitly pinned below.

```sh
# Source/PDF checks use the original ingestion environment, without re-ingestion.
PILOT=/Users/jacquelinehenriksen/.openclaw/worktrees/605009bc321d9ef6/nova-crab
"$PILOT/.venv/bin/python" experiments/qwen-extraction/prepare.py --pilot "$PILOT"

# Reuse the existing MLX environment, not the lightweight judge environment.
MLX_PY=/Users/jacquelinehenriksen/.openclaw/venvs/mlx-dspark/bin/python
MODEL_9B=/Users/jacquelinehenriksen/.cache/huggingface/hub/models--mlx-community--Qwen3.5-9B-4bit/snapshots/8b2b98c00a6b4d291155e4890773ca8f769aee53
"$MLX_PY" experiments/qwen-extraction/run_extraction.py \
  --model "$MODEL_9B" --label untuned-9b \
  --output experiments/qwen-extraction/artifacts/baseline-9b-v2
"$MLX_PY" experiments/qwen-extraction/run_extraction.py \
  --model /Users/jacquelinehenriksen/.openclaw/models/Qwen3.8-27B-4bit \
  --label untuned-27b --output experiments/qwen-extraction/artifacts/baseline-27b-v2

# Python 3.12, jsonschema; existing ChatGPT login, no credential copying.
python3.12 -m venv .venv
.venv/bin/pip install -r experiments/qwen-extraction/requirements-judge.lock.txt
CODEX_BIN='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
.venv/bin/python experiments/qwen-extraction/evaluate.py \
  --targets --historical --codex-bin "$CODEX_BIN" \
  --output experiments/qwen-extraction/artifacts/target-judge-v2
.venv/bin/python experiments/qwen-extraction/evaluate.py \
  --runs experiments/qwen-extraction/artifacts/baseline-9b-v2/run.json \
         experiments/qwen-extraction/artifacts/baseline-27b-v2/run.json \
  --pairwise --review-sample 3 --shuffle-seed 54917 --codex-bin "$CODEX_BIN" \
  --output experiments/qwen-extraction/artifacts/baseline-judge-v3
.venv/bin/python experiments/qwen-extraction/adjudicate.py \
  --evaluation experiments/qwen-extraction/artifacts/baseline-judge-v3/evaluation.json \
  --codex-bin "$CODEX_BIN" --output experiments/qwen-extraction/artifacts/adjudication-v2
"$MLX_PY" experiments/qwen-extraction/smoke_lora.py \
  --model "$MODEL_9B" \
  --target-review experiments/qwen-extraction/artifacts/target-judge-v2/evaluation.json \
  --second-review experiments/qwen-extraction/artifacts/baseline-judge-v3/evaluation.json \
  --output experiments/qwen-extraction/artifacts/lora-smoke-v2

# Offline regression checks; no models or credentials.
.venv/bin/python -m unittest discover -s experiments/qwen-extraction -p 'test_*.py' -v
```

Fresh checkouts require the retained pilot PDFs/queues, local MLX environment and
cached model weights; scripts do not silently download replacements. The source
check command's default output is immutable `prepared-v1`, so skip it if that
verified directory is already present. `report.py` freezes the initial v1/v2
artifact set; it is not a generic automatic model-selection runner.

## Next experiment

Version a clearer research-procedure versus phenomenon-definition rubric and
rejudge the existing development artifacts without regenerating answers. Then
run a prompt-only control on identical evidence. Expand LLM-reviewed task and
source-family coverage before meaningful SFT; freeze a sufficiently sized
development comparison and numerical selection thresholds before final test.
All these reviews remain **LLM-only**. No team human judging is requested.

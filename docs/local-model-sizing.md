# Choosing a local generation model

## No parameter-count ceiling in the provider

The `openai_compatible` provider has **no hard minimum or maximum model size**.
`RESEARCH_MODEL` names a model served by the selected endpoint; the application
does not load its weights or inspect its parameter count. The practical limits
are available memory, runtime support, context capacity, latency, and whether
the model can follow the research-summary contract.

Three different checks matter:

1. **Loads:** the runtime can serve the model within available memory.
2. **Operates:** it handles Chat Completions, the JSON-object request and
   temperature zero, and returns a response within the client timeout.
3. **Meets the task contract:** it returns correctly shaped summaries with
   citations copied from supplied passages, or a valid evidence abstention.

Passing the first two does not establish the third. Even all three do not
establish semantic support, human quality scores or stakeholder approval.

## Memory: weights are only the starting point

For a dense model, idealized weight storage is:

`parameters × bits per weight ÷ 8`

The table uses decimal GB and nominal parameter counts. These are **weight-only
arithmetic estimates**, not measured downloads, total RAM requirements or a
hardware compatibility chart. Quantization metadata, unquantized tensors and
runtime representations can increase the actual size.

| Nominal model | Ideal 4-bit weights | Ideal FP16 weights | How to use the size class |
|---|---:|---:|---|
| 1B | 0.5 GB | 2 GB | Cheap transport/failure-path candidate; not a certified summary baseline |
| 3B | 1.5 GB | 6 GB | Another small candidate; must pass the same checks |
| 8B | 4 GB | 16 GB | A reasonable next instruction-model candidate, not a verified minimum |
| 14B | 7 GB | 28 GB | Larger candidate if memory and latency permit |
| 32B | 16 GB | 64 GB | Substantial memory demand; not required by the provider |
| 70B | 35 GB | 140 GB | Much heavier; not an application-imposed ceiling |

Total working memory additionally includes the KV cache, prompt-processing
buffers, inference runtime, the retrieval embedding model, OS and other apps.
Longer contexts and concurrent requests increase demand. On Apple Silicon,
GPU/CPU share unified memory: do not count RAM and GPU memory as two independent
pools. On a discrete GPU, insufficient VRAM may cause CPU offload or refusal;
offload can make a model fit but too slow for the current client timeout.

Compare available memory with the runtime's **actual model size and working
memory**, not only the table. Leave headroom rather than filling memory to its
advertised capacity. More parameters alone do not guarantee better instruction
following; model family, instruction tuning and quantization also matter.

## Context and latency for this pipeline

The default summarizer bounds its evidence section to **12,000 characters**
and each passage's text to **2,500 characters**. These are character limits,
not token limits, and do not cap the entire request. The query, instructions,
metadata and generated JSON also need room in the runtime's active context.

Measure tokens with the selected model's tokenizer and reserve output space.
A model's advertised maximum context is not necessarily the runtime's active
context setting, nor proof that long-context inference fits available memory.
Do not silently truncate away source IDs or weaken citation checks to fit.

The existing compatible-provider client uses a **60-second SDK timeout** with
no automatic inference retry or provider fallback. Cold loading, long prompts
or slow offload can cause generation failures even when weights fit. This is
not a parameter-count limit or a guaranteed total wall-clock deadline. Test
the actual request on the actual hardware; the application currently exposes
no model-size policy or timeout override for this workflow.

## Measured result, not a universal size rule

On October 13, 2026, the local Ollama `llama3.2:1b` tag reported **1.2B
parameters, Q8_0, and 1,321,098,329 stored bytes** (about 1.32 decimal GB).
This is not the hypothetical 1B/4-bit row above, and it is not measured RAM use.

- A real call through the BYOK factory returned the requested simple
  `{"status":"ok"}` object: local transport/JSON operation worked.
- The ten-question real retrieval/summary run accepted **zero summaries**:
  four malformed responses and six generation failures. For example,
  `chunk_ids` was emitted as a string instead of an array.
- A single Qwen 3 1.7B diagnostic also failed the summary shape by emitting
  uncited string claims. It was not a full comparative model evaluation.

Those observations apply to the tested model digests, prompt, runtime and
request settings. They do **not** prove that every 1B model fails or that any
particular larger model will pass. Generation failures are not automatically
diagnosed as lack of memory or insufficient parameter count.

## Selection recommendation and acceptance

For the next candidate, try a **JSON-capable instruction/chat model around
7–8B**, quantized to fit with memory headroom. This is an engineering starting
point, not a measured recommendation or an enforced lower bound. An appropriately
trained smaller model may pass; an unsuitable larger model may fail.

Current requests use `response_format=json_object`, **not a strict JSON schema**.
Schema-constrained decoding is possible future work, not an implemented switch
in this client, and would still not establish factual support.

Use the [local-model E2E commands](local-model-e2e.md), then the unchanged ten
benchmark questions. Record the exact model digest/quantization, runtime,
hardware, active context and concurrency settings, prompt hash and frozen
corpus/index identity. Inspect execution failures, malformed responses, invalid
citations and genuine abstentions separately. Never promote a model solely
because it loads, returns valid JSON, or has more parameters.

All generated results remain `approved=false`; actual source support and quality
evaluation still require the human review protocol.

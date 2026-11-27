# Fresh Multi-Agent diagnostic evaluation

This is a development-only diagnostic, with one Multi-Agent run per question. It does not compare architectures or reuse the locked 20-question scores. Nothing in this directory submits model requests on its own.

## Frozen materials

- questions.json has the only inputs the provider path is allowed to receive from the evaluation set.
- references.json contains 22 required points, exact original DOM locators and source text, versioned chunk IDs, original HTML hashes, and source links. Source review used the hash-matched original local HTML. An assistant checked the references against the sources. There is no independent human sign-off.
- cases.json is the pre-execution authoring record. Rules and configuration are in rules.json and config.json.
- seal.json pins the evaluation inputs, implementation files, demo-100 index artifacts, model files, and CLI binary. The offline retrieval outputs were generated after freezing the questions and are not a tuning input.
- Locked exclusions were based on paper identifiers only. No locked questions or expected points were used for design. Previously debugged paper IDs were excluded and 21 accessible prior development questions were checked for wording overlap. This establishes no overlap with the locked paper metadata and accessible development materials. It cannot guarantee originality against unrecorded questions.

The effective synthesis packet is always the evidence captured from the real provider boundary. Matching an exact anchor in the original-query offline lookup is not a final evidence sufficiency judgment. Independently checked equivalent evidence may be credited during adjudication with an explicit note, without changing the frozen references.

## Offline commands

From the checkout root, use the existing application Python environment:

```powershell
python -B -m unittest discover -s experiments/measure/fresh-diagnostic-v1 -v
```

For local retrieval, set HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE to 1 and run preflight.py in this directory. Its output is write-once. To verify the seal with an existing offline output, import preflight.verify without running the script entry point. prepare.py is a write-once freezer and is not part of live execution.

## Live execution plan pending approval

1. Reverify the seal and the CLI, cached model listing, ChatGPT login status and local-only retrieval identity. Abort on any mismatch. Never use a billed API, another provider, or a fallback model. Load the current B2 table-comparison configuration using existing encoder and reranker assets on CPU with four threads. Use eight results per query and the current 14-passage merged synthesis cap.
2. Create a new isolated write-once run directory outside the shared demo. Schedule the ten distinct IDs in questions.json in their recorded order. Verify the schedule has exactly those IDs and use a single serial coordinator. Pass only that file's ID and question to the capture path. No provider-facing process reads references.json. Initialize a new in-memory CLI receipt list for this run. Do not open the historical ledger. The capture wrapper reserves one directory per question and persists an attempt before delegating. Its five ordered slots enforce at most five invocations in a question. Ten reserved IDs give a maximum of 50 invocations. Record failed attempts and block reuse of consumed slots or question directories.
3. Use the existing Codex subscription adapter with gpt-6.1-sol, low effort, 300-second timeout, text-only isolation and the existing wire schemas. Run current research-only Multi-Agent with business, chart and numerical shadow off. Initial flow is plan, synthesis, verification. The workflow may skip verification when synthesis abstains. Permit its single existing verifier-requested targeted pass only when new evidence reaches synthesis. This can add one synthesis and one verification invocation. Budget about 30 invocations if all ten use one round, up to 50 if all use the second round. No provider retries at the application level and no question reruns. The cap does not meter internal CLI requests.
4. Use capture.run_question with the approved provider callback only after approval. Save searches and timings, actual evidence for every synthesis round, raw structured replies, verifier and publication traces, final envelopes, per-stage elapsed time and CLI receipts. The outer coordinator must stop on an integrity violation, missing invocation receipt, authentication or model-access failure, quota/rate limit, or provider configuration failure. Report remaining IDs as unrun. A non-systemic failure consumes its slot and may leave a case unscorable. Results and original attempts are never overwritten.
5. After generation stops, use frozen references and rules to adjudicate citation entailment and point coverage from the original evidence. Project each selected-round result into the existing trace diagnostic's anchor/draft/final inputs. Use per-round capture for omissions and selection losses. Score caveats and limitations explicitly from the final envelope and its cited limitations, since the existing trace diagnostic alone does not assess them. Preserve execution errors and unresolved adjudications. Report per-case and aggregate outcomes, historical versus new latency where relevant, counts of provider calls and token usage when available. No follow-up requests or tuning.

Live orchestration remains approval-gated. The offline capture test passes an injected scripted provider through the real OrchestratorAgent and envelope. No approved live callback has been attached.

# Source-grounded quotes (opt-in, offline-validated)

Status: implemented and tested offline only. No live generation was made. Off by default. Not wired into any UI or backend.

## Confirmed root cause

The false abstentions in the simplified-v2 Gemini comparison (`data/processed/gemini-handoff-paired-v2-simplified`) come from **elided quotes**. Neither wrong citations nor unsupported statements caused them. Each case was checked against its saved draft and packet:

| Draft | Rejected quote | In the source? | Claim supported? |
|---|---|---|---|
| F03 current | `Dataset: Cora ( … ); ... Splitting: Random` (and the Arxiv row) | Both pieces are verbatim, in order, in the correctly cited table row | Yes: Cora random, Arxiv time |
| F01 current | `…notably improves the accuracy rate. . . This improvement underscores…` (c0017) | Both sentences are verbatim and adjacent, with one sentence elided | It is an interpretation. The verifier must judge it |
| F01 handoff | Same pattern in c0017 | Same | Same |

In every case, the other claims in the draft carried exact table-row quotes that answered all required points. One elided quote raised `ValueError` in `attach_validated_citations` (`src/research_chat.py:84`), which `synthesize` (`src/research_chat.py:170`) propagates. `ResearchAgent.run` (`experiments/agentic/agents.py`) then turns it into a whole-draft rejection, so the run abstains. The per-claim verifier never ran.

Exact matching is not too strict: the model's text was verbatim. The failures come from all-or-nothing rejection plus the model's habit of eliding text inside table rows.

A secondary finding, pre-existing in the handoff arm: when a second-round draft is rejected, the first round's verified claim is discarded too, and the run abstains (see `MultiRound` in the tests).

## Change

`experiments/agentic/quote_grounding.py` sits between the synthesis model and the **unchanged** validator:

- A quote already in its cited passage is kept byte for byte. A draft with no change is passed through untouched.
- An elided quote (`...`, `. . .`, `…`, or a sentence period followed by `...`) whose pieces of 15 or more characters occur in order in the cited passage is replaced by the **contiguous source span**. The span runs from the first piece to the last, with a maximum of 1,200 characters, the schema's limit. The elided words are restored, so nothing is hidden from the reviewer, the number checks or the verifier.
- Any other unlocatable quote (paraphrase, invented text, unknown or wrong chunk ID) drops **only that claim or limitation**. If no claim survives, the status becomes `insufficient_evidence`, which still needs a cited limitation or synthesis rejects it.
- Wrong IDs are not re-cited to another passage. A first version did this, and self-review removed it: a claim quoting the wrong row would pass the number check with only the model verifier left to catch it.
- Malformed or non-JSON replies pass through, so the existing schema checks still fail closed.
- The trusted text is read from the `paper_passages` in the synthesis prompt itself, which is exactly the evidence the model saw.

Enable it on a constructed engine with `quote_grounding.enable(engine)`. This works for `OrchestratorAgent` and `EvidenceHandoffOrchestrator`. The research reply in the trace gains `quote_grounding` notes (`restored_elided_text` / `dropped` with a reason). No existing file was edited: `current-multi-agent.json` still verifies, so `gemini_paired.py` and the frozen comparator are unaffected.

Kept unchanged: the prompt, the schemas (including automated reviewer’s simplified Gemini wire schema), exact-quote membership, `ground_claim` number and qualifier checks, the independent verifier, the gate and the envelope.

## Offline before/after (identical recorded drafts and packets, no provider)

`py -3.14 -B experiments/agentic-handoff/replay_quote_grounding.py`

| Recorded draft | Before | After (synthesis + deterministic checks) |
|---|---|---|
| F01 current | rejected → abstention | 4 claims pass. Required counts (42 / 72) and Gemma scores (0% → 66.7%, 5.6% → 69.4%) present |
| F01 handoff | rejected → abstention | 4 claims pass, same required points |
| F02 current / handoff | 2 complete claims | byte-identical, no grounding notes |
| F03 current | rejected → abstention | 2 claims pass. 2,708 / 16,316 nodes; Cora random, Arxiv time |
| F03 handoff | provider timeout, no draft | n/a |

"After" means the claims reach the verifier. It does **not** mean they would be published. These drafts never got a live verifier verdict. These are replays of recorded output, not live accuracy.

## Tests

`experiments/agentic/test_quote_grounding.py` holds 22 development cases from verbatim F01/F03 passages, separate from the frozen F01–F10 references. It covers:

- valid exact quotes
- elided table cells and prose
- paraphrase
- invented quotes
- unknown and wrong IDs
- conflicting sources
- numerical contradiction (still held by `ground_claim`)
- partial answers
- two-round handoff
- malformed replies
- overlong and out-of-order elisions
- the recorded-run replay

Full agentic suite: 238 passed, 1 skipped.

```powershell
$env:PYTHONPATH='.;experiments/agentic;experiments/agentic-handoff;experiments/measure/end-to-end-diagnostic;experiments/measure/trace-diagnostics;experiments/table-endpoint'
py -3.14 -B -m unittest test_quote_grounding test_gemini_replay test_handoff test_agentic test_adversarial test_publication_gate test_diagnose test_audit5 test_integration test_audit2 test_audit3 test_audit4 test_ab_harness test_ab_dryrun test_gemini_paired test_gemini_quota test_gemini_credential test_call_ledger
```

## Trade-offs and risks

- A restored span adds the elided text to the quote, so the number check sees more numbers and is somewhat more lenient. This matches what the validator already accepts for any quote up to 1,200 characters.
- The F01 interpretation now reaches the verifier. The paper's sentence concerns its complex-question example. A verifier may judge "these question types" an overgeneralization. Only a live verifier call can show this.
- Typographic drift (curly vs straight quotes, dash variants) is not repaired. No observed failure needed it.
- Table-row claims get `number_grounding: uncertain` and `needs_human_number_check`. That is existing behaviour.

## Reused techniques

- Extractive span grounding: quotes come from source offsets, not generated text, as in attribution and extractive-QA pipelines.
- ALCE/RAGChecker-style per-claim acceptance instead of per-answer rejection.
- The existing `HandoffBudget` pattern of wrapping the provider for a stage without editing the agents.

## Stage A live validation: wired, not run

The mode is `gemini_paired.py --run --grounded-stage-a`, launched through `gemini_credential.py grounded-stage-a`.

- Questions: only F01 and F03, keeping their frozen arm order (current first).
- Settings: same model, temperature 0, simplified-v2 wire, B2 route, budgets and 60 s timeout as simplified-v2.
- Grounding: `enable()` is applied identically to both arms.
- Output: a new one-shot directory, `data/processed/gemini-handoff-paired-v3-grounded-stage-a`.
- Generation cap: 18.
- Preflight records `quote_grounding: true` and the question list.

`stage_a_report.py <run dir>` lists every drafted claim with:

- the original quote(s)
- the recovered quotation
- the full cited passage
- the deterministic checks
- the verifier verdict
- the final outcome: published, held, dropped before verification, or not verified

Execution failures, such as a provider timeout, are listed separately and are not counted as grounding results. `test_stage_a.py` exercises the real runner path through mocked HTTP and checks final publication outcomes. Stage B (F04–F10) is not wired.

## KPMG app integration

- Multi-Agent mode: in `experiments/table-endpoint/live_backend.py`, where `OrchestratorAgent(...)` is built under `--agentic`, wrap it with `quote_grounding.enable(...)` behind a new `--quote-grounding` flag. The envelope and UI contract are unchanged; the trace gains `quote_grounding` notes.
- Baseline (`src/indexed_research.py` → `synthesize`) has the same all-or-nothing rejection. The same `grounded(generate, report)` wrapper could wrap its `generate`. That path was not changed, per the Baseline/B2 freeze. Consider it only after live validation.

## Stage A execution environment

The launcher runs its child with `python -I -B`. Isolated mode drops `PYTHON*` variables and the per-user site-packages, which is intended. System Python 3.14 keeps torch, bs4 and `typing_extensions` in that per-user location, so it cannot run the paired runner.

Stage A uses a dedicated venv, `D:\KPMG-venvs\stage-a-py314` (Python 3.14.2):

- Direct pins: `experiments/agentic-handoff/requirements-stage-a.txt`. These match the ML stack of the environment that produced the simplified-v2 run: torch 2.15.0, sentence-transformers 6.2.0, transformers 5.21.0.
- Full resolved set: `experiments/agentic-handoff/requirements-stage-a.lock.txt`.
- Offline check: the B2 evidence packets for F01–F03, both arms, rebuild identically to the saved v2 packets.

Recreate the venv with:

```powershell
py -3.14 -m venv D:\KPMG-venvs\stage-a-py314
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I -m pip install -r requirements-stage-a.lock.txt
```

`gemini_credential.py` now checks, before it reads the key, that the interpreter can import the runner's dependencies in isolated mode. The check runs with no key in its environment. If it fails, the launcher refuses with a message instead of failing after the key was handed over.

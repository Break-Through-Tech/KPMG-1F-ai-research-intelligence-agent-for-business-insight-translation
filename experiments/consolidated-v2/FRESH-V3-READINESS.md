# fresh-v3 final validation: packet and readiness report (NOT run; awaiting your approval)

**Status:**

- **Ready:** the questions, key, rules and code of all four arms are sealed (45 files). The readiness check passes for every arm: seal verified, ChatGPT login OK, 0 of 90 calls used.
- **Not done:** no live calls, engine changes, merges or deployment.
- **Pending:** your sign-off of the key and approval to execute.

## 1. Benchmark

- **Questions:** `fresh-v3/questions.json`, 8 consultant-framed questions with 38 required points, drawn from the last 8 unused corpus papers. Domains:

  | Domain | Papers |
  |---|---|
  | Catalysis RAG | catalyst discovery study |
  | Molecular ML | MARASON |
  | Clinical evaluation | CliBench, MedQA-CS, Med-CoDE |
  | Biology data access | SANE |
  | AI safety | subtoxic questions |
  | Efficiency | LLM compression survey |

- **Coverage:**

  | Element | Where |
  |---|---|
  | Single-paper questions | 5 |
  | Cross-paper questions | 3 |
  | Numerical and table points | J01, J02, J05 |
  | Multi-part questions | all 8 |
  | Business framing | all 8 |
  | Partly unanswerable | J05, J06, J07 |
  | Relevant limitations | J01.5, J03.5 |
  | Misleading-evidence probes | J01.3, J04.4, J04.5 |

- **Key files:** `fresh-v3/references.json`, `answer-key.md`, `AMBIGUITIES.md` and `KEY-REVIEW-RECORD.md`.
  - Every anchor group, alternatives included, contains every required fact (`build_set.py`).
  - **Review:** one focused independent review (a fresh-context AI reviewer, not human) found 7 substantive errors. All 7 were verified against the corpus and corrected, then the key was sealed once.
- **Rules and frozen criteria:** `fresh-v3/rules.json`.
- **Independence safeguards:**
  - The questions were written from the bundle passages only.
  - No retriever, engine or model was run on them before sealing.
  - The engines are frozen by the seal.

## 2. Arms and call budget

| Arm | Engine | Runner | Expected | Cap |
|---|---|---|---|---|
| B0 | Original Baseline: top-8, quality review, as in every earlier evaluation | `run_fresh3_b0.py` (wraps the frozen `codex_baseline`, not edited) | 16 | 20 |
| S1 | Consolidated Standard v1, frozen control | `run_fresh3_s1.py` (frozen v1 code, verified by the v1 seal) | 16 | 20 |
| S2 | Optimized Consolidated Standard (v2) | `run_consolidated.py standard` | 16 | 20 |
| D2 | Optimized Consolidated Deep (v2) | `run_consolidated.py deep` | 24 | 30 |
| **Total** | | | **72** | **90, persistent, all four arms, retries included** |

- **Run rules:** one run per question per arm, one resume of a failed question, and a 300 s call timeout (unchanged). Adaptive is excluded.
- **Estimated actual provider input:** about 1.8–2.0M tokens. Per question: B0 about 25k, S1 about 77k (measured on fresh-v2), S2 about 50–58k (estimate), D2 about 75–85k (estimate).

## 3. Frozen acceptance criteria (summary; full text in `rules.json`)

| | S2 (Standard) | D2 (Deep) |
|---|---|---|
| Completeness | ≥ 80% (≥ 30.4 / 38) | ≥ 80% |
| Relative | ≥ B0 + 10 pp; ≥ S1 points (no regression) | ≥ S2 + 10 pp |
| Fully answered | ≥ 4/8 | ≥ S2's count |
| Safety | 0 citation-grounding failures; 0 misleading or fabricated claims; 100% exact quotes; 100% numerical correctness | same |
| Execution | 8/8 completed; ≥ 7/8 first pass | ≤ 1 execution error after the resume |
| Latency (total, including failures) | median ≤ 120 s; p90 ≤ 180 s | median ≤ 2× S2; p90 ≤ 300 s |
| Tokens | actual input ≤ 0.80 × S1 | — |

**Decision:**

- **If S2 qualifies:** stop major engine work and move to production integration. The Original Baseline stays default until promotion is approved separately.
- **If S2 fails:** one bounded corrective round only, with no repeated tuning on fresh-v3.
- **D2:** becomes the optional deep mode only if it qualifies.

## 4. Methodological problems flagged before freezing

These are recorded in `rules.json` and kept as you specified.

1. **Absolute 80% is key-dependent.** It measures the key's granularity as much as the engine. Consolidated v1 reached 73.6% and 77.8% on fresh-v2. A fail may reflect key severity.
2. **≥ 4/8 fully answered is demanding.** With 4–6 points per question, a single 0.5 loss blocks a full answer. Earlier arms fully answered 0–1 of 8.
3. **The sample is small and noisy.** One point equals 2.6 pp, and in the previous evaluation, run-to-run variation alone moved five points by 0.5. "No regression vs S1" is an exact comparison and can fail on noise.
4. **The token criterion is bounded by fixed overhead.** The Codex CLI adds about 10k input tokens per call, which limits the achievable relative reduction, roughly −25–35% estimated for S2.
5. **The key author built the engine.** Mitigations: passages-only authoring, sealing before exposure, an independent AI review, and your sign-off. The previous blind scorer caught 1 of 3 identical citation defects, so safety is audited in three passes:
   - programmatic (exact quotes and number recall, digits and spelled counts, every arm);
   - a blind scorer;
   - a Claude audit.

   Anything flagged goes to you; your adjudication is final.
6. **Latency is measured on the Codex provider only.** Production adapters time out at 60 s per call, and that is tested only by the separate smoke test.
7. **Paper reuse within the set:** three papers serve two questions each.

## 5. Previous evaluation: consistent citation adjudication

See `../consolidated/CITATION-ADJUDICATION.md`. Codex's sheet is unchanged.

- **Confirmed additional failures:** Standard H01 L1 and Deep H07 L2. Both say "three-turn", which their own quote does not state.
- **Totals:** Standard 1 failure, Deep 2. Both fail the safety gate, and the closed verdict is unchanged.

## 6. Production-provider smoke test (separate, not part of the 90)

- **Scope:** S2 on 3 fresh-v3 questions with the production adapter you choose (Gemini, OpenAI, OpenAI-compatible or Bedrock).
- **Budget:** 6 calls, **hard cap 10**.
- **Measures:** structured output, schema validation, malformed-output handling, output length against the provider limit, the 60 s adapter timeout, and actual tokens.
- **Status:** prepared after you name the provider. It needs the provider's API configuration on your machine. It does not qualify the provider.

## 7. Execution (you run, in any order, from `D:\KPMG-source-grounded\experiments\consolidated-v2`)

The runners refuse below 6 GB of free memory; 4.4 GB is free now, so close browsers and heavy programs first.

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_fresh3_b0.py --run
```
```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_fresh3_s1.py --run
```
```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --run standard
```
```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --run deep
```

- **Resuming:** rerunning a command resumes it, with at most two attempts per question.
- **Scoring afterwards (0 calls):**
  1. `python -I fresh3_scoring.py audit` (programmatic safety pass).
  2. `python -I fresh3_scoring.py blind` (four-arm blind packet for the independent scorer).
  3. `python -I fresh3_scoring.py criteria <filled sheet>`, after `fresh3-adjudication.json` records the adjudicated safety counts.

## 8. After fresh-v3

This is the corpus's last unused subset. Any later independent validation needs genuinely fresh material: new papers or a new corpus.

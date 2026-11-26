# Opt-in bounded completion pass for Baseline/B2 (offline prototype)

**Files:** `completion.py` (enable with `completion.enable(research)`) and `test_completion.py` (9 tests, passing).

**Status:** offline only. Baseline source is unchanged and no live model calls were made.

## How the existing review detects omissions

`src/answer_quality.py` (answer-quality-v2) tells the reviewer to check "whether retrieved evidence answers a meaningful part that the draft omitted". When it does, the reviewer marks coverage `partial` and says the detail is "available in the passages but omitted".

There is no structured flag for this, and the reviewer may only remove claims, not add them. So the gap text is the only signal.

Observed across 40 saved Baseline runs:

- The pass **triggers on 5 runs**: H05 in both held-out arms, H09 in arm A, H10 in arm B, and F01 in the tables run.
- It **correctly skips** the "do not establish" gaps (F01 and F02 deployed), where the evidence was genuinely missing.
- **Detection limit:** the review marked H06 and H10 (arm A) as `full` although points were omitted. Those omissions are invisible to this mechanism.

## Mechanism

The pass runs at most once, and only when the review reports an *available but omitted* detail:

1. **Re-draft.** One call to the unchanged `synthesize()` on the **same passages**. The question adds the reviewer's gap and the already-published claims. Exact-quote and schema validation apply as usual.
2. **Filter.** Keep only new **findings**; interpretations and duplicates are dropped. Each must pass the deterministic reported-number check.
3. **Review.** Survivors go through the same `review_summary()`. Only claims it judges supported and relevant are added.
4. **Merge.** Published claims and limitations are **never removed or edited**; new claims are appended. The answer lead says a completion pass ran and coverage was not re-assessed.

**Failure behaviour:** any error (provider, invalid JSON, invented quote, invalid review) returns the original answer unchanged.

## Offline tests (saved H05 / H06 / H10 traces replayed through the real synthesize and review)

- **H05.** The completion re-draft quotes c0020 verbatim, recovering GPT-5.1 above 70% and automated reviewer-4.5 at 0%. This would lift H05 from 1 to 3 points if the model drafts as scripted. The original claim stays first and unchanged; the duplicate and the interpretation are dropped; exactly +2 calls.
- **Guarantees tested:**
  - an invented quote discards the re-draft;
  - a number absent from its quote is dropped before review, with no review call;
  - a claim the review rejects is not added;
  - an invalid review or a provider error returns the original;
  - an insufficient re-draft adds nothing;
  - the input answer is never mutated.
- **H06 and H10 (arm A):** not triggered, 0 extra calls. This documents the detection limit.
- **F02 "do not establish":** not triggered.
- **Wiring:** `enable()` works through `create_research().execute()` (synthesis, review, synthesis, review) and refuses to run without the quality review.

## Cost

Per-call figures from the held-out Baseline run: synthesis 16.1 s, 17.6k input tokens; review 9.7 s, 18.2k input tokens.

| | When triggered | Averaged (trigger rate 5/40 = 12.5%) |
|---|---|---|
| Model calls | +2 | +0.25 per question (+12.5%) |
| Latency | about +26 s | about +3 s |
| Input tokens | about +36k | about +4.5k (about +12%) |

**Expected held-out effect:** about +2 points (H05) out of 27, if the model's re-draft behaves like the script. This is not measured live.

## Limitations

- It fixes only omissions that the review itself reports. H06-type and H10-type misses need a stronger completeness check, which is not built.
- Whether the model's re-draft actually supplies the omitted facts is untested live.

# Held-out results (heldout-v1): Baseline/B2 vs Baseline/B2 + question decomposition

- **Runs:** `data/processed/automated reviewer-heldout-v1-baseline` (A) and `automated reviewer-heldout-v1-decomposed` (B). All 10 questions completed in both arms, with no execution errors.
- **Setup:** `gpt-6.1-sol`, low effort; seal verified before each arm.
- **Review status:** the answer key was **AI-assisted reviewed, not independently human-verified**. Scores below are machine-assisted source review: each published claim was checked against its cited passage, and extra details were verified in the index.

## Scores (out of 27 required points)

| Q | A | B | Lost points and cause (identical in both arms unless noted) |
|---|---|---|---|
| H01 | 3 | 3 | — |
| H02 | 3 | 3 | — |
| H03 | 2 | 2 | All five table rows correct in both |
| H04 | 2 | 2 | Both cover QuantMCP API grounding and the metadata pipeline, via equivalent passages (c0019, c0043); the H04.2 anchor (c0002) was absent from both packets |
| H05 | 1 | 1 | H05.2 (GPT-5.1 >70%) and H05.3 (automated reviewer-4.5 0%) omitted. Anchor c0020 was in both packets; the writer drafted one claim and the review flagged the gap. **Draft omission** |
| H06 | 2 | 2 | H06.3 (GPT-4o-mini up to 19%) omitted although c0008 was in the packet. **Draft omission** |
| H07 | 2.5 | 2.5 | H07.1: only the relative 24.1% via c0032; the absolute 62.6%→77.7% (c0030) was retrieved by neither. **Retrieval** |
| H08 | 1.5 | 1.5 | H08.1. A: dataset name only (c0014 not retrieved). **B: dataset + development set of 35 interviews, 12 depressed (decomposition retrieved c0014)**; 189 recordings omitted. Both 0.5 under the strict 1/0.5/0 rule; B's answer is more complete |
| H09 | 3 | 3 | H09.3 published as a cited limitation in both |
| H10 | 2 | 2 | H10.1 Jaccard 0.40 and H10.3 GPT-4 token-classification omitted (anchors present). **Draft omission.** Both link the omitted-label percentages to LLAMA2's missing predictions, which is a reasonable reading of c0030 |
| **Total** | **22.0** | **22.0** | |

| Measure | A (Baseline) | B (+ decomposition) |
|---|---|---|
| Complete / partial / abstained | 4 / 6 / 0 | 4 / 6 / 0 |
| Unsupported published claims | 0 | 0 |
| Misleading claims | 0 | 0 |
| Model calls | 20 | 20 |
| Input / output tokens | 359,073 / 8,884 | 421,779 / 9,396 (input +17%) |
| Total time per question | median 32.8 s, p90 36.5 s | median 42.5 s (+9.6 s), p90 57.7 s (+21.2 s) |
| Retrieval time per question | median 6.4 s | median 15.9 s |
| Packet size | 8 | 8–14 |

**Extra claims checked against the index, all supported:**

- the H05 Table 3 rows for Qwen-3, Llama-3 and Gemini-3
- the H06 religious-persona figures (c0010)
- the H07 41.1% standard-deviation reduction (c0032)
- the H10 BERT 72% / GPT-4 60% / LLAMA2 76% figures (c0003)
- BioBERT 0.61, BERT 0.60 and DistilBERT 0.57 (c0015, c0016)

## Where decomposition helped, hurt, or made no difference

- **Helped (content, below one scoring step):** H08. It retrieved c0014, so B reported the evaluated development set; A could not.
- **Hurt:** none. No new unsupported claims, no crowding losses, no abstentions.
- **No difference:** the other 9 questions. In 8 of them the missing points were draft omissions or a retrieval gap that decomposition did not close.

## Decision rule (pre-registered in `rules.json`)

| Criterion | Result |
|---|---|
| B ≥ A + 2.0 points | **Fail** (+0.0; +0.5 at most if H08 is scored generously) |
| B wins more questions than it loses | **Fail** (0 wins, 0 losses; 1 win at most) |
| No more unsupported or misleading claims | Pass (0 vs 0) |
| No more abstentions | Pass (0 vs 0) |
| Median ≤ +15 s, p90 ≤ +30 s | Pass (+9.6 s, +21.2 s) |

**Outcome:** keep A. Decomposition does **not** meet the bar for integration. The gain is 0 to 0.5 points: at or below the inconclusive band, against +17% input tokens and about 10 s more median latency. It can remain an opt-in experimental flag.

## What limits answer quality on held-out questions

Of the 5 points lost per arm, about **4 are draft omissions**: the needed passage was in the packet, but the single synthesis draft left the fact out. The answer-quality review noticed several of these gaps (for example H05: "the retained claim omits these requested details") but can only remove claims, not add them. About 1 point is retrieval (H07.1 in both, H08.1 in A).

The next lever is synthesis completeness, not retrieval breadth. For example, when the existing review reports a requested detail that is available in the packet, allow one bounded re-draft (+1 call, opt-in). That would need its own pre-registered test.

## Limitations

- 10 questions and 27 points, one run per arm, one model.
- AI-assisted answer key and machine-assisted scoring by the same assistant that built the decomposition. Independent human verification is still required.
- Mostly single-paper questions (H04 is the only multi-paper one), which suits Baseline's single search.

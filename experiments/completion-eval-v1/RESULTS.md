# Completion evaluation results (completion-eval-v1)

**Runs:** A = `data/processed/automated reviewer-completion-v1-baseline`; B = `automated reviewer-completion-v1-completed`, the frozen completion pass applied to A's saved answers. The seal was verified before both runs.

**Review status:** the key and the scoring are **AI-assisted**; there has been no independent human verification. Scores come from my source review of every published claim and cited limitation.

## Required-point coverage (out of 41)

| Q | A | B | Lost points, by cause (A = B unless noted) |
|---|---|---|---|
| C01 | 3 | 3 | — |
| C02 | 2.5 | 2.5 | C02.3 informed-adversary detection (94.5% / 93.9%) and C02.4 cost (~1,700 USD) were not retrieved; the answer correctly says the passages do not establish them. **Retrieval** |
| C03 | 2 | 2 | C03.2: ChatGLM-6B susceptibility omitted, although it was in the packet. **Draft omission.** C03.3: 50/10-sample attack and the pre-training advice were not retrieved. **Retrieval** |
| C04 | 2 | 2 | — (the C04.2 limitations were already published by A as cited limitations) |
| C05 | 2.5 | 2.5 | C05.1: the matched-SeqQA vs LitQA2 nuance was not retrieved (c0028); the 100x summary was given instead. **Retrieval** |
| C06 | 2 | 2 | C06.1 ">10% over SOTA on sparse data" omitted, although c0026 was in the packet. **Draft omission** |
| C07 | 0.5 | 0.5 | **Abstained, evidence-limited.** No KG²RAG passage was retrieved; MultiRAG's mechanism is stated in limitations |
| C08 | 1.5 | 1.5 | C08.1 (size within families) and C08.2 (method-specific mitigation) were not retrieved. **Retrieval.** C08.3 was already published by A as a cited limitation |
| C09 | 1.5 | 1.5 | C09.1 ">50% finance data" omitted, although c0000 was in the packet. **Draft omission** |
| C10 | 1.5 | 1.5 | C10.1: mathematical reasoning / "strongest suit" not retrieved (c0043). **Retrieval** |
| C11 | 1 | 1 | C11.2 (11 of 14 below 65) and C11.3 (impact subdomain) were not retrieved; the answer correctly reports upstream as the weakest *domain*. **Retrieval** |
| C12 | 1.5 | 1.5 | C12.1: chain-of-thought soundness and grounding passage not retrieved (c0033). **Retrieval** |
| C13 | 2 | 2 | — |
| C14 | 2 | 2 | C14.1 and C14.2 latency numbers were not retrieved (F1 values given; the latency direction was stated without numbers); C14.4 chunk-expansion finding omitted. **Retrieval** |
| C15 | 1.5 | 1.5 | C15.1: French and smaller-model details omitted, although c0016 was in the packet. **Draft omission** |
| **Total** | **27.0** | **27.0** | Gain: **+0.0** |

| | A | B |
|---|---|---|
| Complete / partial / abstained | 3 / 11 / 1 | 3 / 11 / 1 |
| Unsupported published claims | 0 | 0 |
| Misleading claims | 0 | 0 |

**Inferred business implications** (C01, C04, C11, C15) were all labelled as interpretations, built on cited findings, and explicitly bounded (for example "a reported comparison, not evidence that openness causes transparency").

**One noteworthy A claim (C06):** A pointed out that its own retrieved figures do not support the paper's assertion of smaller sparsity declines. The arithmetic is correct: Books −6.8 vs −6.1 and Stocks −7.6 vs −6.0.

## Citation accuracy (automated)

- **Exact quotes:** all 158 quotes published by A and all 162 published by B are exact substrings of their cited passages.
- **A content preserved:** B kept every A claim (in order) and every A limitation; only the answer lead was rewritten, as designed.

## Omissions: detected, recovered, missed

- **Triggered: 2 of 15 (C04, C08)**, at 2 calls each. Both triggers were **false positives**. The review's gap said limitations were "omitted from the retained claims", but the same review had already rebuilt those exact limitations into A's published, cited limitations.
- **Added claims: 4**, two each for C04 and C08. All are accurate, quote c0015 and c0028 exactly, and are correctly cited and non-misleading. Each **restates a limitation A already published**: information duplication, not new coverage.
- **Recovered points: 0.**
- **Missed omissions** (available in the packet, never triggered): C03.2, C06.1, C09.1, C15.1, about 2.0 points. Trigger recall: **0 / 4**.
- **Other losses:** most of the remaining ~10 lost points are **retrieval** gaps (the anchor was not in the 8-passage packet), which a re-draft cannot fix.

## Usage and latency

| | A | B |
|---|---|---|
| Calls | 29 (C07 abstained before review) | 4 |
| Tokens (input / output) | 523,391 / 22,640 | 69,522 / 1,141 |
| Wall time | median 48.0 s, p90 58.4 s per question | 19.2 s and 16.0 s on the two triggered questions |
| Errors | none | none |

Total: 33 calls of the 60-call cap.

## Business relevance and usefulness (qualitative, A = B)

**Strengths:**
- Answers are framed for the client's question, with clear published findings and separately labelled, bounded recommendations (C01 rollout safeguards, C04 locally tested aid, C11 vendor-diligence checklist, C15 separate competence and bias checks).
- Strong caveats; zero unsupported claims.
- It states what the evidence does not establish (for example C02 cost, C14 latency numbers) instead of guessing.

**Weaknesses:**
- 66% point coverage. Most misses are retrieval-limited (an 8-passage packet for multi-part business questions).
- One evidence-limited abstention on a two-paper comparison (C07).

## Decision (frozen rule)

| Criterion | Result |
|---|---|
| Integrate: ≥ +2.0 points | **Fail** (+0.0) |
| Abandon: "no point recovered on any triggered question" | **Met** (0 recovered on C04 and C08) |
| Safety: unsupported or misleading additions, removed A content | 0 / 0 |

**Outcome: ABANDON the completion pass.** It is safe, but it adds nothing:

- Its only trigger signal (the review's gap text) fired on limitations the review itself had already published.
- It never fired on the four genuine draft omissions.

Baseline/B2 remains the production default, unchanged.

## Limitations

- One run per arm, one model, 15 questions.
- The key and the scoring are AI-assisted.
- I wrote both the questions and the mechanism.

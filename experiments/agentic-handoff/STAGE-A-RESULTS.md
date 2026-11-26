# Stage A: quote grounding, live Gemini (F01, F03)

Run: `data/processed/gemini-handoff-paired-v3-grounded-stage-a`. It completed with no execution failures.

| Setting | Value |
|---|---|
| Model | `gemini-3.1-flash-lite`, temperature 0, simplified-v2 wire |
| Quote grounding | On in both arms |
| Usage | 10 of the 18 allowed generations; 21 HTTP requests, all HTTP 200 |
| Tokens | 119,975 prompt, 3,853 output |
| Largest single generation | 23.6 s |
| Operator confirmations | Free tier, exclusive use, prior-24h bound of 22 |

The per-claim report is `data/processed/stage-a-report.json`, produced by `stage_a_report.py`.

## Controlled comparison with simplified-v2

Each arm's evidence packet is byte-identical to simplified-v2's for the same question and arm. The current-arm drafts for F01 and F03 are also identical to v2 (temperature 0). For those arms, the only difference between v2 and Stage A is quote grounding.

| Question / arm | Simplified-v2 (no grounding) | Stage A (grounding) | Grounding action |
|---|---|---|---|
| F01 current | False abstention (quote rejection) | Published, full scope: 3 findings + 1 interpretation | Restored elided text in c0017 |
| F01 handoff | False abstention (quote rejection) | Published, full scope: 3 findings + 1 interpretation | Restored elided text in c0017 |
| F03 current | False abstention (quote rejection) | Published, full scope: 2 findings | Restored elided text in both table rows |
| F03 handoff | Execution failure (60 s read timeout) | Published, full scope: 2 findings | None needed. The draft quoted whole rows |

The F03 handoff timeout did not recur, but grounding did not cause that. Its synthesis call returned within the 60 s limit this time; the slowest generation in the run took 23.6 s. Provider latency is variable, so the timeout risk remains.

## Source review

Each published claim was checked against its cited passage and the arXiv HTML. The F01 table and counts were confirmed verbatim. The Topo-RAG Table 1 values match the indexed table rows. The web check of that table and of MultiFinRAG §4.3 came from a fetched-page summary, not verbatim text, but agrees with the passages. This is machine-assisted review, not independent human sign-off.

| Claim | Arms | Verdict |
|---|---|---|
| 300 questions; 42 image-based, 72 table-based (c0012) | both | Correct |
| Image-based: Baseline+Gemma 0%, MultiFinRAG+Gemma 66.7% (Table 1 row 2) | both | Correct |
| Table-based: Baseline+Gemma 5.6%, MultiFinRAG+Gemma 69.4% (Table 1 row 3) | both | Correct |
| Interpretation: the gap on these question types shows MultiFinRAG retrieves and integrates information better (c0017) | both | **Misleading: generalized beyond its source and misattributed** |
| Cora 2,708 nodes, Arxiv 16,316 nodes | both | Correct |
| Cora random split, Arxiv time split | both | Correct |

The F01 interpretation is a problem for two reasons:

- The sentence it relies on ("0% … to 40% … underscores the framework's ability to retrieve relevant trunks and integrate information") is about the category that needs both text and image/table reasoning. That is the 40-question category, scored 0% → 40%.
- For image and table questions, the paper attributes the gap to something else. The Baseline only embeds text, and Gemma 3 describes images and tables better (c0016, c0017).

The restored quote makes this visible, because its 0% → 40% example does not match the claimed categories. Even so, the verifier judged the claim `supported` with no issues. The same over-attribution was published by both arms in the original-wire v1 run, with no grounding involved. It is therefore an existing synthesis/verifier weakness on interpretations. Grounding stopped it from causing an abstention but did not stop it from being published.

## Results

- **Required points:** F01 2/2 in both arms; F03 2/2 in both arms.
- **Published claims:** 18 in total. 16 correct findings; 2 interpretations (one per F01 arm) misleading as described above.
- **Unsupported findings published:** 0. Wrong numbers published: 0.
- **Remaining failures:** the F01 interpretation over-attribution (verifier miss), and the unresolved provider-timeout risk.

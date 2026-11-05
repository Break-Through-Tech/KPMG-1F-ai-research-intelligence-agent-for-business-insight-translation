# Findings: semantic chunking is not intrinsically worse

This stack tests the earlier hypotheses instead of changing the production default.
The clean-source results support further work, but not a blanket superiority claim.

## Clean-source development validation

These are complete **designated-span retrieval** counts, not answer accuracy.
Both sides have a 1600-token evidence cap. Existing is the fixed unexpanded
baseline; the semantic combination is chosen using tuning papers only and may
include neighboring context. Full tables also compare identical expansion
settings and token-only controls.

| Encoder | Source | Existing | Tuning-selected semantic combination | Token-only, no semantic cuts |
| --- | --- | ---: | ---: | ---: |
| MiniLM | HTML | 10/18 | 15/18 | 12/18 |
| MiniLM | TeX | 10/18 | 15/18 | 13/18 |
| BGE | HTML | 11/18 | 13/18 | 12/18 |
| BGE | TeX | 13/18 | 16/18 | 13/18 |
| E5 | HTML | 14/18 | 13/18 | 15/18 |
| E5 | TeX | 10/18 | 12/18 | 12/18 |

The clean-source selected combination beats the fixed existing baseline in five
of six encoder/source cells, but the cells share papers/questions and are not six
independent replications. There are only nine validation papers. Do not interpret
these small differences as statistical significance.

## Which explanations survived the checks?

1. **Equal context budget changes the conclusion.** On MiniLM/HTML, the unchanged
   original semantic policy goes from 8/18 at top5 to 15/18 at 1600 tokens; the
   existing chunker scores 10/18 in both conditions. The earlier fixed-top5 test
   was not sufficient to condemn small semantic chunks. Many small, relevant
   retrieval seeds can work when they are allowed a fair evidence budget.
2. **Tuning is model/source dependent and can fail to transfer.** The tuning
   winner for E5/HTML scores 13/18, below the fixed baseline's 14/18 and the
   original semantic policy's 15/18. BGE/HTML's selected size/overlap policy scores
   13/18 while the original semantic policy reaches 15/18 at the same cap. We do
   not replace the locked tuning choices with the best validation rows.
3. **Not all gains require semantics.** E5/TeX's token-only control also scores
   12/18. Its improvement over the 10/18 baseline does not establish an additional
   benefit from semantic cuts. Token-aware size/overlap is an important control.
4. **Neighbors are not automatically beneficial.** Large baseline windows may
   exceed a cap and be skipped. Both fixed and expansion-matched controls are
   disclosed; the headline does not hide a simpler baseline that performs better.
5. **Source extraction and retrieval are different failure modes.** All 38
   matched clean-source questions have their designated spans in HTML and TeX.
   Two PDF validation questions lack spans in the extracted text. Available-only
   cross-format tables keep that distinction explicit.
6. **The exact-span metric can falsely label an answerable context a failure.**
   [Two post-run spot checks](QUALITATIVE.md) show baseline supporting the answer
   with alternative wording. These scored semantic gains are not factual
   answer-quality wins. No generated answers or judge API were used.

## Scope and decision

The study covers 19 matched versioned papers, 38 development questions, 11 policies,
4 retrieval conditions and 3 encoders in each of PDF/HTML/TeX: 396 ablation cells.
The questions are split by paper (20 tuning / 18 validation), but are development
labels, not a fresh blind test. The larger 105-PDF experiment remains a separate
result; this is not a claim of 105 clean-source papers.

HTML is current-parser output; TeX is cached historical-parser include-block
output with recorded archive hashes, not rendered prose or a rerun of the latest
TeX extractor. Both formats are evaluated separately without PDF substitution.

**Decision:** keep semantic retrieval experimental, with equal-token budgeting
as a required comparison. The results justify better evaluation, not switching
production defaults. Acceptance needs new independent papers and pre-specified
concept/claim rubrics with blinded relevance or generated-answer review.

See [full ablations and provenance](results/SUMMARY.md), the
[locked protocol](results/protocol.json), and [reproduction instructions](README.md).

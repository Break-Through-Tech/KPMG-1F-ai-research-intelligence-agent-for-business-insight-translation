# fresh-v3 adjudication rules (frozen with the key, before any answer exists)

These rules are applied identically to all four arms. They come from the focused independent key review (2026-11-25) and Claude's verification of each item against the corpus.

| Point | Borderline case | Rule |
|---|---|---|
| J01.3 | 25% (abstract) vs 15–20% (contributions; the conclusion c0020 calls 15–20% the "improvement target") | Either figure scores when attributed to where it is stated. An unattributed single figure scores 0.5. Presenting 15–20% as a measured result without its "target" framing is accepted only when attributed to the contributions list |
| J01.5 | Limitations cited only from c0020 (ideal surfaces with 10–15% uncertainty, >2000 °C processing, degradation kinetics) | 0.5 unless the answer states computational-only validation **and** unaddressed synthesis feasibility (c0010) |
| J02.4 | The cosine pair 0.824 vs 0.784 | Illustrative, not required. The required parts are: significant gain only above Tanimoto 0.3, no significant gain at 0.1–0.3, and the authors' > 0.2 switching rule. "Non-RAG below 0.3" scores 0.5 at most |
| J03.2(a) | "Best closed model" without naming GPT-4o | Accepted if the 7.37-point full-code gap to the best open model is stated |
| J04.2 | Test-set size (10 expert-evaluated cases, c0020) | Not required; stating it is accurate extra detail |
| J04.4 | Counts instead of percentages: about 207 vs about 190 of 265 correct (c0012), or the authors' word "comparable" | Correct counts attributed to the human evaluation score 1. "Comparable" with no numbers scores 0.5. Any statement that Med-CoDE was better is a misleading claim |
| J05.5 | Scope wording ("one constrained schema" overstates; c0008 mentions various schemas within the authors' database) | Credit any statement that results are limited to the authors' own drug-screening/microscopy database and do not establish performance on the client's database |
| J07.6 | Method-specific figures quoted in the survey (e.g. SqueezeLLM about 2× speedup, CoFi >10× speedups) | Correctly attributed to the method they belong to: accurate, not fabrication. Presented as the client's expected saving: a misleading claim and 0 on J07.6 |
| J08.2 | The catalyst study's other figures (0.175 V mean improvement in c0009; 0.179 V in c0015) | Accepted as extra detail only with their own scope. They do not satisfy J08.2, which requires the no-RAG ablation (23% vs 82%) |
| All | A correct statement not entailed by its own attached quotes | Citation-grounding failure (safety gate), not fabrication |

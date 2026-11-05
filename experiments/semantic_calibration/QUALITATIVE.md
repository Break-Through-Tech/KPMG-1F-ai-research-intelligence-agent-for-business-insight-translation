# Qualitative spot checks of the metric (not a separate accuracy evaluation)

These examples were inspected **after** MiniLM results, without changing locked
policies, splits, anchors or policy selection. They were deliberately chosen from
scored semantic wins, so they are not representative or independent validation.
They demonstrate why span-count gains must not be equated with answer quality.
The full saved contexts, including paper/source locators, are in each local
`report.json`.

## HTML n05 — gauge-theoretic obstructions

Question: “Which three obstructions to global interpretability are identified by
the gauge framework?”

Designated spans: `local jamming`, `proxy shearing`, `nontrivial holonomy`.

MiniLM, original semantic policy, 1600 tokens: the retrieved abstract explicitly
lists the designated labels, so the metric passes.

The baseline, at the same budget and without neighbor expansion, retrieves:

> three distinct mechanisms—local overload (jamming), cross-chart incompatibility
> (proxy shearing), and intrinsically path-dependent transport (holonomy).

**Inspection:** the baseline already supplies all three mechanisms in explanatory
language. Its failure to contain the exact labels is not an inability to answer.
The semantic result is more direct, but this case does not demonstrate a factual
answer-quality win.

Paper: https://arxiv.org/html/2603.00824v2

## TeX n16 — stages in the physics diagnostic

Question: “What are the four stages in the parallel-physics reasoning diagnostic?”

Designated span: `induction, formulation, prediction, and review`.

MiniLM, threshold .65 with neighboring context, 1600 tokens: the retrieved
abstract contains that literal list, so the metric passes.

The baseline **with the same neighbor setting and budget** retrieves:

> Stage 1 (induction), Stage 2 (formulation), Stage 3 (prediction), and Stage 4
> (review)

**Inspection:** both contexts contain the complete answer. Extra stage numbering
breaks the designated phrase match. This is a metric false negative for baseline,
not evidence that the baseline loses the four stages.

Paper source: https://arxiv.org/src/2607.00276v1

## Consequence

Read the study as a controlled retrieval diagnostic. Cleaner sources and equal
budgets can materially change the ranking of methods, but answer-quality
acceptance needs pre-specified concept/claim rubrics (including valid alternative
wording), more independent papers and blinded relevance/answer review. No judge
API or generated answers were used in this experiment. These spot checks do not
quantify the prevalence of metric artifacts in either direction.

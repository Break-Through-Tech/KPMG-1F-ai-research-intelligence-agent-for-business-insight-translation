# Semantic chunking calibration study (experimental stack above PR #170)

This layer adds **offline experiments only**. It does not select a production
chunker, alter ingestion source precedence, train a model, download models, write
a Chroma index, or merge PR #170. Model/profile/source correctness is distinct
from retrieval quality. Source records, offsets, queries and adverse results are
retained outside the checkout; compact results are committed under `results/`.

## Locked design

- Three pinned small encoders: MiniLM, BGE-small, E5-small. Their adapter profiles
  separate symmetric grouping embeddings from query/passage retrieval prefixes.
- Existing cached versioned source material: 25 PDF papers, 20 HTML papers and
  23 nonempty parsed-TeX papers. **19 papers available in all three formats** are
  the matched primary corpus, including distractor papers in both splits.
- PDF comes from the previous 105-paper extraction, but this experiment does not
  claim a 105-paper clean-source corpus. HTML is re-parsed using current code.
  TeX is cached raw include-block output of parser commit
  `556383c39bbcd6fd979eaf1454564e7fb7c92667`, with original archive SHA256 and
  block-file SHA256 retained. Original archives are not locally present, so this
  is **not a rerun of current TeX extraction**. Raw math/macros are not rendered.
  Empty/unavailable sources are recorded; there is no PDF fallback masquerading
  as HTML/TeX. HTML ingestion removes display equations/table bodies.
- 25 existing factual development questions plus 25 new explanatory questions
  authored from metadata abstracts before this sweep. The 19 matched papers
  supply 38 questions: 20 tuning questions on 10 papers, 18 validation questions
  on 9 different papers. Sorted versioned IDs alternate tuning/validation.
  Both questions from a paper stay together. All papers remain searchable in
  both phases. These are **retrospective development labels, not a fresh blind
  test**, and two questions from one paper are not independent trials.
- Policies, split and selection rule are written to `protocol.json` before any
  retrieval scores. No post-result tuning. Pick the semantic policy/neighbor
  combination per model/source using tuning-only complete-span count at 1600
  tokens. Tie-break on smaller mean context, then lexical policy/mode name.
  Baseline and token-only controls do not participate in semantic selection.

## Ablations

| Policy | What changes from the original semantic prototype? |
| --- | --- |
| original | threshold .72, max 1800 characters, no overlap |
| threshold35 / threshold50 / threshold65 | threshold only |
| minimum80 | suppress semantic cuts until 80 passage tokens, size bound still wins |
| minimum80_token240 | also bound groups to 240 tokens |
| minimum80_token240_overlap32 | additionally repeat up to 32 tokens of whole units |
| threshold50_minimum80_token240 | threshold/size combination |
| percentile20_minimum80_token240 | local 20th percentile of adjacent similarities replaces fixed cutoff |
| baseline | existing recursive 1800-character/250-overlap rule (math-safe split for TeX) |
| token_only240_overlap32 | token/overlap control without semantic cuts |

Minima are soft: source ends and hard size boundaries can produce smaller chunks.
Math/literals and long indivisible units may exceed the token ceiling; counts are
reported, not hidden. A character size is not an encoder-token guarantee. Token
limits include model-specific passage prefixes/special tokens. Over-limit source
units are retained with encoder truncation counted; they are never broken inside
recognized math just to improve a score.

Every policy is tested with top5, 800 tokens, 1600 tokens, and 1600 tokens with
one preceding/following sibling. Exact cosine ranking uses normalized embeddings,
with stable ties and the same **200-seed candidate cap** for every arm. Context
is packed in rank order as whole chunks/windows, skipping those that do not fit.
Oversize context is not truncated. Neighbor expansion never crosses a PDF
page/section, HTML section/subsection or TeX include block. Repeated evidence is
merged by original source offsets; only original whitespace gaps are bridged.
Budget charges each emitted source interval, including prefix/special-token
cost, once. Report actual token use: a cap is not a guarantee every arm fills it.
No generation prompt/citation-framing tokens are budgeted.

## Metrics and interpretation

Primary diagnostic: all designated source spans appear in retrieved context for
a question. Normalize Unicode, punctuation, case and TeX command names for
matching only; the original text is embedded and preserved. Do **not** concatenate
unrelated source intervals to manufacture a matching quote. This is not semantic
entailment, response accuracy, clinical accuracy, or human-scored relevance.

Report all questions and extraction-available denominators separately. A source
can lack an anchor because of parsing, macros, missing tables, or wording. Such
cases stay in the overall denominator and are not silently scored as pure
retrieval failures. Cross-format comparisons must also use the subset whose
anchors are available in every format. Numeric and short-label anchors can
produce false positives, and paraphrases can produce false negatives. A clean
source and a higher span score do not establish better generated answers.

The report includes paired question wins/losses, mean delivered tokens,
fragmentation/encoder-limit counts, selected-policy validation, and full ablation
tables. All arms are disclosed even if the hypothesis fails. Local timings are
one MPS run with cached models and shared sentence/chunk embeddings, **not** a
chunker speed benchmark or comparison with previous CPU timings.

## Reproduce

Use Python 3.12 and the repository requirements. Place source artifacts outside
the product checkout. The preparation command takes explicit paths, not hidden
workspace globals:

```sh
python -m experiments.semantic_calibration.prepare \
  --pages /path/to/expanded/pages.json \
  --questions /path/to/expanded/questions.json \
  --html-dir /path/to/cached/html \
  --tex-audit-dir /path/to/tex-audit \
  --output /path/to/study/corpus.json
python -m experiments.semantic_calibration.run \
  --corpus /path/to/study/corpus.json \
  --output /path/to/study/results --device mps --sources html tex pdf
python -m experiments.semantic_calibration.summarize \
  --corpus /path/to/study/corpus.json --results /path/to/study/results \
  --output experiments/semantic_calibration/results
```

Models are resolved by exact cached revision, never fetched. CPU is the portable
default; MPS is explicit. Corpus hashes and the complete protocol must match to
resume. Completed model/source reports are reused; incomplete arms rerun.
Artifacts include block locators/line numbers, source receipts, all emitted
contexts, chunk/vector matrices and question outcomes. Exact model revision,
input hashes, package versions and source paths are run provenance, not dataset
redistribution. Reproduction requires those versioned source artifacts or the
saved corpus bundle; a compact summary alone cannot reproduce the experiment.

Offline CI checks use fake embeddings and exercise context budgets,
deduplication, citation boundaries, math atomicity, overlap progression and
validation-independent selection. CI does not download research papers or run the
model sweep.

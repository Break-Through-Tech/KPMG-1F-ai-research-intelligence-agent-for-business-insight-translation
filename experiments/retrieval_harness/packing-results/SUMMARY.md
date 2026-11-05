# Packing optimization follow-up

**Retrospective development diagnostic, not answer accuracy or a blind test.**

Fixed E5, 19 matched papers, 38 inspected questions (18 reported validation questions). Every arm deduplicates source intervals. Scores are exact designated-span coverage.

| Policy | HTML 800 / 1600 | TeX 800 / 1600 | PDF 800 / 1600 |
| --- | --- | --- | --- |
| hybrid | 14 / 17 | 14 / 16 | 12 / 14 |
| protected | 9 / 17 | 9 / 14 | 7 / 14 |
| compact | 13 / 15 | 13 / 13 | 12 / 14 |
| protected_compact | 14 / 15 | 14 / 14 | 12 / 14 |

## Findings

- No tested alternative consistently beats equal-rank hybrid with whole-chunk packing. Keep the incumbent; do not change production defaults.
- Protecting the first three dense hits recovers n22 on HTML at 1600 tokens but loses r05: 17/18 remains 17/18. At 800 tokens it drops HTML and TeX from 14/18 to 9/18. Reserving rank positions is too blunt a budget policy.
- Upfront 160-token lexical windows reduce HTML from 17/18 to 15/18 and TeX from 16/18 to 13/18 at 1600 tokens. Smaller windows are not inherently better; query-term coverage can omit required evidence or context.
- PDF remains 14/18 at 1600 tokens, with two questions lacking required anchors in extracted input. No evidence of improved answer quality follows from a tie.
- All source contexts retain exact original offsets/locators and obey the token cap. Indivisible units are not clipped; they may remain oversize and be skipped.
- The cache optimization preserves the completed HTML output exactly. It caches query-independent candidate windows and does not change selection semantics. This is not a controlled latency benchmark.

## Next experiment, not yet implemented

Prefer budget-aware fallback over upfront compaction: retain full high-ranked evidence when it fits, and consider smaller sentence windows only for otherwise excluded candidates. Score window relevance semantically, not only by shared words. Evaluate paired losses as well as recovered misses, and use fresh fact-reviewed questions before promoting a policy. Avoid tuning solely to n22.

## Reproduction and artifacts

See the run_packing command in the parent README. Protocol/outcomes/hashes are committed here; raw source-backed contexts remain in the local kpmg-packing-cached-followup-20261104 output directory. Prefix/special-token overhead is counted per interval; generation-prompt framing is excluded.

Control qualification: this follow-up deduplicates all arms; the previous hybrid arm packed raw intervals. Validation anchor outcomes match, but TeX tuning r04 at 1600 changes partial anchor bits from [true,false] to [false,false]. Both remain incomplete. Do not claim identical contexts or exact parity across every tuning anchor.

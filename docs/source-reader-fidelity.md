# Source reader: navigation and fidelity inspection (#142)

## Changes — 2026-10-27

The source dialog now supplies a named **Source structure navigation** region with
keyboard buttons to each retained table/formula. Targets have unique ordinal names,
source table captions where supplied, visible focus, and independent horizontal
scrolling. Navigation never rewrites citation-check text or source locators.

Real arXiv inspection found `intent=":literal"` and native MathML size/spacing and
boolean attributes caused whole-passage fallback. Both producer and browser now
retain the literal intent and bounded numeric lengths/booleans. Unknown intent,
CSS, unsafe/unbounded values and unsupported mathematical semantics still reject
the whole structured passage. No style/URL execution or inferred headers are added.

## Reproduce source-backed development inspection

Download the exact version-pinned arXiv HTML through the existing bounded fetcher,
retain original bytes and run:

```sh
python -m scripts.audit_source_reader source.html --arxiv-id 2608.20318v1 --out /tmp/reader-audit.json
```

The report records original source SHA-256, section locators, canonical-text hashes,
original/retained structure counts, retained header attributes and extraction gaps.
Inspect formulas and table cells against the original separately from DOM checks.
Counts alone do not certify completeness, meaning, or screen-reader behavior.

## Two real-source inspections

2026-10-27, parser over fetched version-pinned source HTML; no provider/model used.

| Source | Source SHA-256 | Source → retained math | Source → retained tables | Header caveat |
| --- | --- | --- | --- | --- |
| [AI4AI-Bench, 2608.20318v1](https://arxiv.org/html/2608.20318v1) | `60938176890f24ede8eb7040c02b4e8f8b3666c38977af3d5c863123f5a2024c` | 189 → 134 | 2 → 2 | Source contains no `th`; none invented. |
| [Pandora's AI Model Routing Box, 2608.20316v1](https://arxiv.org/html/2608.20316v1) | `4c39edf2ac6dc6aa092bcaa8112ed1a47dec7b80adb13715805630a7ecf66c54` | 694 → 344 | 29 → 11 | All 59 supplied `th` retained; counts do not prove every relationship. |

Unsupported styles/attributes still force fallback in affected sections. Some tables
in the source are layout constructs. Figures/captions are incomplete in retained
structure; provenance and explicit extraction limitations remain visible. These
are bounded development inspections, not representative-corpus certification.
No lost structure is recovered for existing PDF-only/indexed chunks; those remain
honest text/TeX fallback. No index rebuild, corpus replacement or reindexing occurs.

## Remaining manual gate

With VoiceOver and Safari, inspect the same pinned sources: enter the source dialog,
use headings/landmarks and the table/formula jump buttons; navigate table headers
and cells and native MathML; return to the originating claim. Record OS/browser/AT
versions, mode, source hashes, failures and actual audible behavior. Repeat native
200%/400% zoom. Automated roles/namespace/header checks supplement this walkthrough,
not replace it. #142/#145 remain open for that manual acceptance and broader fidelity
review. No WCAG or stakeholder approval is implied.

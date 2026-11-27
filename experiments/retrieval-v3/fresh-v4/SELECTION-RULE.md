# fresh-v4 paper selection rule (written before discovery)

**Purpose:** independent validation material for S3 versus frozen S2. It is never used for development or tuning.

## Eligibility

A paper is eligible only if all of these hold:

1. **Submitted 2026-11-01 to 2026-11-20 (UTC).** The demo-100 corpus ends at 2609.x, so these are newer than every corpus paper.
2. **Category:** cs.CL, cs.AI or cs.LG primary listing.
3. **Not already present:** not in demo-100 by arXiv ID, any version.
4. **HTML available:** an arXiv HTML (LaTeXML) version exists at `arxiv.org/html/<id>`, because the index is built from HTML as for demo-100.
5. **Quantitative:** it reports quantitative results in at least one table.
6. **Extractable:** the existing `html_evidence` extractor yields at least 20 passages with valid source bindings.

## Themes and order

There are five themes, mirroring the corpus's business-research domains. For each theme, the collector is run in `--dry-run` mode with the keywords below (case-insensitive AND on the abstract). The **first two eligible papers by submission date** are taken, with no other judgement.

| Theme | Keywords |
|---|---|
| T1 Retrieval-augmented generation | `retrieval-augmented` |
| T2 LLM agents and tool use | `agent`, `benchmark` |
| T3 LLM safety and jailbreaks | `jailbreak` |
| T4 Clinical and medical LLM evaluation | `clinical`, `language model` |
| T5 Inference efficiency | `quantization`, `language model` |

**Duplicates:** a paper that qualifies for two themes counts for the first theme only, and the second theme takes its next eligible paper.

**Fallback:** if a theme has fewer than two eligible papers in the window, the window for that theme only is extended backwards to 2026-10-01. The extension is recorded.

## Recording and use

- **Recorded for every paper considered:** the discovery listing, each eligibility decision and the reason for any skip, in `selection-log.json`.
- **Questions and answer key:** written afterwards from the extracted passages only. No engine is run on them before the key is sealed.

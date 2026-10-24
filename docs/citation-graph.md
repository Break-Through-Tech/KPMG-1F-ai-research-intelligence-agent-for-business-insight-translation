# Offline source citation graph

This is a separate source-backed layer, not body-text extraction, a crawler,
retrieval expansion, claim-support validation, or a production index update.
It shares the validated archive reader introduced by the figure-text change.

## Usage

```sh
python -m src.data_ingestion.citation_graph \
  --source 2605.00276v1=/path/to/2605.00276v1.source \
  --source 2605.00273v2=/path/to/2605.00273v2.source \
  --output /tmp/citation-graph.json
```

Inputs must be existing local source archives. There is no network code or
integration into the ingestion pipeline. Output is replaced atomically only
after every input is processed; failure preserves the prior graph. API callers
use `build_graph([{arxiv_id, title, source_bytes}, ...])`.

## Semantics and provenance

- A `cites` edge records explicit citation syntax in reachable, branch-filtered
  document-body source. It does **not** mean supports, endorses, agrees with or
  influenced. TeX macro/package execution is not emulated: syntax inside macro
  arguments/definitions is not proof of a rendered citation.
- `bibliography_only` distinguishes uncited/`nocite` records from actual citation
  syntax. `nocite{*}` is not treated as citing every bibliography entry.
- Every edge keeps exact source version and archive SHA-256, case-sensitive
  citation key, citation file/line sites, bibliography file/line, parsed fields,
  syntax format, explicit arXiv IDs, and identity status. Duplicate keys retain
  their distinct source records and remain unresolved.
- Declared `.bib` resources resolve only against the selected root and containing
  file directories. Root-preamble `addbibresource` declarations are recognized;
  arbitrary included preamble programs are not evaluated. Ambiguous and missing
  resources are reported. No unrelated `.bib` file is swept into the graph.
- `.bib` uses pinned `bibtexparser==1.4.3`; undefined/repeated string definitions and malformed assets
  remain explicit instead of becoming silently confident matches. Inline
  `bibitem` is supported. Generated `.bbl` is considered only when its path
  exactly matches the selected root's stem and a declared bibliography is absent;
  even then it stays **provisional**, never a canonical identity/expansion target.
  Filename correspondence is not build/revision proof.
- Explicit arXiv identifier metadata yields a versionless `arxiv:<base-id>` node;
  exact cited versions remain on edges. Metadata candidates are not remotely
  verified identities. Citation keys and titles are never identity evidence.
  DOI-only or ambiguous entries remain separate reference nodes; no fuzzy title,
  case-folded citation-key, or cross-provider DOI merge is performed.
- `papers` receipts preserve missing/ambiguous resources, root-BBL candidates,
  parse failures, unresolved citation keys and duplicate keys. A partial
  bibliography is a reported research artifact, not complete-paper acceptance.

## Expansion and limits

`expansion_candidates(graph)` supplies at most ten **offline hints**, from
explicit, unambiguous `cites` metadata only; provisional/uncited nodes and source
papers are excluded. Counts are unique citing source papers, not duplicate
references or citation popularity as a truth signal. This is not query-relevance
ranking. `enabled=false` and `automatic_expansion=false`: nothing is downloaded.
A later opt-in one-hop acquisition/retrieval change must add relevance selection,
exact-version pinning, rate/byte budgets and separate context labeling.

Existing source-archive validation applies, plus the shared 16 MiB per selected
asset/32 MiB selected-assets bound; graph limits are 100 papers, 100 MiB aggregate
input, 10,000 bibliography records and 20,000 citation sites per source paper.
No archive content is compiled, executed or extracted to disk. Generated corpus
JSON, downloaded papers and local verification receipts do not belong in tracked
diffs. No production ingestion or source-certification claim follows from this
syntax-level graph.

### Conservative conditional boundary (2026-10-23)

Citation discovery uses the shared non-executing source traversal. Unknown
macro calls mixed with conditional selection, including citation commands
inside literal conditions, now reject the bundle instead of guessing branch
execution. URL/path examples are opaque, including delimiter-form operands.
Literal citation/bibliography declarations without unresolved execution still
produce source-located graph hints; no package semantics or truth claim is added.

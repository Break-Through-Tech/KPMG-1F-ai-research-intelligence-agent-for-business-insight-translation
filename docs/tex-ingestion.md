# Optional raw TeX archive ingestion

Run `python -m src.data_ingestion.pipeline --with-tex` to download arXiv
source bundles into ignored `data/tex/` and use HTML → raw TeX → PDF selection.
Without the flag the existing HTML → PDF behavior is unchanged. Offline callers
can cache `<arxiv_id>.source` (replace `/` with `_` for legacy IDs), then call
`process_and_store(metadata, output_path, use_tex=True)`.

Supported inputs: UTF-8 single TeX, gzip single TeX, tar, and gzip tar. Exactly
one `\begin{document}` root is required unless the archive’s `00README.json`
selects a single valid `sources[].usage=toplevel` filename. This honors arXiv’s
root declaration instead of guessing among bundled templates/revisions. Missing
or ambiguous declarations still fail closed. Braced `\input{file}` and
`\include{file}` references resolve against the root document directory or containing file
(ambiguous matches are rejected); `.tex`
is appended if absent. Cyclic, missing, unbraced, traversing, or excessive
includes fail this source rather than silently publishing a partial document.
TeX is **never compiled**, commands are never executed, and files are never
extracted to the filesystem. Links, special entries, duplicate TeX paths,
unsafe paths and oversized archives are rejected. Limits are 32 MiB download,
128 MiB expansion (including binary assets), 32 MiB aggregate TeX text, 2048 archive entries, 128 TeX files/include visits and depth 32.
HTTP 429 stops acquisition; download failures are retryable (no permanent miss
marker). Invalid existing caches are not overwritten automatically: replace or
remove the affected cache deliberately before retrying acquisition.

Chunks retain raw document-body TeX (including math delimiters and commands),
with comments and the preamble omitted. Removed comments and inactive constant
branches are blanked without changing character offsets or line numbers. This is **not** rendered prose or a full
TeX interpreter: no macro expansion, bibliography processing, package semantics, or
general conditional evaluation is supplied. Literal `\iftrue`/`\iffalse` branches
are selected with nesting validated; inactive text and includes are never
published. Dynamic primitives and `\newif` conditionals remain unsupported.
Ordinary macros beginning with `if` (such as `\ifthenelse`, `\ifdefempty`, or
`\ifplotsrgb`) remain raw macros, not misclassified primitive conditions.
`\verb`, `\verb*`, `verbatim`, `Verbatim`, `lstlisting`, and `minted` blocks
are preserved as opaque, atomic source spans: percent signs, dollar signs, and
include-like examples inside them are not interpreted. `comment` environments
are omitted. Malformed/oversized literals fail closed. This is lexical handling,
not execution or interpretation of the examples.
Macro-generated/conditional includes and documents requiring other encodings are unsupported. TeX with these constructs should use
the HTML/PDF route. As with any source, ingestion does not certify semantic
fidelity, completeness, or model claim support.

TeX citations carry `source=tex`, `source_url=https://arxiv.org/src/<id>`,
`source_file`, 1-based `line_start`/`line_end`, and `source_sha256` for the exact
archive bytes. `page_number` is null. Source URLs identify the bundle, **not** a
fabricated browser line anchor; file/line ranges locate text inside that bundle.
The preamble remains recoverable from the archive. Prose uses overlapping soft-size chunks. Explicit inline/display math and common
`equation`, `align`, `alignat`, `flalign`, `gather`, `multline`, `eqnarray`,
`displaymath`, and `math` environments (including starred variants) are atomic:
chunk boundaries do not bisect them. Nearby preceding prose remains with an
equation where possible. A chunk exceeding the 1800-character target to retain
math or a literal is marked `oversized_math=true` and keeps its file/line locator. Individual
math or literal spans above 32768 characters or unclosed delimiters fail the TeX source
and use PDF fallback. Macro-generated math is not recognized; equation
interpretation remains separate. Model-context packing also treats TeX passages
as atomic: if a whole passage cannot fit the per-passage or total budget, it
and lower-ranked passages are omitted and reported, not silently truncated. The existing retrieval adapter and evidence
contract preserve these locators; no UI or preview changes are part of this PR.

Malformed/unusable TeX falls back to PDF. If no source produces chunks for any
selected paper, the atomic corpus publication fails without replacing the prior
Parquet file. This does not build or mutate a vector index automatically.

Validation: `python -m pytest tests/test_tex_ingestion.py` exercises multi-file
math, locators, bounded acquisition, unsafe archives/includes, opt-in selection,
PDF fallback, citation metadata and atomic publication.

## 2026-10-19 compatibility recheck

All 25 versioned source bundles in the checked-in sample were downloaded and
rechecked independently of the production corpus/index. Baseline: 11 parser
passes / 14 rejections. With lexical/manifest/limit fixes: 22 passes / 3
rejections. These are parser-acceptance counts, not semantic-fidelity scores.
The remaining papers still use dynamic conditionals: SEFORA (`\ifdim` in
PGF graphics), RMSWeb (`\ifdefined` controlling publication sections), and
Validity-Aware Jailbreak Evaluation (`\ifCameraReview` custom conditionals).
They deliberately retain HTML/PDF fallback; neither branch is guessed.
Mandatory TeX-only publication is not enabled by this change.

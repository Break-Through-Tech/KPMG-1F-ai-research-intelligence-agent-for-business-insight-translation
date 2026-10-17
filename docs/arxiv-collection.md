# Bounded arXiv candidate collector

`python -m src.arxiv_collection` writes a **separate candidate dataset**. It does
not feed the index builder: that builder reconciles a *complete* corpus and would
delete old chunks if given only the newly collected records.

```sh
# Discovery window is UTC, inclusive since / exclusive until.
python -m src.arxiv_collection --category cs.AI \
  --since 2026-10-01 --until 2026-10-08 --keyword agent \
  --max-results 25 --page-size 10 --output /tmp/arxiv-candidates --dry-run

# Repeat with the same filters/output to resume. Use another output for another window.
python -m src.arxiv_collection --category cs.AI \
  --since 2026-10-01 --until 2026-10-08 --keyword agent \
  --max-results 25 --page-size 10 --output /tmp/arxiv-candidates

# Exact-version replay and optional acquisition. No automatic ingestion.
python -m src.arxiv_collection --ids 1706.03762v7 --download \
  --max-results 1 --output /tmp/arxiv-replay
```

Outputs: 1F-compatible `metadata.csv` and `metadata.jsonl`, versioned
`manifest.json`, `checkpoint.json`, `report.json`, optional hashed PDFs. Downloads
use temporary files and check PDF header/EOF; this is transport validation, not
proof of complete PDF structure, source accuracy, or successful extraction.

Repeated known IDs never terminate scanning. State saves each record before
advancing a page, so an interrupted page can be replayed. Failed downloads retry
on subsequent invocations, including when discovery is exhausted. Downloads are
also capped per invocation by `--max-results`; `downloads_deferred` means more
work remains. Existing validated files are reused. Only one writer may use a
candidate directory at once; do not run concurrent collectors there.

The checkpoint is authoritative. Every completed non-dry invocation republishes
metadata and the manifest from it, including exhausted resumes that reuse all
PDFs. If interrupted between output writes, rerun with the same filters/output
to repair missing or stale exports; the files are not a multi-file atomic snapshot.

Dry run discovers over the network but creates no directories, manifests,
checkpoints or caches. Keywords are case-insensitive **AND** filters on abstracts;
`--query` supplies an optional arXiv API query expression. IDs/versions remain
distinct. An unversioned exact ID resolves latest **once** in that output snapshot;
use a new output to refresh that resolution.

Discovery uses `submittedDate`, oldest first, and bounded pages. The report
distinguishes `window_exhausted`, `truncated_resumable` and `failed_resumable`.
Exhaustion means the API-reported result set was traversed, not an independent
completeness audit. Use closed fixed windows and overlap/replay for ongoing
collection: live API results may shift and offset pagination is not a snapshot
protocol. This does not discover every revision to much older papers.

`.github/workflows/arxiv-collector-manual.yml` is a manual-only artifact-upload
wrapper, not enabled scheduling. It has read-only repository permissions and
does not commit PDFs. It was inspected locally, not dispatched. Each job starts
fresh; cross-job checkpoint persistence/scheduling is deliberately not claimed.

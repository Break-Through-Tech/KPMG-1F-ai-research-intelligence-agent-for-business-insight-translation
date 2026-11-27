# Research evidence integration checkpoint

The consultant UI uses an isolated same-origin proxy. The recorded backend replays
saved briefs, and the live launcher uses the existing B2 pipeline with an explicit
generation budget that defaults to zero. The endpoint reconstructs tables from
the indexed rows and requires an independent extractor audit before marking a
table complete. Unverified or incomplete tables remain available as retrieved
rows without a chart.

## Baseline and local inputs

The checkpoint starts from 727b0b380b1d6e68943e08124b537d4d8982a14e.
Use that exact source export for repeatable demo-bundle comparisons. The 100-paper
bundle, source HTML, local model snapshots, recorded brief database, generated
audit, and browser fixtures are supplied separately. Request the approved QA
inputs from the maintainer. Use a separate writable copy for saved-brief tests.

The verified demo bundle's parents.jsonl SHA-256 is
78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa.
The audit matched indexed source hashes to local HTML and used these extractor
files, identified by SHA-256 of the exact bytes:

| Extractor | Location in the verification inputs | SHA-256 |
| --- | --- | --- |
| html-evidence-v2.1-stage-a | Baseline export, src/experimental/html_evidence.py | 0bba09d7ffa68d731833ae62e372dcd725307b66f9da0758e51087e3ffd3f86d |
| html-evidence-v1.2 | Legacy extractor directory supplied by the maintainer | 75a3f6e7490e12ce9d01244b5541f0fea30d77386d7946243bda9b8313fcbf6f |
| v1.2 HTML parser dependency | html_parser.py beside the legacy extractor | 2876f370e0ce2927ea5a2dd8df27edee150fad811ec747c24f1d03fbc21ab8c4 |

For the legacy extractor, use the exact local source files rather than a
different file with the same version string. Use source snapshots with the
recorded line endings when checking byte hashes. The audit is specific to the
bundle. A different bundle requires its own audit.

## Model-free reproduction

Commands below assume the repository root and a Python environment with the
project dependencies. Use unused loopback ports and replace angle-bracket
arguments with local paths.

~~~text
python -I -B experiments/table-endpoint/build_table_audit.py --export <baseline-export> --bundle <demo-bundle> --extractor-dir <legacy-extractor-dir> --html-root <html-cache> --out <local-audit-json>
python -I -B experiments/table-endpoint/recorded_backend.py --export <baseline-export> --bundle <demo-bundle> --table-audit <local-audit-json> --recorded-briefs <recorded-source-db> --working-copy <disposable-db> --port 8796
python -I -B ui-consult/serve.py 8830 --backend http://127.0.0.1:8796
python -I -B ui-consult/tests/test_serve.py
~~~

Open http://127.0.0.1:8830/ to inspect the recorded workflow. An unconnected
UI host opened with ?mock=1 serves explicit synthetic data.

The endpoint regression suite and fixture exporter retain their verified Windows
QA input paths. Their expected inputs are a baseline export under
D:/KPMG-demo-corpus/main-727b0b3, its data/processed/demo-bundles/demo-100
subdirectory, and D:/KPMG-demo-corpus/fable-live-briefs.sqlite3. If the inputs
are stored elsewhere, adjust their local path constants in disposable test
copies. Supply the generated audit as table-audit-demo-100.json beside those test
copies. Run test_evidence_tables.py with python -I -B. The suite uses a temporary
database copy and ephemeral ports.

To run the browser suite, use the fixture exporter against the approved QA
inputs or obtain the four recorded fixture files from the maintainer. Place
them locally under ui-consult/tests/fixtures. Start the UI host with
--serve-tests and open /tests/evidence.test.html. Keep recorded fixtures out of
Git. The optional live launcher accepts explicit encoder and reranker paths and
--check-only for a model-free startup check.

## Results and limits

The model-free verification includes 21 endpoint tests, eight proxy tests,
and 30 Chromium tests. The browser tests cover numeric order, 810px and 809px
chart scrolling, exact paired-point source targets, and evidence provenance.
A separate recorded-response browser check verified that a delayed Library import
respects newer navigation. The proxy and browser tests exercise a lost response,
including HTTP 504. A write stays in an unknown state until a saved change can
be identified. New brief creation still has no server-side idempotency key.

The prior live demo used a bounded generation budget and recorded research
and review results. The checkpoint tests use saved data. The demo-100 audit
verified 423 tables, refused 12 on extractor-row disagreement, and refused one
for a missing or oversized cell. Saved-brief approval applies to the saved
snapshot. Citation membership checks and table fidelity do not establish
semantic entailment.

V2/V3 ranking and the full-library startup patch remain separate integration work.
The shared backend can be used for ordinary research and saved briefs. Full
tables require the isolated route and a matching audit.

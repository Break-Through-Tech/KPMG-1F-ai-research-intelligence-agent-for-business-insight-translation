# Research progress checkpoint

S2 remains the selected demo engine. S3 is experimental. The application and the deployed demo are unchanged.

## Reproduce the evaluations

- The Fresh-v4 runner and its sealed question, reference, and rule files are under `experiments/retrieval-v3`. The final report and adjudication are there too. Archived per-question result, attempt and call JSON files are under `archived-runs`. To reproduce post-processing, restore each archived arm to its matching name under `data/processed` in a disposable clone.
- Restore the pinned corpus and index from the local project assets using the bundle record, source IDs and checksums. Retrieve original arXiv versions from the source manifest if needed. Downloaded HTML, large diagnostics, local databases, credentials, environments, model weights, logs and generated staging bundles are excluded.
- The consolidated experiment was frozen against several uncommitted shared-source files. Their exact changes are preserved in `shared-engine-dependencies.patch`. Apply it only in a disposable evaluation checkout and verify the frozen manifest before running. This checkpoint does not activate the patch.
- The two staging directories include build and deployment source. Rebuild generated packages locally and supply the inputs described in their README files. No staging deployment is part of this checkpoint.
- Provider identifiers, source citations and frozen attribution are retained wherever changing them could break execution, invalidate hashes, or misstate the evaluation process.

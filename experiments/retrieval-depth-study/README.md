# Offline retrieval depth and selection study

Run from this directory with the pinned research Python environment. Set B2_RESEARCH_ROOT, B2_BUNDLE, B2_ENCODER, B2_RERANKER, and B2_BASELINE_RUN to the existing source checkout, frozen index, two local model directories, and archived baseline run. Enable offline model loading. Input artifacts and generated packet JSON are kept outside Git.

Run capture_rankings.py, compare_selection.py, compare_controls.py, compare_depth.py, and count_passage_tokens.py. The summarization and scoring scripts read their generated artifacts. Source-reviewed reference IDs enter only the scoring steps or retrospective replay diagnostics. The development labels and historical answer grades are AI-assisted and lack independent human verification. See selection-study.md and depth-study.md for results and cited research.

# fresh-v2 paper reuse and overlap

- **Papers:** all 8 are the corpus papers that appear in no earlier question, reference, label, case, benchmark or fixture file under `experiments/`, `tests/`, `evaluation/` or `docs/`.
  - The scan excluded 8 manifest-style files that list more than 25 corpus papers (indexes, bundles).
  - The papers: 2601.01627v3, 2601.07954v1, 2510.18728v1, 2406.03805v1, 2506.17299v2, 2604.12817v1, 2405.17440v1, 2512.11437v1.
- **Questions:** new. No model has answered them.
- **No tuning:** the consolidated engine was designed and tested only on the combined-v1 failure traces, which are recorded as regression cases. No parameter was set or changed using these questions.
- **Offline check:** `offline-check.json` was produced after the engine was written. It reports request sizes and, for information only, anchor coverage of the Standard packet. It changed nothing.
- **Within-set reuse:** some papers appear in two questions with different focus:
  - JMedEthicBench: H01, H07
  - CLINIC: H07, H08
  - Continuous adversarial training: H04, H05

  Their scores are correlated, which is a stated limitation.

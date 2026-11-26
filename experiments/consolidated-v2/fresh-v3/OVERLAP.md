# fresh-v3 paper reuse and overlap

- **Papers:** all 8 appear in no question, reference, answer-key, case, label, fixture or test file under `experiments/`, `tests/`, `evaluation/` or `docs/`. Each appears only in 1–3 retrieval-trace or listing files, as a distractor.
- **Corpus:** these are the last unused papers of the 100-paper corpus.
- **No engine or model has seen the questions.** They were written from the bundle passages only. No retriever, packet builder or engine was run on them before sealing.
- **Within-set reuse** (correlated scores, reported as a limitation):

  | Paper | Questions |
  |---|---|
  | Catalyst study | J01, J08 |
  | MARASON | J02, J08 |
  | MedQA-CS | J03, J04 |

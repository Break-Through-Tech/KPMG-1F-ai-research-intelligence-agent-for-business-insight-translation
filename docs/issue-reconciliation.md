# Evaluation acceptance handoff — October 13, 2026

## Current main versus this proposed stack

Checked main `b00c736b2cb4800db6aa68f45c9931ff97bb6aff` and live issue/PR states
on October 13. Main includes Khoi's HTML validator (#102), source-grounded
summarization (#99), and BYOK generation (#94). The updated #96/#97 stack
is still proposed work, not merged acceptance evidence.

- **#95:** superseded by the merged validator and the retained PDF regression
  in #96. The overlapping HTML test was removed; no separate test PR is needed.
- **#96:** builds directly on main, retaining a precise PDF wrong-page rejection
  test. Consumes the shared validator's `PASS` receipt, protected input hashes,
  implementation hashes, passage counts, and persistent-transport checks. It
  reconciles every indexed ID/text/citation against the validated corpus before
  freezing retrieval outputs. Old lowercase-status receipts are not accepted
  as fresh validation; regenerate a receipt rather than rewriting history.
- **#97:** this handoff only. Historical generated reports, frozen retrieval
  exports, and review worksheets are in the PR discussion, not the source diff.
  Full original records remain recoverable at contributor commit
  `09b47f2916edaef21945626a28f97c0397b322cc`; moving evidence is not a new run.

## Issue dispositions

| Issue | Current implementation/evidence | Remaining acceptance |
|---|---|---|
| #44 | Closed; PDF/layout and data-quality assessments landed | Closure is not proof that every extraction defect is repaired |
| #76 | Open; workflow structural checks and fixtures exist | Dedicated shared interfaces/versioning and acceptance still need their own work |
| #77 | Closed; dedicated `src/summarization.py` landed in #99 | Preserve its semantic-quality limits; this stack does not establish full evaluation |
| #78 | Open; workflow/CLI and configurable generation exist | Bind summary, business, and actual review stages; produce combined-run evidence |
| #80 | Open; prompts landed; translator is proposed in #100 | #100 has not landed; no business-quality or stakeholder approval is inferred |
| #81 | Open; standalone regulatory checkpoint and approval safeguards exist | A dedicated research-review integration and real human review remain |
| #82 | Closed by merged #102; locked-sample HTML validation and audit evidence exist | Omission candidates and scientific-completeness follow-up are not parser fixes |
| #64 | Open; benchmark runner exists; proposed #96 binds capture to the current validator | Fresh validated retrieval capture and a later combined generation/business run |
| #65 | Open; scoring/review tooling exists | Actual named reviews, double review/adjudication, scores, and stakeholder feedback |
| #57/#59 | Open; benchmark/rubric definitions exist | Team pilot, reviewer allocation, and original-paper answerability confirmation |
| #66 | Open; ingestion/index/retrieval exist | Combined outputs and scored human evaluation remain |

No issue is closed or reopened by this handoff. #82 is already closed; this
stack must not claim a second closure or pretend that implementation equals
semantic acceptance.

## Reproduce new evidence without committing generated output

Supply the exact cached sources and processed Parquet required by the validator.
Then use new local output locations (the examples are ignored by Git):

```bash
python -m tests.validate_html_sample --report-dir data/processed/html-validation
python -m evaluation.capture_validated_retrieval \
  --validation data/processed/html-validation/html-ingestion-validation.json \
  --output data/processed/evaluation-runs/new-retrieval-run
```

The validator uses temporary regenerated Parquet/Chroma; capture can rebuild
this checkout's persistent retrieval index. The capture output refuses overwrite.
No answer-generation provider is invoked. The real embedding model must be
available; query execution success does not measure passage relevance.

Publish redacted receipts in a PR comment or attachment. Retain corpus,
validation, implementation, index, and model-weight provenance. Never edit an
old receipt's hashes or schema to make it pass the updated gate.

## Historical capture and next evaluation

The October 13 historical run recorded 877 HTML chunks and ten actual MiniLM
retrieval queries with zero execution failures. Its validator schema and code
revision are historical. It did not run answer generation/business translation
or receive actual human scores. It is not proof that the revised capture has
completed a fresh real-corpus run, nor Precision@5 or end-to-end quality proof.

BYOK and summarization are now implemented on main; #100's business adapter and
#81's review integration remain separate. For a new combined run, bind the real
adapters and an authorized provider, retain abstentions/disagreements, then
have actual reviewers inspect claims at original sections/pages. Provider
calls may incur costs; none were made to update this stack. Empty review input
continues to leave scores null, targets unmet, and `approved=false`.

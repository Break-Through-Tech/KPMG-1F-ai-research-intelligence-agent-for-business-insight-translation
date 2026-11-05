# Query-to-evidence flow and interface acceptance (#120)

This note captures the user flow, fixture-to-screen mapping, and interaction
checks for the local research interface. The walk-through used the browser demo
on 2026-10-30. It was a fixture-based usability check, not a stakeholder review,
screen-reader audit, or evaluation of real research answers.

## Annotated flow

```text
[Mode and research entry]
  Demo mode shows a fixed prepared question and result selector.
  An editable question appears only for explicitly configured live research.
          |
          v
[Question + run status]
  Keep the submitted wording visible; say whether this was a fixture,
  a saved result, or an executed research run.
          |
          v
[Research findings] --------------------> [Inspect citation]
  Show supported claims and gaps.             Show the exact passage and
  Label interpretation separately.            source locator; offer a
          |                                     separate link to the paper.
          |                                              |
          |                                      [Source context]
          |                                      Full passage and metadata
          v
[Business implications]
  Show only if requested and supported.
  Keep suggestions conditional and label actions and assumptions.
          |
          v
[Limitations, risks, review state]
  State what is unknown and why. Keep a draft visibly pending review.
```

### Main acceptance path

1. The page identifies prepared examples before interaction. Selecting one
   displays a sample and does not search the fixed example question.
2. An editable question appears only when a live research mode is configured.
   The result retains its exact wording and a visible run outcome.
3. Findings link to evidence that can be inspected without losing the answer.
4. Unsupported subquestions remain unanswered; they are not filled from model
   memory or treated as false.
5. Any business implication is visually separate from research findings.
   Suggested actions, assumptions, risks, and limitations remain distinct.
6. The review state is explicit. A citation or a successful run does not mean
   that a person has verified or approved the result.

## Fixture-to-screen states

Every research fixture and paper locator below is synthetic. The example.com
URLs are labels for the UI, not links verified against real papers.

| UI state | Fixture or response | What the user should see |
| --- | --- | --- |
| Full draft | `tests/fixtures/research/normal-v1.json` | Research findings, conditional business implications, inspectable HTML and PDF citations, limitations, and pending review. |
| Partial answer | UI-only variation of `normal-v1.json`; business status becomes `insufficient_evidence` | Keep supported findings. Explain that evidence does not support a business recommendation; do not make a recommendation or describe this as a provider failure. |
| Abstention | `tests/fixtures/research/insufficient-v1.json` | Show that passages were found but do not support an answer. Keep claims and recommendations empty; allow inspection of the passages. |
| No evidence | `tests/fixtures/research/empty-v1.json` | Say that no passages were retrieved and generation was skipped. Do not say that the research claim is false or that no such research exists. |
| Provider failure | Simulated `provider-error` envelope; no provider is called | Say that execution failed, no draft was produced, and offer retry. Do not present this as an evidence gap. |
| Local transport failure | Browser cannot reach the local demo server | Explain how to recover and offer retry. In live mode, retain the exact question; in demo mode, retain the selected example. Do not display an earlier answer as the new result. |

These are separate states: **no evidence** means retrieval returned nothing;
**abstention** means passages exist but do not support a response; a **failure**
means a stage did not complete. A **partial answer** preserves the supported
part while making the unsupported part visible.

## Interaction and accessibility checklist

- [ ] Demo mode clearly labels prepared examples, shows their fixed question,
  and does not expose an editable question as if it were searched.
- [ ] A live research question has a visible label and appears only when the
  server explicitly configures a live mode.
- [ ] Loading, success, abstention, no-evidence, and error states have readable
  text and a polite status announcement. Failures name the failed stage when
  known and preserve the original question for retry.
- [ ] A partial answer retains supported findings and clearly identifies the
  unsupported part; it never invents citations or a recommendation to fill a gap.
- [ ] Keyboard users can reach and activate each citation. Citation inspection
  shows the source passage and location; opening the original paper is a separate
  link. Closing the preview returns focus to its citation.
- [ ] Long source passages remain readable and navigable without hiding their
  citation metadata or forcing horizontal scrolling.
- [ ] Research findings, interpretations, business actions, assumptions, risks,
  and limitations are labeled separately.
- [ ] Draft/review status is visible and cannot be inferred from citations,
  generated language, or a successful request.
- [ ] Check the flow at narrow and zoomed layouts; ensure dialogs, focus order,
  errors, and source controls remain usable.

## Prototype walk-through and findings

The current default fixture page labels itself **Demo mode — prepared examples**
and shows a fixed example question before interaction. The editable question
field is absent in this mode; the example selector chooses only a prepared
result. Configured live paper and index modes use a separate research-question
composer. These modes do not imply a live connection unless server
configuration enables one.

Keyboard activation of a citation opened its preview and moved focus to
**Close cited quote**. The preview correctly called the fixture text a **Source
passage**, not a verified quotation, and provided separate actions to open the
source locator or inspect the wider context. The partial state retained its
findings and showed no supported business recommendation. The simulated
provider-failure state explained that no draft was produced and offered
**Retry prepared example**; there is no typed research question in fixture mode.

Earlier walkthroughs exposed ambiguous wording in the partial state: it said the
business translation was “unavailable,” even though the fixture represented
insufficient evidence rather than a failed stage. The interface now says that
the evidence does not support a business recommendation. A genuine business
stage failure gets distinct failure wording and retains the supported research
summary.

This was a bounded desktop walkthrough only. Mobile layout, screen-reader
announcements, real provider failures, and whether source passages semantically
support their claims still need separate checks. Fixture behavior is not
evidence of real-world research quality or stakeholder acceptance.

# Research desk: UI and progress updates

**For Alesha · October 28, 2026**

Suggested changes, not yet implemented. Start with the first two sections;
streaming can come later.

## 1. Make it clear what the app will do

- Label the current mode: **Live research**, **Prepared example**, or **Saved answer**.
- Use one question box and one main **Research** button. Keep reading preferences
  together under **Preferences**.
- Explain live mode briefly: “Searches indexed papers and generates a draft answer.”
- In example mode, say clearly that typing a question will not run research.
- Keep **Draft · Human review pending** on generated answers.

## 2. Show what is happening while the user waits

Add a small progress block beside the answer being prepared:

```text
Researching your question                    Elapsed 01:24
Preparing findings from 3 papers
Last server update: 2 seconds ago
```

The backend should report the current step. Suggested labels:

| What is happening | Label |
| --- | --- |
| Request accepted | Question received |
| Looking up evidence | Searching indexed papers |
| Extracting a particular paper | Reading [paper title] |
| Retrieved evidence | Found 5 passages across 3 papers |
| Evidence sent to the model | Preparing findings from 3 papers |
| Waiting for generation | Waiting for model response |
| Validating the answer | Checking response format and supporting quotes |
| Translating findings | Drafting business implications |
| Finished | Draft answer ready |

Use real titles and counts. If several papers go to the model together, show
**Sources supplied for this step**; do not cycle through titles as if the model
were reading them one at a time. We cannot observe that.

An elapsed timer is useful, but it does not prove the server is working.
Show the time since the last server response separately. If updates stop, say
**No recent server update**; do not immediately call the research failed.
Never invent percentages or advance stages on a timer.

## 3. Stream the answer as it is written

Token streaming would make long waits feel more responsive. Show incoming answer
text in the answer area, labeled **Drafting · Not yet checked**. Keep progress
updates visible too: some stages may produce no answer text for a while.

- Stream only user-facing answer text, not internal reasoning, raw JSON,
  tool logs, or provider errors.
- Before completion, treat text and citations as provisional. Do not enable
  saving, exporting, or read-aloud for this unfinished draft.
- Run the existing format and supporting-quote checks on the complete response.
  Replace the preview with the validated draft and its working citations.
  These checks do not establish that every claim is true; human review remains.
- If generation or validation fails, remove the unchecked preview from the
  answer area and show a clear failure message. Preserve any separately validated
  findings if only a later section fails.
- Do not simulate streaming by slowly revealing an already completed answer.

**Implementation note:** the current Codex adapter waits for the whole response
in `src/codex_generation.py`. Reading its output incrementally is necessary but
not sufficient: first check whether the selected CLI actually exposes answer-text
deltas. If it does not, keep stage updates and defer token streaming or choose a
supported streaming adapter explicitly. Do not promise a typing effect from the
current integration.

## 4. Keep recovery and reading comfortable

- Preserve the question when something fails. Prevent duplicate submissions
  while a request is running; reconnecting must not silently start another run.
- Keep findings, business implications, and limitations visually distinct.
  Preserve existing citation inspection and reading settings.
- Do not steal focus or force scrolling when status or text changes.
- Announce stage changes and completion to screen readers, not every token or
  timer tick. Respect reduced motion; avoid flashing or pulsing indicators.
- Check the layout on a narrow screen and at 200% browser zoom.

## Suggested build order

1. **Clear labels and waiting state.** Mostly `ui/index.html`, `ui/app.js`, and
   `ui/styles.css`. Keep the existing request flow for this first pass.
2. **Real progress updates.** Have the backend report accepted/running/finished
   states and actual stages. A small background job plus status polling is a
   reasonable starting point in `src/research_demo.py`; status reads must stay
   responsive while generation runs. Restrict updates to the requesting session.
3. **Streaming.** Once the adapter supports genuine text deltas, add a streaming
   connection, such as server-sent events. Keep status polling as a recovery path;
   reconnect to the same run rather than submitting again. Bound retained output
   and handle disconnects without losing the final result.

## Quick check before calling it done

- Live, example, and saved modes are unmistakable.
- A slow request shows honest progress; a lost connection is distinguishable.
- Paper titles and counts match the evidence actually supplied.
- Streamed text stays provisional until the full response passes existing checks.
- Failure preserves the question, and double-click/reconnect does not run it twice.
- Keyboard navigation, citations, reading settings, and screen-reader
  announcements still work.

For existing behavior, see [the local interface guide](local-research-interface.md),
[question recovery](accessibility-question-entry.md), and
[research contracts](research-contracts.md).

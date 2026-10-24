# Optional read-aloud: isolated preparation for #144

Parent: #136. This is a **draft, unintegrated component**, not completion of #144,
#137, #138, screen-reader accessibility, or WCAG conformance. The normal research
page and server do not import or serve it. No paid service, account, credentials,
application fetch, or speech dependency was added.

## Dependency boundary

Prepared from origin/main `ffb3027ee1b39a434903b9b1883907d55e52a633` on 2026-10-23.
At inspection #137 and #138 were OPEN, with draft PRs #147 and #146 respectively.
Their inspected heads were `675389e48314b9c5cd745491a243f2ae2658db9c` and
`30859a4a9939b118452d420705009d45da22d5f1`. Neither is assumed delivered.
No shared app.js/index.html/styles.css/server edits are included here.

After those core contracts are delivered, integration must:

1. Add the module/CSS to the server's explicit static asset allowlist, import and
   mount one persistent component outside live answer status regions and within
   the appropriate focus scope (including a mobile source modal).
2. Supply stable, distinct `id`, descriptive `label`, and exact plain `text` for
   each selectable result/source passage via `setItems`. Do not extract the
   entire page/hidden disclosures/KaTeX markup or introduce duplicate math text.
   Preserve findings versus interpretations, citation identifiers, source title
   and page/section, partial/abstention labels, limitations, and pending-review
   status. Speech is supplementary: never replace or hide the visible original.
3. Call `setItems` synchronously whenever content changes/removes, including result
   replacement, new paper, passage selection, and provider failure. Stable IDs
   must not conceal text revisions. Clear items when no eligible text exists.
   The module stops if selected text/label disappears or changes; unselected
   updates do not interrupt playback. Selection/speed changes stop without restart.
4. Stop on source dismissal, result clearing and navigation. Call `destroy()` on
   teardown; DOM removal/pagehide/hidden-tab cancellation are additional safeguards.
5. Recheck #137 keyboard focus, source modal/desktop focus boundaries, #138
   concise announcements and #130 indexed mode. Do not ship optional audio ahead
   of core accessibility or imply it replaces VoiceOver.

API example (not currently wired into the application):

```js
import {mountReadAloud} from '/read-aloud.mjs';
const reader = mountReadAloud(persistentContainer);
reader.setItems([{id: 'result:stable-id', label: 'Result 1 · Draft, not approved',
  text: exactPlainTextIncludingCitationsAndLimitations}]);
// setItems never starts speech; only pressing Play does.
reader.stop();
reader.destroy();
```

## Engine and network behavior

Uses the browser Web Speech API (`speechSynthesis`, `SpeechSynthesisUtterance`).
Only voices advertising `localService === true` are eligible; the first available
local voice is selected. No remote/cloud fallback, recording, microphone access,
voice download, persistence, or text submission endpoint is implemented. The app
makes no network request for speech. Browser/OS local-voice metadata is trusted,
not independently audited: voice installation, OS services and browser telemetry
can have their own network behavior. Do not promise verified offline execution.
If no local voice appears (including engines with only remote voices), Play is
unavailable, an explanation remains visible, and all text/citations remain usable.
A `voiceschanged` event refreshes availability without starting speech.

Playback is chunked into at most 200 Unicode code points (prefer whitespace),
one utterance at a time to reduce long-utterance engine failures. Playback may
pause briefly between chunks. Starting explicitly cancels the document speech
queue and clears a retained engine pause flag. All instances sharing that engine
coordinate ownership; this does not control audio in other tabs/apps or VoiceOver.
Cancelling the queue can interrupt unrelated Web Speech callers in this document;
future integration must use this as the sole document Web Speech owner.

A startup timeout and runtime errors stop playback and leave a text fallback.
Browser pause/resume/end event reliability varies. The browser may ignore pause
or stop; thrown cancellation failure tells the user to use system audio controls.
This is not a guarantee against buggy browser/OS engines.

## Controls and announcements

Native fieldset/legend, explicitly labeled text and speed selects, Play,
Pause/Resume and Stop buttons; visible starting/reading/paused/stopped/error state.
Speed: 0.75×, 1×, 1.25×, 1.5×, 2×. Changing speed requires explicit Play to restart.
Pause/Resume uses the same button to retain focus during label changes.
No automatic playback on load, result update, selection, voice arrival, focus,
resume from hidden tab, or completion. Resume only follows user activation.

Status is short, atomic and polite when idle/paused/error; while starting/reading
its live behavior is off to avoid competing automatic speech. The full passage
is never copied into a live region, and duplicate identical status writes are
suppressed. DOM properties alone do **not** establish VoiceOver announcement
behavior; actual coexistence remains untested.

## Reproduce focused checks

No new Node dependencies are required for controller tests (Node 22+):

```sh
node --test tests/ui/read_aloud.test.mjs
```

The scoped read-aloud workflow runs those tests. Browser tests remain a separate
manual developer command; no new browser dependency/lockfile is introduced.
Use an existing Playwright installation and its installed browser, or set
`PLAYWRIGHT_CHANNEL=chrome` to use installed Chrome:

```sh
python3 -m http.server 9144 --bind 127.0.0.1
# In another terminal; resolve playwright via NODE_PATH or PLAYWRIGHT_MODULE:
PLAYWRIGHT_CHANNEL=chrome node tests/ui/read_aloud_browser.cjs
```

Optional `READ_ALOUD_BASE_URL` overrides the server origin. A separate server
port avoids sibling sessions. Fixture URL: `/tests/fixtures/read-aloud.html`.
Browser script saves screenshots in `/tmp/kpmg-144-*.png`; no report/screenshot
files are committed. It injects a deterministic **mock engine**, not real speech.
Native selector popup keyboard behavior is a manual gate; `selectOption` only
verifies selection change wiring. Enter/Space playback activation and Tab focus
order use actual browser keyboard events.

## Evidence recorded 2026-10-23

| Check | Observed result / boundary |
| --- | --- |
| Controller | 10 Node tests pass: no autoplay; selected text/rate; pause/resume/end; no overlap; revisions/removal; stale callbacks; chunking; unsupported/remote-only voices; late voices; errors/timeouts; teardown |
| Browser | Chrome 155.0.8059.86 headless via existing Playwright; Browser plugin not available; installed Chrome used because Playwright's bundled browser binary was absent |
| Identity/content/overlay/console | Correct fixture title, meaningful original text/citation, no framework overlay, no captured console warnings/errors |
| Interaction | Tab through citation/text/speed/Play, Enter Play, Space Pause, Enter Resume, Enter Stop; same Pause/Resume element retains focus |
| State | Visible status and live-region attributes checked; selection change does not restart; root removal cancels; unsupported Play disabled, original text/citation retained |
| Reflow/visual | 1280×1000 desktop, 390×844 unsupported mobile and 320/390 CSS-pixel reflow; no horizontal document overflow. Desktop and unsupported mobile screenshots inspected |
| Not tested | Real audible synthesis, actual local-voice network traffic, Safari/Firefox, native select popup keyboard interaction, manual browser zoom, VoiceOver, integrated research workflow, indexed mode |

## Required manual/integration gates (not performed)

- Deliver/reconcile #137/#138 first, then test the real ask → answer → inspect
  citation → choose passage → dismiss source workflow, including changed/removed
  results, source switching and modal viewport transitions while speech is active.
- Record macOS, browser, VoiceOver versions and tested modes. With VoiceOver on,
  load/update/inspect without pressing Play: no optional passage speech. Navigate
  headings/citations normally. Explicitly play, pause/resume/stop using keyboard;
  confirm actual audible behavior and concise state announcements without a
  second automatic reading of the passage. If duplication occurs, revise the
  announcement policy; DOM tests cannot certify it.
- Verify native select operation, 200% browser zoom, supported browser engines,
  local voices/voice loss, device sleep, tab/navigation cancellation, and
  offline/network behavior on the supported OS/browser combination.
- Retain all partial/abstention, citation/source provenance and pending-review
  labels; do not mark #144 or parent #136 complete from this fixture PR.

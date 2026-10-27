# Accessibility baseline and integrated audit (#145)

Target: WCAG 2.2 AA. **This is a partial baseline and controlled integrated-fixture audit, not a conformance claim.**
Parent: [#136](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/136).
The feature PRs #146–153 were open at baseline time; none is assumed implemented.
This work does not close #145 or replace #120's interaction/stakeholder acceptance.

## Pinned baseline — 2026-10-23

- Product commit: `ffb3027ee1b39a434903b9b1883907d55e52a633` (refreshed `origin/main`).
  No `ui/`, fixture, or product Python changes in this audit PR. Initial run had
  uncommitted test/documentation additions; each run attaches its actual HEAD and dirty flag.
- macOS 26.6.2 (25G83), Darwin 25.6.0 arm64; headless Chromium 156.0.8078.4;
  Playwright 1.64.1, axe-core 4.14.0, Python 3.12.9, Node 24.22.1.
- Browser plugin unavailable; repository-local Playwright fallback. No committed
  browser-test runner existed at the pin; the suite reuses `src.research_demo`
  and its canonical fixtures, not another session's server or private scripts.
- Offline fixture mode only; **no model/provider call, persistent index, or live paper**.
  Long content is a response-intercepted synthetic variant, not source-quality evidence.
- 1280×900 light/dark; keyboard flows at 1280×900 and 390×900; additional
  320×900, computed-font doubling, text-spacing, and reduced-motion probes.

## Reproduce and retain evidence

From `tests/browser`:

```sh
npm ci --ignore-scripts
npx playwright install chromium
# Python 3.10+ is required; CI uses 3.12. Point PYTHON at a suitable interpreter if needed.
python3 -m pip install beautifulsoup4 jsonschema
PYTHON=python3 npm test
```

Each worker starts and tears down an ephemeral loopback fixture server (`--port 0`).
The browser does not attach to an existing port or enable synthesis. The scanner
is injected via a test-only same-origin route; product CSP stays enabled.
The lockfile pins browser/scanner dependencies. The original baseline needed
only the Python standard library; integrated parser-produced source checks also
use the project's Beautiful Soup and jsonschema dependencies. They call no model.

`tests/browser/artifacts/report.json` retains exact HEAD/dirty flag, OS/browser/tool
versions, axe results (including **incomplete** nodes), screenshots and layout
measurements as Playwright attachments. Failure screenshots and traces are under
`artifacts/results`. Generated output is ignored, not source code.
The `Fixture accessibility regression` workflow uploads these artifacts even on
failure, retaining them for 14 days; download before expiration for a lasting run record.
The PR's Evidence section identifies the final tested head and CI run.

For an exact historical rerun, use a separate checkout of product commit
`ffb3027ee1b39a434903b9b1883907d55e52a633` with the **baseline-compatible harness**
from commit `4d242d39c42da7e6dd56bfbdd5056a04b6f164f9`. Copy only that revision's
`tests/browser` directory into the separate product checkout (for example, via
`git archive 4d242d39c42da7e6dd56bfbdd5056a04b6f164f9 tests/browser`). Do not
copy the current integrated suite onto the baseline product or switch a shared
checkout. Record both SHAs in the run record: the product SHA identifies the
app under test, not the harness. The baseline harness needs only the Python
standard library; the current suite additionally needs the parser dependencies
and `tests.source_reader_fixture` from its matching integrated product revision.

For a current integrated run, use this PR's suite and product files together
at the tested head listed in the Evidence section. Current tests require the
plain-language controls, reading preferences, and parser fixture absent from
the historical baseline. These are two distinct reproducible experiments.

## Automated baseline results and findings

Flow: fixture page → submit question → read draft/status → inspect citation
preview/source panel → dismiss → return focus; failed request → retained question → retry.

The baseline suite has 22 browser cases, plus 28 focused Python HTTP/contract tests.
WCAG-tagged axe checks reported **zero violations in the tested states**, but
**incomplete results remain**. Passing counts are not accessibility sign-off.

| Evidence | Baseline observation | Relevant criterion / follow-up |
| --- | --- | --- |
| Full/partial/abstention/no evidence/simulated provider error, both themes | Distinct states; citations only where supported; pending/unapproved label retained on drafts | 1.3.1, 4.1.3; spoken understanding remains untested |
| Delayed response, both themes | Busy state, disabled submit and polite status; completion restores submit | 4.1.3; actual AT announcement timing untested |
| Injected HTTP 503 after earlier success | Latest turn is failure, not an old answer; question retained; keyboard retry recovers | 3.3.1, 3.3.3; this is transport injection, not a live provider failure |
| Keyboard simulation, desktop/mobile widths | Tab/Enter reach citation preview and More context; panel gets heading focus; Escape closes panel and returns to citation | 2.1.1, 2.4.3; human keyboard and native mobile AT remain pending |
| Dismissal observation, both widths | Returning focus to the citation after panel Escape **reopens the citation preview**. The keyboard test records this separately; focus return alone is not a clean dismissal result | 1.4.13 / 2.4.3 investigation with #137; unresolved baseline behavior, no fix in this PR |
| Long synthetic answer/source, both themes | Preview and source panel reachable after scrolling citation into view; long source remains present | 1.4.10; not proof of reading order or preserved scientific meaning |
| axe incomplete: `#conversation` and `.source-list` | `aria-label` on generic divs without an appropriate role is not well supported; scanner did **not** certify these names | 1.3.1 / 4.1.2 investigation with #138 and #137; do not reclassify incomplete as pass |
| axe incomplete: mobile/long panel contrast | Overlapping/partially clipped elements prevented some background determinations (`blockquote`, rail note and long-panel nodes) | 1.4.3; manual/computed contrast review still required |
| Latest-answer navigation | No dedicated latest-answer control in baseline markup; sequential tab reachability does not prove efficient navigation | 2.4.1 / 2.4.6 investigation with #138; no automatic WCAG-failure conclusion from absence alone |
| 320px reflow proxy | No document or conversation horizontal overflow in full fixture; screenshot checked | 1.4.10; **not native 400% browser zoom** |
| Computed-font 200% proxy | Font sizes doubled; rendered answer/composer visible without document horizontal overflow | 1.4.4; **not native browser text-only resize** |
| Text spacing | 1.5 line height, .12em letter spacing, .16em word spacing, 2em paragraph spacing applied; no document horizontal overflow | 1.4.12; full source/math/table/export surfaces pending |
| Reduced-motion emulation | Media preference active; full state renders | 2.3.3 is AAA; preference coverage, not AA certification or a complete animation audit |

No product fix is claimed here. Preserve baseline findings and link sibling fixes
when rechecked on a new pinned integrated commit. No scanner rules are disabled,
no violations are allowlisted, and incomplete results stay in raw evidence.
The initial scanner injection failed against CSP and was fixed in the harness,
not by relaxing product policy. The initial long-content probe raced focus-triggered
scroll/preview dismissal; final probe scrolls before focus and does not scan the
transient preview. Auto-scroll preview persistence therefore remains untested.

## Controlled integrated fixture follow-up — 2026-10-23

The executable suite now follows the integrated citation activation/name,
Ctrl+Enter composer submission, numbered failure/retry and shared answer-status
contracts. It preserves the original baseline above rather than relabeling it
as a current run. No scanner rules or incomplete results are suppressed.

- **28 cases and 32 WCAG-tagged scans pass**, with zero reported violations.
  Coverage adds the plain-language fixture, parser-produced MathML/table/header
  groups at desktop/mobile widths, and persistent high-contrast preferences at
  320px with 200% text. Duplicate submission and native keyboard retry are checked.
- The mobile Tab walkthrough independently exposed the reading-preferences
  document-scroll preview defect. Its fix belongs to #139/#148, not this harness.
  A strengthened sibling regression verifies that the actual reading scroller
  moves. After repair, Escape returns focus without reopening the preview.
- A named generic source-list div was fixed with an explicit group role in
  #142/#151, removing four scanner-incomplete naming results. The remaining
  **23 incomplete rule results** are retained: 22 hidden-popup IDREF checks and
  one partially obscured MathML contrast check. Actual citation IDREF existence
  is independently asserted; that does not prove spoken behavior or conformance.
- The integrated input is the feature stack through structured-reader head
  `73c3fe42203e9fdbbef010416382ce8de08838c2`; each raw run records its actual
  checkout HEAD and dirty flag. A feature-stack run is not a claim that its
  unmerged dependencies are already on main.
- Selected-result export and real read-aloud enablement are not exercised by
  this audit's application path. Export remains a separate gated PR; read-aloud
  is isolated preparation only. Real indexed execution is still separate.

These are Chromium/fixture/viewport/media-proxy results, not the actual manual
and live-workflow gates below. Original baseline findings remain historical.

## Manual and remaining integrated gates — NOT PERFORMED

Do not mark these complete from Playwright key events, screenshots, scanner output,
source inspection, or a media-query/viewport proxy. There has been **no actual
VoiceOver walkthrough, human keyboard-only walkthrough, native 200% text resize,
or native 400% browser-zoom run** in this baseline.

For every run record: date, tester, product SHA, harness SHA, OS/browser/AT versions,
mode/data identity, viewport/theme/preferences, exact steps, expected/observed
result, finding ID/criterion, fix SHA/retest outcome, and explicitly untested cases.

| Gate | Steps / acceptance evidence required | Status / owner |
| --- | --- | --- |
| Human keyboard-only | Start at page entry; submit; reach newest answer without traversing every old turn; inspect preview and panel; dismiss via Escape and close button; verify visible/unobscured focus and correct focus return; retry after error; repeat mobile-width modal and cross-breakpoint resize | Untested; #145 after #137–140 integrate |
| Actual VoiceOver + Safari | Enable VoiceOver on macOS; navigate headings/landmarks and form labels; listen to loading/success/partial/abstention/failure status; read citations with evidence identity; enter/exit preview and panel; verify no trap, duplicate/stale announcement or loss of context; newest-answer navigation and error recovery | Untested; #145 after feature integration |
| Contrast, both themes | Check actual foreground/background ratios for body/meta/citation/selected-source/error/status text (1.4.3); focus and meaningful control boundaries (1.4.11), including hover/focus/disabled exceptions and scanner-incomplete nodes | Incomplete; #139/#145 |
| Native resize/reflow | Use browser text-only resize to 200%; actual 400% zoom from 1280px-wide window (about 320 CSS px); inspect question entry, all answer states, long content, preview/panel, controls and focus; no loss of content/function or unintended two-dimensional scrolling | Untested; #139/#145 |
| Spacing/motion/mobile | Repeat overrides with disclosures/panels, math/tables and preferences; verify motion behavior rather than only preference activation; mobile modal background inertness, focus containment, dismissal and return; test actual mobile/browser AT separately | Partial automation only; #137/#139/#142/#145 |
| Integrated features | Rebase/reconcile checks after #137–144 land; cover preference persistence, plain language/evidence association, export, optional read-aloud and unsupported capability states; do not infer these from baseline fixtures | Pending feature PRs; #145 |
| Indexed ask → understand → verify | When #130 exists, run explicitly configured real-index multi-paper supported/partial/abstention/failure cases; record index/corpus/model/config identity, source links/quotes and stage outcomes; no silent fixture fallback | Unavailable at baseline; #130/#145 |
| Semantic and stakeholder acceptance | Preserve facts vs interpretation, unsupported parts, limitations, provenance and unapproved review state across modes. Coordinate source-backed semantic judgment with #123–124 and interaction cases with #120/@latiifkaa; do not take over those issues | Not performed; respective issue owners |

Keep #145 open until integrated and actual manual evidence is recorded or scope is
explicitly resolved by the owner. CI green, a draft PR, or scanner silence does not
close any of these gates.

## Integrated follow-through — 2026-10-27

Product integration base: `c8338bb` (the #161 → #162 → #163 stack, refreshed over
main including merged #160). Audit additions were uncommitted during the initial
run and do not change application code. This is a new observation, not a rewrite
of the historical baseline above. #138 and #130 are now closed; their former
open/dependency statements describe the historical baseline only.

### Automated and source-backed results

- **41 browser checks passed**: the integrated light/dark outcome scans,
  keyboard citation/source return, structured math/table navigation, preferences,
  narrow reflow, 200% text size, spacing and reduced motion; actual-page speech
  lifecycle and presentation deadlines; native 200%/400% tab zoom; and six
  desktop/mobile source-backed saved-result walkthroughs.
- Browser plugin unavailable; repository Playwright 1.64.1 / axe 4.14.0 and
  Chromium 156.0.8078.4 used. Desktop 1280×900 and mobile 390×900; native tab zoom
  starts at 1280×1000. No page errors in the exercised interaction paths.
- Native zoom uses an isolated temporary Manifest V3 extension and Chromium's
  `chrome.tabs.setZoom/getZoom`: 2× and approximately 4×, unchanged outer window,
  halved/quartered layout width and doubled/quadrupled DPR. Floating-point zoom
  measurements use a tight numeric tolerance. No CSS zoom, viewport substitution,
  page-scale or deviceScaleFactor claim. Native 400% gives a 320-CSS-pixel layout.
  Source table jump focus, dialog dismissal/focus return and document/panel
  overflow assertions passed. Source table horizontal scrolling remains local.
- Source-backed replay: existing subscription provider generated supported,
  partial-coverage and abstention outputs from the first three pages of the
  version-pinned AI4AI-Bench PDF. Real saved results and identity-bound generated
  presentations were served by the actual replay endpoint, toggled between
  original/plain views, and source citation/quote inspection checked at 1280/390.
  No new provider/index query is performed by replay tests. Development cases,
  not held-out or independent semantic evaluation.
- #163's two pinned HTML inspections expose actual structure/fallback counts and
  source SHA-256. Against current main, structured passages improve from 17 to
  28 of 29 (AI4AI-Bench) and 10 to 39 of 42 (Pandora). Canonical passage text,
  chunk IDs and source URLs are unchanged. Counts are not fidelity certification.

### Native speech diagnostic — separate from mocked browser tests

Native installed Chrome **156.0.8078.48**, headed isolated profile, macOS 26.6.2,
synthetic fixture only. The real Web Speech API reported 180 local voices.
Answer/source playback emitted native start events; keyboard pause/resume/stop
and source dismissal cleared the actual speaking/pending queue. An `interrupted`
event follows explicit cancellation as expected. No JavaScript page errors.
No mock engine was substituted. This verifies browser/OS engine callbacks and
queue state, **not a recorded or independently heard audible result**. VoiceOver
coexistence was not exercised; no new VoiceOver acceptance claim.

Reproduce against an owned synthetic loopback server (visible Chrome may speak):

```sh
RESEARCH_URL=http://127.0.0.1:8765 AUDIT_OUTPUT=/tmp/native-speech node tests/browser/native-speech.manual.cjs
```

For source-backed replay, explicitly select retained development packets:

```sh
RESEARCH_EXAMPLES_DIR=/path/to/retained/examples PYTHON=python3 npm test
```

Packets must provide `{supported,partial,abstention}-{original,presentation}.json`;
without the explicit directory those six cases skip. Fixture/native-zoom tests
continue to run in CI without private sources, index downloads or model calls.

### Remaining acceptance gates

- VoiceOver/Safari math/table navigation and speech coexistence need actual
  native assistive-technology observation. Prior owner acceptance of #138 and
  exports does not certify these new flows.
- No independent meaning/uncertainty approval, full-corpus extraction fidelity,
  platform-wide audit, WCAG conformance, deployment or stakeholder sign-off.
- Persistent-index live-path recheck is completed separately below; source-backed
  replay and source inspection were not used as substitutes for it.

### Live persistent-index recheck — completed 2026-10-27

An audit-owned copy of the existing 877-record `arxiv_papers` index was opened
with the cached `all-MiniLM-L6-v2` encoder, offline hub settings and existing
subscription-backed `gpt-6.1-sol` route. No corpus rebuild/reindex/download or
provider fallback. Indexed-record identity:
`41c71d4bbbdc5aa40a75d03f43691439a36be11ee256dd32ff48969faf3be260`.
The same digest was observed in the earlier integration; this is a fresh browser
run against the current implementation, not reuse of that historical result.

- **1280px supported research query:** “How should AI agents be evaluated?”
  returned `summary-only`, four claims and evidence from `2608.00339v1`,
  `2605.00276v1`, `2604.00319v1`, `2604.00324v1`. Plain-language generation was
  available. Citation → source quote → Escape/focus return passed.
- **390px out-of-corpus query:** nuclear-fusion propulsion efficiency returned
  `insufficient`, zero claims, available no-claim plain view and pending/unapproved
  status, despite retrieval returning five passages. No unsupported answer was
  fabricated for that development question. This is not general abstention accuracy.
- Both runs used the actual `/api/research` path and browser rendering, retained
  result/quote/provenance envelopes, had no horizontal document overflow and no
  JavaScript page errors. They remain development observations, not held-out
  semantic evaluation, independent approval, or VoiceOver walkthroughs.

Reproduce after explicitly starting your indexed server (may call its provider):

```sh
RESEARCH_URL=http://127.0.0.1:8765 AUDIT_OUTPUT=/tmp/live-index-audit node tests/browser/live-index.manual.cjs
```

The full integrated Python suite initially passed **503 tests, 1 skipped** and
699 subtests. A subsequently added nonfinite-presentation HTTP regression passed
in the focused suite; final-head totals are recorded in the PR evidence.

Native-zoom screenshots use `chrome.tabs.captureVisibleTab` in the same disposable
profile: ordinary page screenshot capture mis-framed the surface after tab zoom.
The capture API requires all-URLs permission in that temporary test extension;
the isolated profile contains only owned synthetic loopback tabs, no user profile,
credentials or personal browsing. Captured 200%/400% compositor images were visually
inspected; focused source table content is legible and locally scrollable.

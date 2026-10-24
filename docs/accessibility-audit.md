# Accessibility baseline and integrated audit (#145)

Target: WCAG 2.2 AA. **This is a partial baseline, not a conformance claim.**
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

For an exact historical rerun, use a separate checkout of the pinned product
commit and copy this PR's `tests/browser` directory into it; do not switch a
shared checkout. Record both the product SHA and harness SHA when doing so.

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
  `3e292f9e33b7dca6f14c641060b6ec6b11f2917a`; each raw run records its actual
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

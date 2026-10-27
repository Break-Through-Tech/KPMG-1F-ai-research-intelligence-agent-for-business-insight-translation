/* Fixture-backed browser regressions. Start src.research_demo separately.
 * RESEARCH_UI_URL=http://127.0.0.1:8840 node --test tests/ui_question_entry.cjs
 * Requires an available playwright installation (see docs/accessibility-question-entry.md).
 */
const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const fs = require('node:fs');
const base = process.env.RESEARCH_UI_URL;
if (!base) throw new Error('Set RESEARCH_UI_URL to your isolated local demo server.');
let browser;
before(async () => { browser = await chromium.launch({headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome'}); });
after(async () => { await browser?.close(); });
const fixture = JSON.parse(fs.readFileSync('tests/fixtures/research/normal-v1.json', 'utf8'));
async function desk(fn, {live = false, saved = null, storageBlocked = false} = {}) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  if (storageBlocked) await page.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', {get() { throw new Error('Blocked'); }});
  });
  await page.route('**/api/config', r => r.fulfill({json: {live, ...(live ? {paper_context_id: 'paper-A'} : {})}}));
  await page.route('**/api/saved-result', r => r.fulfill({json: saved}));
  try {
    await page.goto(base);
    await page.waitForFunction(() => (!document.querySelector('#submit').disabled && document.querySelector('#submit').getAttribute('aria-disabled') !== 'true') || document.querySelector('#research-form').hidden);
    assert.equal(await page.title(), 'Research desk · 1F');
    await fn(page);
    assert.deepEqual(errors, []);
  } finally { await context.close(); }
}
async function ready(page) { await page.waitForFunction(() => (!document.querySelector('#submit').disabled && document.querySelector('#submit').getAttribute('aria-disabled') !== 'true')); }
function envelope(request, live = false) {
  const result = structuredClone(fixture);
  if (live) result.provenance = {paper_context_id: 'paper-A'};
  return {mode: live ? 'live-synthesis' : 'fixture', scenario: 'full', submitted_request: request, result};
}

test('newline default, Shift+Enter, Ctrl+Enter; suggestions are editable and never send', async () => {
  await desk(async page => {
    let requests = [];
    await page.route('**/api/demo', async r => { const body = r.request().postDataJSON(); requests.push(body); await r.fulfill({json: envelope(body)}); });
    const input = page.getByRole('textbox', {name: 'Research question'});
    await input.fill('Line one'); await input.press('End'); await input.press('Enter'); await input.press('Shift+Enter');
    assert.equal(await input.inputValue(), 'Line one\n\n'); assert.equal(requests.length, 0);
    await input.press('Control+Enter'); await ready(page);
    assert.equal(requests.length, 1); assert.equal(requests[0].query, 'Line one\n\n');
    assert.equal('history' in requests[0], false);
    const suggestion = page.getByRole('button', {name: 'Show supporting evidence', exact: true});
    await suggestion.focus(); await page.keyboard.press('Enter');
    assert.equal(await input.evaluate(e => e === document.activeElement), true);
    assert.match(await input.inputValue(), /Line one/); assert.equal(requests.length, 1);
    assert.match(await page.locator('#suggestion-note').innerText(), /independent/);
    await input.fill('Edited suggestion'); await input.press('Meta+Enter'); await ready(page);
    assert.equal(requests[1].query, 'Edited suggestion');
  });
});

test('send preference persists across reload; Shift+Enter remains multiline', async () => {
  await desk(async page => {
    let count = 0;
    await page.route('**/api/demo', async r => { count++; await r.fulfill({json: envelope(r.request().postDataJSON())}); });
    await page.getByText('Research options', {exact: true}).click();
    await page.getByLabel('Enter key').selectOption('send'); await page.reload(); await ready(page);
    assert.equal(await page.getByLabel('Enter key').inputValue(), 'send');
    const input = page.getByRole('textbox'); await input.fill('Persisted'); await input.press('End'); await input.press('Shift+Enter');
    assert.equal(count, 0); await input.press('Enter'); await ready(page); assert.equal(count, 1);
  });
});

test('IME composition, legacy 229, commit Enter, repeat and dictation input do not send', async () => {
  await desk(async page => {
    let count = 0;
    await page.route('**/api/demo', async r => { count++; await r.fulfill({json: envelope(r.request().postDataJSON())}); });
    await page.getByText('Research options', {exact: true}).click();
    await page.getByLabel('Enter key').selectOption('send');
    const input = page.getByRole('textbox'); await input.fill('日本語');
    await input.dispatchEvent('compositionstart');
    await input.dispatchEvent('keydown', {key: 'Enter', isComposing: false});
    await input.dispatchEvent('compositionend');
    await input.dispatchEvent('keydown', {key: 'Enter'});
    await input.dispatchEvent('keydown', {key: 'Enter', keyCode: 229});
    await input.dispatchEvent('keydown', {key: 'Enter', isComposing: true});
    await input.dispatchEvent('keydown', {key: 'Enter', repeat: true});
    await input.dispatchEvent('beforeinput', {inputType: 'insertFromDictation', data: ' dictated'});
    await input.dispatchEvent('input', {inputType: 'insertFromDictation', data: ' dictated'});
    assert.equal(count, 0); assert.equal(await input.inputValue(), '日本語');
  });
});

test('HTTP failure preserves original plus concurrent draft; keyboard retry restores snapshot and focus, prevents duplicate sends', async () => {
  await desk(async page => {
    let requests = [], release;
    await page.route('**/api/demo', async r => {
      requests.push(r.request().postDataJSON());
      if (requests.length === 1) await r.fulfill({status: 503, json: {error: 'Unavailable'}});
      else { await new Promise(resolve => { release = resolve; }); await r.fulfill({json: envelope(requests.at(-1))}); }
    });
    const input = page.getByRole('textbox'); await input.fill('Original question'); await input.press('Control+Enter'); await ready(page);
    assert.equal(await input.inputValue(), 'Original question');
    await input.fill('Unsent edit');
    const retry = page.getByRole('button', {name: 'Retry original question'}); await retry.focus(); await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.querySelector('#submit').getAttribute('aria-disabled') === 'true');
    assert.equal(await input.evaluate(e => e === document.activeElement), true);
    assert.equal(await input.inputValue(), 'Original question');
    await input.press('Control+Enter'); await page.locator('#research-form').evaluate(e => e.dispatchEvent(new Event('submit', {cancelable: true})));
    assert.equal(requests.length, 2); assert.equal(requests[1].query, 'Original question');
    assert.match(await page.locator('#feedback').innerText(), /Loading/);
    assert.equal(await page.locator('#output').getAttribute('aria-busy'), 'true');
    await input.fill('Draft typed while busy'); release(); await ready(page);
    assert.equal(await input.inputValue(), 'Draft typed while busy');
  });
});

test('network failure and simulated provider error both expose retry without clearing input', async () => {
  await desk(async page => {
    await page.route('**/api/demo', r => r.abort('failed'));
    const input = page.getByRole('textbox'); await input.fill('Network question'); await input.press('Control+Enter'); await ready(page);
    assert.equal(await input.inputValue(), 'Network question'); assert.equal(await page.getByRole('button', {name: 'Retry original question'}).count(), 1);
    await page.unroute('**/api/demo');
    await page.getByText('Demo options', {exact: true}).click();
    await page.locator('#scenario').selectOption('provider-error');
    await input.press('Control+Enter'); await ready(page);
    assert.equal(await input.inputValue(), 'Network question'); assert.match(await page.locator('#output').innerText(), /Simulated provider failure/);
    assert.equal(await page.getByRole('button', {name: 'Retry original question'}).count(), 2);
  });
});

test('contextual suggestions only in bound live paper mode, with existing successful history', async () => {
  await desk(async page => {
    let requests = [];
    await page.route('**/api/research', async r => { const body = r.request().postDataJSON(); requests.push(body); await r.fulfill({json: envelope(body, true)}); });
    const input = page.getByRole('textbox'); await input.fill('First'); await input.press('Control+Enter'); await ready(page);
    assert.deepEqual(requests[0].history, []);
    await page.getByRole('button', {name: 'Show the supporting evidence', exact: true}).click();
    assert.equal(requests.length, 1); assert.match(await input.inputValue(), /previous answer/);
    await input.press('Control+Enter'); await ready(page);
    assert.equal(requests[1].paper_context_id, 'paper-A'); assert.equal(requests[1].history.length, 2);
  }, {live: true});
});

test('delayed contextual retry retains original history and refuses stale cross-paper context', async () => {
  await desk(async page => {
    const requests = [];
    await page.route('**/api/research', async r => {
      const body = r.request().postDataJSON(); requests.push(body);
      if (requests.length === 2 || requests.length === 4) {
        await r.fulfill({status: 503, json: {error: 'Unavailable'}});
      } else if (requests.length === 5) {
        await r.fulfill({status: 409, json: {code: 'paper_changed', paper_context_id: 'paper-B'}});
      } else await r.fulfill({json: envelope(body, true)});
    });
    const input = page.getByRole('textbox');
    async function ask(text) { await input.fill(text); await input.press('Control+Enter'); await ready(page); }
    await ask('Answer A');
    await ask('Show the supporting evidence for the previous answer.');
    const original = structuredClone(requests[1]);
    await ask('Answer B');
    assert.equal(requests[2].history.length, 2);
    await page.getByRole('button', {name: 'Retry original question'}).click(); await ready(page);
    assert.deepEqual(requests[3], original);
    await ask('Change paper');
    const count = requests.length;
    await page.getByRole('button', {name: 'Retry original question'}).first().click();
    assert.equal(requests.length, count);
    assert.equal(await input.inputValue(), original.query);
    assert.equal(await input.evaluate(e => e === document.activeElement), true);
    assert.match(await page.locator('#feedback').innerText(), /paper changed.*review/i);
    await input.press('Control+Enter'); await ready(page);
    assert.equal(requests.at(-1).paper_context_id, 'paper-B');
    assert.deepEqual(requests.at(-1).history, []);
  }, {live: true});
});

test('paper_changed clears stale context and retry uses new identity with no previous turns', async () => {
  await desk(async page => {
    let requests = [];
    await page.route('**/api/research', async r => {
      const body = r.request().postDataJSON(); requests.push(body);
      if (requests.length === 2) await r.fulfill({status: 409, json: {code: 'paper_changed', paper_context_id: 'paper-B'}});
      else await r.fulfill({json: envelope(body, true)});
    });
    const input = page.getByRole('textbox'); await input.fill('First'); await input.press('Control+Enter'); await ready(page);
    await input.fill('Second'); await input.press('Control+Enter'); await ready(page);
    assert.match(await page.locator('#feedback').innerText(), /paper changed/i);
    assert.equal(await input.inputValue(), 'Second');
    await page.getByRole('button', {name: 'Retry original question'}).click(); await ready(page);
    assert.equal(requests[2].paper_context_id, 'paper-B'); assert.deepEqual(requests[2].history, []);
  }, {live: true});
});

test('saved replay remains read-only; input controls and suggestions hidden', async () => {
  await desk(async page => {
    assert.equal(await page.locator('#research-form').isVisible(), false);
    assert.equal(await page.locator('#entry-options').isVisible(), false);
    assert.equal(await page.locator('#question-suggestions').isVisible(), false);
  }, {saved: {...envelope({query: 'Saved question'}), mode: 'saved-real-result'}});
});

test('storage denial degrades to tab-only preference without disabling entry', async () => {
  await desk(async page => {
    assert.match(await page.locator('#preference-note').textContent(), /tab only/);
    await page.getByText('Research options', {exact: true}).click();
    await page.getByLabel('Enter key').selectOption('send');
    assert.match(await page.locator('#entry-hint').innerText(), /Enter sends/);
  }, {storageBlocked: true});
});

test('configuration failure blocks sending and explicit config retry preserves typed question', async () => {
  await desk(async page => {
    await page.route('**/api/config', r => r.fulfill({status: 503, json: {error: 'Unavailable'}}));
    await page.reload();
    const retry = page.getByRole('button', {name: 'Retry loading question entry'}); await retry.waitFor();
    assert.equal(await page.locator('#submit').isDisabled(), true);
    const input = page.getByRole('textbox'); await input.fill('Keep this question');
    await page.route('**/api/config', r => r.fulfill({json: {live: false}}));
    await retry.focus(); await page.keyboard.press('Enter'); await ready(page);
    assert.equal(await input.inputValue(), 'Keep this question');
    assert.equal(await input.evaluate(e => e === document.activeElement), true);
  });
});


test('configuration retry into live mode does not replace the draft with the example question', async () => {
  await desk(async page => {
    await page.route('**/api/config', r => r.fulfill({status: 503, json: {error: 'Unavailable'}}));
    await page.reload();
    const retry = page.getByRole('button', {name: 'Retry loading question entry'}); await retry.waitFor();
    const input = page.getByRole('textbox'); await input.fill('My actual paper question');
    await page.route('**/api/config', r => r.fulfill({json: {live: true, paper_context_id: 'paper-A'}}));
    await retry.click(); await ready(page);
    assert.equal(await input.inputValue(), 'My actual paper question');
    assert.equal(await input.evaluate(e => e === document.activeElement), true);
  });
});

test('320px keyboard entry and error retry remain reachable without horizontal overflow', async () => {
  await desk(async page => {
    await page.setViewportSize({width: 320, height: 700});
    await page.route('**/api/demo', r => r.fulfill({status: 503, json: {error: 'Unavailable'}}));
    const input = page.getByRole('textbox'); await input.fill('Small screen question'); await input.press('Control+Enter'); await ready(page);
    await input.press('Shift+Tab');
    assert.equal(await page.getByRole('button', {name: 'Jump to latest answer'}).evaluate(e => e === document.activeElement), true);
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.getByRole('button', {name: 'Retry original question'}).evaluate(e => e === document.activeElement), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), true);
  });
});

for (const width of [1280, 320]) {
  test(`single prompt: context travels in question, outer focus and retry remain usable (${width}px)`, async () => {
    await desk(async page => {
      await page.setViewportSize({width, height: 900});
      await page.emulateMedia({colorScheme: 'dark'});
      await page.route('**/api/config', r => r.fulfill({json: {
        live: true, mode: 'indexed', context_id: 'index-A', index: {count: 2},
      }}));
      await page.reload(); await ready(page);
      const input = page.getByRole('textbox', {name: 'Research question'});
      assert.equal(await input.inputValue(), '');
      assert.equal(await page.locator('#industry').count(), 0);
      assert.equal(await page.locator('#entry-options').isVisible(), false);
      await input.focus();
      const style = await input.evaluate(node => ({
        outline: getComputedStyle(node).outlineStyle,
        border: getComputedStyle(node.closest('form')).borderColor,
        primary: getComputedStyle(node).getPropertyValue('--primary').trim(),
      }));
      assert.equal(style.outline, 'none');
      assert.equal(style.border, 'rgb(155, 186, 255)');
      await page.screenshot({path: `/tmp/kpmg-composer-${width}.png`, fullPage: true});
      await page.keyboard.press('Tab');
      assert.equal(await page.locator('#submit').evaluate(node => node === document.activeElement), true);
      assert.notEqual(await page.locator('#submit').evaluate(node => getComputedStyle(node).outlineStyle), 'none');
      let body;
      await page.route('**/api/research', r => {
        body = r.request().postDataJSON();
        return r.fulfill({status: 503, json: {error: 'Injected retryable failure'}});
      });
      await input.fill('What are the business implications for banking?');
      await page.getByRole('button', {name: 'Research', exact: true}).click(); await ready(page);
      assert.equal(body.query, 'What are the business implications for banking?');
      assert.equal(body.interpret_context, true);
      assert.equal('industry' in body, false);
      assert.equal(await input.inputValue(), body.query);
      assert.equal(await page.getByRole('button', {name: 'Retry original question'}).isVisible(), true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    });
  });
}


test('indexed deadline includes the fifth provider budget', async () => {
  await desk(async page => {
    await page.route('**/api/config', r => r.fulfill({json: {
      live: true, mode: 'indexed', context_id: 'index-A', index: {count: 2},
    }}));
    await page.reload(); await ready(page);
    await page.clock.install();
    // Use clock-controlled timers for the native abort deadline; no real provider wait.
    await page.evaluate(() => {
      AbortSignal.timeout = delay => {
        const controller = new AbortController();
        setTimeout(() => controller.abort(), delay);
        return controller.signal;
      };
    });
    let release, started;
    const gate = new Promise(resolve => { release = resolve; });
    const requestStarted = new Promise(resolve => { started = resolve; });
    await page.route('**/api/research', async r => {
      started(); await gate;
      await r.fulfill({json: {...envelope(r.request().postDataJSON()), mode: 'indexed'}});
    });
    await page.getByRole('textbox').fill('What are the business implications for banking?');
    await page.getByRole('button', {name: 'Research', exact: true}).click();
    await requestStarted;
    try {
      // Five valid 260-second stages exceed the previous 1,260-second deadline.
      await page.clock.runFor(1300000);
      assert.equal(await page.locator('#output').getAttribute('aria-busy'), 'true');
    } finally { release(); }
    await ready(page);
    assert.match(await page.locator('.turn').innerText(), /Draft · Not approved/);
    assert.equal(await page.getByRole('textbox').inputValue(), '');
  });
});

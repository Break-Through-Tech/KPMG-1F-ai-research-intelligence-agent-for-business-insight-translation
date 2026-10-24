/* Focused browser regressions for #137. Requires Playwright, no provider/index. */
const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const path = require('node:path');
const fs = require('node:fs');
const {chromium} = require('playwright');
let server, browser, url;

before(async () => {
  server = spawn(process.env.PYTHON || 'python3', ['-u', '-c',
    "from http.server import ThreadingHTTPServer; from src.research_demo import DemoHandler; s=ThreadingHTTPServer(('127.0.0.1',0),DemoHandler); print('http://127.0.0.1:'+str(s.server_port),flush=True); s.serve_forever()"],
    {cwd: path.resolve(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe']});
  let errors = '';
  server.stderr.on('data', data => { errors += data; });
  url = await Promise.race([
    once(server.stdout, 'data').then(([data]) => data.toString().trim()),
    once(server, 'exit').then(() => { throw new Error(errors || 'Fixture server exited'); }),
  ]);
  browser = await chromium.launch();
});
after(async () => { await browser?.close(); server?.kill(); });

async function setup(t, width = 1280) {
  const page = await browser.newPage({viewport: {width, height: 900}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', msg => { if (['error', 'warning'].includes(msg.type())) errors.push(msg.text()); });
  t.after(async () => { await page.close(); assert.deepEqual(errors, []); });
  await page.goto(url);
  assert.equal(await page.title(), 'Research desk · 1F');
  assert.equal(new URL(page.url()).origin, url);
  await page.locator('#query').focus();
  await page.keyboard.press('Control+Enter');
  await page.locator('.citation').first().waitFor();
  assert.match(await page.locator('#output').innerText(), /Draft · Not approved/);
  return page;
}
async function focused(page, selector) {
  assert.equal(await page.locator(selector).first().evaluate(node => node === document.activeElement), true, selector);
}
async function preview(page, key = 'Enter') {
  await page.locator('.citation').first().focus();
  await page.keyboard.press(key);
  await focused(page, '.quote-close');
}
async function panel(page) {
  await preview(page);
  await page.keyboard.press('Tab'); // original URL
  await page.keyboard.press('Tab'); // inspect context
  await page.keyboard.press('Enter');
  await focused(page, '#evidence-heading');
  assert.equal(await page.locator('#evidence-panel').getAttribute('open'), '');
}
async function screenshot(page, name) {
  if (!process.env.UI_QA_ARTIFACTS) return;
  fs.mkdirSync(process.env.UI_QA_ARTIFACTS, {recursive: true});
  await page.screenshot({path: path.join(process.env.UI_QA_ARTIFACTS, name + '.png')});
}

test('citation actions expose source title and PDF page or section in accessible names', async t => {
  const page = await setup(t);
  await panel(page);
  const demo = await page.evaluate(() => structuredClone(activeDemo.demo));
  for (const location of [{page_number: 7, section: null, label: 'PDF page 7'},
    {page_number: null, section: 'Methods', label: 'Methods'},
    {page_number: null, section: null, label: 'No PDF page'}]) {
    await page.evaluate(({demo, location}) => {
      const passage = demo.result.evidence[0];
      Object.assign(passage, location, {title: 'Context-specific research paper'});
      const item = {text: 'Accessible citation fixture', chunk_ids: [passage.chunk_id], support: []};
      document.querySelector('.answer').replaceChildren(citedParagraph(item, demo, 1));
    }, {demo, location});
    const context = `Context-specific research paper, ${location.label}`;
    const citation = page.getByRole('button', {name: `Inspect citation 1, ${context}`, exact: true});
    await citation.focus();
    await citation.press('Enter');
    assert.equal(await page.getByRole('link', {name: `Open original paper, ${context}, opens in a new tab`, exact: true}).count(), 1);
    await page.getByRole('button', {name: `Inspect source context, ${context}`, exact: true}).click();
    assert.equal(await page.getByRole('link', {name: `Open example source, ${context}, opens in a new tab`, exact: true}).count(), 1);
    await page.keyboard.press('Escape');
  }
});

test('Enter/Space inspect, Tab/Shift+Tab leave preview, Escape and Close return focus', async t => {
  const page = await setup(t);
  for (const key of ['Enter', 'Space']) {
    await preview(page, key);
    assert.equal(page.context().pages().length, 1);
    assert.equal(await page.locator('.citation').first().getAttribute('aria-expanded'), 'true');
    await page.keyboard.press('Escape');
    await focused(page, '.citation');
    assert.equal(await page.locator('.citation').first().getAttribute('aria-expanded'), 'false');
  }
  await preview(page);
  await page.keyboard.press('Shift+Tab');
  await focused(page, '.citation');
  await page.keyboard.press('Enter');
  await page.keyboard.press('Tab');
  await focused(page, '.quote-actions a');
  await page.keyboard.press('Tab');
  await focused(page, '.quote-actions button');
  await page.keyboard.press('Tab');
  await focused(page, '.citation:nth-of-type(1)[data-passage="1"]');
  assert.equal(await page.locator('#citation-preview').evaluate(n => n.matches(':popover-open')), false);
  await preview(page);
  await page.keyboard.press('Enter'); // Close cited quote
  await focused(page, '.citation');
});

test('original paper action preserves source locator and opens a separate tab', async t => {
  const page = await setup(t);
  await preview(page);
  await page.context().route('https://example.com/**', route => route.fulfill({body: 'Example locator fixture — not a real paper'}));
  const expected = await page.locator('.quote-actions a').getAttribute('href');
  await page.keyboard.press('Tab');
  const popupPromise = page.waitForEvent('popup');
  await page.keyboard.press('Enter');
  const popup = await popupPromise;
  await popup.waitForLoadState();
  assert.equal(popup.url(), expected);
  await popup.close();
});

test('desktop panel is nonmodal, choices activate natively, Escape restores initiator', async t => {
  const page = await setup(t);
  await panel(page);
  assert.equal(await page.locator('#evidence-panel').evaluate(n => n.matches(':modal')), false);
  await page.keyboard.press('Tab');
  await focused(page, '#evidence-close');
  await page.keyboard.press('Tab');
  await focused(page, '.source-choice:first-child');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Space');
  await focused(page, '.source-choice:last-child');
  assert.equal(await page.locator('.source-choice:last-child').getAttribute('aria-pressed'), 'true');
  assert.equal(await page.locator('.passage .source-metadata dd').last().textContent(), 'synthetic-pdf-2');
  assert.match(await page.locator('.source-link').getAttribute('href'), /#page=2$/);
  await screenshot(page, 'desktop-source-context');
  await page.locator('#query').focus(); // desktop background remains reachable
  await focused(page, '#query');
  await page.keyboard.press('Escape');
  await focused(page, '.citation');
});

test('mobile panel contains Tab/Shift+Tab, closes by button and Escape', async t => {
  const page = await setup(t, 390);
  await panel(page);
  assert.equal(await page.locator('#evidence-panel').evaluate(n => n.matches(':modal')), true);
  await page.keyboard.press('Tab');
  await focused(page, '#evidence-close');
  for (let i = 0; i < 16; i++) {
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.querySelector('#evidence-panel').contains(document.activeElement)), true);
  }
  await page.locator('#evidence-close').focus();
  await page.keyboard.press('Shift+Tab');
  assert.equal(await page.evaluate(() => document.querySelector('#evidence-panel').contains(document.activeElement)), true);
  await screenshot(page, 'mobile-source-context');
  await page.keyboard.press('Escape');
  await focused(page, '.citation');
  await panel(page);
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  await focused(page, '.citation');
});

test('open panel survives breakpoint changes without losing focus or modality', async t => {
  const page = await setup(t);
  await panel(page);
  await page.locator('.source-choice:last-child').focus();
  await page.setViewportSize({width: 390, height: 844});
  await page.waitForFunction(() => document.querySelector('#evidence-panel').matches(':modal'));
  await focused(page, '.source-choice:last-child');
  await page.setViewportSize({width: 1280, height: 900});
  await page.waitForFunction(() => !document.querySelector('#evidence-panel').matches(':modal'));
  await focused(page, '.source-choice:last-child');
  await page.locator('#query').focus();
  await page.setViewportSize({width: 390, height: 844});
  await page.waitForFunction(() => document.querySelector('#evidence-panel').matches(':modal'));
  await focused(page, '#evidence-heading');
  await page.keyboard.press('Escape');
  await focused(page, '.citation');
});

test('result replacement and loading retain surviving panel focus; removed initiator falls back', async t => {
  const page = await setup(t);
  await panel(page);
  await page.locator('.source-choice:last-child').focus();
  // Exercise asynchronous-render boundaries directly, not a live synthesis claim.
  await page.evaluate(() => renderDemo(activeDemo.demo, activeDemo.number, document.querySelector('.answer')));
  await focused(page, '#evidence-heading');
  await page.locator('.source-choice:last-child').focus();
  await page.evaluate(() => resetEvidence('Loading replacement evidence'));
  await focused(page, '#evidence-heading');
  await page.keyboard.press('Escape');
  await focused(page, '#query'); // render removed the old citation
});

test('historical citation still opens its own evidence after a new turn', async t => {
  const page = await setup(t);
  await page.locator('#query').fill('Another fixture question');
  await page.locator('#query').press('Control+Enter');
  await page.waitForFunction(() => document.querySelectorAll('.citation').length === 6);
  await panel(page);
  assert.match(await page.locator('#evidence-content').innerText(), /Example 1/);
});

test('abstention and empty evidence remain inspectable through Details', async t => {
  const page = await setup(t);
  for (const scenario of ['insufficient', 'empty']) {
    await page.locator('.demo-settings > summary').focus();
    await page.keyboard.press('Enter');
    await page.selectOption('#scenario', scenario);
    await page.locator('#query').fill('Fixture state');
    await page.locator('#query').press('Control+Enter');
    const answer = page.locator('.answer').last();
    await answer.locator('.detail-group > details > summary').waitFor();
    await answer.locator('.detail-group > details > summary').focus();
    await page.keyboard.press('Enter');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Space');
    await focused(page, '#evidence-heading');
    assert.equal(await page.locator('.source-choice').count(), scenario === 'empty' ? 0 : 2);
    if (scenario === 'empty') assert.match(await page.locator('#evidence-content').innerText(), /No evidence to inspect/);
    await page.keyboard.press('Escape');
    assert.match(await page.evaluate(() => document.activeElement.textContent), /Inspect evidence/);
  }
});

test('narrow preview focus is visible, in viewport, and actions retain usable target sizes', async t => {
  const page = await setup(t, 320);
  await preview(page, 'Space');
  const firstCitation = await page.locator('.citation').first().boundingBox();
  assert.ok(firstCitation.width >= 44 && firstCitation.height >= 44);
  for (const selector of ['.quote-close', '.quote-actions a', '.quote-actions button']) {
    const box = await page.locator(selector).boundingBox();
    assert.ok(box.height >= 44, selector);
    assert.ok(box.x >= 0 && box.y >= 0 && box.x + box.width <= 320 && box.y + box.height <= 900, selector);
  }
  assert.equal(await page.locator('.quote-close').evaluate(n => n.matches(':focus-visible')), true);
  await screenshot(page, 'narrow-citation-preview');
  await page.keyboard.press('Escape');
  await focused(page, '.citation');
});

test('citation preview survives focus/programmatic scrolling but deliberate user scrolling dismisses it', async t => {
  const page = await setup(t, 320);
  await preview(page, 'Space');
  // Focus and layout may queue scrolling after activation. Exercise an actual
  // scroll rather than a synthetic event, and let its rendering frame finish.
  const scroll = await page.evaluate(async () => {
    const conversation = document.querySelector('#conversation');
    const scroller = getComputedStyle(conversation).overflowY !== 'visible' &&
      conversation.scrollHeight > conversation.clientHeight ? conversation : document.scrollingElement;
    await new Promise(requestAnimationFrame);
    const before = scroller.scrollTop;
    scroller.scrollTop += before > 20 ? -20 : 20;
    await new Promise(requestAnimationFrame);
    await new Promise(requestAnimationFrame);
    return {before, after: scroller.scrollTop};
  });
  assert.notEqual(scroll.after, scroll.before, 'the actual reading scroller moved');
  assert.equal(await page.locator('#citation-preview').evaluate(n => n.matches(':popover-open')), true);
  await focused(page, '.quote-close');
  const box = await page.locator('.quote-close').boundingBox();
  assert.ok(box && box.x >= 0 && box.y >= 0 && box.x + box.width <= 320 && box.y + box.height <= 900);
  await screenshot(page, 'programmatic-scroll-preview');

  // A real wheel gesture in the conversation still dismisses the preview.
  const conversationBox = await page.locator('#conversation').boundingBox();
  await page.mouse.move(conversationBox.x + conversationBox.width - 20, Math.max(20, conversationBox.y + 20));
  await page.mouse.wheel(0, 150);
  await page.waitForFunction(() => !document.querySelector('#citation-preview').matches(':popover-open'));
  await focused(page, '.citation');

  await preview(page);
  await page.keyboard.press('PageDown');
  assert.equal(await page.locator('#citation-preview').evaluate(n => n.matches(':popover-open')), false);
  await focused(page, '.citation');
});

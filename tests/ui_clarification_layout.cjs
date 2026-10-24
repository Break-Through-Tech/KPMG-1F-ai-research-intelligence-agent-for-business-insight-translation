/* Deterministic UI regression, not model-quality proof.
 * RESEARCH_UI_URL=http://127.0.0.1:9131 node --test tests/ui_clarification_layout.cjs
 * Uses the same Playwright installation as tests/ui_question_entry.cjs.
 */
const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const fs = require('node:fs');
const base = process.env.RESEARCH_UI_URL;
if (!base) throw new Error('Set RESEARCH_UI_URL to an isolated local demo server.');
const fixture = JSON.parse(fs.readFileSync('tests/fixtures/research/normal-v1.json', 'utf8'));
const prompt = 'Which part of evaluation should I focus on?';
const options = [
  {text: 'Task-specific evaluation', support: [{chunk_id: fixture.evidence[0].chunk_id, quote: fixture.evidence[0].text}]},
  {text: 'Human checks of the evidence', support: [{chunk_id: fixture.evidence[1].chunk_id, quote: fixture.evidence[1].text}]},
  {text: 'Both, with a practical evaluation plan', support: []},
];
let browser;
before(async () => { browser = await chromium.launch({headless: true}); });
after(async () => { await browser?.close(); });
async function desk(width, fn, {supported = true, retry = false, open = false} = {}) {
  const context = await browser.newContext({viewport: {width, height: 1000}, colorScheme: process.env.QA_COLOR_SCHEME || 'dark'});
  const page = await context.newPage();
  const errors = [], requests = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', e => { if (e.type() === 'error') errors.push(e.text()); });
  let session = 0, attempts = 0;
  await page.route('**/api/config', r => r.fulfill({json: {live: true, mode: 'indexed', clarification: true, context_id: 'fixture', conversation_id: `session-${++session}`, index: {count: 2}}}));
  await page.route('**/api/saved-result', r => r.fulfill({json: null}));
  await page.route('**/api/research', r => {
    const request = r.request().postDataJSON(); requests.push(request);
    if (request.action === 'resume') {
      if (retry && attempts++ === 0) return r.fulfill({json: {mode: 'indexed', scenario: 'provider-error', result: null, error: {stage: 'research', message: 'Injected failure'}, submitted_request: request}});
      return r.fulfill({json: {mode: 'fixture', scenario: 'full', submitted_request: request, result: fixture, error: null}});
    }
    return r.fulfill({json: {mode: 'indexed', scenario: 'clarification', result: null, error: null, submitted_request: request,
      clarification: {question: prompt, options: open ? [] : options.map(o => ({...o, support: supported ? o.support : []}))}, clarification_evidence: fixture.evidence}});
  });
  try {
    await page.goto(base);
    assert.equal(await page.title(), 'Research desk · 1F');
    await page.waitForFunction(() => !document.querySelector('#submit').disabled);
    await page.getByRole('textbox', {name: 'Research question', exact: true}).fill('How should the synthetic agents be evaluated?');
    await page.getByRole('button', {name: 'Search research', exact: true}).click();
    await page.getByRole('heading', {name: prompt}).waitFor();
    await fn(page, requests);
    assert.deepEqual(errors, []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  } finally { await context.close(); }
}
const idle = page => page.waitForFunction(() => document.querySelector('#output').getAttribute('aria-busy') === 'false');
for (const width of [1440, 390, 320]) {
  test(`B+C card, support rail, keyboard selection and resume at ${width}px`, async () => {
    await desk(width, async (page, requests) => {
      assert.equal(await page.locator('#output #clarification-panel').count(), 1);
      assert.equal(await page.locator('.answer-text').count(), 0);
      assert.equal(await page.getByRole('radio').evaluateAll(nodes => nodes.some(n => n.checked)), false);
      assert.equal(await page.getByRole('button', {name: 'Submit answer', exact: true}).isDisabled(), true);
      assert.equal(await page.locator('#evidence-panel').evaluate(n => n.open && !n.matches(':modal')), true);
      assert.equal(await page.locator('#evidence-content blockquote').count(), 2);
      await page.getByRole('radio').first().press('3');
      assert.equal(requests.length, 1);
      assert.equal(await page.getByRole('radio').last().isChecked(), true);
      if (process.env.QA_SCREENSHOT_DIR) {
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.screenshot({path: `${process.env.QA_SCREENSHOT_DIR}/bc-${width}.png`, fullPage: true});
      }
      await page.getByRole('button', {name: 'Close source context', exact: true}).click();
      await page.getByRole('button', {name: 'Why these options?', exact: true}).click();
      assert.equal(await page.locator('#evidence-panel').evaluate(n => n.open && !n.matches(':modal')), true);
      await page.getByRole('button', {name: 'Submit answer', exact: true}).click(); await idle(page);
      assert.equal(requests.at(-1).action, 'resume');
      assert.equal(requests.at(-1).query, options[2].text);
      assert.equal(await page.locator('#clarification-panel').isVisible(), false);
      assert.equal(await page.locator('#research-form').isVisible(), true);
      assert.equal(await page.locator('.answer details').first().locator('blockquote').count(), 2);
      assert.equal(await page.locator('#evidence-heading').innerText(), 'Source context');
      // Completed source inspection still uses the original mobile modal drawer.
      await page.getByRole('button', {name: /Inspect evidence/, includeHidden: true}).evaluate(button => {
        for (let parent = button.parentElement; parent; parent = parent.parentElement) {
          if (parent.tagName === 'DETAILS') parent.open = true;
        }
      });
      await page.getByRole('button', {name: /Inspect evidence/}).click();
      assert.equal(await page.locator('#evidence-panel').evaluate(n => n.matches(':modal')), width <= 800);
    });
  });
}
test('own answer clears choice, survives a provider failure, and retries the same session', async () => {
  await desk(390, async (page, requests) => {
    await page.getByRole('radio').first().check();
    const free = page.getByRole('textbox', {name: 'Clarification answer', exact: true});
    await free.fill('Focus on human review');
    assert.equal(await page.getByRole('radio').first().isChecked(), false);
    await free.press('Control+Enter'); await idle(page);
    assert.equal(await free.inputValue(), 'Focus on human review');
    await page.getByRole('button', {name: 'Retry original question'}).click(); await idle(page);
    assert.deepEqual(requests.at(-1), requests.at(-2));
    assert.equal(await page.locator('#clarification-panel').isVisible(), false);
  }, {retry: true});
});
test('new conversation archives support and discards old pending controls', async () => {
  await desk(1440, async page => {
    await page.setViewportSize({width: 390, height: 844});
    assert.equal(await page.locator('#evidence-panel').evaluate(n => n.matches(':modal')), false);
    await page.getByRole('button', {name: 'New research conversation'}).click(); await idle(page);
    assert.equal(await page.locator('#clarification-panel').isVisible(), false);
    assert.match(await page.locator('#output').innerText(), /Closed/);
    assert.equal(await page.locator('#output details blockquote').count(), 2);
    assert.equal(await page.locator('#evidence-panel').evaluate(n => n.open), false);
  });
});
for (const open of [false, true]) {
  test(`no support does not open a rail; ${open ? 'open-ended' : 'unsupported choices'} still resume`, async () => {
    await desk(320, async (page, requests) => {
      assert.equal(await page.locator('#evidence-panel').evaluate(n => n.open), false);
      await page.getByRole('textbox', {name: 'Clarification answer', exact: true}).fill('A precise topic');
      await page.getByRole('button', {name: 'Submit answer'}).click(); await idle(page);
      assert.equal(requests.at(-1).query, 'A precise topic');
    }, {supported: false, open});
  });
}

test('200 percent reading size keeps the narrow card and its submit reachable', async () => {
  await desk(320, async (page, requests) => {
    await page.evaluate(() => document.documentElement.dataset.readingSize = '200');
    await page.getByRole('textbox', {name: 'Clarification answer', exact: true}).fill('An accessible plan');
    await page.getByRole('button', {name: 'Submit answer'}).click(); await idle(page);
    assert.equal(requests.at(-1).query, 'An accessible plan');
  });
});

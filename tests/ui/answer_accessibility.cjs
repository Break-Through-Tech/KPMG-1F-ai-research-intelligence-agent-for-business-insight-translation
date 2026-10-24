/* Fixture-backed Chromium checks. Run against an isolated research_demo server.
 * Requires playwright on NODE_PATH; no model, index, or external paper requests.
 * This checks browser semantics and focus, not VoiceOver speech/rotor behavior.
 */
const assert = require('node:assert/strict');
const {chromium} = require('playwright');

async function main() {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport: {width: 1280, height: 900}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (['warning', 'error'].includes(message.type())) errors.push(message.text());
    });
    const base = process.env.RESEARCH_DEMO_URL || 'http://127.0.0.1:8838';
    await page.goto(base);
    assert.equal(await page.title(), 'Research desk · 1F');
    await page.waitForFunction(() => !document.querySelector('#submit').disabled);
    assert.equal(await page.locator('#feedback[role="status"]').count(), 1);
    assert.equal(await page.getByRole('button', {name: 'Jump to latest answer'}).isDisabled(), true);

    // Hold each response while the user continues reading the previous answer.
    // Observe the announcer rather than merely asserting its final text.
    await page.evaluate(() => {
      window.statusMessages = [];
      new MutationObserver(() => window.statusMessages.push(document.querySelector('#feedback').textContent))
        .observe(document.querySelector('#feedback'), {childList: true, characterData: true, subtree: true});
    });
    const cases = [
      ['full', 'ready. Draft, not approved.'],
      ['partial', 'ready. Partial draft; business translation abstained. Not approved.'],
      ['insufficient', 'abstained: insufficient support.'],
      ['empty', 'unavailable: no evidence retrieved.'],
      ['provider-error', 'failed: simulated provider error.'],
      ['plain-language', 'ready. Draft, not approved.'],
    ];
    let fixture;
    for (const [index, [scenario, outcome]] of cases.entries()) {
      let release;
      const gate = new Promise(resolve => { release = resolve; });
      await page.route('**/api/demo', async route => {
        const response = await route.fetch();
        if (scenario === 'full') fixture = await response.json();
        await gate;
        await route.fulfill({response});
      });
      await page.locator('.demo-settings summary').click();
      await page.locator('#scenario').selectOption(scenario);
      await page.getByRole('textbox', {name: 'Research question'}).fill(`Question for ${scenario}`);
      await page.getByRole('button', {name: 'View example', exact: true}).click();
      await page.waitForFunction(() => document.querySelector('#output').getAttribute('aria-busy') === 'true');
      assert.equal(await page.locator('#submit').getAttribute('aria-disabled'), 'true');
      assert.equal(await page.evaluate(() => document.activeElement.id), 'submit');
      // A second submission during loading must not create another turn.
      await page.locator('#research-form').evaluate(form => form.requestSubmit());
      assert.equal(await page.locator('.turn').count(), index + 1);
      if (index) await page.locator('#answer-1').focus();
      const before = await page.evaluate(() => ({focus: document.activeElement.id, scroll: document.querySelector('#conversation').scrollTop}));
      release();
      await page.waitForFunction(() => document.querySelector('#output').getAttribute('aria-busy') === 'false');
      assert.deepEqual(await page.evaluate(() => ({focus: document.activeElement.id, scroll: document.querySelector('#conversation').scrollTop})), before);
      assert.equal(await page.locator('#feedback[role="status"]').textContent(), `Answer ${index + 1} ${outcome} Synthetic example.`);
      assert.equal(await page.getByRole('region', {name: `Question ${index + 1}`, exact: true}).count(), 1);
      assert.equal(await page.getByRole('article', {name: `Answer ${index + 1}`, exact: true}).count(), 1);
      assert.equal(await page.locator('#output [aria-live], #output [role="status"], #output [role="log"]').count(), 0);
      const jump = page.getByRole('button', {name: 'Jump to latest answer'});
      await jump.focus();
      await page.keyboard.press(index % 2 ? 'Space' : 'Enter');
      assert.equal(await page.evaluate(() => document.activeElement.id), `answer-${index + 1}`);
      await page.unroute('**/api/demo');
    }
    const messages = await page.evaluate(() => window.statusMessages);
    assert.equal(messages.length, cases.length * 2, JSON.stringify(messages));
    for (let index = 0; index < cases.length; index++) {
      assert.equal(messages[index * 2], 'Loading local example…');
      assert.match(messages[index * 2 + 1], new RegExp(`^Answer ${index + 1} `));
    }

    const failedAnswer = cases.length + 1;

    // Transport failure keeps the question and offers the same explicit jump.
    await page.route('**/api/demo', route => route.abort());
    await page.locator('#query').fill('Keep this question');
    await page.locator('#query').press('Control+Enter');
    await page.waitForFunction(number => document.querySelector('#feedback').textContent.startsWith(`Answer ${number} failed.`), failedAnswer);
    assert.equal(await page.locator('#query').inputValue(), 'Keep this question');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'query');
    assert.equal(await page.getByRole('heading', {name: `Answer ${failedAnswer}`, exact: true}).count(), 1);
    await page.unroute('**/api/demo');

    // Saved-result bootstrap follows the same question/answer semantics.
    fixture.mode = 'saved-result';
    await page.route('**/api/saved-result', route => route.fulfill({json: fixture}));
    await page.reload();
    await page.getByRole('heading', {name: 'Answer 1', exact: true}).waitFor();
    assert.equal(await page.getByRole('region', {name: 'Question 1', exact: true}).count(), 1);
    assert.match(await page.locator('#feedback[role="status"]').textContent(), /Saved result; no live query/);
    assert.notEqual(await page.evaluate(() => document.activeElement.id), 'answer-1');
    assert.equal(await page.locator('#output [aria-busy="true"]').count(), 0);

    // Synthetic live-mode envelope: proves UI branch only, not live synthesis.
    fixture.mode = 'live-synthesis';
    fixture.result.summary.generation_method = 'cited-synthesis-v1';
    fixture.result.summary.claims[0].kind = 'interpretation';
    await page.route('**/api/config', route => route.fulfill({json: {live: true}}));
    await page.reload();
    await page.getByRole('heading', {name: 'Answer 1', exact: true}).waitFor();
    assert.equal(await page.getByRole('heading', {name: 'Interpretation', exact: true}).count(), 1);
    assert.equal(await page.getByRole('heading', {name: 'Research findings', exact: true}).count(), 1);
    assert.equal(await page.getByRole('button', {name: 'Ask paper', exact: true}).count(), 1);
    assert.equal(await page.locator('#feedback[role="status"]').textContent(), 'Answer 1 ready. Draft, not approved.');
    await page.locator('.detail-group > details > summary').click();
    await page.getByText('Assumptions, risks & limitations', {exact: true}).click();
    assert.equal(await page.getByRole('heading', {name: 'Review status', exact: true}).count(), 1);
    assert.equal(await page.getByRole('heading', {name: 'Summary limitations', exact: true}).count(), 1);

    // Exercise the live submission path with a fixture response, without a model.
    await page.route('**/api/research', route => route.fulfill({json: fixture}));
    await page.locator('#query').fill('Synthetic live follow-up');
    await page.locator('#query').press('Control+Enter');
    await page.waitForFunction(() => document.querySelector('#feedback').textContent === 'Answer 2 ready. Draft, not approved.');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'query');
    await page.unroute('**/api/research');
    await page.route('**/api/research', route => route.fulfill({status: 409, json: {code: 'paper_changed', paper_context_id: 'fixture-new-paper'}}));
    await page.locator('#query').fill('Question retained after paper change');
    await page.locator('#query').press('Control+Enter');
    await page.waitForFunction(() => document.querySelector('#feedback').textContent.startsWith('Paper changed.'));
    assert.equal(await page.locator('#query').inputValue(), 'Question retained after paper change');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'query');
    await page.unroute('**/api/research');

    // Restore a successful turn for screenshots and responsive keyboard checks.
    await page.reload();
    await page.getByRole('heading', {name: 'Answer 1', exact: true}).waitFor();

    // Keep screenshots outside the checkout; opt in via a private local path.
    if (process.env.QA_SCREENSHOT_DIR) {
      await page.screenshot({path: `${process.env.QA_SCREENSHOT_DIR}/answer-desktop.png`});
      await page.setViewportSize({width: 390, height: 844});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.getByRole('button', {name: 'Jump to latest answer'}).focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.evaluate(() => document.activeElement.id), 'answer-1');
      await page.screenshot({path: `${process.env.QA_SCREENSHOT_DIR}/answer-mobile.png`});
    }
    // The intentional aborted transport is the only expected browser error.
    assert.deepEqual(errors.filter(error => !error.includes('net::ERR_FAILED') && !error.includes('409 (Conflict)')), []);
    console.log(`PASS: ${cases.length} fixture outcomes, transport failure, saved replay, synthetic live submission and paper-change recovery; Chromium ${browser.version()}`);
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });

// Offline browser evidence only: never a VoiceOver, live-index, or conformance claim.
const {test: base, expect} = require('@playwright/test');
const {spawn, execFileSync} = require('node:child_process');
const {once} = require('node:events');
const os = require('node:os');
const path = require('node:path');

const root = path.resolve(__dirname, '../..');
const axePath = require.resolve('axe-core/axe.min.js');
const test = base.extend({
  // A dedicated ephemeral loopback server per worker; never attach to a sibling's port.
  deskURL: [async ({}, use) => {
    const server = spawn(process.env.PYTHON || 'python3',
      ['-m', 'src.research_demo', '--port', '0'], {cwd: root});
    let stderr = '';
    server.stderr.on('data', data => { stderr += data; });
    try {
      const url = await new Promise((resolve, reject) => {
        let stdout = '';
        const timeout = setTimeout(() => reject(new Error(`Server startup timed out: ${stderr}`)), 10000);
        server.once('error', error => { clearTimeout(timeout); reject(error); });
        server.once('exit', code => { clearTimeout(timeout); reject(new Error(`Server exited ${code}: ${stderr}`)); });
        server.stdout.on('data', data => {
          stdout += data;
          const match = stdout.match(/http:\/\/127\.0\.0\.1:\d+/);
          if (match) { clearTimeout(timeout); resolve(match[0]); }
        });
      });
      await use(url);
    } finally {
      if (server.exitCode === null) { server.kill(); await once(server, 'exit'); }
    }
  }, {scope: 'worker'}],
  page: async ({page, deskURL}, use, info) => {
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await info.attach('environment', {body: JSON.stringify({
      commit: execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root}).toString().trim(),
      dirty: Boolean(execFileSync('git', ['status', '--porcelain'], {cwd: root}).toString().trim()),
      os: `${os.type()} ${os.release()} ${os.arch()}`,
      browser: page.context().browser().version(), mode: 'fixture; no provider or index',
      playwright: require('@playwright/test/package.json').version,
      axe: require('axe-core/package.json').version,
    }, null, 2), contentType: 'application/json'});
    await page.goto(deskURL);
    await expect(page).toHaveTitle('Research desk · 1F');
    await expect(page.getByRole('heading', {name: /Research desk/})).toBeVisible();
    await expect(page.locator('#submit')).toBeEnabled();
    await use(page);
    // Accept only the deliberately injected HTTP status, not arbitrary failure-page errors.
    const unexpectedErrors = info.title.includes('transport failure')
      ? errors.filter(error => !/Failed to load resource:.*503/.test(error)) : errors;
    expect(unexpectedErrors).toEqual([]);
    await info.attach('console-errors', {body: JSON.stringify(errors), contentType: 'application/json'});
  },
});

async function choose(page, state = 'full', query = 'Accessibility fixture question') {
  await page.getByText('Demo options', {exact: true}).click();
  await page.getByLabel('Example state').selectOption(state);
  await page.getByRole('textbox', {name: 'Research question'}).fill(query);
  await page.getByRole('button', {name: 'View example'}).click();
  await expect(page.locator('#output')).toHaveAttribute('aria-busy', 'false');
  return page.locator('.turn').last();
}

async function scan(page, info, label) {
  // Axe retains a manual-review result for hidden popup IDREFs. Independently
  // check actual DOM references without suppressing that scanner result.
  const brokenPopupRefs = await page.locator('.citation').evaluateAll(nodes => nodes
    .filter(node => !document.getElementById(node.getAttribute('aria-controls')))
    .map(node => node.getAttribute('aria-controls')));
  expect(brokenPopupRefs).toEqual([]);
  // Test-only same-origin response: keep the product's CSP enabled and unchanged.
  if (!await page.evaluate(() => Boolean(window.axe))) {
    await page.route('**/__a11y/axe.js', route => route.fulfill({
      path: axePath, contentType: 'text/javascript'}));
    await page.addScriptTag({url: '/__a11y/axe.js'});
  }
  const results = await page.evaluate(async () => axe.run(document, {
    runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']},
  }));
  await info.attach(`axe-${label}`, {body: JSON.stringify(results, null, 2), contentType: 'application/json'});
  expect(results.violations.map(v => ({id: v.id, impact: v.impact,
    targets: v.nodes.map(n => n.target)})), `${label}: inspect attached axe report, including incomplete checks`).toEqual([]);
}

for (const theme of ['light', 'dark']) {
  test.describe(theme, () => {
    test.use({colorScheme: theme});
    for (const state of ['full', 'plain-language', 'partial', 'insufficient', 'empty', 'provider-error']) {
      test(`${state}: rendered state and WCAG-tagged scan`, async ({page}, info) => {
        const turn = await choose(page, state);
        if (state === 'provider-error') {
          await expect(turn).toContainText('No provider was called; no draft was produced.');
          await expect(turn).not.toContainText('Draft · Not approved');
        } else {
          await expect(turn).toContainText('Draft · Not approved');
          await expect(turn.locator('.citation')).toHaveCount({full: 3, 'plain-language': 4, partial: 2, insufficient: 0, empty: 0}[state]);
        }
        if (['partial', 'insufficient', 'empty'].includes(state))
          await expect(turn).toContainText('No supported business recommendations.');
        if (['insufficient', 'empty'].includes(state))
          await expect(turn).toContainText('No supported research claims.');
        await scan(page, info, state);
        if (state === 'full' || state === 'partial') {
          await turn.getByText('Details', {exact: true}).click();
          await turn.getByText('Assumptions, risks & limitations', {exact: true}).click();
          await expect(turn).toContainText('No reviewer has approved this draft.');
          await scan(page, info, `${state}-expanded-limitations`);
        }
        await info.attach(`${theme}-${state}`, {body: await page.screenshot(), contentType: 'image/png'});
      });
    }

    test('loading: busy state then completed draft', async ({page}, info) => {
      let release, requests = 0;
      const gate = new Promise(resolve => { release = resolve; });
      await page.route('**/api/demo', async route => { requests++; await gate; await route.continue(); });
      try {
        await page.getByRole('button', {name: 'View example'}).click();
        await expect(page.locator('#output')).toHaveAttribute('aria-busy', 'true');
        await expect(page.locator('#submit')).toBeDisabled();
        await expect(page.locator('#feedback')).toContainText('Loading local example');
        await expect(page.locator('#submit')).toBeFocused();
        await page.locator('#research-form').evaluate(form => form.requestSubmit());
        await expect(page.locator('.turn')).toHaveCount(1);
        expect(requests).toBe(1);
        await scan(page, info, 'loading');
      } finally { release(); }
      await expect(page.locator('#output')).toHaveAttribute('aria-busy', 'false');
      await expect(page.locator('#submit')).toBeEnabled();
    });

    test('transport failure: question retained and keyboard retry recovers', async ({page}, info) => {
      const query = 'Keep this question after failure';
      await choose(page); // Keep an earlier successful turn to test stale-answer separation.
      await page.route('**/api/demo', route => route.fulfill({status: 503,
        contentType: 'application/json', body: JSON.stringify({error: 'Injected offline failure'})}));
      const failed = await choose(page, 'full', query);
      await expect(failed.getByRole('heading', {name: 'Answer 2', exact: true})).toBeVisible();
      await expect(failed).toContainText('Could not load the local example');
      await expect(failed.locator('.citation')).toHaveCount(0);
      await expect(page.getByRole('textbox')).toHaveValue(query);
      await expect(page.locator('#feedback')).toContainText('retry');
      await scan(page, info, 'transport-failure');
      await page.unroute('**/api/demo');
      await failed.getByRole('button', {name: 'Retry original question'}).focus();
      await page.keyboard.press('Enter');
      await expect(page.locator('.turn')).toHaveCount(3);
      await expect(page.locator('.turn').last()).toContainText('Draft · Not approved');
      await expect(page.getByRole('textbox')).toHaveValue('');
      await expect(page.getByRole('textbox')).toBeFocused();
    });

    test('long content: source, preview, and draft stay inspectable', async ({page}, info) => {
      await page.route('**/api/demo', async route => {
        const response = await route.fetch();
        const envelope = await response.json();
        // Synthetic stress variant of the shared fixture, not a long real-paper run.
        const text = 'Long synthetic passage for reading and source inspection. '.repeat(180);
        envelope.result.evidence[0].text = text;
        envelope.result.summary.claims[0].text = text;
        await route.fulfill({response, json: envelope});
      });
      await choose(page);
      const citation = page.locator('.citation').first();
      await citation.scrollIntoViewIfNeeded();
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      await citation.press('Enter');
      await expect(page.getByRole('dialog', {name: 'Citation preview'})).toBeVisible();
      await page.getByRole('button', {name: /^Inspect source context,/}).click();
      await expect(page.getByRole('dialog', {name: 'Source context'})).toBeVisible();
      await expect(page.locator('.passage .source-reading')).toContainText('Long synthetic passage');
      await scan(page, info, 'long-panel');
      await info.attach(`${theme}-long-panel`, {body: await page.screenshot(), contentType: 'image/png'});
    });
  });
}

for (const width of [1280, 390]) {
  test(`keyboard citation → preview → panel → Escape returns focus (${width}px)`, async ({page}, info) => {
    await page.setViewportSize({width, height: 900});
    // Keyboard-only entry and tab search, no programmatic focus for this walkthrough.
    await page.keyboard.press('Tab');
    await expect(page.locator('.skip')).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('textbox')).toBeFocused();
    await page.keyboard.press('Control+Enter');
    await expect(page.locator('.citation').first()).toBeVisible();
    let reached = false;
    for (let i = 0; i < 30; i++) {
      await page.keyboard.press('Tab');
      reached = await page.locator('.citation').first().evaluate(node => node === document.activeElement);
      if (reached) break;
    }
    expect(reached, 'First citation reachable by Tab').toBe(true);
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog', {name: 'Citation preview'})).toBeVisible();
    await expect(page.getByRole('button', {name: 'Close cited quote'})).toBeFocused();
    await page.keyboard.press('Tab'); // Original paper link (do not leave fixture page).
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', {name: /^Inspect source context,/})).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#evidence-heading')).toBeFocused();
    await scan(page, info, 'keyboard-panel');
    await info.attach(`panel-${width}`, {body: await page.screenshot(), contentType: 'image/png'});
    await page.keyboard.press('Escape');
    await expect(page.locator('#evidence-panel')).not.toBeVisible();
    await expect(page.locator('.citation').first()).toBeFocused();
    await expect(page.locator('#citation-preview')).not.toBeVisible();
    await info.attach('dismissal-observation', {body: JSON.stringify({
      previewReopenedOnFocusReturn: await page.locator('#citation-preview').evaluate(node => node.matches(':popover-open')),
    }), contentType: 'application/json'});
  });
}

for (const width of [1280, 390]) {
  test(`integrated structured source relationships (${width}px)`, async ({page}, info) => {
    await page.setViewportSize({width, height: 900});
    // Producer/parser fixture, not invented DOM or a fetched real paper.
    const fixture = JSON.parse(execFileSync(process.env.PYTHON || 'python3',
      ['-m', 'tests.source_reader_fixture'], {cwd: root}).toString());
    await page.route('**/api/demo', route => route.fulfill({json: fixture}));
    await choose(page);
    await page.locator('.citation').first().press('Enter');
    await page.getByRole('button', {name: /^Inspect source context,/}).click();
    const panel = page.locator('#evidence-panel');
    await expect(panel.locator('.source-exact-quote')).toHaveText(fixture.result.summary.claims[0].support[0].quote);
    await expect(panel.getByRole('columnheader')).toHaveCount(3);
    await expect(panel.locator('math mfrac[linethickness="0"]')).toHaveCount(1);
    await expect(panel.locator('.source-reading figure')).toHaveCount(2);
    await expect(panel.locator('.source-reading figure').first().locator('figcaption')).toHaveCount(0);
    await expect(panel.getByText(/Source-supplied image description: Two/)).toHaveCount(1);
    expect(await panel.locator('td').first().evaluate(cell => cell.headers.split(' ')
      .every(id => document.getElementById(id)?.tagName === 'TH'))).toBe(true);
    await scan(page, info, 'structured-source');
    await info.attach(`structured-${width}`, {body: await page.screenshot(), contentType: 'image/png'});
    await panel.getByRole('button', {name: 'Return to answer'}).first().press('Enter');
    await expect(page.locator('.citation').first()).toBeFocused();
  });
}

for (const theme of ['contrast-light', 'contrast-dark']) {
  test(`integrated reading preferences: ${theme}`, async ({page}, info) => {
    await page.setViewportSize({width: 320, height: 900});
    await page.getByText('Reading preferences', {exact: true}).click();
    await page.getByLabel('Theme', {exact: true}).selectOption(theme);
    await page.getByLabel('Text size', {exact: true}).selectOption('200');
    await page.getByLabel('Line spacing', {exact: true}).selectOption('wide');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await expect(page.locator('html')).toHaveAttribute('data-reading-size', '200');
    await choose(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await scan(page, info, `preferences-${theme}`);
    await info.attach(theme, {body: await page.screenshot(), contentType: 'image/png'});
  });
}

for (const mode of ['reflow-320', 'text-200', 'text-spacing', 'reduced-motion']) {
  test(`reading-mode probe: ${mode}`, async ({page}, info) => {
    if (mode === 'reflow-320') await page.setViewportSize({width: 320, height: 900});
    if (mode === 'reduced-motion') await page.emulateMedia({reducedMotion: 'reduce'});
    await choose(page);
    if (mode === 'text-200') {
      // Computed-font doubling is a stress proxy, NOT native browser text-only zoom.
      await page.evaluate(() => {
        const sizes = [...document.querySelectorAll('body *')].map(node =>
          [node, parseFloat(getComputedStyle(node).fontSize)]);
        for (const [node, size] of sizes) node.style.setProperty('font-size', `${size * 2}px`, 'important');
      });
    }
    if (mode === 'text-spacing') {
      await page.route('**/__a11y/spacing.css', route => route.fulfill({contentType: 'text/css', body: `
        * {line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important;}
        p {margin-bottom: 2em !important;}`}));
      await page.addStyleTag({url: '/__a11y/spacing.css'});
    }
    await expect(page.getByRole('textbox')).toBeVisible();
    await expect(page.locator('#submit')).toBeVisible();
    await expect(page.locator('.turn')).toContainText('Draft · Not approved');
    const measurements = await page.evaluate(() => ({
      viewport: {width: innerWidth, height: innerHeight},
      documentWidth: document.documentElement.scrollWidth,
      conversationWidth: document.querySelector('#conversation').clientWidth,
      conversationScrollWidth: document.querySelector('#conversation').scrollWidth,
      reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
      overflow: [...document.querySelectorAll('body *')]
        .filter(node => node.clientWidth > 0 && node.scrollWidth > node.clientWidth + 2)
        .map(node => ({tag: node.tagName, id: node.id, className: node.className,
          width: node.clientWidth, scrollWidth: node.scrollWidth})),
    }));
    await info.attach('layout-measurements', {body: JSON.stringify(measurements, null, 2), contentType: 'application/json'});
    await info.attach(mode, {body: await page.screenshot(), contentType: 'image/png'});
    // Measure nested overflow separately; document width alone does not prove reflow.
    expect(measurements.documentWidth).toBeLessThanOrEqual(measurements.viewport.width);
    if (mode === 'reduced-motion') expect(measurements.reducedMotion).toBe(true);
    await scan(page, info, mode);
  });
}

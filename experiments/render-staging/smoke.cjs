/* node smoke.cjs <python> <image-context> <empty-state-dir> <playwright> <chrome> [--business-intent] */
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {createInterface} = require('node:readline');
const path = require('node:path');
const [python, image, state, playwright, executablePath] = process.argv.slice(2);
const businessIntent = process.argv.includes('--business-intent');
const {chromium} = require(playwright);

async function launch() {
  const child = spawn(python, ['-B', path.join(__dirname, 'smoke_server.py'), image, state,
    ...(businessIntent ? ['--business-intent'] : [])],
    {env: {...process.env, OMP_NUM_THREADS: '1', MKL_NUM_THREADS: '1', OPENBLAS_NUM_THREADS: '1',
      HF_HUB_OFFLINE: '1', TRANSFORMERS_OFFLINE: '1', HF_HUB_DISABLE_PROGRESS_BARS: '1'},
      stdio: ['ignore', 'pipe', 'inherit']});
  const rl = createInterface({input: child.stdout});
  try {
    const address = await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Cold startup exceeded 120 seconds')), 120000);
      const done = (fn, value) => { clearTimeout(timeout); fn(value); };
      rl.once('line', line => {
        try { done(resolve, JSON.parse(line)); } catch (error) { done(reject, error); }
      });
      child.once('error', error => done(reject, error));
      child.once('exit', code => done(reject, new Error('Test worker exited: ' + code)));
    });
    return {...address, child};
  } catch (error) {
    child.kill();
    throw error;
  }
}

async function smokeBusiness() {
  const service = await launch();
  let browser;
  try {
    const {origin} = service;
    browser = await chromium.launch({executablePath, headless: true});
    const context = await browser.newContext({viewport: {width: 1440, height: 960},
      httpCredentials: {username: 'reviewer', password: 'local-fixture-only-not-a-secret', origin}, reducedMotion: 'reduce'});
    const page = await context.newPage();
    page.setDefaultTimeout(25000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const businessRequests = [];
    page.on('request', request => {
      if (request.url() === origin + '/api/business') businessRequests.push(request.postDataJSON());
    });
    const responseFor = route => page.waitForResponse(response => response.url() === origin + '/api/' + route);
    const ready = responseFor('config');
    await page.goto(origin);
    assert.equal((await (await ready).json()).business_translation, true);

    const ask = async question => {
      await page.locator('#query').fill(question);
      const response = responseFor('research');
      await page.locator('#composer button[type=submit]').click();
      const envelope = await (await response).json();
      assert.equal(envelope.result?.summary?.status, 'ok', JSON.stringify(envelope.error));
      assert.ok(envelope.library.version.id);
      return envelope;
    };
    const finding = page.getByText(/35–46% to 68–78%/);
    const appliedResponse = responseFor('business');
    const applied = await ask('What are the business implications of the CU-DPO accuracy results for AI model routing in financial services?');
    assert.equal(applied.business_auto, true);
    const panel = page.locator('.answer-business').last();
    await finding.first().waitFor();
    await panel.getByText(/Generating business insights/).waitFor();
    assert.equal(await page.locator('.turn').last().getByRole('button', {name: 'Generate business insights', exact: true}).first().isDisabled(), true);
    const translated = await (await appliedResponse).json();
    assert.equal(translated.result.business_insight.industry, 'financial services');
    assert.equal(translated.result.provenance.business_translation.generation_kind, 'fixture');
    assert.deepEqual(translated.result.summary, applied.result.summary);
    assert.deepEqual(translated.result.evidence, applied.result.evidence);
    assert.equal(translated.library.version.number, 2);
    await panel.getByText('Compare routing accuracy on the review queue.').waitFor();
    assert.equal(await panel.locator('details[open]').count(), 0);
    assert.equal(await page.locator('#view-tabs [data-tab="answer"]').getAttribute('aria-selected'), 'true');
    await page.screenshot({path: path.join(state, 'business-answer-desktop.png')});
    await panel.locator('button.citation').first().press('Enter');
    await page.locator('#inspector').waitFor();
    await page.keyboard.press('Escape');
    await page.setViewportSize({width: 390, height: 844});
    await panel.getByRole('heading', {name: 'Business insights'}).scrollIntoViewIfNeeded();
    assert.equal(await panel.locator('.insight-card').evaluate(node => node.scrollWidth <= node.clientWidth + 2), true);
    await page.screenshot({path: path.join(state, 'business-answer-mobile.png')});
    await page.setViewportSize({width: 1440, height: 960});

    const failedResponse = responseFor('business');
    const research = await ask('What are the business implications of the CU-DPO accuracy results for AI model routing in banking?');
    const failed = await (await failedResponse).json();
    assert.equal(failed.error.stage, 'business');
    assert.deepEqual(failed.result.summary, research.result.summary);
    await page.locator('.answer-business').last().getByText(failed.error.message, {exact: true}).waitFor();
    const academic = await ask('By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?');
    assert.equal(academic.business_auto, undefined);
    await page.locator('.turn').last().getByRole('button', {name: 'Generate business insights', exact: true}).first().waitFor();
    assert.deepEqual(businessRequests.map(request => request.automatic), [true, true]);
    assert.deepEqual(errors, []);
    console.log('Offline Standard S2 + business fixtures passed: progressive answer, financial services, citations, mobile, failure, optional academic flow, and one dispatch per eligible answer.');
  } finally {
    await browser?.close();
    service.child.kill();
  }
}

async function main() {
  let service = await launch();
  let browser;
  try {
    let {origin} = service;
    const auth = {Authorization: 'Basic ' + service.auth};
    assert.equal((await fetch(origin + '/healthz')).status, 200);
    for (const file of ['/', '/app.js', '/api/config', '/api/briefs']) {
      assert.equal((await fetch(origin + file)).status, 401);
    }
    for (const file of ['/mock-api.js', '/.env', '/snapshot/manifest.json', '/artifacts/bundle/parents.jsonl']) {
      assert.equal((await fetch(origin + file, {headers: auth})).status, 404);
    }
    const post = (route, body, source = origin) => fetch(origin + route, {
      method: 'POST', headers: {...auth, Origin: source, 'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    assert.equal((await post('/api/research', {}, 'https://untrusted.example')).status, 403);
    assert.equal((await post('/api/agentic-research', {})).status, 404);
    const config = await (await fetch(origin + '/api/config', {headers: auth})).json();
    assert.equal(config.live, true);
    assert.equal(config.mode, 'indexed');
    assert.equal(config.library, true);
    assert.equal((await post('/api/research', {context_id: config.context_id, query: 'test',
      risk_assessment: true, industry: 'banking'})).status, 400);

    browser = await chromium.launch({executablePath, headless: true});
    const context = await browser.newContext({viewport: {width: 1440, height: 960},
      httpCredentials: {username: 'reviewer', password: 'local-fixture-only-not-a-secret', origin},
      reducedMotion: 'reduce'});
    const page = await context.newPage();
    page.setDefaultTimeout(25000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(origin);
    await page.waitForFunction(() => /live/i.test(document.querySelector('#mode-banner').textContent));
    assert.equal(await page.locator('#engine-field').isVisible(), false);
    const question = 'By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?';
    await page.locator('#query').fill(question);
    const received = page.waitForResponse(response => response.url() === origin + '/api/research');
    const began = performance.now();
    await page.locator('#composer button[type=submit]').click();
    const response = await received;
    assert.equal(response.status(), 200);
    const envelope = await response.json();
    const duration = ((performance.now() - began) / 1000).toFixed(2);
    assert.equal(envelope.mode, 'indexed');
    assert.equal(envelope.result.summary.status, 'ok');
    assert.equal(envelope.result.provenance.generation.provider, 'scripted-fixture');
    assert.equal(envelope.result.approved, false);
    assert.equal(envelope.result.provenance.index_path, 'demo-100');
    assert.equal(envelope.result.provenance.retrieval.reranker, 'ms-marco-MiniLM-L6-v2');
    assert.ok(envelope.library.brief.id);
    await page.getByText(/35–46% to 68–78%/).first().waitFor();
    const citation = page.locator('#thread button.citation:visible').first();
    await citation.click();
    await page.locator('#inspector').waitFor();
    assert.match(await page.locator('#inspector').innerText(), /seven base models/);
    assert.ok((await page.locator('#inspector').getByRole('link', {name: /open.*paper/i}).first().getAttribute('href'))
      .startsWith('https://arxiv.org/html/2602.00931v2'));
    await page.keyboard.press('Escape');
    await page.locator('#inspector').waitFor({state: 'hidden'});
    await page.locator('summary:visible').filter({hasText: /All evidence tables|Data and charts/}).click();
    const table = page.locator('figure.ev-figure:not(.compact):visible').filter({hasText: 'Full table shown (16 rows)'});
    await table.waitFor();
    await page.getByText('Unresolved discrepancy.', {exact: true}).first().waitFor({state: 'attached'});
    assert.equal(await table.locator('tbody tr').count(), 16);
    assert.equal(await table.getByRole('link', {name: /open .* in the paper/i}).getAttribute('href'),
      'https://arxiv.org/html/2602.00931v2#S3.T2');
    await table.getByRole('tab', {name: /^Chart/}).click();
    const point = table.locator('.ev-chart').getByRole('button', {name: /open source/i}).first();
    await point.focus();
    await point.press('Enter');
    // Retrieved table rows use the citation inspector. Rows loaded to complete
    // the table use the standalone row inspector. Both must highlight the cell.
    const chartSource = page.locator('#inspector');
    await chartSource.locator('td.hit').first().waitFor();
    assert.match(await chartSource.innerText(), /Cell source ID|Selected cell: \S+/);
    await page.keyboard.press('Escape');
    await page.locator('#inspector').waitFor({state: 'hidden'});

    const {brief, version} = envelope.library;
    await page.locator('#side-library').click();
    const opening = page.waitForResponse(result => result.url() === origin + '/api/briefs/' + brief.id);
    await page.locator('#brief-list').getByRole('button', {name: /CU-DPO/}).click();
    assert.equal((await opening).status(), 200);
    await page.locator('#thread .cited-text:visible').filter({hasText: /35–46% to 68–78%/}).first().waitFor();
    const review = await post('/api/briefs/' + brief.id + '/reviews', {
      version_id: version.id, fingerprint: version.fingerprint,
      reviewer: 'Local smoke reviewer', decision: 'revise', notes: 'Offline review-path smoke test.',
    });
    assert.equal(review.status, 200);
    assert.equal((await review.json()).library.reviews[0].decision, 'revise');
    const reviewed = await (await fetch(origin + '/api/briefs/' + brief.id, {headers: auth})).json();
    const exports = await page.evaluate(({draft, reviewed}) => ['md', 'html'].map(format => [
      AnswerExport.build(draft, format), AnswerExport.build(reviewed, format),
      AnswerExport.build({...reviewed, library: {...reviewed.library, version: {...reviewed.library.version, fingerprint: 'stale'}}}, format),
    ]), {draft: envelope, reviewed});
    for (const [draft, reviewedExport, stale] of exports) {
      assert.match(draft, /No matching review decision/);
      assert.match(reviewedExport, /Recorded review for this version: Changes requested/);
      assert.match(stale, /No matching review decision/);
    }
    assert.deepEqual(errors, []);
    console.log('Browser, auth, exact quote, full chart, saved brief and review passed. Startup ' +
      service.seconds + 's; real retrieval + scripted generation request ' + duration + 's.');

    service.child.kill();
    await new Promise(resolve => service.child.once('exit', resolve));
    service = await launch();
    origin = service.origin;
    const reopened = await fetch(origin + '/api/briefs/' + brief.id, {
      headers: {Authorization: 'Basic ' + service.auth},
    });
    const saved = await reopened.json();
    assert.equal(reopened.status, 200);
    assert.equal(saved.library.version.fingerprint, version.fingerprint);
    assert.equal(saved.library.reviews[0].decision, 'revise');
    console.log('SQLite brief and review survived a complete server restart.');
  } finally {
    await browser?.close();
    service.child.kill();
  }
}
(businessIntent ? smokeBusiness() : main()).catch(error => { console.error(error); process.exitCode = 1; });

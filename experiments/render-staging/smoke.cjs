/* node smoke.cjs <python> <image-context> <empty-state-dir> <playwright> <chrome> */
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {createInterface} = require('node:readline');
const path = require('node:path');
const [python, image, state, playwright, executablePath] = process.argv.slice(2);
const {chromium} = require(playwright);

async function launch() {
  const child = spawn(python, ['-B', path.join(__dirname, 'smoke_server.py'), image, state],
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
    await page.locator('#inspector').getByText('Cell source ID', {exact: true}).waitFor();
    assert.match(await page.locator('#inspector').innerText(), /Cell source ID/);
    assert.ok(await page.locator('#inspector td.hit').count());
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
main().catch(error => { console.error(error); process.exitCode = 1; });





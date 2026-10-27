// Offline library behavior only; no live-provider, source-certification or VoiceOver claim.
const {test: base, expect} = require('@playwright/test');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {mkdtemp, rm} = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const root = path.resolve(__dirname, '../..');
const test = base.extend({
  desk: async ({}, use) => {
    const folder = await mkdtemp(path.join(os.tmpdir(), 'brief-library-'));
    let server;
    async function stop() {
      if (server && server.exitCode === null) { server.kill(); await once(server, 'exit'); }
    }
    async function start() {
      server = spawn(process.env.PYTHON || 'python3', ['-m', 'src.research_demo', '--port', '0',
        '--library', path.join(folder, 'library.sqlite3')], {cwd: root});
      return new Promise((resolve, reject) => {
        let stderr = '';
        server.stderr.on('data', d => { stderr += d; });
        const timeout = setTimeout(() => reject(new Error(`Startup timeout: ${stderr}`)), 10000);
        server.once('error', e => { clearTimeout(timeout); reject(e); });
        server.once('exit', code => { clearTimeout(timeout); if (code) reject(new Error(stderr)); });
        server.stdout.on('data', d => {
          const match = String(d).match(/http:\/\/127\.0\.0\.1:\d+/);
          if (match) { clearTimeout(timeout); resolve(match[0]); }
        });
      });
    }
    try { await use({url: await start(), stop, start}); }
    finally { await stop(); await rm(folder, {recursive: true, force: true}); }
  },
});

test('save → review → new pending version → reopen → archive/restore → restart', async ({page, desk}) => {
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(desk.url);
  await page.locator('#submit').click();
  const answer = () => page.locator('.answer').last();
  await expect(answer().locator('.brief-controls summary')).toHaveText('Saved brief · Version 1');
  await answer().locator('.brief-controls summary').click();
  await answer().getByLabel('Reviewer name').fill('Fixture reviewer');
  await answer().getByRole('button', {name: 'Record review', exact: true}).click();
  await expect(answer().locator('.answer-head')).toContainText('approved by human reviewer');
  const {briefs} = await (await page.request.get(`${desk.url}/api/briefs`)).json();
  const saved = await (await page.request.get(`${desk.url}/api/briefs/${briefs[0].id}`)).json();
  await answer().getByLabel('Import a new version JSON').setInputFiles({name: 'version.json',
    mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(saved))});
  await expect(answer().locator('.brief-controls summary')).toHaveText('Saved brief · Version 2');
  await expect(answer().locator('.answer-head')).toContainText('Not approved');
  await expect(answer().getByLabel('Review history').locator('li')).toHaveCount(0);
  await answer().getByLabel('Brief title').fill('Retained fixture brief');
  await answer().getByRole('button', {name: 'Rename brief', exact: true}).click();
  await expect(answer().locator('.brief-controls')).toContainText('Retained fixture brief');
  await page.locator('#library-open').click();
  await page.getByRole('button', {name: 'Retained fixture brief', exact: true}).click();
  await expect(page.locator('.answer')).toHaveCount(2);
  await expect(answer()).toContainText('No new research executed');
  await answer().locator('.brief-controls summary').click();
  await answer().getByLabel('Version history').selectOption(saved.library.version.id);
  await answer().getByRole('button', {name: 'Open selected version', exact: true}).click();
  await expect(page.locator('.answer')).toHaveCount(3);
  await expect(answer().locator('.answer-head')).toContainText('approved by human reviewer');
  await answer().locator('.brief-controls summary').click();
  await expect(answer()).toContainText('Historical version');
  await expect(answer().getByRole('button', {name: 'Record review', exact: true})).toHaveCount(0);
  await page.locator('#library-open').click();
  await page.getByRole('button', {name: 'Retained fixture brief', exact: true}).click();
  await expect(page.locator('.answer')).toHaveCount(4);
  await answer().locator('.brief-controls summary').click();
  await answer().getByRole('button', {name: 'Archive brief', exact: true}).click();
  await expect(answer().getByRole('button', {name: 'Restore brief', exact: true})).toBeVisible();
  await page.locator('#library-open').click();
  await expect(page.locator('#library-status')).toContainText('No saved briefs');
  await page.locator('#brief-archived').check();
  await page.getByRole('button', {name: 'Retained fixture brief', exact: true}).click();
  await expect(page.locator('.answer')).toHaveCount(5);
  await answer().locator('.brief-controls summary').click();
  await answer().getByRole('button', {name: 'Restore brief', exact: true}).click();
  await expect(answer().getByRole('button', {name: 'Archive brief', exact: true})).toBeVisible();
  await desk.stop();
  await page.goto(await desk.start());
  await page.locator('#library-open').click();
  await page.getByRole('button', {name: 'Retained fixture brief', exact: true}).click();
  await expect(answer()).toContainText('No new research executed');
  expect(errors).toEqual([]);
});

test('storage warning retains answer and saves without another research request', async ({page, desk}) => {
  let requests = 0;
  await page.route('**/api/demo', async route => {
    requests++;
    const response = await route.fetch();
    const body = await response.json();
    delete body.library;
    body.library_error = 'Answer retained but not saved. Injected storage failure.';
    await route.fulfill({response, json: body});
  });
  await page.goto(desk.url);
  await page.locator('#submit').click();
  await expect(page.locator('.brief-controls')).toHaveAttribute('open', '');
  await expect(page.locator('.brief-controls .error')).toContainText('not saved');
  await expect(page.locator('.answer-text')).toBeVisible();
  await page.getByRole('button', {name: 'Save as separate brief', exact: true}).click();
  await expect(page.locator('.brief-controls summary')).toHaveText('Saved brief · Version 1');
  expect(requests).toBe(1);
});

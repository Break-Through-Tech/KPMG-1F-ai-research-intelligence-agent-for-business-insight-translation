/* Run with: node smoke.cjs <site> <playwright module> <chromium executable> */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require(process.argv[3]);

async function main() {
  const root = path.resolve(process.argv[2]);
  const config = JSON.parse(await fs.readFile(path.join(root, 'vercel.json'), 'utf8'));
  const types = {'.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
    '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2'};
  const server = http.createServer(async (request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(root + path.sep) || !['HEAD', 'GET'].includes(request.method)) {
      response.writeHead(405).end();
      return;
    }
    try {
      const bytes = await fs.readFile(file);
      const headers = Object.fromEntries(config.headers[0].headers.map(({key, value}) => [key, value]));
      response.writeHead(200, {...headers, 'Content-Type': types[path.extname(file)] || 'text/plain'});
      response.end(request.method === 'HEAD' ? undefined : bytes);
    } catch {
      response.writeHead(404).end();
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  let browser;
  try {
    browser = await chromium.launch({executablePath: process.argv[4], headless: true});
    for (const [width, height] of [[1440, 960], [390, 844]]) {
      const context = await browser.newContext({viewport: {width, height}, hasTouch: width < 500, reducedMotion: 'reduce'});
      const page = await context.newPage();
      page.setDefaultTimeout(8000);
      const errors = [];
      const external = [];
      const badResponses = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
      page.on('response', res => { if (!res.ok()) badResponses.push(res.status() + ' ' + res.url()); });
      context.on('request', req => { if (!req.url().startsWith(origin + '/') && !req.url().startsWith('data:')) external.push(req.url()); });
      const response = await page.goto(origin);
      assert.equal(response.status(), 200);
      assert.equal(response.headers()['x-robots-tag'], 'noindex, nofollow');
      await page.getByRole('heading', {name: 'Recorded research briefs'}).waitFor();
      assert.match(await page.locator('#mode-banner').innerText(), /replay of recorded research/i);
      assert.equal(await page.locator('#composer').isVisible(), false);
      assert.equal(await page.locator('#new-research').isVisible(), false);
      await page.locator('#recent-briefs').getByRole('button', {name: /CU-DPO/}).click();
      await page.getByText(/35–46% to 68–78%/).first().waitFor();
      await page.locator('summary:visible').filter({hasText: 'All evidence tables'}).click();
      const table = page.locator('figure.ev-figure:not(.compact):visible').filter({hasText: 'Full table shown (16 rows)'}).first();
      await table.waitFor();
      assert.equal(await table.locator('tbody tr').count(), 16);
      const cellsByID = new Map();
      const originalCells = await table.locator('tbody [data-source-id]').evaluateAll(nodes =>
        nodes.map(node => [node.dataset.sourceId, node.innerText.trim()]));
      for (const [id, value] of originalCells) cellsByID.set(id, value);
      const cell = table.locator('tbody button[data-source-id]').first();
      const cellId = await cell.getAttribute('data-source-id');
      await cell.click();
      const inspector = page.locator('#inspector');
      await inspector.waitFor();
      assert.match(await inspector.innerText(), /Cell source ID/i);
      assert.ok((await inspector.innerText()).includes(cellId));
      await page.locator('#inspector-close').click();
      await inspector.waitFor({state: 'hidden'});
      const original = await table.getByRole('link', {name: /open .* in the paper/i}).getAttribute('href');
      assert.equal(original, 'https://arxiv.org/html/2602.00931v2#S3.T2');
      await table.getByRole('tab', {name: /^Chart/}).click();
      await table.locator('.ev-chart').waitFor();
      const point = table.locator('.ev-chart').getByRole('button', {name: /open source/i}).first();
      assert.ok(await point.count(), 'chart should offer a keyboard-accessible source target');
      await point.focus();
      await point.press('Enter');
      await page.locator('#inspector').waitFor();
      assert.match(await inspector.innerText(), /source|table/i);
      const selectedId = await inspector.locator('dd').evaluateAll(fields =>
        fields.find(field => field.previousElementSibling?.textContent === 'Cell source ID')?.textContent);
      assert.ok(cellsByID.has(selectedId), 'chart selected a cell that is in the same complete table');
      assert.equal((await inspector.locator('td.hit').innerText()).trim(), cellsByID.get(selectedId));
      assert.ok(await page.locator('#inspector a[href*="2602.00931v2"]').count());
      await page.keyboard.press('Escape');
      await page.locator('#inspector').waitFor({state: 'hidden'});
      const findingCitation = page.locator('#thread button.citation:visible').first();
      await findingCitation.click();
      const quote = page.locator('#citation-preview:popover-open');
      await quote.waitFor();
      assert.match(await quote.innerText(), /strategy selection accuracy from 35–46% to 68–78%/i);
      assert.ok((await quote.getByRole('link', {name: /open original paper/i}).getAttribute('href')).startsWith('https://arxiv.org/html/2602.00931v2'));
      await quote.getByRole('button', {name: /inspect source context/i}).click();
      await page.locator('#inspector').waitFor();
      await page.locator('#inspector-close').click();
      await page.locator('#inspector').waitFor({state: 'hidden'});
      await page.locator('#library-open').click();
      await page.locator('#brief-list').getByRole('button', {name: /Fin-RATE/}).click();
      await page.getByText(/requires additional Fin-RATE results or conclusion passages/).first().waitFor();
      await page.locator('summary:visible').filter({hasText: 'All evidence tables'}).click();
      await page.locator('figure.ev-figure:not(.compact):visible').filter({hasText: 'Full table shown'}).first().waitFor();
      assert.equal(await page.locator('figure.ev-figure:not(.compact):visible [data-view="chart"]:enabled').count(), 0);
      assert.equal(await page.locator('#library-import input').count(), 0);
      const status = await page.evaluate(async () => {
        const api = window.StagingReplay.fetch;
        return [
          (await api('/api/research', {method: 'POST'})).status,
          (await api('/api/briefs', {method: 'POST'})).status,
          (await api('/api/evidence-table?chunk_id=unknown&index=wrong')).status,
          (await api('/api/briefs?q=not-a-recorded-topic')).ok,
        ];
      });
      assert.deepEqual(status, [405, 405, 404, true]);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      assert.deepEqual(errors, []);
      assert.deepEqual(badResponses, []);
      assert.deepEqual(external, []);
      console.log(width + 'px: replay, 16-row table, chart source target, abstention, blocked writes, and no console/network errors passed');
      await context.close();
    }
  } finally {
    await browser?.close();
    server.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });

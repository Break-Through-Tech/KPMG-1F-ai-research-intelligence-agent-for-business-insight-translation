const {test, expect} = require('@playwright/test');
const {spawn, execFileSync} = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
let server, url;
test.beforeAll(async () => {
  server = spawn(process.env.PYTHON || 'python3', ['-m', 'src.research_demo', '--no-library', '--port', '0'], {cwd: root});
  url = await new Promise((resolve, reject) => {
    server.once('exit', code => reject(new Error(`Server exited ${code}`)));
    server.stdout.on('data', data => {const match = String(data).match(/http:\/\/127.0.0.1:\d+/); if (match) resolve(match[0]);});
  });
});
test.afterAll(() => server?.kill());
for (const indexed of [false, true]) {
  test(`optional presentation gets an additional provider-stage deadline (${indexed ? 'indexed' : 'single-paper'})`, async ({page}) => {
    await page.addInitScript(() => {
      window.requestDeadlines = [];
      const original = AbortSignal.timeout;
      AbortSignal.timeout = ms => {requestDeadlines.push(ms); return original(ms);};
    });
    await page.route('**/api/config', route => route.fulfill({json:{live:true, plain_language:true,
      ...(indexed ? {mode:'indexed', context_id:'test-context', index:{count:2}} : {})}}));
    const envelope = JSON.parse(execFileSync(process.env.PYTHON || 'python3', ['-c',
      "import json;from src.research_demo import load_demo;print(json.dumps(load_demo({'query':'Q'},'plain-language')))"], {cwd:root}).toString());
    envelope.mode = indexed ? 'indexed' : 'live-synthesis';
    await page.route('**/api/research', route => route.fulfill({json:envelope}));
    await page.goto(url);
    await page.getByRole('textbox', {name:'Research question'}).fill('Explain the research');
    await page.locator('#submit').click();
    await expect(page.locator('.answer')).toContainText('Research findings');
    expect(await page.evaluate(() => requestDeadlines)).toContain(indexed ? 1860000 : 630000);
    await page.getByRole('radio', {name:'Plain language', exact:true}).check();
    await expect(page.locator('.answer-text')).toContainText('Synthetic agents need to be tested for the specific task.');
    await expect(page.locator('.answer')).toContainText('Draft · Not approved');
  });
}

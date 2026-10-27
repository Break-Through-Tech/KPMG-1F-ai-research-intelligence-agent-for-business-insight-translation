// Native Chrome tab zoom via an isolated extension. No CSS zoom/DPR substitution.
const {test, expect, chromium} = require('@playwright/test');
const {spawn, execFileSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
let server, url;
test.beforeAll(async () => {
  server = spawn(process.env.PYTHON || 'python3', ['-m', 'src.research_demo', '--port', '0'], {cwd:root});
  url = await new Promise((resolve, reject) => {
    server.once('exit', code => reject(new Error(`Server exited ${code}`)));
    server.stdout.on('data', data => {const match = String(data).match(/http:\/\/127.0.0.1:\d+/); if (match) resolve(match[0]);});
  });
});
test.afterAll(() => server?.kill());
for (const zoom of [2, 4]) {
  test(`native tab zoom ${zoom * 100}% retains source focus and reflow`, async ({}, info) => {
    const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'research-native-zoom-'));
    const extension = path.join(folder, 'extension'); fs.mkdirSync(extension);
    fs.writeFileSync(path.join(extension, 'manifest.json'), JSON.stringify({manifest_version:3,
      name:'Isolated research zoom verification',version:'1.0',permissions:['tabs'],background:{service_worker:'background.js'}}));
    fs.writeFileSync(path.join(extension, 'background.js'), 'chrome.runtime.onInstalled.addListener(()=>{});');
    let context;
    try {
      context = await chromium.launchPersistentContext(path.join(folder, 'profile'), {channel:'chromium',headless:true,
        viewport:{width:1280,height:1000},args:[`--disable-extensions-except=${extension}`, `--load-extension=${extension}`]});
      const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
      const page = await context.newPage();
      page.on('console', m => {if (m.type()==='error') console.log(m.text());});
      const errors = []; page.on('pageerror', e => errors.push(e.message));
      const fixture = JSON.parse(execFileSync(process.env.PYTHON || 'python3', ['-m','tests.source_reader_fixture'], {cwd:root}).toString());
      await page.route('**/api/demo', route => route.fulfill({json:fixture}));
      await page.goto(url);
      await page.locator('#submit').click();
      const metrics = () => page.evaluate(() => ({width:innerWidth,height:innerHeight,outerWidth,outerHeight,dpr:devicePixelRatio}));
      const before = await metrics();
      const api = await worker.evaluate(async ({url,zoom}) => {
        const tabs = await chrome.tabs.query({});
        const tab = tabs.find(t => t.url?.startsWith(url));
        if (!tab) throw new Error('Exact test-origin tab missing');
        await chrome.tabs.setZoom(tab.id, zoom);
        return {zoom:await chrome.tabs.getZoom(tab.id),settings:await chrome.tabs.getZoomSettings(tab.id)};
      }, {url,zoom});
      await expect.poll(async () => (await metrics()).width).toBe(Math.round(before.width / zoom));
      const after = await metrics();
      expect(api.zoom).toBeCloseTo(zoom, 6);
      expect(after.outerWidth).toBe(before.outerWidth);
      expect(after.outerHeight).toBe(before.outerHeight);
      expect(after.dpr).toBeCloseTo(before.dpr * zoom, 6);
      const citation = page.locator('.citation').first();
      await citation.press('Enter');
      await page.getByRole('button', {name:/^Inspect source context,/}).click();
      const panel = page.locator('#evidence-panel');
      await expect(panel).toBeVisible();
      await panel.getByRole('button', {name:/^Go to source table 1/}).press('Enter');
      await expect(panel.getByRole('region', {name:/^Source table 1:/})).toBeFocused();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      expect(await panel.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
      await info.attach('native-zoom', {body:JSON.stringify({commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root}).toString().trim(),
        browser:context.browser()?.version(),mode:'synthetic structured-source fixture; no provider/index/VoiceOver',before,after,api,errors},null,2),contentType:'application/json'});
      const cdp = await context.newCDPSession(page);
      const layout = await cdp.send('Page.getLayoutMetrics');
      const visual = layout.cssVisualViewport;
      const shot = await cdp.send('Page.captureScreenshot', {format:'png',fromSurface:true,captureBeyondViewport:false,
        clip:{x:visual.pageX,y:visual.pageY,width:visual.clientWidth,height:visual.clientHeight,scale:1}});
      await info.attach(`native-${zoom*100}`, {body:Buffer.from(shot.data,'base64'),contentType:'image/png'});
      await info.attach('native-layout', {body:JSON.stringify(layout),contentType:'application/json'});
      await page.keyboard.press('Escape');
      await expect(panel).not.toBeVisible();
      await expect(citation).toBeFocused();
      expect(errors).toEqual([]);
    } finally {
      await context?.close();
      fs.rmSync(folder, {recursive:true,force:true});
    }
  });
}

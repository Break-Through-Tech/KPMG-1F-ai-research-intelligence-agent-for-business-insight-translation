// Opt-in source-backed saved results, never auto-discover private/local research.
const {test, expect} = require('@playwright/test');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const folder = process.env.RESEARCH_EXAMPLES_DIR;
test.skip(!folder, 'Set RESEARCH_EXAMPLES_DIR to explicitly selected retained development packets. No provider called.');
for (const label of ['supported', 'partial', 'abstention']) {
  for (const width of [1280, 390]) {
    test(`${label} source-backed replay preserves plain/original/provenance (${width})`, async ({page}, info) => {
      const original = path.join(folder, `${label}-original.json`);
      const presentation = path.join(folder, `${label}-presentation.json`);
      const result = JSON.parse(fs.readFileSync(original));
      const candidate = JSON.parse(fs.readFileSync(presentation));
      expect(candidate.fixture).toBe(false);
      const server = spawn(process.env.PYTHON || 'python3', ['-m','src.research_demo','--port','0',
        '--result',original,'--presentation',presentation], {cwd:path.resolve(__dirname,'../..')});
      try {
        const url = await new Promise((resolve,reject) => {
          server.once('exit', code => reject(new Error(`Server exited ${code}`)));
          server.stdout.on('data',data=>{const m=String(data).match(/http:\/\/127.0.0.1:\d+/);if(m)resolve(m[0]);});
        });
        const errors=[]; page.on('pageerror', e=>errors.push(e.message));
        await page.setViewportSize({width,height:900});
        await page.goto(url);
        const answer=page.locator('.answer');
        await expect(answer).toContainText('Draft · Not approved');
        await expect(answer).toContainText('Meaning and uncertainty review pending.');
        await page.getByRole('radio',{name:'Plain language',exact:true}).check();
        if(candidate.claims.length) await expect(answer.locator('.answer-text')).toContainText(candidate.claims[0].text);
        else await expect(answer).toContainText('No supported research claims.');
        await page.getByRole('radio',{name:'Technical / original',exact:true}).check();
        if(result.summary.claims.length) {
          await expect(answer.locator('.answer-text')).toContainText(result.summary.claims[0].text);
          await answer.locator('.citation').first().press('Enter');
          await page.getByRole('button',{name:/^Inspect source context,/}).click();
          await expect(page.locator('#evidence-panel')).toContainText('2608.20318v1');
          await expect(page.locator('#evidence-panel .source-exact-quote').first()).toContainText(result.summary.claims[0].support[0].quote);
          await page.keyboard.press('Escape');
        }
        expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
        expect(errors).toEqual([]);
        await info.attach('replay-provenance',{body:JSON.stringify({mode:'saved source-backed development result; no new provider/index execution',result_identity:candidate.result_identity,browser:page.context().browser().version(),width}),contentType:'application/json'});
        await info.attach(`${label}-${width}`,{body:await page.screenshot(),contentType:'image/png'});
      } finally {server.kill();}
    });
  }
}

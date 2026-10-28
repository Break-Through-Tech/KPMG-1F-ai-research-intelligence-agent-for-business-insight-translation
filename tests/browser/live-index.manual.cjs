// Explicit opt-in live development walkthrough. May invoke the server's configured provider.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const origin = process.env.RESEARCH_URL;
const output = process.env.AUDIT_OUTPUT;
if (!origin || !output || !['127.0.0.1','localhost'].includes(new URL(origin).hostname)) {
  throw new Error('Set RESEARCH_URL to your explicitly configured loopback indexed server and AUDIT_OUTPUT. This runs real queries.');
}
fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);
  const config=await (await page.request.get(origin+'/api/config')).json();
  assert.equal(config.mode,'indexed');assert.equal(config.live,true);
  fs.writeFileSync(path.join(output,'indexed-config.json'),JSON.stringify(config,null,2));
  for (const [label,query,width] of [
   ['supported','How should AI agents be evaluated?',1280],
   ['abstention','What measured nuclear-fusion propulsion efficiency do these papers establish?',390],
  ]) {
   await page.setViewportSize({width,height:900});
   await page.getByRole('textbox',{name:'Research question'}).fill(query);
   const responsePromise=page.waitForResponse(r=>r.url().endsWith('/api/research')&&r.request().method()==='POST',{timeout:1900000});
   await page.locator('#submit').click();
   const response=await responsePromise;
   const envelope=await response.json();
   fs.writeFileSync(path.join(output,`indexed-${label}-envelope.json`),JSON.stringify(envelope,null,2));
   assert.equal(response.status(),200);
   assert(envelope.result,'No accepted result; inspect saved failure, do not reinterpret failure as abstention');
   assert.equal(envelope.result.approved,false);assert.equal(envelope.result.human_review.status,'pending');
   const answer=page.locator('.answer').last();
   if (!(await page.locator('#reading-explanation').isVisible())) {
    await page.locator('.reading-settings > summary').click();
   }
   await page.locator('#reading-explanation').selectOption('plain');
   assert.equal(envelope.plain_language.status,'available');
   if(envelope.result.summary.claims.length){
    await answer.locator('.citation').first().press('Enter');
    await page.getByRole('button',{name:/^Inspect source context,/}).click();
    assert(await page.locator('#evidence-panel .source-exact-quote').count()>0);
    await page.keyboard.press('Escape');
    assert(await answer.locator('.citation').first().evaluate(el=>el===document.activeElement));
   }
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   await page.screenshot({path:path.join(output,`indexed-${label}-${width}.png`)});
   const record={label,width,scenario:envelope.scenario,summary:envelope.result.summary.status,
    paperIDs:[...new Set(envelope.result.evidence.map(p=>p.arxiv_id))],claims:envelope.result.summary.claims.length,
    presentation:envelope.plain_language.status,browser:browser.version(),errors,mode:'live existing persistent-index development query; not held-out semantic acceptance'};
   fs.writeFileSync(path.join(output,`indexed-${label}-receipt.json`),JSON.stringify(record,null,2));
   console.log(JSON.stringify(record));
  }
  assert.deepEqual(errors,[]);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

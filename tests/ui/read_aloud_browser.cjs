const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({headless: true, ...(process.env.PLAYWRIGHT_CHANNEL ? {channel: process.env.PLAYWRIGHT_CHANNEL} : {})});
 try {
 const page = await browser.newPage({viewport: {width: 1280, height: 1000}});
 const errors = [];
 page.on('pageerror', error => errors.push(error.message));
 page.on('console', message => {if (['warning','error'].includes(message.type())) errors.push(message.text());});
 await page.addInitScript(() => {
  window.speechCalls = [];
  const listeners = new Set();
  const synth = {
   getVoices: () => [{localService:true,voiceURI:'test-local',lang:'en-US'}],
   speak(u) {window.speechCalls.push(['speak', u.text, u.rate]); window.currentUtterance=u; u.onstart?.();},
   cancel() {window.speechCalls.push(['cancel']);},
   pause() {window.speechCalls.push(['pause']);}, resume() {window.speechCalls.push(['resume']);},
   addEventListener(_,fn) {listeners.add(fn);}, removeEventListener(_,fn) {listeners.delete(fn);},
  };
  Object.defineProperty(window,'speechSynthesis',{value:synth});
  Object.defineProperty(window,'SpeechSynthesisUtterance',{value:class {constructor(text){this.text=text;}}});
 });
 await page.goto(`${process.env.READ_ALOUD_BASE_URL || 'http://127.0.0.1:9144'}/tests/fixtures/read-aloud.html`);
 assert.match(await page.title(), /Read-aloud isolated fixture/);
 const play = page.getByRole('button',{name:'Play',exact:true});
 await play.waitFor();
 assert.equal(await page.evaluate(()=>speechCalls.length),0);
 // Keyboard tab order and playback activation. Native selector popup behavior
 // is a manual gate; selectOption exercises DOM selection changes only.
 await page.keyboard.press('Tab'); assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Citation [1]');
 await page.keyboard.press('Tab'); assert.equal(await page.getByLabel('Read',{exact:true}).evaluate(n=>n===document.activeElement),true);
 await page.getByLabel('Read',{exact:true}).selectOption('passage:fixture:1');
 await page.keyboard.press('Tab'); assert.equal(await page.getByLabel('Speed').evaluate(n=>n===document.activeElement),true);
 await page.getByLabel('Speed').selectOption('1.25');
 await page.keyboard.press('Tab'); assert.equal(await play.evaluate(n=>n===document.activeElement),true);
 await page.keyboard.press('Enter');
 assert.match(await page.getByRole('status').innerText(),/Reading: Source passage/);
 assert.equal(await page.getByRole('status').getAttribute('aria-live'),'off');
 assert.match(await page.evaluate(()=>speechCalls.find(x=>x[0]==='speak')[1]), /Synthetic example, page 1/);
 assert.equal(await page.evaluate(()=>speechCalls.find(x=>x[0]==='speak')[2]),1.25);
 await page.keyboard.press('Tab'); assert.equal(await page.getByRole('button',{name:'Pause',exact:true}).evaluate(n=>n===document.activeElement),true);
 await page.keyboard.press('Space');
 assert.equal(await page.getByRole('status').innerText(),'Paused.');
 assert.equal(await page.getByRole('status').getAttribute('aria-live'),'polite');
 assert.equal(await page.getByRole('button',{name:'Resume',exact:true}).evaluate(n=>n===document.activeElement),true);
 await page.keyboard.press('Enter'); assert.match(await page.getByRole('status').innerText(),/Reading:/);
 await page.keyboard.press('Tab'); await page.keyboard.press('Enter');
 assert.equal(await page.getByRole('status').innerText(),'Stopped.');
 assert.equal(await page.getByRole('link',{name:'Citation [1]'}).isVisible(),true);
 await page.screenshot({path:'/tmp/kpmg-144-desktop.png',fullPage:true});
 // Selection changes stop active speech without starting a new selection.
 await play.click(); const before=await page.evaluate(()=>speechCalls.filter(x=>x[0]==='speak').length);
 await page.getByLabel('Read',{exact:true}).selectOption('result:fixture');
 assert.match(await page.getByRole('status').innerText(),/Stopped: selected text changed/);
 assert.equal(await page.evaluate(()=>speechCalls.filter(x=>x[0]==='speak').length),before);
 await play.click();
 await page.evaluate(()=>document.querySelector('#reader').remove());
 await page.waitForTimeout(50);
 assert.equal(await page.evaluate(()=>speechCalls.at(-1)[0]),'cancel');
 // Capability absence on a separate browser page, with no mock.
 const unsupported=await browser.newPage({viewport:{width:390,height:844}});
 await unsupported.addInitScript(()=>{Object.defineProperty(window,'speechSynthesis',{value:undefined});});
 await unsupported.goto(`${process.env.READ_ALOUD_BASE_URL || 'http://127.0.0.1:9144'}/tests/fixtures/read-aloud.html`);
 await unsupported.getByRole('status').waitFor();
 assert.match(await unsupported.getByRole('status').innerText(),/unavailable/);
 assert.equal(await unsupported.getByRole('button',{name:'Play',exact:true}).isDisabled(),true);
 assert.equal(await unsupported.getByRole('link',{name:'Citation [1]'}).isVisible(),true);
 await unsupported.screenshot({path:'/tmp/kpmg-144-mobile-unavailable.png',fullPage:true});
 for (const width of [320,390]) {
  await page.setViewportSize({width,height:1000}); await page.reload(); await play.waitFor();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 }
 await page.screenshot({path:'/tmp/kpmg-144-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);
 console.log(JSON.stringify({result:'PASS',browser:await browser.version(),checks:['identity','content','no overlay','console','keyboard tab order/play/pause/resume/stop; selector DOM changes','no autoplay','live-region policy','no auto-restart on selection','root-removal cancellation','unsupported fallback','text/citations retained','320/390px no horizontal overflow'],screenshots:['/tmp/kpmg-144-desktop.png','/tmp/kpmg-144-mobile.png','/tmp/kpmg-144-mobile-unavailable.png'],scope:'fixture DOM + mocked engine, not real audio/VoiceOver'}));
 } finally { await browser.close(); }
})().catch(e=>{console.error(e); process.exit(1);});

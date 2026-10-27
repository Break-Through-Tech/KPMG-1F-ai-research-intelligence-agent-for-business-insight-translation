const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');
const origin = process.env.RESEARCH_URL || 'http://127.0.0.1:8765';
if (!['127.0.0.1','localhost'].includes(new URL(origin).hostname)) throw new Error('Use an owned loopback fixture server');
const output = process.env.AUDIT_OUTPUT || fs.mkdtempSync(path.join(os.tmpdir(), 'research-native-speech-'));
fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false});
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{
  window.nativeSpeechEvents=[];
  const native=speechSynthesis.speak.bind(speechSynthesis);
  speechSynthesis.speak=utterance=>{
   for(const type of ['start','end','error','pause','resume']) utterance.addEventListener(type,event=>nativeSpeechEvents.push({type,error:event.error||null}));
   native(utterance);
  };
 });
 try {
  await page.goto(origin);
  assert.equal(await page.locator('#demo-note').textContent(), 'Synthetic demo · Questions are not executed.');
  await page.locator('#submit').click();
  await page.waitForSelector('.read-aloud');
  await page.waitForFunction(()=>speechSynthesis.getVoices().some(v=>v.localService===true),{},{timeout:12000}).catch(()=>{});
  const voices=await page.evaluate(()=>speechSynthesis.getVoices().filter(v=>v.localService).map(v=>({name:v.name,lang:v.lang})));
  const report={browser:browser.version(),mode:'synthetic fixture; actual native Chrome Web Speech API; no mock engine',localVoices:voices.length,events:[],checks:[],audibleCapture:false,voiceOver:'not exercised'};
  if(voices.length){
   const audio=page.locator('.answer .read-aloud');
   await audio.getByRole('button',{name:'Play',exact:true}).press('Enter');
   await page.waitForFunction(()=>nativeSpeechEvents.some(e=>e.type==='start'),{},{timeout:15000});
   await audio.getByRole('button',{name:'Pause',exact:true}).press('Space');
   assert.equal(await audio.getByRole('button',{name:'Resume',exact:true}).isEnabled(),true);
   await audio.getByRole('button',{name:'Resume',exact:true}).press('Enter');
   await audio.getByRole('button',{name:'Stop',exact:true}).press('Enter');
   assert.equal(await page.evaluate(()=>speechSynthesis.speaking||speechSynthesis.pending),false);
   report.checks.push('native answer start event, keyboard pause/resume/stop, engine queue cleared');
   await page.locator('.citation').first().press('Enter');
   await page.getByRole('button',{name:/^Inspect source context,/}).click();
   const before=await page.evaluate(()=>nativeSpeechEvents.filter(e=>e.type==='start').length);
   await page.locator('#evidence-panel .read-aloud').getByRole('button',{name:'Play',exact:true}).press('Enter');
   await page.waitForFunction(count=>nativeSpeechEvents.filter(e=>e.type==='start').length>count,before,{timeout:15000});
   await page.keyboard.press('Escape');
   assert.equal(await page.evaluate(()=>speechSynthesis.speaking||speechSynthesis.pending),false);
   report.checks.push('native source start event, dismissal cancels actual engine queue');
   report.events=await page.evaluate(()=>nativeSpeechEvents);
  } else report.blocker='Chrome reports no local voices; no synthetic engine substitution';
  report.errors=errors;
  await page.screenshot({path:path.join(output,'native-speech.png')});
  fs.writeFileSync(path.join(output,'native-speech.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

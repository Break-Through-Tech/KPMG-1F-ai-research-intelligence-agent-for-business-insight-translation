const {test, expect} = require('@playwright/test');
const {spawn} = require('node:child_process');
const path = require('node:path');
let server, url;
test.beforeAll(async () => {
  server = spawn(process.env.PYTHON || 'python3', ['-m', 'src.research_demo', '--no-library', '--port', '0'], {cwd: path.resolve(__dirname, '../..')});
  url = await new Promise((resolve, reject) => {
    server.once('exit', code => reject(new Error(`Server exited ${code}`)));
    server.stdout.on('data', data => {const match = String(data).match(/http:\/\/127.0.0.1:\d+/); if (match) resolve(match[0]);});
    server.stderr.on('data', data => process.stderr.write(data));
  });
});
test.afterAll(() => server?.kill());
async function mockSpeech(page, voicesAvailable = true) {
  await page.addInitScript(voicesAvailable => {
    window.speechCalls = [];
    const voice = {localService:true, lang:'en-US', voiceURI:'test-local'};
    Object.defineProperty(window, 'speechSynthesis', {value: {
      getVoices: () => voicesAvailable ? [voice] : [], addEventListener() {}, removeEventListener() {},
      speak(utterance) {speechCalls.push(['speak', utterance.text]); utterance.onstart?.();},
      cancel() {speechCalls.push(['cancel']);}, pause() {}, resume() {},
    }});
    window.SpeechSynthesisUtterance = class {constructor(text) {this.text = text;}};
  }, voicesAvailable);
}
for (const width of [1280, 390]) {
  test(`real research page speech lifecycle and modal controls (${width})`, async ({page}) => {
    await page.setViewportSize({width, height:900});
    await mockSpeech(page);
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(url);
    await page.getByRole('button', {name:'View example'}).click();
    const answer = page.locator('.answer').first();
    const audio = answer.getByRole('group', {name:'Optional read-aloud'});
    await answer.locator('.listen-disclosure > summary').click();
    await expect(audio.getByRole('button', {name:'Play', exact:true})).toBeEnabled();
    expect(await page.evaluate(() => speechCalls)).toEqual([]);
    const limitText = await page.evaluate(() => {
      const demo = structuredClone(activeDemo.demo);
      demo.result.summary.limitations = ['A source-supported caveat.', 'An additional uncited gap.'];
      demo.result.summary.limitation_support = [{text:'A source-supported caveat.', chunk_ids:[demo.result.evidence[1].chunk_id]}];
      return ResearchSpeech.result(demo, 9).text;
    });
    expect(limitText).toContain('A source-supported caveat. Citations: 2, Synthetic fixture, not a paper.');
    expect(limitText.match(/A source-supported caveat/g)).toHaveLength(1);
    expect(limitText).toContain('An additional uncited gap.');
    const failedBusiness = await page.evaluate(() => {
      const demo = structuredClone(activeDemo.demo);
      demo.result.business_insight = null;
      demo.error = {stage:'business', message:'Business translation failed. Retry the question.'};
      return ResearchSpeech.result(demo, 10).text;
    });
    expect(failedBusiness).toContain('Business translation unavailable. business: Business translation failed. Retry the question.');
    expect(failedBusiness).not.toContain('Business translation not requested.');
    await audio.getByRole('button', {name:'Play', exact:true}).press('Enter');
    await expect(audio.getByRole('button', {name:'Pause', exact:true})).toBeEnabled();
    expect(await page.evaluate(() => speechCalls.some(c => c[0] === 'speak' && c[1].includes('Draft. Human review pending. Not approved.')))).toBeTruthy();
    await audio.getByRole('button', {name:'Pause', exact:true}).press('Space');
    await expect(audio.getByRole('button', {name:'Resume', exact:true})).toBeFocused();
    await audio.getByRole('button', {name:'Resume', exact:true}).press('Enter');
    await page.locator('.citation').first().press('Enter');
    await page.getByRole('button', {name:/^Inspect source context,/}).click();
    const panel = page.locator('#evidence-panel');
    const sourceAudio = panel.getByRole('group', {name:'Optional read-aloud'});
    await panel.locator('.listen-disclosure > summary').click();
    await expect(sourceAudio).toBeVisible();
    // Starting a passage cancels the result, never queues two readers.
    await sourceAudio.getByRole('button', {name:'Play', exact:true}).press('Enter');
    await expect(audio.getByRole('button', {name:'Play', exact:true})).toBeEnabled();
    await expect(sourceAudio.getByRole('button', {name:'Pause', exact:true})).toBeEnabled();
    // The native select is reachable within the mobile modal focus scope.
    await sourceAudio.getByLabel('Read', {exact:true}).focus();
    await page.keyboard.press('Tab');
    await expect(sourceAudio.getByLabel('Speed', {exact:true})).toBeFocused();
    const callsBeforeClose = await page.evaluate(() => speechCalls.length);
    await page.keyboard.press('Escape');
    await expect(panel).not.toBeVisible();
    expect(await page.evaluate(() => speechCalls.slice(-1)[0][0])).toBe('cancel');
    expect(await page.evaluate(() => speechCalls.length)).toBeGreaterThan(callsBeforeClose);
    await audio.getByRole('button', {name:'Play', exact:true}).press('Enter');
    await page.getByRole('button', {name:'View example'}).click();
    await expect(page.locator('.answer')).toHaveCount(2);
    await expect(audio.getByRole('button', {name:'Play', exact:true})).toBeEnabled();
    expect(errors).toEqual([]);
  });
}
test('unsupported speech keeps the actual answer and citation inspection usable', async ({page}) => {
  await page.addInitScript(() => Object.defineProperty(window, 'speechSynthesis', {value:undefined}));
  await page.goto(url);
  await page.getByRole('button', {name:'View example'}).click();
  const listen = page.locator('.answer .listen-disclosure');
  await listen.locator('summary').click();
  await expect(page.getByText('Read-aloud unavailable in this browser. Text remains available.')).toBeVisible();
  await expect(listen.getByRole('button', {name:'Play', exact:true})).toHaveCount(0);
  await expect(page.locator('.citation').first()).toBeVisible();
});

// Exercise the real mobile dialog and native Tab order, including asynchronously
// mounted speech controls. Hidden controls must never define the wrapping edge.
for (const voicesAvailable of [true, false]) {
  for (const open of [false, true]) {
    test(`mobile source focus wraps with Listen ${open ? 'open' : 'closed'}, voices ${voicesAvailable}`, async ({page}) => {
      await page.setViewportSize({width:390, height:844});
      await mockSpeech(page, voicesAvailable);
      await page.goto(url);
      await page.getByRole('button', {name:'View example'}).click();
      await page.locator('.citation').first().click();
      await page.getByRole('button', {name:/^Inspect source context,/}).click();
      const panel = page.locator('#evidence-panel');
      const summary = panel.locator('.listen-disclosure > summary');
      const play = panel.getByRole('button', {name:'Play', exact:true, includeHidden:true});
      await expect(play).toHaveCount(1); // Wait for asynchronous speech mounting.
      if (voicesAvailable) await expect(play).toBeEnabled();
      else await expect(play).toBeDisabled();
      if (open) await summary.click();
      const close = panel.locator('#evidence-close');
      await close.focus();
      await page.keyboard.press('Shift+Tab');
      if (!open) await expect(summary).toBeFocused();
      else expect(await page.evaluate(() => document.querySelector('#evidence-panel').contains(document.activeElement))).toBe(true);
      // The last sequential control wraps directly, without a BODY/chrome stop.
      await page.keyboard.press('Tab');
      await expect(close).toBeFocused();
      for (const key of ['Tab', 'Shift+Tab']) {
        for (let i = 0; i < 24; i++) {
          await page.keyboard.press(key);
          expect(await page.evaluate(() => document.querySelector('#evidence-panel').contains(document.activeElement))).toBe(true);
        }
      }
      await page.keyboard.press('Escape');
      await expect(page.locator('.citation').first()).toBeFocused();
    });
  }
}

test('indexed mode retains business and regulatory request controls and failed-assessment rendering', async ({page}) => {
  await page.route('**/api/config', route => route.fulfill({json:{live:true, mode:'indexed', context_id:'test-index', index:{count:2}}}));
  await page.route('**/api/saved-result', route => route.fulfill({json:null}));
  const fixture = require('../fixtures/research/normal-v1.json');
  const requests = [];
  await page.route('**/api/research', route => {
    const body = route.request().postDataJSON();
    requests.push(body);
    return route.fulfill({json:{mode:'indexed', scenario:body.risk_assessment ? 'partial' : 'full',
      submitted_request:body, result:fixture,
      ...(body.risk_assessment ? {error:{stage:'regulatory', message:'Assessment unavailable'}} : {})}});
  });
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  await expect(page.locator('#indexed-options')).toBeVisible();
  await expect(page.locator('#mode-description')).toContainText('Independent questions');
  const query = page.getByRole('textbox', {name:'Research question', exact:true});
  await page.getByLabel('Industry or business context (optional)', {exact:true}).fill('Financial services');
  await query.fill('What are the findings?');
  await page.getByRole('button', {name:'Research', exact:true}).click();
  await expect(page.locator('.answer')).toHaveCount(1);
  await expect(page.locator('#output')).toHaveAttribute('aria-busy', 'false');
  expect(requests[0]).toMatchObject({query:'What are the findings?', industry:'Financial services',
    context_id:'test-index', interpret_context:true, risk_assessment:false});
  expect(requests[0]).not.toHaveProperty('jurisdiction');
  await page.getByLabel('Add source-backed risk and compliance assessment', {exact:true}).check();
  const jurisdiction = page.getByLabel('Jurisdiction (required for assessment)', {exact:true});
  await expect(jurisdiction).toBeVisible();
  await jurisdiction.fill('United States');
  await query.fill('Assess the risks');
  await page.getByRole('button', {name:'Research', exact:true}).click();
  await expect(page.locator('.answer')).toHaveCount(2);
  await expect(page.locator('#output')).toHaveAttribute('aria-busy', 'false');
  expect(requests[1]).toMatchObject({query:'Assess the risks', industry:'Financial services',
    risk_assessment:true, jurisdiction:'United States'});
  await expect(page.locator('.answer').last()).toContainText('business implications are available, but risk and compliance assessment failed');
  await expect(page.locator('#feedback')).toContainText('business implications retained');
  expect(errors).toEqual([]);
});

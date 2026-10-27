const {test, expect} = require('@playwright/test');
const {spawn} = require('node:child_process');
const path = require('node:path');
let server, url;
test.beforeAll(async () => {
  server = spawn(process.env.PYTHON || 'python3', ['-m', 'src.research_demo', '--port', '0'], {cwd: path.resolve(__dirname, '../..')});
  url = await new Promise((resolve, reject) => {
    server.once('exit', code => reject(new Error(`Server exited ${code}`)));
    server.stdout.on('data', data => {const match = String(data).match(/http:\/\/127.0.0.1:\d+/); if (match) resolve(match[0]);});
    server.stderr.on('data', data => process.stderr.write(data));
  });
});
test.afterAll(() => server?.kill());
async function mockSpeech(page) {
  await page.addInitScript(() => {
    window.speechCalls = [];
    const voice = {localService:true, lang:'en-US', voiceURI:'test-local'};
    Object.defineProperty(window, 'speechSynthesis', {value: {
      getVoices: () => [voice], addEventListener() {}, removeEventListener() {},
      speak(utterance) {speechCalls.push(['speak', utterance.text]); utterance.onstart?.();},
      cancel() {speechCalls.push(['cancel']);}, pause() {}, resume() {},
    }});
    window.SpeechSynthesisUtterance = class {constructor(text) {this.text = text;}};
  });
}
for (const width of [1280, 390]) {
  test(`real research page speech lifecycle and modal controls (${width})`, async ({page}) => {
    await page.setViewportSize({width, height:900});
    await mockSpeech(page);
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(url);
    await page.getByRole('button', {name:'View example'}).click();
    const answer = page.locator('.answer').last();
    const audio = answer.getByRole('group', {name:'Optional read-aloud'});
    await expect(audio.getByRole('button', {name:'Play', exact:true})).toBeEnabled();
    expect(await page.evaluate(() => speechCalls)).toEqual([]);
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
    await page.getByRole('textbox', {name:'Research question'}).fill('New question');
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
  await expect(page.getByText('Read-aloud unavailable in this browser. Text remains available.')).toBeVisible();
  await expect(page.getByRole('button', {name:'Play', exact:true})).toBeDisabled();
  await expect(page.locator('.citation').first()).toBeVisible();
});

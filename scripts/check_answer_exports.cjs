/* Offline browser regression: NODE_PATH=<installed playwright node_modules> node scripts/check_answer_exports.cjs
 * Start python3.12 -m src.research_demo --port 8843 first. No models/network sources used.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width:1280, height:900}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(process.env.EXPORT_TEST_URL || 'http://127.0.0.1:8843');
    assert.equal(await page.title(), 'Research desk · 1F');
    await page.getByRole('button', {name:'View example', exact:true}).click();
    const first = page.getByRole('region', {name:'Export result 1', exact:true});
    await first.waitFor();
    // Add another turn, then export the first explicitly, using only keyboard activation.
    await page.getByRole('textbox', {name:'Research question', exact:true}).fill('SECOND TURN MUST NOT LEAK');
    await page.getByRole('button', {name:'View example', exact:true}).click();
    await page.getByRole('region', {name:'Export result 2', exact:true}).waitFor();
    for (const [label, extension] of [['HTML','html'], ['Markdown','md']]) {
      const button = first.getByRole('button', {name:`Export this result as ${label}`, exact:true});
      await button.focus();
      const waiting = page.waitForEvent('download');
      await page.keyboard.press('Enter');
      const download = await waiting;
      assert.equal(download.suggestedFilename(), `research-result-1.${extension}`);
      const content = await fs.readFile(await download.path(), 'utf8');
      assert.ok(content.includes('Synthetic agents need task'));
      assert.ok(content.includes('pending'));
      assert.ok(!content.includes('SECOND TURN MUST NOT LEAK'));
      assert.match(await first.getByRole('status').textContent(), /download requested/);
      assert.equal(await button.evaluate(node => node === document.activeElement), true);
    }
    const checks = await page.evaluate(async () => {
      const check = (ok, message) => { if (!ok) throw new Error(message); };
      const demos = {};
      for (const scenario of ['full','partial','insufficient','empty']) {
        const demo = await (await fetch('/api/demo', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:'UNEXECUTED USER QUESTION', scenario})})).json();
        demos[scenario] = demo;
        const original = JSON.stringify(demo);
        for (const format of ['html','md']) {
          const output = AnswerExport.build(demo, format);
          check(output.includes('pending') && output.includes('false'), `${scenario}: review status`);
          check(output.replace(/\\_/g, '_').includes(demo.result.summary.status), `${scenario}: summary state`);
          check(!output.includes('UNEXECUTED USER QUESTION'), 'Fixture query must not be relabeled');
          if (scenario === 'partial') check(output.includes('no supported business recommendations'), 'Partial abstention');
          if (scenario === 'insufficient') check(output.includes('Retrieved context only'), 'Insufficient context label');
          if (scenario === 'empty') check(output.includes('No evidence retained'), 'Empty evidence label');
          if (format === 'html') {
            // The host's CSP also applies to DOMParser; standalone CSS is checked in a fresh artifact page.
            const doc = new DOMParser().parseFromString(output.replace(/<style>[\s\S]*?<\/style>/g, ''), 'text/html');
            check(doc.documentElement.lang === 'en', 'Document language');
            check(doc.querySelectorAll('h1').length === 1 && doc.querySelector('main'), 'Landmarks and headings');
            check(!doc.querySelector('script'), 'No scripts in standalone export');
            for (const link of doc.querySelectorAll('a[href^="#"]')) check(doc.querySelector(link.getAttribute('href')), 'Resolvable citation');
          }
        }
        check(JSON.stringify(demo) === original, 'Export must not mutate review packet');
      }
      const demo = structuredClone(demos.full);
      const normalized = structuredClone(demo);
      const normalizedPassage = normalized.result.evidence[0];
      normalizedPassage.text = 'The mean score was 0.166 across the evaluated systems.';
      const originalQuote = 'The mean\n score was 0.166';
      normalized.result.summary.claims[0].support = [{chunk_id:normalizedPassage.chunk_id, quote:originalQuote}];
      for (const format of ['html', 'md']) {
        const output = AnswerExport.build(normalized, format);
        if (format === 'html') {
          const doc = new DOMParser().parseFromString(output.replace(/<style>[\s\S]*?<\/style>/g, ''), 'text/html');
          check([...doc.querySelectorAll('blockquote')].some(node => node.textContent === originalQuote), 'Retain original normalized-match quote');
          check([...doc.querySelectorAll('blockquote')].some(node => node.textContent === normalizedPassage.text), 'Retain canonical passage');
        } else check(output.includes('The mean\n>  score was 0\\.166'), 'Retain original Markdown quote whitespace');
      }
      // Extraction gaps remain relevant even when the optional reader is absent,
      // unsupported, or declines to render retained structure.
      const fallback = structuredClone(demo);
      fallback.result.evidence.forEach(passage => {
        passage.reader = {version:999, nodes:[], limitations:['SOURCE EXTRACTION GAP MUST SURVIVE']};
      });
      for (const format of ['html', 'md']) {
        const output = AnswerExport.build(fallback, format);
        check(output.includes('SOURCE EXTRACTION GAP MUST SURVIVE'), 'Retain extraction gaps without rendered structure');
        check(output.replace(/\\-/g, '-').includes('Only citation-check text is included'), 'Explain structure fallback');
      }
      const passage = demo.result.evidence[0];
      passage.text += ' Exact quote: <script>alert(1)</script> \\(x^2\\).';
      demo.result.summary.claims[0].support = [{chunk_id:passage.chunk_id, quote:passage.text}];
      passage.source_url = 'javascript:alert(1)';
      demo.result.evidence.push({...passage, chunk_id:'unreferenced-extra', text:'UNRELATED EVIDENCE MUST NOT LEAK'});
      demo.result.request.history = [{role:'user',content:'HISTORY MUST NOT LEAK'}];
      for (const format of ['html','md']) {
        const output = AnswerExport.build(demo, format);
        check(!output.includes('UNRELATED EVIDENCE MUST NOT LEAK'), 'Exclude uncited context in supported results');
        check(!output.includes('HISTORY MUST NOT LEAK'), 'Exclude request history');
        check(!output.includes('javascript:'), 'Exclude unsafe source links');
        check(!output.includes('<script>'), 'Source markup must stay inert');
        check(output.includes('Exact source quote'), 'Claim-specific quote label');
        if (format === 'html') {
          const doc = new DOMParser().parseFromString(output.replace(/<style>[\s\S]*?<\/style>/g, ''), 'text/html');
          check(doc.querySelector('math'), 'Standalone MathML');
          check(doc.querySelector('blockquote').textContent.includes('<script>alert(1)</script>'), 'Literal source markup retained');
          check([...doc.querySelectorAll('pre')].some(node => node.textContent === passage.text), 'Exact original math notation retained');
        }
      }
      const bad = structuredClone(demo);
      bad.result.summary.claims[0].support[0].quote = 'QUOTE NOT IN PASSAGE';
      for (const data of [bad, {...demo, result:{...demo.result, approved:true}},
          {...demo, result:{...demo.result, evidence:[]}}, {...demo, result:null}]) {
        let threw = false;
        try { AnswerExport.build(data, 'html'); } catch { threw = true; }
        check(threw, 'Reject missing citations, invalid quotes or review state');
      }
      const group = AnswerExport.controls(bad, 99); document.querySelector('#output').append(group);
      group.querySelector('button').click();
      check(group.querySelector('[role="status"]').textContent.includes('export failed'), 'Understandable failure feedback');
      check(document.querySelector('[aria-label="Export result 1"]'), 'Keep original answer after failure');
      group.remove();
      return 'full, partial, insufficient, empty; selection isolation; quote/citation integrity; safe markup/URLs; MathML; pending status; failure recovery';
    });
    const artifactDir = process.env.EXPORT_ARTIFACT_DIR;
    if (artifactDir) {
      await fs.mkdir(artifactDir, {recursive:true});
      await page.screenshot({path:path.join(artifactDir,'export-desktop.png'),fullPage:true});
      for (const scenario of ['full','partial','insufficient','empty']) {
        for (const format of ['html','md']) {
          const content = await page.evaluate(async ({scenario,format}) => {
            const demo = await (await fetch('/api/demo', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:'Fixture check',scenario})})).json();
            return AnswerExport.build(demo, format);
          }, {scenario,format});
          await fs.writeFile(path.join(artifactDir,`${scenario}.${format}`), content);
        }
      }
    }
    await page.setViewportSize({width:360,height:800});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await first.getByRole('button', {name:'Export this result as HTML', exact:true}).scrollIntoViewIfNeeded();
    if (artifactDir) {
      await page.screenshot({path:path.join(artifactDir,'export-narrow.png'),fullPage:true});
      const artifactPage = await browser.newPage();
      await artifactPage.setContent(await fs.readFile(path.join(artifactDir,'full.html'), 'utf8'));
      assert.equal(await artifactPage.title(), 'Selected research result');
      await artifactPage.getByRole('link', {name:'Citation 2: Synthetic fixture, not a paper', exact:true}).click();
      assert.match(await artifactPage.url(), /#evidence-2$/);
      await artifactPage.screenshot({path:path.join(artifactDir,'artifact-desktop.png'),fullPage:true});
      await artifactPage.setViewportSize({width:320,height:800});
      assert.equal(await artifactPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await artifactPage.screenshot({path:path.join(artifactDir,'artifact-narrow.png'),fullPage:true});
      await artifactPage.close();
    }
    assert.deepEqual(errors, []);
    console.log(`PASS: keyboard downloads; narrow reflow; no page errors; ${checks}`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

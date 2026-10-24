/* Parser-produced fixture through the actual reader/export script order.
 * Usage: node scripts/check_export_reader_integration.cjs <fixture.json>
 * EXPORT_TEST_URL selects an isolated loopback server; no real paper or AT claim.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const {chromium} = require('playwright');

(async () => {
  const fixture = JSON.parse(await fs.readFile(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.EXPORT_TEST_URL || 'http://127.0.0.1:8843');
    assert.equal(await page.title(), 'Research desk · 1F');
    const artifacts = await page.evaluate(demo => {
      const sources = [...document.scripts].map(script => new URL(script.src).pathname);
      if (!(sources.indexOf('/source-reader.js') < sources.indexOf('/answer-export.js')))
        throw new Error('Reader must load before export');
      return {html: AnswerExport.build(demo, 'html'), md: AnswerExport.build(demo, 'md')};
    }, fixture);
    const artifact = await browser.newPage({viewport: {width: 320, height: 900}});
    artifact.on('pageerror', error => errors.push(error.message));
    await artifact.setContent(artifacts.html);
    assert.equal(await artifact.title(), 'Selected research result');
    const quote = fixture.result.summary.claims[0].support[0].quote;
    const passage = fixture.result.evidence[0];
    const result = await artifact.evaluate(({quote, passage}) => ({
      quote: [...document.querySelectorAll('blockquote')].some(node => node.textContent === quote),
      original: [...document.querySelectorAll('blockquote, pre')].some(node => node.textContent === passage.text),
      headers: [...document.querySelectorAll('td[headers]')].every(cell => cell.headers.split(' ')
        .every(id => document.getElementById(id)?.tagName === 'TH')),
      idsUnique: new Set([...document.querySelectorAll('[id]')].map(node => node.id)).size === document.querySelectorAll('[id]').length,
      colgroup: document.querySelectorAll('colgroup[span="2"]').length,
      barless: document.querySelectorAll('math mfrac[linethickness="0"]').length,
      rowSpan: document.querySelector('th[scope="row"]')?.rowSpan,
      figures: document.querySelectorAll('figure').length,
      limitations: passage.reader.limitations.every(text => document.body.textContent.includes(text)),
      pending: document.body.textContent.includes('Human review: pending. Approved: false.'),
      inert: !document.querySelector('script, iframe, img'),
      reflow: document.documentElement.scrollWidth <= innerWidth,
    }), {quote, passage});
    assert.deepEqual(result, {quote: true, original: true, headers: true, idsUnique: true,
      colgroup: 1, barless: 1, rowSpan: 0, figures: 2, limitations: true,
      pending: true, inert: true, reflow: true});
    assert.match(artifacts.md, /<table/);
    assert.match(artifacts.md, /<math/);
    await artifact.getByRole('link', {name: /^Citation 1:/}).click();
    assert.match(artifact.url(), /#evidence-1$/);
    if (process.env.EXPORT_ARTIFACT_DIR) {
      const out = process.env.EXPORT_ARTIFACT_DIR;
      await fs.mkdir(out, {recursive: true});
      await fs.writeFile(path.join(out, 'structured.html'), artifacts.html);
      await fs.writeFile(path.join(out, 'structured.md'), artifacts.md);
      await artifact.screenshot({path: path.join(out, 'structured-narrow.png'), fullPage: true});
    }
    assert.deepEqual(errors, []);
    console.log('PASS: actual script order; parser-produced table/header groups, barless MathML, figures, exact quote/text, limitations, pending status, local citation, inert markup, 320px artifact reflow. Not screen-reader acceptance.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

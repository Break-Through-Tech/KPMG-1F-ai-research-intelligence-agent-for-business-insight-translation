const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const fixture = fs.readFileSync(process.env.READER_FIXTURE_JSON || '/tmp/source-reader-fixture.json', 'utf8');
const url = process.env.RESEARCH_URL || 'http://127.0.0.1:9142';
const screenshotDirectory = process.env.SCREENSHOT_DIR || os.tmpdir();
(async () => {
  const browser = await chromium.launch({headless:true});
  const results = [];
  for (const width of [1280, 320, 640]) {
    const page = await browser.newPage({viewport:{width,height:900}});
    const errors=[];
    const externalRequests=[];
    page.on('request', request=>{if(new URL(request.url()).origin !== new URL(url).origin) externalRequests.push(request.url());});
    page.on('pageerror', e=>errors.push(e.message));
    page.on('console', m=>{if(['error','warning'].includes(m.type())) errors.push(m.text());});
    await page.route('**/api/demo', route => route.fulfill({status:200,contentType:'application/json',body:fixture}));
    await page.goto(url);
    assert.equal(await page.title(), 'Research desk · 1F');
    await page.getByRole('button',{name:'View example'}).click();
    await page.locator('.citation').first().focus();
    await page.getByRole('button',{name:'More context',exact:true}).click();
    const panel = page.locator('#evidence-panel');
    await panel.waitFor({state:'visible'});
    assert.equal(await panel.locator('.source-exact-quote').innerText(), 'The measured result improves accuracy in this bounded experiment.');
    assert(await panel.getByText('Fixture claim about the bounded experiment.',{exact:true}).isVisible());
    assert.equal(await panel.locator('table th[scope="col"]').count(),2);
    const headerId=await panel.locator('td').first().getAttribute('headers');
    assert(headerId.split(' ').every(id=>id.startsWith('source-reader-')));
    assert(await page.evaluate(()=>[...document.querySelector('td').headers.split(' ')].every(id=>document.getElementById(id)?.tagName==='TH')));
    assert.equal(await panel.locator('math mfrac').count(),2);
    assert.equal(await panel.locator('math mfrac[linethickness="0"]').count(),1);
    assert.equal(await panel.locator('math').first().evaluate(node=>node.namespaceURI),'http://www.w3.org/1998/Math/MathML');
    assert.equal(await panel.getByRole('columnheader').count(),3);
    assert.equal(await panel.locator('table > colgroup[span="2"]').count(),1);
    assert.equal(await panel.locator('th[scope="colgroup"][colspan="2"]').innerText(),'Results');
    assert.equal(await panel.getByRole('rowheader').count(),1);
    assert.equal(await panel.getByRole('rowheader').evaluate(node=>node.rowSpan),0);
    assert(await panel.locator('table').evaluate(table=>{
      const cells=table.querySelectorAll('td');
      return cells.length===2 && cells[0].getBoundingClientRect().left===cells[1].getBoundingClientRect().left;
    }));
    assert.equal(await panel.locator('ol[start="3"] li[value="4"]').count(),1);
    const wideMath = panel.locator('.source-inline-math').filter({has: page.locator('mtable')});
    await wideMath.scrollIntoViewIfNeeded();
    await wideMath.focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(200);
    assert(await wideMath.evaluate(node => node.scrollLeft > 0));
    assert.equal(await panel.locator('.source-reading ul li').count(),2);
    assert.equal(await panel.locator('.source-reading img, .source-reading script, .source-reading iframe').count(),0);
    assert(await panel.getByText(/Source-supplied image description: Two/).count());
    assert((await panel.innerText()).includes('caption alone may omit visual information'));
    assert((await panel.innerText()).includes('END OF LONG PASSAGE.'));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    assert.equal(await panel.evaluate(e=>e.scrollWidth>e.clientWidth),false);
    // Natural keyboard traversal reaches the explicit return action from its heading.
    await panel.locator('#evidence-heading').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.id),'evidence-close');
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Return to answer');
    await page.screenshot({path:path.join(screenshotDirectory, `kpmg142-reader-${width}.png`)});
    await panel.locator('math mfrac[linethickness="0"]').screenshot({path:path.join(screenshotDirectory, `kpmg142-binomial-${width}.png`)});
    await panel.locator('table').screenshot({path:path.join(screenshotDirectory, `kpmg142-table-${width}.png`)});
    await panel.locator('.source-return').first().focus();
    await page.keyboard.press('Enter');
    assert.equal(await panel.isVisible(),false);
    assert.equal(await page.evaluate(()=>document.activeElement.className),'citation');
    // Browse another passage without losing the originating claim identity.
    await page.getByRole('button',{name:'More context',exact:true}).click();
    await panel.getByText('Browse paper pages (2)',{exact:true}).click();
    await panel.locator('.source-choice').nth(1).click();
    assert(await panel.getByText('Fixture claim about the bounded experiment.',{exact:true}).isVisible());
    assert(await panel.getByText(/No exact supporting quote was supplied/).isVisible());
    assert(await panel.getByText('Original-source link not supplied.',{exact:true}).isVisible());
    assert(await panel.getByText(/Structured headings, lists, source MathML/).isVisible());
    // Malformed/injected retained data fails closed; no arbitrary HTML parser.
    const unsafe = await page.evaluate(()=> {
      const reader={version:1,provenance:'source-html',nodes:[{tag:'p',attrs:{onclick:'alert(1)',style:'position:fixed'},children:['<img src=x onerror=bad()>']}]};
      const root=document.createElement('div');root.append(structuredSource(reader));
      const safe=root.querySelector('p').attributes.length===0 && root.querySelector('img')===null;
      const invalidMath={version:1,provenance:'source-html',nodes:[{tag:'math',children:[{tag:'mfrac',attrs:{linethickness:'url(remote)'},children:[]}]}]};
      if (structuredSource(invalidMath)!==null) return false;
      for (const [tag,attrs] of [['menclose',{notation:'updiagonalstrike'}],['mfenced',{open:'[',close:']',separators:';'}]]) {
        invalidMath.nodes[0].children=[{tag,attrs,children:[{tag:'mi',children:['x']}]}];
        if (structuredSource(invalidMath)!==null) return false;
      }
      reader.nodes.push({tag:'script',children:['bad()']});
      return safe && structuredSource(reader)===null;
    });
    assert(unsafe);
    assert.deepEqual(errors,[]);
    assert.deepEqual(externalRequests,[]);
    results.push({width,checks:'claim/quote, return focus, MathML, header IDs, long text, fallback, inert rendering, overflow, console: passed'});
    await page.close();
  }
  console.log(JSON.stringify(results,null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

/* Selected-result exports. Never scrape conversation/source-panel state. */
(() => {
  'use strict';
  const LIMITATION = 'Only retained source structure can be exported. Plain-text passages do not recover tables, figure descriptions, or original layout. Markdown preserves literal math notation, not accessible rendered math or semantic table relationships. HTML uses MathML for supported formulas; unrenderable formulas retain labeled original notation.';
  const safeURL = value => {
    try {
      const url = new URL(value);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : null;
    } catch { return null; }
  };
  // Escape Markdown syntax AND raw HTML; source text must never become markup.
  const mdText = value => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/([\\`*_{}\[\]()#+.!|~-])/g, '\\$1');

  function build(demo, format) {
    const result = demo.result;
    if (!result || result.approved !== false || result.human_review?.status !== 'pending') {
      throw new Error('Only pending, unapproved research results can be exported.');
    }
    if (!['html', 'md'].includes(format)) throw new Error('Unknown export format.');
    const doc = document.implementation.createHTMLDocument('Selected research result');
    doc.documentElement.lang = 'en';
    const meta = doc.createElement('meta');
    meta.name = 'viewport'; meta.content = 'width=device-width, initial-scale=1';
    doc.head.append(meta);
    const charset = doc.createElement('meta'); charset.setAttribute('charset', 'utf-8'); doc.head.prepend(charset);
    const style = doc.createElement('style');
    style.textContent = 'body{font:1rem/1.6 system-ui,sans-serif;color:#18242c;background:#fff;margin:0;padding:1rem}main{max-width:72ch;margin:auto}p,li,blockquote{white-space:pre-wrap;overflow-wrap:anywhere}blockquote{margin:1rem 0;padding-left:1rem;border-left:3px solid #526675}a{color:#005a86}a:focus-visible{outline:3px solid #005a86;outline-offset:3px}math{max-width:100%;overflow-x:auto}table{border-collapse:collapse}th,td{border:1px solid;padding:.5rem}pre{white-space:pre-wrap;overflow-wrap:anywhere}';
    // Serialize this trusted stylesheet only; attaching it would invoke the host CSP.
    const main = doc.createElement('main'); doc.body.append(main);
    const markdown = [];
    function add(tag, text, parent = main) {
      const node = doc.createElement(tag);
      // MathML only: self-contained HTML needs no external fonts/scripts/CDN.
      if (['p', 'li', 'blockquote'].includes(tag) && typeof renderPaperMath === 'function') {
        renderPaperMath(node, String(text));
        node.querySelectorAll('.paper-math').forEach(target => {
          const math = target.querySelector('math');
          if (math) target.replaceChildren(math.cloneNode(true));
          else target.setAttribute('aria-label', `Unrendered formula: ${target.textContent}`);
        });
      } else node.textContent = String(text);
      parent.append(node);
      if (node.querySelector('math') && tag === 'blockquote') {
        const original = doc.createElement('details'), summary = doc.createElement('summary'), pre = doc.createElement('pre');
        summary.textContent = 'Original quote notation'; pre.textContent = String(text);
        original.append(summary, pre); parent.append(original);
      }
      const prefix = {h1:'# ', h2:'## ', h3:'### ', h4:'#### ', li:'- ', blockquote:'> '}[tag] || '';
      markdown.push(prefix + mdText(text).replace(/\n/g, tag === 'blockquote' ? '\n> ' : '\n') + '\n');
      return node;
    }
    function items(title, values) {
      if (!values?.length) return;
      add('h3', title);
      const ul = doc.createElement('ul'); main.append(ul);
      values.forEach(value => add('li', value, ul));
    }
    const evidence = result.evidence;
    const byId = new Map(evidence.map((passage, index) => [passage.chunk_id, {passage, number:index + 1}]));
    const referenced = new Set();
    function cited(item, index, label) {
      const claim = add('p', `${label} ${index + 1}: ${item.text}`);
      for (const id of item.chunk_ids) {
        const entry = byId.get(id);
        if (!entry) throw new Error('A citation is missing its source passage.');
        referenced.add(id);
        const link = doc.createElement('a');
        link.href = `#evidence-${entry.number}`;
        link.textContent = `Citation ${entry.number}: ${entry.passage.title}`;
        claim.append(doc.createTextNode(' '), link);
        markdown.push(`[Citation ${entry.number}](#evidence-${entry.number})\n`);
      }
      for (const support of item.support || []) {
        const entry = byId.get(support.chunk_id);
        if (!entry || !item.chunk_ids.includes(support.chunk_id) || !entry.passage.text.includes(support.quote) || !support.quote) {
          throw new Error('An exact quote no longer matches its associated source.');
        }
        add('p', `Exact source quote for ${label.toLowerCase()} ${index + 1}, citation ${entry.number}:`);
        add('blockquote', support.quote);
      }
      if (!item.support?.length) add('p', 'No claim-specific exact quote retained; consult the cited source passage.');
    }
    add('h1', 'Selected research result');
    add('h2', 'Question');
    add('p', result.request.query);
    if (demo.mode === 'fixture') add('p', 'Synthetic fixture only. The displayed question is the fixed example question; the typed question was not executed.');
    else add('p', demo.mode === 'live-synthesis' ? 'LLM synthesis; not independently verified.' : 'Saved research result; no new query executed.');
    add('h2', 'Status and review');
    add('p', `Result state: ${demo.scenario}. Summary: ${result.summary.status}. Business translation: ${result.business_insight?.status ?? 'not requested'}.`);
    add('p', 'Human review: pending. Approved: false. This export is not approval, source certification, or verification of semantic support.');
    add('h2', 'Generated research summary');
    if (!result.summary.claims.length) add('p', 'Abstention: no supported research claims.');
    result.summary.claims.forEach((claim, index) => cited(claim, index, claim.kind === 'interpretation' ? 'Generated interpretation (not a source finding)' : 'Generated claim'));
    add('h2', 'Generated business implications');
    const business = result.business_insight;
    if (!business) add('p', 'Business translation not requested.');
    else {
      add('p', `Industry: ${business.industry}`);
      if (!business.implications.length) add('p', 'Abstention: no supported business recommendations.');
      business.implications.forEach((item, index) => {
        cited(item, index, 'Generated recommendation');
        add('p', `Suggested action: ${item.suggested_action}`);
        items('Assumptions — not research findings', item.assumptions);
      });
    }
    add('h2', 'Limitations and risks');
    items('Summary limitations', result.summary.limitations);
    (result.summary.limitation_support || []).forEach((item, index) => cited(item, index, 'Supported limitation'));
    items('Business limitations', business?.limitations);
    items('Risks', business?.risks);
    add('p', LIMITATION);
    add('h2', 'Source evidence');
    // For abstentions, retain retrieved passages explicitly as insufficient context.
    const selectedEvidence = evidence.filter(passage => referenced.has(passage.chunk_id) || !referenced.size);
    if (!referenced.size && evidence.length) add('p', 'Retrieved context only: these passages do not establish an answer.');
    if (!selectedEvidence.length) add('p', 'No evidence retained.');
    selectedEvidence.forEach(passage => {
      const {number} = byId.get(passage.chunk_id);
      const heading = add('h3', `Citation ${number}: ${passage.title}`); heading.id = `evidence-${number}`;
      // Explicit anchor works in Markdown readers that do not auto-generate heading IDs.
      markdown.splice(markdown.length - 1, 0, `<a id="evidence-${number}"></a>\n`);
      add('p', `Chunk ID: ${passage.chunk_id}. Source: ${passage.source}. Source identity: ${passage.arxiv_id || 'not retained'}. Version: ${passage.arxiv_id?.match(/v\d+$/)?.[0] || 'not retained'}.`);
      add('p', `Section: ${passage.section || 'not retained'}. PDF page: ${passage.page_number ?? 'not retained'}.`);
      if (passage.source_file) add('p', `Source file: ${passage.source_file}. SHA-256: ${passage.source_sha256 || 'not retained'}. Lines: ${passage.line_start ?? '?'}–${passage.line_end ?? '?'}.`);
      add('h4', 'Source passage — not generated interpretation');
      // Literal exact text; do not interpret source markup or alter quotations.
      add('blockquote', passage.text);
      if (passage.reader) {
        const structured = typeof structuredSource === 'function' ? structuredSource(passage.reader) : null;
        if (structured) {
          add('h4', 'Retained source structure');
          add('p', 'Source-supplied structure, not generated interpretation or extraction certification. Markdown readers may not support the following HTML tables or MathML.');
          const section = doc.createElement('section'); section.append(structured); main.append(section);
          markdown.push(section.outerHTML + '\n');
          items('Source extraction limitations', passage.reader.limitations);
        } else add('p', 'Retained structure could not be rendered by this export. Only citation-check text is included; table relationships, figure descriptions and source MathML are unavailable here.');
      }
      const url = safeURL(passage.source_url);
      if (url) {
        const p = doc.createElement('p'), link = doc.createElement('a');
        link.href = url; link.textContent = `Original source for citation ${number}: ${passage.title}`;
        p.append(link); main.append(p);
        markdown.push(`[Original source for citation ${number}: ${mdText(passage.title)}](<${url.replace(/</g, '%3C').replace(/>/g, '%3E')}>)\n`);
      } else add('p', 'Original-source link unavailable or unsafe.');
    });
    if (result.provenance) {
      add('h2', 'Recorded generation provenance');
      const raw = JSON.stringify(result.provenance, null, 2);
      const pre = doc.createElement('pre'); pre.textContent = raw; main.append(pre);
      // Indented code is robust even when recorded text contains backtick fences.
      markdown.push(raw.split('\n').map(line => `    ${line}`).join('\n') + '\n');
    }
    return format === 'html' ? '<!doctype html>\n' + doc.documentElement.outerHTML.replace('</head>', style.outerHTML + '</head>') : markdown.join('\n');
  }

  function controls(demo, number) {
    const group = document.createElement('section');
    group.setAttribute('aria-label', `Export result ${number}`);
    const status = document.createElement('p'); status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite'); status.className = 'meta';
    for (const [format, label] of [['html', 'HTML'], ['md', 'Markdown']]) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'quiet';
      button.textContent = `Export this result as ${label}`;
      button.addEventListener('click', () => {
        let url;
        try {
          const content = build(demo, format);
          url = URL.createObjectURL(new Blob([content], {type: format === 'html' ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8'}));
          const link = document.createElement('a'); link.href = url;
          link.download = `research-result-${number}.${format}`;
          document.body.append(link);
          try { link.click(); } finally { link.remove(); }
          status.textContent = `${label} download requested for result ${number}. Pending review; not approved. Check your browser downloads.`;
        } catch {
          status.textContent = `${label} export failed. Your answer is unchanged. Check citation/quote integrity and retry.`;
        } finally {
          if (url) setTimeout(() => URL.revokeObjectURL(url), 60000);
        }
      });
      group.append(button);
    }
    group.append(status);
    return group;
  }
  window.AnswerExport = Object.freeze({build, controls});
})();

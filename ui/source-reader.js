/* Source structure is untrusted data. Rebuild only inert semantic elements. */
const READER_HTML_TAGS = new Set('p div span ul ol li dl dt dd blockquote em strong b i sub sup br table caption colgroup col thead tbody tfoot tr th td figure figcaption'.split(' '));
const READER_MATH_TAGS = new Set('math semantics annotation mrow mi mn mo mtext mspace ms mfrac msqrt mroot msub msup msubsup munder mover munderover mmultiscripts mprescripts none mtable mtr mtd menclose mphantom mpadded mstyle mfenced'.split(' '));
const READER_MATH_ATTRS = new Set('display mathvariant stretchy fence separator accent accentunder columnalign rowalign columnspan rowspan encoding linethickness'.split(' '));
const READER_MATH_METADATA = new Set('class id alttext xmlns href xlink:href'.split(' '));
const READER_MATH_LENGTHS = new Set('lspace rspace minsize maxsize mathsize width height depth columnspacing rowspacing'.split(' '));
const READER_MATH_BOOLS = new Set(['displaystyle', 'movablelimits', 'symmetric']);
for (const key of [...READER_MATH_LENGTHS, ...READER_MATH_BOOLS, 'intent']) READER_MATH_ATTRS.add(key);
function validReaderMathAttribute(key, value) {
  if (key === 'intent') return value === ':literal';
  if (READER_MATH_BOOLS.has(key)) return ['true', 'false'].includes(value);
  if (READER_MATH_LENGTHS.has(key)) {
    const parts = ['columnspacing', 'rowspacing'].includes(key) ? value.trim().split(/\s+/) : [value];
    return parts.length > 0 && parts.length <= 12 && parts.every(part =>
      /^(?:\d{1,3}(?:\.\d{1,4})?|\.\d{1,4})(?:em|ex|px|pt|pc|in|cm|mm|%)?$/.test(part) && parseFloat(part) <= 100);
  }
  return true;
}
let sourceReaderNumber = 0;

function readerElement(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function structuredSource(reader) {
  if (reader?.version !== 1 || reader.provenance !== 'source-html' || !Array.isArray(reader.nodes) || !reader.nodes.length) return null;
  const prefix = `source-reader-${++sourceReaderNumber}-`;
  // Encode IDs, including whitespace/punctuation, without introducing collisions.
  const localId = id => prefix + Array.from(id, char => char.codePointAt(0).toString(16)).join('-');
  let count = 0;
  const headingLevels = [];
  function inspect(nodes, depth = 0) {
    if (depth > 48) throw new Error('Reader limit');
    for (const item of nodes) {
      if (++count > 12000) throw new Error('Reader limit');
      if (item && typeof item === 'object') {
        if (/^h[1-6]$/.test(item.tag)) headingLevels.push(Number(item.tag[1]));
        if (Array.isArray(item.children)) inspect(item.children, depth + 1);
      }
    }
  }
  try { inspect(reader.nodes); } catch { return null; }
  const headingBase = Math.min(...headingLevels, 6);
  count = 0;
  function build(item, depth = 0, inMath = false) {
    if (++count > 12000 || depth > 48) throw new Error('Reader limit');
    if (typeof item === 'string') return document.createTextNode(item);
    if (!item || !Array.isArray(item.children)) throw new Error('Invalid source tree');
    const {tag} = item;
    const heading = /^h[1-6]$/.test(tag);
    const math = READER_MATH_TAGS.has(tag);
    if ((!READER_HTML_TAGS.has(tag) && !math && !heading) || (inMath && !math)) throw new Error('Unsupported source element');
    if (math && !inMath && tag !== 'math') throw new Error('Math outside MathML');
    const node = math ? document.createElementNS('http://www.w3.org/1998/Math/MathML', tag)
      : document.createElement(heading ? `h${Math.min(6, 5 + Number(tag[1]) - headingBase)}` : tag);
    const attrs = item.attrs || {};
    if ((tag === 'colgroup' || tag === 'col') && Object.hasOwn(attrs, 'span')) {
      const span = attrs.span;
      if (typeof span !== 'string' || !/^\d{1,5}$/.test(span) || Number(span) < 1 || Number(span) > 1000) throw new Error('Unsupported column span');
      node.setAttribute('span', span);
    }
    if (tag === 'th' || tag === 'td') {
      if (typeof attrs.id === 'string') node.id = localId(attrs.id);
      if (typeof attrs.headers === 'string') node.setAttribute('headers', attrs.headers.trim().split(/\s+/).map(localId).join(' '));
      if (['row', 'col', 'rowgroup', 'colgroup'].includes(attrs.scope)) node.setAttribute('scope', attrs.scope);
      for (const key of ['rowspan', 'colspan']) {
        if (Object.hasOwn(attrs, key)) {
          const value = attrs[key];
          if (typeof value !== 'string' || !/^\d{1,5}$/.test(value) || Number(value) > (key === 'rowspan' ? 65534 : 1000) || (key === 'colspan' && Number(value) === 0)) throw new Error('Unsupported table span');
          node.setAttribute(key, value);
        }
      }
    }
    if (tag === 'ol' && Object.hasOwn(attrs, 'reversed')) node.setAttribute('reversed', '');
    for (const key of tag === 'ol' ? ['start'] : tag === 'li' ? ['value'] : []) {
      if (/^-?\d{1,6}$/.test(attrs[key])) node.setAttribute(key, attrs[key]);
    }
    if (math) {
      // No style, URL, event, href, annotation-xml or arbitrary namespace attrs.
      if (Object.keys(attrs).some(key => !READER_MATH_ATTRS.has(key) && !READER_MATH_METADATA.has(key) && !key.startsWith('on') && !key.startsWith('data-'))) throw new Error('Unsupported math attributes');
      if (Object.hasOwn(attrs, 'linethickness')) {
        if (tag !== 'mfrac' || typeof attrs.linethickness !== 'string' || !/^(?:thin|medium|thick|(?:\d+(?:\.\d+)?|\.\d+)(?:em|ex|px|in|cm|mm|pt|pc|%)?)$/.test(attrs.linethickness)) throw new Error('Unsupported fraction thickness');
        node.setAttribute('linethickness', attrs.linethickness);
      }
      for (const key of READER_MATH_ATTRS) {
        if (key !== 'linethickness' && Object.hasOwn(attrs, key)) {
          if (typeof attrs[key] !== 'string' || attrs[key].length >= 100 || !validReaderMathAttribute(key, attrs[key])) throw new Error('Unsupported math attributes');
          node.setAttribute(key, attrs[key]);
        }
      }
    }
    for (const child of item.children) node.append(build(child, depth + 1, inMath || math));
    if (tag === 'table' || tag === 'math') {
      const inline = tag === 'math' && attrs.display !== 'block';
      const scroll = readerElement(inline ? 'span' : 'div', undefined, inline ? 'source-inline-math' : 'source-scroll');
      scroll.tabIndex = 0;
      scroll.setAttribute('role', 'region');
      scroll.setAttribute('aria-label', tag === 'table' ? 'Source table; scroll horizontally if needed' : 'Source formula; scroll horizontally if needed');
      scroll.append(node);
      return scroll;
    }
    return node;
  }
  const fragment = document.createDocumentFragment();
  try {
    for (const node of reader.nodes) fragment.append(build(node));
    return fragment;
  } catch {
    return null; // Fail closed to the citation-check text, not partially rendered markup.
  }
}

function renderSourcePassage(target, passage, {claim = null, isFixture = false, onReturn}) {
  const add = (tag, text, cls) => { const node = readerElement(tag, text, cls); target.append(node); return node; };
  const returnButton = () => {
    const button = add('button', 'Return to answer', 'quiet source-return');
    button.type = 'button';
    button.addEventListener('click', onReturn);
  };
  target.replaceChildren();
  returnButton();
  add('h3', passage.title || 'Paper title not supplied');
  const metadata = add('dl', undefined, 'source-metadata');
  for (const [label, value] of [
    ['Source identity', passage.arxiv_id || 'Not supplied'],
    ['Version', passage.arxiv_id?.match(/v\d+$/)?.[0] || 'Not supplied'],
    ['Format', passage.source || 'Not supplied'],
    ['Section', passage.section || 'Not supplied'],
    ['PDF page', passage.page_number == null ? 'Not supplied; no PDF page mapping available' : String(passage.page_number)],
    ['Passage ID', passage.chunk_id || 'Not supplied'],
  ]) metadata.append(readerElement('dt', label), readerElement('dd', value));
  const url = (() => { try { return new URL(passage.source_url); } catch { return null; } })();
  if (url && ['https:', 'http:'].includes(url.protocol)) {
    const link = add('a', isFixture ? 'Open example source' : 'Open original paper', 'source-link');
    const location = passage.page_number != null ? `PDF page ${passage.page_number}` : (passage.section || 'No PDF page');
    link.setAttribute('aria-label', `${link.textContent}, ${passage.title || 'Paper title not supplied'}, ${location}, opens in a new tab`);
    link.href = url.href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  } else add('p', 'Original-source link not supplied.', 'meta');
  if (isFixture) add('p', 'Synthetic fixture evidence; not a verified paper.', 'meta');
  add('h4', 'Cited claim');
  add('p', claim?.text || 'No claim selected. You are browsing the available evidence.');
  const quotes = [...new Set((claim?.support || []).filter(item => item.chunk_id === passage.chunk_id).map(item => item.quote))];
  add('h4', 'Selected supporting quote');
  if (quotes.length) {
    for (const quote of quotes) add('blockquote', quote, 'source-exact-quote');
    add('p', 'Quote association retained from this claim. Quote membership is not independent verification of claim support.', 'meta');
  } else add('p', claim ? 'No exact supporting quote was supplied for this claim in this passage.' : 'Select a claim citation to retain its exact quote association.', 'meta');
  add('h4', passage.section || 'Source passage');
  const content = add('div', undefined, 'source-reading');
  const structured = structuredSource(passage.reader);
  if (structured) {
    content.append(structured);
    const structures = [...content.querySelectorAll('.source-scroll, .source-inline-math')];
    if (structures.length) {
      const navigation = readerElement('nav');
      navigation.setAttribute('aria-label', 'Source structure navigation');
      const links = readerElement('ul');
      const counts = {table: 0, formula: 0};
      for (const region of structures) {
        const table = region.querySelector(':scope > table');
        const kind = table ? 'table' : 'formula';
        const caption = table?.querySelector('caption')?.textContent.trim();
        const label = `Source ${kind} ${++counts[kind]}${caption ? ': ' + caption : ''}`;
        region.setAttribute('aria-label', `${label}; scroll horizontally if needed`);
        const item = readerElement('li');
        const button = readerElement('button', `Go to ${label.toLowerCase()}`, 'quiet');
        button.type = 'button';
        button.addEventListener('click', () => {
          region.focus({preventScroll: true});
          region.scrollIntoView({block: 'nearest'});
        });
        item.append(button); links.append(item);
      }
      navigation.append(links); content.before(navigation);
    }

    add('p', 'Structured view retained from source HTML. Not a reconstruction of the PDF or a certification of extraction completeness.', 'meta');
    add('p', `Source HTML SHA-256: ${passage.reader.source_sha256 || 'Not supplied'}`, 'meta');
    const text = add('details', undefined, 'source-check-text');
    text.append(readerElement('summary', 'Citation-check text (retained separately)'), readerElement('blockquote', passage.text));
  } else {
    renderPaperMath(content, passage.text);
    add('p', 'Structured headings, lists, source MathML, table relationships and figure descriptions are not available in this retained passage. Text and any explicit TeX are shown as supplied; missing structure has not been inferred.', 'meta');
  }
  if (!structured || !content.querySelector('figure')) add('p', 'No source-supplied figure description is retained for this passage. This does not establish whether the original contains figures.', 'meta');
  const limitations = Array.isArray(passage.reader?.limitations) ? passage.reader.limitations.filter(item => typeof item === 'string') : [];
  if (limitations.length) {
    add('h4', 'Extraction limitations');
    const list = add('ul');
    for (const limitation of limitations) list.append(readerElement('li', limitation));
  }
  if (passage.distance != null) add('p', `Retrieval distance: ${passage.distance} · Not confidence`, 'meta');
  returnButton();
}

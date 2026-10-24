/* Only explicit math delimiters are interpreted. All prose remains text nodes. */
function renderPaperMath(node, text) {
  // Single dollars deliberately stay literal: research prose often contains money.
  const expression = /\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)|\$\$([\s\S]*?)\$\$/g;
  let offset = 0;
  for (const match of text.matchAll(expression)) {
    node.append(document.createTextNode(text.slice(offset, match.index)));
    const tex = match[1] ?? match[2] ?? match[3];
    const displayMode = match[2] === undefined;
    const target = document.createElement('span');
    target.className = displayMode ? 'paper-math math-display' : 'paper-math';
    target.tabIndex = 0;
    target.setAttribute('role', 'region');
    target.setAttribute('aria-label', 'Formula, scroll horizontally if needed');
    try {
      if (!window.katex || tex.length > 12000) throw new Error('Math unavailable');
      katex.render(tex, target, {
        displayMode, throwOnError: true, trust: false, strict: 'ignore',
        maxExpand: 500, maxSize: 20, output: 'htmlAndMathml',
      });
    } catch {
      target.textContent = match[0];
      target.classList.add('math-fallback');
      target.title = 'Formula could not be rendered; original LaTeX is preserved.';
    }
    node.append(target);
    offset = match.index + match[0].length;
  }
  node.append(document.createTextNode(text.slice(offset)));
  return node;
}

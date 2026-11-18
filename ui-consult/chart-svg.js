/* Builds the dot-plot SVG for one evidence table. Shared by the page (app.js chartView) and the
   in-browser tests, so the tests measure the exact nodes the page draws (audit H1, M1).

   ChartSvg.build({document, table, plan, available, title, onOpen}) returns {root, layout}.
   - Geometry comes from EvidenceModel.chartLayout / panelScale: every panel keeps a positive
     drawing span, so x(min) < x(max) at any width; a frame narrower than the chart scrolls.
   - Paired charts give each dot its own control (data-point = "<column>|<chunk_id>") that opens
     its own row and cell through onOpen(row, cell, trigger).
   Text is always the cell text exactly as recorded; no value is computed or reformatted. */
(function (root, factory) {
  const api = factory(root.EvidenceModel);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ChartSvg = api;
})(typeof self !== 'undefined' ? self : this, function (EM) {
  'use strict';
  const SVGNS = 'http://www.w3.org/2000/svg';

  function build({document: doc, table, plan, available, title, onOpen}) {
    const svg = (tag, attrs, ...children) => {
      const node = doc.createElementNS(SVGNS, tag);
      for (const [key, value] of Object.entries(attrs || {})) if (value != null) node.setAttribute(key, value);
      for (const child of children.flat()) if (child != null) node.append(child);
      return node;
    };
    const text = (attrs, value) => { const node = svg('text', attrs); node.textContent = value; return node; };
    const point = (key, label, row, cell) => {
      const group = svg('g', {class: 'point', tabindex: '0', role: 'button', 'aria-label': label,
        'data-point': key, 'data-source-id': cell.source_id || '', 'data-chunk-id': row.chunk_id});
      const open = () => onOpen(row, cell, group);
      group.addEventListener('click', open);
      group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } });
      return group;
    };
    const paired = plan.form === 'paired_dot';
    const layout = EM.chartLayout(plan.panels.length, available);
    const {width} = layout, rowH = 40, top = 56, bottom = 40;
    const series = plan.panels.map(panel => EM.panelSeries(table, plan, panel));
    const rows = series[0];
    const height = top + rows.length * rowH + bottom;
    const rootNode = svg('svg', {viewBox: `0 0 ${width} ${height}`, width, height, class: 'chart-svg', role: 'group',
      'aria-label': `${title} as a dot plot. Each column has its own scale.`});
    rows.forEach((row, index) => {
      const y = top + index * rowH + rowH / 2;
      const cited = paired ? [row.rowA, row.rowB].some(r => r && r.citedBy.length) : row.row.citedBy.length;
      rootNode.append(svg('line', {x1: 0, x2: width, y1: y + rowH / 2, y2: y + rowH / 2, class: 'row-rule'}),
        text({x: 0, y: y + 5, class: `row-label${cited ? ' cited' : ''}`}, row.label));
    });
    plan.panels.forEach((panel, p) => {
      const x0 = layout.panelX(p), panelW = layout.panelW;
      const cells = paired ? series[p].flatMap(item => [item.a, item.b]) : series[p].map(item => item.cell);
      const values = cells.map(cell => cell.parsed.value);
      const sx = EM.panelScale(layout, p, values);
      const min = Math.min(...values), max = Math.max(...values);
      rootNode.append(text({x: x0 + panelW / 2, y: 22, class: 'panel-head', 'text-anchor': 'middle', 'data-panel': String(p)},
        panel.header.replace(/\\rho/g, 'ρ').replace(/\\Delta/g, 'Δ')));
      rootNode.append(svg('line', {x1: x0, x2: x0 + panelW, y1: top - 10, y2: top - 10, class: 'panel-rule', 'data-panel': String(p)}));
      if (min !== max) for (const value of [min, max]) {
        const x = sx(value);
        rootNode.append(svg('line', {x1: x, x2: x, y1: top - 4, y2: height - bottom + 4, class: 'axis-guide'}),
          text({x, y: height - 14, class: 'axis-end', 'text-anchor': 'middle', 'data-panel': String(p), 'data-end': value === min ? 'min' : 'max'},
            cells[values.indexOf(value)].text));
      }
      series[p].forEach((item, index) => {
        const y = top + index * rowH + rowH / 2;
        if (paired) {
          const xa = sx(item.a.parsed.value), xb = sx(item.b.parsed.value);
          rootNode.append(svg('line', {x1: xa, x2: xb, y1: y, y2: y, class: 'pair-line', 'aria-hidden': 'true'}));
          const [first, second] = plan.category.values;
          for (const [kind, cell, row, x, cls, other] of [[first, item.a, item.rowA, xa, 'dot-a', xb], [second, item.b, item.rowB, xb, 'dot-b', xa]]) {
            const group = point(`${panel.column}|${row.chunk_id}`, `${item.label}, ${kind}, ${panel.header}: ${cell.text}. Open source.`, row, cell);
            const leftOfPair = x < other || (x === other && cls === 'dot-a');
            group.append(svg('circle', {cx: x, cy: y, r: 5.5, class: cls}),
              text({x: leftOfPair ? x - 10 : x + 10, y: y + 4, class: `value${cls === 'dot-b' ? ' strong' : ''}`, 'text-anchor': leftOfPair ? 'end' : 'start'}, cell.text));
            rootNode.append(group);
          }
        } else {
          const x = sx(item.cell.parsed.value);
          const group = point(`${panel.column}|${item.row.chunk_id}`, `${item.label}, ${panel.header}: ${item.cell.text}. Open source.`, item.row, item.cell);
          group.append(svg('circle', {cx: x, cy: y, r: 5.5, class: 'dot-b'}), text({x: x + 10, y: y + 4, class: 'value strong'}, item.cell.text));
          rootNode.append(group);
        }
      });
    });
    return {root: rootNode, layout};
  }

  /* Keeps one chart in its frame. update(available) is called whenever the frame width may
     have changed. The SVG is rebuilt only when its drawn width changes (keeping nodes and focus
     otherwise), but the scroll state is recomputed EVERY time: two frame widths can share one
     SVG width (3 panels need 810px: an 810px frame fits, an 809px frame scrolls), so the
     "scrolls" class, tab stop and region label must follow the frame, not the SVG
     (verification blocker 3). A focused point is restored by its cell key after a rebuild. */
  function mount({document: doc, frame, table, plan, title, onOpen}) {
    let drawnWidth = null;
    function applyScroll(scrolls) {
      frame.classList.toggle('scrolls', scrolls);
      if (scrolls) {
        frame.tabIndex = 0;
        frame.setAttribute('role', 'region');
        frame.setAttribute('aria-label', `${title} chart, scrolls sideways`);
      } else {
        frame.removeAttribute('tabindex'); frame.removeAttribute('role'); frame.removeAttribute('aria-label');
      }
    }
    function update(available, {force = false} = {}) {
      const layout = EM.chartLayout(plan.panels.length, available);
      let rebuilt = false;
      if (force || drawnWidth !== layout.width || !frame.firstChild) {
        const active = doc.activeElement;
        const focused = active && frame.contains(active) ? active.getAttribute('data-point') : null;
        const built = build({document: doc, table, plan, available, title, onOpen});
        frame.replaceChildren(built.root);
        drawnWidth = layout.width;
        rebuilt = true;
        if (focused) {
          const escape = doc.defaultView && doc.defaultView.CSS ? doc.defaultView.CSS.escape : value => value;
          const target = built.root.querySelector(`[data-point="${escape(focused)}"]`);
          if (target) target.focus({preventScroll: true});
        }
      }
      applyScroll(layout.scrolls);
      return {layout, rebuilt};
    }
    return {update};
  }

  return {build, mount};
});

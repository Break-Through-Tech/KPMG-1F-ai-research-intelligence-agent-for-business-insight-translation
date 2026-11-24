/* Builds the dot-plot SVG for one evidence table. Shared by the page (app.js chartView) and the
   in-browser tests, so the tests measure the exact nodes the page draws (audit H1, M1).

   ChartSvg.build({document, table, plan, available, title, onOpen}) returns {root, layout}.
   - Geometry comes from EvidenceModel.chartLayout / panelScale: every panel keeps a positive
     drawing span, so x(min) < x(max) at any width; a frame narrower than the chart scrolls.
   - Paired charts give each dot its own control (data-point = "<column>|<chunk_id>") that opens
     its own row and cell through onOpen(row, cell, trigger).
   Text is always the cell text exactly as recorded; no value is computed or reformatted. */
(function (root, factory) {
  const api = factory(root.EvidenceModel, root.ChartSelect);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ChartSvg = api;
})(typeof self !== 'undefined' ? self : this, function (EM, CS) {
  'use strict';
  const SVGNS = 'http://www.w3.org/2000/svg';
  // SVG text cannot render TeX: show its readable form (ρ, Δ, ±) instead of the raw source.
  const plain = value => (CS ? CS.texPlain(String(value)) : String(value));

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
        wrappedText(svg, {x: 0, y: y + 5, class: `row-label${cited ? ' cited' : ''}`}, plain(row.label), Math.floor((layout.labelW - 12) / CHAR_W), 14));
    });
    plan.panels.forEach((panel, p) => {
      const x0 = layout.panelX(p), panelW = layout.panelW;
      const cells = paired ? series[p].flatMap(item => [item.a, item.b]) : series[p].map(item => item.cell);
      const values = cells.map(cell => cell.parsed.value);
      const sx = EM.panelScale(layout, p, values);
      const min = Math.min(...values), max = Math.max(...values);
      rootNode.append(text({x: x0 + panelW / 2, y: 22, class: 'panel-head', 'text-anchor': 'middle', 'data-panel': String(p)},
        plain(panel.header)));
      rootNode.append(svg('line', {x1: x0, x2: x0 + panelW, y1: top - 10, y2: top - 10, class: 'panel-rule', 'data-panel': String(p)}));
      if (min !== max) for (const value of [min, max]) {
        const x = sx(value);
        rootNode.append(svg('line', {x1: x, x2: x, y1: top - 4, y2: height - bottom + 4, class: 'axis-guide'}),
          text({x, y: height - 14, class: 'axis-end', 'text-anchor': value === min ? 'start' : 'end', 'data-panel': String(p), 'data-end': value === min ? 'min' : 'max'},
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
          // The value sits right of its dot unless that would cross the panel's right edge.
          const flip = x + 10 + plain(item.cell.text).length * CHAR_W > x0 + panelW - 6;
          group.append(svg('circle', {cx: x, cy: y, r: 5.5, class: 'dot-b'}),
            text({x: flip ? x - 10 : x + 10, y: y + 4, class: 'value strong', 'text-anchor': flip ? 'end' : 'start'}, plain(item.cell.text)));
          rootNode.append(group);
        }
      });
    });
    return {root: rootNode, layout};
  }

  /* Grouped (or single) horizontal bars for ONE metric whose unit and meaningful zero are confirmed
     (EvidenceModel.panelUnit). Every bar starts at the same zero line; its length is proportional to
     the cell value; its label is the cell text verbatim. Each bar is its own focusable control
     (data-point = "<column>|<chunk_id>") that opens its exact source cell. */
  function buildBars({document: doc, table, plan, panel, available, title, onOpen}) {
    if (!panel || !panel.unit || !panel.unit.zero) throw new Error('Bars need a confirmed unit with a meaningful zero.');
    const svg = (tag, attrs, ...children) => {
      const node = doc.createElementNS(SVGNS, tag);
      for (const [key, value] of Object.entries(attrs || {})) if (value != null) node.setAttribute(key, value);
      for (const child of children.flat()) if (child != null) node.append(child);
      return node;
    };
    const text = (attrs, value) => { const node = svg('text', attrs); node.textContent = value; return node; };
    const paired = plan.form === 'paired_dot';
    const series = EM.panelSeries(table, plan, panel);
    const cells = paired ? series.flatMap(item => [item.a, item.b]) : series.map(item => item.cell);
    const values = cells.map(cell => cell.parsed.value);
    const maxValue = Math.max(...values);
    const layout = EM.barLayout(available);
    const sx = EM.barScale(layout, maxValue > 0 ? maxValue : 1);
    const barH = 16, inner = 4, gap = 20, top = 12, bottom = 36;
    const groupH = paired ? barH * 2 + inner : barH;
    const height = top + series.length * (groupH + gap) - gap + bottom;
    const root = svg('svg', {viewBox: `0 0 ${layout.width} ${height}`, width: layout.width, height, class: 'chart-svg bars-svg', role: 'group',
      'aria-label': `${title}. Horizontal bars from zero; unit ${panel.unit.label}.`});
    const plotBottom = height - bottom + 6;
    root.append(svg('line', {x1: layout.x0, x2: layout.x0, y1: top - 6, y2: plotBottom, class: 'zero-line', 'data-zero': 'true'}));
    const maxCell = cells[values.indexOf(maxValue)];
    root.append(text({x: layout.x0, y: height - 12, class: 'axis-end', 'text-anchor': 'middle', 'data-end': 'zero'}, '0'),
      svg('line', {x1: sx(maxValue), x2: sx(maxValue), y1: top - 6, y2: plotBottom, class: 'axis-guide'}),
      text({x: sx(maxValue), y: height - 12, class: 'axis-end', 'text-anchor': 'middle', 'data-end': 'max'}, maxCell.text));
    const bar = (key, label, row, cell, y, cls) => {
      const group = svg('g', {class: 'point bar', tabindex: '0', role: 'button', 'aria-label': label,
        'data-point': key, 'data-source-id': cell.source_id || '', 'data-chunk-id': row.chunk_id});
      const end = sx(cell.parsed.value);
      group.append(svg('rect', {x: layout.x0, y, width: Math.max(0, end - layout.x0), height: barH, rx: 2, class: cls}),
        text({x: end + 8, y: y + barH - 3, class: `value${cls === 'bar-b' ? ' strong' : ''}`}, cell.text));
      const open = () => onOpen(row, cell, group);
      group.addEventListener('click', open);
      group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } });
      return group;
    };
    const unit = panel.unit.label === '%' ? '%' : ` (${panel.unit.label})`;
    series.forEach((item, index) => {
      const y = top + index * (groupH + gap);
      const cited = paired ? [item.rowA, item.rowB].some(r => r && r.citedBy.length) : item.row.citedBy.length;
      root.append(wrappedText(svg, {x: layout.labelW - 12, y: y + groupH / 2 + 5, class: `row-label${cited ? ' cited' : ''}`, 'text-anchor': 'end'}, plain(item.label), Math.floor((layout.labelW - 16) / CHAR_W), 14));
      if (paired) {
        const [first, second] = plan.category.values;
        root.append(bar(`${panel.column}|${item.rowA.chunk_id}`, `${item.label}, ${first}, ${panel.header}: ${item.a.text}${unit}. Open source.`, item.rowA, item.a, y, 'bar-a'),
          bar(`${panel.column}|${item.rowB.chunk_id}`, `${item.label}, ${second}, ${panel.header}: ${item.b.text}${unit}. Open source.`, item.rowB, item.b, y + barH + inner, 'bar-b'));
      } else {
        root.append(bar(`${panel.column}|${item.row.chunk_id}`, `${item.label}, ${panel.header}: ${item.cell.text}${unit}. Open source.`, item.row, item.cell, y, 'bar-b'));
      }
    });
    return {root, layout};
  }

  /* ---------- Shared pieces for the business-intelligence views (2026-11-22) ---------- */
  function kit(doc) {
    const svg = (tag, attrs, ...children) => {
      const node = doc.createElementNS(SVGNS, tag);
      for (const [key, value] of Object.entries(attrs || {})) if (value != null) node.setAttribute(key, value);
      for (const child of children.flat()) if (child != null) node.append(child);
      return node;
    };
    const text = (attrs, value) => { const node = svg('text', attrs); node.textContent = value; return node; };
    /* One focusable mark per source cell: Enter/Space or click opens that exact cell. */
    const mark = (key, label, row, cell, onOpen) => {
      const group = svg('g', {class: 'point', tabindex: '0', role: 'button', 'aria-label': label,
        'data-point': key, 'data-source-id': cell.source_id || '', 'data-chunk-id': row.chunk_id});
      const open = () => onOpen(row, cell, group);
      group.addEventListener('click', open);
      group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } });
      return group;
    };
    return {svg, text, mark};
  }
  /* Keep direct labels at least `gap` apart without leaving [lo, hi]; order is preserved. */
  function spread(items, gap, lo, hi) {
    const sorted = [...items].sort((a, b) => a.y - b.y);
    sorted.forEach((item, i) => { item.ly = Math.max(item.y, i ? sorted[i - 1].ly + gap : lo); });
    const over = sorted.length ? sorted[sorted.length - 1].ly - hi : 0;
    if (over > 0) for (let i = sorted.length - 1; i >= 0; i -= 1) {
      sorted[i].ly = Math.min(sorted[i].ly - over, i < sorted.length - 1 ? sorted[i + 1].ly - gap : hi);
    }
    return items;
  }
  const linear = (min, max, a, b) => (min === max ? () => (a + b) / 2 : value => a + ((value - min) / (max - min)) * (b - a));
  const numberOf = cell => (cell.parsed ? cell.parsed.value : CS && CS.parsePlusMinus(cell.text) ? CS.parsePlusMinus(cell.text).value : null);
  const SHAPES = ['circle', 'square', 'diamond', 'triangle'];
  const LABEL_MAX = 40;
  function shape(svg, kind, x, y, cls) {
    if (kind === 'square') return svg('rect', {x: x - 4.5, y: y - 4.5, width: 9, height: 9, class: cls});
    if (kind === 'diamond') return svg('path', {d: `M${x} ${y - 6}L${x + 6} ${y}L${x} ${y + 6}L${x - 6} ${y}Z`, class: cls});
    if (kind === 'triangle') return svg('path', {d: `M${x} ${y - 6}L${x + 6} ${y + 5}L${x - 6} ${y + 5}Z`, class: cls});
    return svg('circle', {cx: x, cy: y, r: 5, class: cls});
  }
  const fitWidth = (available, min, max) => {
    const frame = Math.max(0, Math.round(Number(available) || 0));
    const width = Math.max(min, Math.min(max, frame || max));
    return {width, scrolls: frame > 0 && width > frame};
  };

  /* Wrap a label into lines of at most `maxChars` (word boundaries; a single long word stays whole).
     Never truncates: source labels are shown in full. Returns a <text> with one <tspan> per line,
     vertically centred on y. */
  function wrapLines(value, maxChars) {
    const words = String(value).split(/\s+/).filter(Boolean);
    const lines = [];
    for (const word of words) {
      const last = lines[lines.length - 1];
      if (last && (last + ' ' + word).length <= maxChars) lines[lines.length - 1] = `${last} ${word}`;
      else lines.push(word);
    }
    return lines.length ? lines : [''];
  }
  function wrappedText(svg, attrs, value, maxChars, lineH = 15) {
    const lines = wrapLines(value, Math.max(8, maxChars));
    const node = svg('text', attrs);
    const y = Number(attrs.y) - ((lines.length - 1) * lineH) / 2;
    lines.forEach((line, i) => {
      const span = svg('tspan', {x: attrs.x, y: y + i * lineH});
      span.textContent = line;
      node.append(span);
    });
    node.lineCount = lines.length;
    return node;
  }
  const CHAR_W = 7; // ~13px system sans

  /* Slope chart: the two conditions of a paired table as two columns, one line per row label.
     Same pairing rule as the paired dot plot; y runs from the lowest to the highest printed value. */
  const SLOPE_MIN = 520;
  function buildSlope({document: doc, table, plan, panel, available, title, onOpen}) {
    const {svg, text, mark} = kit(doc);
    const layout = fitWidth(available, SLOPE_MIN, 900);
    const series = EM.panelSeries(table, plan, panel);
    const [first, second] = plan.category.values;
    const labelSpace = Math.min(320, Math.round(layout.width * 0.34));
    const xa = 120, xb = layout.width - labelSpace - 24;
    const maxChars = Math.floor((labelSpace - 64) / CHAR_W);
    const lines = Math.max(...series.map(item => wrapLines(plain(item.label), maxChars).length));
    const gap = Math.max(22, lines * 15 + 6);
    const top = 64, plotH = Math.max(280, series.length * gap + 24), bottom = 32, height = top + plotH + bottom;
    const values = series.flatMap(item => [item.a.parsed.value, item.b.parsed.value]);
    const sy = linear(Math.min(...values), Math.max(...values), top + plotH, top);
    const root = svg('svg', {viewBox: `0 0 ${layout.width} ${height}`, width: layout.width, height, class: 'chart-svg slope-svg', role: 'group',
      'aria-label': `${title}: ${plain(panel.header)}, ${first} to ${second}, one line per row. The vertical scale runs from the lowest to the highest value shown.`});
    root.append(text({x: xa, y: 28, class: 'panel-head', 'text-anchor': 'middle'}, first),
      text({x: xb, y: 28, class: 'panel-head', 'text-anchor': 'middle'}, second),
      svg('line', {x1: xa, x2: xa, y1: top - 16, y2: top + plotH + 8, class: 'axis-guide'}),
      svg('line', {x1: xb, x2: xb, y1: top - 16, y2: top + plotH + 8, class: 'axis-guide'}));
    const left = spread(series.map(item => ({item, y: sy(item.a.parsed.value)})), 20, top - 6, top + plotH + 6);
    const right = spread(series.map(item => ({item, y: sy(item.b.parsed.value)})), gap, top - 6, top + plotH + 6);
    series.forEach((item, index) => {
      const ya = sy(item.a.parsed.value), yb = sy(item.b.parsed.value);
      const cited = [item.rowA, item.rowB].some(r => r && r.citedBy.length);
      root.append(svg('line', {x1: xa, y1: ya, x2: xb, y2: yb, class: `slope-line${cited ? ' cited' : ''}`, 'aria-hidden': 'true'}));
      const ga = mark(`${panel.column}|${item.rowA.chunk_id}`, `${plain(item.label)}, ${first}, ${plain(panel.header)}: ${plain(item.a.text)}. Open source.`, item.rowA, item.a, onOpen);
      ga.append(svg('line', {x1: xa - 8, y1: ya, x2: xa - 14, y2: left[index].ly, class: 'leader', 'aria-hidden': 'true'}),
        svg('circle', {cx: xa, cy: ya, r: 5, class: 'dot-a'}), text({x: xa - 18, y: left[index].ly + 4, class: 'value', 'text-anchor': 'end'}, plain(item.a.text)));
      const gb = mark(`${panel.column}|${item.rowB.chunk_id}`, `${plain(item.label)}, ${second}, ${plain(panel.header)}: ${plain(item.b.text)}. Open source.`, item.rowB, item.b, onOpen);
      gb.append(svg('line', {x1: xb + 8, y1: yb, x2: xb + 14, y2: right[index].ly, class: 'leader', 'aria-hidden': 'true'}),
        svg('circle', {cx: xb, cy: yb, r: 5, class: 'dot-b'}),
        text({x: xb + 18, y: right[index].ly + 4, class: 'value strong'}, plain(item.b.text)),
        wrappedText(svg, {x: xb + 64, y: right[index].ly + 4, class: `row-label${cited ? ' cited' : ''}`}, plain(item.label), maxChars));
      root.append(ga, gb);
    });
    return {root, layout};
  }

  /* Line chart over an axis with a real order (ChartSelect.analyze → ordered).
     columns axis: x = the numbers in the column headers (true spacing), one series per row.
     rows axis: x = the numbers in the row labels, one series per chosen column (or all, when the
     columns share one scale). Series are named in an HTML legend (lineSeries), so long names wrap
     there instead of being clipped; the plot keeps marker shape, colour and dash per series. */
  const LINE_MIN = 340;
  function lineSeries(table, ordered, column) {
    return ordered.axis === 'columns'
      ? table.rows.map(row => ({label: row.cells[0].text, points: ordered.columns.map((col, i) => ({x: ordered.positions[i], cell: row.cells[col.column], row, header: col.header}))}))
      : (column === 'all' ? ordered.columns.map(col => col.column) : [column]).map(c => ({label: table.headers[c].text,
        points: table.rows.map((row, i) => ({x: ordered.positions[i], cell: row.cells[c], row, header: row.cells[0].text}))}));
  }
  function buildLine({document: doc, table, ordered, column, available, title, onOpen}) {
    const {svg, text, mark} = kit(doc);
    const layout = fitWidth(available, LINE_MIN, 1040);
    const series = lineSeries(table, ordered, column);
    const all = series.flatMap(s => s.points).filter(p => numberOf(p.cell) != null);
    const ys = all.map(p => numberOf(p.cell));
    const minP = all[ys.indexOf(Math.min(...ys))], maxP = all[ys.indexOf(Math.max(...ys))];
    const left = Math.max(56, Math.max(plain(minP.cell.text).length, plain(maxP.cell.text).length) * CHAR_W + 20);
    const right = 24, top = 24, plotH = layout.width < 560 ? 240 : 320, bottom = 72, height = top + plotH + bottom;
    const x0 = left, x1 = layout.width - right;
    const sx = linear(Math.min(...ordered.positions), Math.max(...ordered.positions), x0, x1);
    const sy = linear(Math.min(...ys), Math.max(...ys), top + plotH, top);
    const root = svg('svg', {viewBox: `0 0 ${layout.width} ${height}`, width: layout.width, height, class: 'chart-svg line-svg', role: 'group',
      'aria-label': `${title} as a line chart along “${plain(ordered.axisLabel)}”. The vertical scale runs from the lowest to the highest value shown; it does not start at zero.`});
    const ticks = ordered.axis === 'columns' ? ordered.columns.map((col, i) => [ordered.positions[i], col.header]) : table.rows.map((row, i) => [ordered.positions[i], row.cells[0].text]);
    root.append(svg('line', {x1: x0, x2: x1, y1: top + plotH, y2: top + plotH, class: 'panel-rule'}));
    // Thin the tick labels on narrow plots so they never collide (every tick keeps its grid line).
    const minGap = Math.max(...ticks.map(([, label]) => plain(label).length)) * CHAR_W + 10;
    let lastX = -Infinity;
    ticks.forEach(([value, label], i) => {
      const x = sx(value);
      root.append(svg('line', {x1: x, x2: x, y1: top, y2: top + plotH, class: 'grid-line'}));
      if (x - lastX >= minGap || i === ticks.length - 1 && x - lastX >= minGap / 2) {
        root.append(text({x, y: top + plotH + 20, class: 'axis-end', 'text-anchor': 'middle'}, plain(label)));
        lastX = x;
      }
    });
    root.append(wrappedText(svg, {x: (x0 + x1) / 2, y: height - 20, class: 'axis-title', 'text-anchor': 'middle'}, plain(ordered.axisLabel), Math.floor((x1 - x0) / CHAR_W)));
    for (const p of [minP, maxP]) {
      const y = sy(numberOf(p.cell));
      root.append(svg('line', {x1: x0 - 6, x2: x1, y1: y, y2: y, class: 'axis-guide'}),
        text({x: x0 - 12, y: y + 4, class: 'axis-end', 'text-anchor': 'end', 'data-end': p === minP ? 'min' : 'max'}, plain(p.cell.text)));
    }
    series.forEach((s, si) => {
      const pts = s.points.filter(p => numberOf(p.cell) != null);
      const cls = `series s${si % 8}`;
      root.append(svg('polyline', {points: pts.map(p => `${sx(p.x)},${sy(numberOf(p.cell))}`).join(' '), class: `line ${cls}`, 'data-dash': String(si % 4), 'aria-hidden': 'true'}));
      pts.forEach(p => {
        const g = mark(`${p.cell.column}|${p.row.chunk_id}`, `${plain(s.label)}, ${plain(ordered.axisLabel)} ${plain(p.header)}: ${plain(p.cell.text)}. Open source.`, p.row, p.cell, onOpen);
        g.append(shape(svg, SHAPES[si % 4], sx(p.x), sy(numberOf(p.cell)), `marker ${cls}`));
        root.append(g);
      });
    });
    return {root, layout};
  }
  /* A legend swatch for series `si`: its dash pattern and marker shape, same classes as the plot. */
  function legendSwatch(doc, si) {
    const {svg} = kit(doc);
    const cls = `series s${si % 8}`;
    return svg('svg', {viewBox: '0 0 32 14', width: 32, height: 14, class: 'chart-svg legend-swatch', 'aria-hidden': 'true'},
      svg('line', {x1: 1, x2: 31, y1: 7, y2: 7, class: `line ${cls}`, 'data-dash': String(si % 4)}),
      shape(svg, SHAPES[si % 4], 16, 7, `marker ${cls}`));
  }

  /* Trade-off scatter: x = a cost or resource column, y = an outcome column, one point per row.
     Both scales run from the lowest to the highest printed value (labelled), padded so no mark
     sits on the frame; never from zero. Point names wrap, never truncate. */
  const SCATTER_MIN = 480;
  function buildScatter({document: doc, table, xColumn, yColumn, available, title, onOpen}) {
    const {svg, text, mark} = kit(doc);
    const layout = fitWidth(available, SCATTER_MIN, 900);
    const pts = table.rows.map(row => ({row, xc: row.cells[xColumn], yc: row.cells[yColumn]}));
    const xs = pts.map(p => p.xc.parsed.value), ys = pts.map(p => p.yc.parsed.value);
    const yLabelW = Math.max(...pts.map(p => plain(p.yc.text).length)) * CHAR_W + 16;
    const labelSpace = Math.min(280, Math.round(layout.width * 0.32));
    const maxChars = Math.floor((labelSpace - 32) / (CHAR_W + 0.8)); // conservative: labels wrap rather than overrun
    const left = Math.max(72, yLabelW + 28), top = 24, plotH = layout.width < 600 ? 260 : 320, bottom = 64, height = top + plotH + bottom;
    const frameRight = layout.width - labelSpace;
    const padX = (frameRight - left) * 0.07, padY = plotH * 0.08;
    const x0 = left + padX, x1 = frameRight - padX, yTop = top + padY, yBottom = top + plotH - padY;
    const sx = linear(Math.min(...xs), Math.max(...xs), x0, x1), sy = linear(Math.min(...ys), Math.max(...ys), yBottom, yTop);
    const xh = plain(table.headers[xColumn].text), yh = plain(table.headers[yColumn].text);
    const root = svg('svg', {viewBox: `0 0 ${layout.width} ${height}`, width: layout.width, height, class: 'chart-svg scatter-svg', role: 'group',
      'aria-label': `${title}: ${yh} against ${xh}, one point per row. Both scales run from the lowest to the highest value shown.`});
    root.append(svg('rect', {x: left, y: top, width: frameRight - left, height: plotH, class: 'plot-frame'}));
    const xmin = pts[xs.indexOf(Math.min(...xs))].xc, xmax = pts[xs.indexOf(Math.max(...xs))].xc;
    const ymin = pts[ys.indexOf(Math.min(...ys))].yc, ymax = pts[ys.indexOf(Math.max(...ys))].yc;
    for (const [cell, end] of [[xmin, 'min'], [xmax, 'max']]) {
      const x = sx(cell.parsed.value);
      root.append(svg('line', {x1: x, x2: x, y1: top, y2: top + plotH, class: 'axis-guide'}),
        text({x, y: top + plotH + 20, class: 'axis-end', 'text-anchor': 'middle', 'data-end': `x-${end}`}, plain(cell.text)));
    }
    for (const [cell, end] of [[ymin, 'min'], [ymax, 'max']]) {
      const y = sy(cell.parsed.value);
      root.append(svg('line', {x1: left, x2: frameRight, y1: y, y2: y, class: 'axis-guide'}),
        text({x: left - 10, y: y + 4, class: 'axis-end', 'text-anchor': 'end', 'data-end': `y-${end}`}, plain(cell.text)));
    }
    root.append(wrappedText(svg, {x: (left + frameRight) / 2, y: height - 18, class: 'axis-title', 'text-anchor': 'middle'}, `${xh} →`, Math.floor((frameRight - left) / CHAR_W)),
      text({x: 14, y: top + plotH / 2, class: 'axis-title', 'text-anchor': 'middle', transform: `rotate(-90 14 ${top + plotH / 2})`}, `${yh} →`));
    const lineCount = Math.max(...pts.map(p => wrapLines(plain(p.row.cells[0].text), maxChars).length));
    const labels = spread(pts.map(p => ({p, y: sy(p.yc.parsed.value)})), lineCount * 15 + 6, top + 8, top + plotH - 4);
    labels.forEach(({p, ly}) => {
      const cx = sx(p.xc.parsed.value), cy = sy(p.yc.parsed.value);
      const cited = p.row.citedBy.length;
      const g = mark(`${yColumn}|${p.row.chunk_id}`, `${plain(p.row.cells[0].text)}: ${yh} ${plain(p.yc.text)}, ${xh} ${plain(p.xc.text)}. Open source.`, p.row, p.yc, onOpen);
      g.append(svg('circle', {cx, cy, r: 6, class: `dot-b${cited ? ' cited' : ''}`}),
        svg('line', {x1: cx + 8, y1: cy, x2: frameRight + 12, y2: ly, class: 'leader', 'aria-hidden': 'true'}),
        wrappedText(svg, {x: frameRight + 18, y: ly + 4, class: `row-label${cited ? ' cited' : ''}`}, plain(p.row.cells[0].text), maxChars));
      root.append(g);
    });
    return {root, layout};
  }

  /* Error bars: value ± half-width exactly as printed, only when the paper states what ± means.
     Each panel reserves room on its right for the printed "value ± range" so text never crosses
     into the next panel; label, marker and value share one row axis. */
  const ERR = {labelShare: 0.2, maxLabel: 220, minPanel: 300, gap: 32, valueSpace: 116, rowH: 44};
  function errLayout(count, available) {
    const frame = Math.max(0, Math.round(Number(available) || 0));
    let width = Math.max(560, frame || 900);
    const labelW = Math.min(ERR.maxLabel, Math.max(96, Math.round(width * ERR.labelShare)));
    const needed = labelW + count * ERR.minPanel + ERR.gap * (count - 1);
    if (width < needed) width = needed;
    const panelW = (width - labelW - ERR.gap * (count - 1)) / count;
    return {width, labelW, panelW, scrolls: frame > 0 && width > frame, panelX: i => labelW + i * (panelW + ERR.gap)};
  }
  function buildErrorBars({document: doc, table, columns, available, title, onOpen}) {
    const {svg, text, mark} = kit(doc);
    const layout = errLayout(columns.length, available);
    const top = 56, bottom = 24, height = top + table.rows.length * ERR.rowH + bottom;
    const root = svg('svg', {viewBox: `0 0 ${layout.width} ${height}`, width: layout.width, height, class: 'chart-svg err-svg', role: 'group',
      'aria-label': `${title} with error bars: each value with its printed ± range. Each column has its own scale.`});
    const labelChars = Math.floor((layout.labelW - 12) / CHAR_W);
    table.rows.forEach((row, index) => {
      const y = top + index * ERR.rowH + ERR.rowH / 2;
      root.append(svg('line', {x1: 0, x2: layout.width, y1: y + ERR.rowH / 2, y2: y + ERR.rowH / 2, class: 'row-rule'}),
        wrappedText(svg, {x: 0, y: y + 4, class: `row-label${row.citedBy.length ? ' cited' : ''}`}, plain(row.cells[0].text), labelChars));
    });
    columns.forEach((col, p) => {
      const x0 = layout.panelX(p) + 12, x1 = layout.panelX(p) + layout.panelW - ERR.valueSpace;
      const items = table.rows.map(row => ({row, cell: row.cells[col.column], pm: CS.parsePlusMinus(row.cells[col.column].text)}));
      const extents = items.flatMap(item => [item.pm.value - item.pm.err, item.pm.value + item.pm.err]);
      const sx = linear(Math.min(...extents), Math.max(...extents), x0, x1);
      root.append(text({x: layout.panelX(p) + layout.panelW / 2, y: 24, class: 'panel-head', 'text-anchor': 'middle'}, plain(col.header)),
        svg('line', {x1: layout.panelX(p), x2: layout.panelX(p) + layout.panelW, y1: top - 12, y2: top - 12, class: 'panel-rule'}));
      items.forEach((item, index) => {
        const y = top + index * ERR.rowH + ERR.rowH / 2;
        const lo = sx(item.pm.value - item.pm.err), hi = sx(item.pm.value + item.pm.err), x = sx(item.pm.value);
        const g = mark(`${col.column}|${item.row.chunk_id}`, `${plain(item.row.cells[0].text)}, ${plain(col.header)}: ${plain(item.cell.text)}. Open source.`, item.row, item.cell, onOpen);
        g.append(svg('line', {x1: lo, x2: hi, y1: y, y2: y, class: 'whisker'}),
          svg('line', {x1: lo, x2: lo, y1: y - 6, y2: y + 6, class: 'whisker'}), svg('line', {x1: hi, x2: hi, y1: y - 6, y2: y + 6, class: 'whisker'}),
          svg('circle', {cx: x, cy: y, r: 4.5, class: 'dot-b'}),
          text({x: x1 + 14, y: y + 4, class: 'value strong'}, plain(item.cell.text)));
        root.append(g);
      });
    });
    return {root, layout};
  }

  /* Keeps one chart in its frame. update(available) is called whenever the frame width may
     have changed. The SVG is rebuilt only when its drawn width changes (keeping nodes and focus
     otherwise), but the scroll state is recomputed EVERY time: two frame widths can share one
     SVG width (3 panels need 810px: an 810px frame fits, an 809px frame scrolls), so the
     "scrolls" class, tab stop and region label must follow the frame, not the SVG
     (verification blocker 3). A focused point is restored by its cell key after a rebuild.
     view: null or {kind: 'overview'} = every metric as dot plots (the original view);
     {kind: 'bars', panel} = one metric as bars from zero; {kind: 'dots', panel} = one metric as dots. */
  function mount({document: doc, frame, table, plan, title, onOpen, view = null}) {
    const kind = (view && view.kind) || 'overview';
    const shownPlan = kind === 'dots' ? {...plan, panels: [view.panel]} : plan;
    const builders = {
      bars: available => buildBars({document: doc, table, plan, panel: view.panel, available, title, onOpen}),
      slope: available => buildSlope({document: doc, table, plan, panel: view.panel, available, title, onOpen}),
      line: available => buildLine({document: doc, table, ordered: view.ordered, column: view.column, available, title, onOpen}),
      scatter: available => buildScatter({document: doc, table, xColumn: view.x, yColumn: view.y, available, title, onOpen}),
      errorbars: available => buildErrorBars({document: doc, table, columns: view.columns, available, title, onOpen}),
    };
    const fixed = {slope: [SLOPE_MIN, 900], line: [LINE_MIN, 1040], scatter: [SCATTER_MIN, 900]};
    const layoutFor = available => (kind === 'bars' ? EM.barLayout(available)
      : fixed[kind] ? fitWidth(available, ...fixed[kind])
        : kind === 'errorbars' ? errLayout(view.columns.length, available)
          : EM.chartLayout(shownPlan.panels.length, available));
    const render = available => (builders[kind] ? builders[kind](available)
      : build({document: doc, table, plan: shownPlan, available, title, onOpen}));
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
      const layout = layoutFor(available);
      let rebuilt = false;
      if (force || drawnWidth !== layout.width || !frame.firstChild) {
        const active = doc.activeElement;
        const focused = active && frame.contains(active) ? active.getAttribute('data-point') : null;
        const built = render(available);
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
    return {update, kind};
  }

  return {build, buildBars, buildSlope, buildLine, buildScatter, buildErrorBars, mount, spread, lineSeries, legendSwatch, wrapLines};
});

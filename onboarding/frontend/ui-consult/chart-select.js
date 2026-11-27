/* Chart eligibility and selection for evidence tables (business-intelligence views, 2026-11-22).
   Pure and deterministic: no DOM, no network, no model. Builds on EvidenceModel (evidence.js).

   For one table it works out the data shape (labels, numeric columns, units, pairing, ordered axes,
   source-stated uncertainty, cost measures) and which views that shape supports. The question can
   pick the default only among supported views. Every view draws the cell text exactly as recorded;
   parsed numbers only place marks. Nothing is averaged, totalled, differenced, converted or ranked.
   See design/VISUALIZATION-SYSTEM.md for the catalogue and rules. */
(function (root, factory) {
  const api = factory(root.EvidenceModel || (typeof require === 'function' ? require('./evidence.js') : null));
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ChartSelect = api;
})(typeof self !== 'undefined' ? self : this, function (EM) {
  'use strict';

  /* ---------- TeX to readable text (labels, SVG text, accessible names) ---------- */
  const SYMBOLS = {
    alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', varepsilon: 'ε', eta: 'η', theta: 'θ', kappa: 'κ', lambda: 'λ',
    mu: 'μ', nu: 'ν', pi: 'π', rho: 'ρ', sigma: 'σ', tau: 'τ', phi: 'φ', varphi: 'φ', chi: 'χ', psi: 'ψ', omega: 'ω',
    Gamma: 'Γ', Delta: 'Δ', Theta: 'Θ', Lambda: 'Λ', Sigma: 'Σ', Phi: 'Φ', Psi: 'Ψ', Omega: 'Ω',
    pm: '±', mp: '∓', times: '×', cdot: '·', leq: '≤', le: '≤', geq: '≥', ge: '≥', neq: '≠', approx: '≈', sim: '~',
    uparrow: '↑', downarrow: '↓', rightarrow: '→', to: '→', leftarrow: '←', infty: '∞', circ: '°', degree: '°',
    checkmark: '✓', dagger: '†', ddagger: '‡', star: '*', ast: '*', '%': '%', '&': '&', '#': '#', _: '_', ',': ' ', ';': ' ', quad: ' ', qquad: ' ',
    cup: '∪', cap: '∩', in: '∈', notin: '∉', subset: '⊂', subseteq: '⊆', setminus: '∖', ell: 'ℓ', partial: '∂', nabla: '∇',
    sum: 'Σ', prod: 'Π', cdots: '⋯', ldots: '…', dots: '…', prime: '′', propto: '∝', mid: '|', vert: '|', lvert: '|', rvert: '|', log: 'log', exp: 'exp',
  };
  // Layout-only commands: dropped, they carry no meaning in plain text.
  const LAYOUT = /\\(?:scriptstyle|displaystyle|textstyle|scriptscriptstyle|left|right|big|Big|bigg|Bigg|small|tiny|footnotesize|normalsize|large|bf|it|rm|sf|tt|limits|nolimits|!|:|>)(?![A-Za-z])/g;
  /* Readable text for a cell or header that may contain TeX. Used ONLY where markup cannot be
     rendered (SVG text, aria-labels, selector buttons); the visible table still renders the TeX. */
  function texPlain(text) {
    if (typeof text !== 'string' || !text.includes('\\') && !text.includes('$')) return text;
    // Known symbols first, while each command is still followed by its own delimiter ("\cup\mathcal{D}"
    // would otherwise read as "\cupD" once \mathcal{D} collapses to "D").
    let out = text.replace(/\$/g, '').replace(LAYOUT, '').replace(/\\([A-Za-z]+)(?![A-Za-z])/g, (whole, name) => (name in SYMBOLS ? SYMBOLS[name] : whole));
    for (let i = 0; i < 4; i += 1) {
      out = out.replace(/\\(?:mathcal|mathbf|mathrm|mathit|mathsf|mathbb|mathtt|text|textbf|textit|textrm|textsc|texttt|operatorname|boldsymbol|bm|emph|hat|bar|tilde|vec|overline|underline|widehat|widetilde)\s*\{([^{}]*)\}/g, '$1')
        .replace(/\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g, '$1/$2')
        .replace(/\\sqrt\s*\{([^{}]*)\}/g, '√$1');
    }
    out = out.replace(/\\([A-Za-z]+|[%&#_,;])/g, (whole, name) => (name in SYMBOLS ? SYMBOLS[name] : name));
    // Sub- and superscripts keep a visible separator: D_{2k}^{cup} → "D_2k^cup", S_{harm} → "S_harm".
    out = out.replace(/([_^])\s*\{([^{}]*)\}/g, '$1$2').replace(/[{}]/g, '');
    return out.replace(/\s+/g, ' ').trim();
  }

  /* ---------- Cell kinds ---------- */
  const PM = /^\s*([+\-−]?\d+(?:\.\d+)?)\s*(%)?\s*(?:\\pm|±|\+\/-)\s*(\d+(?:\.\d+)?)\s*(%)?\s*$/;
  /* "0.211 \pm 0.004" → value and half-width as printed. Both parts are the source's own numbers. */
  function parsePlusMinus(text) {
    if (typeof text !== 'string') return null;
    const match = PM.exec(text.replace(/\$/g, ''));
    if (!match) return null;
    const value = Number(match[1].replace('−', '-')), err = Number(match[3]);
    if (!Number.isFinite(value) || !Number.isFinite(err)) return null;
    if (Boolean(match[2]) !== Boolean(match[4]) && match[4]) return null; // "1.2 ± 3%" mixes units
    return {value, err, percent: Boolean(match[2] || match[4])};
  }

  /* What the ± means, ONLY if the caption or source notes name the statistic. "Over 5 runs" alone
     does not say whether ± is a standard deviation, a standard error or an interval. */
  const STATISTIC = /(?:\\pm|±)?\s*(?:\d+(?:\.\d+)?\s*)?(?:standard deviations?|standard errors?|std\.?(?:\s*dev\.?)?|s\.d\.|\bsd\b|\bs\.?e\.?m?\b|confidence intervals?|\bci\b)[^.;)]*/i;
  function uncertaintyMeaning(table) {
    const texts = [['caption', table.caption || ''], ...((table.notes || []).map(note => ['source note', note.text || '']))];
    for (const [basis, text] of texts) {
      const match = STATISTIC.exec(text);
      if (!match) continue;
      // Quote the paper's own clause. Start: include a directly preceding "mean"/"average"/"median".
      let start = match.index + (match[0].length - match[0].trimStart().length);
      const before = /\b(?:mean|means|average|median)\s*$/i.exec(text.slice(Math.max(0, start - 12), start));
      if (before) start -= before[0].length;
      // End: ".", ";" or a ")" that closes a bracket opened before the quote (balanced inside).
      let depth = 0, end = start;
      for (; end < text.length; end += 1) {
        const ch = text[end];
        if (ch === '(') depth += 1;
        else if (ch === ')') { if (depth === 0) break; depth -= 1; }
        else if ((ch === '.' && !/\d/.test(text[end + 1] || '')) || ch === ';') break;
      }
      return {quote: text.slice(start, Math.min(end, start + 160)).trim(), basis};
    }
    return null;
  }

  /* ---------- Vocabulary for axis meaning ---------- */
  const COST = /\b(cost|costs|latency|time|runtime|run[- ]time|wall[- ]clock|memory|price|usd|\$|flops|gflops|tflops|params?|parameters|gpu[- ]hours?|energy|calls|throughput|speed|seconds|hours)\b|\((?:s|ms|h|min|mins|gb|mb|usd|\$)\)/i;
  const ID_HEADER = /^\s*(?:#|no\.?|id|index|link id|row|idx)\s*$|\bid\b/i;
  const QUANTITY_HEADER = /\b(k|top-?\s*k|shots?|epochs?|steps?|iterations?|rounds?|years?|size|sizes|scale|samples?|budget|ratio|length|layers?|levels?|temperature|turns?|hops?|n|degree|depth|width|days?|weeks?|months?)\b/i;
  const NUMBERED = /^(.*?)(-?\d+(?:\.\d+)?)(\s*[A-Za-z%]{0,6})$/; // "Level 3", "8", "13B", "k=5"

  /* Positions for an ordered axis taken from labels that share one template ("Level 1..5",
     "1, 2, 3, 5, 8, 10", "7B, 13B, 70B") and increase strictly in source order. */
  function orderedPositions(labels) {
    if (labels.length < 3) return null;
    const parts = labels.map(label => NUMBERED.exec(texPlain(String(label || '')).trim()));
    if (parts.some(part => !part)) return null;
    const template = new Set(parts.map(part => `${part[1].trim().toLowerCase()}#${part[3].trim().toLowerCase()}`));
    if (template.size !== 1) return null;
    const values = parts.map(part => Number(part[2]));
    if (values.some((value, i) => i && !(value > values[i - 1]))) return null;
    return {values, prefix: parts[0][1].trim(), suffix: parts[0][3].trim()};
  }

  /* ---------- Shape analysis ---------- */
  const MAX_ROWS = 40;
  function analyze(table) {
    const out = {ok: false, reason: '', columns: [], labels: [], ordered: null, uncertainty: null, pairing: null};
    if (table.fidelity !== 'round_trip_ok') { out.reason = 'The structured cells did not match the cited source text.'; return out; }
    if (table.completeness !== 'complete_from_index') {
      out.reason = `Only ${table.retrievedCount} retrieved row${table.retrievedCount === 1 ? '' : 's'} of a larger table are loaded. Charts stay off until the complete table is loaded from the index, so no baseline or comparison row is left out.`;
      return out;
    }
    const rows = table.rows;
    if (rows.length < 2) { out.reason = 'A single row cannot be compared on a chart.'; return out; }
    if (rows.length > MAX_ROWS) { out.reason = `This table has ${rows.length} rows; a chart would not be legible.`; return out; }
    if (rows.some(row => row.row_group)) { out.reason = 'This table groups rows under sub-headings; a flat chart would lose that structure.'; return out; }
    out.labels = rows.map(row => row.cells[0].text);
    if (out.labels.some(label => !label)) { out.reason = 'Some rows have no label, so marks could not be named.'; return out; }
    out.ok = true;
    out.labelHeader = table.headers[0]?.text || '';
    out.uniqueLabels = new Set(out.labels).size === out.labels.length;
    out.idLabels = ID_HEADER.test(texPlain(out.labelHeader));
    out.plan = EM.chartPlan(table);
    out.pairing = out.plan.eligible && out.plan.form === 'paired_dot' ? out.plan.category : null;
    for (let column = 1; column < table.headers.length; column += 1) {
      if (out.pairing && column === out.pairing.column) continue;
      const header = table.headers[column].text;
      const cells = rows.map(row => row.cells[column]);
      const filled = cells.filter(cell => cell.text);
      const numbers = filled.filter(cell => cell.parsed);
      const pm = filled.map(cell => parsePlusMinus(cell.text));
      let kind = 'text';
      if (filled.length && numbers.length === filled.length) kind = 'number';
      else if (filled.length && pm.every(Boolean)) kind = 'pm';
      else if (numbers.length || pm.some(Boolean)) kind = 'mixed';
      const complete = filled.length === cells.length;
      const percentKinds = kind === 'number' ? new Set(numbers.map(cell => cell.parsed.percent)) : kind === 'pm' ? new Set(pm.map(p => p.percent)) : new Set();
      const safe = kind !== 'number' || numbers.every(cell => cell.parsed.safe !== false);
      const merged = cells.some(cell => cell.merged_from_previous_row);
      const pmOffender = pm.some(Boolean) ? filled.find((cell, i) => !pm[i]) || cells.find(cell => !cell.text) || null : null;
      out.columns.push({column, header, plain: texPlain(header), kind, complete, safe: safe && !merged && percentKinds.size <= 1,
        pmAny: pm.some(Boolean), pmOffender: pmOffender ? (pmOffender.text || '(empty)') : null,
        percent: percentKinds.size === 1 && [...percentKinds][0], shaded: numbers.length + pm.filter(Boolean).length,
        cost: COST.test(texPlain(header)), unitText: (/\(([^()]{1,24})\)\s*$/.exec(texPlain(header)) || [])[1] || null});
    }
    out.numeric = out.columns.filter(col => col.kind === 'number' && col.complete && col.safe);
    out.pmColumns = out.columns.filter(col => col.kind === 'pm' && col.complete && col.safe);
    // Ordered axis along the columns: value headers like 1,2,3,5,8,10 or "Level 1..5" (same template).
    const seq = [];
    for (const col of out.columns) {
      if (col.kind === 'number' || col.kind === 'pm' || col.kind === 'mixed') seq.push(col);
    }
    const positions = seq.length >= 3 ? orderedPositions(seq.map(col => col.header)) : null;
    if (positions) {
      const lineKind = seq.every(col => col.kind === 'number' && col.complete && col.safe) ? 'number'
        : seq.every(col => col.kind === 'pm' && col.complete && col.safe) ? 'pm' : null;
      out.ordered = {axis: 'columns', columns: seq, positions: positions.values, lineKind,
        axisLabel: out.labelHeader, percentKinds: new Set(seq.map(col => col.percent)).size};
    } else if (!out.idLabels && out.uniqueLabels) {
      // Rows form an axis when the label column names a quantity (k, size, steps, …) or every label
      // is a bare number, and the labels increase strictly in source order. Identifier columns never do.
      const rowsPos = orderedPositions(out.labels);
      const bare = out.labels.every(label => /^\s*-?\d+(?:\.\d+)?\s*$/.test(label));
      const lineColumns = [...out.numeric, ...out.pmColumns].sort((a, b) => a.column - b.column);
      if (rowsPos && lineColumns.length && (bare || QUANTITY_HEADER.test(texPlain(out.labelHeader)))) {
        // One shared scale only when every column reports the same kind of value (all plain or all
        // value ± range, one unit) and their printed ranges overlap: e.g. methods measured on one quantity.
        const values = col => rows.map(row => row.cells[col.column]).map(cell => (cell.parsed ? cell.parsed.value : parsePlusMinus(cell.text)?.value));
        const ranges = lineColumns.map(col => { const v = values(col); return [Math.min(...v), Math.max(...v)]; });
        const sameKind = new Set(lineColumns.map(col => `${col.kind}|${col.percent}`)).size === 1;
        const overlap = ranges.every(([lo, hi], a) => ranges.some(([lo2, hi2], b) => b !== a && lo <= hi2 && lo2 <= hi));
        out.ordered = {axis: 'rows', positions: rowsPos.values, axisLabel: out.labelHeader, columns: lineColumns, lineKind: 'number',
          shared: lineColumns.length > 1 && lineColumns.length <= 8 && sameKind && overlap};
      }
    }
    out.uncertainty = out.pmColumns.length ? uncertaintyMeaning(table) : null;
    return out;
  }

  /* ---------- Views ---------- */
  const KINDS = ['paired', 'slope', 'bars', 'line', 'errorbars', 'heatmap', 'scatter', 'dots'];
  // Plain names a business reader recognises; the technical name stays in the view's explanation.
  const LABELS = {paired: 'Before and after', slope: 'Change lines', bars: 'Bar chart', line: 'Trend line', errorbars: 'Values with uncertainty',
    heatmap: 'Colour-coded table', scatter: 'Cost vs. result', dots: 'Value comparison'};

  function viewsFor(table, analysis = analyze(table)) {
    const views = [];
    const add = (kind, eligible, reason, details = {}) => views.push({kind, label: LABELS[kind], eligible, reason, ...details});
    if (!analysis.ok) {
      for (const kind of KINDS) add(kind, false, analysis.reason);
      return views;
    }
    const plan = analysis.plan;
    const paired = Boolean(analysis.pairing);
    const pairText = paired ? `each ${texPlain(analysis.labelHeader).toLowerCase() || 'row'} appears once under “${analysis.pairing.values[0]}” and once under “${analysis.pairing.values[1]}” in the “${texPlain(analysis.pairing.header)}” column` : '';
    add('paired', paired, paired ? `Two conditions per row: ${pairText}.` : 'Rows do not pair into two conditions (each label once under exactly two values of one column).');
    add('slope', paired, paired ? `Shows the same two conditions as lines from left to right; ${pairText}.` : 'Needs the same two conditions for every row.');
    const zero = plan.eligible ? plan.panels.filter(panel => panel.unit && panel.unit.zero) : [];
    add('bars', zero.length > 0, zero.length ? `${zero.map(p => texPlain(p.header)).join(', ')}: the table states a percentage unit, so bars can start at a meaningful zero.`
      : plan.eligible ? 'No column states a percentage unit, so bars from zero could exaggerate or hide differences. Dots are used instead.' : plan.reason, {panels: zero});
    const ord = analysis.ordered;
    let lineOk = false, lineReason = 'No axis has a numeric, temporal or ordered meaning: rows are separate categories, so a line would imply a trend that is not there.';
    if (ord && ord.axis === 'columns') {
      if (!ord.lineKind) lineReason = 'The ordered columns mix plain numbers with other formats, so points could not all be placed.';
      else if (ord.percentKinds > 1) lineReason = 'The ordered columns mix percentages and plain numbers.';
      else if (analysis.labels.length > 8) lineReason = `${analysis.labels.length} series would overlap; a line chart stays legible up to 8.`;
      else { lineOk = true; lineReason = `The columns form an ordered axis (${ord.columns.map(col => texPlain(col.header)).join(', ')}) under “${texPlain(ord.axisLabel)}”, so each row is a series across it.`; }
    } else if (ord && ord.axis === 'rows') {
      lineOk = true; lineReason = `The rows form an ordered axis under “${texPlain(ord.axisLabel)}” (${analysis.labels.map(texPlain).join(', ')}).`;
    } else if (analysis.idLabels) lineReason = `“${texPlain(analysis.labelHeader)}” numbers the rows as identifiers, not as an ordered quantity, so no line is drawn.`;
    add('line', lineOk, lineReason, {ordered: ord});
    const pmCols = analysis.pmColumns;
    const errOk = pmCols.length > 0 && Boolean(analysis.uncertainty) && analysis.uniqueLabels;
    const partial = analysis.columns.find(col => col.pmAny && col.pmOffender);
    add('errorbars', errOk, errOk ? `The ${analysis.uncertainty.basis} states what ± means: “${texPlain(analysis.uncertainty.quote)}”.`
      : !pmCols.length && partial ? `Column “${partial.plain}” mixes value ± range cells with other cells such as “${texPlain(partial.pmOffender)}”, so error bars would be incomplete.`
      : !pmCols.length ? 'No column reports a value with ± uncertainty.'
        : !analysis.uncertainty ? 'The table reports ± values, but its caption and notes do not say whether ± is a standard deviation, a standard error or an interval, so no error bars are drawn.'
          : 'Row labels repeat, so error bars could not be named per row.', {columns: pmCols, meaning: analysis.uncertainty});
    const shadedCols = analysis.columns.filter(col => col.shaded > 0 && col.safe);
    const heatOk = analysis.labels.length >= 3 && shadedCols.length >= 2;
    add('heatmap', heatOk, heatOk ? `${shadedCols.length} numeric columns across ${analysis.labels.length} rows; each column is shaded on its own scale.`
      : analysis.labels.length < 3 ? 'A heatmap needs at least 3 rows.' : 'A heatmap needs at least 2 numeric columns.', {columns: shadedCols});
    const costCols = analysis.numeric.filter(col => col.cost);
    const otherCols = analysis.numeric.filter(col => !col.cost);
    const scatterOk = analysis.uniqueLabels && !analysis.idLabels && analysis.labels.length >= 3 && costCols.length > 0 && otherCols.length > 0;
    add('scatter', scatterOk, scatterOk ? `Plots ${otherCols.map(c => `“${c.plain}”`).join(' or ')} against the cost or resource measure ${costCols.map(c => `“${c.plain}”`).join(' or ')}, one point per row.`
      : !costCols.length ? 'No column measures cost, time or resources, so a trade-off chart would pair arbitrary columns.'
        : !otherCols.length ? 'There is no outcome column to compare with the cost column.'
          : analysis.idLabels ? 'Rows are identifiers, not alternatives to compare.' : 'A trade-off chart needs at least 3 distinct rows.', {x: costCols, y: otherCols});
    add('dots', plan.eligible, plan.eligible ? 'Each column on its own scale, values exactly as written.' : plan.reason);
    return views;
  }

  /* ---------- Question intent (deterministic keywords; the question never invents a view) ---------- */
  const INTENTS = [
    ['uncertainty', /\b(uncertain\w*|variance|confidence|error bars?|significan\w*|standard deviation|std|spread|reliab\w*|noise|seeds?)\b/i, ['errorbars']],
    ['tradeoff', /\b(trade-?offs?|cost|costs|costly|latency|efficien\w*|expensive|cheap\w*|speed|price|budget|overhead|resources?|compute)\b/i, ['scatter']],
    ['trend', /\b(trends?|over time|as .{1,40} (?:increases?|grows?|scales?)|scal(?:e|es|ing)|curves?|top-?k|over (?:epochs|steps|years|rounds)|growth|evolv\w*)\b/i, ['line']],
    ['improvement', /\b(improv\w*|gains?|increase[ds]?|boost\w*|before|after|uplift|effect of|impact of|lift|better than|reduc\w*|mitigat\w*)\b/i, ['paired', 'slope']],
    ['ranking', /\b(best|top|rank\w*|highest|lowest|leader\w*|outperform\w*|which .{0,30}(?:most|least|better|worse))\b/i, ['bars', 'dots']],
    ['multi', /\b(across (?:benchmarks|datasets|tasks|metrics|models)|all (?:metrics|benchmarks)|overview|heat ?map|matrix|compare .{0,30} (?:metrics|benchmarks))\b/i, ['heatmap']],
  ];
  function intentOf(question) {
    if (typeof question !== 'string' || !question.trim()) return null;
    for (const [name, pattern, kinds] of INTENTS) if (pattern.test(question)) return {name, kinds};
    return null;
  }
  const FALLBACK = ['paired', 'line', 'errorbars', 'bars', 'heatmap', 'dots', 'scatter'];
  const INTENT_TEXT = {uncertainty: 'asks about uncertainty', tradeoff: 'asks about cost or efficiency', trend: 'asks about a trend',
    improvement: 'asks about improvement', ranking: 'asks which performs best', multi: 'asks for an overview across metrics'};
  /* The default view: the question's intent if a matching view is supported, else the shape's
     natural view. Returns {kind, why} or {kind: 'table', why} when nothing can be charted. */
  function chooseDefault(views, question) {
    const ok = new Map(views.filter(view => view.eligible).map(view => [view.kind, view]));
    if (!ok.size) return {kind: 'table', why: views[0]?.reason || 'No chart fits this table.', intent: null};
    const intent = intentOf(question);
    if (intent) {
      const kind = intent.kinds.find(k => ok.has(k));
      if (kind) return {kind, intent: intent.name, why: `Your question ${INTENT_TEXT[intent.name]}. ${ok.get(kind).reason}`};
    }
    const kind = FALLBACK.find(k => ok.has(k) && !(k === 'heatmap' && (views.find(v => v.kind === 'heatmap').columns.length < 3)));
    const chosen = kind || FALLBACK.find(k => ok.has(k));
    return {kind: chosen, intent: intent ? intent.name : null,
      why: `${intent ? `Your question ${INTENT_TEXT[intent.name]}, but this table has no matching view. ` : ''}${ok.get(chosen).reason}`};
  }

  /* ---------- KPI tiles: cited headline values, verbatim ---------- */
  /* One tile per cited row (up to `limit`), showing the first chartable value column. For a paired
     table the tile shows both conditions as printed ("0.46 → 0.78"), taken from the two source rows. */
  function kpiTiles(table, limit = 4) {
    const cited = table.rows.filter(row => row.citedBy.length);
    if (!cited.length || table.fidelity !== 'round_trip_ok') return {tiles: [], more: 0};
    const analysis = table.completeness === 'complete_from_index' ? analyze(table) : null;
    const pairing = analysis && analysis.ok ? analysis.pairing : null;
    const valueColumn = row => {
      for (let column = 1; column < row.cells.length; column += 1) {
        if (pairing && column === pairing.column) continue;
        const cell = row.cells[column];
        if (cell.text && (cell.parsed || parsePlusMinus(cell.text))) return column;
      }
      return null;
    };
    const tiles = [], seen = new Set();
    for (const row of cited) {
      const label = row.cells[0].text;
      if (pairing) {
        if (seen.has(label)) continue;
        const pair = table.rows.filter(r => r.cells[0].text === label);
        const [a, b] = pairing.values.map(value => pair.find(r => r.cells[pairing.column].text === value));
        const column = a && b ? valueColumn(a) : null;
        if (column == null) continue;
        seen.add(label);
        tiles.push({label, header: table.headers[column].text, column, conditions: pairing.values,
          from: {row: a, cell: a.cells[column]}, to: {row: b, cell: b.cells[column]}, citedBy: [...new Set([...a.citedBy, ...b.citedBy])].sort((x, y) => x - y)});
      } else {
        const column = valueColumn(row);
        if (column == null) continue;
        tiles.push({label, header: table.headers[column].text, column, value: {row, cell: row.cells[column]}, citedBy: row.citedBy});
      }
    }
    return {tiles: tiles.slice(0, limit), more: Math.max(0, tiles.length - limit)};
  }

  /* ---------- Count check: a cited count of models versus the paper's own table ---------- */
  const WORDS = {two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12};
  const COUNTED = /\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s+(?:(?:different|diverse|distinct|open-?source|open-?weight|popular|base|backbone|large language|language)\s+)*(models|llms|backbones)\b/i;
  /* Returns an issue when an accepted claim states "N models" and a complete table from the same
     paper, whose first column names models, lists a different number of distinct labels. The paper
     may describe a different subset; this only asks a person to check. */
  function countCheck(result, table) {
    if (table.completeness !== 'complete_from_index' || !/\b(model|llm|backbone|base)\b/i.test(texPlain(table.headers[0]?.text || ''))) return null;
    const evidence = result?.evidence || [];
    for (const claim of result?.summary?.claims || []) {
      if (claim.kind === 'interpretation') continue;
      const match = COUNTED.exec(claim.text || '');
      if (!match) continue;
      const papers = new Set((claim.chunk_ids || []).map(id => evidence.find(p => p.chunk_id === id)?.arxiv_id).filter(Boolean));
      if (!papers.has(table.arxiv_id)) continue;
      const stated = WORDS[match[1].toLowerCase()] || Number(match[1]);
      const distinct = new Set(table.rows.map(row => row.cells[0].text)).size;
      if (stated === distinct) continue;
      const numbers = (claim.chunk_ids || []).map(id => evidence.findIndex(p => p.chunk_id === id) + 1).filter(n => n > 0);
      return {phrase: match[0], stated, distinct, citations: numbers, header: table.headers[0].text,
        text: `The answer says “${match[0]}”${numbers.length ? ` [${numbers.join('], [')}]` : ''}, quoting the paper. This table lists ${distinct} distinct entries under “${texPlain(table.headers[0].text)}”. The paper may describe a different subset; check which models the statement covers before quoting the count.`};
    }
    return null;
  }

  /* ---------- Plain-language framing (no new claims: built only from the table's own labels) ---------- */
  const lower = text => texPlain(String(text || '')).replace(/\s+/g, ' ').trim();
  /* The business question a chart answers, phrased from its labels: "How did Acc. change from
     Baseline to + CU- DPO for each base model?". It never states a result. */
  function businessQuestion(kind, table, details = {}) {
    const rows = lower(table.headers[0]?.text || 'row').toLowerCase();
    const metric = details.metric ? lower(details.metric) : 'the reported values';
    switch (kind) {
      case 'paired': case 'slope':
        return `How did ${metric} change from “${details.from}” to “${details.to}” for each ${rows}?`;
      case 'bars': case 'dots': return `How does ${metric} compare across ${rows}s?`;
      case 'line': return `How do the values change as ${lower(details.axis || rows)} increases?`;
      case 'scatter': return `How does ${lower(details.y)} compare with ${lower(details.x)}?`;
      case 'errorbars': return `How certain is each reported value of ${metric}?`;
      case 'heatmap': return `Where are values highest and lowest, column by column?`;
      default: return 'What does this table show?';
    }
  }
  /* Short glosses for common metric abbreviations in column labels. General definitions only,
     never a statement about this paper's results. */
  const GLOSSARY = [
    [/\bspear(?:man)?\.?\s*(?:ρ|\\rho)?/i, 'Spearman ρ', 'how closely two rankings agree (1 = same order)'],
    [/\bpearson\b/i, 'Pearson r', 'how closely two sets of values move together'],
    [/\bacc\.?(?:uracy)?(?![a-z])/i, 'Acc.', 'accuracy: share of answers that were correct'],
    [/\btop-?\s*(?:\d+|k)\b/i, 'Top-k', 'the right answer appears among the first k suggestions'],
    [/\bf1\b/i, 'F1', 'balance of precision and recall (higher is better)'],
    [/\bauc\b/i, 'AUC', 'how well scores separate two classes (0.5 = chance, 1 = perfect)'],
    [/\basr\b/i, 'ASR', 'attack success rate: share of attacks that worked (lower is safer)'],
    [/\bbleu\b/i, 'BLEU', 'word overlap with a reference answer'],
    [/\brouge/i, 'ROUGE', 'word overlap with a reference summary'],
    [/\bem\b|exact match/i, 'EM', 'exact match: answer identical to the reference'],
    [/±|\\pm/, '±', 'the uncertainty range the paper reports around each value'],
    [/↑|\\uparrow/, '↑', 'higher is better, as the paper marks it'], [/↓|\\downarrow/, '↓', 'lower is better, as the paper marks it'],
  ];
  function glossaryFor(labels) {
    const text = labels.map(label => String(label || '')).join(' | ');
    const seen = new Set(), out = [];
    for (const [pattern, term, meaning] of GLOSSARY) {
      if (pattern.test(text) && !seen.has(term)) { seen.add(term); out.push({term, meaning}); }
    }
    return out;
  }

  return {texPlain, parsePlusMinus, businessQuestion, glossaryFor, uncertaintyMeaning, orderedPositions, analyze, viewsFor, intentOf, chooseDefault,
    kpiTiles, countCheck, LABELS, KINDS};
});

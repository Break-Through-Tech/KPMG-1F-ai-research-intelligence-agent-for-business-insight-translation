/* Evidence model for reconstructed source tables and chart eligibility.
   Pure and deterministic: no DOM, no network, no model. Implements
   ui-next/design/EVIDENCE-VISUALIZATION-SPEC.md §3–§7.

   Display is ALWAYS the cell text exactly as recorded. Parsed numbers are used only to
   place points and to sort on request; nothing is computed, filled, converted or ranked. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EvidenceModel = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const ROW_INTRO = 'Derived source table row (HTML cell serialization, not verbatim prose).';
  const EMPTY_CELL = '[empty in source]';
  const NUMBER = /^([+\-−])?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?\s*(%)?$/;
  const MAX_CHART_ROWS = 40;
  const MAX_PANELS = 6;
  // A double keeps decimals with up to 15 significant digits distinct (9007199254740992 and
  // 9007199254740993 are not). Longer values stay in the table and never chart.
  const MAX_SAFE_DIGITS = 15;
  const COMPLETENESS_CHECK = 'extractor_table_audit_v1';

  /* §6 strict numeric parse. Anything with ±, arrows, brackets, slashes, ranges, TeX,
     letters, empty text or a lone dash is NOT a number for charting. */
  function parseNumber(text) {
    if (typeof text !== 'string') return null;
    const match = NUMBER.exec(text.trim());
    if (!match) return null;
    const [, sign, int, dec, pct] = match;
    const negative = sign === '-' || sign === '−';
    const digitsInt = int.replace(/,/g, '');
    const value = Number(`${negative ? '-' : ''}${digitsInt}${dec ? `.${dec}` : ''}`);
    if (!Number.isFinite(value)) return null;
    const significant = `${digitsInt}${dec || ''}`.replace(/^0+/, '').length;
    // A leading minus or plus without digits after it is rejected by the pattern.
    return {value, decimals: dec ? dec.length : 0, percent: Boolean(pct), signed: Boolean(sign),
      safe: significant <= MAX_SAFE_DIGITS,
      exact: {negative: negative && /[1-9]/.test(`${digitsInt}${dec || ''}`),
        int: digitsInt.replace(/^0+(?=\d)/, ''), dec: (dec || '').replace(/0+$/, '')}};
  }
  // Parsed objects made without `exact` (older saved state, hand-built tests): rebuild it.
  function exactOf(parsed) {
    if (parsed.exact) return parsed.exact;
    const [int, dec = ''] = Math.abs(parsed.value).toFixed(parsed.decimals || 0).split('.');
    return {negative: parsed.value < 0, int, dec: dec.replace(/0+$/, '')};
  }

  /* Exact decimal comparison of two parsed cells: no floating-point rounding, so values that
     differ only in their 16th digit still order correctly. */
  function compareParsed(a, b) {
    const x = exactOf(a), y = exactOf(b);
    if (x.negative !== y.negative) return x.negative ? -1 : 1;
    const sign = x.negative ? -1 : 1;
    if (x.int.length !== y.int.length) return (x.int.length - y.int.length) * sign;
    if (x.int !== y.int) return (x.int < y.int ? -1 : 1) * sign;
    const width = Math.max(x.dec.length, y.dec.length);
    const dx = x.dec.padEnd(width, '0'), dy = y.dec.padEnd(width, '0');
    return dx === dy ? 0 : (dx < dy ? -1 : 1) * sign;
  }

  /* A column sorts by number only when every non-empty cell is a plain number of one kind
     (all percentages or none). Mixed or text columns sort by their text, deterministically. */
  function columnSortKind(rows, column) {
    const cells = rows.map(row => row.cells[column]).filter(cell => cell && cell.text);
    if (!cells.length || cells.some(cell => !cell.parsed)) return 'text';
    return new Set(cells.map(cell => cell.parsed.percent)).size === 1 ? 'number' : 'text';
  }
  function sortRows(rows, column, dir) {
    const list = [...rows];
    if (column == null || !dir) return list;
    const kind = columnSortKind(rows, column);
    const index = new Map(list.map((row, i) => [row, i]));
    return list.sort((a, b) => {
      const x = a.cells[column], y = b.cells[column];
      // Empty cells always sit last, whichever the direction; ties keep source order.
      if (!x.text || !y.text) return (!x.text) - (!y.text) || index.get(a) - index.get(b);
      const order = kind === 'number' ? compareParsed(x.parsed, y.parsed)
        : x.text.localeCompare(y.text, 'en', {numeric: true});
      return order * dir || index.get(a) - index.get(b);
    });
  }

  /* Chart geometry (audit H1). Each panel needs room for its two end pads plus a positive
     drawing span; when the frame is too narrow the chart gets wider and its frame scrolls
     instead of squeezing panels until the scale runs backwards. */
  const CHART = {gap: 32, pad: 52, minSpan: 80, maxLabel: 240, labelShare: 0.24, minWidth: 640};
  const MIN_PANEL_WIDTH = CHART.pad * 2 + CHART.minSpan;
  function chartLayout(panelCount, available) {
    if (!Number.isInteger(panelCount) || panelCount < 1) throw new Error('chartLayout needs at least one panel.');
    const frame = Math.max(0, Math.round(Number(available) || 0));
    let width = Math.max(CHART.minWidth, frame || 880);
    const labelW = Math.min(CHART.maxLabel, Math.round(width * CHART.labelShare));
    const needed = labelW + panelCount * MIN_PANEL_WIDTH + CHART.gap * (panelCount - 1);
    if (width < needed) width = needed;
    const panelW = (width - labelW - CHART.gap * (panelCount - 1)) / panelCount;
    return {width, labelW, gap: CHART.gap, pad: CHART.pad, panelW, span: panelW - CHART.pad * 2,
      scrolls: frame > 0 && width > frame,
      panelX: index => labelW + index * (panelW + CHART.gap)};
  }
  /* Position of a value inside panel `index`: x(min) is always left of x(max). */
  function panelScale(layout, index, values) {
    if (!(layout.span > 0)) throw new Error('Chart panel has no drawing span.');
    const x0 = layout.panelX(index) + layout.pad;
    const min = Math.min(...values), max = Math.max(...values);
    if (min === max) return () => x0 + layout.span / 2;
    return value => x0 + ((value - min) / (max - min)) * layout.span;
  }

  /* §4.8 round-trip: rebuild the extractor's citation-check text from structured fields. */
  function rowText(passage) {
    const headers = passage.table_headers || [];
    const cells = passage.table_cells || [];
    const pairs = headers.map((header, index) => `${header.text}: ${(cells[index] && cells[index].text) || EMPTY_CELL}`).join('; ');
    let text = `${ROW_INTRO}\n${passage.title}\n${passage.caption}\n${passage.row_group ? `Row group: ${passage.row_group}; ` : ''}${pairs}`;
    const notes = (passage.source_notes || []).map(note => note.text);
    if (notes.length) text += `\nSource notes: ${notes.join(' ')}`;
    return text;
  }
  function roundTripOk(passage) {
    const headers = passage.table_headers, cells = passage.table_cells;
    if (!Array.isArray(headers) || !Array.isArray(cells) || headers.length !== cells.length || !headers.length) return false;
    if (cells.some((cell, index) => cell.column !== index || typeof cell.text !== 'string')) return false;
    return rowText(passage) === passage.text;
  }

  /* Key-order-independent comparison of header lists (saved briefs may reorder JSON keys). */
  const headerSignature = headers => JSON.stringify((headers || []).map(header =>
    [header.column, header.text, header.source_id ?? null, header.source_ids ?? null]));

  const isTableRow = passage => passage && passage.representation === 'linearized_table'
    && Array.isArray(passage.table_cells) && Array.isArray(passage.table_headers) && passage.table_id;
  const tableKey = passage => `${passage.arxiv_id}#${passage.table_id}`;

  /* Which citation numbers point at each passage: claims, interpretations, limitations, insights. */
  function citationMap(result) {
    const map = new Map();
    const evidence = result.evidence || [];
    const add = (chunkId, kind) => {
      const index = evidence.findIndex(passage => passage.chunk_id === chunkId);
      if (index < 0) return;
      if (!map.has(chunkId)) map.set(chunkId, {numbers: new Set(), kinds: new Set()});
      map.get(chunkId).numbers.add(index + 1);
      map.get(chunkId).kinds.add(kind);
    };
    for (const claim of result.summary?.claims || []) for (const id of claim.chunk_ids || []) add(id, claim.kind === 'interpretation' ? 'interpretation' : 'finding');
    for (const item of result.summary?.limitation_support || []) for (const id of item.chunk_ids || []) add(id, 'limitation');
    for (const item of result.business_insight?.implications || []) for (const id of item.chunk_ids || []) add(id, 'insight');
    return map;
  }

  function headerStatus(table) {
    if (table.header_review === 'verified') {
      return {verified: true, label: 'Column labels checked by a person.'};
    }
    const how = {
      latexml_guessed: "Column labels inferred from the paper's HTML.",
      first_row_assumed: 'First row assumed to be the column labels.',
      html_th_markup: "Column labels taken from the paper's header markup.",
    }[table.header_provenance] || 'Column label source not recorded.';
    return {verified: false, label: `${how} Not checked by a person.`};
  }

  /* §3: group retrieved table rows into tables, in source order. */
  function buildTables(result) {
    const cites = citationMap(result);
    const groups = new Map();
    (result.evidence || []).forEach((passage, index) => {
      if (!isTableRow(passage)) return;
      const key = tableKey(passage);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({passage, evidenceIndex: index});
    });
    const tables = [];
    for (const [key, items] of groups) {
      items.sort((a, b) => a.passage.table_row - b.passage.table_row);
      const first = items[0].passage;
      const consistent = items.every(({passage}) => passage.caption === first.caption
        && passage.source_sha256 === first.source_sha256
        && headerSignature(passage.table_headers) === headerSignature(first.table_headers));
      const fidelity = consistent && items.every(({passage}) => roundTripOk(passage)) ? 'round_trip_ok' : 'round_trip_mismatch';
      const table = {
        key, arxiv_id: first.arxiv_id, paper_title: first.title, table_id: first.table_id,
        caption: first.caption, html_url: first.html_url, pdf_url: first.pdf_url,
        source_sha256: first.source_sha256, extractor_version: first.extractor_version,
        header_provenance: first.header_provenance, header_review: first.header_review,
        headers: first.table_headers.map(header => ({...header})),
        notes: (first.source_notes || []).map(note => ({...note})),
        rows: items.map(({passage, evidenceIndex}) => rowFrom(passage, evidenceIndex, cites)),
        retrievedCount: items.length, rowCount: null,
        completeness: 'retrieved_rows_only', fidelity,
        sourceTexts: items.map(({passage}) => passage.text),
      };
      table.headerStatus = headerStatus(table);
      tables.push(table);
    }
    return tables;
  }
  function rowFrom(passage, evidenceIndex, cites) {
    const cite = cites.get(passage.chunk_id);
    return {
      chunk_id: passage.chunk_id, table_row: passage.table_row, row_label: passage.row_label,
      row_group: passage.row_group || null, evidenceIndex,
      retrieved: true, citedBy: cite ? [...cite.numbers].sort((a, b) => a - b) : [],
      cells: passage.table_cells.map(cell => ({...cell, parsed: parseNumber(cell.text)})),
    };
  }

  /* §8: accept a complete table from the read-only endpoint only if it agrees with the
     answer's own evidence on index, source hash, caption, headers and every retrieved cell. */
  function mergeComplete(table, full, answerIndexSha) {
    const fail = reason => ({ok: false, reason});
    if (!full || full.complete !== true || !Array.isArray(full.rows)) return fail('The index did not return a complete table.');
    if (!answerIndexSha || full.index_sha256 !== answerIndexSha) return fail('The loaded index differs from the one this answer used.');
    if (full.arxiv_id !== table.arxiv_id || full.table_id !== table.table_id) return fail('The index returned a different table.');
    if (full.source_sha256 !== table.source_sha256) return fail('The indexed paper source differs from the saved evidence.');
    if (full.caption !== table.caption) return fail('The indexed caption differs from the saved evidence.');
    if (headerSignature(full.headers) !== headerSignature(table.headers)) return fail('The indexed column labels differ from the saved evidence.');
    for (const field of ['header_provenance', 'header_review', 'extractor_version']) {
      if ((full[field] ?? null) !== (table[field] ?? null)) return fail(`The indexed ${field.replace(/_/g, ' ')} differs from the saved evidence.`);
    }
    if (notesSignature(full.source_notes) !== notesSignature(table.notes)) return fail('The indexed source notes differ from the saved evidence.');
    const numbers = full.rows.map(row => row && row.table_row);
    if (numbers.some((n, i) => n !== i + 1) || full.row_count !== full.rows.length) return fail('The indexed rows are not numbered 1..N.');
    // Audit H2: 1..N numbering cannot tell a whole table from a prefix. Completeness must come
    // from the extractor's own accepted-row count; without it (or if it differs) nothing merges.
    if (full.completeness_check !== COMPLETENESS_CHECK || !Number.isInteger(full.extractor_rows_emitted)) {
      return fail('The index could not show that this table is complete (no extractor row count).');
    }
    if (full.extractor_rows_emitted !== full.rows.length) {
      return fail(`The extractor emitted ${full.extractor_rows_emitted} rows but the index returned ${full.rows.length}.`);
    }
    const width = table.headers.length;
    for (const row of full.rows) {
      const problem = rowShapeProblem(row, width, table);
      if (problem) return fail(`Indexed row ${row && row.table_row}: ${problem}`);
    }
    for (const row of table.rows) {
      const match = full.rows.find(candidate => candidate.chunk_id === row.chunk_id);
      if (!match || match.table_row !== row.table_row) return fail('A retrieved row is missing from the indexed table.');
      if (match.row_label !== row.row_label) return fail(`Row ${row.table_row} label differs between the answer and the index.`);
      // Audit M3: grouping and merged-cell provenance change chart eligibility, so they must agree too.
      if ((match.row_group || null) !== (row.row_group || null)) return fail(`Row ${row.table_row} grouping differs between the answer and the index.`);
      if (cellsSignature(row.cells) !== cellsSignature(match.cells)) return fail(`Row ${row.table_row} differs between the answer and the index.`);
    }
    const byChunk = new Map(table.rows.map(row => [row.chunk_id, row]));
    const merged = {
      ...table,
      rows: full.rows.map(row => byChunk.get(row.chunk_id) || {
        chunk_id: row.chunk_id, table_row: row.table_row, row_label: row.row_label, row_group: row.row_group || null,
        evidenceIndex: null, retrieved: false, citedBy: [],
        cells: row.cells.map(cell => ({...cell, parsed: parseNumber(cell.text)})),
      }),
      rowCount: full.rows.length, completeness: 'complete_from_index',
      extractorRowsEmitted: full.extractor_rows_emitted,
      notes: (full.source_notes || []).map(note => ({...note})),
    };
    return {ok: true, table: merged};
  }
  /* Every field of every cell (except our own `parsed`), independent of key order. */
  const canonical = value => Array.isArray(value) ? value.map(canonical)
    : value && typeof value === 'object' ? Object.keys(value).sort().filter(key => key !== 'parsed').map(key => [key, canonical(value[key])])
      : value;
  const cellsSignature = cells => JSON.stringify(canonical(cells || []));
  const notesSignature = notes => JSON.stringify(canonical(notes || []));
  const CELL_KEYS = new Set(['row', 'column', 'text', 'source_id', 'merged_from_previous_row', 'parsed']);
  function rowShapeProblem(row, width, table) {
    if (!row || typeof row !== 'object') return 'not a row object.';
    if (typeof row.chunk_id !== 'string' || !row.chunk_id.startsWith(`${table.arxiv_id}_table_`)) return 'its passage ID belongs to another paper.';
    if (row.row_group != null && typeof row.row_group !== 'string') return 'its row group is not text.';
    if (!Array.isArray(row.cells) || row.cells.length !== width) return 'it does not have one cell per column.';
    for (let column = 0; column < width; column += 1) {
      const cell = row.cells[column];
      if (!cell || cell.column !== column || typeof cell.text !== 'string') return `cell ${column + 1} is malformed.`;
      if (cell.row !== undefined && cell.row !== row.table_row) return `cell ${column + 1} names another row.`;
      if (cell.merged_from_previous_row !== undefined && cell.merged_from_previous_row !== true) return `cell ${column + 1} has unknown merge provenance.`;
      if (Object.keys(cell).some(key => !CELL_KEYS.has(key))) return `cell ${column + 1} carries unknown fields.`;
    }
    if (row.row_label !== row.cells[0].text) return 'its label does not match its first cell.';
    return null;
  }

  /* §5 chart eligibility. Returns {eligible, reason, form, panels, excluded, category}. */
  function chartPlan(table) {
    const no = reason => ({eligible: false, reason, panels: [], excluded: []});
    if (table.fidelity !== 'round_trip_ok') return no('The structured cells did not match the cited source text, so this table is not charted.');
    if (table.completeness !== 'complete_from_index') {
      return no(`This answer retrieved ${table.retrievedCount} row${table.retrievedCount === 1 ? '' : 's'} of a larger table. A chart could leave out baselines or comparison rows, so it stays off until the full table is loaded from the index.`);
    }
    const rows = table.rows;
    if (rows.length < 2) return no('A single row cannot be compared on a chart.');
    if (rows.length > MAX_CHART_ROWS) return no(`This table has ${rows.length} rows; a chart would not be legible. Use the table.`);
    if (rows.some(row => row.row_group)) return no('This table groups rows under sub-headings; a flat chart would lose that structure.');
    const width = table.headers.length;
    if (width < 2) return no('This table has no value columns.');
    const labels = rows.map(row => row.cells[0].text);
    if (labels.some(label => !label)) return no('Some rows have no label, so points could not be named.');
    let category = null;
    if (new Set(labels).size !== labels.length) {
      // Repeated labels are only chartable as a two-way pairing: each label appears once
      // under each of exactly two values of one text column (for example Baseline / + Method).
      for (let column = 1; column < width; column += 1) {
        const values = rows.map(row => row.cells[column].text);
        if (values.some(value => !value || parseNumber(value))) continue;
        const kinds = [...new Set(values)];
        if (kinds.length !== 2) continue;
        const pairs = new Map();
        rows.forEach((row, index) => {
          const key = labels[index];
          if (!pairs.has(key)) pairs.set(key, []);
          pairs.get(key).push(values[index]);
        });
        const clean = [...pairs.values()].every(list => list.length === 2 && list[0] !== list[1]);
        if (clean) { category = {column, values: kinds, header: table.headers[column].text}; break; }
      }
      if (!category) return no('Row labels repeat without a clean two-way pairing, so rows cannot be told apart on a chart.');
    }
    const panels = [], excluded = [];
    for (let column = 1; column < width; column += 1) {
      if (category && column === category.column) continue;
      const header = table.headers[column].text;
      const cells = rows.map(row => row.cells[column]);
      const texts = cells.map(cell => cell.text);
      if (!cells.some(cell => cell.parsed)) continue; // no plain number at all: a text or symbol column, not a measurement
      const empty = texts.findIndex(text => !text);
      if (empty >= 0) { excluded.push({column, header, reason: `Row "${labels[empty]}" is empty in the source.`}); continue; }
      const bad = cells.find(cell => !cell.parsed);
      if (bad) { excluded.push({column, header, reason: `"${bad.text}" is not a plain number`}); continue; }
      const kinds = new Set(cells.map(cell => cell.parsed.percent));
      if (kinds.size > 1) { excluded.push({column, header, reason: 'Mixes percentages and plain numbers.'}); continue; }
      const unsafe = cells.find(cell => cell.parsed.safe === false || !Number.isFinite(cell.parsed.value));
      if (unsafe) { excluded.push({column, header, reason: `"${unsafe.text}" has too many digits to place exactly on a chart`}); continue; }
      const merged = rows.findIndex(row => row.cells[column].merged_from_previous_row);
      if (merged >= 0) { excluded.push({column, header, reason: `Row "${labels[merged]}" repeats a value merged across rows in the source.`}); continue; }
      panels.push({column, header, percent: cells[0].parsed.percent, unit: panelUnit(table, column, cells)});
    }
    if (!panels.length) {
      return {...no(excluded.length ? `No column can be charted: ${excluded[0].header}: ${excluded[0].reason}` : 'This table has no columns of plain numbers to chart (its values are text or symbols).'), excluded};
    }
    return {eligible: true, reason: '', form: category ? 'paired_dot' : 'dot', category,
      panels: panels.slice(0, MAX_PANELS), excluded, truncatedPanels: Math.max(0, panels.length - MAX_PANELS)};
  }

  /* Unit and meaningful zero for one value column (chart-first design, 2026-11-17).
     Bars are drawn only when the paper itself states a percentage unit, so zero means "none":
     every cell carries "%", or the column header says "%", or the caption states exactly one
     parenthetical unit containing "%" (e.g. "(Pass@1, %)"). Values must then lie in 0..100.
     Nonnegative numbers alone are NOT enough: accuracies written as 0.46, correlations, scores
     or losses without a stated unit stay on a dot or dumbbell plot. The label is quoted verbatim. */
  const CAPTION_UNIT = /\(([^()]*%[^()]*)\)/g;
  function panelUnit(table, column, cells) {
    const header = table.headers[column]?.text || '';
    const values = cells.map(cell => cell.parsed && cell.parsed.value);
    const inRange = values.every(value => Number.isFinite(value) && value >= 0 && value <= 100);
    const none = reason => ({unit: null, label: null, basis: null, zero: false, reason});
    let found = null;
    if (cells.every(cell => cell.parsed && cell.parsed.percent)) found = {label: '%', basis: 'cells'};
    else if (/%|\bpercent(?:age)?\b/i.test(header)) found = {label: header, basis: 'column label'};
    else {
      const units = [...(table.caption || '').matchAll(CAPTION_UNIT)].map(match => match[1].trim());
      if (units.length === 1) found = {label: units[0], basis: 'caption'};
      else if (units.length > 1) return none('The caption states more than one percentage unit, so this column\'s unit is not certain.');
    }
    if (!found) return none('No unit with a meaningful zero is stated for this column.');
    if (!inRange) return none(`Values fall outside 0–100, which does not fit the stated unit "${found.label}".`);
    return {unit: '%', label: found.label, basis: found.basis, zero: true, reason: ''};
  }

  /* A chart title built from the table's own words: "Table 4: DM by base model, Baseline vs + CU- DPO". */
  function chartTitle(table, plan, panel) {
    const match = /^(Table\s*[A-Za-z]?\d+[a-z]?)/.exec(table.caption || '');
    const name = match ? match[1].replace(/\s+/g, ' ') : `Table ${table.table_id}`;
    const by = (table.headers[0]?.text || 'row').toLowerCase();
    const metric = panel ? panel.header : plan.panels.map(p => p.header).join(', ');
    return `${name}: ${metric} by ${by}${plan.form === 'paired_dot' ? `, ${plan.category.values[0]} vs ${plan.category.values[1]}` : ''}`;
  }

  /* The takeaway is never written by the chart: it is the answer's own accepted, cited finding
     about this table (quotes already checked against the source), or nothing. */
  function takeawayFor(table, result) {
    if (!result || result.summary?.status !== 'ok') return null;
    const ids = new Set(table.rows.map(row => row.chunk_id));
    const evidence = result.evidence || [];
    for (const claim of result.summary.claims || []) {
      if (claim.kind !== 'finding' || !(claim.chunk_ids || []).some(id => ids.has(id))) continue;
      const numbers = (claim.chunk_ids || []).map(id => evidence.findIndex(p => p.chunk_id === id) + 1).filter(n => n > 0);
      return {text: claim.text, citations: [...new Set(numbers)].sort((a, b) => a - b)};
    }
    return null;
  }

  /* Explicit chart request, same rule as the backend (chart_preview.py). */
  const CHART_INTENT = /\b(?:charts?|graphs?|plots?|plotting|visuali[sz](?:e|ed|ing|ation)|bar\s+charts?|diagram)\b/i;
  const chartIntent = query => typeof query === 'string' && CHART_INTENT.test(query);

  /* Chart preview (POST /api/chart-preview): the page re-runs its own checks before drawing.
     The retrieved rows must round-trip to their source text, and the complete table must pass
     mergeComplete (extractor row count, index and source hashes, headers, every retrieved cell).
     Anything that fails stays out of the chart, with its reason. */
  function previewTables(preview) {
    const out = [], refused = [];
    if (!preview || !Array.isArray(preview.tables) || !Array.isArray(preview.evidence)) return {tables: out, refused};
    const pseudo = {evidence: preview.evidence, summary: {claims: []}};
    const built = new Map(buildTables(pseudo).map(table => [table.key, table]));
    for (const entry of preview.tables) {
      const table = built.get(entry.key);
      if (entry.status !== 'complete' || !entry.table) { refused.push({key: entry.key, reason: entry.reason || 'The index could not show that this table is complete.'}); continue; }
      if (!table) { refused.push({key: entry.key, reason: 'The retrieved rows for this table were not returned.'}); continue; }
      if (table.fidelity !== 'round_trip_ok') { refused.push({key: entry.key, reason: 'The structured cells did not match the source text.'}); continue; }
      const merged = mergeComplete(table, entry.table, preview.index_sha256);
      if (!merged.ok) { refused.push({key: entry.key, reason: merged.reason}); continue; }
      // Rows are not part of an answer yet: no citation numbers, no evidence-list position.
      merged.table.rows.forEach(row => { row.evidenceIndex = null; row.citedBy = []; });
      out.push({table: merged.table, plan: chartPlan(merged.table), entry});
    }
    return {tables: out, refused};
  }

  /* Horizontal bar geometry: one shared zero on the left, bars grow right in proportion to value. */
  const BARS = {minWidth: 560, maxLabel: 220, minLabel: 120, labelShare: 0.26, valueSpace: 72, minSpan: 220, right: 16};
  function barLayout(available) {
    const frame = Math.max(0, Math.round(Number(available) || 0));
    let width = Math.max(BARS.minWidth, frame || 880);
    const labelW = Math.max(BARS.minLabel, Math.min(BARS.maxLabel, Math.round(width * BARS.labelShare)));
    if (width - labelW - BARS.valueSpace - BARS.right < BARS.minSpan) width = labelW + BARS.minSpan + BARS.valueSpace + BARS.right;
    const span = width - labelW - BARS.valueSpace - BARS.right;
    return {width, labelW, span, x0: labelW, scrolls: frame > 0 && width > frame};
  }
  function barScale(layout, max) {
    if (!(layout.span > 0) || !(max > 0)) throw new Error('Bar chart needs a positive span and maximum.');
    return value => layout.x0 + (value / max) * layout.span;
  }

  /* Points for one chart panel: verbatim text plus parsed value, in source row order. */
  function panelSeries(table, plan, panel) {
    const rows = table.rows;
    if (plan.form === 'paired_dot') {
      const [a, b] = plan.category.values;
      const order = [];
      const by = new Map();
      for (const row of rows) {
        const label = row.cells[0].text;
        if (!by.has(label)) { by.set(label, {label, points: {}, rows: {}}); order.push(label); }
        const kind = row.cells[plan.category.column].text;
        by.get(label).points[kind] = row.cells[panel.column];
        by.get(label).rows[kind] = row;
      }
      return order.map(label => {
        const entry = by.get(label);
        return {label, a: entry.points[a], b: entry.points[b], rowA: entry.rows[a], rowB: entry.rows[b]};
      });
    }
    return rows.map(row => ({label: row.cells[0].text, cell: row.cells[panel.column], row}));
  }

  /* §9: prose numbers are never tabulated. Only table rows produce tables. */
  function studies(result) {
    const papers = new Map();
    (result.evidence || []).forEach((passage, index) => {
      const id = passage.arxiv_id || passage.title || 'unknown';
      if (!papers.has(id)) papers.set(id, {arxiv_id: passage.arxiv_id, title: passage.title, html_url: passage.html_url || passage.source_url,
        passages: [], tables: new Map(), citations: new Set()});
      const paper = papers.get(id);
      paper.passages.push(index + 1);
      if (isTableRow(passage) && !paper.tables.has(passage.table_id)) {
        paper.tables.set(passage.table_id, {table_id: passage.table_id, caption: passage.caption,
          headers: passage.table_headers.map(header => header.text)});
      }
    });
    const cites = citationMap(result);
    (result.evidence || []).forEach((passage, index) => {
      if (cites.has(passage.chunk_id)) papers.get(passage.arxiv_id || passage.title || 'unknown').citations.add(index + 1);
    });
    return [...papers.values()].map(paper => ({...paper, tables: [...paper.tables.values()],
      citations: [...paper.citations].sort((a, b) => a - b)}));
  }

  /* One generated list of what still needs a person, each item tied to the field it came from. */
  function verificationItems(demo, tables) {
    const result = demo.result;
    const items = [];
    if (!result) return items;
    if (result.summary?.support_check) {
      items.push({text: 'Claim support was checked by exact quote membership only, not by meaning. Read each cited quote against its claim.',
        origin: `summary.support_check = ${result.summary.support_check}`});
    }
    if (result.summary?.quality_review) {
      items.push({text: 'The relevance and support review was done by a model, not an independent person.',
        origin: `summary.quality_review.reviewer = ${result.summary.quality_review.reviewer || 'model'}`});
    }
    for (const table of tables) {
      if (!table.headerStatus.verified) {
        items.push({text: `Check the column labels of ${table.table_id} (${table.paper_title}) against the paper.`,
          origin: `header_review = ${table.header_review || 'not recorded'}`});
      }
      if (table.fidelity !== 'round_trip_ok') {
        items.push({text: `${table.table_id}: structured cells did not match the cited text; rely on the paper.`, origin: 'round-trip check'});
      }
    }
    if (demo.plain_language?.status === 'available' && demo.plain_language.claims?.length) {
      items.push({text: 'Plain-language rewrites have not been reviewed for meaning and uncertainty.', origin: 'plain_language.status = available'});
    }
    const checkpoint = result.regulatory_checkpoint;
    if (checkpoint && checkpoint.status !== 'assessed') {
      items.push({text: `Risk & compliance assessment is ${checkpoint.status}; no regulatory conclusion exists.`, origin: 'regulatory_checkpoint.status'});
    }
    if (result.business_insight?.implications?.length) {
      items.push({text: 'Business implications are conditional interpretations; confirm the assumptions with the client context.',
        origin: 'business_insight.implications[].assumptions'});
    }
    const decision = demo.library?.reviews?.at(-1)?.decision;
    if (decision !== 'approve') {
      items.push({text: decision ? `The latest human review is "${decision}"; this version is not approved.`
        : demo.library ? 'No person has approved this saved version yet. Record a review.' : 'No person has approved this answer. Save it as a brief and record a review.',
        origin: demo.library ? 'brief review history' : 'not saved'});
    }
    return items;
  }


  /* Papers the question names, in the order the question names them. A paper counts as named when its
     full title, or the part before the first colon (at least 4 characters), appears in the question as
     whole words. Matching only; nothing about the evidence changes. */
  function namedStudies(studies, question) {
    const norm = text => String(text || '').toLowerCase().replace(/[“”"'‘’]/g, '').replace(/\s+/g, ' ').trim();
    const q = norm(question);
    if (!q) return [];
    const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const found = [];
    for (const study of studies) {
      const full = norm(study.title);
      const short = norm((study.title || '').split(':')[0]);
      let at = full ? q.indexOf(full) : -1;
      if (at < 0 && short.length >= 4) {
        const match = new RegExp(`(^|[^a-z0-9])${escape(short)}($|[^a-z0-9])`).exec(q);
        if (match) at = match.index;
      }
      if (at >= 0) found.push({study, at});
    }
    return found.sort((a, b) => a.at - b.at).map(item => item.study);
  }
  return {namedStudies, parseNumber, compareParsed, sortRows, columnSortKind, chartLayout, panelScale, MIN_PANEL_WIDTH,
    panelUnit, chartTitle, takeawayFor, chartIntent, previewTables, barLayout, barScale, BARS,
    rowText, roundTripOk, buildTables, mergeComplete, chartPlan, panelSeries,
    studies, verificationItems, citationMap, headerStatus, EMPTY_CELL};
});

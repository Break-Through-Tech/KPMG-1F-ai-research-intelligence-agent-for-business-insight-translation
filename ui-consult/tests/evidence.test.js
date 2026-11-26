/* Deterministic, model-free tests for evidence.js (EVIDENCE-VISUALIZATION-SPEC.md §10).
   Fixtures are recorded live responses (2026-11-17) plus complete tables from the read-only
   experimental endpoint. Browser: open /tests/evidence.test.html. Node: node tests/evidence.test.js */
(function (root) {
  'use strict';
  const isNode = typeof module === 'object' && module.exports;
  const M = isNode ? require('../evidence.js') : root.EvidenceModel;

  async function load(name) {
    if (isNode) return JSON.parse(require('fs').readFileSync(require('path').join(__dirname, 'fixtures', `${name}.json`), 'utf8'));
    return (await fetch(`/tests/fixtures/${name}.json`)).json();
  }
  const clone = value => JSON.parse(JSON.stringify(value));

  async function run() {
    const results = [];
    const test = (name, fn) => {
      try { fn(); results.push({name, ok: true}); } catch (error) { results.push({name, ok: false, error: String(error && error.message || error)}); }
    };
    const atest = async (name, fn) => {
      try { await fn(); results.push({name, ok: true}); } catch (error) { results.push({name, ok: false, error: String(error && error.message || error)}); }
    };
    const assert = (cond, message) => { if (!cond) throw new Error(message || 'assertion failed'); };
    const eq = (a, b, message) => assert(JSON.stringify(a) === JSON.stringify(b), `${message || 'not equal'}: ${JSON.stringify(a)} !== ${JSON.stringify(b)}`);

    const cu = await load('recorded-cu-dpo');
    const cross = await load('recorded-fin-rate-crossstudy');
    const result = cu.envelope.result;
    const indexSha = result.provenance.index.indexed_records_sha256;
    const tables = M.buildTables(result);

    test('grouping: 6 recorded table rows form 2 tables in source row order', () => {
      eq(tables.map(t => t.table_id), ['S3.T2', 'S4.T4.fig1']);
      eq(tables[0].rows.map(r => r.table_row), [4, 10, 14, 16]);
      eq(tables[1].rows.map(r => r.table_row), [6, 10]);
    });

    test('cell to source mapping: every cell keeps its recorded text and source_id', () => {
      for (const table of tables) for (const row of table.rows) {
        const passage = result.evidence[row.evidenceIndex];
        eq(row.cells.map(c => [c.text, c.source_id]), passage.table_cells.map(c => [c.text, c.source_id]), row.chunk_id);
      }
    });

    test('round trip: recorded rows rebuild their citation-check text exactly', () => {
      for (const p of result.evidence.filter(p => p.representation === 'linearized_table')) assert(M.roundTripOk(p), p.chunk_id);
      assert(tables.every(t => t.fidelity === 'round_trip_ok'));
    });

    test('round trip: a mutated cell is detected and blocks charting', () => {
      const mutated = clone(result);
      const row = mutated.evidence.find(p => p.table_id === 'S3.T2');
      row.table_cells[2].text = '0.86';
      const [table] = M.buildTables(mutated);
      eq(table.fidelity, 'round_trip_mismatch');
      const merged = M.mergeComplete(table, cu.full_tables['2602.00931v2#S3.T2'], indexSha);
      assert(!merged.ok, 'merge must refuse a row that differs from the index');
      assert(!M.chartPlan(table).eligible);
    });

    test('C2: retrieved-only S3.T2 (4 of 16 rows, no baselines) produces no chart', () => {
      const plan = M.chartPlan(tables[0]);
      assert(!plan.eligible);
      assert(/retrieved 4 rows/.test(plan.reason), plan.reason);
    });

    test('complete table: merge succeeds only with matching index and keeps cited markers', () => {
      const merged = M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], indexSha);
      assert(merged.ok, merged.reason);
      eq(merged.table.rows.length, 16);
      eq(merged.table.rows.filter(r => r.retrieved).map(r => r.table_row), [4, 10, 14, 16]);
      const wrong = M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], '0'.repeat(64));
      assert(!wrong.ok && /index/.test(wrong.reason));
      const otherSource = clone(cu.full_tables['2602.00931v2#S3.T2']); otherSource.source_sha256 = 'x';
      assert(!M.mergeComplete(tables[0], otherSource, indexSha).ok);
    });

    test('complete S3.T2 charts as a Baseline / + CU- DPO pairing with three panels', () => {
      const {table} = M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], indexSha);
      const plan = M.chartPlan(table);
      assert(plan.eligible, plan.reason);
      eq(plan.form, 'paired_dot');
      eq(plan.category.values, ['Baseline', '+ CU- DPO']);
      eq(plan.panels.map(p => p.header), ['Acc.', 'Top-3', 'Spear. \\rho']);
      const series = M.panelSeries(table, plan, plan.panels[0]);
      eq(series.length, 8);
      eq([series[0].label, series[0].a.text, series[0].b.text], ['DeepSeek-Math (7B)', '0.46', '0.78']);
    });

    test('C4: S4.T4.fig1 Δ column ("–" on baselines) is excluded; DM, HM2, PN chart', () => {
      const {table} = M.mergeComplete(tables[1], cu.full_tables['2602.00931v2#S4.T4.fig1'], indexSha);
      const plan = M.chartPlan(table);
      assert(plan.eligible, plan.reason);
      eq(plan.panels.map(p => p.header), ['DM', 'HM2', 'PN']);
      eq(plan.excluded.map(e => e.header), ['\\Delta']);
    });

    test('Fin-RATE S1.T1 (checkmarks, text) is never charted', () => {
      const [table] = M.buildTables(cross.envelope.result);
      const sha = cross.envelope.result.provenance.index.indexed_records_sha256;
      const merged = M.mergeComplete(table, cross.full_tables['2602.07294v4#S1.T1'], sha);
      assert(merged.ok, merged.reason);
      const plan = M.chartPlan(merged.table);
      assert(!plan.eligible, 'checkmark table must not chart');
    });

    test('C1: rows from two papers never share one table or chart', () => {
      const papers = M.studies(cross.envelope.result);
      assert(papers.length >= 2, 'cross-study fixture has two papers');
      const crossTables = M.buildTables(cross.envelope.result);
      for (const t of crossTables) assert(new Set(t.rows.map(r => r.chunk_id.split('_')[0])).size === 1);
    });

    test('strict parse rejects compound and non-numeric cells', () => {
      for (const text of ['27.8 \\pm 9.6', '56.0 \\uparrow 4.0', '26.97 (-10.45)', '29.5 / 50.0 / 20.5', '–', '', '-', '4x', '\\bm{\\checkmark}', '1e5', '35–46%']) {
        eq(M.parseNumber(text), null, text);
      }
      // parseNumber also returns `safe` and `exact` (audit L1); these checks cover the original fields.
      const core = ({value, decimals, percent, signed}) => ({value, decimals, percent, signed});
      eq(core(M.parseNumber('0.70')), {value: 0.7, decimals: 2, percent: false, signed: false});
      eq(M.parseNumber('+5.6').value, 5.6);
      eq(M.parseNumber('−3.2').value, -3.2);
      eq(core(M.parseNumber('78.0%')), {value: 78, decimals: 1, percent: true, signed: false});
      eq(M.parseNumber('5,586').value, 5586);
    });

    test('mixed percent and plain values in one column are not charted', () => {
      const {table} = M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], indexSha);
      const t = clone(table);
      t.rows[0].cells[2] = {...t.rows[0].cells[2], text: '46%', parsed: M.parseNumber('46%')};
      const plan = M.chartPlan(t);
      assert(!plan.panels.some(p => p.header === 'Acc.'));
      assert(plan.excluded.some(e => e.header === 'Acc.' && /percent/.test(e.reason)));
    });

    test('header status never claims verification for pending headers', () => {
      for (const t of tables) {
        assert(!t.headerStatus.verified);
        assert(/Not checked by a person/.test(t.headerStatus.label));
        assert(!/\bverified\b/i.test(t.headerStatus.label));
      }
    });

    test('prose numbers are never tabulated (abstract with 35–46% → 68–78% stays a quote)', () => {
      const proseOnly = clone(result); proseOnly.evidence = proseOnly.evidence.filter(p => p.representation !== 'linearized_table');
      eq(M.buildTables(proseOnly).length, 0);
    });

    test('citations: rows cited by no claim carry no citation numbers', () => {
      for (const t of tables) for (const r of t.rows) eq(r.citedBy, [], r.chunk_id);
    });

    test('verification list ties every item to a recorded field', () => {
      const items = M.verificationItems(cu.envelope, tables);
      assert(items.length >= 4);
      assert(items.every(item => item.text && item.origin));
      assert(items.some(item => /quote membership/.test(item.text)));
      assert(items.some(item => /S3\.T2/.test(item.text)));
    });

    /* ---------- Regression tests for the evidence audit (2026-11-17) ---------- */
    const fullS32 = cu.full_tables['2602.00931v2#S3.T2'];
    const merged32 = () => M.mergeComplete(tables[0], fullS32, indexSha).table;
    // Synthetic complete table with `columns` numeric columns: no paper data, only geometry.
    const synthetic = (columns, rows = 4) => {
      const headers = [{column: 0, text: 'Model'}, ...Array.from({length: columns}, (_, i) => ({column: i + 1, text: `Metric ${i + 1}`}))];
      const body = Array.from({length: rows}, (_, r) => ({
        chunk_id: `9999.00001v1_table_${'0'.repeat(16)}_${r + 1}`, table_row: r + 1, row_label: `Model ${r + 1}`, row_group: null,
        evidenceIndex: null, retrieved: false, citedBy: [],
        cells: [{column: 0, text: `Model ${r + 1}`, source_id: `S.r${r}c0`},
          ...Array.from({length: columns}, (_, c) => { const text = `${(r * 7 + c * 3) % 11}.${r}${c}`; return {column: c + 1, text, source_id: `S.r${r}c${c + 1}`, parsed: M.parseNumber(text)}; })],
      }));
      body.forEach(row => { row.cells[0].parsed = null; });
      return {key: 'synthetic', arxiv_id: '9999.00001v1', table_id: 'T1', caption: 'Synthetic', headers, notes: [], rows: body,
        retrievedCount: 0, completeness: 'complete_from_index', fidelity: 'round_trip_ok', headerStatus: {verified: false, label: ''}};
    };

    test('H1 reproduction: the old panel formula reverses the axis for 4–6 panels at 640px', () => {
      for (const n of [4, 5, 6]) {
        const width = 640, labelW = Math.min(240, Math.round(width * 0.24)), gap = 32, pad = 52;
        const oldSpan = (width - labelW - gap * (n - 1)) / n - pad * 2;
        assert(oldSpan < 0, `old span for ${n} panels was ${oldSpan}`);
      }
    });

    test('H1: chartLayout keeps a positive span and x(min) < x(max) for 1–6 panels at every width', () => {
      for (let n = 1; n <= 6; n += 1) for (const available of [0, 320, 480, 640, 760, 900, 1024, 1280, 1440]) {
        const layout = M.chartLayout(n, available);
        assert(layout.span >= 80, `${n} panels at ${available}: span ${layout.span}`);
        assert(layout.panelW >= M.MIN_PANEL_WIDTH - 1e-9, `${n} panels at ${available}: panel ${layout.panelW}`);
        for (let p = 0; p < n; p += 1) {
          const sx = M.panelScale(layout, p, [0.1, 0.5, 0.9]);
          assert(sx(0.1) < sx(0.5) && sx(0.5) < sx(0.9), `${n}/${available}/panel ${p}: order`);
          assert(sx(0.1) >= layout.panelX(p) && sx(0.9) <= layout.panelX(p) + layout.panelW, 'inside its panel');
          if (p) assert(layout.panelX(p) >= layout.panelX(p - 1) + layout.panelW, 'panels do not overlap');
        }
        if (layout.width > Math.max(640, available || 880)) assert(layout.scrolls === (available > 0), 'too-wide charts scroll');
      }
    });

    test('H1 rendered: 4-, 5- and 6-panel SVGs at 1280 and 1440 (and 640) never reverse a scale', () => {
      if (!root.ChartSvg || typeof document === 'undefined') throw new Error('needs the browser test page');
      const host = document.createElement('div');
      host.style.cssText = 'position:absolute;left:-10000px;top:0;';
      document.body.append(host);
      try {
        for (const n of [4, 5, 6]) {
          const table = synthetic(n);
          const plan = M.chartPlan(table);
          assert(plan.eligible && plan.panels.length === n, `plan for ${n}: ${plan.reason}`);
          for (const available of [1280 - 2 * 240, 1280, 1440, 640]) {
            const {root: svgRoot, layout} = root.ChartSvg.build({document, table, plan, available, title: 'Synthetic', onOpen() {}});
            host.replaceChildren(svgRoot);
            for (let p = 0; p < n; p += 1) {
              const ends = Object.fromEntries([...svgRoot.querySelectorAll(`.axis-end[data-panel="${p}"]`)].map(t => [t.getAttribute('data-end'), Number(t.getAttribute('x'))]));
              assert(ends.min < ends.max, `${n} panels, width ${available}, panel ${p}: min ${ends.min} max ${ends.max}`);
            }
            for (const group of svgRoot.querySelectorAll('.point')) {
              const [column, chunk] = group.getAttribute('data-point').split('|');
              const row = table.rows.find(r => r.chunk_id === chunk);
              const cell = row.cells[Number(column)];
              eq(group.querySelector('text').textContent, cell.text, 'point label is the exact cell text');
              const p = plan.panels.findIndex(panel => panel.column === Number(column));
              const cx = Number(group.querySelector('circle').getAttribute('cx'));
              assert(cx >= layout.panelX(p) + layout.pad - 1e-6 && cx <= layout.panelX(p) + layout.pad + layout.span + 1e-6, 'dot inside its panel');
            }
            // Ordering on screen follows the values: sort cells by value, x must not decrease.
            for (const panel of plan.panels) {
              const dots = table.rows.map(row => [row.cells[panel.column].parsed.value,
                Number(svgRoot.querySelector(`[data-point="${panel.column}|${row.chunk_id}"] circle`).getAttribute('cx'))]).sort((a, b) => a[0] - b[0]);
              for (let i = 1; i < dots.length; i += 1) assert(dots[i][1] >= dots[i - 1][1], `panel ${panel.column} ordering`);
            }
          }
        }
      } finally { host.remove(); }
    });

    test('M1: each point of a paired chart opens its own row and exact source cell', () => {
      if (!root.ChartSvg || typeof document === 'undefined') throw new Error('needs the browser test page');
      const table = merged32();
      const plan = M.chartPlan(table);
      const opened = [];
      const {root: svgRoot} = root.ChartSvg.build({document, table, plan, available: 1100, title: 'S3.T2', onOpen: (row, cell) => opened.push([row.chunk_id, cell.source_id, cell.text])});
      const series = M.panelSeries(table, plan, plan.panels[0]);
      const first = series[0];
      const dotA = svgRoot.querySelector(`[data-point="${plan.panels[0].column}|${first.rowA.chunk_id}"]`);
      const dotB = svgRoot.querySelector(`[data-point="${plan.panels[0].column}|${first.rowB.chunk_id}"]`);
      assert(dotA && dotB && dotA !== dotB, 'two separate controls');
      dotA.dispatchEvent(new MouseEvent('click'));
      dotB.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));
      eq(opened, [[first.rowA.chunk_id, first.a.source_id, '0.46'], [first.rowB.chunk_id, first.b.source_id, '0.78']]);
      assert(first.a.source_id !== first.b.source_id, 'the two cells have different source IDs');
      eq(svgRoot.querySelectorAll('.point').length, series.length * 2 * plan.panels.length, 'one control per dot');
    });

    test('H2: a complete table missing its final row is refused (fail closed)', () => {
      const prefix = clone(fullS32);
      prefix.rows = prefix.rows.slice(0, -1); prefix.row_count = prefix.rows.length;
      const out = M.mergeComplete(tables[0], prefix, indexSha);
      // Row 16 is retrieved, so drop a non-retrieved final row from S4.T4.fig1 too (rows 6 and 10 retrieved).
      assert(!out.ok, 'prefix of S3.T2 must not merge');
      const fig = clone(cu.full_tables['2602.00931v2#S4.T4.fig1']);
      fig.rows = fig.rows.slice(0, -1); fig.row_count = fig.rows.length;
      const figOut = M.mergeComplete(tables[1], fig, indexSha);
      assert(!figOut.ok && /extractor emitted 14 rows but the index returned 13/.test(figOut.reason), figOut.reason);
      for (const strip of ['extractor_rows_emitted', 'completeness_check']) {
        const bare = clone(cu.full_tables['2602.00931v2#S4.T4.fig1']); delete bare[strip];
        const r = M.mergeComplete(tables[1], bare, indexSha);
        assert(!r.ok && /could not show that this table is complete/.test(r.reason), `${strip}: ${r.reason}`);
        assert(!M.chartPlan(tables[1]).eligible, 'no chart without completeness');
      }
      assert(M.mergeComplete(tables[1], cu.full_tables['2602.00931v2#S4.T4.fig1'], indexSha).ok, 'the real complete table still merges');
    });

    test('M3: row grouping, notes, header status and merged-cell provenance must agree', () => {
      const retrievedRow = tables[0].rows[0].table_row; // 4
      const mutate = fn => { const f = clone(fullS32); fn(f, f.rows[retrievedRow - 1]); return M.mergeComplete(tables[0], f, indexSha); };
      const cases = [
        [(f, r) => { r.row_group = 'Ablations'; }, /grouping differs/],
        [(f, r) => { r.cells[0].merged_from_previous_row = true; delete r.cells[0].merged_from_previous_row; r.cells[1].merged_from_previous_row = true; }, /differs between/],
        [(f, r) => { delete r.cells[0].merged_from_previous_row; }, /differs between/],
        [f => { f.source_notes = [{anchor: 'x', text: 'footnote'}]; }, /source notes differ/],
        [f => { f.header_review = 'verified'; }, /header review differs/],
        [f => { f.rows[0].cells.push({column: 99, text: '1', row: 1}); }, /one cell per column/],
        [f => { f.rows[0].cells[1].merged_from_previous_row = 'yes'; }, /merge provenance/],
        [f => { f.rows[0].cells[1].note = 'x'; }, /unknown fields/],
        [f => { f.rows[0].cells[1].row = 5; }, /another row/],
        [f => { f.rows[0].row_group = 7; }, /row group is not text/],
      ];
      for (const [fn, pattern] of cases) {
        const out = mutate(fn);
        assert(!out.ok && pattern.test(out.reason), `${pattern}: ${out.reason}`);
      }
      // A grouped indexed row turns grouping on for the whole table, so the chart stays off.
      const grouped = clone(fullS32); grouped.rows[0].row_group = 'Group A';
      const g = M.mergeComplete(tables[0], grouped, indexSha);
      assert(g.ok, g.reason);
      assert(!M.chartPlan(g.table).eligible && /sub-headings/.test(M.chartPlan(g.table).reason));
      // A value merged across rows is never plotted as two independent points.
      const t = synthetic(2); t.rows[1].cells[1].merged_from_previous_row = true;
      const plan = M.chartPlan(t);
      eq(plan.panels.map(p => p.column), [2]);
      assert(plan.excluded.some(e => e.column === 1 && /merged across rows/.test(e.reason)));
    });

    test('L1: unsafe precision never charts; sorting is exact and mixed columns sort by text', () => {
      const a = M.parseNumber('9007199254740992'), b = M.parseNumber('9007199254740993');
      eq(a.value === b.value, true, 'the doubles collide (reproduction)');
      eq([a.safe, b.safe], [false, false]);
      eq(M.compareParsed(a, b), -1); eq(M.compareParsed(b, a), 1); eq(M.compareParsed(a, M.parseNumber('9,007,199,254,740,992')), 0);
      eq(M.compareParsed(M.parseNumber('-0.5'), M.parseNumber('-0.25')), -1);
      eq(M.compareParsed(M.parseNumber('0.70'), M.parseNumber('0.7')), 0);
      eq(M.parseNumber('123456789012345').safe, true);
      const t = synthetic(2);
      ['9007199254740993', '9007199254740992', '1', '2'].forEach((text, i) => { t.rows[i].cells[1] = {...t.rows[i].cells[1], text, parsed: M.parseNumber(text)}; });
      eq(M.sortRows(t.rows, 1, 1).map(r => r.cells[1].text), ['1', '2', '9007199254740992', '9007199254740993']);
      eq(M.sortRows(t.rows, 1, -1).map(r => r.cells[1].text), ['9007199254740993', '9007199254740992', '2', '1']);
      const plan = M.chartPlan(t);
      assert(plan.excluded.some(e => e.column === 1 && /too many digits/.test(e.reason)), JSON.stringify(plan.excluded));
      const mixed = synthetic(1);
      ['10%', '9', '', '70%'].forEach((text, i) => { mixed.rows[i].cells[1] = {...mixed.rows[i].cells[1], text, parsed: M.parseNumber(text)}; });
      eq(M.columnSortKind(mixed.rows, 1), 'text');
      eq(M.sortRows(mixed.rows, 1, 1).map(r => r.cells[1].text), ['9', '10%', '70%', '']);
      eq(M.sortRows(mixed.rows, 1, -1).map(r => r.cells[1].text), ['70%', '10%', '9', '']);
      eq(M.sortRows(mixed.rows, null, 0).map(r => r.table_row), [1, 2, 3, 4], 'third click restores source order');
    });

    const G = isNode ? require('../async-guards.js') : root.AsyncGuards;
    const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return {promise, resolve}; };

    await atest('M2: a stale saved-brief response cannot override newer navigation', async () => {
      const nav = G.createNavGuard();
      const shown = [];
      const open = async (name, response) => { const token = nav.begin(); const demo = await response; if (nav.isCurrent(token)) shown.push(name); };
      const a = deferred(), b = deferred();
      const first = open('A', a.promise);
      nav.bump(); // the person switches to Research while A is loading
      const second = open('B', b.promise);
      b.resolve('B'); await second;
      a.resolve('A'); await first;
      eq(shown, ['B'], 'only the newest navigation is applied');
      const c = deferred(); const third = open('C', c.promise); c.resolve('C'); await third;
      eq(shown, ['B', 'C']);
    });

    await atest('L3: failed table loads are not cached; successes expire; in-flight requests are shared', async () => {
      let clock = 0, calls = 0;
      const cache = G.createResultCache({ttlMs: 1000, now: () => clock});
      const replies = [{ok: false, reason: '503'}, {ok: true, full: 1}, {ok: true, full: 2}];
      const loader = async () => replies[calls++];
      eq(await cache.get('k', loader), {ok: false, reason: '503'});
      eq(await cache.get('k', loader), {ok: true, full: 1}, 'a temporary failure is retried');
      eq(await cache.get('k', loader), {ok: true, full: 1}, 'success is reused');
      eq(calls, 2);
      clock = 1001;
      eq(await cache.get('k', loader), {ok: true, full: 2}, 'success expires');
      const gate = deferred(); let shared = 0;
      const slow = () => { shared += 1; return gate.promise; };
      const p1 = cache.get('x', slow), p2 = cache.get('x', slow);
      gate.resolve({ok: true}); await Promise.all([p1, p2]);
      eq(shared, 1, 'one request for concurrent callers');
      let thrown = 0;
      await cache.get('y', async () => { thrown += 1; throw new Error('net'); }).catch(() => {});
      eq(await cache.get('y', async () => ({ok: true, again: true})), {ok: true, again: true}, 'a thrown failure is not cached');
    });

    test('M4: a write whose response is lost is "unknown", and the reloaded state decides', () => {
      const timeout = Object.assign(new Error('t'), {name: 'TimeoutError'});
      eq(G.writeFailure(timeout, {write: true}), {kind: 'unknown', timeout: true});
      eq(G.writeFailure(new TypeError('Failed to fetch'), {write: true}), {kind: 'unknown', timeout: false});
      eq(G.writeFailure(timeout, {write: false}).kind, 'not_applied');
      eq(G.writeFailure(Object.assign(new Error('x'), {status: 409}), {write: true}), {kind: 'rejected', status: 409});
      const before = [{reviewer: 'QA reviewer', decision: 'revise', notes: 'fix'}];
      const sent = {reviewer: ' QA reviewer ', decision: 'revise', notes: 'fix '};
      eq(G.reviewRecorded(before, before, sent), false, 'an older identical review is not this one');
      eq(G.reviewRecorded(before, [...before, {reviewer: 'QA reviewer', decision: 'revise', notes: 'fix'}], sent), true);
      eq(G.reviewRecorded(before, [...before, {reviewer: 'QA reviewer', decision: 'approve', notes: 'fix'}], sent), false);
      eq(G.briefChanged({title: 'New', archived: false}, {expected_version: 'v', title: 'New '}), true);
      eq(G.briefChanged({title: 'Old', archived: false}, {expected_version: 'v', title: 'New'}), false);
      eq(G.briefChanged({title: 'Old', archived: true}, {expected_version: 'v', archived: true}), true);
    });

    /* ---------- Regression tests for verification regressions (2026-11-17) ---------- */
    test('B1: a proxy 504 or other 5xx after forwarding a write is "unknown", never a rejection', () => {
      const status = (code, writeOutcome) => Object.assign(new Error('x'), {status: code, ...(writeOutcome ? {writeOutcome} : {})});
      eq(G.writeFailure(status(504, 'unknown'), {write: true}).kind, 'unknown', 'proxy timeout after forwarding');
      eq(G.writeFailure(status(504), {write: true}).kind, 'unknown', 'a 504 without detail is not proof of rejection');
      eq(G.writeFailure(status(502, 'unknown'), {write: true}).kind, 'unknown');
      eq(G.writeFailure(status(500), {write: true}).kind, 'unknown');
      eq(G.writeFailure(status(408), {write: true}).kind, 'unknown');
      eq(G.writeFailure(status(503, 'unknown'), {write: true}).kind, 'unknown', 'connection dropped after sending');
      eq(G.writeFailure(status(503, 'not_sent'), {write: true}).kind, 'not_applied', 'the backend connection never opened');
      for (const code of [400, 404, 405, 409, 413, 415, 422]) eq(G.writeFailure(status(code), {write: true}).kind, 'rejected', String(code));
      eq(G.writeFailure(status(504), {write: false}).kind, 'rejected', 'a failed read just shows its message');
    });

    await atest('B1: a late commit is not reported as "not saved"; it is confirmed once it lands', async () => {
      // A fake store whose write commits only after the first reconciliation read.
      const store = {reviews: [{reviewer: 'QA', decision: 'revise', notes: 'old'}]};
      const before = store.reviews.slice();
      const sent = {reviewer: 'QA', decision: 'approve', notes: null};
      const commitLater = new Promise(resolve => setTimeout(() => { store.reviews.push({...sent}); resolve(); }, 20));
      const read = () => ({library: {reviews: store.reviews.slice()}});
      // The page maps "no match" to null (unknown), never to false ("not saved").
      const verdict = latest => (G.reviewRecorded(before, latest.library.reviews, sent) ? true : null);
      eq(verdict(read()), null, 'immediately after the timeout the review is not visible: still unknown');
      await commitLater;
      eq(verdict(read()), true, '"Check again" after the late commit confirms it');
    });

    test('B1: an unrelated newer version does not confirm a version import', () => {
      const imported = {request: {query: 'Q'}, summary: {claims: [{text: 'A', chunk_ids: ['x']}]}};
      const latest = (versionId, current, result) => ({result, library: {version: {id: versionId}, brief: {current_version: current}}});
      eq(G.importRecorded(latest('v1', 'v1', imported), 'v1', imported), false, 'no new version yet');
      eq(G.importRecorded(latest('v2', 'v2', {request: {query: 'someone else'}}), 'v1', imported), false, 'concurrent unrelated version');
      eq(G.importRecorded(latest('v2', 'v3', imported), 'v1', imported), false, 'not the current version');
      eq(G.importRecorded(latest('v2', 'v2', {summary: {claims: [{chunk_ids: ['x'], text: 'A'}]}, request: {query: 'Q'}}), 'v1', imported), true,
        'the new current version holds exactly the imported result (key order ignored)');
      eq(G.importRecorded(latest('v2', 'v2', imported), 'v1', null), false, 'nothing imported, nothing to confirm');
    });

    test('B3: a resize from 810px to 809px updates the scroll state without losing order or focus', () => {
      if (!root.ChartSvg || typeof document === 'undefined') throw new Error('needs the browser test page');
      const fits = M.chartLayout(3, 810), tight = M.chartLayout(3, 809);
      eq([fits.width, tight.width], [810, 810], 'same SVG width on both sides of the threshold (reproduction)');
      eq([fits.scrolls, tight.scrolls], [false, true]);
      const table = merged32();
      const plan = M.chartPlan(table);
      const host = document.createElement('div');
      host.style.cssText = 'position:absolute;left:-10000px;top:0;';
      const frame = document.createElement('div');
      host.append(frame); document.body.append(host);
      try {
        const chart = root.ChartSvg.mount({document, frame, table, plan, title: 'S3.T2', onOpen() {}});
        const first = chart.update(810);
        assert(first.rebuilt && !frame.classList.contains('scrolls') && !frame.hasAttribute('tabindex') && !frame.hasAttribute('role'), 'fits at 810');
        const svgNode = frame.querySelector('svg');
        const point = frame.querySelector('.point');
        point.focus();
        assert(document.activeElement === point, 'point focused');
        const second = chart.update(809);
        assert(!second.rebuilt && frame.querySelector('svg') === svgNode, 'same SVG kept');
        assert(frame.classList.contains('scrolls'), 'scroll class added at 809');
        eq([frame.getAttribute('tabindex'), frame.getAttribute('role'), frame.getAttribute('aria-label')], ['0', 'region', 'S3.T2 chart, scrolls sideways']);
        assert(document.activeElement === point, 'keyboard focus kept');
        for (let p = 0; p < plan.panels.length; p += 1) {
          const ends = Object.fromEntries([...frame.querySelectorAll(`.axis-end[data-panel="${p}"]`)].map(t => [t.getAttribute('data-end'), Number(t.getAttribute('x'))]));
          assert(ends.min < ends.max, `panel ${p} still ascending`);
        }
        chart.update(810);
        assert(!frame.classList.contains('scrolls') && !frame.hasAttribute('tabindex'), 'back to fitting at 810');
        const wider = chart.update(1200);
        assert(wider.rebuilt && document.activeElement && document.activeElement.getAttribute('data-point') === point.getAttribute('data-point'),
          'a real rebuild restores focus to the same cell');
      } finally { host.remove(); }
    });

    /* ---------- Chart-first design (2026-11-17) ---------- */
    const fullFig = cu.full_tables['2602.00931v2#S4.T4.fig1'];
    const mergedFig = () => M.mergeComplete(tables[1], fullFig, indexSha).table;
    const previewPayload = () => ({index_sha256: fullFig.index_sha256, model_calls: 0,
      evidence: clone(result.evidence.filter(p => p.table_id === 'S4.T4.fig1')),
      tables: [{key: '2602.00931v2#S4.T4.fig1', status: 'complete', table: clone(fullFig)}]});

    test('CF1: chart intent is explicit (chart, graph, plot, visualize), same rule as the backend', () => {
      for (const q of ['Show a grouped bar chart using Table 4', 'Plot accuracy by model', 'Can you visualize Table 2?', 'show a graph'])
        assert(M.chartIntent(q), q);
      for (const q of ['How much did CU-DPO improve accuracy?', 'Explain the method', 'Which table reports DeepMath?', ''])
        assert(!M.chartIntent(q), q);
    });

    test('CF2: bars only where the table states a percentage unit with a meaningful zero', () => {
      const fig = M.chartPlan(mergedFig());
      eq(fig.panels.map(p => [p.header, p.unit.zero, p.unit.label, p.unit.basis]),
        [['DM', true, 'Pass@1, %', 'caption'], ['HM2', true, 'Pass@1, %', 'caption'], ['PN', true, 'Pass@1, %', 'caption']]);
      const t2 = M.chartPlan(merged32());
      assert(t2.panels.every(p => !p.unit.zero && /No unit/.test(p.unit.reason)), 'Table 2 accuracies (0.46 …) have no stated unit: no bars');
      const t = synthetic(2);
      ['10%', '20%', '30%', '40%'].forEach((text, i) => { t.rows[i].cells[1] = {...t.rows[i].cells[1], text, parsed: M.parseNumber(text)}; });
      eq(M.chartPlan(t).panels.map(p => [p.column, p.unit.zero, p.unit.basis]), [[1, true, 'cells'], [2, false, null]]);
      const twoUnits = synthetic(1); twoUnits.caption = 'Table 9: Rates (%) and shares (%).';
      assert(!M.chartPlan(twoUnits).panels[0].unit.zero, 'two caption units: not certain');
      const outOfRange = synthetic(1); outOfRange.caption = 'Table 9: Scores (%).';
      outOfRange.rows[0].cells[1] = {...outOfRange.rows[0].cells[1], text: '140.5', parsed: M.parseNumber('140.5')};
      assert(!M.chartPlan(outOfRange).panels[0].unit.zero && /outside 0–100/.test(M.chartPlan(outOfRange).panels[0].unit.reason));
    });

    test('CF3 rendered: grouped bars share one zero, are proportional, label exact values and open their own cells', () => {
      if (!root.ChartSvg || typeof document === 'undefined') throw new Error('needs the browser test page');
      const table = mergedFig();
      const plan = M.chartPlan(table);
      const panel = plan.panels[0];
      const host = document.createElement('div');
      host.style.cssText = 'position:absolute;left:-10000px;top:0;';
      document.body.append(host);
      try {
        for (const available of [860, 1100, 560, 400]) {
          const opened = [];
          const {root: svgRoot, layout} = root.ChartSvg.buildBars({document, table, plan, panel, available, title: 'T4', onOpen: (row, cell) => opened.push([row.chunk_id, cell.source_id])});
          host.replaceChildren(svgRoot);
          const bars = [...svgRoot.querySelectorAll('.point.bar')];
          eq(bars.length, 14, 'one bar per row');
          const ratios = bars.map(group => {
            const rect = group.querySelector('rect');
            assert(Number(rect.getAttribute('x')) === layout.x0, 'every bar starts at the shared zero');
            const [column, chunk] = group.getAttribute('data-point').split('|');
            const cell = table.rows.find(r => r.chunk_id === chunk).cells[Number(column)];
            eq(group.querySelector('text').textContent, cell.text, 'label is the exact cell text');
            eq(group.getAttribute('data-source-id'), cell.source_id);
            return Number(rect.getAttribute('width')) / cell.parsed.value;
          });
          assert(Math.max(...ratios) - Math.min(...ratios) < 1e-6, `bar length proportional to value at ${available}`);
          assert(layout.span >= M.BARS.minSpan && (available < M.BARS.minWidth ? layout.scrolls : true), 'narrow frames scroll instead of squeezing');
          bars[0].dispatchEvent(new MouseEvent('click'));
          bars[1].dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));
          eq(opened.map(o => o[1]), [bars[0].getAttribute('data-source-id'), bars[1].getAttribute('data-source-id')]);
          assert(opened[0][0] !== opened[1][0], 'baseline and treatment bars open different rows');
        }
        let refused = false;
        const t2 = merged32(), plan2 = M.chartPlan(t2);
        try { root.ChartSvg.buildBars({document, table: t2, plan: plan2, panel: plan2.panels[0], available: 900, title: 'x', onOpen() {}}); }
        catch { refused = true; }
        assert(refused, 'bars are refused for a column without a confirmed zero');
      } finally { host.remove(); }
    });

    test('CF4: a preview chart passes the same checks as an answer table, and fails closed', () => {
      const ok = M.previewTables(previewPayload());
      eq([ok.tables.length, ok.refused.length], [1, 0]);
      const t = ok.tables[0].table;
      eq([t.completeness, t.rows.length, t.extractorRowsEmitted], ['complete_from_index', 14, 14]);
      assert(t.rows.every(r => r.evidenceIndex === null && r.citedBy.length === 0), 'preview rows are not cited');
      assert(ok.tables[0].plan.eligible);
      const cases = [
        [p => { delete p.tables[0].table.extractor_rows_emitted; }, /complete/],
        [p => { p.tables[0].table.rows.pop(); p.tables[0].table.row_count -= 1; }, /extractor emitted|numbered/],
        [p => { p.evidence[0].table_cells[2].text = '99.9'; }, /did not match/],
        [p => { p.tables[0].status = 'refused'; p.tables[0].table = null; p.tables[0].reason = 'audit'; }, /audit/],
        [p => { p.evidence = []; }, /not returned/],
      ];
      for (const [mutate, pattern] of cases) {
        const payload = previewPayload(); mutate(payload);
        const out = M.previewTables(payload);
        assert(out.tables.length === 0 && pattern.test(out.refused[0]?.reason), `${pattern}: ${JSON.stringify(out.refused)}`);
      }
    });

    test('CF5: the takeaway is the answer\'s own cited finding about the table, or nothing', () => {
      const t = mergedFig();
      eq(M.takeawayFor(t, result), null, 'the recorded answer cites only the abstract, not this table');
      const r = clone(result);
      const row = r.evidence.find(p => p.table_id === 'S4.T4.fig1');
      r.summary.claims = [{kind: 'interpretation', text: 'An inference.', chunk_ids: [row.chunk_id]},
        {kind: 'finding', text: 'Mistral-8x7B reaches 28.9 on DM with CU-DPO.', chunk_ids: [row.chunk_id]}];
      r.summary.status = 'ok';
      const takeaway = M.takeawayFor(t, r);
      eq(takeaway, {text: 'Mistral-8x7B reaches 28.9 on DM with CU-DPO.', citations: [r.evidence.indexOf(row) + 1]});
      r.summary.status = 'insufficient_evidence';
      eq(M.takeawayFor(t, r), null, 'no takeaway for an abstention');
    });

    test('CF6: the chart title uses only the table\'s own words', () => {
      const t = mergedFig();
      const plan = M.chartPlan(t);
      eq(M.chartTitle(t, plan, plan.panels[0]), 'Table 4: DM by base model, Baseline vs + CU- DPO');
      eq(M.chartTitle(t, plan, null), 'Table 4: DM, HM2, PN by base model, Baseline vs + CU- DPO');
    });

    test('CF7: switching metric or width keeps keyboard focus and the scroll state in bar view', () => {
      if (!root.ChartSvg || typeof document === 'undefined') throw new Error('needs the browser test page');
      const table = mergedFig();
      const plan = M.chartPlan(table);
      const host = document.createElement('div');
      host.style.cssText = 'position:absolute;left:-10000px;top:0;';
      const frame = document.createElement('div');
      host.append(frame); document.body.append(host);
      try {
        const chart = root.ChartSvg.mount({document, frame, table, plan, title: 'T4', onOpen() {}, view: {kind: 'bars', panel: plan.panels[1]}});
        chart.update(900);
        const target = frame.querySelectorAll('.point.bar')[3];
        target.focus();
        const key = target.getAttribute('data-point');
        assert(!frame.classList.contains('scrolls'));
        const narrow = chart.update(400);
        assert(narrow.rebuilt && frame.classList.contains('scrolls') && frame.getAttribute('tabindex') === '0', 'narrow: rebuilt and scrollable');
        eq(document.activeElement && document.activeElement.getAttribute('data-point'), key, 'focus follows the same cell');
        eq(chart.kind, 'bars');
        const dots = root.ChartSvg.mount({document, frame, table, plan, title: 'T4', onOpen() {}, view: {kind: 'dots', panel: plan.panels[1]}});
        dots.update(900);
        eq(frame.querySelectorAll('.panel-head').length, 1, 'single-metric dot view has one panel');
      } finally { host.remove(); }
    });

    /* ---------- Business-intelligence views (chart-select.js), real tables from the index ---------- */
    const CS = isNode ? require('../chart-select.js') : root.ChartSelect;
    const corpus = await load('corpus-tables');
    const real = key => {
      const entry = corpus.tables[key];
      const result = {evidence: entry.passages, summary: {status: 'ok', claims: []}};
      const [table] = M.buildTables(result);
      const merged = M.mergeComplete(table, entry.full, corpus.index_sha256);
      if (!merged.ok) throw new Error(`${key}: ${merged.reason}`);
      return merged.table;
    };
    const viewsOf = (key, question = '') => {
      const table = real(key);
      const views = CS.viewsFor(table);
      return {table, views, by: Object.fromEntries(views.map(v => [v.kind, v])), def: CS.chooseDefault(views, question)};
    };
    const eligibleKinds = views => views.filter(v => v.eligible).map(v => v.kind).sort();

    test('TeX labels: readable text with no raw commands or duplicates (ρ\\rhoρ regression)', () => {
      eq(CS.texPlain('Spear. \\rho'), 'Spear. ρ');
      eq(CS.texPlain('\\mathcal{D}_{\\mathrm{2k}}\\cup\\mathcal{D}_{\\mathrm{EH}}'), 'D_2k∪D_EH');
      eq(CS.texPlain('\\scriptstyle\\mathbf{\\frac{N}{d}}'), 'N/d');
      eq(CS.texPlain('Llama-3-8B / \\mathcal{S}_{\\mathrm{harm}}'), 'Llama-3-8B / S_harm');
      eq(CS.texPlain('Token Cost \\downarrow'), 'Token Cost ↓');
      eq(CS.texPlain('0.211 \\pm 0.004'), '0.211 ± 0.004');
      eq(CS.texPlain('plain text'), 'plain text');
    });

    test('± cells: value and half-width exactly as printed; artefacts and plain numbers refused', () => {
      eq(CS.parsePlusMinus('0.211 \\pm 0.004'), {value: 0.211, err: 0.004, percent: false});
      eq(CS.parsePlusMinus('82.4\\pm 1.8'), {value: 82.4, err: 1.8, percent: false});
      eq(CS.parsePlusMinus('0.576 \\pm 0.0060.718'), null, 'extraction artefact');
      eq(CS.parsePlusMinus('0.238'), null);
      eq(CS.parsePlusMinus('-'), null);
    });

    test('uncertainty meaning: quoted only when the caption names the statistic', () => {
      eq(CS.uncertaintyMeaning(real('2502.17874v2#A2.T6')).quote, 'mean \\pm 1.96 standard deviation of three random seeds');
      eq(CS.uncertaintyMeaning(real('2607.00275v1#S4.T1')).quote, 'mean \\pm standard deviation of A(\\theta) over 30 different run seeds');
      eq(CS.uncertaintyMeaning(real('2603.15712v1#A3.T2')), null, '"over 5 independent runs" does not name the statistic');
      eq(CS.uncertaintyMeaning(real('2506.03610v3#S5.T8.st1')), null);
    });

    test('eligibility: ordered top-k columns give a line by default; no trade-off, no pairing', () => {
      const {views, def, by} = viewsOf('2502.17874v2#A1.T5');
      eq(eligibleKinds(views), ['dots', 'heatmap', 'line']);
      eq(def.kind, 'line');
      eq(by.line.ordered.positions, [1, 2, 3, 4, 5, 8, 10], 'x positions come from the headers, with true spacing');
    });

    test('eligibility: mixed ± table refuses error bars and line, and names the offending cell', () => {
      const {views, by} = viewsOf('2502.17874v2#A2.T6');
      eq(eligibleKinds(views), ['heatmap']);
      assert(/mixes value ± range cells/.test(by.errorbars.reason), by.errorbars.reason);
      assert(/mix plain numbers with other formats/.test(by.line.reason), by.line.reason);
    });

    test('eligibility: stated mean ± sd over ordered sample sizes gives line and error bars', () => {
      const {views, def, by} = viewsOf('2607.00275v1#S4.T1');
      eq(eligibleKinds(views), ['errorbars', 'heatmap', 'line']);
      eq(def.kind, 'line');
      eq(by.line.ordered.axis, 'rows');
      assert(by.line.ordered.shared, 'four methods on one quantity share a scale');
      eq(CS.chooseDefault(views, 'How uncertain are these results across seeds?').kind, 'errorbars');
    });

    test('eligibility: unstated ± meaning refuses error bars', () => {
      const {by} = viewsOf('2506.03610v3#S5.T8.st1');
      assert(!by.errorbars.eligible && /do not say whether ± is/.test(by.errorbars.reason), by.errorbars.reason);
      const ablation = viewsOf('2603.15712v1#A3.T2');
      assert(!ablation.by.errorbars.eligible, 'over 5 runs only');
      assert(ablation.by.scatter.eligible, 'Time (h) is a cost measure');
    });

    test('eligibility: accuracy vs token cost is a trade-off, default only when the question asks', () => {
      const {views, def, by} = viewsOf('2609.11414v1#S6.T6');
      assert(by.scatter.eligible);
      eq(by.scatter.x.map(c => c.plain), ['Token Cost ↓']);
      eq(def.kind, 'dots', 'no question: the neutral view');
      const asked = CS.chooseDefault(views, 'Which router gives the best accuracy for its token cost?');
      eq(asked.kind, 'scatter');
      assert(/asks about cost or efficiency/.test(asked.why), asked.why);
    });

    test('refusal: identifier-numbered rows never form a line or a trade-off', () => {
      const {by} = viewsOf('2412.06681v2#S5.T1');
      assert(!by.line.eligible && /identifiers/.test(by.line.reason), by.line.reason);
      assert(!by.scatter.eligible, 'travel time vs capacity per link ID is not a trade-off between alternatives');
    });

    test('eligibility: stated percentages give bars from zero; paired rows give before/after and slope', () => {
      eq(viewsOf('2412.15272v2#S6.T4').def.kind, 'bars');
      const paired = viewsOf('2405.19358v2#S5.T2');
      eq(paired.def.kind, 'paired');
      assert(paired.by.slope.eligible);
      const cost = CS.chooseDefault(paired.views, 'What does it cost?');
      assert(cost.kind === 'paired' && /has no matching view/.test(cost.why), 'intent never picks an ineligible view');
    });

    test('eligibility: retrieved rows only means every view is off, with the completeness reason', () => {
      const views = CS.viewsFor(tables[0]);
      assert(views.every(v => !v.eligible));
      assert(/complete table is loaded/.test(views[0].reason), views[0].reason);
      eq(CS.chooseDefault(views, 'improve').kind, 'table');
    });

    test('intent: deterministic keywords', () => {
      eq(CS.intentOf('By how much did CU-DPO improve accuracy?').name, 'improvement');
      eq(CS.intentOf('Which model is best?').name, 'ranking');
      eq(CS.intentOf('How does accuracy change as k increases?').name, 'trend');
      eq(CS.intentOf('Compare results across benchmarks').name, 'multi');
      eq(CS.intentOf('What is the latency overhead?').name, 'tradeoff');
      eq(CS.intentOf(''), null);
    });

    test('KPI tiles: cited rows only, values verbatim, paired as printed before → after', () => {
      const merged = clone(M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], indexSha).table);
      const restore = t => { t.rows.forEach(r => r.cells.forEach(c => { c.parsed = M.parseNumber(c.text); })); return t; };
      const table = restore(merged);
      eq(CS.kpiTiles(table).tiles.length, table.rows.some(r => r.citedBy.length) ? CS.kpiTiles(table).tiles.length : 0);
      table.rows.forEach(r => { r.citedBy = r.cells[0].text === 'DeepSeek-Math (7B)' ? [2] : []; });
      const {tiles} = CS.kpiTiles(table);
      eq(tiles.length, 1);
      eq([tiles[0].label, tiles[0].header, tiles[0].from.cell.text, tiles[0].to.cell.text, tiles[0].conditions], ['DeepSeek-Math (7B)', 'Acc.', '0.46', '0.78', ['Baseline', '+ CU- DPO']]);
      eq(tiles[0].from.cell.source_id, table.rows.find(r => r.chunk_id === tiles[0].from.row.chunk_id).cells[2].source_id);
    });

    test('count check: "seven base models" vs Table 2 (8 models) flags a review item; Table 4 (7) does not', () => {
      const t2 = M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], indexSha).table;
      const t4 = M.mergeComplete(tables[1], cu.full_tables['2602.00931v2#S4.T4.fig1'], indexSha).table;
      const issue = CS.countCheck(result, t2);
      assert(issue && issue.stated === 7 && issue.distinct === 8, JSON.stringify(issue));
      assert(/seven base models/.test(issue.text) && /\[1\]/.test(issue.text), issue.text);
      eq(CS.countCheck(result, t4), null);
      eq(CS.countCheck(result, tables[0]), null, 'never on a partial table');
      eq(result.summary.claims[0].text.includes('seven base models'), true, 'the recorded answer is not rewritten');
    });

    test('plain framing: chart titles are questions built only from table labels, never results', () => {
      const t2 = M.mergeComplete(tables[0], cu.full_tables['2602.00931v2#S3.T2'], indexSha).table;
      eq(CS.businessQuestion('paired', t2, {metric: 'Acc.', from: 'Baseline', to: '+ CU- DPO'}),
        'How did Acc. change from “Baseline” to “+ CU- DPO” for each base model?');
      const q = CS.businessQuestion('scatter', real('2609.11414v1#S6.T6'), {x: 'Token Cost \\downarrow', y: 'Evaluation Acc. \\uparrow'});
      eq(q, 'How does Evaluation Acc. ↑ compare with Token Cost ↓?');
      for (const kind of ['paired', 'slope', 'bars', 'dots', 'line', 'scatter', 'errorbars', 'heatmap']) {
        const text = CS.businessQuestion(kind, t2, {metric: 'Acc.', from: 'a', to: 'b', x: 'x', y: 'y', axis: 'k'});
        assert(text.endsWith('?') && !/\d/.test(text.replace('Acc.', '')), `${kind}: a question with no numbers: ${text}`);
      }
      eq(CS.LABELS.heatmap, 'Colour-coded table');
    });

    test('comparison focus: papers named in the question, in question order; partial names need whole words', () => {
      const studies = [{title: 'Fin-RATE: A Real-world Financial Analytics and Tracking Evaluation Benchmark for LLMs on SEC Filings'},
        {title: 'MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-source Retrieval Augmented Generation'},
        {title: 'Scalable Defense against In-the-wild Jailbreaking Attacks'}];
      const q = 'How do the conclusions of "MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-source Retrieval Augmented Generation" differ from those of "Fin-RATE: A Real-world Financial Analytics and Tracking Evaluation Benchmark for LLMs on SEC Filings"?';
      eq(M.namedStudies(studies, q).map(s => s.title.split(':')[0]), ['MultiRAG', 'Fin-RATE']);
      eq(M.namedStudies(studies, 'Compare Fin-RATE with MultiRAG').map(s => s.title.split(':')[0]), ['Fin-RATE', 'MultiRAG']);
      eq(M.namedStudies(studies, 'What do multiragged systems do?'), []);
      eq(M.namedStudies(studies, ''), []);
    });

    test('glossary: general meanings for abbreviations present in the labels only', () => {
      eq(CS.glossaryFor(['Acc.', 'Top-3', 'Spear. \\rho']).map(g => g.term), ['Spearman ρ', 'Acc.', 'Top-k']);
      eq(CS.glossaryFor(['Configuration', 'Calls', 'Cost (USD)']), []);
      eq(CS.glossaryFor(['Llama-3-8B / ASR']).map(g => g.term), ['ASR']);
      assert(!CS.glossaryFor(['Evaluation Acc. \\uparrow']).some(g => /\d/.test(g.meaning) && !/1 = same|0\.5/.test(g.meaning)), 'no numbers from the data');
    });

    if (!isNode) await atest('new SVG views: every mark opens its own source cell; texts verbatim', async () => {
      const host = document.createElement('div');
      host.style.width = '1000px';
      document.body.append(host);
      try {
        const check = (frame, table, expected) => {
          const marks = [...frame.querySelectorAll('.point')];
          eq(marks.length, expected, 'mark count');
          for (const mark of marks) {
            const row = table.rows.find(r => r.chunk_id === mark.getAttribute('data-chunk-id'));
            assert(row, 'mark names a row of this table');
            const cell = row.cells.find(c => c.source_id === mark.getAttribute('data-source-id'));
            assert(cell, `mark ${mark.getAttribute('data-point')} names a cell of its row`);
            assert(mark.getAttribute('aria-label').includes(CS.texPlain(cell.text)), 'accessible name carries the cell text');
          }
        };
        const opened = [];
        const onOpen = (row, cell) => opened.push([row.chunk_id, cell.source_id]);
        // Line over ordered columns: 4 rows × 7 columns.
        let table = real('2502.17874v2#A1.T5'), views = CS.viewsFor(table), frame = document.createElement('div');
        host.append(frame);
        let chart = root.ChartSvg.mount({document, frame, table, plan: M.chartPlan(table), title: 'T5', onOpen, view: {kind: 'line', ordered: views.find(v => v.kind === 'line').ordered}});
        chart.update(1000);
        check(frame, table, 28);
        const ends = [...frame.querySelectorAll('[data-end]')].map(n => n.textContent).sort();
        eq(ends, ['0.142', '0.853'], 'scale ends are the printed lowest and highest values');
        frame.querySelector('.point').dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));
        eq(opened.length, 1, 'Enter opens the source');
        // Error bars: 7 rows × 4 ± columns; slope: 4 pairs × 2; scatter: 3 rows.
        table = real('2607.00275v1#S4.T1'); views = CS.viewsFor(table);
        chart = root.ChartSvg.mount({document, frame, table, plan: M.chartPlan(table), title: 'T1', onOpen, view: {kind: 'errorbars', columns: views.find(v => v.kind === 'errorbars').columns}});
        chart.update(1000);
        check(frame, table, 28);
        assert([...frame.querySelectorAll('.value')].some(n => n.textContent === '0.140 ± 0.039'), 'printed ± text shown');
        chart = root.ChartSvg.mount({document, frame, table, plan: M.chartPlan(table), title: 'T1', onOpen, view: {kind: 'line', ordered: views.find(v => v.kind === 'line').ordered, column: 'all'}});
        chart.update(1000);
        check(frame, table, 28);
        table = real('2405.19358v2#S5.T2');
        const plan = M.chartPlan(table);
        chart = root.ChartSvg.mount({document, frame, table, plan, title: 'T2', onOpen, view: {kind: 'slope', panel: plan.panels[0]}});
        chart.update(1000);
        check(frame, table, 8);
        table = real('2609.11414v1#S6.T6'); views = CS.viewsFor(table);
        const sc = views.find(v => v.kind === 'scatter');
        chart = root.ChartSvg.mount({document, frame, table, plan: M.chartPlan(table), title: 'T6', onOpen, view: {kind: 'scatter', x: sc.x[0].column, y: sc.y[0].column}});
        chart.update(1000);
        check(frame, table, 3);
        eq([...frame.querySelectorAll('[data-end]')].map(n => n.textContent).length, 4, 'both axes labelled at the printed ends');
        // Narrow frames scroll instead of squeezing the drawing.
        const narrow = chart.update(400);
        assert(frame.classList.contains('scrolls') && narrow.layout.width >= 480, 'scatter keeps its minimum width (480) and scrolls instead of shrinking text');
      } finally { host.remove(); }
    });

    return results;
  }

  if (isNode) {
    run().then(results => {
      for (const r of results) console.log(`${r.ok ? 'PASS' : 'FAIL'}  ${r.name}${r.ok ? '' : `\n      ${r.error}`}`);
      const failed = results.filter(r => !r.ok).length;
      console.log(`\n${results.length - failed}/${results.length} passed`);
      process.exitCode = failed ? 1 : 0;
    });
  } else {
    root.runEvidenceTests = run;
  }
})(typeof self !== 'undefined' ? self : this);

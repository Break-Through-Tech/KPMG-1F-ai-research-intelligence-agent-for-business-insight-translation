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

    /* ---------- Regression tests for the Codex audit (2026-11-17) ---------- */
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

    /* ---------- Regression tests for the Codex verification blockers (2026-11-17) ---------- */
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

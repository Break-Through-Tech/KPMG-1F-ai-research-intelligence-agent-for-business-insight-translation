/* Redesigned research workspace. Same backend contracts and state rules as ui/app.js and
   ui/brief-library.js; source passages still render through the existing renderSourcePassage,
   exports through AnswerExport and audio through ResearchSpeech. Prose is always text nodes. */
(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const ICONS = {
    sidebar: 'M4 5h16v14H4z|M9 5v14', menu: 'M4 7h16|M4 12h16|M4 17h16', plus: 'M12 5v14|M5 12h14',
    bookmark: 'M6 4h12v16l-6-4-6 4z', sliders: 'M4 7h10|M18 7h2|M4 17h2|M10 17h10|M16 5v4|M8 15v4',
    sun: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z|M12 2v2|M12 20v2|M4.9 4.9l1.4 1.4|M17.7 17.7l1.4 1.4|M2 12h2|M20 12h2|M4.9 19.1l1.4-1.4|M17.7 6.3l1.4-1.4',
    moon: 'M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z', up: 'M12 19V5|M6 11l6-6 6 6', down: 'M6 9l6 6 6-6',
    x: 'M6 6l12 12|M6 18L18 6', chevron: 'M9 6l6 6-6 6', search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14z|M20 20l-3.5-3.5',
    book: 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z|M19 17v4H6', bulb: 'M9 18h6|M10 21h4|M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z',
    alert: 'M12 4l9 16H3z|M12 10v4|M12 17.5v.5', shield: 'M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z|M9 12l2 2 4-4',
    download: 'M12 4v11|M7 11l5 5 5-5|M5 20h14', upload: 'M12 16V5|M7 9l5-5 5 5|M5 20h14', history: 'M4 12a8 8 0 1 0 2.5-5.8|M4 4v4h4|M12 8v4l3 2',
    check: 'M5 12.5l4.5 4.5L19 7.5', external: 'M14 5h5v5|M19 5l-8 8|M11 6H6v12h12v-5', volume: 'M5 9v6h3l5 4V5L8 9z|M16 9a4 4 0 0 1 0 6',
    code: 'M8 8l-4 4 4 4|M16 8l4 4-4 4|M13 5l-2 14', clock: 'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16z|M12 8v4l3 2',
    layers: 'M12 4l8 4-8 4-8-4z|M4 12l8 4 8-4|M4 16l8 4 8-4', refresh: 'M20 12a8 8 0 1 1-2.5-5.8|M20 4v4h-4',
    sparkle: 'M12 4l1.8 4.7 4.7 1.8-4.7 1.8L12 17l-1.8-4.7-4.7-1.8 4.7-1.8z|M18.5 16.5v3|M17 18h3', archive: 'M4 5h16v4H4z|M6 9v10h12V9|M10 13h4',
    pencil: 'M4 20l1-4L16 5l3 3L8 19z', arrow: 'M5 12h14|M13 6l6 6-6 6',
    table: 'M4 5h16v14H4z|M4 10h16|M4 15h16|M10 5v14', chart: 'M5 19V5|M5 19h14|M9 15l3-4 3 2 4-6',
    copy: 'M9 9h10v10H9z|M5 15V5h10', type: 'M3 19l5-13 5 13|M5 14.5h6|M15 19v-5.5a2.75 2.75 0 0 1 5.5 0V19|M15 15.5h5.5', info: 'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16z|M12 11v5|M12 8v.5',
  };
  function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true'); svg.classList.add('icon');
    for (const d of ICONS[name].split('|')) {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', d); svg.append(path);
    }
    return svg;
  }
  document.querySelectorAll('[data-icon]').forEach(node => {
    const svg = icon(node.dataset.icon);
    if (node.className) svg.classList.add(...node.classList);
    node.replaceWith(svg);
  });
  function h(tag, props, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props || {})) {
      if (value == null || value === false) continue;
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key === 'math') renderPaperMath(node, String(value));
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else if (key in node && !key.startsWith('aria')) node[key] = value;
      else node.setAttribute(key, value);
    }
    for (const child of children.flat(Infinity)) if (child != null && child !== false) node.append(child);
    return node;
  }
  const btn = (label, onclick, className = 'text-btn', iconName) =>
    h('button', {type: 'button', class: className, onclick}, iconName && icon(iconName), h('span', {text: label}));
  const store = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); return true; } catch { return false; } },
  };
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const narrow = matchMedia('(max-width: 920px)');
  function morph(change) {
    if (!document.startViewTransition || reduced.matches || document.hidden) return change();
    // A skipped or timed-out transition still applies the change; it only loses the animation.
    const transition = document.startViewTransition(change);
    for (const phase of [transition.ready, transition.finished, transition.updateCallbackDone]) phase.catch(() => {});
  }

  const stage = $('#stage'), thread = $('#thread'), scroller = $('#scroll'), dock = $('#dock');
  new ResizeObserver(() => document.documentElement.style.setProperty('--dock-h', `${Math.ceil(dock.getBoundingClientRect().height)}px`)).observe(dock);
  const form = $('#composer'), queryInput = $('#query'), submit = $('#submit'), scenarioSelect = $('#scenario');
  const industryInput = $('#industry'), suggestions = $('#suggestions'), jumpLatest = $('#jump-latest');
  const inspector = $('#inspector'), inspectorBody = $('#inspector-body'), inspectorHeading = $('#inspector-heading');
  const inspectorNote = $('#inspector-note'), quotePreview = $('#citation-preview'), toastNode = $('#toast');
  const DEFAULT_NOTE = 'Inspect source quotes and the original paper. Citations are not proof of support.';

  let turnNumber = 0, returnFocus = null, previewTrigger = null, previewTimer, activeDemo = null, savedResult = null;
  let liveSynthesis = false, indexedMode = false, presentationEnabled = false, indexedContextId = null;
  let clarificationEnabled = false, researchConversationId = null, clarificationPending = false, activeClarificationTurn = null;
  let clarificationCard = null, conversationHistory = [], activePaperContextId = null, requestPending = false;
  let latestAnswer = null, appReady = false, retryContext = null, composing = false, compositionEndedAt = -Infinity;
  let needsDivider = false, toastTimer, libraryEnabled = false, revision = null, recordedMode = false;
  const explanationRenderers = new WeakMap();

  /* ---------- Status ---------- */
  function announce(message, visible = true) {
    toastNode.textContent = message;
    clearTimeout(toastTimer);
    toastNode.classList.toggle('show', visible && Boolean(message));
    if (visible) toastTimer = setTimeout(() => toastNode.classList.remove('show'), 5200);
  }

  /* ---------- Mode banner: Live research / Recorded replay / Mock demo / Not connected ---------- */
  let pageMode = 'pending', liveBudget = null;
  function setMode(mode, text) {
    pageMode = mode;
    document.body.dataset.mode = mode;
    const titles = {live: 'Live research', recorded: 'Saved research only', mock: 'Mock demo · not research output',
      demo: 'Synthetic examples · not research output', offline: 'Not connected'};
    const banner = $('#mode-banner');
    banner.dataset.tone = mode;
    $('#mode-banner-title').textContent = titles[mode] || mode;
    $('#mode-banner-text').textContent = text;
    const chip = $('#mode-chip');
    chip.hidden = false;
    chip.textContent = titles[mode] || mode;
    chip.className = `mode ${mode === 'live' ? 'ok' : mode === 'recorded' ? '' : 'warn'}`;
    const side = document.getElementById('side-mode');
    if (side) { side.dataset.tone = mode; side.title = text; side.replaceChildren(h('span', {class: 'mode-dot', 'aria-hidden': 'true'}), h('span', {class: 'side-label', text: titles[mode] || mode}), h('span', {class: 'sr-only', text: `. ${text}`})); }
  }
  function liveText(config) {
    const count = Number(config.index?.count || 0).toLocaleString();
    const budget = config.call_budget;
    const index = `the 100-paper research index (${count} passages${config.index?.indexed_records_sha256 ? `, ${config.index.indexed_records_sha256.slice(0, 8)}` : ''})`;
    if (!budget) return `Fresh answers from ${index}. Each question uses model calls.`;
    const left = `${budget.remaining} of ${budget.cap} approved model calls left (a question uses up to ${budget.per_question.with_industry} with an industry, ${budget.per_question.without_industry} without)`;
    return `Fresh answers from ${index} · ${budget.provider} · ${left}.` +
      (budget.remaining < budget.per_question.with_industry ? ' New questions are refused before any model call until a budget is approved.' : '');
  }
  async function refreshBudget() {
    if (pageMode !== 'live') return;
    try {
      const config = await (await fetch('/api/config', {signal: AbortSignal.timeout(10000)})).json();
      if (config.live) { liveBudget = config.call_budget || null; setMode('live', liveText(config)); }
    } catch { /* keep the last banner */ }
  }

  /* ---------- Shell: views (home / brief / library), rail, theme ---------- */
  // The workspace has no collapsible sidebar; these remain as no-ops for shared call sites.
  function setDrawer() {}
  function syncScrim() {}

  const darkQuery = matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => { const t = ReadingPrefs.get('theme'); return t.includes('dark') || (t === 'system' && darkQuery.matches); };
  function syncTheme() {
    const toggle = $('#theme-toggle');
    toggle.replaceChildren(icon(isDark() ? 'sun' : 'moon'));
    toggle.title = isDark() ? 'Switch to light theme' : 'Switch to dark theme';
    toggle.setAttribute('aria-label', toggle.title);
    const sideTheme = document.getElementById('side-theme');
    if (sideTheme) { sideTheme.replaceChildren(icon(isDark() ? 'sun' : 'moon'), h('span', {class: 'side-label', text: isDark() ? 'Light theme' : 'Dark theme'})); sideTheme.title = toggle.title; }
  }
  $('#theme-toggle').addEventListener('click', () => morph(() => { ReadingPrefs.set('theme', isDark() ? 'light' : 'dark'); }));
  document.addEventListener('reading-preferences-applied', () => { syncTheme(); syncPrefs(); });
  darkQuery.addEventListener('change', syncTheme);

  let currentView = 'home', activeTurn = null;
  function placeDock() {
    // One composer, moved to where it is used: the home page, or the end of the brief being read.
    // Home: in the middle of the page. Reading an answer: pinned under the reading column.
    if (currentView === 'home') $('#home-slot').append(dock);
    else if (currentView === 'thread' && activeTurn) $('#main').append(dock);
    dock.hidden = currentView === 'library' || (currentView === 'thread' && !activeTurn);
  }
  // The requested view is recorded immediately; an animated change applies whichever view is
  // requested last, so a quick Library → brief switch cannot be overtaken by a pending transition.
  let targetView = null;
  // Navigation token (audit M2): every navigation advances it; a slow saved-brief response may
  // change the view only if its token is still current when it arrives.
  const nav = AsyncGuards.createNavGuard();
  function setView(requested, animate = true) {
    if ((targetView ?? stage.dataset.view) === requested) return;
    nav.bump();
    targetView = requested;
    const change = () => {
      const view = targetView;
      if (stage.dataset.view === view) return;
      currentView = view;
      stage.dataset.view = view;
      stage.classList.toggle('is-home', view === 'home');
      $('#hero').hidden = view !== 'home'; thread.hidden = view !== 'thread'; $('#library-view').hidden = view !== 'library';
      $('#examples').hidden = view !== 'home' || recordedMode || pageMode === 'mock' || pageMode === 'offline';
      $('#thread-title').classList.toggle('show', view === 'thread');
      $('#nav-research').toggleAttribute('aria-current', view !== 'library');
      if (view !== 'library') $('#nav-research').setAttribute('aria-current', 'page');
      $('#library-open').toggleAttribute('aria-current', view === 'library');
      if (view === 'library') $('#library-open').setAttribute('aria-current', 'page');
      if (view !== 'thread') { suggestions.hidden = true; jumpLatest.hidden = true; }
      placeDock();
      autosize();
      syncTopbar();
      if (view !== 'thread') scroller.scrollTop = 0;
    };
    if (animate) morph(change); else change();
  }
  $('#nav-research').addEventListener('click', () => setView(activeTurn ? 'thread' : 'home'));

  /* ---------- Answer views (Answer / Sources / Evidence) and the top bar ---------- */
  const tabButtons = [...document.querySelectorAll('#view-tabs .view-tab')];
  // One indicator slides between the view tabs instead of each tab drawing its own underline.
  const tabIndicator = h('span', {class: 'tab-indicator', 'aria-hidden': 'true'});
  $('#view-tabs').append(tabIndicator);
  function moveIndicator(animate = true) {
    const selected = tabButtons.find(button => button.getAttribute('aria-selected') === 'true');
    if (!selected || $('#view-tabs').hidden) return;
    tabIndicator.classList.toggle('instant', !animate);
    tabIndicator.style.width = `${selected.offsetWidth}px`;
    tabIndicator.style.transform = `translateX(${selected.offsetLeft}px)`;
  }
  addEventListener('resize', () => moveIndicator(false));
  document.addEventListener('reading-preferences-applied', () => requestAnimationFrame(() => moveIndicator(false)));
  function setTab(name, {focus = false, scroll = true} = {}) {
    const turn = activeTurn;
    const panes = turn ? turn.querySelectorAll('.brief-pane') : [];
    if (!panes.length) return;
    // Each view keeps its own reading position: leaving a tab remembers where you were.
    turn.scrollMemory = turn.scrollMemory || {};
    const previous = turn.dataset.tab;
    if (previous && previous !== name) turn.scrollMemory[previous] = scroller.scrollTop;
    turn.dataset.tab = name;
    panes.forEach(node => { node.hidden = node.dataset.pane !== name; });
    stage.dataset.tab = name;
    tabButtons.forEach(button => { const selected = button.dataset.tab === name; button.setAttribute('aria-selected', String(selected)); button.tabIndex = selected ? 0 : -1; });
    moveIndicator(previous !== undefined && previous !== name);
    if (scroll) scroller.scrollTop = previous === name ? scroller.scrollTop : (turn.scrollMemory[name] || 0);
    if (focus) $(`.brief-pane[data-pane="${name}"] .pane-title`, turn)?.focus({preventScroll: true});
  }
  tabButtons.forEach(button => button.addEventListener('click', () => setTab(button.dataset.tab)));
  $('#view-tabs').addEventListener('keydown', event => {
    if (!['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
    const index = tabButtons.indexOf(document.activeElement);
    const next = tabButtons[(index + (event.key === 'ArrowRight' ? 1 : tabButtons.length - 1)) % tabButtons.length];
    next.click(); next.focus();
  });
  function syncTopbar() {
    const turn = currentView === 'thread' ? activeTurn : null;
    const demo = turn?.demoState?.demo;
    const hasBrief = Boolean(turn?.querySelector('.brief-pane'));
    $('#view-tabs').hidden = !hasBrief;
    stage.classList.toggle('has-tabs', hasBrief);
    if (hasBrief) setTab(turn.dataset.tab || 'answer', {scroll: false});
    else delete stage.dataset.tab;
    const evidence = demo?.result?.evidence || [];
    const papers = new Set(evidence.map(p => p.arxiv_id || p.title || 'unknown')).size;
    $('#tab-sources-count').textContent = hasBrief && papers ? String(papers) : '';
    const stack = $('#source-stack');
    stack.hidden = !hasBrief || !evidence.length;
    if (!stack.hidden) {
      stack.replaceChildren(icon('layers'), h('span', {text: `${papers} paper${papers === 1 ? '' : 's'}`}));
      stack.setAttribute('aria-label', `${evidence.length} source passages from ${papers} paper${papers === 1 ? '' : 's'}. Open Sources.`);
    }
    const action = $('#brief-action');
    action.hidden = !hasBrief || !turn.tools;
    if (!action.hidden) action.replaceChildren(icon(demo.library ? 'shield' : 'bookmark'), h('span', {class: 'btn-text', text: demo.library ? 'Review' : 'Save'}));
  }
  $('#source-stack').addEventListener('click', () => setTab('sources', {focus: true}));
  $('#brief-action').addEventListener('click', event => activeTurn?.tools?.reveal('brief', event.currentTarget));

  /* ---------- Segmented controls & reading preferences ---------- */
  let segmentNumber = 0;
  function segmented(labelledby, options, value, onChange) {
    const name = `seg-${++segmentNumber}`;
    const group = h('div', {class: 'seg', role: 'radiogroup', 'aria-labelledby': labelledby});
    for (const [optionValue, label] of options) {
      const input = h('input', {type: 'radio', name, value: optionValue, checked: optionValue === value,
        onchange: () => onChange(optionValue)});
      group.append(h('label', null, input, h('span', {text: label})));
    }
    group.select = next => group.querySelectorAll('input').forEach(input => { input.checked = input.value === next; });
    return group;
  }
  // Research mode: Baseline RAG (the stable /api/research pipeline, always the default) or the
  // experimental multi-agent route, offered only when the backend reports agentic_mode.
  let researchEngine = 'baseline', agenticAvailable = false;
  const engineSeg = segmented('engine-label', [['baseline', 'Baseline RAG'], ['agentic', 'Multi-Agent']], 'baseline', value => {
    researchEngine = agenticAvailable && value === 'agentic' ? 'agentic' : 'baseline';
    syncSettingsSummary();
  });
  $('#engine-seg').append(engineSeg);
  function setAgenticAvailable(available) {
    agenticAvailable = available;
    $('#engine-field').hidden = !available;
    if (!available) { researchEngine = 'baseline'; engineSeg.select('baseline'); }
  }
  // Every explanation-style control is the same preference; extra copies (inside answers) are kept in sync.
  const explanationSwitches = new Set();
  function explanationSwitch(labelledby) {
    const seg = segmented(labelledby, [['technical', 'Technical'], ['plain', 'Plain language']],
      ReadingPrefs.get('explanation'), value => ReadingPrefs.set('explanation', value));
    explanationSwitches.add(seg);
    return seg;
  }
  const explanationSeg = explanationSwitch('explanation-label');
  $('#explanation-seg').append(explanationSeg);
  const prefControls = {};
  (() => {
    const body = $('#prefs-body');
    // A single theme: no appearance picker.
    for (const [name, label, options] of [
      ['size', 'Text size', [['100', '100%'], ['125', '125%'], ['150', '150%']]],
      ['spacing', 'Line spacing', [['standard', 'Standard'], ['relaxed', 'Relaxed'], ['wide', 'Wide']]],
      ['explanation', 'Explanation style', [['technical', 'Technical'], ['plain', 'Plain language']]]]) {
      prefControls[name] = segmented(`pref-${name}`, options, ReadingPrefs.get(name), value => ReadingPrefs.set(name, value));
      body.append(h('div', {class: 'field'}, h('span', {class: 'field-label', id: `pref-${name}`, text: label}), prefControls[name]));
    }
  })();
  function syncPrefs() {
    for (const name of Object.keys(prefControls)) prefControls[name].select(ReadingPrefs.get(name));
    for (const seg of explanationSwitches) seg.select(ReadingPrefs.get('explanation'));
    $('#prefs-status').textContent = ReadingPrefs.storageUnavailable() ? 'Preferences apply for this page. Browser storage is unavailable.' : '';
    syncSettingsSummary();
  }
  const prefsDialog = $('#prefs');
  $('#prefs-open').addEventListener('click', () => prefsDialog.showModal());
  $('#prefs-close').addEventListener('click', () => prefsDialog.close());
  $('#prefs-reset').addEventListener('click', () => ReadingPrefs.reset());
  for (const dialog of document.querySelectorAll('dialog')) {
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  }

  /* ---------- Composer ---------- */
  const enterKey = 'research-desk.enter-behavior.v1';
  let enterBehavior = 'send'; void enterKey; // Enter sends; Shift+Enter inserts a newline.
  function updateEntryHint() {
    $('#entry-hint').textContent = 'Enter sends the question. Shift+Enter inserts a new line.';
  }
  $('#enter-seg').append(segmented('enter-label', [['newline', 'Inserts newline'], ['send', 'Sends question']], enterBehavior, value => {
    enterBehavior = value; updateEntryHint();
    if (!store.set(enterKey, value)) announce('Preference storage unavailable; applies to this tab only.');
  }));
  updateEntryHint();
  const inlineIndustry = [];
  for (const name of ['Banking', 'Insurance', 'Healthcare', 'Retail']) {
    $('#industry-quick').append(btn(name, () => { industryInput.value = name.toLowerCase(); syncSettingsSummary(); }, 'quick-chip'));
    // Same choices, visible under the composer on the home screen: business insights need an industry.
    const toggle = btn(name, () => {
      industryInput.value = industryInput.value.trim().toLowerCase() === name.toLowerCase() ? '' : name.toLowerCase();
      syncSettingsSummary();
    }, 'quick-chip');
    toggle.dataset.industry = name.toLowerCase();
    inlineIndustry.push(toggle);
    $('#industry-inline-chips').append(toggle);
  }
  industryInput.addEventListener('input', syncSettingsSummary);
  $('#risk-assessment').addEventListener('change', syncSettingsSummary);
  scenarioSelect.addEventListener('change', syncSettingsSummary);
  function syncSettingsSummary() {
    // Always say what the next question will use, so the current configuration is visible without opening the panel.
    const parts = [];
    if (researchEngine === 'agentic') parts.push('Multi-Agent');
    if (!$('#industry-field').hidden) parts.push(industryInput.value.trim() ? `Industry: ${industryInput.value.trim()}` : 'No industry');
    parts.push(ReadingPrefs.get('explanation') === 'plain' ? 'Plain language' : 'Technical');
    if (!$('#risk-field').hidden && $('#risk-assessment').checked) parts.push('Risk & compliance check');
    if (!$('#scenario-field').hidden && scenarioSelect.selectedIndex > 0) parts.push(scenarioSelect.selectedOptions[0].textContent);
    $('#settings-summary').textContent = parts.join(' · ');
    const current = industryInput.value.trim().toLowerCase();
    for (const toggle of inlineIndustry) toggle.setAttribute('aria-pressed', String(toggle.dataset.industry === current));
    $('#industry-inline').hidden = $('#industry-field').hidden;
  }
  function requestBusinessInsights(query) {
    // Summary-only answers: keep the question, open settings at the industry field.
    setQuery(query);
    setSettings(true);
    dock.scrollIntoView({block: 'nearest', behavior: reduced.matches ? 'auto' : 'smooth'});
    industryInput.focus({preventScroll: true});
    announce('Choose or type an industry, then send the question again to get business insights.');
  }
  function setSettings(open) {
    $('#settings').classList.toggle('open', open);
    $('#settings').inert = !open;
    $('#settings-toggle').setAttribute('aria-expanded', String(open));
  }
  $('#settings-toggle').addEventListener('click', () => setSettings(!$('#settings').classList.contains('open')));
  function autosize() {
    // An empty box keeps the stylesheet height (measuring it while detached or hidden is unreliable).
    queryInput.style.height = 'auto';
    if (queryInput.value && queryInput.isConnected && queryInput.offsetWidth) queryInput.style.height = `${Math.min(queryInput.scrollHeight, 240)}px`;
    else queryInput.style.height = '';
    const length = Array.from(queryInput.value).length;
    $('#counter').hidden = length < 1600;
    $('#counter').textContent = `${length} / 2000`;
    form.classList.toggle('has-text', Boolean(queryInput.value.trim()));
  }
  function setQuery(text) { queryInput.value = text; autosize(); }
  queryInput.addEventListener('input', autosize);
  queryInput.addEventListener('compositionstart', () => { composing = true; });
  queryInput.addEventListener('compositionend', () => { composing = false; compositionEndedAt = performance.now(); });
  queryInput.addEventListener('keydown', event => {
    // Safari can report isComposing=false on the Enter that commits an IME candidate.
    if (event.key !== 'Enter' || event.shiftKey || event.repeat || event.isComposing ||
        composing || event.keyCode === 229 || performance.now() - compositionEndedAt < 100) return;
    if (event.ctrlKey || event.metaKey || (enterBehavior === 'send' && !event.altKey)) {
      event.preventDefault();
      if (!submit.disabled && !requestPending) form.requestSubmit();
    }
  });
  const EXAMPLES = [
    // Grounded in papers that are in the 100-paper demo index (retrieval checked without model calls).
    'How accurately do LLMs answer financial analysis questions on SEC filings, and where do they fail most?',
    'By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?',
    'Do large language models show financial bias when making investment decisions, and how much can it be reduced?',
  ];
  for (const text of EXAMPLES) {
    $('#examples').append(h('button', {type: 'button', class: 'example', onclick: () => {
      if (requestPending) return;
      setQuery(text); queryInput.focus();
      announce('Example added. Edit the question, then send when ready.');
    }}, h('span', {text}), icon('arrow')));
  }

  function setQuestionBusy(busy) {
    requestPending = busy;
    // Preserve the focused submit button during requests, while guarding repeats.
    submit.disabled = !appReady;
    if (busy) submit.setAttribute('aria-disabled', 'true'); else submit.removeAttribute('aria-disabled');
    form.classList.toggle('busy', busy);
    document.querySelectorAll('.retry-question, #suggestions button, #new-research, .example').forEach(button => {
      button.disabled = busy || !appReady;
    });
    if (clarificationCard) {
      clarificationCard.querySelectorAll('input, textarea').forEach(control => { control.disabled = busy; });
      const send = $('.question-submit', clarificationCard);
      if (send) { send.disabled = busy || !queryInput.value.trim(); $('span', send).textContent = busy ? 'Submitting…' : 'Submit answer'; }
    }
    thread.setAttribute('aria-busy', String(busy));
  }

  /* ---------- Shared research helpers (unchanged semantics) ---------- */
  const isSynthesis = demo => demo.mode === 'indexed' || demo.mode === 'live-synthesis' || demo.result?.summary.generation_method === 'cited-synthesis-v1';
  const isReal = demo => demo.mode !== 'fixture';
  const runLabel = demo => {
    if (demo.library?.replayed) return 'Saved snapshot · No new research executed · Original provenance retained';
    if (isSynthesis(demo)) return 'LLM synthesis · Citation quotes checked · Not independently verified';
    const generation = demo.result?.provenance?.generation;
    return generation?.provider || generation?.prompt_version
      ? 'Saved research result · Recorded generation provenance in Details · Not independently verified'
      : 'Saved research result · Generation method unverified · Inspect provenance in Details';
  };
  const STATES = {
    'plain-language': ['Full draft · definition fixture', 'Synthetic example with explicit term support.', 'ok'],
    full: ['Full draft', 'Research summary and conditional business implications are available.', 'ok'],
    partial: ['Partial draft', 'The research summary is available. Business translation is unavailable; inspect stage details.', 'warn'],
    'summary-only': ['Research summary', 'Business translation was not requested. Add industry context to request it.', 'ok'],
    insufficient: ['Abstention · insufficient support', 'Passages are available, but do not support an answer.', 'warn'],
    empty: ['No evidence', 'No passages were retrieved. Generation was skipped.', 'warn'],
    'execution-error': ['Research execution failed', 'No draft was accepted. Inspect the failed stage and retry.', 'bad'],
    'provider-error': ['Provider error · simulated', 'No draft was produced. Choose another example state to continue.', 'bad'],
  };
  function reviewText(demo) {
    const latest = demo.library?.reviews.at(-1);
    if (!latest) return 'Draft · Not approved';
    return {approve: 'Saved version approved by human reviewer · Not source certification',
      revise: 'Changes requested · Not approved', reject: 'Rejected · Not approved'}[latest.decision];
  }
  const reviewTone = demo => ({approve: 'ok', revise: 'warn', reject: 'bad'}[demo.library?.reviews.at(-1)?.decision] || 'draft');
  window.BriefLibrary = {reviewText}; // research-speech.js reads this, as before.

  function readyAnnouncement(demo, number) {
    const outcome = {
      'plain-language': 'ready. Draft, not approved.', full: 'ready. Draft, not approved.',
      partial: demo.error?.stage === 'business'
        ? 'failed: business implications; research summary retained. Not approved.'
        : demo.error?.stage === 'regulatory'
          ? 'failed: risk and compliance assessment; research summary and business implications retained. Not approved.'
          : 'ready. Partial draft; no business recommendation is supported. Not approved.',
      'summary-only': 'ready. Research summary; business translation not requested. Not approved.',
      insufficient: 'abstained: insufficient support.', empty: 'unavailable: no evidence retrieved.',
      'provider-error': 'failed: simulated provider error.', 'execution-error': 'failed: research execution error.',
    }[demo.scenario];
    if (demo.library?.replayed) return `Answer ${number} opened from saved version ${demo.library.version.number}. ${reviewText(demo)}. No model call.`;
    const mode = !isReal(demo) ? ' Synthetic example.' : (!isSynthesis(demo) ? ' Saved result; no live query.' : '');
    return `Answer ${number} ${outcome}${mode}`;
  }
  function rememberAcceptedTurn(query, demo) {
    if (!isSynthesis(demo) || !activePaperContextId || demo.result?.provenance?.paper_context_id !== activePaperContextId) return;
    const summary = demo.result.summary;
    const content = Array.from([...(summary.claims || []).map(claim => claim.text), ...(summary.limitations || [])].join('\n\n')).slice(0, 6000).join('');
    if (!content.trim()) return;
    conversationHistory.push({role: 'user', content: Array.from(query).slice(0, 2000).join('')}, {role: 'assistant', content});
    while (conversationHistory.length > 12 || conversationHistory.reduce((total, message) => total + message.content.length, 0) > 24000) {
      conversationHistory.splice(0, 2);
    }
  }
  const sourceLocation = passage => (passage.page_number != null ? `PDF page ${passage.page_number}`
    : passage.table_id ? `Table ${passage.table_id}${passage.row_label ? ` · ${passage.row_label}` : ''}`
      : (passage.section || passage.subsection || 'No PDF page'));
  const citationSourceContext = passage => `${passage.title}, ${sourceLocation(passage)}`;
  function focusInitiator(trigger) {
    const fallback = queryInput.getClientRects().length ? queryInput : scroller;
    const target = trigger?.isConnected && !trigger.disabled && trigger.getClientRects().length ? trigger : fallback;
    target.focus({preventScroll: true});
  }

  /* ---------- Evidence inspector ---------- */
  function setInspector(open, trigger = null) {
    if (open && trigger) returnFocus = trigger;
    const wasOpen = document.body.classList.contains('insp-open');
    if (open && document.body.classList.contains('review-open')) { document.body.classList.remove('review-open'); $('#review-drawer').inert = true; }
    document.body.classList.toggle('insp-open', open);
    inspector.inert = !open;
    $('#evidence-toggle').setAttribute('aria-expanded', String(open));
    syncScrim();
    if (!open && wasOpen) { ResearchSpeech.stopAll(); focusInitiator(returnFocus); }
  }
  $('#inspector-close').addEventListener('click', () => setInspector(false));
  $('#evidence-toggle').addEventListener('click', event => {
    if (document.body.classList.contains('insp-open')) return setInspector(false);
    if (activeDemo?.demo) showEvidence(activeDemo.demo, activeDemo.number, activeDemo.selected || 0, event.currentTarget, activeDemo.claim);
    else { setInspector(true, event.currentTarget); inspectorHeading.focus(); }
  });
  function inspectorChrome(heading, kicker, note) {
    inspectorHeading.textContent = heading; $('#inspector-kicker').textContent = kicker; inspectorNote.textContent = note;
  }
  function resetEvidence(message) {
    ResearchSpeech.stopAll(); closePreview();
    inspectorChrome('Source context', 'Evidence', DEFAULT_NOTE);
    activeDemo = null;
    const focusWasInContent = inspectorBody.contains(document.activeElement);
    inspectorBody.replaceChildren(h('p', {class: 'empty', text: message}));
    if (focusWasInContent) inspectorHeading.focus();
  }
  function showEvidence(demo, number, selected = 0, trigger = null, claim = null, highlightId = null) {
    closePreview();
    inspectorChrome('Source context', isReal(demo) ? `Answer ${number} · Real-paper evidence` : `Example ${number} · ${STATES[demo.scenario][0]}`,
      savedResult && !liveSynthesis ? 'Source passages from the paper. Open the original section or cited PDF page.' : DEFAULT_NOTE);
    const focusWasInContent = inspectorBody.contains(document.activeElement);
    activeDemo = {demo, number, selected, claim};
    const evidence = demo.result?.evidence ?? [];
    const choices = h('div', {class: 'source-tabs', role: 'group', 'aria-label': 'Source passages'});
    const passageView = h('article', {class: 'passage'});
    function selectPassage(index) {
      ResearchSpeech.stopAll();
      activeDemo.selected = index;
      const passage = evidence[index];
      choices.querySelectorAll('button').forEach((button, position) => button.setAttribute('aria-pressed', String(position === index)));
      // Existing evidence renderer: metadata, cited claim, exact quote, structured source and table navigation.
      renderSourcePassage(passageView, passage, {claim, isFixture: !isReal(demo), onReturn: () => setInspector(false)});
      inspectorHeading.textContent = `Source ${index + 1} of ${evidence.length}`;
      passageView.prepend(evidenceChecks(passage, claim, highlightId));
      if (passage.representation === 'linearized_table' && Array.isArray(passage.table_cells) && Array.isArray(passage.table_headers)) {
        const row = {table_row: passage.table_row, row_label: passage.row_label,
          cells: passage.table_cells.map(cell => ({...cell, parsed: EvidenceModel.parseNumber(cell.text)}))};
        const grid = rowGrid({headers: passage.table_headers}, row, highlightId);
        const anchor = passageView.querySelector('h4');
        const label = h('h4', {text: 'Table row as extracted'});
        const status = h('p', {class: 'meta', text: `${EvidenceModel.headerStatus(passage).label} ${highlightId ? `Selected cell: ${highlightId}.` : ''}`});
        if (anchor) anchor.before(label, grid, status); else passageView.append(label, grid, status);
      }
      tidySource(passageView, passage);
      passageView.classList.remove('swap'); void passageView.offsetWidth; passageView.classList.add('swap');
      ResearchSpeech.attach(passageView, {id: `source:${number}:${passage.chunk_id}`,
        label: `Citation ${index + 1} · ${citationSourceContext(passage)}`, text: ResearchSpeech.source(passage, index + 1)});
      document.querySelectorAll('.source-row[data-active]').forEach(row => row.removeAttribute('data-active'));
      document.querySelector(`#turn-${number} .source-row[data-passage="${index}"]`)?.setAttribute('data-active', '');
    }
    evidence.forEach((passage, index) => {
      const location = passage.representation === 'linearized_table'
        ? [(passage.caption || '').split(/[:.]/)[0].trim() || 'Table', passage.row_label].filter(Boolean).join(' · ')
        : passage.source === 'pdf' && passage.page_number != null ? `page ${passage.page_number}` : (passage.section || sourceLocation(passage));
      choices.append(h('button', {type: 'button', class: 'source-tab', title: citationSourceContext(passage),
        'aria-label': `Citation ${index + 1}, ${passage.source.toUpperCase()}, ${location}`, onclick: () => selectPassage(index)},
        h('b', {text: String(index + 1)}), h('span', {text: location})));
    });
    if (evidence.length) {
      inspectorBody.replaceChildren(choices, passageView);
      selectPassage(Math.min(selected, evidence.length - 1));
    } else {
      inspectorBody.replaceChildren(h('p', {class: 'empty', text: demo.result ? 'No evidence to inspect. This is not a provider failure.' : 'No draft or passages. This provider failure is simulated.'}));
    }
    inspectorBody.scrollTop = 0;
    setInspector(true, trigger);
    if (trigger || focusWasInContent) inspectorHeading.focus({preventScroll: true});
  }

  /* ---------- Citation preview ---------- */
  function closePreview() {
    clearTimeout(previewTimer);
    const trigger = previewTrigger;
    const focusedInside = quotePreview.contains(document.activeElement);
    if (quotePreview.matches(':popover-open')) quotePreview.hidePopover();
    trigger?.removeAttribute('aria-details');
    trigger?.setAttribute('aria-expanded', 'false');
    previewTrigger = null;
    if (focusedInside) focusInitiator(trigger);
  }
  function deferClosePreview() {
    clearTimeout(previewTimer);
    previewTimer = setTimeout(() => {
      if (!quotePreview.contains(document.activeElement) && document.activeElement !== previewTrigger && !quotePreview.matches(':hover')) closePreview();
    }, 180);
  }
  function showQuote(item, demo, number, index, trigger) {
    clearTimeout(previewTimer);
    if (previewTrigger === trigger && quotePreview.matches(':popover-open')) return;
    closePreview();
    previewTrigger = trigger;
    trigger.setAttribute('aria-details', 'citation-preview');
    trigger.setAttribute('aria-expanded', 'true');
    const passage = demo.result.evidence[index];
    const quotes = [...new Set((item.support || []).filter(support => support.chunk_id === passage.chunk_id).map(support => support.quote))];
    const close = h('button', {type: 'button', class: 'icon-btn small', 'aria-label': 'Close cited quote',
      onclick: () => { closePreview(); focusInitiator(trigger); }}, icon('x'));
    const actions = h('div', {class: 'quote-actions'});
    if (passage.source_url) {
      actions.append(h('a', {href: passage.source_url, target: '_blank', rel: 'noopener noreferrer', class: 'text-btn',
        'aria-label': `Open original paper, ${citationSourceContext(passage)}, opens in a new tab`}, h('span', {text: 'Open original paper'}), icon('external')));
    }
    actions.append(h('button', {type: 'button', class: 'solid-btn small', 'aria-label': `Inspect source context, ${citationSourceContext(passage)}`,
      onclick: () => { closePreview(); showEvidence(demo, number, index, trigger, item); }}, h('span', {text: 'Inspect source context'}), icon('chevron')));
    quotePreview.replaceChildren(
      h('div', {class: 'quote-head'}, h('span', {class: 'cite-num', text: String(index + 1)}),
        h('p', {class: 'quote-label', text: quotes.length ? 'Cited quote' : 'Source passage'}), close),
      h('div', {class: 'quote-excerpts'}, (quotes.length ? quotes : [passage.text]).map(quote => h('blockquote', {math: quote}))),
      h('p', {class: 'quote-source', text: `${passage.title} · ${sourceLocation(passage)}`}), actions);
    quotePreview.showPopover();
    positionQuotePreview();
  }
  function positionQuotePreview() {
    if (!previewTrigger || !quotePreview.matches(':popover-open')) return;
    const rect = previewTrigger.getBoundingClientRect();
    const box = quotePreview.getBoundingClientRect();
    quotePreview.style.left = `${Math.max(12, Math.min(rect.left - 16, innerWidth - box.width - 12))}px`;
    const below = rect.bottom + 8 + box.height <= innerHeight - 12;
    quotePreview.dataset.side = below ? 'below' : 'above';
    const top = below ? rect.bottom + 8 : rect.top - box.height - 8;
    quotePreview.style.top = `${Math.max(12, Math.min(top, innerHeight - box.height - 12))}px`;
  }
  quotePreview.addEventListener('pointerenter', () => clearTimeout(previewTimer));
  quotePreview.addEventListener('pointerleave', deferClosePreview);
  quotePreview.addEventListener('focusout', deferClosePreview);
  quotePreview.addEventListener('keydown', event => {
    if (event.key !== 'Tab' || !previewTrigger) return;
    const controls = quotePreview.querySelectorAll('a, button');
    if ((event.shiftKey && document.activeElement === controls[0]) || (!event.shiftKey && document.activeElement === controls[controls.length - 1])) {
      const trigger = previewTrigger;
      trigger.focus({preventScroll: true});
      closePreview();
      if (event.shiftKey) event.preventDefault();
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented) return;
    if (previewTrigger) {
      const trigger = previewTrigger;
      closePreview(); trigger.focus({preventScroll: true});
      event.preventDefault();
    } else if (document.querySelector('dialog[open]')) {
      return;
    } else if (document.body.classList.contains('insp-open')) {
      setInspector(false); event.preventDefault();
    } else if (document.body.classList.contains('review-open')) {
      setReview(false); event.preventDefault();
    } else if ($('#settings').classList.contains('open')) {
      setSettings(false); $('#settings-toggle').focus(); event.preventDefault();
    }
  });
  document.addEventListener('pointerdown', event => {
    if (!quotePreview.contains(event.target) && event.target.closest?.('.citation') !== previewTrigger) closePreview();
  });
  scroller.addEventListener('scroll', positionQuotePreview, {passive: true});
  const dismissForReadingGesture = event => { if (!quotePreview.contains(event.target)) closePreview(); };
  window.addEventListener('wheel', dismissForReadingGesture, {passive: true});
  window.addEventListener('touchmove', dismissForReadingGesture, {passive: true});
  window.addEventListener('resize', closePreview);

  // One-time hint that citation numbers open their source quote; hidden after the first citation is used.
  const citeHintKey = 'research-desk.cite-hint-seen.v1';
  let citeHintSeen = store.get(citeHintKey) === '1';
  function citeHint() {
    return citeHintSeen ? null : h('p', {class: 'cite-hint'}, h('span', {class: 'cite-sample', 'aria-hidden': 'true', text: '1'}),
      h('span', {text: 'Select a number to see the exact quote it came from.'}));
  }
  function dismissCiteHint() {
    if (citeHintSeen) return;
    citeHintSeen = true;
    store.set(citeHintKey, '1');
    document.querySelectorAll('.cite-hint').forEach(node => node.remove());
  }

  function cited(tag, item, demo, number, className) {
    const node = h(tag, {class: className}, h('span', {class: 'cited-text', math: item.text}));
    for (const id of item.chunk_ids) {
      const index = demo.result.evidence.findIndex(passage => passage.chunk_id === id);
      if (index < 0) throw new Error('Unknown citation');
      const passage = demo.result.evidence[index];
      const citation = h('button', {type: 'button', class: 'citation', text: String(index + 1),
        'aria-label': `Inspect citation ${index + 1}, ${citationSourceContext(passage)}`,
        'aria-haspopup': 'dialog', 'aria-controls': 'citation-preview', 'aria-expanded': 'false'});
      citation.dataset.turn = number; citation.dataset.passage = index;
      citation.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') showQuote(item, demo, number, index, citation); });
      citation.addEventListener('pointerleave', deferClosePreview);
      citation.addEventListener('blur', deferClosePreview);
      citation.addEventListener('keydown', event => {
        if (event.key === 'Tab' && !event.shiftKey && previewTrigger === citation) {
          event.preventDefault();
          quotePreview.querySelector('button, a').focus({preventScroll: true});
        }
      });
      // Opening the original URL stays a separate, explicitly named link inside the preview.
      citation.title = 'Open this source';
      citation.setAttribute('aria-controls', 'inspector');
      citation.addEventListener('click', () => {
        dismissCiteHint();
        closePreview();
        showEvidence(demo, number, index, citation, item);
      });
      node.append(' ', citation);
    }
    return node;
  }

  /* ---------- Turns: one brief on screen at a time ---------- */
  function answerHeading(number, text = `Answer ${number}`) {
    return h('h2', {id: `answer-${number}`, class: 'answer-kicker sr-only', tabIndex: -1, text});
  }
  function elapsedCounter() {
    // The endpoint answers once with a single envelope; this only shows that the wait is alive.
    const node = h('span', {class: 'elapsed', 'aria-hidden': 'true'});
    const started = performance.now();
    const timer = setInterval(() => {
      if (!node.isConnected) return clearInterval(timer);
      const seconds = Math.round((performance.now() - started) / 1000);
      if (seconds >= 4) node.textContent = `${seconds}s`;
    }, 1000);
    return node;
  }
  function createTurn(query, number, questionLabel, loading) {
    if (needsDivider && thread.children.length) thread.append(h('p', {class: 'divider', hidden: true, text: 'New conversation · earlier answers are not context'}));
    needsDivider = false;
    const question = h('h1', {id: `question-${number}`, class: 'question', text: query});
    const answer = h('article', {class: 'answer', 'aria-labelledby': `question-${number}`}, answerHeading(number),
      h('div', {class: 'loading', role: 'status'}, h('div', {class: 'loading-line'}, h('span', {class: 'orb'}), h('p', {text: loading}), elapsedCounter()),
        h('div', {class: 'skeleton'}, h('i'), h('i'), h('i'), h('i'))));
    const turn = h('section', {class: 'turn', id: `turn-${number}`, 'aria-labelledby': question.id, hidden: true},
      h('header', {class: 'turn-head'}, h('p', {class: 'question-label', text: questionLabel, hidden: !/Multi-Agent|clarification/i.test(questionLabel)}), question),
      answer, h('div', {class: 'followup-slot'}, h('h2', {class: 'followup-title', text: 'Ask a follow-up'})));
    $('#session-section').hidden = false;
    const entry = h('li', null, h('button', {type: 'button', class: 'rail-link', title: query, onclick: () => activateTurn(turn)},
      h('span', {class: 'rail-link-text', text: query})));
    turn.sessionEntry = entry;
    $('#session-list').prepend(entry);
    return {turn, answer};
  }
  function activateTurn(turn, {scroll = true} = {}) {
    if (!turn) return;
    if (turn !== activeTurn) nav.bump();
    activeTurn = turn;
    queueMicrotask(renderSidebar);
    thread.querySelectorAll(':scope > .turn').forEach(node => { node.hidden = node !== turn; });
    document.querySelectorAll('#session-list .rail-link').forEach(link => link.removeAttribute('aria-current'));
    $('.rail-link', turn.sessionEntry || document.createElement('i'))?.setAttribute('aria-current', 'true');
    $('#thread-title').textContent = $('.question', turn)?.textContent || '';
    setView('thread');
    placeDock();
    buildContents(turn);
    const turnDemo = turn.demoState;
    if (turnDemo) activeDemo = turnDemo;
    syncTopbar();
    if (scroll) scroller.scrollTop = 0;
  }
  function showTurn(turn) {
    thread.append(turn);
    activateTurn(turn);
  }
  function markAnswerReady(answer) {
    latestAnswer = $('.answer-kicker', answer);
    if (answer.closest('.turn') === activeTurn) buildContents(activeTurn);
  }
  function syncJump() { jumpLatest.hidden = true; } // One brief is shown at a time; nothing to jump to.
  jumpLatest.addEventListener('click', () => latestAnswer?.focus());

  const chip = (text, tone, iconName) => h('span', {class: `chip ${tone || ''}`}, iconName && icon(iconName), h('span', {text}));
  function bullets(items, className = 'bullets') { return h('ul', {class: className}, items.map(item => h('li', {math: item}))); }
  function note(text, tone = '', iconName) { return h('p', {class: `note ${tone}`}, iconName && icon(iconName), h('span', {text})); }
  // Small TeX fragments inside table text (\rho, \pm, \bm{\checkmark}) render with the bundled KaTeX;
  // the surrounding text is untouched and the raw text stays available to assistive technology.
  // A command with its braced arguments plus any sub/superscripts that follow (S_{harm}, D_{2k}^{cup}).
  const TEX = /\\[a-zA-Z]+(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})*(?:\s*[_^](?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|[A-Za-z0-9]))*/g;
  function texText(node, text) {
    node.textContent = '';
    if (!text || !window.katex || !text.includes('\\')) { node.textContent = text; return node; }
    // KaTeX's default output adds a hidden MathML copy whose annotation repeats the raw TeX, and the
    // old screen-reader copy repeated it again, so copy, find and assistive tech got "ρ\rhoρ".
    // Render visual HTML only and name each formula with its readable form (ρ, Δ, ±).
    let last = 0;
    for (const match of text.matchAll(TEX)) {
      if (match.index > last) node.append(text.slice(last, match.index));
      const span = document.createElement('span');
      try {
        katex.render(match[0], span, {throwOnError: true, displayMode: false, output: 'html'});
        span.setAttribute('role', 'img');
        span.setAttribute('aria-label', ChartSelect.texPlain(match[0]));
        node.append(span);
      } catch { span.textContent = ChartSelect.texPlain(match[0]); node.append(span); }
      last = match.index + match[0].length;
    }
    if (last < text.length) node.append(text.slice(last));
    return node;
  }

  /* ---------- Contents rail with section highlight ---------- */
  let spyFrame = 0;
  function buildContents(turn) {
    const nav = $('#contents');
    const blocks = turn ? [...turn.querySelectorAll('.block[data-nav]:not([hidden])')] : []; // hidden blocks (e.g. no eligible key chart) get no link
    nav.replaceChildren();
    if (!blocks.length) return;
    nav.append(h('h2', {class: 'rail-title', text: 'In this brief'}));
    const list = h('ol', {class: 'contents-list'});
    let lastGroup = null;
    for (const block of blocks) {
      // One divider between levels: the answer, then Explore the evidence, then Technical details.
      const level = block.closest('.layer-technical') ? 'technical' : block.closest('.layer-explore') ? 'explore' : 'answer';
      if (lastGroup !== null && level !== lastGroup) list.append(h('li', {class: 'contents-group', 'aria-hidden': 'true'}));
      lastGroup = level;
      const link = h('button', {type: 'button', class: 'contents-link', onclick: () => {
        for (let node = block; node; node = node.parentElement) if (node.tagName === 'DETAILS') node.open = true;
        block.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
        $('.block-title', block)?.focus({preventScroll: true});
        markContents(link);
      }}, h('span', {text: block.dataset.nav}), block.dataset.count && h('span', {class: 'contents-count', text: block.dataset.count}));
      link.target = block;
      list.append(h('li', null, link));
    }
    nav.append(list);
    spyContents();
  }
  function markContents(active) {
    document.querySelectorAll('.contents-link').forEach(link => link.toggleAttribute('aria-current', link === active));
    if (active) active.setAttribute('aria-current', 'true');
  }
  function spyContents() {
    spyFrame = 0;
    const links = [...document.querySelectorAll('.contents-link')];
    if (!links.length || currentView !== 'thread') return;
    const line = scroller.getBoundingClientRect().top + 120;
    let current = links[0];
    for (const link of links) if (link.target.getBoundingClientRect().top <= line) current = link;
    if (scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 4) {
      const lastVisible = links.filter(link => link.target.getBoundingClientRect().top < scroller.getBoundingClientRect().bottom).at(-1);
      if (lastVisible) current = lastVisible;
    }
    markContents(current);
  }
  scroller.addEventListener('scroll', () => { if (!spyFrame) spyFrame = requestAnimationFrame(spyContents); }, {passive: true});

  /* ---------- Evidence tables and charts (EvidenceModel; see design/EVIDENCE-VISUALIZATION-SPEC.md) ---------- */
  const EM = window.EvidenceModel;
  // Successful tables are cached for 10 minutes; failures (a temporary 503, a timeout) are never
  // cached, so reopening the answer asks again. In-flight requests are shared separately.
  const fullTableCache = AsyncGuards.createResultCache({ttlMs: 10 * 60 * 1000});
  function fetchFullTable(table, indexSha) {
    const chunk = table.rows[0]?.chunk_id;
    if (!chunk || !indexSha) return Promise.resolve({ok: false, reason: 'The answer does not record which index it used.'});
    return fullTableCache.get(`${indexSha}|${table.key}`, async () => {
      try {
        const response = await fetch(`/api/evidence-table?${new URLSearchParams({chunk_id: chunk, index: indexSha})}`, {signal: AbortSignal.timeout(15000)});
        const body = await response.json().catch(() => ({}));
        if (response.ok) return {ok: true, full: body};
        const reasons = {404: 'This backend does not provide full tables.', 409: 'The loaded index differs from the one this answer used.',
          422: 'The index cannot rebuild this table reliably.'};
        return {ok: false, reason: (response.status === 422 && body.error) ? `The index cannot rebuild this table reliably: ${body.error}` : reasons[response.status] || 'The full table could not be loaded.'};
      } catch { return {ok: false, reason: 'The full table could not be loaded (no response).', retry: true}; }
    });
  }
  function tableTitle(table) {
    const match = /^(Table\s*[A-Za-z]?\d+[a-z]?)\s*:?/.exec(table.caption || '');
    const name = match ? match[1].replace(/\s+/g, ' ') : `Table ${table.table_id}`;
    return window.MOCK_API === true ? `Mock ${name.toLowerCase()}` : name;
  }
  function captionBody(table) { return (table.caption || '').replace(/^Table\s*[A-Za-z]?\d+[a-z]?\s*:\s*/, ''); }
  function statusRow(iconName, tone, text) {
    return h('li', {class: `ev-flag ${tone}`}, icon(iconName), h('span', {text}));
  }
  function tsv(table) {
    const clean = text => String(text).replace(/[\t\n\r]+/g, ' ');
    const lines = [table.headers.map(header => clean(header.text)).join('\t'),
      ...table.rows.map(row => row.cells.map(cell => clean(cell.text)).join('\t'))];
    lines.push('', `Source: ${table.paper_title} (${table.arxiv_id}), ${table.table_id}`, `Caption: ${clean(table.caption)}`,
      `Link: ${table.html_url || 'not supplied'}`,
      table.completeness === 'complete_from_index' ? `All ${table.rows.length} rows from the indexed table.` : `${table.rows.length} rows retrieved for this answer; the paper's table may contain more rows.`,
      table.headerStatus.label, 'Values exactly as extracted from the paper HTML; nothing computed.');
    return lines.join('\n');
  }
  function openRowSource(ctx, table, row, cell, trigger) {
    const {demo, number} = ctx;
    if (row.evidenceIndex != null) {
      showEvidence(demo, number, row.evidenceIndex, trigger, null, cell?.source_id);
      return;
    }
    // A row loaded from the index but not retrieved for this answer: show it with its table context.
    closePreview();
    inspectorChrome('Table row', `${tableTitle(table)} · ${ctx.preview ? 'from the research index' : 'loaded from the index'}`,
      ctx.preview ? 'This row comes from the verified table in the research index. The research explanation has not cited it yet.'
        : 'This row was loaded from the research index to complete the table. It is not part of the evidence this answer retrieved or cited.');
    activeDemo = {demo, number, selected: 0, claim: null};
    const view = h('article', {class: 'passage'},
      h('h3', {text: table.paper_title}),
      h('p', {class: 'meta', math: table.caption}),
      rowGrid(table, row, cell?.source_id),
      h('dl', {class: 'source-metadata'}, h('dt', {text: 'Row'}), h('dd', {text: `${row.table_row} of ${table.rows.length}`}),
        h('dt', {text: 'Cell source ID'}), h('dd', {class: 'mono', text: cell?.source_id || 'Not supplied'}),
        h('dt', {text: 'Passage ID'}), h('dd', {class: 'mono', text: row.chunk_id})),
      table.html_url && h('a', {class: 'source-link', href: table.html_url, target: '_blank', rel: 'noopener noreferrer', text: "Open the paper's table"}),
      h('p', {class: 'meta', text: table.headerStatus.label}));
    inspectorBody.replaceChildren(view);
    inspectorBody.scrollTop = 0;
    setInspector(true, trigger);
    inspectorHeading.focus({preventScroll: true});
  }
  function rowGrid(table, row, highlightId) {
    const grid = h('table', {class: 'row-grid'},
      h('thead', null, h('tr', null, table.headers.map(header => texText(h('th', {scope: 'col'}), header.text)))),
      h('tbody', null, h('tr', null, row.cells.map(cell => {
        const td = h('td', {class: `${cell.parsed ? 'num' : ''}${cell.source_id && cell.source_id === highlightId ? ' hit' : ''}`});
        if (cell.text) texText(td, cell.text); else td.append(h('span', {class: 'empty-cell', text: 'empty in source'}));
        return td;
      }))));
    return h('div', {class: 'row-grid-wrap', tabIndex: 0, role: 'region', 'aria-label': `Row ${row.table_row}: ${row.row_label}`}, grid);
  }

  function renderEvidenceTable(table, ctx) {
    const figure = h('figure', {class: `ev-figure${ctx.compact ? ' compact' : ''}`, id: `a${ctx.number}-${ctx.preview ? 'preview-' : ''}${ctx.compact ? 'key-' : ''}tbl-${table.table_id.replace(/[^A-Za-z0-9]/g, '-')}`});
    figure.dataset.tableKey = table.key;
    let mode = 'table', sort = {column: null, dir: 0}, plan = EM.chartPlan(table), fullNote = null;
    // Which views this table's shape supports, and the default for this question (chart-select.js).
    let analysis = null, views = [], defaultView = null, chartKind = null, countIssue = null;
    function refreshViews() {
      analysis = ChartSelect.analyze(table);
      views = ChartSelect.viewsFor(table, analysis);
      defaultView = ChartSelect.chooseDefault(views, ctx.question ? ctx.question() : '');
      if (!views.some(view => view.eligible && view.kind === chartKind)) chartKind = null;
      countIssue = ctx.preview ? null : ChartSelect.countCheck(ctx.demo.result, table);
      if (countIssue && ctx.onReviewIssue) ctx.onReviewIssue(table, countIssue);
    }
    const anyChart = () => views.some(view => view.eligible);
    const tiles = h('div', {class: 'kpi-strip', role: 'group', 'aria-label': `Cited figures from ${tableTitle(table)}`});
    const view = h('div', {class: 'ev-view'});
    const flags = h('ul', {class: 'ev-flags'});
    // Two choices only: Table or Chart (the recommended view). Other eligible charts sit behind one
    // "Change chart" menu instead of competing buttons.
    const tabs = h('div', {class: 'seg ev-seg view-seg', role: 'tablist', 'aria-label': `${tableTitle(table)} view`});
    let viewButtons = [];
    const menuList = h('div', {class: 'chart-menu-list', role: 'group', 'aria-label': 'Chart types'});
    const menu = h('details', {class: 'chart-menu'}, h('summary', {class: 'quiet-btn'}, icon('chart'), h('span', {text: 'Change chart'})), menuList);
    menu.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.open) { event.preventDefault(); menu.open = false; menu.querySelector('summary').focus(); }
    });
    document.addEventListener('click', event => { if (menu.open && !menu.contains(event.target)) menu.open = false; });
    const copy = h('button', {type: 'button', class: 'quiet-btn', onclick: async () => {
      try { await navigator.clipboard.writeText(tsv(table)); announce(`${tableTitle(table)} copied with its source line.`); }
      catch { announce('Copy is not available in this browser. Use Export instead.'); }
    }}, icon('copy'), h('span', {text: 'Copy'}));
    const open = table.html_url ? h('a', {class: 'quiet-btn', href: table.html_url, target: '_blank', rel: 'noopener noreferrer',
      'aria-label': `Open ${tableTitle(table)} in the paper, opens in a new tab`}, icon('external'), h('span', {text: 'Open in paper'})) : null;
    const chartReason = h('div', {class: 'ev-chart-reason'});

    const detailFlags = h('ul', {class: 'ev-flags'});
    function renderFlags() {
      detailFlags.replaceChildren();
      const forWhat = ctx.preview ? 'for this question' : 'for this answer';
      flags.replaceChildren(
        table.completeness === 'complete_from_index'
          ? statusRow('check', 'ok', `Full table shown (${table.rows.length} rows). ${table.retrievedCount} ${table.retrievedCount === 1 ? 'row was' : 'rows were'} used ${forWhat}.`)
          : statusRow('alert', 'warn', `Only the ${table.retrievedCount} row${table.retrievedCount === 1 ? '' : 's'} used ${forWhat} ${table.retrievedCount === 1 ? 'is' : 'are'} shown; the paper's table may have more.`),
        statusRow(table.headerStatus.verified ? 'check' : 'alert', table.headerStatus.verified ? 'ok' : 'warn',
          table.headerStatus.verified ? 'Column headings checked by a person.' : 'Column headings were read automatically; check them against the paper.'),
        table.fidelity === 'round_trip_ok'
          ? statusRow('check', 'ok', 'All values match the paper exactly.')
          : statusRow('alert', 'bad', 'The values could not be matched to the paper, so only the source text is shown.'));
      // Routine confirmations move into Table details; warnings that change interpretation stay inline.
      for (const item of [...flags.children]) if (item.classList.contains('ok')) { if (ctx.compact) item.remove(); else detailFlags.append(item); }
      if (fullNote) flags.append(statusRow('info', '', fullNote));
      if (countIssue && !ctx.compact) flags.append(statusRow('alert', 'warn', `Count check: ${countIssue.text}`));
      if (table.notes.length) detailFlags.append(h('li', {class: 'ev-flag'}, icon('info'), h('span', {text: `Source notes: ${table.notes.map(n => n.text).join(' ')}`})));
    }
    function setMode(next) {
      if (next !== 'table' && !anyChart()) return;
      if (next !== 'table' && next !== 'chart') chartKind = next;
      mode = next === 'table' ? 'table' : 'chart';
      const current = mode === 'table' ? 'table' : (chartKind || defaultView.kind);
      const chartName = views.find(v => v.kind === (chartKind || defaultView.kind))?.label || 'Chart';
      viewButtons.forEach(button => {
        button.setAttribute('aria-selected', String(button.dataset.view === (mode === 'table' ? 'table' : 'chart')));
        if (button.dataset.view === 'chart') button.querySelector('.tab-detail').textContent = chartName;
      });
      menuList.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(mode === 'chart' && button.dataset.view === current)));
      renderAbout(current);
      const swap = () => {
        view.querySelector('.ev-chart')?.dispose?.(); // stop the old chart's resize observer
        view.replaceChildren(mode === 'chart' ? viewBody(table, plan, ctx, analysis, views.find(v => v.kind === current)) : tableView());
      };
      if (reduced.matches || !view.firstChild) swap();
      else { view.classList.remove('swap'); swap(); void view.offsetWidth; view.classList.add('swap'); }
    }
    function syncChartTab() {
      const eligible = views.filter(view => view.eligible);
      const tableButton = h('button', {type: 'button', role: 'tab', class: 'seg-btn', onclick: () => setMode('table')}, icon('table'), h('span', {text: 'Table'}));
      tableButton.dataset.view = 'table';
      const chartButton = h('button', {type: 'button', role: 'tab', class: 'seg-btn', disabled: !eligible.length,
        title: eligible.length ? null : defaultView.why, onclick: () => setMode('chart')},
        icon('chart'), h('span', {text: 'Chart'}), h('span', {class: 'tab-detail'}));
      chartButton.dataset.view = 'chart';
      viewButtons = ctx.compact ? [] : [tableButton, chartButton];
      tabs.replaceChildren(...viewButtons);
      tabs.hidden = Boolean(ctx.compact);
      menuList.replaceChildren(...eligible.map(view => {
        const button = h('button', {type: 'button', class: 'chart-menu-item', onclick: () => { menu.open = false; setMode(view.kind); menu.querySelector('summary').focus(); }},
          h('span', {class: 'chart-menu-name', text: view.label}), view.kind === defaultView.kind ? h('span', {class: 'seg-note', text: 'Suggested'}) : null);
        button.dataset.view = view.kind;
        return button;
      }));
      menu.hidden = eligible.length < 2;
    }
    /* What the reader needs to know about the current view: a refusal stays visible (it is the
       finding); the rationale, other views and uncharted columns sit behind one disclosure. */
    function renderAbout(current) {
      const eligible = views.filter(view => view.eligible);
      chartReason.replaceChildren();
      if (!eligible.length) {
        chartReason.append(texText(h('p', {class: 'off'}), `Shown as a table: ${defaultView.why}`));
        return;
      }
      const selected = views.find(view => view.kind === current);
      const unavailable = views.filter(view => !view.eligible);
      const details = h('details', {class: 'fold view-about'},
        h('summary', {text: current === 'table' ? `Suggested chart: ${eligible.find(v => v.kind === defaultView.kind).label}` : 'About this chart'}));
      details.append(texText(h('p'), current === 'table' || current === defaultView.kind ? defaultView.why : selected.reason));
      if (plan.excluded.length) details.append(texText(h('p'), `Columns not charted: ${plan.excluded.map(e => `${e.header} (${e.reason})`).join('; ')}.`));
      void unavailable; // charts that are not offered are simply not listed
      chartReason.append(details);
    }
    function renderTiles() {
      const {tiles: list, more} = ChartSelect.kpiTiles(table);
      tiles.replaceChildren();
      tiles.hidden = !list.length;
      if (!list.length) return;
      const valueButton = (row, cell, extra) => {
        const button = h('button', {type: 'button', class: 'kpi-value', 'aria-label': `${row.row_label}, ${extra}: ${cell.text}. Open source.`,
          onclick: () => openRowSource(ctx, table, row, cell, button)});
        texText(button, cell.text);
        return button;
      };
      for (const tile of list) {
        const head = h('p', {class: 'kpi-label'}, texText(h('span', {class: 'kpi-row'}), tile.label), h('span', {class: 'kpi-sep', 'aria-hidden': 'true', text: ' · '}), texText(h('span'), tile.header));
        const values = tile.from
          ? h('p', {class: 'kpi-values'}, valueButton(tile.from.row, tile.from.cell, `${tile.conditions[0]}, ${ChartSelect.texPlain(tile.header)}`),
            h('span', {class: 'kpi-arrow', 'aria-hidden': 'true', text: '→'}), valueButton(tile.to.row, tile.to.cell, `${tile.conditions[1]}, ${ChartSelect.texPlain(tile.header)}`))
          : h('p', {class: 'kpi-values'}, valueButton(tile.value.row, tile.value.cell, ChartSelect.texPlain(tile.header)));
        const foot = h('p', {class: 'kpi-foot'}, h('span', {text: tile.from ? `${tile.conditions[0]} → ${tile.conditions[1]} · as printed` : 'As printed'}),
          h('span', {class: 'cites'}, tile.citedBy.map(n => h('span', {class: 'cite-num', text: String(n)}))));
        tiles.append(h('div', {class: 'kpi'}, head, values, foot));
      }
      if (more) tiles.append(h('p', {class: 'kpi-more', text: `${more} more cited row${more === 1 ? '' : 's'} in the table.`}));
    }
    // Exact decimal ordering; mixed percent/plain or text columns sort by their text (evidence.js).
    const sortedRows = () => EM.sortRows(table.rows, sort.column, sort.dir);
    function tableView() {
      if (table.fidelity !== 'round_trip_ok') {
        return h('div', {class: 'ev-fallback'}, table.sourceTexts.map(text => h('pre', {class: 'source-text', text})));
      }
      const head = h('tr', null, h('th', {scope: 'col', class: 'ev-mark-col'}, h('span', {class: 'sr-only', text: 'Use in this answer'})),
        table.headers.map((header, column) => {
          const state = sort.column === column ? sort.dir : 0;
          const numeric = column > 0 && EM.columnSortKind(table.rows, column) === 'number';
          const th = h('th', {scope: 'col', class: column === 0 ? 'ev-label-col' : numeric ? 'num' : '', 'aria-sort': state > 0 ? 'ascending' : state < 0 ? 'descending' : 'none'});
          const button = h('button', {type: 'button', class: 'sort-btn', title: 'Sort by this column (source order on the third click)', onclick: () => {
            sort = sort.column !== column ? {column, dir: 1} : sort.dir === 1 ? {column, dir: -1} : {column: null, dir: 0};
            view.replaceChildren(tableView());
            $(`th:nth-child(${column + 2}) .sort-btn`, view)?.focus();
          }}, texText(h('span'), header.text), h('span', {class: 'sort-mark', 'aria-hidden': 'true', text: state > 0 ? '↑' : state < 0 ? '↓' : ''}));
          th.append(button);
          return th;
        }));
      const body = h('tbody');
      for (const row of sortedRows()) {
        const mark = row.citedBy.length
          ? h('span', {class: 'row-mark cited', title: `Cited as [${row.citedBy.join('], [')}]`}, row.citedBy.map(n => h('span', {class: 'cite-num', text: String(n)})))
          : row.retrieved ? h('span', {class: 'row-mark retrieved', title: 'Retrieved for this answer, not cited'}, h('span', {class: 'dot'}), h('span', {class: 'sr-only', text: 'Retrieved, not cited'}))
            : h('span', {class: 'sr-only', text: 'Loaded from the index'});
        const tr = h('tr', {class: `${row.citedBy.length ? 'is-cited' : row.retrieved ? 'is-retrieved' : ''}`}, h('td', {class: 'ev-mark-col'}, mark));
        row.cells.forEach((cell, column) => {
          const header = table.headers[column]?.text || `Column ${column + 1}`;
          const button = h('button', {type: 'button', class: `cell-btn${cell.parsed ? ' num' : ''}`,
            'aria-label': `${header}, ${row.row_label}: ${cell.text || 'empty in source'}. Open source.`,
            onclick: () => openRowSource(ctx, table, row, cell, button)});
          if (cell.text) texText(button, cell.text); else button.append(h('span', {class: 'empty-cell', text: 'empty'}));
          if (cell.source_id) button.dataset.sourceId = cell.source_id;
          tr.append(h(column === 0 ? 'th' : 'td', {scope: column === 0 ? 'row' : null, class: `${column === 0 ? 'ev-label-col' : ''}${cell.parsed ? ' num' : ''}`}, button));
        });
        body.append(tr);
      }
      const legend = h('p', {class: 'ev-legend'},
        h('span', null, h('span', {class: 'cite-num', text: 'n'}), ' cited in this answer'),
        h('span', null, h('span', {class: 'dot'}), ' retrieved, not cited'),
        table.completeness === 'complete_from_index' ? h('span', {text: 'unmarked: loaded from the index to complete the table'}) : null,
        h('span', {text: 'Select any value to open its source.'}));
      void legend; // the row-mark legend lives in Table details
      return h('div', null,
        h('div', {class: 'table-scroll', tabIndex: 0, role: 'region', 'aria-label': `${tableTitle(table)}, scrollable`},
          h('table', {class: 'ev-table'}, h('caption', {class: 'sr-only', text: `${tableTitle(table)}: ${captionBody(table)}`}), h('thead', null, head), body)));
    }

    const fullLink = ctx.compact ? h('button', {type: 'button', class: 'quiet-btn', onclick: () => ctx.showFullTable && ctx.showFullTable(table)},
      icon('table'), h('span', {text: 'See the full table'})) : null;
    const toolbar = ctx.compact ? h('div', {class: 'ev-toolbar'}, menu, h('div', {class: 'ev-actions'}, fullLink, open))
      : h('div', {class: 'ev-toolbar'}, tabs, menu, h('div', {class: 'ev-actions'}, open));
    const tableDetails = ctx.compact ? null : h('details', {class: 'fold table-details'}, h('summary', {text: 'Table details'}),
      texText(h('p', {class: 'ev-text'}), captionBody(table)), detailFlags,
      h('p', {class: 'ev-legend'}, h('span', null, h('span', {class: 'cite-num', text: 'n'}), ' cited in this answer'),
        h('span', null, h('span', {class: 'dot'}), ' retrieved, not cited'),
        h('span', {text: 'unmarked: loaded from the index to complete the table'})),
      h('div', {class: 'row'}, copy));
    figure.append(
      ctx.compact
        ? h('figcaption', {class: 'ev-caption key-source'}, texText(h('p', {class: 'fig-title'}), captionBody(table) || tableTitle(table)),
          h('p', {class: 'fig-source'}, h('span', {text: `${tableTitle(table)}, `}), h('cite', {text: table.paper_title}),
            h('span', {text: '. Values as printed in the paper; select a mark to see its source.'})))
        : h('figcaption', {class: 'ev-caption'},
          h('p', {class: 'ev-title'}, h('span', {class: 'ev-name', text: tableTitle(table)}), h('span', {class: 'ev-paper', text: table.paper_title}))),
      // KPI tiles are not shown: a number lifted out of its table loses its row, column and conditions.
      ...[ctx.compact ? null : flags, toolbar, ctx.compact ? null : chartReason, view, ctx.compact ? flags : tableDetails].filter(Boolean));
    // The key chart appears only once a chart can be drawn from the complete table.
    function syncCompact() {
      if (!ctx.compact) return;
      const waiting = table.completeness !== 'complete_from_index' && table.fidelity === 'round_trip_ok' && fullNote && /Checking/.test(fullNote);
      figure.hidden = !anyChart() && !waiting;
      figure.classList.toggle('waiting', Boolean(waiting) && !anyChart());
      if (ctx.onCompact) ctx.onCompact(!figure.hidden);
    }
    // Explicit chart questions open in chart mode when the table is complete, chartable and
    // cited by the accepted answer (or is a verified preview); everything else opens as a table.
    const wantsChart = () => Boolean(ctx.autoChart && plan.eligible && ctx.autoChart(table, plan));
    refreshViews(); renderFlags(); renderTiles(); syncChartTab();
    setMode(wantsChart() || ((ctx.openChart || ctx.compact) && anyChart()) ? 'chart' : 'table');

    // Complete the table from the read-only index endpoint when the backend offers it.
    const indexSha = ctx.demo.result?.provenance?.index?.indexed_records_sha256;
    if (table.completeness !== 'complete_from_index' && table.fidelity === 'round_trip_ok') {
      fullNote = 'Checking the research index for the complete table…';
      renderFlags();
      fetchFullTable(table, indexSha).then(outcome => {
        if (!figure.isConnected && !document.body.contains(figure)) return;
        if (outcome.ok) {
          const merged = EM.mergeComplete(table, outcome.full, indexSha);
          if (merged.ok) {
            table = merged.table; fullNote = null; plan = EM.chartPlan(table);
          } else fullNote = `Full table not used: ${merged.reason}`;
        } else fullNote = `Full table not loaded: ${outcome.reason}`;
        refreshViews(); renderFlags(); renderTiles(); syncChartTab(); setMode((mode === 'chart' || wantsChart() || ctx.compact) && anyChart() ? 'chart' : 'table');
        syncCompact();
      });
    }
    syncCompact();
    if (ctx.compact && figure.classList.contains('waiting')) view.replaceChildren(h('p', {class: 'muted key-wait', text: 'Loading the complete table from the research library to draw the chart…'}));
    return figure;
  }

  /* Dot plots drawn as inline SVG: one shared row axis, one independent scale per column. */
  const SVGNS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs, ...children) {
    const node = document.createElementNS(SVGNS, tag);
    for (const [key, value] of Object.entries(attrs || {})) if (value != null) node.setAttribute(key, value);
    for (const child of children.flat()) if (child != null) node.append(child);
    return node;
  }
  /* Chart view (chart-first design, 2026-11-17).
     - One metric at a time, chosen with a metric selector; "All metrics" keeps the original
       small-multiple dot plots.
     - A metric is drawn as horizontal bars from a shared zero ONLY when the table states a
       percentage unit for it (EvidenceModel.panelUnit). Otherwise it stays a dot or dumbbell plot,
       and the page says why.
     - Title and unit come from the table's own words. The takeaway is the answer's own accepted,
       cited finding about this table, or nothing.
     - Every bar or dot opens its exact source cell; completeness and header warnings stay above. */
  function chartView(table, plan, ctx, initial) {
    const wrap = h('div', {class: 'ev-chart'});
    const paired = plan.form === 'paired_dot';
    const metrics = plan.panels;
    const choices = ctx.chartChoice || (ctx.chartChoice = new Map());
    const preferred = metrics.findIndex(panel => panel.unit && panel.unit.zero);
    let choice = initial !== undefined ? initial
      : choices.has(table.key) ? choices.get(table.key) : preferred >= 0 ? preferred : (metrics.length > 1 ? 'all' : 0);
    const title = h('h4', {class: 'chart-title'});
    const unitLine = h('p', {class: 'chart-unit'});
    const takeawayData = ctx.takeaway ? ctx.takeaway(table) : null;
    const takeaway = takeawayData ? h('p', {class: 'chart-takeaway'},
      h('span', {class: 'term', text: 'From the answer'}), h('span', {math: takeawayData.text}),
      takeawayData.citations.length ? h('span', {class: 'cites'}, takeawayData.citations.map(n => h('span', {class: 'cite-num', text: String(n)}))) : null) : null;
    const selector = h('div', {class: 'seg metric-seg', role: 'radiogroup', 'aria-label': 'Metric shown in the chart'});
    const options = [...metrics.map((panel, index) => ({value: index, label: panel.header})),
      ...(metrics.length > 1 ? [{value: 'all', label: 'All metrics'}] : [])];
    const buttons = options.map(option => {
      const button = h('button', {type: 'button', role: 'radio', class: 'seg-btn', onclick: () => { picked = true; show(option.value, true); }});
      texText(button, option.label);
      button.dataset.metric = String(option.value);
      return button;
    });
    selector.append(...buttons);
    selector.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp'].includes(event.key)) return;
      event.preventDefault();
      const index = options.findIndex(option => option.value === choice);
      const step = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : options.length - 1;
      picked = true; show(options[(index + step) % options.length].value, true);
    });
    const legend = paired ? h('p', {class: 'chart-legend'},
      h('span', {class: 'key'}, h('span', {class: 'swatch a', 'aria-hidden': 'true'}), h('span', {text: plan.category.values[0]})),
      h('span', {class: 'key'}, h('span', {class: 'swatch b', 'aria-hidden': 'true'}), h('span', {text: plan.category.values[1]})),
      h('span', {class: 'legend-note', text: `Labels as written in the “${plan.category.header}” column.`})) : null;
    const frame = h('div', {class: 'chart-frame'});
    const hint = scrollHint();
    const why = h('p', {class: 'chart-why'});
    const foot = h('p', {class: 'chart-foot'});
    const glossHost = h('div', {class: 'gloss-host'});
    wrap.append(...[h('div', {class: 'chart-head'}, title, unitLine, glossHost, takeaway, metrics.length > 1 || metrics[0]?.unit?.zero ? chartOptions(selector) : null), legend, hint, frame, why, foot].filter(Boolean)); // append(null) would print "null"
    let chart = null, picked = false;
    const draw = options => {
      if (!chart) return;
      chart.update(Math.round(frame.clientWidth || wrap.clientWidth || 0), options);
      hint.hidden = !frame.classList.contains('scrolls');
    };
    function show(next, focusSelector = false) {
      choice = next;
      choices.set(table.key, next);
      const panel = next === 'all' ? null : metrics[next];
      const bars = Boolean(panel && panel.unit && panel.unit.zero);
      wrap.classList.toggle('is-bars', bars);
      texText(title, ChartSelect.businessQuestion(paired ? 'paired' : bars ? 'bars' : 'dots', table,
        {metric: panel ? panel.header : metrics.length > 1 ? 'each measure' : metrics[0].header, from: plan.category?.values[0], to: plan.category?.values[1]}));
      texText(unitLine, `${EM.chartTitle(table, plan, panel)}. ${panel
        ? (panel.unit && panel.unit.zero ? `Unit: ${panel.unit.label}, as stated in the table.` : 'The paper gives no unit for these values.')
        : 'Each measure has its own scale.'}`);
      glossHost.replaceChildren(glossLine([...(panel ? [panel.header] : metrics.map(m => m.header))]) || '');
      why.textContent = panel && !bars ? 'No unit with a true zero is stated, so values are compared by position rather than bar length.' : '';
      why.hidden = !why.textContent;
      foot.textContent = bars
        ? 'Bars start at zero on one shared scale. Values exactly as written; nothing computed or ranked.'
        : 'Scale: lowest to highest printed value, labelled at both ends. Values exactly as written; nothing computed or ranked.'
          + (plan.truncatedPanels ? ` ${plan.truncatedPanels} more chartable column(s) are in the table view.` : '');
      buttons.forEach(button => {
        const selected = button.dataset.metric === String(next);
        button.setAttribute('aria-checked', String(selected));
        button.setAttribute('aria-selected', String(selected));
        button.tabIndex = selected ? 0 : -1;
      });
      chart = ChartSvg.mount({document, frame, table, plan, title: tableTitle(table),
        view: panel ? {kind: bars ? 'bars' : 'dots', panel} : {kind: 'overview'},
        onOpen: (row, cell, trigger) => openRowSource(ctx, table, row, cell, trigger)});
      if (wrap.isConnected) draw({force: true});
      if (focusSelector) buttons.find(button => button.dataset.metric === String(next))?.focus();
    }
    show(choice);
    // "All metrics" side by side is the default only when it fits; on a narrower frame the chart
    // opens on the first metric instead of scrolling (the reader can still choose "All metrics").
    requestAnimationFrame(() => {
      if (!wrap.isConnected) return;
      draw({force: true});
      if (!picked && choice === 'all' && frame.classList.contains('scrolls')) show(0);
    });
    // Redraw only while attached; a detached chart stops observing (audit L2).
    const observer = new ResizeObserver(() => { if (wrap.isConnected) draw(); else observer.disconnect(); });
    observer.observe(frame);
    wrap.dispose = () => observer.disconnect();
    wrap.redraw = () => draw({force: true});
    wrap.update = () => draw();
    wrap.showMetric = value => show(value);
    return wrap;
  }

  /* ---------- Chart views chosen by the table's shape (chart-select.js, 2026-11-22) ---------- */
  /* A radio-style segmented control with arrow-key movement; `options` = [{value, label, note}]. */
  // Advanced chart controls stay folded: the recommended view is shown first.
  function chartOptions(control) {
    return h('details', {class: 'chart-options'}, h('summary', null, icon('sliders'), h('span', {text: 'Chart options'})), control);
  }
  function choiceSeg(label, options, value, onChange, className = 'seg metric-seg') {
    const group = h('div', {class: className, role: 'radiogroup', 'aria-label': label});
    const buttons = options.map(option => {
      const button = h('button', {type: 'button', role: 'radio', class: 'seg-btn', onclick: () => select(option.value, true)});
      texText(button, option.label);
      if (option.note) button.append(h('span', {class: 'seg-note', text: option.note}));
      button.dataset.value = String(option.value);
      return button;
    });
    function select(next, focus = false) {
      value = next;
      buttons.forEach(button => {
        const on = button.dataset.value === String(next);
        button.setAttribute('aria-checked', String(on));
        button.tabIndex = on ? 0 : -1;
        if (on && focus) button.focus();
      });
      onChange(next);
    }
    group.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp'].includes(event.key)) return;
      event.preventDefault();
      const index = options.findIndex(option => String(option.value) === String(value));
      const step = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : options.length - 1;
      select(options[(index + step) % options.length].value, true);
    });
    group.append(...buttons);
    group.select = select;
    buttons.forEach(button => {
      const on = button.dataset.value === String(value);
      button.setAttribute('aria-checked', String(on));
      button.tabIndex = on ? 0 : -1;
    });
    return group;
  }

  /* A one-line plain gloss for abbreviations in the labels a chart shows (general meanings only). */
  function glossLine(labels) {
    const terms = ChartSelect.glossaryFor(labels);
    return terms.length ? h('p', {class: 'chart-gloss'}, h('span', {class: 'gloss-label', text: 'In plain terms: '}),
      ...terms.flatMap((t, i) => [i ? h('span', {text: ' · '}) : null, h('strong', {text: t.term}), h('span', {text: `: ${t.meaning}`})])) : null;
  }
  // Shown only while a chart is wider than its frame: the chart keeps its readable size and scrolls.
  function scrollHint() {
    return h('p', {class: 'scroll-hint', hidden: true}, icon('arrow'), h('span', {text: 'Wider than the screen: scroll the chart sideways to see every value.'}));
  }
  function viewBody(table, plan, ctx, analysis, view) {
    const title = tableTitle(table);
    const open = (row, cell, trigger) => openRowSource(ctx, table, row, cell, trigger);
    if (view.kind === 'paired' || view.kind === 'dots') return chartView(table, plan, ctx, plan.panels.length > 1 ? 'all' : 0);
    if (view.kind === 'bars') return chartView(table, plan, ctx, plan.panels.findIndex(panel => panel.unit && panel.unit.zero));
    if (view.kind === 'heatmap') return heatmapView(table, ctx, view);
    // SVG views share one frame with a resize observer, like chartView.
    const wrap = h('div', {class: 'ev-chart'});
    const head = h('div', {class: 'chart-head'});
    const frame = h('div', {class: 'chart-frame'});
    const foot = h('p', {class: 'chart-foot'});
    const legend = h('div', {class: 'chart-legend'});
    const hint = scrollHint();
    wrap.append(head, legend, hint, frame, foot);
    let chart = null;
    const draw = options => {
      if (!chart) return;
      chart.update(Math.round(frame.clientWidth || wrap.clientWidth || 0), options);
      hint.hidden = !frame.classList.contains('scrolls');
    };
    const mount = svgView => {
      chart = ChartSvg.mount({document, frame, table, plan, title, onOpen: open, view: svgView});
      if (wrap.isConnected) draw({force: true});
    };
    const titleNode = h('h4', {class: 'chart-title'});
    const unit = h('p', {class: 'chart-unit'});
    const tech = h('p', {class: 'chart-unit chart-tech'});
    const glossHost = h('div', {class: 'gloss-host'});
    const setTitle = (question, technical, labels) => {
      texText(titleNode, question); texText(tech, technical);
      glossHost.replaceChildren(glossLine(labels) || '');
    };
    const labelsNote = ''; // the column-label caveat is shown once, in the table's status list above
    head.append(titleNode, tech, unit, glossHost);
    const takeawayData = ctx.takeaway ? ctx.takeaway(table) : null;
    if (takeawayData) head.append(h('p', {class: 'chart-takeaway'}, h('span', {class: 'term', text: 'From the answer'}), h('span', {math: takeawayData.text}),
      takeawayData.citations.length ? h('span', {class: 'cites'}, takeawayData.citations.map(n => h('span', {class: 'cite-num', text: String(n)}))) : null));
    const name = title;
    const lineLegend = column => {
      const series = ChartSvg.lineSeries(table, view.ordered, column);
      legend.replaceChildren(h('ul', {class: 'series-legend', 'aria-label': 'Series'}, series.map((item, si) => {
        const last = item.points.filter(p => p.cell.text).pop();
        return h('li', null, ChartSvg.legendSwatch(document, si), texText(h('span', {class: 'name'}), item.label),
          last ? h('span', {class: 'last'}, h('span', {text: '· '}), texText(h('span'), last.cell.text)) : null);
      })));
    };
    if (view.kind === 'slope') {
      const [a, b] = plan.category.values;
      const show = index => {
        const panel = plan.panels[index];
        setTitle(ChartSelect.businessQuestion('slope', table, {metric: panel.header, from: a, to: b}),
          `${name}: ${panel.header} by ${(table.headers[0]?.text || 'row').toLowerCase()}, ${a} → ${b}`, [panel.header]);
        unit.textContent = `Each line joins a row's two printed values.${labelsNote}`;
        mount({kind: 'slope', panel});
      };
      legend.replaceChildren(h('span', {class: 'key'}, h('span', {class: 'swatch a', 'aria-hidden': 'true'}), h('span', {text: a})),
        h('span', {class: 'key'}, h('span', {class: 'swatch b', 'aria-hidden': 'true'}), h('span', {text: b})),
        h('span', {class: 'legend-note', text: `Labels as written in the “${ChartSelect.texPlain(plan.category.header)}” column.`}));
      if (plan.panels.length > 1) head.append(choiceSeg('Metric shown', plan.panels.map((panel, i) => ({value: i, label: panel.header})), 0, value => show(Number(value))));
      show(0);
      foot.textContent = 'Scale: lowest to highest printed value, not from zero. Slopes show direction, not size. Values exactly as written.';
    } else if (view.kind === 'line') {
      const ordered = view.ordered;
      if (ordered.axis === 'columns') {
        setTitle(ChartSelect.businessQuestion('line', table, {axis: ordered.axisLabel}), `${name}: ${captionBody(table).split(/(?<=\.)\s/)[0]}`, [ordered.axisLabel]);
        unit.textContent = `Horizontal axis: the column headings ${ordered.columns.map(col => ChartSelect.texPlain(col.header)).join(', ')} under “${ChartSelect.texPlain(ordered.axisLabel)}”, placed at their numeric positions.${labelsNote}`;
        mount({kind: 'line', ordered});
        lineLegend(undefined);
      } else {
        const show = choice => {
          const axis = ChartSelect.texPlain(ordered.axisLabel);
          if (choice === 'all') {
            setTitle(ChartSelect.businessQuestion('line', table, {axis: ordered.axisLabel}), `${name}: ${ordered.columns.map(col => col.header).join(', ')} by ${ordered.axisLabel}`, ordered.columns.map(col => col.header));
            unit.textContent = `Horizontal axis: “${axis}” as listed in the rows. All columns share one vertical scale because each reports the same kind of value and their ranges overlap; check in the caption that they measure the same quantity.${labelsNote}`;
            mount({kind: 'line', ordered, column: 'all'});
            lineLegend('all');
            return;
          }
          const col = ordered.columns[choice];
          setTitle(ChartSelect.businessQuestion('line', table, {axis: ordered.axisLabel}), `${name}: ${col.header} by ${ordered.axisLabel}`, [col.header]);
          unit.textContent = `Horizontal axis: “${axis}” as listed in the rows, at their numeric positions.${labelsNote}`;
          mount({kind: 'line', ordered, column: col.column});
          lineLegend(col.column);
        };
        const start = ordered.shared ? 'all' : 0;
        if (ordered.columns.length > 1) {
          head.append(choiceSeg('Columns shown', [...(ordered.shared ? [{value: 'all', label: 'All columns'}] : []),
            ...ordered.columns.map((col, i) => ({value: i, label: col.header}))], start, value => show(value === 'all' ? 'all' : Number(value))));
        }
        show(start);
      }
      foot.textContent = 'Lines join one series along an axis the paper orders. Scale: lowest to highest printed value, not from zero. Values exactly as written.';
    } else if (view.kind === 'scatter') {
      let x = view.x[0].column, y = view.y[0].column;
      const show = () => {
        setTitle(ChartSelect.businessQuestion('scatter', table, {x: table.headers[x].text, y: table.headers[y].text}),
          `${name}: ${table.headers[y].text} against ${table.headers[x].text}`, [table.headers[x].text, table.headers[y].text]);
        unit.textContent = `Horizontal: “${ChartSelect.texPlain(table.headers[x].text)}”. Vertical: “${ChartSelect.texPlain(table.headers[y].text)}”. Units and arrows as written in the column labels.${labelsNote}`;
        mount({kind: 'scatter', x, y});
      };
      const pickers = h('div', {class: 'axis-pickers'});
      if (view.x.length > 1) pickers.append(h('span', {class: 'chart-type-label', text: 'Cost axis'}), choiceSeg('Cost or resource axis', view.x.map(col => ({value: col.column, label: col.header})), x, value => { x = Number(value); show(); }));
      if (view.y.length > 1) pickers.append(h('span', {class: 'chart-type-label', text: 'Outcome axis'}), choiceSeg('Outcome axis', view.y.map(col => ({value: col.column, label: col.header})), y, value => { y = Number(value); show(); }));
      if (pickers.childElementCount) head.append(chartOptions(pickers));
      show();
      foot.textContent = 'One point per row. Both scales run from the lowest to the highest printed value, not from zero. Better is ↑ or ↓ as the paper marks it. Nothing fitted.';
    } else if (view.kind === 'errorbars') {
      const all = view.columns;
      let picked = false;
      const show = choice => {
        const columns = choice === 'all' ? all : [all[choice]];
        setTitle(ChartSelect.businessQuestion('errorbars', table, {metric: columns.length === 1 ? columns[0].header : 'each measure'}),
          `${name}: ${columns.map(col => col.header).join(', ')} with reported uncertainty`, ['±', ...columns.map(col => col.header)]);
        mount({kind: 'errorbars', columns});
      };
      unit.replaceChildren(h('span', {text: `± as stated in the ${view.meaning.basis}: “`}), texText(h('span'), view.meaning.quote), h('span', {text: '”.'}));
      const picker = all.length > 1 ? choiceSeg('Columns shown', [{value: 'all', label: 'All columns'}, ...all.map((col, i) => ({value: i, label: col.header}))], 'all',
        value => { picked = true; show(value === 'all' ? 'all' : Number(value)); }) : null;
      if (picker) head.append(picker);
      show('all');
      // Side by side only when every column fits; otherwise open on the first column.
      requestAnimationFrame(() => {
        if (!wrap.isConnected) return;
        draw({force: true});
        if (!picked && picker && frame.classList.contains('scrolls')) { picker.select(0); picked = false; }
      });
      foot.textContent = 'Each dot is the printed value; each bar spans the printed ± range. Each column has its own scale. Values exactly as written.';
    }
    requestAnimationFrame(() => { if (wrap.isConnected) draw({force: true}); });
    const observer = new ResizeObserver(() => { if (wrap.isConnected) draw(); else observer.disconnect(); });
    observer.observe(frame);
    wrap.dispose = () => observer.disconnect();
    wrap.redraw = () => draw({force: true});
    return wrap;
  }

  /* Heatmap table: the full table with every number visible; numeric cells shaded on their own
     column's scale (lowest to highest printed value). Shading never means "better". */
  function heatmapView(table, ctx, view) {
    const shaded = new Map(view.columns.map(col => [col.column, col]));
    const valueOf = cell => (cell.parsed ? cell.parsed.value : ChartSelect.parsePlusMinus(cell.text)?.value ?? null);
    const ranges = new Map();
    for (const column of shaded.keys()) {
      const values = table.rows.map(row => valueOf(row.cells[column])).filter(value => value != null);
      ranges.set(column, [Math.min(...values), Math.max(...values)]);
    }
    const head = h('tr', null, table.headers.map((header, column) => texText(h('th', {scope: 'col', class: column === 0 ? 'ev-label-col' : shaded.has(column) ? 'num' : ''}), header.text)));
    const body = h('tbody');
    for (const row of table.rows) {
      const tr = h('tr', {class: row.citedBy.length ? 'is-cited' : ''});
      row.cells.forEach((cell, column) => {
        const header = table.headers[column]?.text || `Column ${column + 1}`;
        const value = shaded.has(column) ? valueOf(cell) : null;
        const [min, max] = ranges.get(column) || [0, 0];
        const level = value == null ? null : max === min ? 0.5 : (value - min) / (max - min);
        const button = h('button', {type: 'button', class: `cell-btn${value != null ? ' num' : ''}`,
          'aria-label': `${ChartSelect.texPlain(header)}, ${ChartSelect.texPlain(row.row_label)}: ${cell.text ? ChartSelect.texPlain(cell.text) : 'empty in source'}${level != null ? `, shade ${Math.round(level * 4) + 1} of 5 in this column` : ''}. Open source.`,
          onclick: () => openRowSource(ctx, table, row, cell, button)});
        if (cell.text) texText(button, cell.text); else button.append(h('span', {class: 'empty-cell', text: 'empty'}));
        if (cell.source_id) button.dataset.sourceId = cell.source_id;
        const td = h(column === 0 ? 'th' : 'td', {scope: column === 0 ? 'row' : null, class: `${column === 0 ? 'ev-label-col' : ''}${level != null ? ' heat' : ''}`}, button);
        if (level != null) { td.style.setProperty('--heat', level.toFixed(3)); td.dataset.heat = String(Math.round(level * 4) + 1); }
        if (column === 0 && row.citedBy.length) button.append(h('span', {class: 'cites'}, row.citedBy.map(n => h('span', {class: 'cite-num', text: String(n)}))));
        tr.append(td);
      });
      body.append(tr);
    }
    const scale = h('span', {class: 'heat-scale', 'aria-hidden': 'true'}, [1, 2, 3, 4, 5].map(n => {
      const swatch = h('span', {class: 'heat-swatch'});
      swatch.style.setProperty('--heat', String((n - 1) / 4)); // CSSOM, allowed under the page CSP
      return swatch;
    }));
    return h('div', {class: 'ev-chart heatmap'},
      h('div', {class: 'chart-head'}, texText(h('h4', {class: 'chart-title'}), ChartSelect.businessQuestion('heatmap', table)),
        texText(h('p', {class: 'chart-unit chart-tech'}), `${tableTitle(table)}: ${captionBody(table).split(/(?<=\.)\s/)[0]}`),
        glossLine(table.headers.map(hd => hd.text)),
        h('p', {class: 'chart-unit', text: `Every value is shown exactly as written. Shaded columns: ${view.columns.map(col => col.plain).join(', ')}.`})),
      h('div', {class: 'table-scroll', tabIndex: 0, role: 'region', 'aria-label': `${tableTitle(table)} heatmap, scrollable`},
        h('table', {class: 'ev-table heat-table'}, h('caption', {class: 'sr-only', text: `${tableTitle(table)} heatmap: ${captionBody(table)}`}), h('thead', null, head), body)),
      h('p', {class: 'chart-legend heat-legend'}, h('span', {class: 'key'}, h('span', {text: 'Lowest'}), scale, h('span', {text: 'Highest value in that column'})),
        h('span', {class: 'legend-note', text: 'Each column has its own scale. Darker does not mean better: for some metrics lower is better (↓ in the label, where the paper gives one). Unshaded cells are text, empty, or not a plain number.'})));
  }

  /* Question-focused comparison: when the question names two or more retrieved papers, show those papers
     side by side with what the answer actually found from each (verbatim, cited), or say plainly that no
     supported finding came from it. Other retrieved sources stay available, folded. */
  function shortTitle(title) { const head = (title || 'Untitled source').split(':')[0].trim(); return head.length <= 40 ? head : `${head.slice(0, 38)}…`; }
  function focusedComparison(named, studies, ctx) {
    const result = ctx.demo.result;
    const chunksOf = study => new Set((result.evidence || []).filter(p => (p.arxiv_id || p.title) === (study.arxiv_id || study.title)).map(p => p.chunk_id));
    const findings = (result.summary.claims || []).filter(claim => claim.kind !== 'interpretation');
    const reasons = result.summary.limitation_support || [];
    const column = study => {
      const chunks = chunksOf(study);
      const own = list => list.filter(item => (item.chunk_ids || []).some(id => chunks.has(id)));
      const found = own(findings), why = own(reasons);
      const textCount = (result.evidence || []).filter(p => chunks.has(p.chunk_id) && p.representation !== 'linearized_table').length;
      return h('section', {class: 'compare-col', 'aria-label': study.title},
        h('h3', {class: 'compare-name', text: shortTitle(study.title)}),
        h('p', {class: 'compare-full', text: study.title}),
        h('p', {class: 'compare-retrieved', text: `Retrieved: ${[textCount ? `${textCount} text passage${textCount === 1 ? '' : 's'}` : null,
          study.tables.length ? `${study.tables.length} table${study.tables.length === 1 ? '' : 's'}` : null].filter(Boolean).join(', ') || 'nothing'}.`}),
        h('h4', {text: 'What the answer found'}),
        found.length ? h('ul', {class: 'bullets'}, found.map(item => cited('li', item, ctx.demo, ctx.number)))
          : h('p', {class: 'compare-missing'}, icon('alert'), h('span', {text: 'The answer states no finding from this paper.'})),
        why.length ? h('div', null, h('h4', {text: 'Why it is missing or limited'}), h('ul', {class: 'bullets'}, why.map(item => cited('li', item, ctx.demo, ctx.number)))) : null);
    };
    const others = studies.filter(study => !named.includes(study));
    return h('div', {class: 'compare-focus'},
      h('p', {class: 'block-intro', text: `The question names ${named.length} papers. Each column shows only what the answer found from that paper, quoted from the cited evidence.`}),
      h('div', {class: 'compare-cols'}, named.map(column)),
      note('Findings are shown as reported; they are not placed on one scale or ranked against each other.', '', 'info'),
      others.length ? h('details', {class: 'fold'}, h('summary', {text: `Other sources retrieved for this answer (${others.length})`}), renderStudies(others, ctx)) : null);
  }

  /* ---------- Study comparison (never a shared scale across papers) ---------- */
  function renderStudies(studies, ctx) {
    const rows = studies.map(study => h('tr', null,
      h('th', {scope: 'row'}, h('span', {class: 'study-title', text: study.title || 'Untitled source'}), study.arxiv_id && h('span', {class: 'mono muted', text: study.arxiv_id})),
      h('td', null, study.tables.length
        ? h('ul', {class: 'plain-list'}, study.tables.map(t => h('li', null, texText(h('span'), t.caption))))
        : h('span', {class: 'muted', text: 'Text passages only; no table retrieved.'})),
      h('td', null, study.tables.length
        ? h('ul', {class: 'plain-list'}, study.tables.map(t => h('li', null, texText(h('span'), t.headers.slice(1).join(', ')))))
        : h('span', {class: 'muted', text: 'Not stated in a retrieved table.'})),
      h('td', {class: 'num'}, h('span', {text: `${study.passages.length} passage${study.passages.length === 1 ? '' : 's'}`}),
        h('span', {class: 'cites'}, study.citations.length ? study.citations.map(n => h('span', {class: 'cite-num', text: String(n)})) : h('span', {class: 'muted', text: 'not cited'})))));
    return h('div', null,
      h('div', {class: 'table-scroll', tabIndex: 0, role: 'region', 'aria-label': 'What each study measured'},
        h('table', {class: 'matrix'}, h('thead', null, h('tr', null,
          ['Study', 'What the retrieved evidence covers', 'Values reported (column labels as written)', 'In this answer'].map(text => h('th', {scope: 'col', text})))),
          h('tbody', null, rows))),
      note('These studies were measured in different tables, under different conditions. Their values are not placed on one scale or ranked against each other.', '', 'info'));
  }

  /* What the reader can rely on for this source, in plain words, from the answer's own records. */
  function evidenceChecks(passage, claim, highlightId) {
    const items = [];
    const quotes = (claim?.support || []).filter(support => support.chunk_id === passage.chunk_id);
    if (quotes.length) items.push(['check', 'ok', 'The highlighted quote was found word-for-word in this source.']);
    else if (claim) items.push(['info', '', 'This source is cited for the statement; read the passage to judge the support.']);
    if (passage.representation === 'linearized_table') {
      items.push(EvidenceModel.roundTripOk(passage) ? ['check', 'ok', 'This table row matches the paper exactly.'] : ['alert', 'bad', 'This table row could not be matched to the paper text.']);
      items.push(passage.header_review === 'verified' ? ['check', 'ok', 'Column headings were checked by a person.'] : ['alert', 'warn', 'Column headings were read automatically; compare them with the paper.']);
      if (highlightId) items.push(['info', '', 'The selected value is highlighted in the row below.']);
    }
    items.push(['info', '', passage.source === 'pdf' ? 'Text taken from the paper\u2019s PDF; exact PDF highlighting is not available.' : 'Text taken from the paper\u2019s web (HTML) version.']);
    return h('ul', {class: 'evidence-checks', 'aria-label': 'What was checked for this source'},
      items.map(([iconName, tone, text]) => h('li', {class: `ev-flag ${tone}`}, icon(iconName), h('span', {text}))));
  }
  /* Evidence Inspector reading order: the quote first, then the claim and the surrounding passage.
     Identity, version, hashes and extraction notes move into a folded "Source details". Nothing is removed. */
  function tidySource(view, passage) {
    const kids = [...view.children];
    const ret = view.querySelector(':scope > .source-return'), title = view.querySelector(':scope > h3');
    const checks = view.querySelector(':scope > .evidence-checks'), meta = view.querySelector(':scope > .source-metadata');
    const link = view.querySelector(':scope > .source-link');
    const segs = [], loose = [];
    let cur = null;
    for (const node of kids) {
      if ([ret, title, checks, meta, link].includes(node)) continue;
      if (node.tagName === 'H4') { cur = {head: node, nodes: [node]}; segs.push(cur); continue; }
      (cur ? cur.nodes : loose).push(node);
    }
    const find = re => segs.find(seg => re.test(seg.head.textContent));
    const quote = find(/supporting quote/i), row = find(/^Table row/i), claimSeg = find(/^Cited claim/i);
    const rest = segs.filter(seg => ![quote, row, claimSeg].includes(seg));
    if (quote) quote.head.textContent = 'Supporting quote';
    if (claimSeg) claimSeg.head.textContent = 'Claim in the answer';
    const details = h('details', {class: 'source-details'}, h('summary', {text: 'Source details'}));
    if (meta) details.append(meta);
    const keepTop = loose.filter(node => /synthetic|not supplied/i.test(node.textContent));
    details.append(...loose.filter(node => !keepTop.includes(node)));
    const context = [];
    rest.forEach((seg, i) => {
      if (i === 0) {
        seg.head.textContent = 'Surrounding passage';
        for (const node of seg.nodes) {
          if (node.matches('p.meta, details.source-check-text')) details.append(node); else context.push(node);
        }
      } else details.append(...seg.nodes);
    });
    const where = [passage.section, passage.source === 'pdf' ? `PDF${passage.page_number != null ? `, page ${passage.page_number}` : ''}` : 'web (HTML) version'].filter(Boolean).join(' · ');
    view.replaceChildren(...[ret, title, h('p', {class: 'source-sub', text: where}), link, ...keepTop,
      ...(quote?.nodes || []), ...(row?.nodes || []), checks, ...(claimSeg?.nodes || []), ...context, details].filter(Boolean));
  }

  /* Perplexity-style source row under the answer: the sources the answer cites, one click to inspect. */
  function sourcesRow(demo, number) {
    const evidence = demo.result.evidence || [];
    const cites = EvidenceModel.citationMap(demo.result);
    const cited = evidence.map((passage, index) => ({passage, index})).filter(({passage}) => cites.has(passage.chunk_id));
    const shown = (cited.length ? cited : evidence.map((passage, index) => ({passage, index}))).slice(0, 4);
    if (!shown.length) return null;
    const row = h('div', {class: 'source-cards', role: 'list', 'aria-label': 'Sources cited in this answer'});
    for (const {passage, index} of shown) {
      const card = h('button', {type: 'button', class: 'source-card', role: 'listitem', 'aria-label': `Open source ${index + 1}: ${passage.title}, ${sourceLocation(passage)}`,
        onclick: () => showEvidence(demo, number, index, card)},
        h('span', {class: 'source-card-num', text: String(index + 1)}),
        h('span', {class: 'source-card-text'}, h('span', {class: 'source-card-title', text: passage.title}),
          h('span', {class: 'source-card-where', text: passage.representation === 'linearized_table' ? `${(passage.caption || '').split(/[:.]/)[0] || 'Table'} · row` : sourceLocation(passage)})));
      row.append(card);
    }
    const more = evidence.length - shown.length;
    if (more > 0) row.append(h('a', {href: `#a${number}-sources`, class: 'source-card more', role: 'listitem',
      'aria-label': `View all ${evidence.length} sources`, onclick: event => { event.preventDefault(); openTo(`#a${number}-sources`); }, text: `View all ${evidence.length} sources`}));
    return row;
  }
  /* Follow-up area. Live: the existing composer (each question is researched with the server's
     history policy). Replay: an explanation, never a simulated answer. */
  function followUpNote() {
    return h('p', {class: 'followup-off'}, icon('info'),
      h('span', {text: 'Follow-up questions need live research, which is not running in this copy. Open other saved research from the sidebar or the Library.'}));
  }


  /* ---------- Answer reading helpers (answer-first layout, 2026-11-22) ---------- */
  // Group consecutive findings into short paragraphs (three sentences at most) for continuous reading.
  function paragraphs(items) {
    const out = [];
    for (let i = 0; i < items.length; i += 3) out.push(items.slice(i, i + 3));
    return out;
  }
  // Selective emphasis: bold quantities exactly as written (percentages, ranges, signed points), nothing else.
  const QUANTITY = /[+−-]?\d+(?:[.,]\d+)?(?:\s?[–-]\s?\d+(?:[.,]\d+)?)?(?:\s?(?:%|percentage points|points|pp|×|x\b)|-point\b|-percentage-point\b)/g;
  function emphasizeQuantities(node) {
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, {acceptNode: text =>
      text.parentElement.closest('.katex, .citation, strong') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
    const texts = [];
    while (walker.nextNode()) texts.push(walker.currentNode);
    for (const text of texts) {
      const value = text.nodeValue;
      QUANTITY.lastIndex = 0;
      if (!QUANTITY.test(value)) continue;
      QUANTITY.lastIndex = 0;
      const frag = document.createDocumentFragment();
      let last = 0;
      for (const match of value.matchAll(QUANTITY)) {
        frag.append(value.slice(last, match.index), h('strong', {text: match[0]}));
        last = match.index + match[0].length;
      }
      frag.append(value.slice(last));
      text.replaceWith(frag);
    }
    return node;
  }
  /* Material problems only: issues that change how the headline can be used (table-count conflicts,
     partial coverage). Routine checks sit in the verification line. Hidden when there is nothing material. */
  function materialNotice(demo, number, ctx) {
    const list = h('ul', {class: 'material-list'});
    const box = h('div', {class: 'material', id: `a${number}-caveats`, role: 'note', hidden: true},
      h('p', {class: 'material-head'}, icon('alert'), h('span', {text: 'Check before quoting'})), list);
    const add = text => { list.append(h('li', {text})); box.hidden = false; };
    if (demo.result?.summary.answer_scope === 'partial') add('This answer covers only part of the question.');
    ctx.addCaveat = content => { list.prepend(typeof content === 'string' ? h('li', {class: 'caveat-strong', text: content}) : h('li', {class: 'caveat-strong'}, content)); box.hidden = false; refreshIssues(number); };
    return box;
  }
  /* One quiet line under the answer: what was checked automatically, and the human review state from the
     backend's review records for this saved version. Automatic checks are never presented as approval. */
  function humanReview(demo) {
    if (!demo.library) return {tone: 'draft', short: 'Not saved, so not reviewed', long: 'This answer has not been saved as a brief, so no one can review it yet.'};
    const latest = demo.library.reviews.at(-1);
    if (!latest) return {tone: 'draft', short: 'Not reviewed by a person yet', long: 'No reviewer has recorded a decision on this version. It is not ready for client use.'};
    const by = latest.reviewer ? ` by ${latest.reviewer}` : '';
    const on = latest.created_at ? `, ${when(latest.created_at)}` : '';
    const note = latest.notes ? ` Note: “${latest.notes}”` : '';
    return {
      approve: {tone: 'ok', short: `Approved${by}`, long: `Approved${by}${on}. Approval covers this saved version; it does not certify the sources.${note}`},
      revise: {tone: 'warn', short: `Changes requested${by}`, long: `Changes requested${by}${on}. This version is not approved.${note}`},
      reject: {tone: 'bad', short: `Rejected${by}`, long: `Rejected${by}${on}. Do not use this version.${note}`},
    }[latest.decision] || {tone: 'draft', short: 'Review status unknown', long: `Unrecognised review decision “${latest.decision}”.`};
  }
  // The shared exporter's message always says "not approved"; replace it with the recorded review state.
  function exportControls(demo, number) {
    const group = AnswerExport.controls(demo, number);
    const status = group.querySelector('[role="status"]');
    group.addEventListener('click', () => queueMicrotask(() => {
      if (status && /download requested/.test(status.textContent)) status.textContent = status.textContent.replace(/Pending review; not approved\./, `Review record: ${humanReview(demo).short}.`);
    }));
    return group;
  }
  function answerActions(demo, tools) {
    const saved = demo.library
      ? h('span', {class: 'answer-saved'}, icon('check'), h('span', {text: 'Saved in Library'}))
      : h('button', {type: 'button', class: 'text-btn', onclick: () => tools.reveal('brief')}, icon('bookmark'), h('span', {text: 'Save'}));
    const menu = h('details', {class: 'export-menu'},
      h('summary', {class: 'text-btn'}, icon('download'), h('span', {text: 'Export'})),
      h('div', {class: 'export-pop'}, exportControls(demo, tools.number), snapshotButton(demo),
        h('p', {class: 'export-note', text: `Exports contain the answer as generated and its sources. They do not include the review record; current review: ${humanReview(demo).short}.`})));
    return h('div', {class: 'answer-actions'}, saved, menu);
  }
  // What a reviewer should resolve, taken from the answer as shown (material notes first, then routine checks).
  function issueList(number) {
    const turn = document.getElementById(`turn-${number}`);
    const texts = turn ? [...turn.querySelectorAll('.ws-panel .notes-list > li')].map(li => li.textContent.trim()).filter(Boolean) : [];
    return texts.length ? h('ul', {class: 'bullets'}, texts.map(text => h('li', {text}))) : h('p', {class: 'muted small', text: 'The automatic checks recorded no outstanding issues for this version.'});
  }
  // Table checks can add a material issue after the workspace opened; keep its list current.
  function refreshIssues(number) {
    document.querySelectorAll(`.review-issues[data-number="${number}"]`).forEach(section => section.children[1].replaceWith(issueList(number)));
  }
  function outstandingIssues(number) {
    return h('section', {class: 'review-issues', 'aria-label': 'Outstanding issues', 'data-number': String(number)},
      h('p', {class: 'term', text: 'Outstanding issues'}),
      issueList(number),
      h('a', {href: `#a${number}-verify`, class: 'link-btn', onclick: event => { event.preventDefault(); openTo(`#a${number}-verify`); }, text: 'See every check and where it comes from'}));
  }
  function verificationLine(demo, number, checks, tables, tools) {
    const review = humanReview(demo);
    const automatic = isSynthesis(demo) || demo.result?.summary?.support_check
      ? 'Quotes matched word-for-word in the papers' : 'Saved answer';
    const routine = [];
    const papers = new Set((demo.result.evidence || []).map(p => p.arxiv_id || p.title)).size;
    if (papers === 1 && demo.result.summary.status === 'ok') routine.push('The answer rests on a single paper.');
    if (tables.some(t => !t.headerStatus.verified)) routine.push('Table column headings were read automatically; compare them with the paper before quoting numbers.');
    const reviewBtn = demo.library
      ? h('button', {type: 'button', class: 'text-btn', onclick: () => tools.reveal('brief')}, icon('shield'), h('span', {text: 'Open review workspace'}))
      : h('button', {type: 'button', class: 'text-btn', onclick: () => tools.reveal('brief')}, icon('bookmark'), h('span', {text: 'Save as brief'}));
    return h('details', {class: 'verify-line', id: `a${number}-status`},
      h('summary', null,
        h('span', {class: 'verify-auto'}, icon('check'), h('span', {text: automatic})),
        h('span', {class: 'verify-sep', 'aria-hidden': 'true', text: '·'}),
        h('span', {class: `verify-review ${review.tone}`}, icon(review.tone === 'ok' ? 'check' : 'shield'), h('span', {text: review.short})),
        h('span', {class: 'verify-more', text: 'Details'})),
      h('div', {class: 'verify-body'},
        h('p', null, h('strong', {text: 'Automatic checks. '}),
          h('span', {text: 'Every quoted passage was found word-for-word in its source, and table values were matched to the paper. Whether a passage fully supports a claim is a judgement for the reviewer.'})),
        h('p', null, h('strong', {text: 'Human review. '}), h('span', {text: review.long})),
        routine.length ? h('ul', {class: 'bullets'}, routine.map(text => h('li', {text}))) : null,
        h('div', {class: 'verify-actions'}, reviewBtn,
          h('a', {href: `#a${number}-verify`, class: 'text-btn', 'data-checks': 'line', onclick: event => { event.preventDefault(); openTo(`#a${number}-verify`); },
            text: `All ${checks.length} checks`}))));
  }

  /* ---------- Plain-language answer card (progressive disclosure, 2026-11-22) ---------- */
  /* Every place that states the number of checks says the same number. */
  function setCheckCount(root, total) {
    for (const link of root.querySelectorAll('[data-checks]')) {
      link.textContent = link.dataset.checks === 'card' ? `See all ${total} checks and where each comes from` : link.dataset.checks === 'line' ? `All ${total} checks` : `${total} item${total === 1 ? '' : 's'}`;
    }
  }
  function plainReview(demo) {
    const decision = demo.library?.reviews.at(-1)?.decision;
    if (!demo.library) return 'Not saved or reviewed yet';
    return {approve: 'Approved by a reviewer', revise: 'A reviewer asked for changes', reject: 'Rejected by a reviewer'}[decision] || 'Not reviewed by a person yet';
  }
  function plainEvidence(result) {
    const evidence = result.evidence || [];
    const papers = new Set(evidence.map(p => p.arxiv_id || p.title)).size;
    const tableKeys = new Set(evidence.filter(p => p.representation === 'linearized_table').map(p => `${p.arxiv_id}#${p.table_id}`)).size;
    const text = evidence.filter(p => p.representation !== 'linearized_table').length;
    const parts = [];
    if (tableKeys) parts.push(`${tableKeys} table${tableKeys === 1 ? '' : 's'}`);
    if (text) parts.push(`${text} text excerpt${text === 1 ? '' : 's'}`);
    return `${papers} paper${papers === 1 ? '' : 's'}${parts.length ? ` (${parts.join(', ')})` : ''}`;
  }
  /* Open every collapsed layer around a target, then bring it into view and focus its heading. */
  function openTo(selector, root = document) {
    const target = typeof selector === 'string' ? $(selector, root) : selector;
    if (!target) return;
    const pane = target.closest('.brief-pane');
    if (pane?.hidden && pane.closest('.turn') === activeTurn) setTab(pane.dataset.pane, {scroll: false});
    const wsPanel = target.closest('.ws-panel');
    if (wsPanel?.hidden) target.closest('.brief')?.selectWorkspace?.(wsPanel.id.split('-ws-')[1]);
    for (let node = target; node; node = node.parentElement) if (node.tagName === 'DETAILS') node.open = true;
    target.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
    (target.querySelector('.block-title, h2, h3, summary') || target).focus?.({preventScroll: true});
  }
  /* "Check before quoting": the few caveats a first-time reader must see, in plain words. Each item
     comes from the answer's own records; the full list with field origins stays in Technical details. */
  function caveatCard(demo, number, checks, tables, ctx) {
    const items = [];
    const decision = demo.library?.reviews.at(-1)?.decision;
    if (decision !== 'approve') items.push(decision === 'revise' ? 'A reviewer asked for changes; this version is not approved.'
      : decision === 'reject' ? 'A reviewer rejected this version.' : 'No person has reviewed this answer yet, so it is not ready for client use.');
    const papers = new Set((demo.result.evidence || []).map(p => p.arxiv_id || p.title)).size;
    if (papers === 1 && demo.result.summary.status === 'ok') items.push('It rests on a single paper.');
    if (tables.some(t => !t.headerStatus.verified)) items.push("Table column headings were read automatically; compare them with the paper before quoting numbers.");
    const list = h('ul', {class: 'caveat-list'}, items.map(text => h('li', {text})));
    const card = h('section', {class: 'caveats', id: `a${number}-caveats`, 'aria-labelledby': `a${number}-caveats-h`},
      h('h3', {id: `a${number}-caveats-h`, tabIndex: -1}, icon('alert'), h('span', {text: 'Check before quoting'})), list,
      h('a', {href: `#a${number}-verify`, class: 'link-btn', 'data-checks': 'card', onclick: event => { event.preventDefault(); openTo(`#a${number}-verify`); },
        text: `See all ${checks.length} checks and where each comes from`}));
    // Table-level problems found later (e.g. a model count that differs from the paper's table) join this list first.
    ctx.addCaveat = text => list.prepend(h('li', {class: 'caveat-strong', text}));
    return card;
  }
  /* The first business implication, labelled as an interpretation, with its suggested action. */
  function soWhat(insight, demo, number) {
    const first = insight?.implications?.[0];
    if (!first) return null;
    return h('section', {class: 'so-what', 'aria-labelledby': `a${number}-sowhat-h`},
      h('h3', {id: `a${number}-sowhat-h`, text: `Possible implication for ${insight.industry}`}),
      cited('p', first, demo, number, 'so-what-text'),
      first.suggested_action ? h('p', {class: 'so-what-action'}, h('strong', {text: 'Suggested next step: '}), h('span', {math: first.suggested_action})) : null,
      h('p', {class: 'so-what-note'}, h('span', {text: 'An interpretation for business use, not something the study tested. '}),
        h('a', {href: `#a${number}-business`, class: 'link-btn', onclick: event => { event.preventDefault(); openTo(`#a${number}-business`); },
          text: insight.implications.length > 1 ? `All ${insight.implications.length} implications` : 'Assumptions and details'})));
  }
  /* Three levels: the answer card, key chart and supporting evidence stay open; everything else
     sits in "Explore the evidence"; run metadata and audit detail sit in "Technical details". */
  function layerBrief(body, number, technical, view) {
    const take = key => { const b = $(`:scope > .block-${key}`, body); if (b) { b.classList.add('in-layer'); b.classList.remove('group-start'); } return b; };
    const key = take('keychart'), numbers = take('numbers'), findings = take('findings');
    const defs = findings ? $('.fold', findings) : null;
    const sections = h('section', {class: 'explore', 'aria-labelledby': `a${number}-explore-h`},
      h('h2', {class: 'explore-title', id: `a${number}-explore-h`, text: 'Explore this research'}));
    const add = (name, hint, ...content) => {
      const parts = content.filter(Boolean);
      if (!parts.length) return null;
      const details = h('details', {class: 'section'}, h('summary', null, h('span', {class: 'section-name', text: name}), hint ? h('span', {class: 'section-hint', text: hint}) : null), ...parts);
      sections.append(details);
      return details;
    };
    // Only offered when the answer carries a plain-language version; otherwise the findings are the answer above.
    if (findings && view?.status === 'available') add('Plain-language version', 'The same findings, explained simply', findings);
    else findings?.remove();
    const business = take('business');
    add('Business implications', business ? 'Consultant interpretation, not a study finding' : null, business);
    add('Limitations and uncertainty', 'What this evidence cannot show', take('risks'));
    const compare = take('compare');
    add('Source comparison', compare?.dataset.hint || 'What each paper measured', compare);
    add('Risk and compliance', 'Advisory only', take('regulatory'));
    const tableCount = numbers ? numbers.querySelectorAll('.ev-figure').length : 0;
    if (numbers) $('.block-title', numbers).textContent = 'Source tables';
    add('Data and charts', tableCount ? `${tableCount} source table${tableCount === 1 ? '' : 's'}, with charts where the data allows` : null, key, numbers);
    const verify = take('verify');
    // No count in the hint: table-level checks can be added after this is built (see the status line).
    add('Evidence checks and review', verify ? 'Every check, where it comes from, and the review history' : null, verify);
    const sources = take('sources');
    add('Sources', sources ? `${sources.querySelectorAll('tbody tr').length} passages and table rows` : null, sources);
    const activity = add('Research activity', 'How this answer was produced and exported',
      technical.length ? h('section', {class: 'block in-layer', 'aria-label': 'Run details'}, h('h3', {text: 'Run details'}), h('ul', {class: 'bullets'}, technical.map(text => h('li', {text})))) : null,
      defs ? h('section', {class: 'block in-layer', 'aria-label': 'Definitions'}, defs) : null);
    activity?.classList.add('section-activity');
    body.append(sections);
    return activity || sections;
  }

  /* ---------- Brief rendering ---------- */
  // Which part of the brief a section belongs to: a visible label above its heading, so the research
  // answer, its evidence, the business reading and the assurance checks are told apart at a glance.
  const BLOCK_GROUPS = {
    summary: ['research', 'Research answer'], keychart: ['research', 'Research'], findings: ['research', 'Research'], numbers: ['evidence', 'Evidence'],
    compare: ['evidence', 'Evidence'], business: ['business', 'Business'], regulatory: ['assurance', 'Assurance'],
    risks: ['assurance', 'Assurance'], verify: ['review', 'Human review'], sources: ['evidence', 'Evidence'],
  };
  // Groups shape rhythm (spacing and rules between parts) and the contents rail, not labels above headings.
  function blockKicker() { return null; }
  /* Multi-agent trace: which agents ran, what each was asked, what it returned, and every routing
     decision with its reason. Text only; nothing here is a finding. */
  const AGENT_NAMES = {orchestrator: 'Orchestrator', research_agent: 'Research agent', verification_agent: 'Verification agent',
    business_insight_agent: 'Business insight agent', chart_tool: 'Chart tool (no model)'};
  const DECISION_NAMES = {decompose: 'Extra searches', business_routing: 'Business insight routing', chart_routing: 'Chart routing',
    targeted_retrieval: 'Extra targeted search', targeted_retrieval_result: 'Targeted search result', verify: 'Verification',
    draft_rejected: 'Draft rejected', business_run: 'Business insight run', select_round: 'Answer round', start: 'Start'};
  const ABSTENTION_TEXT = {insufficient_evidence: 'the research agent found the evidence insufficient',
    no_supported_claims: 'no drafted claim passed verification', verification_rejected: 'the verification output was rejected, so nothing was kept',
    synthesis_rejected: 'the research draft failed citation or schema validation'};
  function agentTaskText(task) {
    const p = task.payload || {};
    if (task.kind === 'plan') return 'Planning call: decide what to search and which agents are needed.';
    if (task.kind === 'targeted_research') return `Targeted search for “${(p.searches || [])[0]?.query || ''}”. Keep the ${(p.pinned_ids || []).length} passage(s) earlier claims cite, add any new passages, and draft again only if something new was found.`;
    if (task.kind === 'research') return `Search the index for ${(p.searches || []).length} quer${(p.searches || []).length === 1 ? 'y' : 'ies'}: ${(p.searches || []).map(s => `“${s.query}”`).join(', ')}; draft cited claims.`;
    if (task.kind === 'verify') return `Check ${p.claim_count} drafted claim${p.claim_count === 1 ? '' : 's'} against ${(p.passage_ids || []).length} passages.`;
    if (task.kind === 'business_insight') return `Turn ${p.verified_claims} verified finding${p.verified_claims === 1 ? '' : 's'} into ${p.industry} implications.`;
    if (task.kind === 'chart_preview') return `Look for audit-verified tables among ${p.passage_count} passages.`;
    return task.kind;
  }
  function agentReplyText(reply) {
    const o = reply.output || {};
    if (reply.status === 'provider_failure') return o.kind === 'budget'
      ? `Call refused by the call budget (${o.cause.replace(/_/g, ' ')}). Nothing was retried.`
      : `AI provider failure (${o.cause.replace(/_/g, ' ')}). Nothing was retried.`;
    if (reply.status === 'rejected') return `Output rejected by validation: ${o.reason}`;
    if (reply.status === 'budget_exhausted') return o.reason;
    if (reply.from === 'orchestrator') return `${o.question_type?.replace(/_/g, ' ') || 'Plan'}: ${(o.subquestions || []).length} extra search${(o.subquestions || []).length === 1 ? '' : 'es'}. ${o.notes || ''}`.trim();
    if (reply.from === 'research_agent') {
      if (reply.status === 'no_new_evidence') return 'No passage that was not already in the evidence; no synthesis call was spent.';
      const added = o.new_passage_ids?.length ? `, ${o.new_passage_ids.length} new` : '';
      const drafted = (o.claims || []).length;
      return `${(o.passage_ids || []).length} passages${added}; ${drafted ? `${drafted} cited claim${drafted === 1 ? '' : 's'} drafted` : 'no claim drafted: the evidence was judged insufficient'}.`;
    }
    if (reply.from === 'verification_agent') {
      const claims = o.claims || [];
      const kept = claims.filter(c => c.decision === 'accepted').length;
      const adjusted = o.coverage_adjusted ? ` (the verifier reported ${o.coverage_reported}; recomputed from the claims kept)` : '';
      return `${kept} of ${claims.length} claim${claims.length === 1 ? '' : 's'} kept; coverage of the kept claims: ${o.coverage || 'none'}${adjusted}.${o.rejection ? ` ${o.rejection}` : ''}`;
    }
    if (reply.from === 'business_insight_agent') {
      const removed = (o.screened_out || []).length;
      return `Business insight ${String(o.status || reply.status).replace(/_/g, ' ')}: ${o.implication_count ?? 0} implication(s) kept${removed ? `, ${removed} removed by the unsupported-advice screen` : ''}.`;
    }
    if (reply.from === 'chart_tool') return o.reason || `${(o.tables || []).filter(t => t.status === 'complete').length} verified table(s).`;
    return reply.status;
  }
  function agentTraceBlock(agentic, number) {
    const calls = agentic.model_calls || {};
    const byAgent = Object.entries(calls.by_agent || {}).map(([name, n]) => `${AGENT_NAMES[name] || name} ${n}`).join(', ');
    const replies = new Map(agentic.trace.filter(e => e.type === 'reply').map(e => [e.task_id, e]));
    const steps = h('ol', {class: 'agent-steps'});
    for (const entry of agentic.trace) {
      if (entry.type === 'task') {
        const reply = replies.get(entry.task_id);
        const tone = !reply ? 'warn' : ['ok', 'available'].includes(reply.status) ? 'ok' : ['provider_failure', 'rejected', 'failed', 'budget_exhausted'].includes(reply.status) ? 'bad' : 'warn';
        steps.append(h('li', {class: 'agent-step'},
          h('div', {class: 'agent-step-head'}, h('strong', {text: AGENT_NAMES[entry.to] || entry.to}),
            reply ? chip(reply.status.replace(/_/g, ' '), tone) : chip('no reply', 'warn'),
            reply ? h('span', {class: 'muted small', text: `${reply.seconds.toFixed(1)} s · ${reply.model_calls || 0} model call${reply.model_calls === 1 ? '' : 's'}`}) : null),
          h('p', {class: 'agent-step-task', text: agentTaskText(entry)}),
          reply ? h('p', {class: 'muted small', text: agentReplyText(reply)}) : null));
      } else if (entry.type === 'decision') {
        steps.append(h('li', {class: 'agent-step decision'},
          h('div', {class: 'agent-step-head'}, h('strong', {text: `Orchestrator decision · ${DECISION_NAMES[entry.decision] || entry.decision}`}),
            chip(entry.run ? 'run' : 'skipped', entry.run ? 'ok' : '')),
          h('p', {class: 'muted small', text: entry.reason})));
      }
    }
    const verdictRows = (agentic.rounds || []).flatMap(round => (round.verification?.claims || []).map(row => h('tr', null,
      h('td', {text: String(round.round)}), h('td', {text: row.text}),
      h('td', {text: `quote ${row.deterministic?.quote_membership}; numbers, units and qualifiers ${row.deterministic?.numbers_and_qualifiers ?? row.deterministic?.reported_numbers}${row.number_grounding ? `; number grounding ${row.number_grounding.status.replace(/_/g, ' ')}${row.number_grounding.uncertain?.length ? ` (${row.number_grounding.uncertain.join(', ').replace(/_/g, ' ')})` : ''}` : ''}`}),
      h('td', {text: row.automated ? `${row.automated.verdict.replace(/_/g, ' ')}${row.automated.issues.length ? ` (${row.automated.issues.join(', ').replace(/_/g, ' ')})` : ''}: ${row.automated.reason}` : 'not judged'}),
      h('td', null, chip(row.decision, row.decision === 'accepted' ? 'ok' : 'warn')))));
    const verdicts = verdictRows.length ? h('details', {class: 'fold'}, h('summary', {text: `Claim-by-claim verification (${verdictRows.length})`}),
      h('div', {class: 'agent-table-wrap'}, h('table', {class: 'agent-table'},
        h('thead', null, h('tr', null, ['Round', 'Drafted claim', 'Deterministic checks', 'Verification agent (model judgment)', 'Decision'].map(text => h('th', {scope: 'col', text})))),
        h('tbody', null, verdictRows)))) : null;
    const removedAdvice = (agentic.business_screening || []).filter(item => item.status !== 'kept_unverified');
    const screened = removedAdvice.length ? h('details', {class: 'fold'},
      h('summary', {text: `Business advice removed by the screen (${removedAdvice.length})`}),
      bullets(agentic.business_screening.filter(item => item.status !== 'kept_unverified').map(item => `${item.text || item.implication || item.risks || ''} — ${Object.entries(item.issues || {}).map(([field, found]) => `${field.replace(/_/g, ' ')}: ${found.join(', ').replace(/_/g, ' ')}`).join('; ')}`))) : null;
    const roundNote = agentic.selected_round ? ` The answer uses round ${agentic.selected_round} only: its claims, its ${(agentic.evidence_ids || []).length} passages and its limitations.` : '';
    const abstained = agentic.abstention ? ` No answer was given because ${ABSTENTION_TEXT[agentic.abstention] || agentic.abstention}.` : '';
    return block('agents', 'Agents', 'How this answer was produced', number,
      h('p', {class: 'block-intro', text: `Experimental multi-agent mode. ${agentic.agents_run.map(name => AGENT_NAMES[name] || name).join(', ')} ran. `
        + `${calls.used} of up to ${calls.limit} model calls (${byAgent || 'none'}), ${Number(agentic.seconds).toFixed(1)} s.${roundNote}${abstained} `
        + 'Only claims that passed both the checks in code and the verification agent are shown as findings. A person still has to review them.'}),
      steps, verdicts, screened);
  }

  function block(key, nav, title, number, ...children) {
    return h('section', {class: `block block-${key}`, id: `a${number}-${key}`, 'data-nav': nav, 'data-group': BLOCK_GROUPS[key]?.[0],
      'aria-labelledby': `a${number}-${key}-h`},
      blockKicker(key), h('h2', {class: 'block-title', id: `a${number}-${key}-h`, tabIndex: -1, text: title}), children);
  }
  function evidenceMix(result) {
    const evidence = result.evidence || [];
    const papers = new Set(evidence.map(p => p.arxiv_id || p.title)).size;
    const tableKeys = new Set(evidence.filter(p => p.representation === 'linearized_table').map(p => `${p.arxiv_id}#${p.table_id}`));
    const rows = evidence.filter(p => p.representation === 'linearized_table').length;
    const text = evidence.length - rows;
    const parts = [`${papers} paper${papers === 1 ? '' : 's'}`];
    if (tableKeys.size) parts.push(`${tableKeys.size} table${tableKeys.size === 1 ? '' : 's'} (${rows} row${rows === 1 ? '' : 's'})`);
    if (text) parts.push(`${text} text passage${text === 1 ? '' : 's'}`);
    return parts.join(', ');
  }
  function provenanceLabel(demo) {
    if (window.MOCK_API === true) return 'Prototype mock data, not research output';
    if (demo.library?.replayed) {
      const created = demo.library.version?.created_at ? ` from ${when(demo.library.version.created_at)}` : '';
      return `Saved research snapshot${created}, opened without a model call`;
    }
    if (!isReal(demo)) return 'Synthetic example';
    return isSynthesis(demo) ? 'Live research answer' : 'Saved research result';
  }

  /* ---------- Brief rendering: one answer, three views (research-publication layout, 2026-11-26) ----------
     Answer: the recorded lead and findings as prose, a chart beside the finding that cites its table,
     requested implications, then one compact "Research notes" disclosure. Sources: grouped by paper.
     Evidence: statements with their exact quotes, source tables, comparisons, every check and the
     review, and developer diagnostics last. The page only arranges recorded fields: it never writes,
     rewords or summarises research text, and every safeguard below is the same data as before. */
  const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
  const paperKey = passage => passage.arxiv_id || passage.title || 'unknown';
  const sectionTitle = title => { const head = String(title || 'Untitled source').split(/\s[·:–—]\s|:\s/)[0].trim(); return head.length <= 64 ? head : `${head.slice(0, 62)}…`; };
  function claimPaper(claim, evidence) {
    const keys = new Set((claim.chunk_ids || []).map(id => evidence.find(p => p.chunk_id === id)).filter(Boolean).map(paperKey));
    return keys.size === 1 ? [...keys][0] : null;
  }
  /* Long answers that move between papers read better in sections. Consecutive findings from the same
     paper form one section (headed by that paper's own title); the order of findings never changes,
     and when the runs are short or interleaved the answer stays plain paragraphs. */
  function paperSections(claims, evidence) {
    if (claims.length < 5) return null;
    const runs = [];
    for (const claim of claims) {
      const key = claimPaper(claim, evidence);
      const last = runs.at(-1);
      if (last && (last.key === key || key === null)) last.claims.push(claim);
      else runs.push({key, claims: [claim]});
    }
    if (runs.length < 2 || runs.length > 4 || runs.some(run => !run.key || run.claims.length < 2)) return null;
    return runs;
  }
  function kindOf(passage) {
    return passage.representation === 'linearized_table' ? 'Table row' : passage.source === 'pdf' ? 'PDF text' : 'Text passage';
  }
  function whereOf(passage) {
    return passage.representation === 'linearized_table'
      ? [(passage.caption || '').split(/[:.]/)[0].trim() || 'Table', passage.row_label].filter(Boolean).join(' · ')
      : sourceLocation(passage);
  }

  function renderBrief(demo, number, answer, tools) {
    const result = demo.result, summary = result.summary, insight = result.business_insight, view = demo.plain_language;
    const evidence = result.evidence || [];
    const ctx = {demo, number, technical: [...(answer.runDetails || [])]};
    // The question as the person typed it (the server may store a reworded query without "chart").
    const askedQuery = $('.question', answer.closest('.turn') || document.createElement('i'))?.textContent
      || result.request?.query || demo.submitted_request?.query || '';
    ctx.question = () => askedQuery;
    ctx.autoChart = (table, plan) => EM.chartIntent(askedQuery) && summary.status === 'ok' && plan.eligible
      && table.completeness === 'complete_from_index' && table.rows.some(row => row.citedBy.length);
    ctx.takeaway = table => EM.takeawayFor(table, result);
    const tables = EM.buildTables(result);
    const studies = EM.studies(result);
    const checks = EM.verificationItems(demo, tables);
    const cites = EM.citationMap(result);
    const body = h('div', {class: 'brief'});
    const pane = (key, label) => h('section', {class: `brief-pane pane-${key}`, 'data-pane': key, 'aria-label': label, hidden: key !== 'answer'});
    const paneAnswer = pane('answer', 'Answer'), paneSources = pane('sources', 'Sources'),
      paneEvidence = pane('evidence', 'Evidence'), paneWorkspace = pane('workspace', 'Workspace');
    body.append(paneAnswer, paneSources, paneEvidence, paneWorkspace);
    const stage = demo.error?.stage;
    const tableAnchor = table => `#a${number}-tbl-${table.table_id.replace(/[^A-Za-z0-9]/g, '-')}`;

    /* Research notes are collected while the answer is built and shown in Workspace. */
    const notes = {coverage: [], limits: [], business: [], other: []};
    const openWorkspace = section => { setTab('workspace', {scroll: true}); selectWorkspace(section, true); };
    /* Answer caveats: only what is specifically missing or in conflict, said once, near the answer. */
    const asides = h('div', {class: 'answer-asides'});
    const aside = (content, tone = 'warn') => {
      const line = h('p', {class: `aside-line ${tone}`}, icon(tone === 'info' ? 'info' : 'alert'),
        h('span', null, typeof content === 'string' ? h('span', {text: content}) : content));
      asides.append(line);
      return line;
    };

    if (window.MOCK_API === true) paneAnswer.append(h('p', {class: 'mock-stamp', role: 'note'}, icon('info'),
      h('span', {text: 'Mock data for interface testing. Papers, numbers and tables are invented and are not research output.'})));

    /* Quiet source line: the lead paper and the retrieved passage count; opens Sources. */
    const citedPapers = studies.filter(study => study.citations.length);
    if (evidence.length) {
      const lead = (citedPapers.length ? citedPapers : studies);
      paneAnswer.append(h('p', {class: 'answer-source-line'},
        h('button', {type: 'button', class: 'paper-chip', title: lead[0].title, 'aria-label': `Sources: ${lead[0].title}. Open Sources for this answer.`,
          onclick: () => setTab('sources', {focus: true})}, icon('layers'), h('span', {text: sectionTitle(lead[0].title)})),
        lead.length > 1 ? h('span', {class: 'source-more', text: `+${plural(lead.length - 1, 'paper')}`}) : null,
        h('span', {class: 'source-count', text: `${plural(evidence.length, 'passage')} retrieved`})));
    }

    /* ---- The answer ---- */
    const claims = summary.claims.filter(claim => claim.kind !== 'interpretation');
    const interpretations = summary.claims.filter(claim => claim.kind === 'interpretation');
    const abstained = summary.status !== 'ok';
    const partial = summary.answer_scope === 'partial';
    const scoped = isSynthesis(demo) && summary.limitation_support?.length ? summary.limitation_support : null;
    const gapItems = (summary.limitation_support || []).filter(item => item.kind === 'coverage_gap');
    // answer_lead is a coverage note in every pipeline that sets it (answer_quality, evidence_led,
    // consolidated publication, S3, agentic, completion). It is uncited, so it is a caveat, never the opening.
    const coverageNote = !abstained && summary.answer_lead ? String(summary.answer_lead).trim() : null;
    const held = Array.isArray(summary.held_claims) ? summary.held_claims : [];

    const prose = h('div', {class: 'prose', id: `a${number}-summary`});
    const claimNodes = [];
    const span = claim => {
      const node = emphasizeQuantities(cited('span', claim, demo, number, 'claim'));
      claimNodes.push({claim, index: summary.claims.indexOf(claim), node});
      return node;
    };
    const para = group => { const p = h('p'); group.forEach((claim, i) => { if (i) p.append(' '); p.append(span(claim)); }); return p; };
    if (abstained) {
      prose.append(h('p', {class: 'lead', text: evidence.length
        ? 'The retrieved evidence does not support an answer to this question.'
        : 'No passages were found for this question, so no answer was written.'}));
      const plain = scoped ? [] : (summary.limitations || []);
      if (scoped || plain.length) {
        prose.append(h('h3', {class: 'prose-h', text: 'Why there is no answer'}),
          h('ul', {class: 'prose-list'}, scoped ? scoped.map(item => cited('li', item, demo, number)) : plain.map(text => h('li', {math: text}))));
      }
    } else {
      // The direct finding first, then short supporting paragraphs (at most three findings each), in recorded order.
      const sections = paperSections(claims, evidence);
      if (sections) {
        for (const run of sections) {
          const title = evidence.find(p => paperKey(p) === run.key)?.title || '';
          prose.append(h('h3', {class: 'prose-h', title, text: sectionTitle(title)}));
          paragraphs(run.claims).forEach(group => prose.append(para(group)));
        }
      } else if (claims.length) {
        prose.append(para([claims[0]]));
        paragraphs(claims.slice(1)).forEach(group => prose.append(para(group)));
      }
      prose.querySelector('p')?.classList.add('lead');
      for (const item of interpretations) {
        prose.append(h('p', {class: 'interpretation'}, h('span', {class: 'label', text: 'Interpretation'}),
          cited('span', item, demo, number, 'claim')));
      }
    }
    paneAnswer.append(prose, asides);

    // Plain-language view (findings only).
    const plainFallback = h('p', {class: 'aside-line info', hidden: true});
    asides.append(plainFallback);
    function selectView() {
      closePreview();
      const plain = document.documentElement.dataset.readingExplanation === 'plain';
      for (const entry of claimNodes) {
        const rewrite = plain && view?.status === 'available' ? view.claims[entry.index] : null;
        const node = emphasizeQuantities(cited('span', rewrite ? {...entry.claim, text: rewrite.text, support: rewrite.support} : entry.claim, demo, number, 'claim'));
        if (rewrite) node.classList.add('rewritten');
        entry.node.replaceWith(node); entry.node = node;
      }
      prose.classList.toggle('plain', plain && view?.status === 'available');
      const unavailable = plain && view?.status !== 'available' && claimNodes.length;
      plainFallback.hidden = !unavailable;
      plainFallback.textContent = unavailable ? `Plain language is not available for this answer. ${view?.reason || 'The original wording is shown.'}` : '';
    }
    explanationRenderers.set(answer, selectView);
    selectView();

    /* What is missing, once, only when the answer records what it is. */
    const gap = coverageNote || gapItems[0]?.text || null;
    if (gap) aside(h('span', null, h('strong', {text: partial ? 'Partial answer. ' : 'Note. '}), h('span', {math: gap})));
    const numberChecks = result.provenance?.agentic?.claims_needing_number_check || [];
    if (numberChecks.length) {
      aside(`Check the numbers in ${plural(numberChecks.length, 'finding')}: code could not confirm what they refer to.`);
      notes.other.push(...numberChecks);
    }
    if (demo.error && !['business', 'regulatory'].includes(stage)) aside(demo.error.message || String(demo.error), 'bad');
    if (stage === 'business') {
      aside('Business implications could not be generated. The research answer above is unaffected.');
      notes.other.push(`Business translation: ${demo.error.message || 'failed'}`);
    }
    if (stage === 'regulatory') {
      aside('The risk and compliance assessment did not complete. No regulatory conclusion exists; the research answer is unaffected.');
      notes.other.push(`Risk & compliance: ${demo.error.message || 'failed'}`);
    }

    /* Search and selection notes (same wording as before). */
    const search = result.provenance?.arxiv_search;
    const searchMessages = {
      answered: ['arXiv search completed. Open the citations to see the papers found for this question.', ''],
      insufficient_evidence: ['arXiv search completed. The papers examined did not provide enough evidence.', 'warn'],
      unreadable: ['arXiv found papers, but the app could not extract readable text. The library result is shown. Retry the question or rephrase it.', 'warn'],
      timeout: ['The arXiv search timed out. The library result is shown. Retry the question or rephrase it.', 'warn'],
      failed: ['The arXiv search could not finish. The library result is shown. Retry the question or rephrase it.', 'warn'],
      answer_failed: ['arXiv returned papers, but the app could not validate an answer. The library result is shown. Retry the question or rephrase it.', 'warn'],
    };
    if (search && searchMessages[search.status]) {
      notes.other.push(searchMessages[search.status][0]);
      if (searchMessages[search.status][1] === 'warn') aside(searchMessages[search.status][0]);
    } else if (result.provenance?.arxiv_fallback_enabled) notes.other.push('Sources come from the loaded library.');
    if (result.provenance?.evidence_selection_result?.status === 'selection_failed_baseline_retained') {
      notes.other.push('The question coverage check was unavailable. This answer uses the original source ranking; review its citations and limitations.');
    }

    /* Limitations: cited where the answer cites them; coverage gaps separately. */
    if (!abstained) {
      const shownText = new Set();
      for (const item of scoped || []) {
        shownText.add(String(item.text).trim());
        if (item.kind === 'coverage_gap') notes.coverage.push(item.text);
        else notes.limits.push(item);
      }
      for (const text of summary.limitations || []) {
        const key = String(text).trim();
        if (shownText.has(key)) continue;
        shownText.add(key);
        if (coverageNote && key === coverageNote) notes.coverage.push(text);
        else notes.limits.push(text);
      }
      // The missing information itself is stated once, in the Completeness card; the list keeps only other gaps.
      notes.coverage = notes.coverage.filter(text => String(text).trim() !== coverageNote);
      if (held.length) {
        const reasons = [...new Set(held.flatMap(item => item.reasons || []))];
        notes.coverage.push(`${plural(held.length, 'drafted statement')} ${held.length === 1 ? 'was' : 'were'} withheld by the verification gates${reasons.length ? ` (${reasons.join('; ')})` : ''}.`);
      }
      for (const text of summary.evidence_notes || []) notes.other.push(text);
    }
    if (new Set(evidence.map(paperKey)).size === 1 && summary.status === 'ok') notes.other.push('The answer rests on a single paper.');
    if (tables.some(t => !t.headerStatus.verified) && tables.some(t => t.rows.some(r => r.citedBy.length))) {
      notes.other.push('Table column headings were read automatically; compare them with the paper before quoting numbers.');
    }
    if (insight) {
      for (const risk of insight.risks || []) notes.business.push({text: risk, label: 'Risk'});
      for (const limit of insight.limitations || []) notes.business.push({text: limit, label: 'Limit'});
    }

    /* ---- Actions right below the response ---- */
    const review = humanReview(demo);
    const quoteChecked = isSynthesis(demo) || Boolean(summary.support_check);
    const actions = h('div', {class: 'answer-actions', role: 'group', 'aria-label': 'Answer actions'},
      demo.library
        ? h('button', {type: 'button', class: 'act-btn', onclick: () => openWorkspace('review')}, icon('check'), h('span', {text: 'Saved'}), h('span', {class: 'act-sub', text: '· Review'}))
        : h('button', {type: 'button', class: 'act-btn', onclick: () => tools.reveal('brief')}, icon('bookmark'), h('span', {text: 'Save'})),
      h('details', {class: 'export-menu'},
        h('summary', {class: 'act-btn'}, icon('download'), h('span', {text: 'Export'})),
        h('div', {class: 'export-pop'}, exportControls(demo, number), snapshotButton(demo),
          h('p', {class: 'export-note', text: `Exports contain the answer as generated and its sources, not the review record. Current review: ${review.short}.`}))),
      tools.listenButton,
      evidence.length ? h('button', {type: 'button', class: 'act-btn', onclick: () => setTab('sources', {focus: true})}, icon('layers'), h('span', {text: 'Sources'})) : null,
      insight?.implications?.length ? h('button', {type: 'button', class: 'act-btn act-quiet', onclick: () => openWorkspace('business')}, icon('bulb'), h('span', {text: 'Business insight'})) : null,
      view?.status === 'available' && claimNodes.length ? h('div', {class: 'act-switch'}, h('span', {id: `a${number}-explain-label`, class: 'sr-only', text: 'Explanation style'}), explanationSwitch(`a${number}-explain-label`)) : null);
    paneAnswer.append(actions, tools.listenPanel);

    /* Slim line: research notes and the real review status; opens Workspace. */
    const noteCount = h('span', {class: 'strip-count'});
    paneAnswer.append(h('button', {type: 'button', class: 'answer-note-strip', onclick: () => openWorkspace('notes')},
      h('span', {class: 'strip-title'}, icon('info'), h('span', {text: 'Research notes'})),
      h('span', {class: 'facet'}, icon(quoteChecked ? 'check' : 'info'), h('span', {text: quoteChecked ? 'Quotes matched' : 'Quote check not recorded'})),
      abstained ? h('span', {class: 'facet warn'}, icon('alert'), h('span', {text: 'No answer'})) : partial ? h('span', {class: 'facet warn'}, icon('alert'), h('span', {text: 'Partial'})) : null,
      h('span', {class: `facet ${review.tone === 'ok' ? 'ok' : review.tone === 'bad' ? 'bad' : ''}`}, icon(review.tone === 'ok' ? 'check' : 'shield'),
        h('span', {text: review.tone === 'draft' ? (demo.library ? 'Not reviewed by a person' : 'Not saved or reviewed') : review.short})),
      noteCount, icon('chevron')));

    /* ---- Workspace: Business insight / Research notes / Review ---- */
    const wsTabs = h('div', {class: 'ws-tabs', role: 'tablist', 'aria-label': 'Workspace sections'});
    const wsBody = h('div', {class: 'ws-panel-wrap'});
    const wsSections = [];
    function wsSection(key, label) {
      const panel = h('section', {class: 'ws-panel', id: `a${number}-ws-${key}`, role: 'tabpanel', 'aria-label': label, hidden: true});
      const button = h('button', {type: 'button', role: 'tab', class: 'ws-tab', 'aria-selected': 'false', 'aria-controls': panel.id, onclick: () => selectWorkspace(key, true)}, h('span', {text: label}));
      wsSections.push({key, panel, button});
      wsTabs.append(button); wsBody.append(panel);
      return panel;
    }
    function selectWorkspace(key, focus = false) {
      for (const s of wsSections) {
        const on = s.key === key;
        s.panel.hidden = !on; s.button.setAttribute('aria-selected', String(on)); s.button.tabIndex = on ? 0 : -1;
        if (on && focus) s.button.focus({preventScroll: true});
      }
    }
    wsTabs.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
      const i = wsSections.findIndex(s => s.button === document.activeElement);
      const next = wsSections[(i + (event.key === 'ArrowRight' ? 1 : wsSections.length - 1)) % wsSections.length];
      selectWorkspace(next.key, true);
    });
    paneWorkspace.append(h('header', {class: 'pane-head'}, h('h2', {class: 'pane-title', id: `a${number}-workspace`, tabIndex: -1, text: 'Workspace'})), wsTabs, wsBody);

    // Business insight: one interpretation tied to the industry and its cited finding; the action beside it.
    if (insight) {
      const panel = wsSection('business', 'Business insight');
      panel.append(h('p', {class: 'ws-kicker', text: `Industry: ${insight.industry} · an interpretation for business use, not something the paper measured`}));
      if (result.provenance?.agentic) {
        const dropped = (result.provenance.agentic.business_screening || []).filter(item => item.status === 'removed').length;
        panel.append(h('p', {class: 'aside-line warn'}, icon('alert'), h('span', {text: `Drafted by the business insight agent and not checked by the verification agent or a person. ${plural(dropped, 'unsupported statement')} ${dropped === 1 ? 'was' : 'were'} withheld.`})));
      }
      if (!insight.implications.length) panel.append(h('p', {class: 'muted', text: 'No supported business implications.'}));
      const more = h('details', {class: 'fold more-insights'}, h('summary', {text: `More interpretations (${Math.max(0, insight.implications.length - 1)})`}));
      insight.implications.forEach((implication, i) => {
        (i ? more : panel).append(h('article', {class: 'insight-card'},
          h('div', {class: 'insight-main'}, h('h3', {class: 'ws-h', text: 'Interpretation'}), cited('p', implication, demo, number, 'insight-text')),
          implication.suggested_action ? h('div', {class: 'insight-action'}, h('h3', {class: 'ws-h', text: 'Suggested action'}), h('p', {math: implication.suggested_action})) : null,
          implication.assumptions?.length ? h('details', {class: 'fold insight-assumptions'}, h('summary', {text: `Assumptions (${implication.assumptions.length})`}), bullets(implication.assumptions)) : null));
      });
      if (insight.implications.length > 1) panel.append(more);
      const checkpoint = result.regulatory_checkpoint;
      if (checkpoint) {
        const assessed = checkpoint.status === 'assessed';
        const reg = h('section', {class: 'ws-group', id: `a${number}-regulatory`}, h('h3', {class: 'ws-h', text: 'Risk and compliance (advisory)'}),
          h('p', {class: 'section-note', text: `${assessed ? 'Assessed' : `Assessment ${checkpoint.status}`}. Not legal advice or compliance approval; a person must review it.`}));
        if (assessed && checkpoint.assessment) {
          reg.append(h('p', {math: checkpoint.summary || ''}));
          const grid = h('div', {class: 'two-col'});
          for (const [key, title] of [['regulatory_compliance', 'Regulatory compliance'], ['legal_constraints', 'Legal constraints'],
            ['governance', 'Governance'], ['operational_feasibility', 'Operational feasibility']]) {
            const finding = checkpoint.assessment[key];
            if (finding) grid.append(h('div', {class: 'col'}, h('h4', {text: `${title} · ${finding.status}`}), h('p', {math: finding.explanation || ''})));
          }
          reg.append(grid);
          if (checkpoint.assessment.risks?.length) reg.append(bullets(checkpoint.assessment.risks));
        } else reg.append(h('p', {class: 'aside-line warn'}, icon('alert'), h('span', {text: `No regulatory conclusion was produced: ${checkpoint.reason || 'no assessment was returned.'}`})));
        panel.append(reg);
      }
    }

    // Research notes: discrepancies first, then what was checked, then risks and limits.
    const notesPanel = wsSection('notes', 'Research notes');
    const discrepancyList = h('ul', {class: 'notes-list'});
    const discrepancyBox = h('section', {class: 'discrepancy-box', hidden: true}, h('h3', {class: 'ws-h', text: 'Unresolved discrepancies'}), discrepancyList);
    const support = result.provenance?.agentic
      ? 'Each claim was re-checked in code and judged by a separate verification agent (a model). No person has checked support.'
      : summary.quality_review ? 'A model reviewed whether each quote supports its claim. No person has checked this.'
        : quoteChecked ? 'Not checked. A matching quote shows the words are in the paper, not that they support the claim.'
          : 'Not recorded for this saved result.';
    const completeness = abstained ? 'No answer: the retrieved evidence did not support one.'
      : partial ? (gap ? `Partial. Missing: ${gap}` : 'Partial. The review marked the answer as incomplete.')
        : summary.answer_scope === 'full' ? 'The automated review judged that the answer covers the question.' : 'Not assessed for this answer.';
    const card = (title, text, tone = '') => h('article', {class: `check-card ${tone}`}, h('h3', {class: 'ws-h', text: title}), h('p', {text}));
    const group = (title, items) => items.length ? h('section', {class: 'ws-group'}, h('h3', {class: 'ws-h', text: title}),
      h('ul', {class: 'notes-list'}, items.map(item => typeof item === 'string' ? h('li', {math: item}) : item.chunk_ids ? cited('li', item, demo, number)
        : h('li', null, item.label ? h('span', {class: 'li-label', text: `${item.label}. `}) : null, h('span', {math: item.text}))))) : null;
    notesPanel.append(discrepancyBox,
      h('div', {class: 'check-grid'},
        card('Quotations', quoteChecked ? 'Every quote attached to a statement was found word-for-word in its source paper. This does not show that the quote supports the statement.' : 'This saved result does not record a quote check.'),
        card('Claim support', support),
        card('Completeness', completeness, partial || abstained ? 'warn' : ''),
        card('Human approval', review.long, review.tone === 'ok' ? 'ok' : '')),
      group('What the answer does not cover', notes.coverage),
      group('Limitations of the evidence', notes.limits),
      group(insight ? `Risks and limits of the ${insight.industry} insight` : 'Business risks', notes.business),
      group('Other notes', notes.other),
      h('button', {type: 'button', class: 'quiet-btn ws-jump', onclick: () => selectWorkspace('review', true)}, icon('shield'), h('span', {text: 'Review checks'})));
    const countNotes = () => {
      const n = notesPanel.querySelectorAll('.notes-list > li').length;
      noteCount.textContent = n ? plural(n, 'note') : '';
    };
    countNotes();

    // Review: the saved brief's actual status and what a person needs to check.
    const reviewPanel = wsSection('review', 'Review');
    const checklist = h('ol', {class: 'checklist'}, checks.map(item => h('li', null, h('span', {class: 'box', 'aria-hidden': 'true'}),
      h('div', null, h('p', {text: item.text}), h('details', {class: 'origin-fold'}, h('summary', {text: 'Check origin'}), h('p', {class: 'origin', text: item.origin}))))));
    reviewPanel.append(h('section', {class: 'ws-group', id: `a${number}-verify`},
      h('div', {class: 'review-status'}, h('span', {class: `state ${reviewTone(demo)}`}, icon('shield'), h('span', {text: reviewText(demo)})),
        demo.library
          ? h('button', {type: 'button', class: 'solid-btn', onclick: () => tools.reveal('brief')}, icon('shield'), h('span', {text: 'Record a review'}))
          : h('button', {type: 'button', class: 'solid-btn', onclick: () => tools.reveal('brief')}, icon('bookmark'), h('span', {text: 'Save as brief to review'}))),
      h('p', {class: 'section-note', text: demo.library
        ? 'Saving, quote matching and automated checks are not human approval. Approval applies only to this saved version.'
        : 'Save this draft as a brief first; reviews attach to a saved version.'}),
      h('h3', {class: 'ws-h', text: 'Checks before relying on this answer'}), checklist,
      h('p', {class: 'section-note', text: `Exports do not include the review record. Compare an exported file with saved version ${demo.library?.version?.number ?? '—'} before claiming it was approved.`})));
    selectWorkspace(insight ? 'business' : 'notes');

    /* A table-level count check: one actionable link near the answer; details in Research notes and Evidence. */
    let discrepancyAside = null;
    ctx.addCaveat = (content, table) => {
      discrepancyList.append(typeof content === 'string' ? h('li', {text: content}) : h('li', null, content));
      discrepancyBox.hidden = false;
      countNotes();
      if (!discrepancyAside) discrepancyAside = aside(h('button', {type: 'button', class: 'inline-link',
        onclick: () => table ? openTo(tableAnchor(table)) : openWorkspace('notes')}, h('span', {text: 'Check model count'})));
      refreshIssues(number);
    };
    const reviewIssues = new Set();
    ctx.onReviewIssue = (table, issue) => {
      const key = `${table.key}|${issue.phrase}`;
      if (reviewIssues.has(key)) return;
      reviewIssues.add(key);
      checklist.append(h('li', {class: 'review-issue'}, h('span', {class: 'box', 'aria-hidden': 'true'}),
        h('div', null, h('p', {text: `${tableTitle(table)} (${table.paper_title}): ${issue.text}`}),
          h('details', {class: 'origin-fold'}, h('summary', {text: 'Check origin'}), h('p', {class: 'origin', text: 'Count check: answer claim vs. complete table'})))));
      const quoted = summary.claims.some(claim => (claim.support || []).some(s => (s.quote || '').includes(issue.phrase)));
      ctx.addCaveat(h('span', {text: `${quoted ? 'The cited passage of the paper reports' : 'The answer states'} “${issue.phrase}”, but ${tableTitle(table)} of the same paper lists ${issue.distinct} models. The evidence does not settle which is right; confirm which models the figure covers before quoting it.`}), table);
      setCheckCount(body, checklist.children.length);
    };

    /* ---- Sources: grouped by paper, cited passages first, other retrieved passages folded ---- */
    const statementCount = passage => [summary.claims, summary.limitation_support, insight?.implications]
      .flatMap(list => list || []).filter(item => item.chunk_ids?.includes(passage.chunk_id)).length;
    const citedTotal = evidence.filter(p => cites.has(p.chunk_id)).length;
    paneSources.append(h('header', {class: 'pane-head'},
      h('h2', {class: 'pane-title', id: `a${number}-sources`, tabIndex: -1, text: 'Sources'}),
      h('p', {class: 'pane-sub', text: evidence.length ? `${plural(studies.length, 'paper')} · ${plural(citedTotal, 'cited passage')}` : 'No passages were retrieved for this question.'})));
    const settingOf = passage => (passage.table_cells || []).slice(1).map(c => c.text).find(text => text && !EM.parseNumber(text)) || null;
    const sourceRow = index => {
      const passage = evidence[index];
      const count = statementCount(passage);
      const where = passage.representation === 'linearized_table'
        ? [(passage.caption || '').split(/[:.]/)[0].trim() || 'Table', passage.row_label, settingOf(passage)].filter(Boolean).join(' · ')
        : sourceLocation(passage);
      const open = h('button', {type: 'button', class: 'source-row', 'aria-label': `Open source ${index + 1}, ${citationSourceContext(passage)}`,
        onclick: () => showEvidence(demo, number, index, open)},
        h('span', {class: 'cite-num', text: String(index + 1)}),
        h('span', {class: 'row-where'}, texText(h('span', {class: 'row-loc'}), where), h('span', {class: 'row-kind', text: kindOf(passage)})),
        h('span', {class: `row-use ${count ? 'is-cited' : ''}`, text: count ? `Cited by ${plural(count, 'statement')}` : 'Retrieved, not cited'}));
      open.dataset.passage = index;
      return h('li', null, open);
    };
    const orderedStudies = [...studies].sort((a, b) => (b.citations.length ? 1 : 0) - (a.citations.length ? 1 : 0));
    for (const study of orderedStudies) {
      const link = /^https?:\/\//.test(study.html_url || '') ? study.html_url : null;
      const indices = study.passages.map(n => n - 1);
      const citedRows = indices.filter(i => statementCount(evidence[i]) > 0);
      const otherRows = indices.filter(i => !citedRows.includes(i));
      paneSources.append(h('article', {class: `source-paper${citedRows.length ? ' is-cited' : ''}`},
        h('header', {class: 'paper-head'},
          h('h3', {class: 'paper-name', text: study.title || 'Untitled source'}),
          h('p', {class: 'paper-meta'}, study.arxiv_id ? h('span', {class: 'paper-id', text: `arXiv ${study.arxiv_id}`}) : null,
            link ? h('a', {href: link, target: '_blank', rel: 'noopener noreferrer'}, h('span', {text: 'Open paper'}), icon('external')) : null)),
        citedRows.length ? h('ol', {class: 'source-rows'}, citedRows.map(sourceRow)) : null,
        otherRows.length ? h('details', {class: 'fold other-sources'}, h('summary', {text: `Other retrieved passages (${otherRows.length})`}),
          h('ol', {class: 'source-rows'}, otherRows.map(sourceRow))) : null));
    }

    /* ---- Evidence: source tables first, then the comparison and the statements behind the answer ---- */
    paneEvidence.append(h('header', {class: 'pane-head'}, h('h2', {class: 'pane-title', id: `a${number}-evidence`, tabIndex: -1, text: 'Evidence'})));
    if (tables.length) {
      paneEvidence.append(h('section', {class: 'ev-section block-numbers', id: `a${number}-numbers`, 'aria-labelledby': `a${number}-numbers-h`},
        h('h2', {class: 'section-h', id: `a${number}-numbers-h`, tabIndex: -1, text: 'Source tables'}),
        tables.map(table => renderEvidenceTable(table, ctx))));
    }
    const named = studies.length >= 2 ? EM.namedStudies(studies, ctx.question()) : [];
    if (named.length >= 2) {
      paneEvidence.append(h('section', {class: 'ev-section', id: `a${number}-compare`},
        h('h2', {class: 'section-h', text: named.map(study => sectionTitle(study.title)).join(' and ')}), focusedComparison(named, studies, ctx)));
    } else if (studies.length >= 2) {
      paneEvidence.append(h('section', {class: 'ev-section', id: `a${number}-compare-all`},
        h('h2', {class: 'section-h', text: 'What each paper covers'}), renderStudies(studies, ctx)));
    }
    const quotesFor = item => {
      const quotes = (item.support || []).filter(s => s.quote);
      if (!quotes.length) return h('p', {class: 'quote-missing', text: 'Cited without a recorded quote. Read the passage to judge the support.'});
      return quotes.map(s => {
        const index = evidence.findIndex(p => p.chunk_id === s.chunk_id);
        const passage = evidence[index];
        const open = passage ? h('button', {type: 'button', class: 'quote-src', onclick: () => showEvidence(demo, number, index, open, item)},
          h('span', {class: 'cite-num', text: String(index + 1)}), h('span', {text: `${sectionTitle(passage.title)} · ${whereOf(passage)}`})) : null;
        return h('figure', {class: 'quote'}, h('blockquote', {math: s.quote}), open && h('figcaption', null, open));
      });
    };
    const statementItems = [...claims.map(c => [c, 'Finding']), ...interpretations.map(c => [c, 'Interpretation']),
      ...(scoped || []).filter(item => item.kind !== 'coverage_gap' && (item.chunk_ids || []).length).map(c => [c, 'Limitation']),
      ...(insight?.implications || []).map(c => [c, 'Implication'])];
    if (statementItems.length) {
      paneEvidence.append(h('section', {class: 'ev-section', id: `a${number}-claims`},
        h('h2', {class: 'section-h', text: 'Statements and their quotes'}),
        h('ol', {class: 'statements'}, statementItems.map(([item, label]) => h('li', {class: 'statement'},
          h('p', {class: 'statement-kind', text: label}), cited('p', item, demo, number, 'statement-text'), quotesFor(item))))));
    }
    if (view?.status === 'available') {
      const definitions = h('details', {class: 'fold'}, h('summary', {text: 'Term definitions and plain-language details'}));
      for (const definition of view.definitions) {
        definitions.append(h('div', {class: 'definition'}, h('p', {class: 'term', text: definition.term}),
          definition.status === 'supported' ? cited('p', definition, demo, number) : h('p', {class: 'muted', text: `Definition unavailable: ${definition.reason}`})));
      }
      definitions.append(h('p', {class: 'muted small', text: `${view.fixture ? 'Synthetic fixture demonstration. ' : ''}Only research findings are rewritten; source passages stay unchanged.`}));
      paneEvidence.append(h('section', {class: 'ev-section'}, definitions));
    }
    const trust = [];
    if (isSynthesis(demo)) trust.push('Citation IDs and source quotes checked');
    if (summary.quality_review) trust.push('automated support and relevance review applied (model judgment)');
    if (result.provenance?.agentic) trust.push('each claim re-checked in code, then judged by a separate verification agent (model judgment)');
    if (trust.length) ctx.technical.push(`${trust.join('; ').replace(/^./, c => c.toUpperCase())}. Claim support has not been independently verified by a person.`);
    ctx.technical.push(provenanceLabel(demo));
    paneEvidence.append(h('details', {class: 'diagnostics', id: `a${number}-diagnostics`},
      h('summary', null, icon('code'), h('span', {text: 'Developer diagnostics'})),
      h('div', {class: 'diag-body'},
        h('ul', {class: 'bullets'}, ctx.technical.map(text => h('li', {text}))),
        result.provenance?.agentic ? agentTraceBlock(result.provenance.agentic, number) : null,
        search?.candidates?.length ? h('details', {class: 'fold'}, h('summary', {text: `Papers examined on arXiv (${search.candidates.length})`}),
          h('ul', {class: 'bullets'}, search.candidates.map(candidate => h('li', null, /^https?:\/\//.test(candidate.url || '')
            ? h('a', {href: candidate.url, target: '_blank', rel: 'noopener noreferrer', text: candidate.title || candidate.arxiv_id})
            : h('span', {text: candidate.title || candidate.arxiv_id}), h('span', {class: 'muted', text: ` · ${candidate.arxiv_id} · ${candidate.status}`}))))) : null,
        tools.diagnostics)));

    body.selectWorkspace = selectWorkspace;
    answer.append(body);
    return body;
  }
  document.addEventListener('reading-preferences-change', () => {
    for (const answer of document.querySelectorAll('.answer')) explanationRenderers.get(answer)?.();
  });

  /* ---------- Appendix tools (export, listen, run details) and the brief drawer ---------- */
  const reviewDrawer = $('#review-drawer'), reviewBody = $('#review-body');
  let reviewReturn = null;
  function setReview(open, trigger = null) {
    if (open && trigger) reviewReturn = trigger;
    if (open) setInspector(false);
    document.body.classList.toggle('review-open', open);
    reviewDrawer.inert = !open;
    if (!open) focusInitiator(reviewReturn);
  }
  $('#review-close').addEventListener('click', () => setReview(false));
  function openReview(demo, number, onChanged, trigger) {
    const panel = h('div', {class: 'review-panel', id: `a${number}-panel-brief`});
    briefPanel(panel, demo, onChanged, number);
    $('#review-heading').textContent = demo.library ? 'Brief and review' : 'Save this answer';
    $('#review-kicker').textContent = demo.library ? `Brief · version ${demo.library.version.number}` : 'Brief';
    reviewBody.replaceChildren(panel);
    reviewBody.scrollTop = 0;
    setReview(true, trigger);
    $('#review-heading').focus({preventScroll: true});
  }

  function answerTools(demo, number, answer, onChanged) {
    const real = isReal(demo);
    const listenPanel = h('div', {class: 'listen-panel', id: `a${number}-panel-listen`, hidden: true});
    let listenBuilt = false;
    const listenButton = h('button', {type: 'button', class: 'act-btn', 'aria-expanded': 'false', 'aria-controls': listenPanel.id}, icon('volume'), h('span', {text: 'Listen'}));
    listenButton.addEventListener('click', () => {
      const open = listenPanel.hidden;
      if (open && !listenBuilt) { ResearchSpeech.attach(listenPanel, ResearchSpeech.result(demo, number)); listenBuilt = true; }
      listenPanel.hidden = !open; listenButton.setAttribute('aria-expanded', String(open));
    });
    // Run details and the raw JSON are built only when the diagnostics fold is opened.
    const diagnostics = h('details', {class: 'fold'}, h('summary', {text: real ? 'Run details and result JSON' : 'Run details and demo JSON'}));
    diagnostics.addEventListener('toggle', () => {
      if (!diagnostics.open || diagnostics.dataset.built) return;
      diagnostics.dataset.built = '1';
      diagnostics.append(h('p', {text: `${real ? 'Executed query' : 'Fixed example'}: ${demo.result.request.query}`}),
        h('p', {class: 'muted', text: real ? runLabel(demo) : STATES[demo.scenario][1]}),
        !real ? h('p', {class: 'muted', text: `Your question (not executed): ${demo.submitted_request.query}`}) : null,
        h('pre', {class: 'json', tabIndex: 0, text: JSON.stringify(demo, null, 2)}));
    });
    const open = key => {
      if (key === 'brief') return openReview(demo, number, onChanged, document.activeElement);
      if (key === 'listen' && listenPanel.hidden) listenButton.click();
    };
    return {number, open, reveal: key => open(key), inspect: trigger => showEvidence(demo, number, 0, trigger), listenButton, listenPanel, diagnostics};
  }
  function snapshotButton(demo) {
    return btn('Export snapshot JSON', () => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(demo, null, 2)], {type: 'application/json'}));
      const link = h('a', {href: url, download: 'research-snapshot.json'}); document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, 'quiet-btn', 'download');
  }

  function renderDemo(demo, number, answer) {
    const [label, baseExplanation, tone] = STATES[demo.scenario] || STATES.full;
    const stage = demo.error?.stage;
    const explanation = demo.scenario === 'partial' && stage === 'business'
      ? 'The research summary is available, but generating business implications failed. Inspect the error and retry.'
      : demo.scenario === 'partial' && stage === 'regulatory'
        ? 'The research summary and business implications are available, but risk and compliance assessment failed. No regulatory conclusion was produced. Inspect the error and retry.'
        : demo.scenario === 'partial' && !demo.error ? 'The research summary is available. No business recommendation is supported by the evidence.' : baseExplanation;
    const seconds = demo.result?.provenance?.timings_seconds?.total;
    const turn = answer.closest('.turn');
    const label2 = $('.question-label', turn);
    const runDetails = [demo.library?.replayed ? 'Saved snapshot: no new research was run to show this answer.' : null,
      Number.isFinite(seconds) ? `Research took ${seconds.toFixed(1)} s.` : null,
      demo.mode === 'indexed' ? (demo.history_policy === 'server_owned_bounded_intent_only' ? 'Indexed research, bounded conversation.' : 'Indexed research, independent query.') : null,
      demo.result?.provenance?.arxiv_search ? 'arXiv fallback search was used.' : null].filter(Boolean);
    if (label2) {
      const plainLabel = /draft/i.test(label) && tone === 'ok' ? 'Draft answer' : label;
      // Review status lives under the answer; above the question only material warnings remain.
      void plainLabel;
      const chips = [demo.result?.provenance?.agentic ? h('span', {class: 'mode-label', text: 'Multi-agent research · Experimental'}) : null,
      ].filter(Boolean);
      label2.replaceChildren(...chips);
      label2.hidden = !chips.length;
    }
    answer.runDetails = runDetails;
    answer.replaceChildren(answerHeading(number));
    if (demo.result) {
      const onChanged = updated => {
        ResearchSpeech.stopAll();
        renderDemo(updated, number, answer);
        openReview(updated, number, onChanged, null);
        loadRecentBriefs();
      };
      const tools = answerTools(demo, number, answer, onChanged);
      const abstention = demo.result && demo.result.summary?.status !== 'ok';
      // Stage outcomes (a failed business or regulatory stage) are stated inside the brief where that
      // part would be; a feature that was not requested is not announced. (explanation/tone/abstention
      // remain for the screen-reader announcement below.)
      void explanation; void tone; void abstention;
      renderBrief(demo, number, answer, tools);
      turn.tools = tools;
      if (demo.library_error) openReview(demo, number, onChanged, null);
      turn.demoState = {demo, number};
      if (!turn.dataset.tab) turn.dataset.tab = 'answer';
      queueMicrotask(renderSidebar);
      if (turn === activeTurn) queueMicrotask(syncTopbar);
      if (turn === activeTurn) activeDemo = turn.demoState;
      if (document.body.classList.contains('insp-open') && turn === activeTurn) showEvidence(demo, number);
      $('#evidence-toggle').hidden = false;
      markAnswerReady(answer);
      announce(readyAnnouncement(demo, number), false);
      if (liveSynthesis && !demo.library?.replayed) refreshBudget();
      return tools;
    }
    answer.append(h('div', {class: 'block-failed'}, h('p', {class: 'lead-plain', text: 'No answer was produced.'}),
      h('p', {class: 'aside-line bad'}, icon('alert'), h('span', {text: demo.error?.message || String(demo.error || 'The research request did not return a result.')}))));
    markAnswerReady(answer);
    announce(readyAnnouncement(demo, number), false);
    return null;
  }

  /* ---------- Clarification ---------- */
  function archiveClarification(status) {
    if (!clarificationCard) return;
    const support = clarificationCard.supportDisclosure;
    clarificationCard.replaceWith(h('div', {class: 'clarified'}, icon('check'),
      h('p', {text: `${clarificationCard.dataset.question} · ${status}`}), support));
    if (support) support.open = false;
    clarificationCard = null;
  }
  function setClarificationPending(pending, status = 'Closed') {
    clarificationPending = pending;
    if (!pending) { activeClarificationTurn = null; archiveClarification(status); }
    if (!clarificationEnabled) return;
    dock.classList.toggle('awaiting-clarification', pending);
    $('.send-label').textContent = pending ? 'Send clarification' : 'Research';
  }
  function renderClarification(demo, number, answer) {
    archiveClarification('Answered');
    activeClarificationTurn = number;
    const token = researchConversationId;
    const current = () => clarificationPending && activeClarificationTurn === number && token === researchConversationId;
    const options = h('fieldset', {class: 'question-options'}, h('legend', {class: 'sr-only', text: 'Choose an answer'}));
    const free = h('textarea', {id: 'clarification-answer', class: 'question-free', rows: 1, maxLength: 2000, 'aria-label': 'Clarification answer',
      placeholder: demo.clarification.options.length ? 'Or type your own answer…' : 'Type your answer…'});
    const send = h('button', {type: 'button', class: 'solid-btn question-submit', disabled: true, onclick: () => {
      if (!current() || requestPending || !queryInput.value.trim()) return;
      form.requestSubmit();
    }}, h('span', {text: 'Submit answer'}), icon('up'));
    demo.clarification.options.forEach((option, index) => {
      const choice = h('input', {type: 'radio', name: `clarification-${number}`, value: option.text, onchange: () => {
        if (!current() || requestPending) return;
        free.value = ''; queryInput.value = option.text; send.disabled = false;
      }});
      options.append(h('label', {class: 'question-option'}, choice, h('span', {class: 'option-text', text: option.text}), h('kbd', {text: String(index + 1)})));
    });
    free.addEventListener('input', () => {
      if (!current() || requestPending) return;
      options.querySelectorAll('input').forEach(input => { input.checked = false; });
      queryInput.value = free.value; send.disabled = !free.value.trim();
    });
    const card = h('section', {class: 'question-card', 'aria-labelledby': 'clarification-prompt'},
      h('div', {class: 'question-card-head'}, h('p', {class: 'tag', text: 'Clarification needed'}), h('span', {class: 'muted small', text: '1 / 1'})),
      h('h3', {id: 'clarification-prompt', text: demo.clarification.question}),
      h('p', {class: 'muted', text: 'Choose a direction, or answer in your own words.'}));
    card.dataset.question = demo.clarification.question;
    card.addEventListener('keydown', event => {
      if (event.isComposing || requestPending || !current()) return;
      if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); send.click(); }
      else if (event.target !== free && !event.ctrlKey && !event.metaKey && !event.altKey && /^[1-9]$/.test(event.key)) {
        const choice = options.querySelectorAll('input')[Number(event.key) - 1];
        if (choice) { event.preventDefault(); choice.click(); choice.focus(); }
      }
    });
    if (demo.clarification.options.length) card.append(options);
    card.append(free);
    const footer = h('div', {class: 'question-card-foot'}, h('span', {class: 'muted small', text: 'Ctrl / ⌘ + Enter to submit'}));
    const supported = demo.clarification.options.filter(option => option.support.length);
    if (supported.length) {
      const evidence = h('details', {class: 'fold'}, h('summary', {text: 'Why these options?'}),
        h('p', {class: 'muted small', text: 'Exact source quotes; interpretations not independently verified.'}));
      for (const option of supported) {
        evidence.append(h('h4', {text: option.text}));
        for (const support of option.support) {
          const passage = demo.clarification_evidence.find(p => p.chunk_id === support.chunk_id);
          evidence.append(h('blockquote', {math: support.quote}));
          if (passage) {
            evidence.append(h('p', {class: 'muted small', text: citationSourceContext(passage)}));
            if (passage.source_url) evidence.append(h('a', {href: passage.source_url, target: '_blank', rel: 'noopener noreferrer', text: 'Open supporting source'}));
          }
        }
      }
      card.supportDisclosure = evidence;
      const inspect = btn('Why these options?', () => {
        if (!current()) return;
        closePreview(); activeDemo = null;
        inspectorChrome('Why these options?', 'Clarification', 'Source quotes explain these options; they do not independently verify the interpretations.');
        inspectorBody.replaceChildren(h('div', {class: 'why'}, Array.from(evidence.children).slice(1).map(node => node.cloneNode(true))));
        setInspector(true, inspect); inspectorHeading.focus({preventScroll: true});
      }, 'text-btn', 'layers');
      footer.prepend(inspect);
    }
    footer.append(send);
    card.append(footer);
    clarificationCard = card;
    answer.replaceChildren(answerHeading(number, 'Clarification'), card);
    markAnswerReady(answer);
    announce(`Reply needed: ${demo.clarification.question}`, false);
    card.scrollIntoView({block: 'nearest', behavior: reduced.matches ? 'auto' : 'smooth'});
    (options.querySelector('input') || free).focus({preventScroll: true});
  }

  /* ---------- Conversations ---------- */
  function clearRetries() { retryContext = null; document.querySelectorAll('.retry-question').forEach(button => button.remove()); }
  async function startResearchConversation() {
    if (requestPending) return false;
    if (!clarificationEnabled) {
      conversationHistory = []; finishRevision(); clearRetries();
      needsDivider = true; setQuery(''); suggestions.hidden = true; setView('home'); queryInput.focus();
      return true;
    }
    setQuestionBusy(true);
    try {
      const response = await fetch('/api/config', {signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error('Session unavailable');
      const config = await response.json();
      if (!config.clarification || !config.conversation_id) throw new Error('Session unavailable');
      researchConversationId = config.conversation_id;
      indexedContextId = config.context_id;
      finishRevision(); clearRetries();
      setClarificationPending(false);
      needsDivider = true; setQuery(''); suggestions.hidden = true;
      resetEvidence('New research conversation. Previous answers remain visible but are not conversation context.');
      setView('home'); queryInput.focus();
      announce('New research conversation. Previous answers, pending clarification and revision target will not be used.');
      return true;
    } catch {
      announce('Could not start a new conversation. Current question and session are unchanged; retry when ready.');
      return false;
    } finally { setQuestionBusy(false); }
  }
  $('#new-research').addEventListener('click', () => { if (narrow.matches) setDrawer(false); startResearchConversation(); });

  function updateSuggestions(query) {
    const contextual = clarificationEnabled || (liveSynthesis && activePaperContextId && conversationHistory.length > 0);
    const prompts = contextual
      ? [['Explain that term', 'Explain the term [enter term] from the previous answer.'], ['Show the supporting evidence', 'Show the supporting evidence for the previous answer.']]
      : [['Explain a term', 'Explain the term [enter term] in this paper.'], ['Show supporting evidence', `Show the supporting evidence for this question: ${query}`]];
    suggestions.replaceChildren(h('span', {class: 'muted small', text: 'Follow up'}));
    suggestions.title = contextual
      ? (clarificationEnabled ? 'Suggestions fill the composer; review and send. Bounded server-owned history resolves intent, never supplies evidence.' : 'Suggestions fill the composer; review and send. Recent successful turns are included in this paper mode.')
      : 'Suggestions fill the composer; review and send. Include all needed context. Demo questions are not executed; independent modes do not use previous answers.';
    for (const [label, text] of prompts) {
      suggestions.append(btn(label, () => {
        if (submit.disabled || requestPending) return;
        setQuery(Array.from(text).slice(0, 2000).join(''));
        queryInput.focus();
        const start = queryInput.value.indexOf('[enter term]');
        if (start >= 0) queryInput.setSelectionRange(start, start + 12);
        announce('Suggestion added. Edit the question, then send when ready.');
      }, 'quick-chip'));
    }
    suggestions.hidden = false;
  }
  function offerRetry(answer, query, scenario, context, pendingTurn = null) {
    const retry = btn('Retry original question', () => {
      if (submit.disabled || requestPending) return;
      if (clarificationEnabled && (
        (context?.action === 'resume' && (!clarificationPending || pendingTurn !== activeClarificationTurn || context.conversation_id !== researchConversationId)) ||
        (context?.action !== 'resume' && clarificationPending))) {
        retry.remove();
        announce('This retry no longer owns the active clarification. Answer the current question or start a new conversation.');
        return;
      }
      setQuery(query); scenarioSelect.value = scenario; queryInput.focus(); retry.remove();
      if (clarificationEnabled && context?.conversation_id !== researchConversationId) {
        announce('This failed request belongs to an earlier research conversation. Your text is restored; review before sending in the new conversation.');
        return;
      }
      if (!indexedMode && context && context.paper_context_id !== activePaperContextId) {
        announce('The paper changed since this question failed. Original question restored; review it before sending about the current paper. Previous context will not be sent.');
        return;
      }
      retryContext = context;
      try { form.requestSubmit(); } finally { retryContext = null; }
    }, 'solid-btn small retry-question', 'refresh');
    answer.append(retry);
  }

  /* ---------- Chart-first preview and live progress (experimental backend; model-free) ----------
     An explicit chart question starts two requests at once: the research answer, and
     POST /api/chart-preview (retrieval plus audit-verified complete tables, no model call). A
     verified chart appears as soon as the preview passes the page's own checks
     (EvidenceModel.previewTables), labelled as not yet explained. If the explanation later fails,
     the chart stays with a separate explanation error; if it abstains, the chart switches back
     to its table; if it succeeds and shows the same table with citations, the preview steps aside. */
  let chartPreviewEnabled = false, progressEnabled = false;
  const STAGE_TEXT = {
    starting: 'Starting the research request…', retrieval: 'Searching the research index…',
    validating: 'Checking the evidence and citations…', finished: 'Finishing the answer…',
    failed: 'The research request failed.', idle: 'Waiting for the research backend…'};
  function startProgress(answer) {
    if (!progressEnabled) return () => {};
    let stopped = false, timer = null;
    const tick = async () => {
      if (stopped) return;
      try {
        const state = await (await fetch('/api/progress', {signal: AbortSignal.timeout(4000)})).json();
        const line = $('.loading-line p', answer);
        if (stopped || !line) return;
        let text = STAGE_TEXT[state.stage] || line.textContent;
        if (state.stage === 'generation' && state.call) {
          const step = (state.steps || []).filter(item => String(item.step).startsWith('generation')).length + 1;
          const most = state.max_calls || state.budget?.per_question_max;
          const who = state.mode === 'agentic' ? `${AGENT_NAMES[state.agent] || 'Multi-agent research'} is waiting for the AI` : 'Waiting for the AI explanation';
          text = `${who} · model call ${step}${most ? ` of up to ${most}` : ''} · ${Math.round(state.call.seconds)} s of its ${state.call.timeout} s limit`;
        }
        line.textContent = text;
      } catch { /* keep the last message; the request itself reports failures */ }
      if (!stopped) timer = setTimeout(tick, 1000);
    };
    tick();
    return () => { stopped = true; clearTimeout(timer); };
  }
  async function providerFailure() {
    if (!progressEnabled) return null;
    try {
      const state = await (await fetch('/api/progress', {signal: AbortSignal.timeout(4000)})).json();
      if (!state.last_error) return null;
      return `${state.last_error.message}${state.budget?.stopped
        ? ' Generation is now stopped for this session (no automatic retries). Restart the live backend with a newly approved call budget before asking again.' : ''}`;
    } catch { return null; }
  }
  function startChartPreview(turn, query, number, preset = null) {
    // preset: the multi-agent chart tool's result (same shape as /api/chart-preview, or status
    // 'unavailable' when the backend has no verified table audit). The page re-runs the same checks.
    const status = h('p', {class: 'preview-status', role: 'status', text: 'Looking for a verified table to chart…'});
    const explain = h('p', {class: 'preview-explain', role: 'status'});
    const section = h('section', {class: 'chart-preview', 'aria-label': 'Verified chart from the paper'},
      h('p', {class: 'preview-kicker', text: ['unavailable', 'failed'].includes(preset?.status) ? 'Chart evidence' : 'Verified chart · values from the paper\'s table'}), status, explain);
    $('.answer', turn).before(section);
    const ctx = {demo: {result: {request: {query}}}, number, preview: true, question: () => query, autoChart: (table, plan) => plan.eligible, chartChoice: new Map()};
    const state = {section, status, explain, keys: new Set(), ready: false};
    state.done = (async () => {
      const started = performance.now();
      try {
        if (preset?.status === 'unavailable' || preset?.status === 'failed') {
          status.textContent = `No chart: ${preset.reason || 'chart evidence is unavailable.'}`; section.classList.add('empty'); state.keepEmpty = true; return;
        }
        const response = preset ? null : await fetch('/api/chart-preview', {method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query}), signal: AbortSignal.timeout(60000)});
        const body = preset || await response.json().catch(() => ({}));
        if (response && !response.ok) { status.textContent = `No chart preview: ${body.error || 'the preview service did not answer.'}`; section.classList.add('empty'); return; }
        const {tables, refused} = EM.previewTables(body);
        const chartable = tables.filter(item => item.plan.eligible);
        if (!chartable.length) {
          status.textContent = refused.length ? `No verified chart: ${refused[0].reason}`
            : tables.length ? `No chart: ${tables[0].plan.reason}` : 'No table rows were found for this question. The research explanation will use text passages.';
          section.classList.add('empty');
          return;
        }
        ctx.demo.result.provenance = {index: {indexed_records_sha256: body.index_sha256}};
        for (const {table} of chartable.slice(0, 2)) { section.append(renderEvidenceTable(table, ctx)); state.keys.add(table.key); }
        status.textContent = preset ? `The orchestrator's chart tool found ${chartable.length === 1 ? 'a verified table' : 'verified tables'}, without an AI model call.`
          : `Verified ${chartable.length === 1 ? 'table' : 'tables'} found in ${((performance.now() - started) / 1000).toFixed(1)} s, without an AI model call.`;
        explain.textContent = 'The research explanation is still being written. The chart shows the paper\'s values exactly and does not depend on it.';
        state.ready = true;
      } catch {
        status.textContent = 'No chart preview: the preview request did not complete.';
        section.classList.add('empty');
      }
    })();
    return state;
  }
  function settleChartPreview(state, outcome) {
    if (!state) return;
    state.done.then(() => {
      if (!state.ready) { if (outcome.kind !== 'failed' && !state.keepEmpty) state.section.remove(); return; }
      if (outcome.kind === 'answered') {
        const evidence = outcome.demo.result?.evidence || [];
        const cited = new Set((outcome.demo.result?.summary?.claims || []).flatMap(claim => claim.chunk_ids || []));
        const tableOf = id => { const passage = evidence.find(p => p.chunk_id === id); return passage ? `${passage.arxiv_id}#${passage.table_id}` : null; };
        const citedKeys = new Set([...cited].map(tableOf).filter(Boolean));
        // The answer charts a table itself (with citations) only when it cites it: hand those over,
        // keep the others here with a note.
        for (const key of [...state.keys].filter(k => citedKeys.has(k))) {
          state.section.querySelectorAll('.ev-figure').forEach(figure => { if (figure.dataset.tableKey === key) { figure.querySelector('.ev-chart')?.dispose?.(); figure.remove(); } });
          state.keys.delete(key);
        }
        if (!state.keys.size) { state.section.remove(); return; }
        state.explain.textContent = 'The research explanation is ready below. It does not cite the table shown here, so this chart is not part of its findings.';
      } else if (outcome.kind === 'insufficient') {
        state.explain.textContent = 'The research explanation found the evidence insufficient (see below). The verified table stays available for reference; no conclusion is drawn from it.';
        state.section.querySelectorAll('.ev-seg .seg-btn:first-child').forEach(button => button.click());
      } else {
        state.explain.textContent = `Research explanation unavailable: ${outcome.message} The verified chart above comes straight from the paper's table and does not depend on the explanation.`;
        state.explain.classList.add('bad');
      }
    });
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (submit.disabled || requestPending || composing) return;
    if (savedResult && !liveSynthesis) return;
    const query = queryInput.value;
    const scenario = scenarioSelect.value || 'full';
    const industry = $('#industry-field').hidden ? '' : industryInput.value.trim();
    const risk = !$('#risk-field').hidden && $('#risk-assessment').checked;
    const jurisdiction = $('#jurisdiction').value.trim();
    if (risk && !retryContext && (!industry || !jurisdiction)) {
      setSettings(true);
      (industry ? $('#jurisdiction') : industryInput).focus();
      announce('Risk and compliance assessment needs an industry context and a jurisdiction. Fill both, or turn the assessment off.');
      return;
    }
    const agentic = researchEngine === 'agentic' && agenticAvailable && indexedMode && liveSynthesis;
    if (agentic && risk && !retryContext) {
      setSettings(true);
      $('#risk-assessment').focus();
      announce('Risk and compliance assessment is not available in Multi-Agent mode yet. Turn it off, or switch to Baseline RAG.');
      return;
    }
    const pendingTurn = clarificationPending ? activeClarificationTurn : null;
    let submissionContext = indexedMode ? (retryContext || {context_id: indexedContextId, interpret_context: true,
      ...(industry && !clarificationPending ? {industry} : {}),
      ...(risk && !clarificationPending ? {risk_assessment: true, jurisdiction} : {}),
      ...(clarificationEnabled ? {conversation_id: researchConversationId, action: clarificationPending ? 'resume' : 'ask'} : {})}) : liveSynthesis ? (retryContext || {
      history: conversationHistory.map(message => ({...message})), paper_context_id: activePaperContextId}) : null;
    setSettings(false);
    if (!query.trim()) {
      announce('Enter a nonempty research question.');
      queryInput.focus();
      return;
    }
    const number = ++turnNumber;
    const loading = agentic ? 'Multi-agent research: planning, searching the index, then verifying each claim…'
      : indexedMode ? (clarificationEnabled ? 'Checking your question and researching its evidence…' : 'Searching the research index and synthesizing supported findings…') : liveSynthesis ? 'Reading the paper and synthesizing an answer…' : 'Loading local example…';
    const {turn, answer} = createTurn(query, number, clarificationPending ? 'Your clarification answer' : agentic ? 'Your question · Multi-Agent' : liveSynthesis ? 'Your question' : 'Your question · Not executed', loading);
    showTurn(turn);
    resetEvidence('Loading a new answer. No current evidence to inspect.');
    setQuestionBusy(true);
    suggestions.hidden = true;
    announce(loading, false);
    // Chart-first: a verified chart can appear before (and without) the generated explanation.
    // In Multi-Agent mode the orchestrator decides whether to use the chart tool; its result is shown after the run.
    let chartPreview = !agentic && indexedMode && liveSynthesis && chartPreviewEnabled && !clarificationEnabled && EM.chartIntent(query)
      ? startChartPreview(turn, query, number) : null;
    const stopProgress = liveSynthesis ? startProgress(answer) : () => {};
    let contextRecoveryMessage = null, responseReceived = false, executionFailed = false;
    try {
      const response = await fetch(agentic ? '/api/agentic-research' : liveSynthesis ? '/api/research' : '/api/demo', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query, scenario, ...(revision ? {library_revision: {...revision}} : {}), ...(submissionContext || {})}),
        // Indexed: context, two clarification gates, summary and translation (5 × 300s + 60s).
        // Multi-Agent: up to 6 model calls of 300 s each plus retrieval.
        signal: AbortSignal.timeout(agentic ? 1860000 : (indexedMode ? 1560000 : liveSynthesis ? 330000 : 10000) + (liveSynthesis && presentationEnabled ? 300000 : 0)),
      });
      responseReceived = true;
      const demo = await response.json();
      if (!response.ok) {
        if (liveSynthesis && demo.code === 'paper_changed') {
          conversationHistory = [];
          activePaperContextId = demo.paper_context_id || null;
          submissionContext = {history: [], paper_context_id: activePaperContextId};
          contextRecoveryMessage = 'The loaded paper changed. Previous conversation context was cleared. Your question is unchanged; select Ask paper again to ask about the current paper.';
        }
        if (indexedMode) {
          contextRecoveryMessage = (typeof demo.error === 'string' ? demo.error : demo.error?.message) || 'Indexed research failed. No answer was accepted.';
          if (response.status === 409 && demo.code === 'indexed_context_changed' && !clarificationEnabled) {
            // The server's research context moved on. Pick up the current one so a retry can succeed.
            try {
              const fresh = await (await fetch('/api/config', {signal: AbortSignal.timeout(10000)})).json();
              if (fresh.context_id) {
                indexedContextId = fresh.context_id;
                submissionContext = {...submissionContext, context_id: fresh.context_id};
                contextRecoveryMessage += ' The page has picked up the current research context; retry your question.';
              }
            } catch { /* Keep the server's own message. */ }
          }
        }
        throw new Error('Request rejected.');
      }
      if (demo.scenario === 'clarification') {
        setClarificationPending(true);
        renderClarification(demo, number, answer);
        if (queryInput.value === query) setQuery('');
        return;
      }
      if (demo.result && clarificationEnabled) {
        const wasPending = clarificationPending;
        setClarificationPending(false, 'Answered');
        if (wasPending) queryInput.focus({preventScroll: true});
      }
      if (demo.result) finishRevision();
      if (!demo.result && demo.error) {
        executionFailed = true; // the pipeline ran and failed: /api/progress knows which step
        contextRecoveryMessage = typeof demo.error === 'string' ? demo.error : demo.error.message;
        if (demo.agentic) {
          const calls = demo.agentic.model_calls || {};
          contextRecoveryMessage += ` Multi-agent run stopped at ${AGENT_NAMES[demo.error.stage] || demo.error.stage} (${demo.error.cause}) after ${calls.used ?? 0} model call${calls.used === 1 ? '' : 's'}; nothing was retried.`;
        }
        throw new Error('Research execution failed.');
      }
      renderDemo(demo, number, answer);
      if (agentic && demo.agentic_charts) chartPreview = startChartPreview(turn, query, number, demo.agentic_charts);
      settleChartPreview(chartPreview, {kind: demo.result?.summary?.status === 'ok' ? 'answered' : 'insufficient', demo});
      if (demo.library) loadRecentBriefs();
      if (liveSynthesis) rememberAcceptedTurn(query, demo);
      const searchFailed = ['timeout', 'failed', 'answer_failed', 'unreadable'].includes(demo.result?.provenance?.arxiv_search?.status);
      if (demo.error || searchFailed) {
        // A result means the pending resume has been consumed, even when the later
        // business stage fails. Recover using the original research input.
        const completed = clarificationEnabled && demo.result;
        const retryQuery = completed ? demo.submitted_request.query : query;
        const context = completed ? {...submissionContext, action: 'ask', industry: demo.submitted_request.industry || ''} : submissionContext;
        offerRetry(answer, retryQuery, scenario, context, pendingTurn);
      }
      if (demo.result) updateSuggestions(query);
      if (demo.result && queryInput.value === query) setQuery('');
    } catch (error) {
      const timeout = ['TimeoutError', 'AbortError'].includes(error?.name);
      stopProgress();
      // Say what actually failed (e.g. "The AI provider did not respond within 300 s (call 2).")
      // instead of the generic pipeline message.
      const provider = indexedMode && executionFailed ? await providerFailure() : null;
      if (provider) contextRecoveryMessage = `${provider} No answer was accepted. Your question is unchanged.`;
      const message = contextRecoveryMessage || (timeout
        ? 'The research request timed out. Your question is unchanged. Check that the demo server is running before retrying.'
        : !responseReceived
          ? 'Cannot reach the local demo server. Restart the demo, refresh this page, and retry your question.'
          : liveSynthesis
            ? 'The server response could not be displayed. No answer was accepted. Your question is unchanged; retry when ready.'
            : 'Could not load the local example. Your question is unchanged; retry when ready.');
      if (!contextRecoveryMessage && responseReceived) console.error(error);
      answer.replaceChildren(answerHeading(number), h('div', {class: 'block-failed'}, h('p', {class: 'lead-plain', text: 'No answer was accepted.'}),
        h('p', {class: 'aside-line bad'}, icon('alert'), h('span', {text: message}))));
      offerRetry(answer, query, scenario, submissionContext, pendingTurn);
      markAnswerReady(answer);
      announce(contextRecoveryMessage && !indexedMode ? 'Paper changed. Context cleared; submit your question again.' : `Answer ${number} failed. Your question is unchanged; retry when ready.`);
      resetEvidence('The latest answer did not load. Retry to inspect its evidence.');
      settleChartPreview(chartPreview, {kind: 'failed', message});
    } finally {
      stopProgress();
      setQuestionBusy(false);
      autosize();
    }
  });

  /* ---------- Saved briefs (same /api/briefs contract as ui/brief-library.js) ---------- */
  async function api(path, payload) {
    const response = await fetch(path, {signal: AbortSignal.timeout(15000),
      ...(payload === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)})});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error((typeof data.error === 'string' && data.error) || 'Saved work is unavailable.');
      error.status = response.status;
      // The proxy says whether a failed write ever reached the backend ('not_sent' / 'unknown').
      if (typeof data.write_outcome === 'string') error.writeOutcome = data.write_outcome;
      throw error;
    }
    return data;
  }
  // Messages shown in a rebuilt brief panel after a write was reconciled (kept out of the demo
  // object so they never reach exports or saved snapshots).
  const panelNotices = new WeakMap();
  /* Runs a saved-work request. Reads that never answered changed nothing. A write whose response
     was lost (browser timeout, dropped connection, proxy 504 or other 5xx after forwarding) may
     already be stored or may still commit (audit M4, verification blocker 1). Its outcome stays
     "unknown" until the reloaded brief positively shows this exact change: a reload without the
     change proves nothing, so it never says "not saved". `reconcile` returns {applied: true|null, latest?}. */
  const UNKNOWN_TEXT = 'Outcome unknown: the saved brief does not show this change yet, but the original request may still be processed. Retrying now could save it twice. Check again in a moment, or open the Library.';
  async function reconcileInto(message, reconcile, onReconciled) {
    let verdict = {applied: null};
    try { if (reconcile) verdict = await reconcile(); }
    catch { verdict = {applied: null, text: 'Outcome unknown: the saved brief could not be reloaded. Check it in the Library before retrying, so nothing is saved twice.'}; }
    if (verdict.applied === true) {
      const text = 'The server confirms this change was saved. Nothing needs to be retried.';
      message.textContent = text; message.classList.remove('bad');
      if (verdict.latest && onReconciled) onReconciled(verdict.latest, text, true);
      announce(text);
      return;
    }
    const text = verdict.text || (reconcile ? UNKNOWN_TEXT : 'Outcome unknown: this change may have been saved. Check the Library before saving again, so nothing is saved twice.');
    message.textContent = text; message.classList.add('bad');
    if (reconcile) {
      const again = btn('Check again', () => {
        again.disabled = true;
        message.textContent = 'Checking the saved brief again…';
        reconcileInto(message, reconcile, onReconciled);
      }, 'text-btn', 'refresh');
      message.append(' ', again);
    }
    message.append(' ', btn('Open the Library', () => openLibrary(), 'text-btn', 'arrow'));
    announce(text);
  }
  async function operation(control, message, action, {write = false, reconcile = null, onReconciled = null} = {}) {
    if (control.disabled) return;
    control.disabled = true;
    message.classList.remove('bad');
    try { await action(); }
    catch (error) {
      const failure = AsyncGuards.writeFailure(error, {write});
      message.classList.add('bad');
      if (failure.kind === 'unknown') {
        message.textContent = `${failure.timeout ? 'The server did not answer in time' : 'The connection dropped'} after the change was sent, so it may already be saved. Checking the saved brief before anything is retried…`;
        await reconcileInto(message, reconcile, onReconciled);
      } else {
        message.textContent = failure.kind === 'not_applied'
          ? (failure.timeout ? 'The saved-work request timed out. Nothing was changed; retry when ready.'
            : 'Cannot reach the local server. Nothing was changed; retry when it is running.')
          : error.message || 'Saved-work request failed. Your answer is unchanged.';
        // 409: this snapshot is stale (another version, review or archive happened). Offer the current one.
        if (error.status === 409 && message.recover) message.append(' ', message.recover());
      }
    }
    finally { control.disabled = false; }
  }
  /* Opens a saved brief or version unless a newer navigation happened while it loaded (audit M2). */
  function openSaved(control, message, path) {
    const token = nav.begin();
    return operation(control, message, async () => {
      const demo = await api(path);
      if (!nav.isCurrent(token)) return; // superseded: never override the newer view or move focus
      openSnapshot(demo);
    });
  }
  const when = value => new Date(value).toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'});
  const briefList = $('#brief-list'), libraryStatus = $('#library-status');
  const briefSearch = $('#brief-search'), briefArchived = $('#brief-archived');
  let offset = 0, loadSequence = 0;
  // The library is a page of the workspace rather than a modal; this keeps the shared call sites unchanged.
  const libraryDialog = {get open() { return currentView === 'library'; }, close() { setView(activeTurn ? 'thread' : 'home', false); }};
  function openSnapshot(demo) {
    // Replays are display-only: never feed them into live conversation history.
    const number = ++turnNumber;
    const {turn, answer} = createTurn(demo.result.request.query, number, 'Saved question · No new research', 'Opening saved snapshot…');
    showTurn(turn);
    resetEvidence('Select a saved citation to inspect the retained evidence.');
    renderDemo(demo, number, answer);
    latestAnswer.focus({preventScroll: true});
  }
  const REVIEW_LABELS = {pending: 'Not reviewed yet', approve: 'Approved', revise: 'Changes requested', reject: 'Rejected'};
  const reviewLabel = status => REVIEW_LABELS[status] || status || 'Draft';
  const statusTone = text => (/approved/i.test(text) && !/not approved/i.test(text) ? 'ok' : /change|revise/i.test(text) ? 'warn' : /reject/i.test(text) ? 'bad' : 'draft');
  function briefRow(brief, status) {
    const label = reviewLabel(brief.review_status);
    const open = h('button', {type: 'button', class: 'brief-open'},
      h('span', {class: 'brief-title', text: brief.title}),
      h('span', {class: 'brief-meta'},
        h('span', {class: `state ${statusTone(label)}`}, icon(statusTone(label) === 'ok' ? 'check' : 'shield'), h('span', {text: label})),
        brief.number > 1 ? h('span', {text: `Version ${brief.number}`}) : null,
        brief.mode === 'fixture' ? h('span', {text: 'Synthetic example'}) : null,
        h('span', {text: when(brief.updated_at)})),
      icon('chevron'));
    open.addEventListener('click', () => openSaved(open, status, `/api/briefs/${brief.id}`));
    return h('li', null, open);
  }
  /* A saved research example on the home page: the question, its review state, and one action. */
  function exampleCard(brief, status) {
    const label = reviewLabel(brief.review_status);
    const open = h('button', {type: 'button', class: 'example-card'},
      h('span', {class: 'example-card-q', text: brief.title}),
      h('span', {class: 'example-card-meta'},
        h('span', {class: `state ${statusTone(label)}`}, icon(statusTone(label) === 'ok' ? 'check' : 'shield'), h('span', {text: label})),
        h('span', {text: `Saved ${when(brief.updated_at)}`})),
      icon('chevron'));
    open.addEventListener('click', () => openSaved(open, status, `/api/briefs/${brief.id}`));
    return h('li', null, open);
  }
  /* ---------- Library: saved research and the papers it cites (real records only) ---------- */
  // Saved research comes from /api/briefs. "Papers" lists the papers cited by the saved research on
  // this page, read from each brief (GET /api/briefs/{id}); the full indexed-paper catalogue needs a
  // backend endpoint that does not exist yet (see design/WORKSPACE-INTEGRATION.md).
  let libraryTab = 'briefs', statusFilter = 'all', lastBriefs = [];
  const papersPanel = h('div', {class: 'papers-panel', hidden: true});
  const libTabs = h('div', {class: 'seg lib-tabs', role: 'tablist', 'aria-label': 'Library sections'});
  const statusChips = h('div', {class: 'quick status-filter', role: 'group', 'aria-label': 'Filter by review status'});
  const STATUS_FILTERS = [['all', 'All'], ['revise', 'Changes requested'], ['pending', 'Not reviewed'], ['approve', 'Approved'], ['reject', 'Rejected']];
  function renderLibTabs() {
    libTabs.replaceChildren(...[['briefs', 'Saved research'], ['papers', 'Papers in saved research']].map(([value, label]) => {
      const tab = h('button', {type: 'button', role: 'tab', class: 'seg-btn', 'aria-selected': String(libraryTab === value),
        onclick: () => { libraryTab = value; renderLibTabs(); showLibraryTab(); }}, h('span', {text: label}));
      return tab;
    }));
  }
  function renderStatusChips() {
    const counts = Object.fromEntries(STATUS_FILTERS.map(([key]) => [key, key === 'all' ? lastBriefs.length : lastBriefs.filter(b => (b.review_status || 'pending') === key).length]));
    statusChips.replaceChildren(...STATUS_FILTERS.filter(([key]) => key === 'all' || counts[key]).map(([key, label]) =>
      btn(`${label} (${counts[key]})`, () => { statusFilter = key; renderStatusChips(); renderBriefList(); }, 'quick-chip')));
    statusChips.querySelectorAll('button').forEach((chip, i) => chip.setAttribute('aria-pressed', String(STATUS_FILTERS.filter(([key]) => key === 'all' || counts[key])[i][0] === statusFilter)));
  }
  function renderBriefList() {
    const shown = lastBriefs.filter(b => statusFilter === 'all' || (b.review_status || 'pending') === statusFilter);
    briefList.replaceChildren(...shown.map(brief => briefRow(brief, libraryStatus)));
    if (!shown.length && lastBriefs.length) briefList.replaceChildren(h('li', {class: 'empty', text: 'No saved research with this review status on this page.'}));
  }
  function showLibraryTab() {
    const papers = libraryTab === 'papers';
    briefList.hidden = papers; $('.pages', $('#library-view')).hidden = papers; statusChips.hidden = papers;
    papersPanel.hidden = !papers; libraryStatus.hidden = papers;
    if (papers) loadPapers();
  }
  async function loadPapers() {
    papersPanel.replaceChildren(h('p', {class: 'hint', role: 'status', text: 'Reading the papers cited by saved research…'}));
    const papers = new Map();
    try {
      for (const brief of lastBriefs) {
        const data = await api(`/api/briefs/${brief.id}`);
        for (const passage of data.result?.evidence || []) {
          const key = passage.arxiv_id || passage.title;
          if (!key) continue;
          if (!papers.has(key)) papers.set(key, {arxiv_id: passage.arxiv_id, title: passage.title, html_url: passage.html_url, pdf_url: passage.pdf_url, tables: new Set(), briefs: new Map()});
          const paper = papers.get(key);
          if (!paper.abstract && /^abstract$/i.test(passage.section || '') && passage.representation !== 'linearized_table') paper.abstract = passage.text;
          if (passage.representation === 'linearized_table') paper.tables.add(passage.table_id);
          paper.briefs.set(brief.id, brief);
        }
      }
    } catch (error) {
      papersPanel.replaceChildren(h('p', {class: 'hint bad', text: error.message || 'Could not read saved research.'}));
      return;
    }
    const query = briefSearch.value.trim().toLowerCase();
    const list = [...papers.values()].filter(p => !query || `${p.title} ${p.arxiv_id}`.toLowerCase().includes(query));
    papersPanel.replaceChildren(
      h('p', {class: 'hint', text: `${list.length} paper${list.length === 1 ? '' : 's'} retrieved for the saved research shown. The full catalogue of indexed papers is not available from this server yet.`}),
      h('ul', {class: 'paper-rows'}, list.map(paper => h('li', {class: 'paper-row'},
        h('p', {class: 'paper-title', text: paper.title || paper.arxiv_id}),
        h('p', {class: 'paper-meta'}, paper.arxiv_id ? h('span', {class: 'mono', text: `arXiv ${paper.arxiv_id}`}) : null,
          paper.tables.size ? h('span', {text: `${paper.tables.size} table${paper.tables.size === 1 ? '' : 's'} retrieved`}) : null,
          paper.html_url ? h('a', {href: paper.html_url, target: '_blank', rel: 'noopener noreferrer', text: 'Paper (web)'}) : null,
          paper.pdf_url ? h('a', {href: paper.pdf_url, target: '_blank', rel: 'noopener noreferrer', text: 'PDF'}) : null),
        paper.abstract ? h('details', {class: 'paper-abstract'}, h('summary', {text: 'Abstract (as retrieved)'}), h('p', {math: paper.abstract})) : null,
        h('div', {class: 'paper-briefs'}, h('span', {class: 'muted', text: 'Retrieved for: '}), [...paper.briefs.values()].map(brief => {
          const open = h('button', {type: 'button', class: 'link-btn', text: brief.title});
          open.addEventListener('click', () => openSaved(open, libraryStatus, `/api/briefs/${brief.id}`));
          return open;
        }))))));
  }
  (() => {
    const tools = $('.library-tools');
    tools.before(libTabs);
    const panel = h('div', {class: 'lib-filters', id: 'lib-filters', hidden: true}, statusChips, $('#brief-archived').closest('label'), $('#library-import'));
    const toggle = h('button', {type: 'button', class: 'text-btn lib-filter-toggle', 'aria-expanded': 'false', 'aria-controls': 'lib-filters'}, icon('sliders'), h('span', {text: 'Filters'}));
    toggle.addEventListener('click', () => { const open = panel.hidden; panel.hidden = !open; toggle.setAttribute('aria-expanded', String(open)); });
    tools.append(toggle);
    tools.after(panel);
    briefList.after(papersPanel);
    renderLibTabs();
  })();
  /* ---------- Sidebar (desktop ≥1024px): navigation and real history only ----------
     "Saved research" comes from /api/briefs, grouped by each brief's own updated_at. "This session" lists
     answers opened here that are not saved briefs. Saved briefs are not presented as conversation threads. */
  function sideGroup(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return 'Older';
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const day = 864e5;
    if (date >= today) return 'Today';
    if (date >= today - day) return 'Yesterday';
    if (date >= today - 7 * day) return 'Previous 7 days';
    return 'Older';
  }
  function turnBriefId(turn) { return turn?.demoState?.demo?.library?.brief?.id || null; }
  function renderSidebar() {
    const root = $('#side-history');
    if (!root) return;
    const briefs = renderSidebar.briefs || [];
    const activeId = currentView === 'thread' ? turnBriefId(activeTurn) : null;
    const status = h('span', {class: 'sr-only', role: 'status'});
    const item = (text, current, onclick, title) => {
      const button = h('button', {type: 'button', class: 'side-link', title: title || text, onclick}, h('span', {text}));
      if (current) button.setAttribute('aria-current', 'true');
      return h('li', null, button);
    };
    const parts = [];
    const unsaved = [...thread.querySelectorAll(':scope > .turn')].filter(turn => turn.demoState && !turnBriefId(turn)).reverse();
    if (unsaved.length) {
      parts.push(h('section', {class: 'side-group'}, h('h2', {class: 'side-title', text: 'This session'}),
        h('ul', null, unsaved.map(turn => item($('.question', turn)?.textContent || 'Answer', currentView === 'thread' && turn === activeTurn,
          () => { activateTurn(turn); setView('thread'); renderSidebar(); })))));
    }
    if (briefs.length) {
      const groups = new Map();
      for (const brief of briefs) {
        const key = sideGroup(brief.updated_at);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(brief);
      }
      const section = h('section', {class: 'side-group'}, h('h2', {class: 'side-title', text: 'Saved research'}));
      for (const key of ['Today', 'Yesterday', 'Previous 7 days', 'Older']) {
        if (!groups.has(key)) continue;
        section.append(h('h3', {class: 'side-when', text: key}), h('ul', null, groups.get(key).map(brief => {
          const open = () => {
            const existing = [...thread.querySelectorAll(':scope > .turn')].find(turn => turnBriefId(turn) === brief.id);
            if (existing) { activateTurn(existing); setView('thread'); renderSidebar(); return; }
            openSaved(document.activeElement, status, `/api/briefs/${brief.id}`);
          };
          return item(brief.title, brief.id === activeId, open, `${brief.title} · ${reviewLabel(brief.review_status)}`);
        })));
      }
      parts.push(section);
    }
    root.replaceChildren(...parts, status);
    $('#side-library').toggleAttribute('aria-current', currentView === 'library');
    $('#side-new').toggleAttribute('aria-current', currentView === 'home');
  }
  (() => {
    const key = '1f.sidebar.collapsed';
    const collapse = $('#side-collapse');
    if (!collapse) return; // an older cached index.html without the sidebar: keep the page working
    const setCollapsed = collapsed => {
      document.body.classList.toggle('side-collapsed', collapsed);
      collapse.setAttribute('aria-expanded', String(!collapsed));
      collapse.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
      collapse.setAttribute('aria-label', collapse.title);
      store.set(key, collapsed ? '1' : '0');
    };
    setCollapsed(store.get(key) === '1');
    // Narrow screens: the sidebar is a drawer opened from the top bar; the collapse button closes it.
    const setSideOpen = open => {
      document.body.classList.toggle('side-open', open);
      $('#side-scrim').hidden = !open;
      $('#menu-open').setAttribute('aria-expanded', String(open));
      if (open) $('#side-new').focus({preventScroll: true});
    };
    collapse.addEventListener('click', () => {
      if (narrow.matches) return setSideOpen(false);
      setCollapsed(!document.body.classList.contains('side-collapsed'));
    });
    $('#menu-open').addEventListener('click', () => setSideOpen(!document.body.classList.contains('side-open')));
    $('#side-scrim').addEventListener('click', () => setSideOpen(false));
    $('#sidebar').addEventListener('click', event => { if (narrow.matches && event.target.closest('.side-link, .side-item')) setSideOpen(false); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && document.body.classList.contains('side-open')) setSideOpen(false); });
    const historyKey = '1f.sidebar.history-collapsed';
    const setHistory = open => {
      $('#history-toggle').setAttribute('aria-expanded', String(open));
      $('#side-history').hidden = !open;
      store.set(historyKey, open ? '0' : '1');
    };
    setHistory(store.get(historyKey) !== '1');
    $('#history-toggle').addEventListener('click', () => setHistory($('#side-history').hidden));
    // New research when research can run; otherwise the research home with saved examples (never a dead search box).
    const syncNew = () => {
      const canAsk = !$('#new-research').hidden;
      const button = $('#side-new');
      button.replaceChildren(icon(canAsk ? 'plus' : 'search'), h('span', {class: 'side-label', text: canAsk ? 'New research' : 'Research home'}));
      button.title = canAsk ? 'New research' : 'Research home';
    };
    $('#side-new').addEventListener('click', () => { if (!$('#new-research').hidden) $('#new-research').click(); else setView('home'); });
    $('#side-library').addEventListener('click', () => $('#library-open').click());
    $('#side-display').addEventListener('click', () => $('#prefs-open').click());
    document.getElementById('side-theme')?.addEventListener('click', () => $('#theme-toggle').click());
    const syncLibrary = () => { $('#side-library').hidden = $('#library-open').hidden; };
    new MutationObserver(syncNew).observe($('#new-research'), {attributes: true, attributeFilter: ['hidden']});
    new MutationObserver(syncLibrary).observe($('#library-open'), {attributes: true, attributeFilter: ['hidden']});
    new MutationObserver(() => renderSidebar()).observe(stage, {attributes: true, attributeFilter: ['data-view']});
    syncNew(); syncLibrary(); syncTheme();
  })();

  async function loadLibrary() {
    const sequence = ++loadSequence;
    libraryStatus.textContent = 'Loading saved briefs…'; libraryStatus.classList.remove('bad');
    briefList.setAttribute('aria-busy', 'true');
    try {
      const params = new URLSearchParams({q: briefSearch.value, archived: briefArchived.checked ? '1' : '0', offset});
      const data = await api(`/api/briefs?${params}`);
      if (sequence !== loadSequence) return;
      lastBriefs = data.briefs;
      renderStatusChips(); renderBriefList();
      if (libraryTab === 'papers') loadPapers();
      $('#brief-previous').disabled = offset === 0;
      $('#brief-next').disabled = data.briefs.length < 30;
      libraryStatus.textContent = data.briefs.length ? `Showing ${offset + 1}–${offset + data.briefs.length} saved research briefs.` : (liveSynthesis ? 'No saved research yet. Ask a question, then save the answer as a brief.' : 'No saved research here yet.');
    } catch (error) { if (sequence === loadSequence) libraryStatus.textContent = error.message || 'Could not load saved briefs. Try Refresh.'; }
    finally { if (sequence === loadSequence) briefList.setAttribute('aria-busy', 'false'); }
  }
  async function loadRecentBriefs() {
    if (!libraryEnabled) return;
    try {
      const data = await api('/api/briefs?q=&archived=0&offset=0');
      renderSidebar.briefs = data.briefs; renderSidebar();
      const status = h('span');
      $('#recent-briefs').replaceChildren(...data.briefs.slice(0, recordedMode ? 6 : 4).map(brief => recordedMode ? exampleCard(brief, status) : briefRow(brief, status)));
      $('#recent-briefs').classList.toggle('example-grid', recordedMode);
      $('#recent-heading').textContent = recordedMode ? 'Saved research to explore' : 'Recent research';
      $('#recent-all').textContent = recordedMode ? 'All saved research' : 'Open library';
      $('#recent-section').hidden = !data.briefs.length;
    } catch { $('#recent-section').hidden = true; }
  }
  function openLibrary() {
    setView('library'); offset = 0; loadLibrary();
    requestAnimationFrame(() => briefSearch.focus());
  }
  $('#library-open').addEventListener('click', openLibrary);
  $('#recent-all').addEventListener('click', openLibrary);
  $('#library-search-form').addEventListener('submit', event => { event.preventDefault(); offset = 0; loadLibrary(); });
  briefArchived.addEventListener('change', () => { offset = 0; loadLibrary(); });
  $('#brief-previous').addEventListener('click', () => { offset = Math.max(0, offset - 30); loadLibrary(); });
  $('#brief-next').addEventListener('click', () => { offset += 30; loadLibrary(); });
  function importControl(label, target, onSaved, message, onReconciled = null) {
    const input = h('input', {type: 'file', accept: '.json,application/json', class: 'sr-only'});
    let importedResult = null;
    // A new version of an existing brief is confirmed only if the brief's current version is new
    // AND holds exactly the imported result; an unrelated newer version proves nothing.
    const reconcile = target ? async () => {
      const latest = await api(`/api/briefs/${target.brief_id}`);
      return {applied: AsyncGuards.importRecorded(latest, target.expected_version, importedResult) ? true : null, latest};
    } : null; // a brand-new brief cannot be identified afterwards: the Library is the place to check
    input.addEventListener('change', () => {
      // Captured before any asynchronous work, so a late completion cannot override a newer view.
      const token = nav.peek();
      operation(input, message, async () => {
        if (!input.files[0]) return;
        if (input.files[0].size > 8_000_000) throw new Error('Snapshot exceeds 8 MB.');
        const value = JSON.parse(await input.files[0].text());
        input.value = '';
        importedResult = value.result ? value.result : value;
        const saved = await api('/api/briefs', {...(value.result ? {envelope: value} : {result: value}), ...(target || {})});
        await onSaved(saved, token);
      }, {write: true, reconcile, onReconciled});
    });
    return h('label', {class: 'quiet file'}, icon('upload'), h('span', {text: label}), input);
  }
  $('#library-import').append(importControl('Import result JSON', null, async (saved, token) => {
    libraryStatus.textContent = 'Snapshot imported. No model call. It is in the Library.'; loadRecentBriefs();
    if (nav.isCurrent(token)) openSnapshot(saved); // the person moved on while it saved: do not pull them back
  }, libraryStatus));

  function beginRevision(demo) {
    const {brief, version} = demo.library;
    revision = {brief_id: brief.id, expected_version: version.id};
    $('#revision-banner').hidden = false;
    $('#revision-text').textContent = `Next accepted answer becomes a new version of “${brief.title}”. This starts a fresh exchange using the current source configuration.`;
    setQuery(demo.result.request.query); queryInput.focus();
  }
  function finishRevision() { revision = null; $('#revision-banner').hidden = true; }
  $('#revision-cancel').addEventListener('click', finishRevision);
  async function reviseBrief(demo) {
    if (requestPending) return;
    if (clarificationEnabled && !await startResearchConversation()) return;
    conversationHistory = []; clearRetries();
    setView('thread');
    beginRevision(demo);
  }

  function briefPanel(panel, demo, onChanged, number) {
    const notice = panelNotices.get(demo);
    const message = h('p', {class: `hint ${demo.library_error || (notice && !notice.ok) ? 'bad' : ''}`, role: 'status', text: demo.library_error || notice?.text || ''});
    // After a reconciled write, rebuild the panel from what the server holds and keep the verdict visible.
    const showReconciled = (latest, text, applied) => { panelNotices.set(latest, {text, ok: applied === true}); onChanged(latest); };
    if (!libraryEnabled || !demo.library) {
      // A brand-new brief cannot be identified afterwards, so an unknown outcome points to the Library.
      const save = btn('Save as separate brief', () => operation(save, message, async () => onChanged(await api('/api/briefs', {envelope: demo})), {write: true}), 'solid-btn', 'bookmark');
      panel.append(h('p', {class: 'panel-title', text: 'Save this answer'}),
        h('p', {class: 'muted small', text: libraryEnabled ? 'Saving keeps this exact answer and its evidence as version 1 of a brief. Reviews and later versions attach to it.' : 'Persistent library disabled for this session.'}),
        h('div', {class: 'row'}, libraryEnabled && save, snapshotButton(demo)), message);
      return;
    }
    const {brief, version, versions, reviews} = demo.library;
    message.recover = () => {
      const reopen = btn('Reopen the latest version', () => openSaved(reopen, message, `/api/briefs/${brief.id}`), 'text-btn', 'refresh');
      return reopen;
    };
    const current = !brief.archived && version.id === brief.current_version;
    const isLatest = version.id === brief.current_version;
    const title = h('input', {type: 'text', maxLength: 200, value: brief.title, class: 'title-input', 'aria-label': 'Brief title'});
    const latestBrief = async sent => {
      const latest = await api(`/api/briefs/${brief.id}`);
      return {applied: AsyncGuards.briefChanged(latest.library?.brief, sent) ? true : null, latest};
    };
    const rename = btn('Rename brief', () => {
      const sent = {expected_version: version.id, title: title.value};
      operation(rename, message, async () => onChanged(await api(`/api/briefs/${brief.id}`, sent)),
        {write: true, reconcile: () => latestBrief(sent), onReconciled: showReconciled});
    }, 'quiet', 'pencil');
    rename.disabled = !isLatest;
    panel.append(h('div', {class: 'brief-head'}, title, rename),
      h('p', {class: 'muted small', text: `${demo.mode === 'fixture' ? 'Synthetic example, not live research' : 'Retained research snapshot'} · Reviews belong to this exact snapshot, including its evidence and presentation.`}), message);

    const tabs = h('div', {class: 'tabs', role: 'tablist', 'aria-label': 'Saved brief'});
    const panes = h('div', {class: 'panes'});
    const tabNodes = [];
    const tab = (key, label, iconName, content) => {
      const pane = h('div', {class: 'pane', role: 'tabpanel', id: `${panel.id}-${key}`, hidden: true}, content);
      const button = h('button', {type: 'button', role: 'tab', class: 'tab', id: `${panel.id}-tab-${key}`, 'aria-controls': pane.id,
        onclick: () => tabNodes.forEach(item => {
          const selected = item.button === button;
          item.button.setAttribute('aria-selected', String(selected)); item.button.tabIndex = selected ? 0 : -1; item.pane.hidden = !selected;
        })}, icon(iconName), h('span', {text: label}));
      pane.setAttribute('aria-labelledby', button.id);
      tabNodes.push({button, pane}); tabs.append(button); panes.append(pane);
    };
    tabs.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
      const index = tabNodes.findIndex(item => item.button === document.activeElement);
      const next = tabNodes[(index + (event.key === 'ArrowRight' ? 1 : tabNodes.length - 1)) % tabNodes.length];
      next.button.click(); next.button.focus();
    });

    /* Version history */
    const timeline = h('ol', {class: 'timeline', 'aria-label': 'Version history'});
    for (const item of [...versions].reverse()) {
      const viewing = item.id === version.id;
      const open = btn('Open this version', () => openSaved(open, message, `/api/briefs/${brief.id}?version=${item.id}`), 'text-btn', 'arrow');
      timeline.append(h('li', {class: viewing ? 'viewing' : ''}, h('span', {class: 'node'}),
        h('div', null, h('p', {class: 'timeline-title'}, h('span', {text: `Version ${item.number}`}),
          item.id === brief.current_version && chip('Latest', 'accent'), viewing && chip('Viewing', 'ok')),
          h('p', {class: 'muted small', text: `${item.audience} · ${when(item.created_at)}`})),
        !viewing && open));
    }
    tab('versions', `Versions (${versions.length})`, 'history', timeline);

    /* Review */
    const history = h('ul', {class: 'reviews', 'aria-label': 'Review history'});
    for (const review of [...reviews].reverse()) {
      const tone = {approve: 'ok', revise: 'warn', reject: 'bad'}[review.decision];
      history.append(h('li', null, h('span', {class: `dot ${tone}`}), h('div', null,
        h('p', null, h('strong', {text: {approve: 'Approved', revise: 'Changes requested', reject: 'Rejected'}[review.decision] || review.decision}),
          h('span', {class: 'muted', text: ` · ${review.reviewer} · ${when(review.created_at)}`})),
        review.notes && h('p', {class: 'review-notes', text: review.notes}))));
    }
    const reviewPane = [outstandingIssues(number)];
    if (current) {
      const reviewer = h('input', {type: 'text', required: true, maxLength: 120, autocomplete: 'name', id: `${panel.id}-reviewer`});
      const notes = h('textarea', {maxLength: 4000, rows: 2, id: `${panel.id}-notes`});
      // The backend refuses approval while a requested risk & compliance check is unresolved.
      const gate = demo.result.regulatory_checkpoint;
      const approvalBlocked = Boolean(gate) && gate.assessment?.verdict !== 'potentially_feasible';
      let decision = null; // no preselected decision: a reviewer must choose deliberately
      const decisions = h('div', {class: 'decisions', role: 'radiogroup', 'aria-label': 'Review decision'});
      for (const [value, label, hint, iconName] of [['approve', 'Approve this version', approvalBlocked ? 'Unavailable: the risk & compliance assessment is unresolved.' : 'Records human approval of this exact snapshot.', 'check'],
        ['revise', 'Request changes', 'Notes are required.', 'pencil'], ['reject', 'Reject this version', 'Marks the snapshot as not usable.', 'x']]) {
        decisions.append(h('label', {class: `decision ${value}`}, h('input', {type: 'radio', name: `${panel.id}-decision`, value, checked: value === decision, disabled: value === 'approve' && approvalBlocked,
          onchange: () => { decision = value; }}), icon(iconName), h('span', null, h('strong', {text: label}), h('small', {text: hint}))));
      }
      const send = h('button', {type: 'submit', class: 'solid-btn'}, icon('shield'), h('span', {text: 'Record review'}));
      const reviewForm = h('form', {class: 'review-form', onsubmit: event => {
        event.preventDefault();
        if (!decision) { message.textContent = 'Choose a decision: approve, request changes or reject.'; message.classList.add('bad'); decisions.querySelector('input:not(:disabled)').focus(); return; }
        if (!reviewer.value.trim()) { message.textContent = 'Reviewer name is required.'; message.classList.add('bad'); reviewer.focus(); return; }
        if (decision === 'revise' && !notes.value.trim()) { message.textContent = 'Describe the requested changes in the review notes.'; message.classList.add('bad'); notes.focus(); return; }
        const sent = {version_id: version.id, fingerprint: version.fingerprint, reviewer: reviewer.value, decision, notes: notes.value || null};
        // If the response is lost, reload this version's history: a matching new review means it was recorded.
        operation(send, message, async () => onChanged(await api(`/api/briefs/${brief.id}/reviews`, sent)), {write: true,
          reconcile: async () => {
            const latest = await api(`/api/briefs/${brief.id}?version=${version.id}`);
            return {applied: AsyncGuards.reviewRecorded(reviews, latest.library?.reviews, sent) ? true : null, latest};
          }, onReconciled: showReconciled});
      }}, decisions,
        h('div', {class: 'field'}, h('label', {htmlFor: reviewer.id, text: 'Reviewer name'}), reviewer),
        h('div', {class: 'field'}, h('label', {htmlFor: notes.id, text: 'Review notes (required for changes)'}), notes), send);
      reviewPane.push(reviewForm);
    } else reviewPane.push(note(brief.archived ? 'Restore this brief before adding versions or reviews.' : 'Historical version. Open the latest version before revising or reviewing.', 'warn', 'history'));
    reviewPane.push(h('p', {class: 'term', text: `Review history for version ${version.number}`}),
      reviews.length ? history : h('p', {class: 'muted small', text: 'No reviews recorded for this version.'}));
    tab('review', `Review${reviews.length ? ` (${reviews.length})` : ''}`, 'shield', reviewPane);

    /* Manage */
    const archive = btn(brief.archived ? 'Restore brief' : 'Archive brief', () => {
      const sent = {expected_version: version.id, archived: !brief.archived};
      operation(archive, message, async () => onChanged(await api(`/api/briefs/${brief.id}`, sent)),
        {write: true, reconcile: () => latestBrief(sent), onReconciled: showReconciled});
    }, 'quiet', 'archive');
    archive.disabled = !isLatest;
    tab('manage', 'Manage', 'sliders', [h('div', {class: 'row'},
      current && liveSynthesis && btn('Revise with new research', () => reviseBrief(demo), 'solid-btn', 'refresh'),
      current && importControl('Import a new version JSON', {brief_id: brief.id, expected_version: version.id}, onChanged, message, showReconciled),
      snapshotButton(demo), archive),
      h('p', {class: 'muted small', text: 'Original result JSON and existing HTML/Markdown exports remain pending drafts; library decisions are retained separately in snapshot JSON.'})]);
    panel.append(tabs, panes);
    tabNodes[1].button.click(); // Review is the action most people open this panel for.
  }

  /* ---------- Startup: /api/config + /api/saved-result, as before ---------- */
  const initialQuestion = queryInput.value;
  submit.disabled = true;
  function loadQuestionEntry() {
    setQuestionBusy(true);
    $('#composer-note').textContent = 'Checking question entry configuration…';
    return Promise.all(['/api/config', '/api/saved-result'].map(async url => {
      const response = await fetch(url, {signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || 'App configuration unavailable');
      return response.json();
    })).then(([config, demo]) => {
      const untouchedQuestion = queryInput.value === initialQuestion;
      const composerNote = $('#composer-note');
      appReady = true;
      liveSynthesis = config.live;
      libraryEnabled = config.library === true;
      $('#library-open').hidden = !libraryEnabled;
      finishRevision();
      presentationEnabled = config.plain_language === true;
      chartPreviewEnabled = config.chart_preview === true;
      progressEnabled = config.progress === true;
      activePaperContextId = config.paper_context_id || null;
      indexedMode = config.mode === 'indexed';
      indexedContextId = config.context_id || null;
      clarificationEnabled = config.clarification === true;
      researchConversationId = config.conversation_id || null;
      // Multi-agent needs a live indexed backend started with --agentic (independent queries only).
      setAgenticAvailable(config.agentic_mode === true && indexedMode
        && (window.MOCK_API === true || (config.live === true && !clarificationEnabled)));
      setClarificationPending(false);
      const mock = window.MOCK_API === true;
      // Scenario choice exists for fixtures (existing demo options) and for the mock backend.
      const scenarios = mock
        ? [['full', 'Full answer'], ['short', 'Short factual answer'], ['long', 'Long multi-part answer'], ['coverage-gap', 'Partial coverage · findings withheld'],
          ['conflict', 'Conflicting studies'], ['tables', 'Answer with a table'], ['clarification', 'Ask a clarifying question first'], ['partial', 'Partial · business translation failed'],
          ['insufficient', 'Abstention · insufficient support'], ['empty', 'No evidence'], ['provider-error', 'Provider error'],
          ['context-changed', 'Index context changed'], ['unreachable', 'Server unreachable']]
        : [['full', 'Full draft'], ['plain-language', 'Plain-language · supported definition fixture'], ['partial', 'Partial · summary only'],
          ['insufficient', 'Abstention · insufficient support'], ['empty', 'No evidence'], ['provider-error', 'Provider error (simulated)']];
      scenarioSelect.replaceChildren(...scenarios.map(([value, text]) => h('option', {value, text})));
      $('#scenario-field').hidden = !(mock || !liveSynthesis);
      $('#scenario-label').textContent = mock ? 'Mock response' : 'Example state';
      $('#scenario-hint').textContent = mock ? 'Choose which response the mock backend returns, to test each state.' : 'Choose a prepared example. No live research runs.';
      $('#industry-field').hidden = !indexedMode;
      recordedMode = !mock && !config.live && libraryEnabled;
      $('#new-research').hidden = recordedMode; // asking is disabled here, so the control would be a dead end
      document.body.classList.toggle('replay-only', recordedMode); // hides follow-up prompts that cannot be used
      if (mock) $('#examples').hidden = true;
      if (mock) setMode('mock', 'This page was opened with ?mock=1. Papers, numbers, tables and charts are invented to test the interface. Do not use or quote anything here.');
      else if (config.live) { liveBudget = config.call_budget || null; setMode('live', liveText(config)); }
      else if (recordedMode) setMode('recorded', 'Open, check and review saved answers. Asking new questions is not available in this copy.');
      else setMode('demo', 'This backend serves prepared fixture examples only. Questions are not researched.');
      $('#risk-field').hidden = !indexedMode || mock;
      if (recordedMode) {
        $('#hero-title').textContent = 'What would you like to research?';
        $('#hero-sub').textContent = 'Answers from the indexed research papers, with every claim linked to the passage or table cell it came from. Asking new questions is not available in this copy, so start from saved research below.';
        form.hidden = true; $('#industry-inline').hidden = true; $('#examples').hidden = true;
        composerNote.textContent = '';
      } else if (!liveSynthesis) {
        $('#hero-title').textContent = 'Explore a research example.';
        $('#hero-sub').textContent = 'Read an answer. Follow a citation when you need the source.';
        composerNote.textContent = 'Synthetic demo · Questions are not executed.';
        $('.send-label').textContent = 'View example';
        if (untouchedQuestion) setQuery('How should the synthetic agents be evaluated?');
      } else if (!indexedMode) {
        $('#hero-title').textContent = 'Ask about this paper.';
        $('#hero-sub').textContent = 'Read an answer. Follow a citation when you need the source.';
        composerNote.textContent = 'Live LLM synthesis · This paper only · Recent successful turns included; older context may be dropped.';
        $('.send-label').textContent = 'Ask paper';
        if (untouchedQuestion) setQuery('What does this paper suggest about AI agents’ ability to improve AI training?');
      } else {
        const count = Number(config.index?.count || 0).toLocaleString();
        let status = `Persistent research index · ${count} passages`;
        composerNote.textContent = 'Independent questions; previous answers are not context.';
        if (config.arxiv_fallback) {
          $('#hero-sub').textContent = 'Search the library. If it lacks evidence, the app searches public arXiv papers using your topic.';
          composerNote.textContent += ' arXiv fallback enabled.';
        }
        if (config.index?.metadata?.human_acceptance === 'pending') {
          status = `Experimental research index · ${count} complete source passages · Human evaluation pending`;
        }
        if (config.support_selection) composerNote.textContent += ' Question coverage check enabled.';
        if (clarificationEnabled) composerNote.textContent = 'Clarification enabled · Recent successful turns are intent context, never evidence. New research clears context.';
        $('#mode-chip').title = status;
        $('.send-label').textContent = 'Research';
      }
      if (mock) composerNote.textContent = `Prototype with mock research data · ${composerNote.textContent}`;
      // Static mode description: shown in full on home, one line while reading (full text on hover).
      composerNote.classList.add('static');
      composerNote.title = composerNote.textContent;
      syncSettingsSummary();
      loadRecentBriefs();
      if (!demo) return;
      savedResult = demo;
      if (liveSynthesis) rememberAcceptedTurn(demo.result.request.query, demo);
      // Loading/retrying configuration must not discard a question typed while waiting.
      if (liveSynthesis && untouchedQuestion) setQuery('');
      $('#scenario-field').hidden = !mock;
      form.hidden = !liveSynthesis;
      if (!liveSynthesis) composerNote.title = composerNote.textContent = runLabel(demo);
      const number = ++turnNumber;
      const {turn, answer} = createTurn(demo.result.request.query, number, 'Executed query · Saved result', 'Loading saved result…');
      showTurn(turn);
      renderDemo(demo, number, answer);
    }).catch(error => {
      console.error(error);
      appReady = false;
      const retry = btn('Retry loading question entry', () => {
        retry.disabled = true;
        loadQuestionEntry().then(() => { if (appReady) queryInput.focus(); });
      }, 'text-btn', 'refresh');
      const reason = error?.message && error.message !== 'App configuration unavailable' && !(error instanceof TypeError) ? `${error.message} ` : 'Question entry unavailable: configuration or saved-result check failed. Your question is unchanged. ';
      $('#composer-note').classList.remove('static');
      $('#composer-note').title = '';
      $('#composer-note').replaceChildren(reason, retry);
      setMode('offline', /illustrative/i.test(reason) ? reason.trim() : `${reason}This page never substitutes illustrative answers.`);
      $('#new-research').hidden = true; // nothing can be researched without a backend
      $('#examples').hidden = true;
    }).finally(() => { setQuestionBusy(false); autosize(); });
  }
  syncTheme(); syncPrefs(); setView('home', false); autosize();
  /* ---------- Chart gallery (test page: ?gallery=1, needs serve.py --serve-tests) ----------
     Renders real verified tables from the research index, exported read-only into a test fixture,
     through the same renderEvidenceTable path an answer uses. It is labelled as not an answer:
     nothing is cited, no model is called, and no brief is created. */
  async function openGallery(question = '') {
    let data;
    try {
      const response = await fetch('/tests/fixtures/corpus-tables.json');
      if (!response.ok) throw new Error(String(response.status));
      data = await response.json();
    } catch {
      announce('The chart gallery needs the test fixtures: start serve.py with --serve-tests.');
      return;
    }
    thread.querySelector('.gallery')?.remove();
    const turn = h('section', {class: 'turn gallery', 'aria-labelledby': 'gallery-h'});
    const input = h('input', {id: 'gallery-question', type: 'text', maxlength: 300, value: question, placeholder: 'e.g. Which router has the best accuracy for its token cost?'});
    const form = h('form', {class: 'gallery-form', onsubmit: event => { event.preventDefault(); openGallery(input.value); }},
      h('label', {htmlFor: 'gallery-question', text: 'Try a question to see how it changes each default view'}), h('div', {class: 'row'}, input, h('button', {type: 'submit', class: 'quiet-btn', text: 'Apply'})));
    turn.append(h('div', {class: 'turn-head'},
      h('p', {class: 'question-label'}, h('span', {text: 'Chart gallery'}), h('span', {text: 'Test page'}), h('span', {text: `${Object.keys(data.tables).length} real tables`})),
      h('h1', {class: 'question', id: 'gallery-h', text: 'How each table shape is charted'}),
      note('Not a research answer. These are verified tables from the 100-paper research index, exported read-only into a test fixture (no model call). No row here is cited by an answer, so no takeaway or KPI tile appears.', 'warn', 'alert'),
      form));
    const block = h('section', {class: 'block block-numbers', id: 'gallery-numbers', 'data-group': 'evidence', 'data-nav': 'Gallery'},
      h('h2', {class: 'block-title', text: 'Tables and their eligible views'}));
    for (const [key, entry] of Object.entries(data.tables)) {
      const result = {evidence: entry.passages, summary: {status: 'ok', claims: []},
        provenance: {index: {indexed_records_sha256: data.index_sha256}}, request: {query: question}};
      const [table] = EM.buildTables(result);
      const merged = EM.mergeComplete(table, entry.full, data.index_sha256);
      const ctx = {demo: {result}, number: 900, question: () => question, openChart: true, chartChoice: new Map()};
      block.append(h('p', {class: 'gallery-purpose'}, h('span', {class: 'mono', text: key}), h('span', {text: ` · fixture purpose: ${entry.purpose}`})),
        renderEvidenceTable(merged.ok ? merged.table : table, ctx));
    }
    turn.append(block);
    thread.append(turn);
    for (const other of thread.querySelectorAll('.turn:not(.gallery)')) other.hidden = true;
    turn.hidden = false;
    setView('thread', false);
    $('#thread-title').textContent = 'Chart gallery (test page)';
  }

  loadQuestionEntry().then(() => {
    if (new URLSearchParams(location.search).get('gallery') === '1') { openGallery(); return; }
    if (appReady && !narrow.matches) queryInput.focus();
  });
})();

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
    copy: 'M9 9h10v10H9z|M5 15V5h10', info: 'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16z|M12 11v5|M12 8v.5',
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
    const titles = {live: 'Live research', recorded: 'Recorded replay', mock: 'Mock demo · not research output',
      demo: 'Synthetic examples · not research output', offline: 'Not connected'};
    const banner = $('#mode-banner');
    banner.dataset.tone = mode;
    $('#mode-banner-title').textContent = titles[mode] || mode;
    $('#mode-banner-text').textContent = text;
    const chip = $('#mode-chip');
    chip.hidden = false;
    chip.textContent = titles[mode] || mode;
    chip.className = `mode ${mode === 'live' ? 'ok' : mode === 'recorded' ? '' : 'warn'}`;
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
  }
  $('#theme-toggle').addEventListener('click', () => morph(() => { ReadingPrefs.set('theme', isDark() ? 'light' : 'dark'); }));
  document.addEventListener('reading-preferences-applied', () => { syncTheme(); syncPrefs(); });
  darkQuery.addEventListener('change', syncTheme);

  let currentView = 'home', activeTurn = null;
  function placeDock() {
    // One composer, moved to where it is used: the home page, or the end of the brief being read.
    if (currentView === 'home') $('#home-slot').append(dock);
    else if (currentView === 'thread' && activeTurn) $('.followup-slot', activeTurn)?.append(dock);
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
      if (view !== 'thread') scroller.scrollTop = 0;
    };
    if (animate) morph(change); else change();
  }
  $('#nav-research').addEventListener('click', () => setView(activeTurn ? 'thread' : 'home'));

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
  const explanationSeg = segmented('explanation-label', [['technical', 'Technical'], ['plain', 'Plain language']],
    ReadingPrefs.get('explanation'), value => ReadingPrefs.set('explanation', value));
  $('#explanation-seg').append(explanationSeg);
  const prefControls = {};
  (() => {
    const body = $('#prefs-body');
    const themeSelect = h('select', {id: 'reading-theme', onchange: event => morph(() => ReadingPrefs.set('theme', event.target.value))},
      [['system', 'System'], ['light', 'Light'], ['dark', 'Dark'], ['contrast-light', 'High contrast light'], ['contrast-dark', 'High contrast dark']]
        .map(([value, text]) => h('option', {value, text})));
    prefControls.theme = {select: value => { themeSelect.value = value; }};
    body.append(h('div', {class: 'field'}, h('label', {htmlFor: 'reading-theme', text: 'Theme'}), themeSelect));
    for (const [name, label, options] of [
      ['size', 'Text size', [['100', '100%'], ['125', '125%'], ['150', '150%'], ['200', '200%']]],
      ['spacing', 'Line spacing', [['standard', 'Standard'], ['relaxed', 'Relaxed'], ['wide', 'Wide']]],
      ['explanation', 'Explanation style', [['technical', 'Technical'], ['plain', 'Plain language']]]]) {
      prefControls[name] = segmented(`pref-${name}`, options, ReadingPrefs.get(name), value => ReadingPrefs.set(name, value));
      body.append(h('div', {class: 'field'}, h('span', {class: 'field-label', id: `pref-${name}`, text: label}), prefControls[name]));
    }
  })();
  function syncPrefs() {
    for (const name of Object.keys(prefControls)) prefControls[name].select(ReadingPrefs.get(name));
    explanationSeg.select(ReadingPrefs.get('explanation'));
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
  let enterBehavior = store.get(enterKey) === 'send' ? 'send' : 'newline';
  function updateEntryHint() {
    $('#entry-hint').textContent = `Enter ${enterBehavior === 'send' ? 'sends a question' : 'inserts a newline'}. Ctrl+Enter or Command+Enter sends. Shift+Enter always inserts a newline.`;
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
  scenarioSelect.addEventListener('change', syncSettingsSummary);
  function syncSettingsSummary() {
    const parts = [];
    if (industryInput.value.trim() && !$('#industry-field').hidden) parts.push(industryInput.value.trim());
    if (ReadingPrefs.get('explanation') === 'plain') parts.push('Plain language');
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
      if (passage.representation === 'linearized_table' && Array.isArray(passage.table_cells) && Array.isArray(passage.table_headers)) {
        const row = {table_row: passage.table_row, row_label: passage.row_label,
          cells: passage.table_cells.map(cell => ({...cell, parsed: EvidenceModel.parseNumber(cell.text)}))};
        const grid = rowGrid({headers: passage.table_headers}, row, highlightId);
        const anchor = passageView.querySelector('h4');
        const label = h('h4', {text: 'Table row as extracted'});
        const status = h('p', {class: 'meta', text: `${EvidenceModel.headerStatus(passage).label} ${highlightId ? `Selected cell: ${highlightId}.` : ''}`});
        if (anchor) anchor.before(label, grid, status); else passageView.append(label, grid, status);
      }
      passageView.classList.remove('swap'); void passageView.offsetWidth; passageView.classList.add('swap');
      ResearchSpeech.attach(passageView, {id: `source:${number}:${passage.chunk_id}`,
        label: `Citation ${index + 1} · ${citationSourceContext(passage)}`, text: ResearchSpeech.source(passage, index + 1)});
      document.querySelectorAll('.sources tr[data-active]').forEach(row => row.removeAttribute('data-active'));
      document.querySelector(`#turn-${number} .sources tr[data-passage="${index}"]`)?.setAttribute('data-active', '');
    }
    evidence.forEach((passage, index) => {
      const location = passage.source === 'pdf' && passage.page_number != null ? `page ${passage.page_number}` : sourceLocation(passage);
      choices.append(h('button', {type: 'button', class: 'source-tab', title: citationSourceContext(passage),
        'aria-label': `Citation ${index + 1}, ${passage.source.toUpperCase()}, ${location}`, onclick: () => selectPassage(index)},
        h('b', {text: String(index + 1)}), h('span', {text: `${passage.source.toUpperCase()} · ${location}`})));
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
      citation.title = 'See the source quote';
      citation.addEventListener('click', () => {
        dismissCiteHint();
        showQuote(item, demo, number, index, citation);
        quotePreview.querySelector('.quote-actions button').focus({preventScroll: true});
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
      h('header', {class: 'turn-head'}, h('p', {class: 'question-label', text: questionLabel}), question),
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
    thread.querySelectorAll(':scope > .turn').forEach(node => { node.hidden = node !== turn; });
    document.querySelectorAll('#session-list .rail-link').forEach(link => link.removeAttribute('aria-current'));
    $('.rail-link', turn.sessionEntry || document.createElement('i'))?.setAttribute('aria-current', 'true');
    $('#thread-title').textContent = $('.question', turn)?.textContent || '';
    setView('thread');
    placeDock();
    buildContents(turn);
    const turnDemo = turn.demoState;
    if (turnDemo) activeDemo = turnDemo;
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
  const TEX = /\\[a-zA-Z]+(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})*/g;
  function texText(node, text) {
    node.textContent = '';
    if (!text || !window.katex || !text.includes('\\')) { node.textContent = text; return node; }
    let last = 0;
    for (const match of text.matchAll(TEX)) {
      if (match.index > last) node.append(text.slice(last, match.index));
      const span = document.createElement('span');
      try { katex.render(match[0], span, {throwOnError: true, displayMode: false}); span.setAttribute('aria-hidden', 'true'); node.append(span); }
      catch { span.textContent = match[0]; node.append(span); }
      last = match.index + match[0].length;
    }
    if (last < text.length) node.append(text.slice(last));
    if (node.querySelector('.katex')) node.append(h('span', {class: 'sr-only', text}));
    return node;
  }

  /* ---------- Contents rail with section highlight ---------- */
  let spyFrame = 0;
  function buildContents(turn) {
    const nav = $('#contents');
    const blocks = turn ? [...turn.querySelectorAll('.block[data-nav]')] : [];
    nav.replaceChildren();
    if (!blocks.length) return;
    nav.append(h('h2', {class: 'rail-title', text: 'In this brief'}));
    const list = h('ol', {class: 'contents-list'});
    for (const block of blocks) {
      const link = h('button', {type: 'button', class: 'contents-link', onclick: () => {
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
    inspectorChrome('Table row', `${tableTitle(table)} · loaded from the index`,
      'This row was loaded from the research index to complete the table. It is not part of the evidence this answer retrieved or cited.');
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
    const figure = h('figure', {class: 'ev-figure', id: `a${ctx.number}-tbl-${table.table_id.replace(/[^A-Za-z0-9]/g, '-')}`});
    let mode = 'table', sort = {column: null, dir: 0}, plan = EM.chartPlan(table), fullNote = null;
    const view = h('div', {class: 'ev-view'});
    const flags = h('ul', {class: 'ev-flags'});
    const tabs = h('div', {class: 'seg ev-seg', role: 'tablist', 'aria-label': `${tableTitle(table)} view`});
    const tableTab = h('button', {type: 'button', role: 'tab', class: 'seg-btn', onclick: () => setMode('table')}, icon('table'), h('span', {text: 'Table'}));
    const chartTab = h('button', {type: 'button', role: 'tab', class: 'seg-btn', onclick: () => setMode('chart')}, icon('chart'), h('span', {text: 'Chart'}));
    tabs.append(tableTab, chartTab);
    const copy = h('button', {type: 'button', class: 'quiet-btn', onclick: async () => {
      try { await navigator.clipboard.writeText(tsv(table)); announce(`${tableTitle(table)} copied with its source line.`); }
      catch { announce('Copy is not available in this browser. Use Export instead.'); }
    }}, icon('copy'), h('span', {text: 'Copy'}));
    const open = table.html_url ? h('a', {class: 'quiet-btn', href: table.html_url, target: '_blank', rel: 'noopener noreferrer',
      'aria-label': `Open ${tableTitle(table)} in the paper, opens in a new tab`}, icon('external'), h('span', {text: 'Open in paper'})) : null;
    const chartReason = h('p', {class: 'ev-chart-reason'});

    function renderFlags() {
      flags.replaceChildren(
        table.completeness === 'complete_from_index'
          ? statusRow('check', 'ok', `All ${table.rows.length} rows of this table, loaded from the research index. ${table.retrievedCount} ${table.retrievedCount === 1 ? 'was' : 'were'} retrieved for this answer.`)
          : statusRow('alert', 'warn', `Showing the ${table.retrievedCount} row${table.retrievedCount === 1 ? '' : 's'} retrieved for this answer. The paper's table may contain more.`),
        statusRow(table.headerStatus.verified ? 'check' : 'alert', table.headerStatus.verified ? 'ok' : 'warn', table.headerStatus.label),
        table.fidelity === 'round_trip_ok'
          ? statusRow('check', 'ok', 'Every cell matches the cited source text exactly.')
          : statusRow('alert', 'bad', 'The structured cells did not match the cited source text. Only the source text is shown.'));
      if (fullNote) flags.append(statusRow('info', '', fullNote));
      if (table.notes.length) flags.append(h('li', {class: 'ev-flag'}, icon('info'), h('span', {text: `Source notes: ${table.notes.map(n => n.text).join(' ')}`})));
    }
    function setMode(next) {
      if (next === 'chart' && !plan.eligible) return;
      mode = next;
      tableTab.setAttribute('aria-selected', String(mode === 'table'));
      chartTab.setAttribute('aria-selected', String(mode === 'chart'));
      const swap = () => {
        view.querySelector('.ev-chart')?.dispose?.(); // stop the old chart's resize observer
        view.replaceChildren(mode === 'chart' ? chartView(table, plan, ctx) : tableView());
      };
      if (reduced.matches || !view.firstChild) swap();
      else { view.classList.remove('swap'); swap(); void view.offsetWidth; view.classList.add('swap'); }
    }
    function syncChartTab() {
      chartTab.disabled = !plan.eligible;
      chartTab.title = plan.eligible ? 'Show as a chart' : plan.reason;
      texText(chartReason, plan.eligible
        ? `Chart available: ${plan.panels.map(p => p.header).join(', ')}${plan.excluded.length ? `. Not charted: ${plan.excluded.map(e => `${e.header} (${e.reason})`).join('; ')}` : ''}.`
        : `No chart: ${plan.reason}`);
      chartReason.classList.toggle('off', !plan.eligible);
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
      return h('div', null,
        h('div', {class: 'table-scroll', tabIndex: 0, role: 'region', 'aria-label': `${tableTitle(table)}, scrollable`},
          h('table', {class: 'ev-table'}, h('caption', {class: 'sr-only', text: `${tableTitle(table)}: ${captionBody(table)}`}), h('thead', null, head), body)),
        legend);
    }

    const toolbar = h('div', {class: 'ev-toolbar'}, tabs, h('span', {class: 'grow'}), copy, open);
    figure.append(
      h('figcaption', {class: 'ev-caption'},
        h('p', {class: 'ev-title'}, h('span', {class: 'ev-name', text: tableTitle(table)}), h('span', {class: 'ev-paper', text: table.paper_title})),
        texText(h('p', {class: 'ev-text'}), captionBody(table))),
      flags, toolbar, chartReason, view);
    renderFlags(); syncChartTab(); setMode('table');

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
        renderFlags(); syncChartTab(); setMode(mode === 'chart' && plan.eligible ? 'chart' : 'table');
      });
    }
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
  function chartView(table, plan, ctx) {
    const wrap = h('div', {class: 'ev-chart'});
    const paired = plan.form === 'paired_dot';
    if (paired) {
      wrap.append(h('p', {class: 'chart-legend'},
        h('span', {class: 'key'}, h('span', {class: 'swatch a', 'aria-hidden': 'true'}), h('span', {text: plan.category.values[0]})),
        h('span', {class: 'key'}, h('span', {class: 'swatch b', 'aria-hidden': 'true'}), h('span', {text: plan.category.values[1]})),
        h('span', {class: 'legend-note', text: `Labels as written in the “${plan.category.header}” column.`})));
    }
    // The SVG sits in its own frame. When panels would be narrower than EM.MIN_PANEL_WIDTH the
    // chart keeps that width and the frame scrolls sideways (audit H1: never a reversed scale).
    const frame = h('div', {class: 'chart-frame'});
    const foot = h('p', {class: 'chart-foot'},
      'Each column has its own scale, running from its lowest to its highest value; the scale ends are labelled with those values. ',
      'Values are exactly as written in the table. Nothing is computed, converted or ranked.',
      plan.truncatedPanels ? ` ${plan.truncatedPanels} more chartable column(s) are in the table view.` : '');
    wrap.append(frame, foot);
    // ChartSvg.mount rebuilds the SVG only when its width changes (keeping focus), and recomputes
    // the scroll state on every frame-width change (audit L2; verification blocker 3).
    const chart = ChartSvg.mount({document, frame, table, plan, title: tableTitle(table),
      onOpen: (row, cell, trigger) => openRowSource(ctx, table, row, cell, trigger)});
    const draw = (options) => chart.update(Math.round(frame.clientWidth || wrap.clientWidth || 0), options);
    requestAnimationFrame(() => { if (wrap.isConnected) draw(); });
    // Redraw only while attached; a detached chart stops observing (audit L2).
    const observer = new ResizeObserver(() => { if (wrap.isConnected) draw(); else observer.disconnect(); });
    observer.observe(frame);
    wrap.dispose = () => observer.disconnect();
    wrap.redraw = () => draw({force: true});
    wrap.update = () => draw();
    return wrap;
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

  /* ---------- Brief rendering ---------- */
  function block(key, nav, title, number, ...children) {
    return h('section', {class: `block block-${key}`, id: `a${number}-${key}`, 'data-nav': nav, 'aria-labelledby': `a${number}-${key}-h`},
      h('h2', {class: 'block-title', id: `a${number}-${key}-h`, tabIndex: -1, text: title}), children);
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

  function renderBrief(demo, number, answer, tools) {
    const result = demo.result, insight = result.business_insight, view = demo.plain_language;
    const ctx = {demo, number};
    const tables = EM.buildTables(result);
    const studies = EM.studies(result);
    const checks = EM.verificationItems(demo, tables);
    const body = h('div', {class: 'brief'});
    if (window.MOCK_API === true) body.append(h('p', {class: 'mock-stamp', role: 'note'}, icon('alert'),
      h('span', {text: 'Mock answer for interface testing. The papers, numbers, tables and charts below are invented. They are not research output.'})));

    /* A. Summary: the answer, and a quiet status column beside it. */
    const claims = result.summary.claims.filter(claim => claim.kind !== 'interpretation');
    // An abstention leads with its own cited reasons instead of a bare "no answer".
    const abstained = result.summary.status !== 'ok';
    const scopedReasons = abstained && result.summary.limitation_support?.length ? result.summary.limitation_support : null;
    const plainReasons = abstained && !scopedReasons ? (result.summary.limitations || []) : [];
    const leadNode = result.summary.answer_lead
      ? h('p', {class: 'answer-lead', math: result.summary.answer_lead})
      : null;
    const fallback = h('p', {class: 'note warn', role: 'status', hidden: true});
    const trust = [];
    if (isSynthesis(demo)) trust.push('Citation IDs and source quotes checked');
    if (result.summary.quality_review) trust.push('automated support and relevance review applied (model judgment)');
    const reviewState = reviewText(demo);
    const reviewButton = h('button', {type: 'button', class: 'primary-btn', onclick: () => tools.reveal('brief')}, icon(demo.library ? 'shield' : 'bookmark'),
      h('span', {text: demo.library ? (demo.library.reviews.length ? 'Open brief & review' : 'Review this brief') : 'Save as brief'}));
    const facts = h('dl', {class: 'facts'},
      h('div', null, h('dt', {text: 'Status'}), h('dd', null, h('span', {class: `state ${reviewTone(demo)}`}, icon(reviewTone(demo) === 'ok' ? 'check' : 'shield'), h('span', {text: reviewState})))),
      h('div', null, h('dt', {text: 'Evidence'}), h('dd', {text: evidenceMix(result)})),
      h('div', null, h('dt', {text: 'Industry'}), h('dd', {text: insight?.industry || 'Not requested'})),
      h('div', null, h('dt', {text: 'Open checks'}), h('dd', null, h('a', {href: `#a${number}-verify`, class: 'link-btn', onclick: event => {
        event.preventDefault(); $(`#a${number}-verify`)?.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
        $(`#a${number}-verify-h`)?.focus({preventScroll: true});
      }, text: `${checks.length} item${checks.length === 1 ? '' : 's'} to verify`}))),
      h('div', null, h('dt', {text: 'Source'}), h('dd', {text: provenanceLabel(demo)})));
    const inspect = h('button', {type: 'button', class: 'quiet-btn', onclick: () => tools.inspect(inspect)}, icon('layers'),
      h('span', {text: `Inspect ${result.evidence.length} source${result.evidence.length === 1 ? '' : 's'}`}));
    const summary = h('section', {class: 'block block-summary', id: `a${number}-summary`, 'data-nav': 'Answer', 'aria-labelledby': `a${number}-summary-h`},
      h('h2', {class: 'sr-only block-title', id: `a${number}-summary-h`, tabIndex: -1, text: 'Answer'}),
      h('div', {class: 'summary-grid'},
        h('div', {class: 'summary-main'},
          leadNode || (claims[0] ? h('p', {class: 'answer-lead from-finding'}, cited('span', claims[0], demo, number))
            : h('p', {class: 'answer-lead', text: abstained ? 'The retrieved evidence does not support a full answer.' : 'No supported answer.'})),
          abstained && (scopedReasons || plainReasons.length) ? h('div', {class: 'why-not'}, h('h3', {text: 'Why there is no full answer'}),
            scopedReasons ? h('ul', {class: 'bullets'}, scopedReasons.map(item => cited('li', item, demo, number))) : bullets(plainReasons)) : null,
          !leadNode && claims[0] ? h('p', {class: 'lead-note', text: 'No separate summary was generated; this is the first supported finding.'}) : null,
          fallback,
          trust.length ? h('p', {class: 'trust'}, icon('shield'),
            h('span', {text: `${trust.join('; ').replace(/^./, c => c.toUpperCase())}. Claim support has not been independently verified by a person.`})) : null),
        h('aside', {class: 'summary-aside', 'aria-label': 'Brief status'}, facts, h('div', {class: 'aside-actions'}, reviewButton, inspect))));
    body.append(summary);

    /* Search and selection notes (unchanged wording). */
    const search = result.provenance?.arxiv_search;
    const searchMessages = {
      answered: ['arXiv search completed. Open the citations to see the papers found for this question.', ''],
      insufficient_evidence: ['arXiv search completed. The papers examined did not provide enough evidence.', 'warn'],
      unreadable: ['arXiv found papers, but the app could not extract readable text. The library result is shown below. Retry the question or rephrase it.', 'warn'],
      timeout: ['The arXiv search timed out. The library result is shown below. Retry the question or rephrase it.', 'warn'],
      failed: ['The arXiv search could not finish. The library result is shown below. Retry the question or rephrase it.', 'warn'],
      answer_failed: ['arXiv returned papers, but the app could not validate an answer. The library result is shown below. Retry the question or rephrase it.', 'warn'],
    };
    const notes = [];
    if (search && searchMessages[search.status]) {
      notes.push(note(searchMessages[search.status][0], searchMessages[search.status][1], 'search'));
      if (search.candidates?.length) {
        const found = h('details', {class: 'fold'}, h('summary', {text: `Papers examined on arXiv (${search.candidates.length})`}));
        found.append(h('ul', {class: 'bullets'}, search.candidates.map(candidate => {
          const safe = /^https?:\/\//.test(candidate.url || '');
          return h('li', null, safe ? h('a', {href: candidate.url, target: '_blank', rel: 'noopener noreferrer', text: candidate.title || candidate.arxiv_id})
            : h('span', {text: candidate.title || candidate.arxiv_id}), h('span', {class: 'muted', text: ` · ${candidate.arxiv_id} · ${candidate.status}`}));
        })), h('p', {class: 'muted small', text: `Search used: ${search.query}`}));
        notes.push(found);
      }
    } else if (result.provenance?.arxiv_fallback_enabled) notes.push(note('Sources from the loaded library.', '', 'book'));
    if (result.provenance?.evidence_selection_result?.status === 'selection_failed_baseline_retained') {
      notes.push(note('The question coverage check was unavailable. This answer uses the original source ranking; review its citations and limitations.', 'warn', 'alert'));
    }
    if (notes.length) $('.summary-main', summary).append(...notes);

    /* B. Findings. */
    const claimList = h('ol', {class: 'findings'});
    const claimNodes = [];
    for (const [index, claim] of result.summary.claims.entries()) {
      if (claim.kind === 'interpretation') continue;
      const node = cited('li', claim, demo, number);
      claimList.append(node); claimNodes.push({index, claim, node});
    }
    const findings = block('findings', 'Findings', 'Findings', number,
      claimNodes.length ? citeHint() : null,
      claimNodes.length ? claimList : h('p', {class: 'muted', text: 'No supported research claims.'}));
    const interpretations = result.summary.claims.filter(claim => claim.kind === 'interpretation');
    if (interpretations.length) {
      findings.append(h('div', {class: 'interpretation'}, h('h3', {text: 'Interpretation'}),
        h('p', {class: 'muted small', text: 'Inferred from the evidence; not a finding the studies validated.'}),
        interpretations.map(claim => cited('p', claim, demo, number))));
    }
    if (tables.some(t => !t.headerStatus.verified) && tables.some(t => t.rows.some(r => r.citedBy.length))) {
      findings.append(note('Table check needed: this answer cites extracted table rows whose column labels have not been verified. Compare the numbers and headings with the original paper before relying on them.', 'warn table-review-notice', 'alert'));
    }
    const definitions = h('details', {class: 'fold'}, h('summary', {text: 'Technical term definitions'}));
    const viewNote = h('p', {class: 'muted small'});
    if (view?.status === 'available') {
      viewNote.textContent = `${view.fixture ? 'Synthetic fixture demonstration. ' : ''}Meaning and uncertainty review pending. Only research findings are rewritten; interpretations, business actions, assumptions, limitations and source passages stay unchanged.`;
      for (const definition of view.definitions) {
        definitions.append(h('div', {class: 'definition'}, h('p', {class: 'term', text: definition.term}),
          definition.status === 'supported' ? cited('p', definition, demo, number) : h('p', {class: 'muted', text: `Definition unavailable: ${definition.reason}`})));
      }
      if (!view.definitions.length) definitions.append(h('p', {class: 'muted', text: 'No supported term definitions supplied.'}));
    } else {
      viewNote.textContent = view?.reason || 'Plain-language generation is unavailable. The original answer is retained.';
      definitions.append(h('p', {class: 'muted', text: 'Definitions unavailable: no validated supporting material supplied.'}));
    }
    definitions.append(h('p', {class: 'term', text: 'Plain-language rewrite details'}), viewNote);
    findings.append(definitions);
    body.append(findings);

    /* C. The numbers: reconstructed tables, with charts only where the rules allow. */
    if (tables.length) {
      body.append(block('numbers', 'Numbers', 'The numbers behind the findings', number,
        h('p', {class: 'block-intro', text: 'Tables retrieved from the papers, rebuilt cell by cell from each paper’s HTML. Values appear exactly as written in the source; select one to open where it came from.'}),
        tables.map(table => renderEvidenceTable(table, ctx))));
    }

    /* D. Study comparison: only when the evidence spans two or more papers. */
    if (studies.length >= 2) {
      body.append(block('compare', 'Comparison', 'How the studies compare', number,
        h('p', {class: 'block-intro', text: 'What each paper’s retrieved evidence actually covers. Use this to see what can and cannot be compared.'}),
        renderStudies(studies, ctx)));
    }

    /* E. Business implications. */
    if (insight || !isSynthesis(demo) || demo.error?.stage === 'business') {
      const business = block('business', 'Implications', insight ? `What it could mean for ${insight.industry}` : 'Business implications', number);
      if (!insight) {
        business.append(h('p', {class: 'muted', text: demo.error?.stage === 'business'
          ? 'Generating business implications failed. The supported research summary above is retained. Retry to request them again.' : 'Business translation was not requested.'}));
      } else {
        business.append(h('p', {class: 'block-intro', text: 'Conditional interpretations for business use. These are not findings the studies validated.'}));
        if (!insight.implications.length) business.append(h('p', {class: 'muted', text: 'No supported business recommendations.'}));
        const list = h('div', {class: 'insights'});
        for (const implication of insight.implications) {
          const item = h('article', {class: 'insight'}, cited('p', implication, demo, number, 'insight-text'),
            h('div', {class: 'action'}, h('h3', {text: 'Suggested action'}), h('p', {math: implication.suggested_action})));
          if (implication.assumptions?.length) {
            item.append(h('details', {class: 'fold'}, h('summary', {text: `Assumptions, not research findings (${implication.assumptions.length})`}), bullets(implication.assumptions)));
          }
          list.append(item);
        }
        business.append(list);
      }
      body.append(business);
    } else if (!insight && isSynthesis(demo) && !$('#industry-field').hidden && demo.scenario !== 'insufficient' && demo.scenario !== 'empty') {
      body.append(block('business', 'Implications', 'Business implications', number,
        h('p', {class: 'muted', text: 'Business translation was not requested for this answer.'}),
        h('div', {class: 'row'}, btn('Add an industry to get business implications',
          () => requestBusinessInsights(result.request?.query || demo.submitted_request?.query || ''), 'quiet-btn', 'bulb'))));
    }

    /* Risk & compliance checkpoint (optional, advisory). */
    const checkpoint = result.regulatory_checkpoint;
    if (checkpoint) {
      const assessed = checkpoint.status === 'assessed';
      const regulatoryEvidence = checkpoint.regulatory_evidence;
      const regulatory = block('regulatory', 'Risk & compliance', 'Risk and compliance assessment', number,
        h('p', {class: 'block-intro', text: `${assessed ? 'Assessed' : `Assessment ${checkpoint.status}`}. Advisory only. Human review required. Not legal advice or compliance approval.`}));
      if (checkpoint.jurisdiction || regulatoryEvidence?.jurisdiction) {
        regulatory.append(h('p', {class: 'muted small', text: `Jurisdiction: ${checkpoint.jurisdiction || regulatoryEvidence.jurisdiction} · As of: ${regulatoryEvidence?.as_of || 'not recorded'}`}));
      }
      if (!assessed || !checkpoint.assessment) {
        regulatory.append(note(`Assessment ${checkpoint.status}: ${checkpoint.reason || 'No assessment was produced.'}`, 'warn', 'alert'),
          h('p', {class: 'muted small', text: 'No regulatory conclusion was produced. The research findings and business implications above are unaffected.'}));
      } else {
        regulatory.append(h('p', {math: checkpoint.summary || ''}));
        const grid = h('div', {class: 'two-col'});
        for (const [key, title] of [['regulatory_compliance', 'Regulatory compliance'], ['legal_constraints', 'Legal constraints'],
          ['governance', 'Governance'], ['operational_feasibility', 'Operational feasibility']]) {
          const finding = checkpoint.assessment[key];
          if (!finding) continue;
          const sources = (regulatoryEvidence?.sources || []).filter(source => (finding.source_ids || []).includes(source.source_id));
          grid.append(h('div', {class: 'col'}, h('h3', {text: `${title} · ${finding.status}`}), h('p', {math: finding.explanation || ''}),
            sources.length ? h('ul', {class: 'bullets'}, sources.map(source => h('li', null, /^https?:\/\//.test(source.url || '')
              ? h('a', {href: source.url, target: '_blank', rel: 'noopener noreferrer', text: source.title || `Regulatory source ${source.source_id}`})
              : h('span', {text: source.title || `Regulatory source ${source.source_id}`})))) : null));
        }
        regulatory.append(grid);
        if (checkpoint.assessment.risks?.length) regulatory.append(h('h3', {text: 'Identified risks'}), bullets(checkpoint.assessment.risks));
        regulatory.append(h('p', {class: 'muted small', text: 'Sources and applicability have not been independently verified by a human.'}));
      }
      body.append(regulatory);
    }

    /* F. Risks and limitations: two plain columns, no cards. */
    const scoped = isSynthesis(demo) && result.summary.limitation_support?.length ? result.summary.limitation_support : null;
    const shown = new Set((scoped || []).map(item => item.text.trim()));
    const extra = (result.summary.limitations || []).filter(text => !shown.has(String(text).trim()));
    const limitsCol = h('div', {class: 'col'}, h('h3', {text: 'Limitations of the evidence'}));
    if (abstained && (scopedReasons || plainReasons.length)) {
      limitsCol.append(h('p', {class: 'muted', text: 'Shown at the top, under “Why there is no full answer”.'}));
    } else {
      if (scoped) limitsCol.append(h('ul', {class: 'bullets'}, scoped.map(item => cited('li', item, demo, number))));
      if (extra.length) limitsCol.append(bullets(extra));
      if (!scoped && !extra.length) limitsCol.append(h('p', {class: 'muted', text: 'None stated by the answer.'}));
    }
    const riskCol = h('div', {class: 'col'}, h('h3', {text: 'Risks'}));
    riskCol.append(insight?.risks?.length ? bullets(insight.risks) : h('p', {class: 'muted', text: insight ? 'None stated.' : 'Risks are stated with business implications; none were requested.'}));
    const risks = block('risks', 'Risks & limits', 'Risks and limitations', number, h('div', {class: 'two-col'}, riskCol, limitsCol));
    if (insight?.limitations?.length) risks.append(h('div', {class: 'col single'}, h('h3', {text: 'Limits of the business implications'}), bullets(insight.limitations)));
    body.append(risks);

    /* G. Before you rely on this: one list, each item tied to the field it comes from. */
    const checklist = h('ol', {class: 'checklist'}, checks.map(item => h('li', null, h('span', {class: 'box', 'aria-hidden': 'true'}),
      h('div', null, h('p', {text: item.text}), h('p', {class: 'origin', text: `From ${item.origin}`})))));
    const verify = block('verify', 'Before you rely on it', 'Before you rely on this', number,
      h('p', {class: 'block-intro', text: 'What a person still needs to check. Nothing here is a new warning; each item comes from the answer’s own records.'}),
      checklist,
      h('div', {class: 'verify-foot'}, h('p', null, h('span', {class: `state ${reviewTone(demo)}`}, icon('shield'), h('span', {text: reviewState}))),
        h('button', {type: 'button', class: 'quiet-btn', onclick: () => tools.reveal('brief')}, h('span', {text: demo.library ? 'Record a review' : 'Save to record a review'}))));
    body.append(verify);

    /* H. Sources. */
    const rows = result.evidence.map((passage, index) => {
      const count = [result.summary.claims, result.summary.limitation_support, insight?.implications]
        .flatMap(group => group || []).filter(item => item.chunk_ids?.includes(passage.chunk_id)).length;
      const open = h('button', {type: 'button', class: 'source-open', 'aria-label': `Inspect source ${index + 1}, ${citationSourceContext(passage)}`,
        onclick: () => showEvidence(demo, number, index, open)}, h('span', {class: 'source-title', text: passage.title}),
        h('span', {class: 'source-where', text: sourceLocation(passage)}));
      const row = h('tr', {onclick: event => { if (!event.target.closest('button')) open.click(); }},
        h('td', {class: 'num'}, h('span', {class: 'cite-num', text: String(index + 1)})), h('td', null, open),
        h('td', null, h('span', {class: 'kind', text: passage.representation === 'linearized_table' ? 'Table row' : passage.source === 'pdf' ? 'PDF text' : 'Text'})),
        h('td', {class: 'num', text: count ? `${count} ${count === 1 ? 'statement' : 'statements'}` : 'Not cited'}));
      row.dataset.passage = index;
      return row;
    });
    body.append(block('sources', 'Sources', 'Sources', number,
      rows.length ? h('div', {class: 'table-scroll'}, h('table', {class: 'sources'},
        h('thead', null, h('tr', null, ['#', 'Source', 'Kind', 'Cited by'].map(text => h('th', {scope: 'col', text})))), h('tbody', null, rows)))
        : h('p', {class: 'muted', text: 'No passages were retrieved.'})));

    /* Plain-language reading preference (unchanged rules). */
    function selectView() {
      closePreview();
      const plain = document.documentElement.dataset.readingExplanation === 'plain';
      for (const entry of claimNodes) {
        const rewrite = plain && view?.status === 'available' ? view.claims[entry.index] : null;
        const node = cited('li', rewrite ? {...entry.claim, text: rewrite.text, support: rewrite.support} : entry.claim, demo, number);
        if (rewrite) node.classList.add('rewritten');
        entry.node.replaceWith(node); entry.node = node;
      }
      claimList.classList.toggle('plain', plain && view?.status === 'available');
      const unavailable = plain && view?.status !== 'available';
      fallback.hidden = !unavailable;
      fallback.textContent = unavailable ? `Plain language unavailable for this answer. ${view?.reason || 'The original answer is retained.'}` : '';
    }
    explanationRenderers.set(answer, selectView);
    selectView();
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
    briefPanel(panel, demo, onChanged);
    $('#review-heading').textContent = demo.library ? 'Brief and review' : 'Save this answer';
    $('#review-kicker').textContent = demo.library ? `Brief · version ${demo.library.version.number}` : 'Brief';
    reviewBody.replaceChildren(panel);
    reviewBody.scrollTop = 0;
    setReview(true, trigger);
    $('#review-heading').focus({preventScroll: true});
  }

  function answerTools(demo, number, answer, onChanged) {
    const real = isReal(demo);
    const bar = h('div', {class: 'tools', role: 'group', 'aria-label': `Answer ${number} tools`});
    const panels = h('div', {class: 'tool-panels'});
    const entries = [];
    function tool(key, label, iconName, build) {
      const panel = h('div', {class: 'tool-panel', id: `a${number}-panel-${key}`, hidden: true});
      const button = h('button', {type: 'button', class: 'quiet-btn tool', 'aria-expanded': 'false', 'aria-controls': panel.id}, icon(iconName), h('span', {text: label}));
      let built = false;
      const entry = {key, set(open) {
        if (open && !built) { build(panel); built = true; }
        panel.hidden = !open; button.setAttribute('aria-expanded', String(open));
      }};
      button.addEventListener('click', () => {
        const open = panel.hidden;
        entries.forEach(item => item.set(false));
        entry.set(open);
        if (open) panel.scrollIntoView({block: 'nearest', behavior: reduced.matches ? 'auto' : 'smooth'});
      });
      entries.push(entry); bar.append(button); panels.append(panel);
      return entry;
    }
    tool('export', 'Export', 'download', panel => {
      panel.append(h('p', {class: 'panel-title', text: 'Export this result'}),
        h('p', {class: 'muted small', text: 'Exports stay pending drafts. They are not approval or source certification.'}),
        AnswerExport.controls(demo, number), snapshotButton(demo));
    });
    tool('listen', 'Listen', 'volume', panel => ResearchSpeech.attach(panel, ResearchSpeech.result(demo, number)));
    tool('details', 'Run details', 'code', panel => {
      panel.append(h('div', null, h('p', {class: 'panel-title', text: real ? 'Run details & result JSON' : 'Run details & demo JSON'}),
        h('p', {text: `${real ? 'Executed query' : 'Fixed example'}: ${demo.result.request.query}`}),
        h('p', {class: 'muted', text: real ? runLabel(demo) : STATES[demo.scenario][1]}),
        !real && h('p', {class: 'muted', text: `Your question (not executed): ${demo.submitted_request.query}`}),
        h('pre', {class: 'json', tabIndex: 0, text: JSON.stringify(demo, null, 2)})));
    });
    const appendix = block('appendix', 'Export & details', 'Export, audio and run details', number, bar, panels);
    const open = key => {
      if (key === 'brief') return openReview(demo, number, onChanged, document.activeElement);
      entries.forEach(entry => entry.set(entry.key === key));
    };
    return {
      appendix, open,
      reveal: key => open(key),
      inspect: trigger => showEvidence(demo, number, 0, trigger),
    };
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
    if (label2) {
      label2.replaceChildren(...[h('span', {class: `state ${tone}`}, h('span', {text: label})),
        demo.library?.replayed ? h('span', {text: 'Saved snapshot · No new research executed'}) : null,
        Number.isFinite(seconds) ? h('span', {text: `Research took ${seconds.toFixed(1)} s`}) : null,
        demo.mode === 'indexed' ? h('span', {text: demo.history_policy === 'server_owned_bounded_intent_only' ? 'Indexed research · Bounded conversation' : 'Indexed research · Independent query'}) : null,
        demo.result?.provenance?.arxiv_search ? h('span', {text: 'arXiv fallback used'}) : null,
        demo.result?.summary.answer_scope === 'partial' ? h('span', {class: 'state warn', text: 'Partial coverage of the question'}) : null].filter(Boolean));
    }
    answer.replaceChildren(answerHeading(number));
    if (demo.result) {
      const onChanged = updated => {
        ResearchSpeech.stopAll();
        renderDemo(updated, number, answer);
        openReview(updated, number, onChanged, null);
        loadRecentBriefs();
      };
      const tools = answerTools(demo, number, answer, onChanged);
      if (!['full', 'plain-language'].includes(demo.scenario)) answer.append(note(explanation, tone === 'ok' ? '' : tone, tone === 'ok' ? 'info' : 'alert'));
      if (demo.error) answer.append(note(`${{regulatory: 'Risk & compliance', business: 'Business translation'}[stage] || stage || 'Error'}: ${demo.error.message || demo.error}`, stage === 'regulatory' ? 'warn error' : 'bad error', 'alert'));
      const brief = renderBrief(demo, number, answer, tools);
      brief.append(tools.appendix);
      if (demo.library_error) openReview(demo, number, onChanged, null);
      turn.demoState = {demo, number};
      if (turn === activeTurn) activeDemo = turn.demoState;
      if (document.body.classList.contains('insp-open') && turn === activeTurn) showEvidence(demo, number);
      $('#evidence-toggle').hidden = false;
      markAnswerReady(answer);
      announce(readyAnnouncement(demo, number), false);
      if (liveSynthesis && !demo.library?.replayed) refreshBudget();
      return tools;
    }
    answer.append(h('div', {class: 'block block-failed'}, note(demo.error?.message || String(demo.error || 'No answer was produced.'), 'bad error', 'alert')));
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
    const loading = indexedMode ? (clarificationEnabled ? 'Checking your question and researching its evidence…' : 'Searching the research index and synthesizing supported findings…') : liveSynthesis ? 'Reading the paper and synthesizing an answer…' : 'Loading local example…';
    const {turn, answer} = createTurn(query, number, clarificationPending ? 'Your clarification answer' : liveSynthesis ? 'Your question' : 'Your question · Not executed', loading);
    showTurn(turn);
    resetEvidence('Loading a new answer. No current evidence to inspect.');
    setQuestionBusy(true);
    suggestions.hidden = true;
    announce(loading, false);
    let contextRecoveryMessage = null, responseReceived = false;
    try {
      const response = await fetch(liveSynthesis ? '/api/research' : '/api/demo', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query, scenario, ...(revision ? {library_revision: {...revision}} : {}), ...(submissionContext || {})}),
        // Indexed: context, two clarification gates, summary and translation (5 × 300s + 60s).
        signal: AbortSignal.timeout((indexedMode ? 1560000 : liveSynthesis ? 330000 : 10000) + (liveSynthesis && presentationEnabled ? 300000 : 0)),
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
        contextRecoveryMessage = typeof demo.error === 'string' ? demo.error : demo.error.message;
        throw new Error('Research execution failed.');
      }
      renderDemo(demo, number, answer);
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
      const message = contextRecoveryMessage || (timeout
        ? 'The research request timed out. Your question is unchanged. Check that the demo server is running before retrying.'
        : !responseReceived
          ? 'Cannot reach the local demo server. Restart the demo, refresh this page, and retry your question.'
          : liveSynthesis
            ? 'The server response could not be displayed. No answer was accepted. Your question is unchanged; retry when ready.'
            : 'Could not load the local example. Your question is unchanged; retry when ready.');
      if (!contextRecoveryMessage && responseReceived) console.error(error);
      answer.replaceChildren(h('header', {class: 'answer-head'}, answerHeading(number), h('div', {class: 'chips'}, chip('No answer accepted', 'bad'))),
        note(message, 'bad error', 'alert'));
      offerRetry(answer, query, scenario, submissionContext, pendingTurn);
      markAnswerReady(answer);
      announce(contextRecoveryMessage && !indexedMode ? 'Paper changed. Context cleared; submit your question again.' : `Answer ${number} failed. Your question is unchanged; retry when ready.`);
      resetEvidence('The latest answer did not load. Retry to inspect its evidence.');
    } finally {
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
  const REVIEW_LABELS = {pending: 'Draft', approve: 'Approved', revise: 'Changes requested', reject: 'Rejected'};
  const reviewLabel = status => REVIEW_LABELS[status] || status || 'Draft';
  const statusTone = text => (/approved/i.test(text) && !/not approved/i.test(text) ? 'ok' : /change|revise/i.test(text) ? 'warn' : /reject/i.test(text) ? 'bad' : 'draft');
  function briefRow(brief, status) {
    const label = reviewLabel(brief.review_status);
    const open = h('button', {type: 'button', class: 'brief-open'},
      h('span', {class: 'brief-title', text: brief.title}),
      h('span', {class: 'brief-meta'},
        h('span', {class: `state ${statusTone(label)}`}, icon(statusTone(label) === 'ok' ? 'check' : 'shield'), h('span', {text: label})),
        h('span', {text: `Version ${brief.number}`}),
        h('span', {text: brief.mode === 'fixture' ? 'Synthetic example' : 'Research snapshot'}),
        h('span', {text: when(brief.updated_at)})),
      icon('chevron'));
    open.addEventListener('click', () => openSaved(open, status, `/api/briefs/${brief.id}`));
    return h('li', null, open);
  }
  async function loadLibrary() {
    const sequence = ++loadSequence;
    libraryStatus.textContent = 'Loading saved briefs…'; libraryStatus.classList.remove('bad');
    briefList.setAttribute('aria-busy', 'true');
    try {
      const params = new URLSearchParams({q: briefSearch.value, archived: briefArchived.checked ? '1' : '0', offset});
      const data = await api(`/api/briefs?${params}`);
      if (sequence !== loadSequence) return;
      briefList.replaceChildren(...data.briefs.map(brief => briefRow(brief, libraryStatus)));
      $('#brief-previous').disabled = offset === 0;
      $('#brief-next').disabled = data.briefs.length < 30;
      libraryStatus.textContent = data.briefs.length ? `Showing ${offset + 1}–${offset + data.briefs.length}.` : 'No saved briefs here. Generate an answer or import a result JSON file.';
    } catch (error) { if (sequence === loadSequence) libraryStatus.textContent = error.message || 'Could not load saved briefs. Try Refresh.'; }
    finally { if (sequence === loadSequence) briefList.setAttribute('aria-busy', 'false'); }
  }
  async function loadRecentBriefs() {
    if (!libraryEnabled) return;
    try {
      const data = await api('/api/briefs?q=&archived=0&offset=0');
      const status = h('span');
      $('#recent-briefs').replaceChildren(...data.briefs.slice(0, 4).map(brief => briefRow(brief, status)));
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

  function briefPanel(panel, demo, onChanged) {
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
    const reviewPane = [];
    if (current) {
      const reviewer = h('input', {type: 'text', required: true, maxLength: 120, autocomplete: 'name', id: `${panel.id}-reviewer`});
      const notes = h('textarea', {maxLength: 4000, rows: 2, id: `${panel.id}-notes`});
      // The backend refuses approval while a requested risk & compliance check is unresolved.
      const gate = demo.result.regulatory_checkpoint;
      const approvalBlocked = Boolean(gate) && gate.assessment?.verdict !== 'potentially_feasible';
      let decision = approvalBlocked ? 'revise' : 'approve';
      const decisions = h('div', {class: 'decisions', role: 'radiogroup', 'aria-label': 'Review decision'});
      for (const [value, label, hint, iconName] of [['approve', 'Approve this version', approvalBlocked ? 'Unavailable: the risk & compliance assessment is unresolved.' : 'Records human approval of this exact snapshot.', 'check'],
        ['revise', 'Request changes', 'Notes are required.', 'pencil'], ['reject', 'Reject this version', 'Marks the snapshot as not usable.', 'x']]) {
        decisions.append(h('label', {class: `decision ${value}`}, h('input', {type: 'radio', name: `${panel.id}-decision`, value, checked: value === decision, disabled: value === 'approve' && approvalBlocked,
          onchange: () => { decision = value; }}), icon(iconName), h('span', null, h('strong', {text: label}), h('small', {text: hint}))));
      }
      const send = h('button', {type: 'submit', class: 'solid-btn'}, icon('shield'), h('span', {text: 'Record review'}));
      const reviewForm = h('form', {class: 'review-form', onsubmit: event => {
        event.preventDefault();
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
      activePaperContextId = config.paper_context_id || null;
      indexedMode = config.mode === 'indexed';
      indexedContextId = config.context_id || null;
      clarificationEnabled = config.clarification === true;
      researchConversationId = config.conversation_id || null;
      setClarificationPending(false);
      const mock = window.MOCK_API === true;
      // Scenario choice exists for fixtures (existing demo options) and for the mock backend.
      const scenarios = mock
        ? [['full', 'Full answer'], ['clarification', 'Ask a clarifying question first'], ['partial', 'Partial · business translation failed'],
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
      if (mock) $('#examples').hidden = true;
      if (mock) setMode('mock', 'This page was opened with ?mock=1. Papers, numbers, tables and charts are invented to test the interface. Do not use or quote anything here.');
      else if (config.live) { liveBudget = config.call_budget || null; setMode('live', liveText(config)); }
      else if (recordedMode) setMode('recorded', 'Saved answers from earlier live runs, replayed exactly. Asking new questions is disabled; nothing here calls a model.');
      else setMode('demo', 'This backend serves prepared fixture examples only. Questions are not researched.');
      $('#risk-field').hidden = !indexedMode || mock;
      if (recordedMode) {
        $('#hero-title').textContent = 'Recorded research briefs';
        $('#hero-sub').textContent = 'Research is not running in this session. Open a brief recorded from a live run; its answer, evidence and review history are replayed exactly, with no model call.';
        form.hidden = true; $('#industry-inline').hidden = true; $('#examples').hidden = true;
        composerNote.textContent = 'Replay only. Start a research backend to ask new questions.';
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
      $('#examples').hidden = true;
    }).finally(() => { setQuestionBusy(false); autosize(); });
  }
  syncTheme(); syncPrefs(); setView('home', false); autosize();
  loadQuestionEntry().then(() => { if (appReady && !narrow.matches) queryInput.focus(); });
})();

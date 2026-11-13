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
    for (const child of children.flat()) if (child != null && child !== false) node.append(child);
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
  let needsDivider = false, toastTimer, libraryEnabled = false, revision = null;
  const explanationRenderers = new WeakMap();

  /* ---------- Status ---------- */
  function announce(message, visible = true) {
    toastNode.textContent = message;
    clearTimeout(toastTimer);
    toastNode.classList.toggle('show', visible && Boolean(message));
    if (visible) toastTimer = setTimeout(() => toastNode.classList.remove('show'), 5200);
  }

  /* ---------- Shell: sidebar, theme, view ---------- */
  const sidebarKey = 'research-desk.sidebar.v1';
  function setSidebar(collapsed, persist = true) {
    document.body.classList.toggle('sb-collapsed', collapsed);
    $('#sb-toggle').setAttribute('aria-expanded', String(!collapsed));
    $('#sb-toggle').setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
    if (persist) store.set(sidebarKey, collapsed ? '1' : '0');
  }
  function setDrawer(open) {
    document.body.classList.toggle('sb-drawer', open);
    syncScrim();
    if (open) $('#new-research').focus(); else if (narrow.matches) $('#sb-open').focus();
  }
  function syncScrim() {
    const show = narrow.matches && (document.body.classList.contains('sb-drawer') || document.body.classList.contains('insp-open'));
    $('#scrim').hidden = !show;
    stage.inert = show;
  }
  setSidebar(store.get(sidebarKey) === '1', false);
  $('#sb-toggle').addEventListener('click', () => {
    if (narrow.matches) setDrawer(false); else setSidebar(!document.body.classList.contains('sb-collapsed'));
  });
  $('#sb-open').addEventListener('click', () => setDrawer(true));
  $('#scrim').addEventListener('click', () => {
    if (document.body.classList.contains('insp-open')) setInspector(false); else setDrawer(false);
  });
  narrow.addEventListener('change', () => { document.body.classList.remove('sb-drawer'); syncScrim(); });

  const darkQuery = matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => { const t = ReadingPrefs.get('theme'); return t.includes('dark') || (t === 'system' && darkQuery.matches); };
  function syncTheme() {
    const toggle = $('#theme-toggle');
    toggle.replaceChildren(icon(isDark() ? 'sun' : 'moon'), h('span', {class: 'sb-label', text: isDark() ? 'Light theme' : 'Dark theme'}));
    toggle.title = isDark() ? 'Switch to light theme' : 'Switch to dark theme';
  }
  $('#theme-toggle').addEventListener('click', () => morph(() => { ReadingPrefs.set('theme', isDark() ? 'light' : 'dark'); }));
  document.addEventListener('reading-preferences-applied', () => { syncTheme(); syncPrefs(); });
  darkQuery.addEventListener('change', syncTheme);

  function setView(view, animate = true) {
    const home = view === 'home';
    if (stage.classList.contains('is-home') === home) return;
    const change = () => {
      stage.classList.toggle('is-home', home);
      $('#hero').hidden = !home; thread.hidden = home; $('#examples').hidden = !home;
      $('#thread-title').classList.toggle('show', !home);
      if (home) { suggestions.hidden = true; jumpLatest.hidden = true; }
    };
    if (animate) morph(change); else change();
  }

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
  for (const name of ['Banking', 'Insurance', 'Healthcare', 'Retail']) {
    $('#industry-quick').append(btn(name, () => { industryInput.value = name.toLowerCase(); syncSettingsSummary(); }, 'quick-chip'));
  }
  industryInput.addEventListener('input', syncSettingsSummary);
  scenarioSelect.addEventListener('change', syncSettingsSummary);
  function syncSettingsSummary() {
    const parts = [];
    if (industryInput.value.trim() && !$('#industry-field').hidden) parts.push(industryInput.value.trim());
    if (ReadingPrefs.get('explanation') === 'plain') parts.push('Plain language');
    if (!$('#scenario-field').hidden && scenarioSelect.selectedIndex > 0) parts.push(scenarioSelect.selectedOptions[0].textContent);
    $('#settings-summary').textContent = parts.join(' · ');
  }
  function setSettings(open) {
    $('#settings').classList.toggle('open', open);
    $('#settings').inert = !open;
    $('#settings-toggle').setAttribute('aria-expanded', String(open));
  }
  $('#settings-toggle').addEventListener('click', () => setSettings(!$('#settings').classList.contains('open')));
  function autosize() {
    queryInput.style.height = 'auto';
    queryInput.style.height = `${Math.min(queryInput.scrollHeight, 240)}px`;
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
    'How reliable are AI agents for compliance review in retail banking?',
    'What does a verification step add to cited AI summaries for insurance claims?',
    'Can cited AI summaries be trusted without checking the sources?',
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
  function showEvidence(demo, number, selected = 0, trigger = null, claim = null) {
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
    } else if (document.body.classList.contains('sb-drawer')) {
      setDrawer(false); event.preventDefault();
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
      citation.addEventListener('click', () => {
        showQuote(item, demo, number, index, citation);
        quotePreview.querySelector('.quote-actions button').focus({preventScroll: true});
      });
      node.append(' ', citation);
    }
    return node;
  }

  /* ---------- Turns ---------- */
  function answerHeading(number, text = `Answer ${number}`) {
    return h('h3', {id: `answer-${number}`, class: 'answer-kicker', tabIndex: -1, text});
  }
  function elapsedCounter() {
    // The endpoint answers once with a single envelope; this only shows that the wait is alive.
    const node = h('span', {class: 'muted small elapsed', 'aria-hidden': 'true'});
    const started = performance.now();
    const timer = setInterval(() => {
      if (!node.isConnected) return clearInterval(timer);
      const seconds = Math.round((performance.now() - started) / 1000);
      if (seconds >= 4) node.textContent = `${seconds}s`;
    }, 1000);
    return node;
  }
  function createTurn(query, number, questionLabel, loading) {
    if (needsDivider && thread.children.length) thread.append(h('p', {class: 'divider', text: 'New conversation · earlier answers are not context'}));
    needsDivider = false;
    const question = h('h2', {id: `question-${number}`, class: 'question', text: query});
    const answer = h('article', {class: 'answer', 'aria-labelledby': `answer-${number}`}, answerHeading(number),
      h('div', {class: 'loading'}, h('div', {class: 'loading-line'}, h('span', {class: 'orb'}), h('p', {text: loading}), elapsedCounter()),
        h('div', {class: 'skeleton'}, h('i'), h('i'), h('i'), h('i'))));
    const turn = h('section', {class: 'turn', id: `turn-${number}`, 'aria-labelledby': question.id},
      h('p', {class: 'question-label', text: `Question ${number} · ${questionLabel}`}), question, answer);
    $('#session-section').hidden = false;
    $('#session-list').prepend(h('li', null, h('button', {type: 'button', class: 'sb-link', title: query, text: query, onclick: () => {
      setView('thread'); if (narrow.matches) setDrawer(false);
      turn.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
    }})));
    $('#thread-title').textContent = query;
    return {turn, answer};
  }
  function showTurn(turn) {
    setView('thread');
    thread.append(turn);
    requestAnimationFrame(() => turn.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'}));
  }
  function markAnswerReady(answer) {
    latestAnswer = $('.answer-kicker', answer);
    syncJump();
  }
  function syncJump() {
    // Offer the jump only when the latest answer is entirely outside the reading area.
    const box = latestAnswer?.closest('.answer')?.getBoundingClientRect(), frame = scroller.getBoundingClientRect();
    const away = box && (box.bottom < frame.top + 40 || box.top > frame.bottom - 40);
    jumpLatest.hidden = !away || stage.classList.contains('is-home');
  }
  scroller.addEventListener('scroll', syncJump, {passive: true});
  // Only an explicit navigation action moves reading focus to a new answer.
  jumpLatest.addEventListener('click', () => {
    latestAnswer?.focus({preventScroll: true});
    latestAnswer?.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
  });

  const chip = (text, tone, iconName) => h('span', {class: `chip ${tone || ''}`}, iconName && icon(iconName), h('span', {text}));
  const sectionHead = (id, title, iconName, extra) => h('div', {class: 'section-head'}, icon(iconName), h('h4', {id, text: title, tabIndex: -1}), extra);
  function bullets(items) { return h('ul', {class: 'bullets'}, items.map(item => h('li', {math: item}))); }
  function note(text, tone = '', iconName) { return h('p', {class: `note ${tone}`}, iconName && icon(iconName), h('span', {text})); }

  function renderDraft(demo, number, answer) {
    const result = demo.result, insight = result.business_insight, view = demo.plain_language;
    const body = h('div', {class: 'answer-body'});
    const nav = h('nav', {class: 'answer-nav', 'aria-label': `Answer ${number} sections`});
    const section = (key, label, ...children) => {
      const node = h('section', {class: `block block-${key}`, 'aria-labelledby': `a${number}-${key}`}, children);
      nav.append(h('button', {type: 'button', class: 'nav-pill', text: label, onclick: () => {
        node.scrollIntoView({block: 'start', behavior: reduced.matches ? 'auto' : 'smooth'});
        $(`#a${number}-${key}`).focus({preventScroll: true});
      }}));
      body.append(node);
      return node;
    };
    if (result.summary.answer_lead) body.append(h('p', {class: 'lead', math: result.summary.answer_lead}));
    body.append(nav);
    const fallback = h('p', {class: 'note warn', role: 'status', hidden: true});
    body.append(fallback);
    // One trust line instead of separate notes repeating that nothing was independently verified.
    const checks = [];
    if (isSynthesis(demo)) checks.push('Citation IDs and source quotes checked');
    if (result.summary.quality_review) checks.push('automated support and relevance review applied (model judgment)');
    if (checks.length) {
      const text = checks.join('; ');
      body.append(note(`${text.charAt(0).toUpperCase()}${text.slice(1)}. Claim support has not been independently verified by a person.`, 'trust', 'shield'));
    }
    const search = result.provenance?.arxiv_search;
    const searchMessages = {
      answered: ['arXiv search completed. Open the citations to see the papers found for this question.', ''],
      insufficient_evidence: ['arXiv search completed. The papers examined did not provide enough evidence.', 'warn'],
      unreadable: ['arXiv found papers, but the app could not extract readable text. The library result is shown below. Retry the question or rephrase it.', 'warn'],
      timeout: ['The arXiv search timed out. The library result is shown below. Retry the question or rephrase it.', 'warn'],
      failed: ['The arXiv search could not finish. The library result is shown below. Retry the question or rephrase it.', 'warn'],
      answer_failed: ['arXiv returned papers, but the app could not validate an answer. The library result is shown below. Retry the question or rephrase it.', 'warn'],
    };
    if (search && searchMessages[search.status]) {
      body.append(note(searchMessages[search.status][0], searchMessages[search.status][1], 'search'));
      if (search.candidates?.length) {
        const found = h('details', {class: 'fold'}, h('summary', {text: `Papers examined on arXiv (${search.candidates.length})`}));
        const items = h('ul', {class: 'bullets'});
        for (const candidate of search.candidates) {
          const safe = /^https?:\/\//.test(candidate.url || '');
          items.append(h('li', null, safe ? h('a', {href: candidate.url, target: '_blank', rel: 'noopener noreferrer', text: candidate.title || candidate.arxiv_id})
            : h('span', {text: candidate.title || candidate.arxiv_id}), h('span', {class: 'muted', text: ` · ${candidate.arxiv_id} · ${candidate.status}`})));
        }
        found.append(items, h('p', {class: 'muted small', text: `Search used: ${search.query}`}));
        body.append(found);
      }
    } else if (result.provenance?.arxiv_fallback_enabled) {
      body.append(note('Sources from the loaded library.', '', 'book'));
    }
    if (result.provenance?.evidence_selection_result?.status === 'selection_failed_baseline_retained') {
      body.append(note('The question coverage check was unavailable. This answer uses the original source ranking; review its citations and limitations.', 'warn', 'alert'));
    }

    /* Research findings */
    const claimList = h('ol', {class: 'claims'});
    const claimNodes = [];
    for (const [index, claim] of result.summary.claims.entries()) {
      if (claim.kind === 'interpretation') continue;
      const node = cited('li', claim, demo, number);
      claimList.append(node); claimNodes.push({index, claim, node});
    }
    const findings = section('findings', 'Findings', sectionHead(`a${number}-findings`, 'Research findings', 'book'),
      result.summary.claims.length ? claimList : h('p', {class: 'muted', text: 'No supported research claims.'}));
    const interpretations = result.summary.claims.filter(claim => claim.kind === 'interpretation');
    if (interpretations.length) {
      findings.append(h('div', {class: 'interpretation'}, h('p', {class: 'tag', text: 'Interpretation'}),
        h('p', {class: 'muted small', text: 'Inferences from the evidence—not findings validated by the study.'}),
        interpretations.map(claim => cited('p', claim, demo, number))));
    }
    if (isSynthesis(demo)) {
      // Scope & limitations are shown once, under Risks & limits (with their citations).
      const citedIds = new Set();
      for (const groups of [result.summary.claims, result.summary.limitation_support, insight?.implications]) {
        for (const item of groups || []) {
          for (const id of item.chunk_ids || []) citedIds.add(id);
          for (const support of item.support || []) citedIds.add(support.chunk_id);
        }
      }
      if ((result.evidence || []).some(passage => citedIds.has(passage.chunk_id) && passage.representation === 'linearized_table' && passage.header_review !== 'verified')) {
        findings.append(note('Table check needed: this answer cites extracted table rows whose column labels have not been verified. Compare the numbers and headings with the original paper before relying on them.', 'warn table-review-notice', 'alert'));
      }
    }

    /* Business insights */
    if (insight || !isSynthesis(demo) || demo.error?.stage === 'business') {
      const business = section('business', 'Business insights',
        sectionHead(`a${number}-business`, 'Business insights', 'bulb', insight && chip(`Industry: ${insight.industry}`, 'accent')));
      if (!insight) business.append(h('p', {class: 'muted', text: demo.error?.stage === 'business'
        ? 'Generating business implications failed. The supported research summary above is retained. Retry to request them again.' : 'Business translation was not requested.'}));
      else {
        business.append(h('p', {class: 'muted small', text: 'Conditional interpretations for business use—not findings validated by the study.'}));
        if (!insight.implications.length) business.append(h('p', {class: 'muted', text: 'No supported business recommendations.'}));
        const cards = h('div', {class: 'insights'});
        insight.implications.forEach((implication, index) => {
          const card = h('div', {class: 'insight'}, h('span', {class: 'insight-num', text: String(index + 1).padStart(2, '0')}),
            cited('p', implication, demo, number, 'insight-text'),
            h('div', {class: 'action'}, icon('arrow'), h('div', null, h('p', {class: 'action-label', text: 'Suggested action'}), h('p', {math: implication.suggested_action}))));
          if (implication.assumptions?.length) {
            card.append(h('details', {class: 'fold'}, h('summary', {text: `Assumptions · not research findings (${implication.assumptions.length})`}), bullets(implication.assumptions)));
          }
          cards.append(card);
        });
        business.append(cards);
      }
    }

    /* Risk & compliance checkpoint (optional, advisory). Its sources are separate from academic citations. */
    const checkpoint = result.regulatory_checkpoint;
    if (checkpoint) {
      const assessed = checkpoint.status === 'assessed';
      const regulatoryEvidence = checkpoint.regulatory_evidence;
      const regulatory = section('regulatory', 'Risk & compliance', sectionHead(`a${number}-regulatory`, 'Risk & compliance assessment', 'shield',
        chip(assessed ? 'Assessed' : `Assessment ${checkpoint.status}`, assessed ? 'ok' : 'warn')),
        h('p', {class: 'muted small', text: 'Advisory only · Human review required · Not legal advice or compliance approval.'}));
      if (checkpoint.jurisdiction || regulatoryEvidence?.jurisdiction) {
        regulatory.append(h('p', {class: 'muted small', text: `Jurisdiction: ${checkpoint.jurisdiction || regulatoryEvidence.jurisdiction} · As of: ${regulatoryEvidence?.as_of || 'not recorded'}`}));
      }
      if (!assessed || !checkpoint.assessment) {
        regulatory.append(note(`Assessment ${checkpoint.status}: ${checkpoint.reason || 'No assessment was produced.'}`, 'warn', 'alert'),
          h('p', {class: 'muted small', text: 'No regulatory conclusion was produced. The research findings and business insights above are unaffected.'}));
      } else {
        regulatory.append(h('p', {math: checkpoint.summary || ''}));
        const cards = h('div', {class: 'risk-grid'});
        for (const [key, title] of [['regulatory_compliance', 'Regulatory compliance'], ['legal_constraints', 'Legal constraints'],
          ['governance', 'Governance'], ['operational_feasibility', 'Operational feasibility']]) {
          const finding = checkpoint.assessment[key];
          if (!finding) continue;
          const card = h('div', {class: 'risk-card'}, h('p', {class: 'risk-title'}, icon('shield'), h('span', {text: `${title} · ${finding.status}`})),
            h('p', {math: finding.explanation || ''}));
          const sources = (regulatoryEvidence?.sources || []).filter(source => (finding.source_ids || []).includes(source.source_id));
          if (sources.length) {
            card.append(h('ul', {class: 'bullets'}, sources.map(source => h('li', null, /^https?:\/\//.test(source.url || '')
              ? h('a', {href: source.url, target: '_blank', rel: 'noopener noreferrer', text: source.title || `Regulatory source ${source.source_id}`})
              : h('span', {text: source.title || `Regulatory source ${source.source_id}`})))));
          }
          cards.append(card);
        }
        regulatory.append(cards);
        if (checkpoint.assessment.risks?.length) regulatory.append(h('h5', {text: 'Identified risks'}), bullets(checkpoint.assessment.risks));
        regulatory.append(h('p', {class: 'muted small', text: 'Sources and applicability have not been independently verified by a human.'}));
      }
    }

    /* Risks, limitations and review status */
    const riskCards = h('div', {class: 'risk-grid'});
    const riskCard = (title, items, tone, iconName) => {
      if (items?.length) riskCards.append(h('div', {class: `risk-card ${tone}`}, h('p', {class: 'risk-title'}, icon(iconName), h('span', {text: title})), bullets(items)));
    };
    riskCard('Risks', insight?.risks, 'warn', 'alert');
    const scoped = isSynthesis(demo) && result.summary.limitation_support?.length ? result.summary.limitation_support : null;
    if (scoped) {
      // Keep every summary limitation: cited ones first, then any uncited ones not already shown.
      const shown = new Set(scoped.map(item => item.text.trim()));
      const extra = (result.summary.limitations || []).filter(text => !shown.has(String(text).trim()));
      riskCards.append(h('div', {class: 'risk-card'}, h('p', {class: 'risk-title'}, icon('book'), h('span', {text: 'Scope & limitations'})),
        h('div', {class: 'scoped'}, scoped.map(item => cited('p', item, demo, number, 'scope'))), extra.length ? bullets(extra) : null));
    } else riskCard('Scope & limitations', result.summary.limitations, '', 'book');
    riskCard('Business limitations', insight?.limitations, '', 'bulb');
    // Assumptions stay attached to each business insight (one place, next to the claim they qualify).
    riskCards.append(h('div', {class: `risk-card review ${reviewTone(demo)}`}, h('p', {class: 'risk-title'}, icon('shield'), h('span', {text: 'Review status'})),
      h('p', {text: demo.library ? reviewText(demo) : 'No reviewer has approved this draft. Save it as a brief to record a review.'})));
    section('risks', 'Risks & limits', sectionHead(`a${number}-risks`, 'Risks, assumptions & limitations', 'alert'), riskCards);

    /* Sources table: each row opens the evidence inspector on that passage */
    const rows = result.evidence.map((passage, index) => {
      const count = [result.summary.claims, result.summary.limitation_support, insight?.implications]
        .flatMap(group => group || []).filter(item => item.chunk_ids?.includes(passage.chunk_id)).length;
      const open = h('button', {type: 'button', class: 'source-open', 'aria-label': `Inspect source ${index + 1}, ${citationSourceContext(passage)}`,
        onclick: () => showEvidence(demo, number, index, open)}, h('span', {class: 'source-title', text: passage.title}),
        h('span', {class: 'source-where', text: sourceLocation(passage)}));
      const row = h('tr', {onclick: event => { if (!event.target.closest('button')) open.click(); }},
        h('td', null, h('span', {class: 'cite-num', text: String(index + 1)})), h('td', null, open),
        h('td', null, chip(passage.source.toUpperCase(), 'mono')),
        h('td', {class: 'num', text: count ? `${count} ${count === 1 ? 'statement' : 'statements'}` : 'Not cited'}));
      row.dataset.passage = index;
      return row;
    });
    section('sources', `Sources (${result.evidence.length})`, sectionHead(`a${number}-sources`, 'Sources', 'layers',
      h('span', {class: 'muted small', text: `${result.evidence.length} retrieved ${result.evidence.length === 1 ? 'passage' : 'passages'}`})),
      rows.length ? h('div', {class: 'table-wrap'}, h('table', {class: 'sources'},
        h('thead', null, h('tr', null, ['#', 'Source', 'Format', 'Cited by'].map(text => h('th', {scope: 'col', text})))), h('tbody', null, rows)))
        : h('p', {class: 'muted', text: 'No passages were retrieved.'}));

    /* Plain-language view (reading preference), unchanged rules */
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
  }
  document.addEventListener('reading-preferences-change', () => {
    for (const answer of document.querySelectorAll('.answer')) explanationRenderers.get(answer)?.();
  });

  /* Tool row under each answer: evidence, brief, export, listen, run details */
  function answerTools(demo, number, answer, onChanged) {
    const real = isReal(demo);
    const bar = h('div', {class: 'tools', role: 'group', 'aria-label': `Answer ${number} tools`});
    const panels = h('div', {class: 'tool-panels'});
    const entries = [];
    function tool(key, label, iconName, build) {
      const panel = h('div', {class: 'tool-panel', id: `a${number}-panel-${key}`, hidden: true});
      const button = h('button', {type: 'button', class: 'tool', 'aria-expanded': 'false', 'aria-controls': panel.id}, icon(iconName), h('span', {text: label}));
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
    const evidenceButton = h('button', {type: 'button', class: 'tool primary', onclick: () => showEvidence(demo, number, 0, evidenceButton)},
      icon('layers'), h('span', {text: `Inspect evidence (${demo.result.evidence.length})`}));
    bar.append(evidenceButton);
    tool('brief', demo.library ? `Brief · v${demo.library.version.number}` : 'Save brief', 'bookmark', panel => briefPanel(panel, demo, onChanged));
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
    answer.append(bar, panels);
    return {open: key => entries.forEach(entry => entry.set(entry.key === key))};
  }
  function snapshotButton(demo) {
    return btn('Export snapshot JSON', () => {
      const url = URL.createObjectURL(new Blob([JSON.stringify(demo, null, 2)], {type: 'application/json'}));
      const link = h('a', {href: url, download: 'research-snapshot.json'}); link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, 'quiet', 'download');
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
    const chips = h('div', {class: 'chips'}, chip(label, tone),
      demo.result && chip(reviewText(demo), reviewTone(demo), 'shield'),
      demo.result?.summary.answer_scope === 'partial' && chip('Partial coverage of the question', 'warn'),
      demo.result?.provenance?.arxiv_search && chip('arXiv fallback used', 'accent', 'search'),
      demo.mode === 'indexed' && chip(demo.history_policy === 'server_owned_bounded_intent_only' ? 'Indexed research · Bounded conversation' : 'Indexed research · Independent query'),
      demo.library?.replayed && chip('Saved snapshot · No new research executed', '', 'history'),
      Number.isFinite(seconds) && chip(`Research processing time: ${seconds.toFixed(1)} seconds`, '', 'clock'));
    answer.replaceChildren(h('header', {class: 'answer-head'}, answerHeading(number), chips));
    if (demo.result) {
      if (!['full', 'plain-language'].includes(demo.scenario)) answer.append(note(explanation, tone === 'ok' ? '' : tone));
      renderDraft(demo, number, answer);
      if (demo.error) answer.append(note(`${{regulatory: 'Risk & compliance', business: 'Business translation'}[stage] || stage || 'Error'}: ${demo.error.message || demo.error}`, stage === 'regulatory' ? 'warn error' : 'bad error', 'alert'));
      const tools = answerTools(demo, number, answer, updated => {
        ResearchSpeech.stopAll();
        const reopened = renderDemo(updated, number, answer);
        reopened?.open('brief');
        $('.tool[aria-controls$="panel-brief"]', answer)?.focus({preventScroll: true});
        loadRecentBriefs();
      });
      if (demo.library_error) tools.open('brief');
      // Keep an open inspector current without opening one over the answer.
      activeDemo = {demo, number};
      if (document.body.classList.contains('insp-open')) showEvidence(demo, number);
      $('#evidence-toggle').hidden = false;
      markAnswerReady(answer);
      announce(readyAnnouncement(demo, number), false);
      return tools;
    }
    answer.append(note(demo.error?.message || String(demo.error || 'No answer was produced.'), 'bad error', 'alert'));
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
      throw error;
    }
    return data;
  }
  async function operation(control, message, action) {
    if (control.disabled) return;
    control.disabled = true;
    try { await action(); }
    catch (error) {
      const timeout = ['TimeoutError', 'AbortError'].includes(error?.name);
      message.textContent = timeout ? 'The saved-work request timed out. Nothing was changed; retry when ready.'
        : error instanceof TypeError ? 'Cannot reach the local server. Nothing was changed; retry when it is running.'
          : error.message || 'Saved-work request failed. Your answer is unchanged.';
      message.classList.add('bad');
      // 409: this snapshot is stale (another version, review or archive happened). Offer the current one.
      if (error.status === 409 && message.recover) message.append(' ', message.recover());
    }
    finally { control.disabled = false; }
  }
  const when = value => new Date(value).toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'});
  const libraryDialog = $('#library'), briefList = $('#brief-list'), libraryStatus = $('#library-status');
  const briefSearch = $('#brief-search'), briefArchived = $('#brief-archived');
  let offset = 0, loadSequence = 0, restoreLibraryFocus = true;
  function openSnapshot(demo) {
    if (libraryDialog.open) { restoreLibraryFocus = false; libraryDialog.close(); }
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
    const open = h('button', {type: 'button', class: 'brief-open'}, h('span', {class: 'brief-title', text: brief.title}),
      h('span', {class: 'brief-meta'}, chip(`v${brief.number}`, 'mono'), chip(reviewLabel(brief.review_status), statusTone(reviewLabel(brief.review_status))),
        h('span', {text: `${brief.mode === 'fixture' ? 'Synthetic example' : 'Research snapshot'} · ${when(brief.updated_at)}`})));
    open.addEventListener('click', () => operation(open, status, async () => openSnapshot(await api(`/api/briefs/${brief.id}`))));
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
      libraryStatus.textContent = data.briefs.length ? `Showing ${offset + 1}–${offset + data.briefs.length}. Reopening uses saved evidence; no model call.` : 'No saved briefs here. Generate an answer or import a result JSON file.';
    } catch (error) { if (sequence === loadSequence) libraryStatus.textContent = error.message || 'Could not load saved briefs. Try Refresh.'; }
    finally { if (sequence === loadSequence) briefList.setAttribute('aria-busy', 'false'); }
  }
  async function loadRecentBriefs() {
    if (!libraryEnabled) return;
    try {
      const data = await api('/api/briefs?q=&archived=0&offset=0');
      const status = h('span');
      $('#recent-briefs').replaceChildren(...data.briefs.slice(0, 5).map(brief => {
        const link = h('button', {type: 'button', class: 'sb-link', title: brief.title}, h('span', {class: `dot ${statusTone(reviewLabel(brief.review_status))}`}), h('span', {text: brief.title}));
        link.addEventListener('click', () => operation(link, status, async () => {
          if (narrow.matches) setDrawer(false);
          openSnapshot(await api(`/api/briefs/${brief.id}`));
        }));
        return h('li', null, link);
      }));
      $('#recent-section').hidden = !data.briefs.length;
    } catch { $('#recent-section').hidden = true; }
  }
  $('#library-open').addEventListener('click', () => {
    if (narrow.matches) setDrawer(false);
    libraryDialog.showModal(); briefSearch.focus(); offset = 0; loadLibrary();
  });
  $('#library-close').addEventListener('click', () => libraryDialog.close());
  libraryDialog.addEventListener('close', () => { if (restoreLibraryFocus) $('#library-open').focus(); restoreLibraryFocus = true; });
  $('#library-search-form').addEventListener('submit', event => { event.preventDefault(); offset = 0; loadLibrary(); });
  briefArchived.addEventListener('change', () => { offset = 0; loadLibrary(); });
  $('#brief-previous').addEventListener('click', () => { offset = Math.max(0, offset - 30); loadLibrary(); });
  $('#brief-next').addEventListener('click', () => { offset += 30; loadLibrary(); });
  function importControl(label, target, onSaved, message) {
    const input = h('input', {type: 'file', accept: '.json,application/json', class: 'sr-only'});
    input.addEventListener('change', () => operation(input, message, async () => {
      if (!input.files[0]) return;
      if (input.files[0].size > 8_000_000) throw new Error('Snapshot exceeds 8 MB.');
      const value = JSON.parse(await input.files[0].text());
      const saved = await api('/api/briefs', {...(value.result ? {envelope: value} : {result: value}), ...(target || {})});
      input.value = ''; await onSaved(saved);
    }));
    return h('label', {class: 'quiet file'}, icon('upload'), h('span', {text: label}), input);
  }
  $('#library-import').append(importControl('Import result JSON', null, async saved => {
    libraryStatus.textContent = 'Snapshot imported. No model call.'; loadRecentBriefs(); openSnapshot(saved);
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
    const message = h('p', {class: `hint ${demo.library_error ? 'bad' : ''}`, role: 'status', text: demo.library_error || ''});
    if (!libraryEnabled || !demo.library) {
      const save = btn('Save as separate brief', () => operation(save, message, async () => onChanged(await api('/api/briefs', {envelope: demo}))), 'solid-btn', 'bookmark');
      panel.append(h('p', {class: 'panel-title', text: 'Save this answer'}),
        h('p', {class: 'muted small', text: libraryEnabled ? 'Saving keeps this exact answer and its evidence as version 1 of a brief. Reviews and later versions attach to it.' : 'Persistent library disabled for this session.'}),
        h('div', {class: 'row'}, libraryEnabled && save, snapshotButton(demo)), message);
      return;
    }
    const {brief, version, versions, reviews} = demo.library;
    message.recover = () => {
      const reopen = btn('Reopen the latest version', () => operation(reopen, message,
        async () => openSnapshot(await api(`/api/briefs/${brief.id}`))), 'text-btn', 'refresh');
      return reopen;
    };
    const current = !brief.archived && version.id === brief.current_version;
    const isLatest = version.id === brief.current_version;
    const title = h('input', {type: 'text', maxLength: 200, value: brief.title, class: 'title-input', 'aria-label': 'Brief title'});
    const rename = btn('Rename brief', () => operation(rename, message, async () =>
      onChanged(await api(`/api/briefs/${brief.id}`, {expected_version: version.id, title: title.value}))), 'quiet', 'pencil');
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
      const open = btn('Open this version', () => operation(open, message, async () =>
        openSnapshot(await api(`/api/briefs/${brief.id}?version=${item.id}`))), 'text-btn', 'arrow');
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
        operation(send, message, async () => onChanged(await api(`/api/briefs/${brief.id}/reviews`, {version_id: version.id,
          fingerprint: version.fingerprint, reviewer: reviewer.value, decision, notes: notes.value || null})));
      }}, decisions,
        h('div', {class: 'field'}, h('label', {htmlFor: reviewer.id, text: 'Reviewer name'}), reviewer),
        h('div', {class: 'field'}, h('label', {htmlFor: notes.id, text: 'Review notes (required for changes)'}), notes), send);
      reviewPane.push(reviewForm);
    } else reviewPane.push(note(brief.archived ? 'Restore this brief before adding versions or reviews.' : 'Historical version. Open the latest version before revising or reviewing.', 'warn', 'history'));
    reviewPane.push(h('p', {class: 'term', text: `Review history for version ${version.number}`}),
      reviews.length ? history : h('p', {class: 'muted small', text: 'No reviews recorded for this version.'}));
    tab('review', `Review${reviews.length ? ` (${reviews.length})` : ''}`, 'shield', reviewPane);

    /* Manage */
    const archive = btn(brief.archived ? 'Restore brief' : 'Archive brief', () => operation(archive, message, async () =>
      onChanged(await api(`/api/briefs/${brief.id}`, {expected_version: version.id, archived: !brief.archived}))), 'quiet', 'archive');
    archive.disabled = !isLatest;
    tab('manage', 'Manage', 'sliders', [h('div', {class: 'row'},
      current && liveSynthesis && btn('Revise with new research', () => reviseBrief(demo), 'solid-btn', 'refresh'),
      current && importControl('Import a new version JSON', {brief_id: brief.id, expected_version: version.id}, onChanged, message),
      snapshotButton(demo), archive),
      h('p', {class: 'muted small', text: 'Original result JSON and existing HTML/Markdown exports remain pending drafts; library decisions are retained separately in snapshot JSON.'})]);
    panel.append(tabs, panes);
    tabNodes[demo.library.replayed === false && reviews.length ? 1 : 0].button.click();
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
      const modeChip = $('#mode-chip');
      modeChip.hidden = false;
      modeChip.textContent = mock ? 'Prototype · mock data' : liveSynthesis ? 'Live backend' : 'Synthetic demo';
      modeChip.classList.toggle('ok', !mock && liveSynthesis);
      $('#risk-field').hidden = !indexedMode || mock;
      if (!liveSynthesis) {
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
        $('#index-status').textContent = status;
        $('.send-label').textContent = 'Research';
      }
      if (mock) composerNote.textContent = `Prototype with mock research data · ${composerNote.textContent}`;
      syncSettingsSummary();
      loadRecentBriefs();
      if (!demo) return;
      savedResult = demo;
      if (liveSynthesis) rememberAcceptedTurn(demo.result.request.query, demo);
      // Loading/retrying configuration must not discard a question typed while waiting.
      if (liveSynthesis && untouchedQuestion) setQuery('');
      $('#scenario-field').hidden = !mock;
      form.hidden = !liveSynthesis;
      if (!liveSynthesis) composerNote.textContent = runLabel(demo);
      const number = ++turnNumber;
      const {turn, answer} = createTurn(demo.result.request.query, number, 'Executed query · Saved result', 'Loading saved result…');
      setView('thread', false);
      thread.append(turn);
      renderDemo(demo, number, answer);
    }).catch(error => {
      console.error(error);
      appReady = false;
      const retry = btn('Retry loading question entry', () => {
        retry.disabled = true;
        loadQuestionEntry().then(() => { if (appReady) queryInput.focus(); });
      }, 'text-btn', 'refresh');
      const reason = error?.message && error.message !== 'App configuration unavailable' && !(error instanceof TypeError) ? `${error.message} ` : 'Question entry unavailable: configuration or saved-result check failed. Your question is unchanged. ';
      $('#composer-note').replaceChildren(reason, retry);
    }).finally(() => { setQuestionBusy(false); autosize(); });
  }
  syncTheme(); syncPrefs(); autosize();
  loadQuestionEntry().then(() => { if (appReady && !narrow.matches) queryInput.focus(); });
})();

/* Prose is text; explicitly delimited math uses locally bundled, untrusted KaTeX. */
const form = document.querySelector('#research-form');
const output = document.querySelector('#output');
const conversation = document.querySelector('#conversation');
const feedback = document.querySelector('#feedback');
const submit = document.querySelector('#submit');
const rail = document.querySelector('#evidence-panel');
const railContent = document.querySelector('#evidence-content');
const railHeading = document.querySelector('#evidence-heading');
const quotePreview = document.querySelector('#citation-preview');
const mobile = matchMedia('(max-width: 800px)');
let turnNumber = 0;
let returnFocus = null;
let previewTrigger = null;
let previewTimer;
let activeDemo = null;
let savedResult = null;
let liveSynthesis = false;
const isSynthesis = demo => demo.mode === 'live-synthesis' || demo.result?.summary.generation_method === 'cited-synthesis-v1';
const isReal = demo => demo.mode !== 'fixture';
const runLabel = demo => {
  if (isSynthesis(demo)) return 'LLM synthesis · Citation quotes checked · Not independently verified';
  const generation = demo.result?.provenance?.generation;
  return generation?.provider || generation?.prompt_version
    ? 'Saved research result · Recorded generation provenance in Details · Not independently verified'
    : 'Saved research result · Generation method unverified · Inspect provenance in Details';
};
const STATES = {
  full: ['Full draft', 'Research summary and conditional business implications are available.'],
  partial: ['Partial draft', 'The research summary is available. Business translation abstained.'],
  insufficient: ['Abstention · insufficient support', 'Passages are available, but do not support an answer.'],
  empty: ['No evidence', 'No passages were retrieved. Generation was skipped.'],
  'provider-error': ['Provider error · simulated', 'No draft was produced. Choose another example state to continue.'],
};

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) {
    if (['p', 'li', 'blockquote'].includes(tag)) renderPaperMath(node, text);
    else node.textContent = text;
  }
  if (className) node.className = className;
  return node;
}

function disclosure(title) {
  const node = element('details');
  node.append(element('summary', title));
  return node;
}

function list(parent, title, items) {
  if (!items?.length) return;
  if (title) parent.append(element('h3', title));
  const ul = element('ul');
  for (const item of items) ul.append(element('li', item));
  parent.append(ul);
}

function setRailOpen(open, trigger = null) {
  if (open && !rail.open) {
    returnFocus = trigger;
    if (mobile.matches) rail.showModal();
    else rail.show();
  } else if (!open && rail.open) {
    rail.close();
    returnFocus?.focus();
  }
}

document.querySelector('#evidence-close').addEventListener('click', () => setRailOpen(false));
rail.addEventListener('cancel', event => {
  event.preventDefault();
  setRailOpen(false);
});
mobile.addEventListener('change', () => {
  if (!rail.open) return;
  rail.close();
  setRailOpen(true, returnFocus);
});

function resetEvidence(message) {
  closePreview();
  activeDemo = null;
  railContent.replaceChildren(element('p', message, 'meta rail-empty'));
}

function showEvidence(demo, number, selected = 0, trigger = null) {
  activeDemo = {demo, number, selected};
  const evidence = demo.result?.evidence ?? [];
  railContent.replaceChildren(element('p', isReal(demo) ? 'Real-paper evidence' : `Example ${number} · ${STATES[demo.scenario][0]}`, 'meta'));
  const choices = element('div', undefined, 'source-list');
  choices.setAttribute('aria-label', 'Source passages');
  const passageView = element('article', undefined, 'passage');
  function selectPassage(index) {
    activeDemo.selected = index;
    const passage = evidence[index];
    choices.querySelectorAll('button').forEach((button, position) => button.setAttribute('aria-pressed', String(position === index)));
    passageView.replaceChildren(element('h3', passage.title), element('p', `Passage ${index + 1}`, 'meta'), element('blockquote', passage.text));
    if (passage.source_url) {
      const link = element('a', isReal(demo) ? 'Open original paper' : 'Open example source', 'source-link');
      link.href = passage.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      passageView.append(link);
    } else passageView.append(element('p', 'Synthetic passage · No source URL', 'meta'));
    const details = disclosure('Source details');
    details.className = 'source-details';
    details.append(element('p', `${passage.source.toUpperCase()} · ${passage.page_number === null ? 'No PDF page' : `PDF page ${passage.page_number}`}${passage.section ? ` · ${passage.section}` : ''}`));
    if (passage.distance !== undefined && passage.distance !== null) details.append(element('p', `Retrieval distance: ${passage.distance} · Not confidence`));
    details.append(element('p', passage.chunk_id));
    passageView.append(details);
  }
  evidence.forEach((passage, index) => {
    const location = passage.source === 'pdf' ? `page ${passage.page_number}` : (passage.section || 'No PDF page');
    const button = element('button', `[${index + 1}]  ${passage.source.toUpperCase()} · ${location}`, 'source-choice');
    button.type = 'button';
    button.addEventListener('click', () => selectPassage(index));
    choices.append(button);
  });
  if (evidence.length) {
    if (isSynthesis(demo)) {
      const browse = disclosure(`Browse paper pages (${evidence.length})`);
      browse.append(choices);
      railContent.append(passageView, browse);
    } else railContent.append(choices, passageView);
    selectPassage(selected);
  } else {
    railContent.append(element('p', demo.result ? 'No evidence to inspect. This is not a provider failure.' : 'No draft or passages. This provider failure is simulated.', 'meta rail-empty'));
  }
  setRailOpen(true, trigger);
  if (trigger) {
    returnFocus = trigger;
    railHeading.focus();
  }
}

function closePreview() {
  clearTimeout(previewTimer);
  if (quotePreview.matches(':popover-open')) quotePreview.hidePopover();
  previewTrigger?.removeAttribute('aria-details');
  previewTrigger = null;
}

function deferClosePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => {
    if (!quotePreview.contains(document.activeElement) && document.activeElement !== previewTrigger) closePreview();
  }, 180);
}

function showQuote(item, demo, number, index, trigger) {
  clearTimeout(previewTimer);
  if (previewTrigger === trigger && quotePreview.matches(':popover-open')) return;
  closePreview();
  previewTrigger = trigger;
  trigger.setAttribute('aria-details', 'citation-preview');
  const passage = demo.result.evidence[index];
  const quotes = [...new Set((item.support || []).filter(support => support.chunk_id === passage.chunk_id).map(support => support.quote))];
  const head = element('div', undefined, 'quote-head');
  const close = element('button', '×', 'quiet quote-close');
  close.type = 'button';
  close.setAttribute('aria-label', 'Close cited quote');
  close.addEventListener('click', () => { closePreview(); trigger.focus({preventScroll: true}); closePreview(); });
  head.append(element('p', quotes.length ? 'Cited quote' : 'Source passage', 'quote-label'), close);
  const excerpts = element('div', undefined, 'quote-excerpts');
  for (const quote of quotes.length ? quotes : [passage.text]) excerpts.append(element('blockquote', quote));
  const location = passage.page_number != null ? `PDF page ${passage.page_number}` : (passage.section || 'No PDF page');
  const actions = element('div', undefined, 'quote-actions');
  if (passage.source_url) {
    const link = element('a', 'Open paper ↗');
    link.href = passage.source_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    actions.append(link);
  }
  const more = element('button', 'More context', 'quiet');
  more.type = 'button';
  more.addEventListener('click', () => {
    closePreview();
    showEvidence(demo, number, index, trigger);
  });
  actions.append(more);
  quotePreview.replaceChildren(head, excerpts, element('p', `${passage.title} · ${location}`, 'meta quote-source'), actions);
  quotePreview.showPopover();
  const rect = trigger.getBoundingClientRect();
  const box = quotePreview.getBoundingClientRect();
  quotePreview.style.left = `${Math.max(12, Math.min(rect.left, innerWidth - box.width - 12))}px`;
  const top = rect.bottom + 8 + box.height <= innerHeight - 12 ? rect.bottom + 8 : rect.top - box.height - 8;
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
  if (event.key === 'Escape' && previewTrigger) {
    const trigger = previewTrigger;
    const focusedInside = quotePreview.contains(document.activeElement);
    closePreview();
    if (focusedInside) { trigger.focus({preventScroll: true}); closePreview(); }
    event.preventDefault();
  } else if (event.key === 'Escape' && rail.open) {
    setRailOpen(false);
    event.preventDefault();
  }
});
document.addEventListener('pointerdown', event => {
  if (!quotePreview.contains(event.target) && event.target !== previewTrigger) closePreview();
});
conversation.addEventListener('scroll', closePreview);
window.addEventListener('resize', closePreview);

function citedParagraph(item, demo, number) {
  const paragraph = element('p', item.text);
  for (const id of item.chunk_ids) {
    const index = demo.result.evidence.findIndex(passage => passage.chunk_id === id);
    if (index < 0) throw new Error('Unknown citation');
    const passage = demo.result.evidence[index];
    const citation = element(passage.source_url ? 'a' : 'button', `[${index + 1}]`, 'citation');
    if (passage.source_url) {
      citation.href = passage.source_url;
      citation.target = '_blank';
      citation.rel = 'noopener noreferrer';
    } else citation.type = 'button';
    citation.dataset.turn = number;
    citation.dataset.passage = index;
    citation.setAttribute('aria-label', `Citation ${index + 1}${passage.page_number != null ? `, PDF page ${passage.page_number}` : ''}. ${passage.source_url ? 'Cited quote and original paper.' : 'Source passage preview.'}`);
    let pointerType = null;
    citation.addEventListener('pointerdown', event => { pointerType = event.pointerType; });
    citation.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') showQuote(item, demo, number, index, citation); });
    citation.addEventListener('pointerleave', deferClosePreview);
    citation.addEventListener('focus', () => showQuote(item, demo, number, index, citation));
    citation.addEventListener('blur', deferClosePreview);
    citation.addEventListener('keydown', event => {
      if (event.key === 'Tab' && !event.shiftKey && previewTrigger === citation) {
        event.preventDefault();
        quotePreview.querySelector('button, a').focus();
      }
    });
    citation.addEventListener('click', event => {
      if ((pointerType === 'touch' && event.detail !== 0) || !passage.source_url) {
        event.preventDefault();
        showQuote(item, demo, number, index, citation);
      }
      pointerType = null;
    });
    paragraph.append(document.createTextNode(' '), citation);
  }
  return paragraph;
}

function renderDraft(demo, number, answer) {
  const result = demo.result;
  const narrative = element('div', undefined, 'answer-text');
  if (!result.summary.claims.length) narrative.append(element('p', 'No supported research claims.'));
  for (const claim of result.summary.claims.filter(claim => claim.kind !== 'interpretation')) narrative.append(citedParagraph(claim, demo, number));
  const interpretations = result.summary.claims.filter(claim => claim.kind === 'interpretation');
  if (interpretations.length) {
    narrative.append(element('h3', 'Interpretation'), element('p', 'Inferences from the evidence—not findings validated by the study.', 'meta'));
    for (const claim of interpretations) narrative.append(citedParagraph(claim, demo, number));
  }
  if (isSynthesis(demo)) {
    if (result.summary.limitation_support?.length) {
      narrative.append(element('h3', 'Scope & limitations'));
      for (const item of result.summary.limitation_support) narrative.append(citedParagraph(item, demo, number));
    } else list(narrative, 'Scope & limitations', result.summary.limitations);
    narrative.append(element('p', 'Citation IDs and source quotes checked. Claim support has not been independently verified.', 'meta'));
  }
  const insight = result.business_insight;
  if (insight || !isSynthesis(demo)) narrative.append(element('h3', 'Business implications'));
  if (!insight && !isSynthesis(demo)) narrative.append(element('p', 'Business translation was not requested.'));
  if (insight) {
    if (!insight.implications.length) narrative.append(element('p', 'No supported business recommendations.'));
    for (const implication of insight.implications) {
      narrative.append(citedParagraph(implication, demo, number), element('p', `Suggested action: ${implication.suggested_action}`));
    }
  }
  answer.append(narrative);
  const detailGroup = element('div', undefined, 'detail-group');
  const limits = disclosure('Assumptions, risks & limitations');
  list(limits, 'Summary limitations', result.summary.limitations);
  if (insight) {
    limits.append(element('p', `Industry: ${insight.industry}`));
    for (const implication of insight.implications) list(limits, 'Assumptions · not research findings', implication.assumptions);
    list(limits, 'Risks', insight.risks);
    list(limits, 'Business limitations', insight.limitations);
  }
  limits.append(element('p', 'No reviewer has approved this draft. This demo cannot record or grant approval.'));
  const evidenceButton = element('button', `Inspect evidence (${result.evidence.length})`, 'quiet');
  evidenceButton.type = 'button';
  evidenceButton.addEventListener('click', () => showEvidence(demo, number, 0, evidenceButton));
  limits.append(evidenceButton);
  const details = disclosure('Details');
  details.append(limits);
  detailGroup.append(details);
  answer.append(detailGroup);
}

function renderDemo(demo, number, answer) {
  const [label, explanation] = STATES[demo.scenario];
  const head = element('div', undefined, 'answer-head');
  head.append(element('h2', demo.scenario === 'full' ? 'Answer' : label));
  if (demo.result) head.append(element('p', 'Draft · Not approved', 'meta'));
  answer.replaceChildren(head);
  if (demo.result) {
    if (demo.scenario !== 'full') answer.append(element('p', explanation));
    renderDraft(demo, number, answer);
  } else answer.append(element('p', demo.error.message, 'error'));
  const real = isReal(demo);
  const raw = disclosure(real ? 'Run details & result JSON' : 'Run details & demo JSON');
  if (demo.result) raw.append(element('p', `${real ? 'Executed query' : 'Fixed example'}: ${demo.result.request.query}`));
  raw.append(element('p', real ? runLabel(demo) : explanation));
  if (!real) raw.append(element('p', `Your question (not executed): ${demo.submitted_request.query}`));
  raw.append(element('pre', JSON.stringify(demo, null, 2)));
  const group = answer.querySelector('.detail-group');
  (group?.querySelector('details') || answer).append(raw);
  // Keep desktop context current without opening a mobile drawer over the answer.
  activeDemo = {demo, number};
  if (rail.open) showEvidence(demo, number);
  feedback.textContent = real ? (isSynthesis(demo) ? 'Synthesized answer ready. Inspect citations to check support.' : 'Saved research result loaded. No live query execution.') : `${label} loaded. Synthetic fixture only.`;
}

form.elements.query.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!submit.disabled) form.requestSubmit();
  }
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (submit.disabled) return;
  if (savedResult && !liveSynthesis) return;
  const query = form.elements.query.value;
  document.querySelector('.demo-settings').open = false;
  if (!query.trim()) {
    feedback.textContent = 'Enter a nonempty research question.';
    feedback.classList.remove('sr-only');
    form.elements.query.focus();
    return;
  }
  feedback.classList.add('sr-only');
  const number = ++turnNumber;
  const turn = element('section', undefined, 'turn');
  turn.setAttribute('aria-label', `Example ${number}`);
  const user = element('div', undefined, 'user-message');
  user.append(element('p', liveSynthesis ? 'Your question' : 'Your question · Not executed', 'meta'), element('p', query, 'user-bubble'));
  const loading = liveSynthesis ? 'Reading the paper and synthesizing an answer…' : 'Loading local example…';
  const answer = element('div', loading, 'answer');
  turn.append(user, answer);
  document.querySelector('#welcome').hidden = true;
  output.append(turn);
  resetEvidence('Loading a new example. No current evidence to inspect.');
  submit.disabled = true;
  output.setAttribute('aria-busy', 'true');
  feedback.textContent = loading;
  turn.scrollIntoView({block: 'start'});
  try {
    const response = await fetch(liveSynthesis ? '/api/research' : '/api/demo', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query, scenario: form.elements.scenario.value}),
      signal: AbortSignal.timeout(liveSynthesis ? 330000 : 10000),
    });
    const demo = await response.json();
    if (!response.ok) throw new Error(demo.error || 'Request rejected.');
    renderDemo(demo, number, answer);
    if (demo.result && form.elements.query.value === query) form.elements.query.value = '';
  } catch {
    const message = liveSynthesis ? 'Synthesis unavailable or citation validation failed. No answer was accepted. Your question is unchanged; retry when ready.' : 'Could not load the local example. Check that the demo server is running, then retry. Your question is unchanged.';
    answer.replaceChildren(element('h2', liveSynthesis ? 'Answer unavailable' : 'Example unavailable'), element('p', message, 'error'));
    feedback.textContent = message;
    feedback.classList.remove('sr-only');
    resetEvidence('The latest example did not load. Retry to inspect its evidence.');
  } finally {
    submit.disabled = false;
    output.setAttribute('aria-busy', 'false');
  }
});

// Evidence opens only when requested.
submit.disabled = true;
Promise.all(['/api/config', '/api/saved-result'].map(async url => {
  const response = await fetch(url);
  if (!response.ok) throw new Error('App configuration unavailable');
  return response.json();
})).then(([config, demo]) => {
  liveSynthesis = config.live;
  if (liveSynthesis) {
    document.querySelector('.demo-settings').hidden = true;
    document.querySelector('#welcome h2').textContent = 'Ask about this paper.';
    document.querySelector('#demo-note').textContent = 'Live LLM synthesis · This paper only · Each question is independent.';
    document.querySelector('.rail-note').textContent = 'Inspect source quotes and the original paper. Citations are not proof of support.';
    submit.firstChild.textContent = 'Ask paper';
    form.elements.query.value = 'What does this paper suggest about AI agents’ ability to improve AI training?';
  }
  if (!demo) return;
  savedResult = demo;
  if (liveSynthesis) form.elements.query.value = '';
  document.querySelector('.demo-settings').hidden = true;
  document.querySelector('#welcome').hidden = true;
  form.hidden = !liveSynthesis;
  if (!liveSynthesis) document.querySelector('#demo-note').textContent = runLabel(demo);
  document.querySelector('.rail-note').textContent = 'Source passages from the paper. Open the original section or cited PDF page.';
  const turn = element('section', undefined, 'turn');
  turn.append(element('p', demo.result.request.query, 'user-bubble'));
  const answer = element('div', undefined, 'answer');
  turn.append(answer);
  output.append(turn);
  renderDemo(demo, ++turnNumber, answer);
}).catch(() => {
  feedback.textContent = 'Saved-result check unavailable. Only synthetic examples are available.';
}).finally(() => { submit.disabled = false; });

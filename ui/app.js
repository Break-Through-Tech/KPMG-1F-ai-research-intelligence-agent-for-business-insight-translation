/* Fixture-only presentation. Text is inserted as text, never interpreted as HTML. */
const form = document.querySelector('#research-form');
const output = document.querySelector('#output');
const feedback = document.querySelector('#feedback');
const submit = document.querySelector('#submit');
const STATES = {
  full: ['Full draft', 'Research summary and conditional business implications are available.'],
  partial: ['Partial draft', 'The research summary is available. Business translation abstained.'],
  insufficient: ['Abstention · insufficient support', 'Passages are available, but do not support an answer.'],
  empty: ['No evidence', 'No passages were retrieved. Generation was skipped.'],
  'provider-error': ['Provider error · simulated', 'No draft was produced. Choose another example state to continue.'],
};

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function section(title) {
  const node = element('section', undefined, 'section');
  node.append(element('h2', title));
  return node;
}

function list(parent, title, items) {
  if (!items?.length) return;
  if (title) parent.append(element('h3', title));
  const ul = element('ul');
  for (const item of items) ul.append(element('li', item));
  parent.append(ul);
}

function citations(ids, evidence) {
  const links = element('div', undefined, 'citations');
  for (const id of ids) {
    const index = evidence.findIndex(passage => passage.chunk_id === id);
    const link = element('a', `Passage ${index + 1}`);
    link.href = `#passage-${index + 1}`;
    links.append(link);
  }
  return links;
}

function renderDraft(result) {
  const workspace = element('div', undefined, 'workspace');
  const narrative = element('div');
  const summary = section('Research summary');
  if (!result.summary.claims.length) summary.append(element('p', 'No supported research claims.'));
  for (const claim of result.summary.claims) {
    summary.append(element('p', claim.text), citations(claim.chunk_ids, result.evidence));
  }
  list(summary, 'Summary limitations', result.summary.limitations);
  narrative.append(summary);

  const business = section('Business implications');
  const insight = result.business_insight;
  if (!insight) business.append(element('p', 'Business translation was not requested.'));
  else {
    business.append(element('p', `Industry: ${insight.industry}`, 'meta'));
    if (!insight.implications.length) business.append(element('p', 'No supported business recommendations.'));
    for (const implication of insight.implications) {
      business.append(element('p', implication.text), citations(implication.chunk_ids, result.evidence));
      business.append(element('h3', 'Suggested action'), element('p', implication.suggested_action));
      const assumptions = element('div', undefined, 'assumptions');
      list(assumptions, 'Assumptions · not research findings', implication.assumptions);
      business.append(assumptions);
    }
    list(business, 'Risks', insight.risks);
    list(business, 'Business limitations', insight.limitations);
  }
  narrative.append(business);
  const review = section('Human review');
  review.append(element('p', 'Pending review · Not approved', 'review'),
    element('p', 'No reviewer has approved this draft. This demo cannot record or grant approval.'));
  narrative.append(review);

  const sources = section(`Sources & passages (${result.evidence.length})`);
  sources.append(element('p', 'All content is synthetic. Example.com links preserve fixture locations; they are not verified sources.', 'meta'));
  if (!result.evidence.length) sources.append(element('p', 'No evidence to inspect. This is not a provider failure.'));
  result.evidence.forEach((passage, index) => {
    const article = element('article', undefined, 'passage');
    article.id = `passage-${index + 1}`;
    article.tabIndex = -1;
    article.append(element('h3', `Passage ${index + 1} · ${passage.title}`));
    article.append(element('p', `${passage.source.toUpperCase()} · ${passage.page_number === null ? 'No PDF page' : `PDF page ${passage.page_number}`}${passage.section ? ` · ${passage.section}` : ''}`, 'meta'));
    article.append(element('blockquote', passage.text));
    if (passage.source_url) {
      const link = element('a', 'Open example source ↗');
      link.href = passage.source_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      article.append(link);
    } else article.append(element('p', 'Synthetic passage · No source URL', 'meta'));
    if (passage.distance !== undefined && passage.distance !== null) {
      article.append(element('p', `Retrieval distance: ${passage.distance} · Not confidence`, 'meta'));
    }
    article.append(element('p', passage.chunk_id, 'meta'));
    sources.append(article);
  });
  workspace.append(narrative, sources);
  return workspace;
}

function renderDemo(demo) {
  const fragment = document.createDocumentFragment();
  const header = element('div', undefined, `result-head ${demo.scenario}`);
  const [label, explanation] = STATES[demo.scenario];
  header.append(element('h2', label), element('p', explanation));
  header.append(element('p', `Your question (not executed): ${demo.submitted_request.query}`, 'meta'));
  if (demo.result) {
    header.append(element('p', `Fixed fixture question: ${demo.result.request.query}`, 'meta'));
    header.append(element('p', 'Pending human review · Not approved', 'review'));
  }
  fragment.append(header);
  if (demo.result) fragment.append(renderDraft(demo.result));
  else fragment.append(element('p', demo.error.message));
  const raw = element('details');
  raw.append(element('summary', 'Inspect demo JSON'), element('pre', JSON.stringify(demo, null, 2)));
  fragment.append(raw);
  output.replaceChildren(fragment);
  feedback.textContent = `${label} loaded. Synthetic fixture only.`;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const query = form.elements.query.value;
  if (!query.trim()) {
    feedback.textContent = 'Enter a nonempty research question.';
    form.elements.query.focus();
    return;
  }
  submit.disabled = true;
  output.setAttribute('aria-busy', 'true');
  output.replaceChildren();
  feedback.textContent = 'Loading local example…';
  try {
    const response = await fetch('/api/demo', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query, scenario: form.elements.scenario.value}),
      signal: AbortSignal.timeout(10000),
    });
    const demo = await response.json();
    if (!response.ok) throw new Error('Demo request rejected. Check your question and example state.');
    renderDemo(demo);
  } catch {
    feedback.textContent = 'Could not load the local example. Check that the demo server is running, then retry. Your question is unchanged.';
  } finally {
    submit.disabled = false;
    output.setAttribute('aria-busy', 'false');
  }
});

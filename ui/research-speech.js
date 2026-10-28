/* Read explicit model fields, never hidden disclosures, math markup or the page. */
(() => {
  'use strict';
  const module = import('/read-aloud.mjs');
  const readers = new Set();
  function attach(parent, item) {
    const root = document.createElement('div');
    parent.append(root);
    module.then(({mountReadAloud}) => {
      if (!root.isConnected) return;
      const reader = mountReadAloud(root);
      readers.add(reader);
      reader.setItems([item]);
      const observer = new MutationObserver(() => {
        if (!root.isConnected) { readers.delete(reader); observer.disconnect(); }
      });
      observer.observe(document.documentElement, {childList: true, subtree: true});
    }).catch(() => {
      root.textContent = 'Read-aloud could not load. All text and citations remain available.';
    });
  }
  function source(passage, number) {
    return [`Citation ${number}. ${passage.title}.`,
      `Source: ${passage.source}. Identity: ${passage.arxiv_id || 'not retained'}.`,
      `Section: ${passage.section || 'not retained'}. PDF page: ${passage.page_number ?? 'not retained'}.`,
      'Source passage, not generated interpretation.', passage.text,
      ...(passage.reader?.limitations || []),
      'Audio reads retained citation-check text, not structured math or table navigation. Use the structured reader or your screen reader for those.'].join('\n');
  }
  function result(demo, number) {
    const value = demo.result;
    const citation = item => `${item.text} Citations: ${item.chunk_ids.map(id => {
      const index = value.evidence.findIndex(p => p.chunk_id === id);
      return `${index + 1}, ${value.evidence[index]?.title || 'source unavailable'}`;
    }).join('; ')}.`;
    const business = value.business_insight;
    return {id: `answer:${number}`, label: `Answer ${number} · Original · Draft, not approved`, text: [
      `Answer ${number}. ${demo.mode === 'fixture' ? 'Synthetic example. Question not executed.' : 'Research result.'}`,
      `Question: ${value.request.query}`, `Outcome: ${demo.scenario}. Draft. Human review pending. Not approved.`,
      ...(demo.library ? [`Saved version review: ${BriefLibrary.reviewText(demo)}. Original snapshot review fields are unchanged.`] : []),
      'Original research summary.', ...value.summary.claims.map(c => `${c.kind === 'interpretation' ? 'Interpretation, not study finding. ' : ''}${citation(c)}`),
      ...(value.summary.claims.length ? [] : ['No supported research claims.']),
      'Summary limitations.', ...(value.summary.limitation_support || []).map(citation),
      ...value.summary.limitations.filter(text => !(value.summary.limitation_support || []).some(item => item.text === text)),
      ...(business ? ['Conditional business interpretations, not study findings.', `Industry: ${business.industry}.`,
        `Business translation: ${business.status}.`, ...business.implications.flatMap(i => [citation(i), `Suggested action: ${i.suggested_action}`, 'Transfer assumptions.', ...i.assumptions]),
        'Risks.', ...business.risks, 'Business limitations.', ...business.limitations] : [demo.error ? `Business translation unavailable. ${demo.error.stage || 'Execution'}: ${demo.error.message}` : 'Business translation not requested.']),
      'Audio reads original retained text. Plain-language rewrites and source support have not been independently approved.',
    ].join('\n')};
  }
  window.ResearchSpeech = {attach, source, result, stopAll() { for (const reader of readers) reader.stop(); }};
})();

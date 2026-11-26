/* PROTOTYPE ONLY. Answers /api/* in the browser with invented data shaped like the real
   envelopes, for UI-state testing. It is OFF unless the page is opened with ?mock=1, so a
   page connected to a backend can never silently fall back to illustrative answers.
   Nothing here is real research. */
(() => {
  'use strict';
  if (new URLSearchParams(location.search).get('mock') !== '1') return;
  window.MOCK_API = true;

  const PAPER_A = 'Illustrative study A · Retrieval-grounded agents for compliance review';
  const PAPER_B = 'Illustrative study B · Measuring citation faithfulness in generated summaries';
  const EVIDENCE = [
    {chunk_id: 'mock-a-results-1', arxiv_id: 'mock.0001v2', title: PAPER_A, source: 'html', section: '4.2 Results',
      page_number: null, distance: 0.214, source_url: 'https://example.org/mock-study-a#results',
      text: 'Across 1,240 annotated compliance cases, the agent pipeline with retrieval and a verification step reached 91.4% agreement with senior reviewers, compared with 78.9% for the single-prompt baseline. Agreement dropped to 72.3% on cases requiring cross-document reasoning. Table 3 reports agreement by case type.',
      reader: {version: 1, provenance: 'source-html', source_sha256: 'mock-sha256-not-a-real-digest',
        limitations: ['Mock structured passage for the prototype; not extracted from a real paper.'],
        nodes: [
          {tag: 'p', children: ['Across 1,240 annotated compliance cases, the agent pipeline with retrieval and a verification step reached 91.4% agreement with senior reviewers, compared with 78.9% for the single-prompt baseline. Agreement dropped to 72.3% on cases requiring cross-document reasoning.']},
          {tag: 'table', children: [
            {tag: 'caption', children: ['Table 3: Reviewer agreement by case type']},
            {tag: 'thead', children: [{tag: 'tr', children: [
              {tag: 'th', attrs: {scope: 'col'}, children: ['Case type']},
              {tag: 'th', attrs: {scope: 'col'}, children: ['Cases']},
              {tag: 'th', attrs: {scope: 'col'}, children: ['Agent + verification']},
              {tag: 'th', attrs: {scope: 'col'}, children: ['Single prompt']}]}]},
            {tag: 'tbody', children: [
              ['Routine, single document', '812', '95.2%', '84.1%'],
              ['Policy exception', '236', '88.6%', '74.2%'],
              ['Cross-document reasoning', '192', '72.3%', '61.5%'],
              ['All cases', '1,240', '91.4%', '78.9%'],
            ].map(row => ({tag: 'tr', children: row.map((cell, i) => (
              {tag: i ? 'td' : 'th', attrs: i ? {} : {scope: 'row'}, children: [cell]}))}))},
          ]},
          {tag: 'p', children: ['Table 3 reports agreement by case type.']},
        ]}},
    {chunk_id: 'mock-a-pdf-7', arxiv_id: 'mock.0001v2', title: PAPER_A, source: 'pdf', section: null,
      page_number: 7, distance: 0.268, source_url: 'https://example.org/mock-study-a.pdf#page=7',
      text: 'Human reviewers overturned 14% of agent decisions flagged as high confidence, most often where the governing policy had been updated after the retrieval index was built. We therefore recommend that deployments retain a human approval step for all adverse determinations.'},
    {chunk_id: 'mock-a-limits-1', arxiv_id: 'mock.0001v2', title: PAPER_A, source: 'html', section: '5 Limitations',
      page_number: null, distance: 0.301, source_url: 'https://example.org/mock-study-a#limitations',
      text: 'Our evaluation covers English-language retail banking policies from a single institution. Results may not transfer to other jurisdictions, product lines or regulatory regimes, and we did not measure performance drift over time.'},
    {chunk_id: 'mock-a-table-5', arxiv_id: 'mock.0001v2', title: PAPER_A, source: 'html', section: 'Table 5',
      page_number: null, distance: 0.322, source_url: 'https://example.org/mock-study-a#table-5',
      representation: 'linearized_table', header_review: 'unverified',
      text: 'Row: Verification step enabled | Cost per case: $0.42 | Median latency: 38 s | Unsupported-claim rate: 3.1%. Row: Verification step disabled | Cost per case: $0.18 | Median latency: 11 s | Unsupported-claim rate: 11.8%.'},
    {chunk_id: 'mock-b-pdf-3', arxiv_id: 'mock.0002v1', title: PAPER_B, source: 'pdf', section: null,
      page_number: 3, distance: 0.347, source_url: 'https://example.org/mock-study-b.pdf#page=3',
      text: 'We define citation precision as \\(P = |C_{supported}| / |C_{cited}|\\), the share of cited passages that a human annotator judges to support the attached claim. Citation precision averaged 0.87 across systems; no system exceeded 0.93.'},
  ];
  const byId = Object.fromEntries(EVIDENCE.map(p => [p.chunk_id, p]));
  const cite = (text, pairs, extra = {}) => {
    const support = pairs.filter(([, quote]) => quote).map(([chunk_id, quote]) => ({chunk_id, quote}));
    for (const s of support) if (!byId[s.chunk_id].text.includes(s.quote)) console.warn('Mock quote is not in passage', s);
    return {text, chunk_ids: [...new Set(pairs.map(([id]) => id))], support, ...extra};
  };
  const clone = value => JSON.parse(JSON.stringify(value));

  function makeResult(query, industry, {short = false, seconds = 18.4} = {}) {
    const claims = [
      cite('A retrieval-grounded agent pipeline with a verification step agreed with senior reviewers in 91.4% of 1,240 annotated compliance cases, versus 78.9% for a single-prompt baseline.',
        [['mock-a-results-1', 'reached 91.4% agreement with senior reviewers, compared with 78.9% for the single-prompt baseline']]),
      cite('Performance was weaker on harder cases: agreement fell to 72.3% where cross-document reasoning was required.',
        [['mock-a-results-1', 'Agreement dropped to 72.3% on cases requiring cross-document reasoning.']]),
      cite('The verification step cut the unsupported-claim rate from 11.8% to 3.1%, at higher cost and latency per case.',
        [['mock-a-table-5', 'Unsupported-claim rate: 3.1%'], ['mock-a-table-5', 'Unsupported-claim rate: 11.8%']]),
      cite('Citations are not a guarantee of support: citation precision averaged 0.87 and no system exceeded 0.93.',
        [['mock-b-pdf-3', 'Citation precision averaged 0.87 across systems; no system exceeded 0.93.']]),
      cite('Taken together, the evidence suggests verification layers reduce, but do not remove, the need for human review of high-stakes outputs.',
        [['mock-a-pdf-7', 'Human reviewers overturned 14% of agent decisions flagged as high confidence'], ['mock-b-pdf-3', '']],
        {kind: 'interpretation'}),
    ];
    const limitation = 'Evidence comes from English-language retail banking policies at a single institution and may not transfer to other jurisdictions or product lines.';
    const result = {
      schema_version: '1.0',
      request: {query, top_k: 8, ...(industry ? {industry} : {})},
      evidence: clone(EVIDENCE),
      summary: {
        status: 'ok', query, generation_method: 'cited-synthesis-v1',
        answer_lead: 'The retrieved studies suggest agent pipelines can match senior reviewers on most routine compliance cases when retrieval is paired with a verification step, but accuracy falls on cross-document cases and human approval remains necessary for adverse decisions.',
        claims: short ? claims.slice(0, 3) : claims,
        limitations: [limitation, 'Performance drift over time was not measured.'],
        limitation_support: [cite(limitation, [['mock-a-limits-1', 'Our evaluation covers English-language retail banking policies from a single institution.']])],
        quality_review: {status: 'applied', reviewer: 'automated'},
      },
      business_insight: industry ? {
        status: 'ok', industry,
        implications: [
          cite('A bounded pilot on routine, single-document compliance cases is the best-supported starting point.',
            [['mock-a-results-1', 'reached 91.4% agreement with senior reviewers']],
            {suggested_action: 'Pilot on routine case types first and track reviewer agreement against the reported 91.4% before widening scope.',
              assumptions: ['Your case mix resembles the study’s retail banking policies.', 'Senior reviewers are available to annotate a comparison sample.']}),
          cite('Keep a human approval step for adverse determinations; high-confidence agent decisions were still overturned.',
            [['mock-a-pdf-7', 'retain a human approval step for all adverse determinations']],
            {suggested_action: 'Route every adverse determination to a named reviewer and log overturn rates monthly.',
              assumptions: ['Policy updates reach your retrieval index with some delay, as in the study.']}),
          cite('Budget for verification: it more than doubles cost per case but removes most unsupported claims.',
            [['mock-a-table-5', 'Cost per case: $0.42'], ['mock-a-table-5', 'Cost per case: $0.18']],
            {suggested_action: 'Model cost per case with and without verification before committing to volumes.',
              assumptions: ['Reported costs reflect the study’s model pricing, which may differ from yours.']}),
        ],
        risks: ['A stale retrieval index after policy updates can produce confident but outdated decisions.',
          'Extracted table values (cost, latency) have unverified column labels; confirm against the original paper.',
          'Regulatory expectations for automated decisions vary by jurisdiction and were not assessed in the cited studies.'],
        limitations: ['Business implications are conditional interpretations, not findings validated by the studies.',
          'Single-institution evidence; no cross-industry comparison.'],
      } : null,
      human_review: {status: 'pending', reviewer: null, notes: null},
      approved: false,
      provenance: {timings_seconds: {total: seconds}, generation: {provider: 'mock', prompt_version: 'prototype-mock-v1'},
        index: {count: 48210, metadata: {note: 'mock index identity'}}},
    };
    if (!result.business_insight) delete result.business_insight;
    return result;
  }
  function plainLanguage() {
    return {status: 'available', claims: [
      {text: 'An AI assistant that looks up the rules and then double-checks its own work agreed with senior reviewers about 9 times out of 10 (91.4% of 1,240 cases). Without those steps it agreed about 8 times out of 10 (78.9%).',
        support: [{chunk_id: 'mock-a-results-1', quote: 'reached 91.4% agreement with senior reviewers, compared with 78.9% for the single-prompt baseline'}]},
      {text: 'It did worse on harder cases. When the answer depended on combining several documents, agreement fell to 72.3%.',
        support: [{chunk_id: 'mock-a-results-1', quote: 'Agreement dropped to 72.3% on cases requiring cross-document reasoning.'}]},
      {text: 'The double-check step reduced statements with no backing from 11.8% to 3.1%, but each case cost more and took longer.',
        support: [{chunk_id: 'mock-a-table-5', quote: 'Unsupported-claim rate: 3.1%'}, {chunk_id: 'mock-a-table-5', quote: 'Unsupported-claim rate: 11.8%'}]},
      {text: 'A citation does not prove a statement. On average 87% of cited passages really backed the statement, and no system did better than 93%.',
        support: [{chunk_id: 'mock-b-pdf-3', quote: 'Citation precision averaged 0.87 across systems; no system exceeded 0.93.'}]},
      null],
      definitions: [
        {term: 'Citation precision', status: 'supported', ...cite('The share of cited passages that a human judges to actually support the claim they are attached to.',
          [['mock-b-pdf-3', 'the share of cited passages that a human annotator judges to support the attached claim']])},
        {term: 'Cross-document reasoning', status: 'unavailable', reason: 'No retained passage defines this term.'}]};
  }
  function envelope(query, industry, scenario = 'full', options) {
    const result = makeResult(query, industry, options);
    const env = {mode: 'indexed', scenario, history_policy: 'server_owned_bounded_intent_only',
      submitted_request: {query, industry: industry || ''}, result, error: null, plain_language: plainLanguage()};
    if (scenario === 'summary-only') delete result.business_insight;
    if (scenario === 'partial') {
      delete result.business_insight;
      env.error = {stage: 'business', code: 'provider_unavailable', message: 'Business translation did not complete. The supported research summary is retained.'};
    }
    if (scenario === 'insufficient' || scenario === 'empty') {
      result.summary.status = 'insufficient_evidence'; result.summary.claims = []; result.summary.limitation_support = [];
      delete result.summary.answer_lead; delete result.business_insight;
      env.plain_language = {status: 'unavailable', reason: 'No supported findings to rewrite.'};
      if (scenario === 'empty') {
        result.evidence = []; result.summary.limitations = ['No passages were retrieved for this question.'];
      } else {
        result.evidence = result.evidence.slice(0, 2);
        result.summary.limitations = ['The retrieved passages discuss compliance review agents but do not address the question asked.'];
      }
    }
    return env;
  }

  /* ---- In-memory brief library (server-owned in the real app: src/brief_store.py) ---- */
  let sequence = 0;
  const id = prefix => `${prefix}-${(++sequence).toString(36)}${Math.random().toString(36).slice(2, 6)}`;
  const daysAgo = n => new Date(Date.now() - n * 864e5).toISOString();
  const briefs = [];
  function addVersion(record, env, created = new Date().toISOString()) {
    const snapshot = clone(env); delete snapshot.library; delete snapshot.library_error;
    const version = {id: id('ver'), number: record.versions.length + 1, created_at: created, fingerprint: id('fp'),
      audience: snapshot.result.business_insight?.industry || 'research', envelope: snapshot};
    record.versions.push(version); record.brief.current_version = version.id; record.brief.updated_at = created;
    return version;
  }
  function createBrief(title, env, created) {
    const record = {brief: {id: id('brief'), title, archived: false, current_version: null, updated_at: created}, versions: [], reviews: []};
    addVersion(record, env, created); briefs.unshift(record); return record;
  }
  function view(record, versionId, replayed = true) {
    const version = record.versions.find(v => v.id === (versionId || record.brief.current_version));
    if (!version) throw [404, 'Saved version not found.'];
    return {...clone(version.envelope), library: {replayed, brief: clone(record.brief),
      version: {id: version.id, number: version.number, created_at: version.created_at, fingerprint: version.fingerprint, audience: version.audience},
      versions: record.versions.map(({envelope, ...rest}) => clone(rest)),
      reviews: clone(record.reviews.filter(review => review.version_id === version.id))}};
  }
  const reviewLabel = record => {
    const latest = record.reviews.filter(r => r.version_id === record.brief.current_version).at(-1);
    return latest ? {approve: 'Approved', revise: 'Changes requested', reject: 'Rejected'}[latest.decision] : 'Draft';
  };
  (() => {
    const first = createBrief('Agent reliability in compliance review',
      envelope('How reliable are AI agents for compliance review in retail banking?', 'banking', 'full', {short: true, seconds: 21.7}), daysAgo(6));
    first.reviews.push({version_id: first.versions[0].id, decision: 'revise', reviewer: 'Demo reviewer',
      notes: 'Add the cost and latency trade-off before this goes to the client team.', created_at: daysAgo(5)});
    addVersion(first, envelope('How reliable are AI agents for compliance review in retail banking?', 'banking'), daysAgo(2));
    const second = createBrief('Citation faithfulness in generated summaries',
      envelope('Can cited AI summaries be trusted without checking the sources?', '', 'summary-only', {seconds: 14.2}), daysAgo(9));
    second.reviews.push({version_id: second.versions[0].id, decision: 'approve', reviewer: 'Demo reviewer', notes: null, created_at: daysAgo(8)});
    const third = createBrief('Verification cost per case (archived)',
      envelope('What does a verification step cost per reviewed case?', 'insurance', 'full', {seconds: 16.9}), daysAgo(20));
    third.brief.archived = true;
    briefs.sort((a, b) => b.brief.updated_at.localeCompare(a.brief.updated_at));
  })();
  const find = briefId => {
    const record = briefs.find(item => item.brief.id === briefId);
    if (!record) throw [404, 'Saved brief not found.'];
    return record;
  };
  const guard = (record, expected) => {
    if (expected !== record.brief.current_version) throw [409, 'This brief changed elsewhere. Reopen the latest version and retry.'];
  };

  /* ---- Conversation state for the clarification flow ---- */
  let conversation = 0;
  const pending = new Map();
  const config = () => ({live: true, plain_language: true, library: true, mode: 'indexed', clarification: true,
    agentic_mode: true,
    context_id: 'mock-context-1', conversation_id: `mock-conversation-${++conversation}`,
    history_policy: 'server_owned_bounded_intent_only', index: {count: 48210, metadata: {}}});

  /* Invented multi-agent run (same envelope and provenance.agentic shape as experiments/agentic). */
  function agentic(body) {
    const query = body.query;
    if (typeof query !== 'string' || !query.trim() || query.length > 2000) throw [400, 'Enter a question up to 2000 characters.'];
    const industry = (body.industry || '').trim();
    const scenario = body.scenario || 'full';
    const task = (id, to, kind, payload) => ({type: 'task', task_id: id, from: 'orchestrator', to, kind, payload});
    const reply = (id, from, status, output, seconds, calls) => ({type: 'reply', task_id: id, from, to: 'orchestrator', status, output, seconds, model_calls: calls});
    const decision = (name, run, reason) => ({type: 'decision', actor: 'orchestrator', decision: name, run, reason});
    const searches = [{query, purpose: 'original question'}, {query: 'unsupported-claim rate with a verification step', purpose: 'second part of the question'}];
    const trace = [
      task('t1', 'orchestrator', 'plan', {question: query}),
      reply('t1', 'orchestrator', 'ok', {question_type: 'multi_part', subquestions: [searches[1]], notes: 'Two outcomes are asked for.'}, 4.1, 1),
      decision('decompose', true, '1 extra search(es) planned in addition to the question'),
      decision('business_routing', !!industry, industry ? 'Industry selected by the user.' : 'Orchestrator: the question asks for research findings only.'),
      decision('chart_routing', true, 'Orchestrator: the question compares numeric results.'),
      task('t2', 'research_agent', 'research', {question: query, searches, existing_passage_ids: []}),
    ];
    if (scenario === 'provider-error') {
      trace.push(reply('t2', 'research_agent', 'provider_failure', {cause: 'timeout'}, 300.0, 1));
      return {mode: 'indexed', scenario: 'error', result: null, submitted_request: {query, top_k: 8},
        error: {stage: 'research_agent', code: 'agentic_execution_error', cause: 'timeout', message: 'The AI provider did not respond in time. No answer was accepted. (Simulated by the prototype.)'},
        agentic: {model_calls: {limit: 6, used: 2, by_agent: {orchestrator: 1, research_agent: 1}}, trace}};
    }
    const env = envelope(query, industry, industry ? 'full' : 'summary-only');
    const claims = env.result.summary.claims;
    const rows = claims.map((claim, index) => ({index, kind: claim.kind, text: claim.text,
      deterministic: {quote_membership: index === 4 ? 'failed' : 'passed', numbers_and_qualifiers: index === 2 ? 'failed: unit_mismatch' : 'passed'},
      number_grounding: {status: index === 3 ? 'uncertain' : index === 2 ? 'contradicted' : 'grounded', uncertain: index === 3 ? ['metric_unconfirmed'] : []},
      needs_human_number_check: index === 3,
      automated: {verdict: index === 1 ? 'partially_supported' : 'supported', issues: index === 1 ? ['overgeneralization'] : [],
        reason: index === 1 ? 'The passage reports one subset; the claim generalizes it.' : 'The cited passage states this, including the values.'},
      decision: [1, 2, 4].includes(index) ? 'held' : 'accepted',
      held_reason: index === 1 ? 'verifier judged partially supported (overgeneralization)' : index === 2 ? 'deterministic check failed: numbers_and_qualifiers (unit_mismatch)' : index === 4 ? 'deterministic check failed: quote_membership' : null}));
    env.result.summary.claims = claims.filter((_, index) => rows[index].decision === 'accepted');
    const ids = env.result.evidence.map(p => p.chunk_id);
    trace.push(reply('t2', 'research_agent', 'ok', {searches, passage_ids: ids, claims: claims.map((c, index) => ({index, kind: c.kind, text: c.text}))}, 9.6, 1),
      task('t3', 'verification_agent', 'verify', {question: query, claim_count: claims.length, passage_ids: ids}),
      reply('t3', 'verification_agent', 'ok', {claims: rows, coverage: 'partial', coverage_reported: 'full', coverage_adjusted: true, missing_aspects: ['3 drafted claim(s) did not pass verification'], retrieval_request: {needed: false, query: '', reason: 'Both parts are covered.'}}, 7.2, 1),
      decision('targeted_retrieval', false, 'Verifier did not request more evidence: Both parts are covered.'));
    let used = 3;
    if (industry) {
      trace.push(task('t4', 'business_insight_agent', 'business_insight', {industry, verified_claims: env.result.summary.claims.length}),
        reply('t4', 'business_insight_agent', 'ok', {status: 'ok', implication_count: 2, screened_out: [{implication: 'Adopting the pipeline will cut review costs by 40%.', issues: {text: ['numbers_absent', 'roi_or_savings']}}]}, 6.0, 1));
      used += 1;
    }
    trace.push(task('t5', 'chart_tool', 'chart_preview', {question: query, passage_count: ids.length}),
      reply('t5', 'chart_tool', 'unavailable', {reason: 'Chart evidence is unavailable on this backend: no verified table audit is loaded. Text answers are unaffected.', tables: []}, 0.0, 0));
    env.result.provenance = {...env.result.provenance, execution: 'agentic_orchestrator_experimental', agentic: {
      experimental: true, question: query, trace, decisions: trace.filter(e => e.type === 'decision'),
      rounds: [{round: 1, searches, research_status: 'ok', verification: {claims: rows, coverage: 'full'}, draft_claim_count: claims.length}],
      selected_round: 1, evidence_ids: ids, claims_needing_number_check: [claims[3].text],
      business_screening: industry ? [{field: 'implication', text: 'Adopting the pipeline will cut review costs by 40%.', status: 'removed', issues: {implication: ['numbers_absent', 'roi_or_savings']}},
        {field: 'implication', text: 'Pilot the verification step on a sample of past cases.', status: 'kept_unverified', issues: {}}] : [],
      model_calls: {limit: 6, used, by_agent: {orchestrator: 1, research_agent: 1, verification_agent: 1, ...(industry ? {business_insight_agent: 1} : {})}},
      agents_run: ['chart_tool', 'orchestrator', 'research_agent', 'verification_agent', ...(industry ? ['business_insight_agent'] : [])].sort(),
      seconds: 27.3, status: 'ok', error: null}};
    env.agentic_charts = {status: 'unavailable', reason: 'Chart evidence is unavailable on this backend: no verified table audit is loaded. Text answers are unaffected.', tables: []};
    // Same revision contract as the research route: a revision saves the next version of the brief.
    return finish(env, {...body, industry});
  }

  function research(body) {
    const query = body.query;
    if (typeof query !== 'string' || !query.trim() || query.length > 2000) throw [400, 'Enter a question (up to 2000 characters).'];
    const scenario = body.scenario || 'full';
    if (scenario === 'provider-error') return {mode: 'indexed', scenario: 'execution-error', result: null,
      submitted_request: {query}, error: {stage: 'summary', code: 'provider_unavailable', message: 'The generation provider did not respond. No draft was accepted. (Simulated by the prototype.)'}};
    if (scenario === 'context-changed') throw [409, 'Indexed context changed. Restart the server and reload the page; no stale context was used.'];
    if (body.action === 'resume' && pending.has(body.conversation_id)) {
      const original = pending.get(body.conversation_id); pending.delete(body.conversation_id);
      return finish(envelope(original.query, original.industry, 'full'), original);
    }
    if (scenario === 'clarification') {
      pending.set(body.conversation_id, {query, industry: (body.industry || '').trim() || 'banking', library_revision: body.library_revision});
      return {mode: 'indexed', scenario: 'clarification', result: null, phase: 'post', submitted_request: {query},
        clarification: {question: 'Which aspect of reliability matters most for your decision?', options: [
          {text: 'Agreement with expert reviewers', support: [{chunk_id: 'mock-a-results-1', quote: 'reached 91.4% agreement with senior reviewers'}]},
          {text: 'Rate of unsupported claims', support: [{chunk_id: 'mock-a-table-5', quote: 'Unsupported-claim rate: 3.1%'}]},
          {text: 'Cost and latency per case', support: []}]},
        clarification_evidence: clone([byId['mock-a-results-1'], byId['mock-a-table-5']])};
    }
    // The real server resolves industry context from the prompt (interpret_context) or the industry field.
    const named = [['bank', 'banking'], ['insur', 'insurance'], ['health', 'healthcare'], ['pharma', 'pharmaceuticals'],
      ['telecom', 'telecommunications'], ['energy', 'energy'], ['retail', 'retail']].find(([stem]) => query.toLowerCase().includes(stem));
    const industry = (body.industry || '').trim() || (named ? named[1] : '');
    return finish(envelope(query, industry, industry || scenario !== 'full' ? scenario : 'summary-only'), {...body, industry});
  }
  function finish(env, body) {
    if (!env.result || !body.library_revision) return env;
    try {
      const record = find(body.library_revision.brief_id);
      guard(record, body.library_revision.expected_version);
      const version = addVersion(record, env);
      return view(record, version.id, false);
    } catch (error) { return {...env, library_error: Array.isArray(error) ? error[1] : 'Could not save the new version.'}; }
  }

  function route(url, method, body) {
    const path = url.pathname;
    if (path === '/api/config') return config();
    if (path === '/api/saved-result') return null;
    if (path === '/api/research' || path === '/api/demo') return research(body || {});
    if (path === '/api/agentic-research') return agentic(body || {});
    const match = path.match(/^\/api\/briefs(?:\/([^/]+))?(\/reviews)?$/);
    if (!match) throw [404, 'Not found.'];
    const [, briefId, reviews] = match;
    if (!briefId && method === 'GET') {
      const q = (url.searchParams.get('q') || '').toLowerCase();
      const archived = url.searchParams.get('archived') === '1';
      const offset = Number(url.searchParams.get('offset')) || 0;
      const rows = briefs.filter(r => r.brief.archived === archived).filter(r => {
        const current = r.versions.find(v => v.id === r.brief.current_version);
        return !q || r.brief.title.toLowerCase().includes(q) || current.envelope.result.request.query.toLowerCase().includes(q);
      }).sort((a, b) => b.brief.updated_at.localeCompare(a.brief.updated_at));
      return {briefs: rows.slice(offset, offset + 30).map(r => ({id: r.brief.id, title: r.brief.title,
        number: r.versions.length, review_status: reviewLabel(r), mode: 'indexed', updated_at: r.brief.updated_at}))};
    }
    if (!briefId) {
      const env = body.envelope || (body.result ? {mode: 'saved-real-result', scenario: 'full', result: body.result, error: null,
        submitted_request: body.result.request} : null);
      if (!env?.result?.request?.query || !Array.isArray(env.result.evidence)) throw [400, 'This file is not a research result or snapshot.'];
      if (body.brief_id) {
        const record = find(body.brief_id); guard(record, body.expected_version);
        return view(record, addVersion(record, env).id, false);
      }
      const title = Array.from(env.result.request.query).slice(0, 80).join('');
      return view(createBrief(title, env, new Date().toISOString()), null, false);
    }
    const record = find(briefId);
    if (method === 'GET') return view(record, url.searchParams.get('version'));
    if (reviews) {
      guard(record, body.version_id);
      if (!String(body.reviewer || '').trim()) throw [400, 'Reviewer name is required.'];
      if (body.decision === 'revise' && !String(body.notes || '').trim()) throw [400, 'Review notes are required when requesting changes.'];
      if (!['approve', 'revise', 'reject'].includes(body.decision)) throw [400, 'Unknown review decision.'];
      record.reviews.push({version_id: body.version_id, decision: body.decision, reviewer: body.reviewer.trim(),
        notes: body.notes || null, created_at: new Date().toISOString()});
      record.brief.updated_at = new Date().toISOString();
      return view(record, body.version_id, false);
    }
    guard(record, body.expected_version);
    if (typeof body.title === 'string') {
      if (!body.title.trim()) throw [400, 'Enter a brief title.'];
      record.brief.title = body.title.trim().slice(0, 200);
    }
    if (typeof body.archived === 'boolean') record.brief.archived = body.archived;
    record.brief.updated_at = new Date().toISOString();
    return view(record, null, false);
  }

  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (url.origin !== location.origin || !url.pathname.startsWith('/api/')) return realFetch(input, init);
    const method = (init.method || 'GET').toUpperCase();
    const body = init.body ? JSON.parse(init.body) : undefined;
    const research = url.pathname === '/api/research' || url.pathname === '/api/demo' || url.pathname === '/api/agentic-research';
    const slow = research && body?.scenario !== 'clarification' && body?.action !== 'resume' ? 2600 : research ? 1100 : 180;
    await new Promise(resolve => setTimeout(resolve, slow + Math.random() * 200));
    if (research && body?.scenario === 'unreachable') throw new TypeError('Failed to fetch');
    let status = 200, data;
    try { data = route(url, method, body); }
    catch (error) {
      if (!Array.isArray(error)) { console.error(error); status = 500; data = {error: 'Mock API failure.'}; }
      else { [status] = error; data = {error: error[1]}; }
    }
    return new Response(JSON.stringify(data), {status, headers: {'Content-Type': 'application/json'}});
  };
})();

"""Wrap an orchestrator result in the same research envelope the baseline returns.

The verified agentic summary, the final evidence and any business insight go through the shared
``src.research_pipeline.run_research`` contract, so the result is validated, sealed with the same
review fingerprint and starts pending human review exactly like a baseline answer. That is what lets
saved briefs, citations, evidence inspection and reviews work unchanged in both modes.

The agentic plan, routing decisions, selected round, verification rounds, call counts, chart
provenance and full message trace are stored in ``result.provenance.agentic``, so they are part of the
reviewed snapshot (a saved brief keeps them, and changing them invalidates a review).
"""
import copy

ENVELOPE_MODE = 'indexed'  # the saved-brief store and the dashboard accept this envelope type
EXECUTION = 'agentic_orchestrator_experimental'

FAILURE_MESSAGES = {
    'call_budget': 'Not enough approved model calls for multi-agent research. No model call was made.',
    'cumulative_call_cap': 'The cumulative call authorization is used up. No answer was accepted.',
    'per_run_call_cap': 'This backend session reached its approved call cap. No answer was accepted.',
    'stopped_after_provider_error': 'Generation is stopped after an earlier provider error. No answer was accepted.',
    'timeout': 'The AI provider did not respond in time. No answer was accepted.',
    'rate_limited': 'The AI provider refused the request (rate limit). No answer was accepted.',
}


def _index_sha(provenance):
    index = (provenance or {}).get('index') or {}
    return index.get('indexed_records_sha256')


def _chart_provenance(charts, index_sha):
    """Sealed copy of the ONE chart decision the orchestrator made (the same object the page shows)."""
    if charts is None:
        return None
    if charts.get('status') == 'available' and charts.get('index_sha256') != index_sha:
        # The orchestrator binds charts to its own index; reaching here means the two disagree. Refuse.
        raise ValueError('An available chart is bound to a different index than the answer.')
    return {'status': charts.get('status'), 'reason': charts.get('reason'), 'rejected': charts.get('rejected'),
            'model_calls': 0, 'index_sha256': charts.get('index_sha256'),
            'tables': [{'key': t.get('key'), 'status': t.get('status'), 'reason': t.get('reason')}
                       for t in charts.get('tables', [])]}


def _agentic_provenance(agentic, index_sha):
    summary = agentic.get('summary') or {}
    return {
        'experimental': True,
        'question': agentic['question'],
        'index_sha256': index_sha,
        'plan': agentic['plan'],
        'decisions': [e for e in agentic['trace'] if e['type'] == 'decision'],
        'trace': agentic['trace'],
        'selected_round': agentic.get('selected_round'),
        'evidence_ids': [p['chunk_id'] for p in agentic.get('evidence', [])],
        'rounds': [{k: v for k, v in r.items() if k != 'draft_claims'} | {'draft_claim_count': len(r.get('draft_claims', []))}
                   for r in agentic.get('verification') or []],
        'held_claims': summary.get('held_claims', []),
        # Kept claims whose numbers code could not tie to their source context: model-verified only.
        'claims_needing_number_check': [c['text'] for c in summary.get('claims', [])
                                        if (c.get('verification') or {}).get('needs_human_number_check')],
        'abstention': summary.get('abstention'),
        'business_screening': agentic.get('business_screening', []),
        'charts': _chart_provenance(agentic.get('charts'), index_sha),
        'model_calls': agentic['model_calls'],
        'agents_run': agentic['agents_run'],
        'seconds': agentic['seconds'],
        'status': agentic['status'],
        'error': agentic.get('error'),
    }


def to_envelope(agentic, *, top_k, provenance, context_id):
    """Return a baseline-compatible envelope. Execution errors carry no result, like the baseline."""
    from src.research_pipeline import run_research
    base = copy.deepcopy(provenance or {})
    index_sha = _index_sha(base)
    agentic_block = _agentic_provenance(agentic, index_sha)
    request = {'query': agentic['question'], 'top_k': top_k}
    business_industry = agentic.get('business_industry')
    if business_industry:
        request['industry'] = business_industry
    if agentic['status'] == 'execution_error':
        error = agentic.get('error') or {}
        cause, kind = error.get('cause', 'unknown'), error.get('kind', 'provider')
        message = FAILURE_MESSAGES.get(cause) or (
            'The AI provider failed before a verified answer was produced. No answer was accepted.' if kind == 'provider'
            else 'Multi-agent research stopped at a call or step limit. No answer was accepted.')
        return {'mode': ENVELOPE_MODE, 'scenario': 'error', 'submitted_request': request, 'result': None,
                'error': {'stage': error.get('stage') or 'agentic', 'code': f'agentic_{kind}_failure', 'kind': kind,
                          'cause': cause, 'message': message,
                          **({'diagnostic': error['diagnostic']} if 'diagnostic' in error else {})},
                'fixture_file': None, 'context_id': context_id, 'agentic': agentic_block}

    summary = copy.deepcopy(agentic['summary'])
    evidence = copy.deepcopy(agentic['evidence'])
    business = agentic.get('business_insight')
    error = None
    translate_fn = None
    if business_industry:
        if business is None or business.get('status') in {'ok', 'insufficient_evidence'}:
            # None: no verified claims, so run_research records the standard skipped translation.
            translate_fn = lambda s, ps, *, industry: copy.deepcopy(business)  # noqa: E731
        else:
            request.pop('industry')
            provider = business.get('cause') == 'provider_failure'
            error = {'stage': 'business', 'kind': 'provider' if provider else 'validation' if business.get('status') == 'failed' else 'budget',
                     'code': 'business_provider_failure' if provider else 'business_failed' if business.get('status') == 'failed' else 'business_skipped',
                     'message': ('Business insight did not complete: ' + business.get('reason', 'unknown reason')[:200]
                                 + ' The verified research answer is kept.')}
    result = run_research(request, retrieve=lambda query, k: copy.deepcopy(evidence),
                          summarize_fn=lambda query, passages: copy.deepcopy(summary),
                          translate_fn=translate_fn,
                          provenance={**base, 'execution': EXECUTION, 'agentic': agentic_block,
                                      'timings_seconds': {'total': agentic['seconds']},
                                      'stages': {'retrieval': 'ok' if evidence else 'empty', 'summary': summary['status'],
                                                 'business': (business or {}).get('status', 'not_requested') if business_industry else 'not_requested'}})
    scenario = ('empty' if not result['evidence'] else 'insufficient' if result['summary']['status'] != 'ok'
                else 'partial' if error else 'full' if result.get('business_insight') else 'summary-only')
    envelope = {'mode': ENVELOPE_MODE, 'scenario': scenario, 'submitted_request': copy.deepcopy(request),
                'result': result, 'error': error, 'fixture_file': None, 'context_id': context_id}
    if agentic.get('charts') is not None:
        # Displayed decision == sealed provenance == trace: all three come from agentic['charts'].
        envelope['agentic_charts'] = copy.deepcopy(agentic['charts'])
    if 'numerical_shadow' in agentic:
        envelope['numerical_shadow'] = copy.deepcopy(agentic['numerical_shadow'])
    return envelope

"""Prompt/transport contracts, not a simulated model-quality verdict.

The source excerpt is from 2604.00324v1_c0038. The live q10 capture is
separate: a scripted provider here cannot prove semantic classification.
"""
import json
from copy import deepcopy
from unittest.mock import Mock

from src.evidence_led import summarize, translate


QUERY = 'What should a business ask a vendor claiming their AI agent is "interpretable"?'
QUOTE = 'First, pin down a behavior using a metric and data set.'
PASSAGES = [{'chunk_id': '2604.00324v1_c0038', 'text': QUOTE,
             'arxiv_id': '2604.00324v1', 'title': 'The Persistent Vulnerability of Aligned AI Systems'}]
GAP = 'The evidence does not establish vendor compliance or validation of the deployed system.'
LEDGER = {'coverage_gaps': [GAP], 'facts': [
    {'chunk_id': PASSAGES[0]['chunk_id'], 'quote': QUOTE,
     'finding': 'The described workflow specifies a behavior, metric and dataset.', 'relevance': 'direct'}]}
ANSWER = {'status': 'ok', 'claims': [
    {'text': LEDGER['facts'][0]['finding'], 'fact_ids': [0]}], 'limitations': [{'text': GAP, 'kind': 'coverage_gap', 'fact_ids': []}]}


def test_due_diligence_policy_reaches_both_generation_stages():
    """Regression for the conflicting extraction/synthesis prompt contract.

    Fails on the old prompts; no mocked semantic decision is counted as proof.
    Check the actual rendered requests, including original quote and gap.
    """
    provider = Mock(side_effect=[json.dumps(LEDGER), json.dumps(ANSWER)])
    out = summarize(QUERY, PASSAGES, generate=provider)
    assert out['status'] == 'ok'
    extract, synthesize = [call.args[0] for call in provider.call_args_list]
    assert 'CONDITIONAL due-diligence' in extract
    assert 'literal vendor-question wording' in extract
    assert 'does not establish vendor compliance or validation' in extract
    assert 'CONDITIONAL due-diligence' in synthesize
    assert 'Keep proposed checks out of research claims' in synthesize
    assert QUERY in extract and QUOTE in extract
    assert GAP in synthesize


def test_conditional_partial_chain_preserves_gap_quotes_and_unapproved_status():
    """Existing strict contracts permit the proposed partial answer shape."""
    from src.research_pipeline import run_research
    business = {'status': 'ok', 'industry': 'professional services', 'implications': [
        {'text': 'The workflow specifies a behavior, metric and dataset.',
         'chunk_ids': [PASSAGES[0]['chunk_id']],
         'suggested_action': 'Ask which behavior, metric and dataset support the claim; compare the vendor evidence with the claimed scope.',
         'assumptions': ['Applying this research workflow to vendor due diligence is a proposed transfer, not tested vendor validation.']}],
        'risks': [], 'limitations': [GAP]}
    provider = Mock(side_effect=[json.dumps(LEDGER), json.dumps(ANSWER), json.dumps(business)])
    result = run_research({'query': QUERY, 'industry': 'professional services', 'top_k': 5},
        retrieve=lambda q, k: deepcopy(PASSAGES),
        summarize_fn=lambda q, p: summarize(q, p, generate=provider),
        translate_fn=lambda s, p, *, industry: translate(s, p, industry=industry, generate=provider))
    assert result['summary']['status'] == 'ok'
    assert GAP in result['summary']['limitations']
    assert result['summary']['evidence_ledger']['facts'][0]['quote'] == QUOTE
    assert result['business_insight'] == business
    assert result['approved'] is False


def test_due_diligence_does_not_bypass_quote_or_context_gates():
    context = deepcopy(LEDGER)
    context['facts'][0]['relevance'] = 'context'
    provider = Mock(return_value=json.dumps(context))
    assert summarize(QUERY, PASSAGES, generate=provider)['claims'] == []
    assert provider.call_count == 1
    fabricated = deepcopy(LEDGER)
    fabricated['facts'][0]['quote'] = 'The vendor has validated its deployed system.'
    provider = Mock(return_value=json.dumps(fabricated))
    out = summarize(QUERY, PASSAGES, generate=provider)
    assert out['error'] == 'evidence_led_failed'
    assert out['claims'] == []
    assert provider.call_count == 1  # Main fails closed without a correction call.

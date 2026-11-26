"""TEST-ONLY deterministic stand-in for ``src.codex_generation`` (no network, no model).

Injected as ``sys.modules['src.codex_generation']`` in a child process so the REAL live backend, capped wrapper, call
ledger, retrieval index, orchestrator, validators and envelope run unchanged while every "model" answer is produced
here. Answers are schema-valid and quote the passages the backend actually retrieved, so they pass the exact-quote
validators. They are NOT research results and must never be reported as such.

Recognized prompts: baseline synthesis, baseline quality review, orchestrator plan, verification. Any other prompt raises
(so an unexpected model call, e.g. business translation, fails loudly). Every call is appended to FAKE_CALL_LOG when set.
"""
import json
import os
import re

PAYLOAD_MARKER = '{"question": '


def _payload(prompt):
    start = prompt.find(PAYLOAD_MARKER)
    while start != -1:
        try:
            return json.loads(prompt[start:])
        except ValueError:
            start = prompt.find(PAYLOAD_MARKER, start + 1)
    raise ValueError('fake provider: no JSON payload in prompt')


def _quote(text):
    text = re.sub(r'\s+', ' ', text or '').strip()
    sentence = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)[0]
    sentence = sentence if 15 <= len(sentence) <= 300 else text[:200].rsplit(' ', 1)[0]
    return sentence


def _log(kind):
    path = os.environ.get('FAKE_CALL_LOG')
    if path:
        with open(path, 'a', encoding='utf-8') as handle:
            handle.write(kind + '\n')


def answer(prompt):
    if prompt.startswith('Synthesize an answer'):
        _log('baseline_or_research_synthesis')
        passages = _payload(prompt)['paper_passages'][:2]
        claims = [{'text': _quote(p['text']), 'kind': 'finding', 'support': [{'chunk_id': p['chunk_id'], 'quote': _quote(p['text'])}]}
                  for p in passages if len(_quote(p['text'])) >= 15]
        return {'status': 'ok' if claims else 'insufficient_evidence', 'claims': claims,
                'limitations': [] if claims else [{'text': 'No usable passage.', 'support': [
                    {'chunk_id': passages[0]['chunk_id'], 'quote': _quote(passages[0]['text'])}]}]}
    if prompt.startswith('ANSWER QUALITY REVIEW'):
        _log('baseline_quality_review')
        claims = _payload(prompt)['draft']['claims']
        return {'coverage': 'full', 'gap': '', 'retained_claim_indices': list(range(len(claims))), 'limitations': [],
                'decisions': [{'index': i, 'supported': True, 'relevant': True, 'reason': 'fake provider'} for i in range(len(claims))]}
    if prompt.startswith('You are the planning orchestrator'):
        _log('agentic_plan')
        return {'question_type': 'other', 'subquestions': [], 'notes': 'fake provider plan',
                'business': {'delegate': False, 'industry_in_question': '', 'reason': 'fake provider'},
                'chart': {'delegate': False, 'reason': 'fake provider'}}
    if prompt.startswith('You are an independent evidence verifier'):
        _log('agentic_verify')
        claims = _payload(prompt)['claims']
        return {'verdicts': [{'index': c['index'], 'verdict': 'supported', 'issues': [], 'reason': 'fake provider'} for c in claims],
                'coverage': 'full', 'missing_aspects': [], 'retrieval_request': {'needed': False, 'query': '', 'reason': 'fake provider'}}
    _log('UNEXPECTED')
    raise RuntimeError('fake provider: unexpected prompt type (no such call is allowed in the research-only A/B)')


def create_codex_generate(**kwargs):
    def inner(prompt, response_schema=None):
        return json.dumps(answer(prompt))
    return inner, {'provider': 'fake_provider (test only)', 'model': 'none'}

"""Launch the sealed candidate for browser tests with scripted generation only."""
from base64 import b64encode
import json
import os
from pathlib import Path
import re
import sys
import time

DUMMY_PASSWORD = 'local-fixture-only-not-a-secret'
QUESTION = 'By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?'
QUOTE = 'On mathematical reasoning benchmarks, CU- DPO improves strategy selection accuracy from 35–46% to 68–78% across seven base models, yielding consistent downstream reasoning gains of up to +6.6 points on in-distribution datasets with effective transfer to out-of-distribution tasks.'
CLAIM = 'On mathematical reasoning benchmarks, CU-DPO improved strategy-selection accuracy from 35–46% to 68–78% across seven base models.'
APPLIED = 'What are the business implications of the CU-DPO accuracy results for AI model routing in financial services?'
FAILURE = 'What are the business implications of the CU-DPO accuracy results for AI model routing in banking?'


def scripted(prompt, *, response_schema, question=QUESTION, quote=QUOTE, claim=CLAIM):
    properties = response_schema.get('properties', {})
    if 'decisions' in properties and 'retained_claim_indices' not in properties:
        return json.dumps({'coverage': 'full', 'gap': '', 'limitations': [], 'decisions': [{
            'index': 0, 'supported': True, 'relevant': True, 'quotes_entail': True,
            'reason': 'The retrieved passage supports the scripted finding.',
            'supported_text': '', 'reduced_entailed': False, 'related': False,
            'added_support': [], 'flag_resolutions': []
        }]})
    if prompt.startswith('Decide whether this research question genuinely needs clarification'):
        # Scripted follow-up resolution through the existing query-clarification contract.
        query = json.loads(prompt.rsplit('\n', 1)[1])['query']
        if 'that one' in query:
            return json.dumps({'decision': 'clarify', 'resolved_query': '', 'question': 'Which result do you mean?',
                               'options': [{'text': 'The strategy-selection accuracy gain', 'support': []}]})
        # A risks follow-up continues the business question (scripted resolution writes the topic in).
        resolved = APPLIED if 'risks' in query else question
        return json.dumps({'decision': 'continue', 'resolved_query': resolved, 'question': '', 'options': []})
    if prompt.startswith('Synthesize an answer'):
        request = json.loads(prompt.split('\n', 1)[1])
        if request['question'] != question:
            raise ValueError('Only the disclosed browser-test question is allowed.')
        passage = next(p for p in request['paper_passages'] if quote in ' '.join(p['text'].split()))
        return json.dumps({'status': 'ok', 'claims': [
            {'text': claim, 'kind': 'finding', 'support': [{'chunk_id': passage['chunk_id'], 'quote': quote}]}
        ], 'limitations': []})
    from src.answer_quality import POLICY
    if prompt.startswith(POLICY):
        draft = json.loads(prompt[len(POLICY):])['draft']
        assert len(draft['claims']) == 1 and draft['claims'][0]['text'] == claim
        return json.dumps({'coverage': 'full', 'gap': '', 'retained_claim_indices': [0],
                           'decisions': [{'index': 0, 'supported': True, 'relevant': True,
                                          'reason': 'The retrieved passage supports the scripted finding.'}],
                           'limitations': []})
    raise ValueError('Unexpected generation stage.')


def main():
    context, state = (Path(v).resolve() for v in sys.argv[1:3])
    business_intent = '--business-intent' in sys.argv[3:]
    if business_intent:
        os.environ.update(RESEARCH_ENGINE='s2', S2_PAPER_BALANCE='0', KPMG_GEMINI_SMOKE='0')
    sys.path.insert(0, str(context / 'experiments/render-staging'))
    from server import Server, build_handler

    def research(prompt, *, response_schema):
        question = QUESTION
        if business_intent and prompt.startswith('Synthesize an answer'):
            question = json.loads(prompt.split('\n', 1)[1])['question']
            if question not in {QUESTION, APPLIED, FAILURE}:
                raise ValueError('Unexpected business intent fixture question.')
        return scripted(prompt, response_schema=response_schema, question=question)

    failures = []

    def business(prompt):
        time.sleep(1.5)
        if FAILURE in prompt and not failures:
            # First attempt: the provider is temporarily unavailable (as after a 503 and its retry).
            failures.append(1)
            from src.business_generation import BusinessTranslationUnavailable
            raise BusinessTranslationUnavailable('Offline provider failure fixture.')
        chunk = re.search(r'"chunk_id"\s*:\s*"([^"]+)"', prompt)[1]
        return json.dumps({'status': 'ok', 'industry': 'banking' if FAILURE in prompt else 'financial services', 'risks': [],
                           'limitations': ['The benchmark uses mathematical reasoning tasks.'],
                           'implications': [{'text': 'Use the benchmark to choose what to measure in routing.',
                                             'chunk_ids': [chunk],
                                             'suggested_action': 'Compare routing accuracy on the review queue.',
                                             'assumptions': ['A routing review queue is available.']}]})

    start = time.perf_counter()
    with Server(('127.0.0.1', 0), None) as service:
        origin = f'http://127.0.0.1:{service.server_port}'
        service.RequestHandlerClass = build_handler(context / 'snapshot', state, origin,
                                                     DUMMY_PASSWORD, research, {'provider': 'scripted-fixture'},
                                                     business_generate=business if business_intent else None,
                                                     business_metadata={'execution': 'offline_fixture'})
        print(json.dumps({'origin': origin, 'seconds': round(time.perf_counter() - start, 2),
                          'auth': b64encode(f'reviewer:{DUMMY_PASSWORD}'.encode()).decode()}), flush=True)
        service.serve_forever()


if __name__ == '__main__':
    main()

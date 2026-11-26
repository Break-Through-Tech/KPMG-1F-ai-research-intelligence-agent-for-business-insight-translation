"""Launch the sealed candidate for browser tests with scripted generation only."""
from base64 import b64encode
import json
from pathlib import Path
import sys
import time

context, state = (Path(v).resolve() for v in sys.argv[1:])
sys.path.insert(0, str(context / 'experiments/render-staging'))
from server import Server, build_handler
from src.answer_quality import POLICY

DUMMY_PASSWORD = 'local-fixture-only-not-a-secret'
QUESTION = 'By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?'
QUOTE = 'On mathematical reasoning benchmarks, CU- DPO improves strategy selection accuracy from 35–46% to 68–78% across seven base models, yielding consistent downstream reasoning gains of up to +6.6 points on in-distribution datasets with effective transfer to out-of-distribution tasks.'
CLAIM = 'On mathematical reasoning benchmarks, CU-DPO improved strategy-selection accuracy from 35–46% to 68–78% across seven base models.'


def scripted(prompt, *, response_schema):
    if prompt.startswith('Synthesize an answer'):
        request = json.loads(prompt.split('\n', 1)[1])
        if request['question'] != QUESTION:
            raise ValueError('Only the disclosed browser-test question is allowed.')
        passage = next(p for p in request['paper_passages'] if QUOTE in ' '.join(p['text'].split()))
        return json.dumps({'status': 'ok', 'claims': [
            {'text': CLAIM, 'kind': 'finding', 'support': [{'chunk_id': passage['chunk_id'], 'quote': QUOTE}]}
        ], 'limitations': []})
    if prompt.startswith(POLICY):
        draft = json.loads(prompt[len(POLICY):])['draft']
        assert len(draft['claims']) == 1 and draft['claims'][0]['text'] == CLAIM
        return json.dumps({'coverage': 'full', 'gap': '', 'retained_claim_indices': [0],
                           'decisions': [{'index': 0, 'supported': True, 'relevant': True,
                                          'reason': 'The retrieved abstract supplies the exact ranges and model count.'}],
                           'limitations': []})
    raise ValueError('Unexpected generation stage.')


start = time.perf_counter()
with Server(('127.0.0.1', 0), None) as service:
    origin = f'http://127.0.0.1:{service.server_port}'
    service.RequestHandlerClass = build_handler(context / 'snapshot', state, origin,
                                                 DUMMY_PASSWORD, scripted, {'provider': 'scripted-fixture'})
    print(json.dumps({'origin': origin, 'seconds': round(time.perf_counter() - start, 2),
                      'auth': b64encode(f'reviewer:{DUMMY_PASSWORD}'.encode()).decode()}), flush=True)
    service.serve_forever()

"""Local developer preview. Uses scripted responses and never invokes a provider."""
import argparse
import json
import os
from pathlib import Path
from secrets import token_urlsafe

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ.setdefault('OMP_NUM_THREADS', '1')

from server import Server, build_handler
from smoke_server import CLAIM, QUESTION, QUOTE, scripted

FIXTURE_QUESTION = "What does the test fixture contain?"
FIXTURE_QUOTE = "The test fixture contains one blue box."


def fake(prompt, *, response_schema, question=QUESTION, quote=QUOTE, claim=CLAIM):
    if prompt.startswith('Synthesize an answer'):
        request = json.loads(prompt.split('\n', 1)[1])
        if request['question'] != question:
            return json.dumps({'status': 'insufficient_evidence', 'claims': [], 'limitations': []})
    return scripted(prompt, response_schema=response_schema, question=question, quote=quote, claim=claim)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--engine', choices=('baseline', 's2'), default='baseline')
    parser.add_argument('--container', action='store_true')
    parser.add_argument('--fixture', action='store_true')
    args = parser.parse_args()
    os.environ['RESEARCH_ENGINE'] = args.engine
    os.environ['S2_PAPER_BALANCE'] = '0'
    os.environ['KPMG_GEMINI_SMOKE'] = '0'
    origin = 'http://127.0.0.1:8821'
    args.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    password = token_urlsafe(24)
    question = FIXTURE_QUESTION if args.fixture else QUESTION

    def generate(prompt, *, response_schema):
        if args.fixture:
            return fake(prompt, response_schema=response_schema, question=question,
                        quote=FIXTURE_QUOTE, claim=FIXTURE_QUOTE)
        return fake(prompt, response_schema=response_schema)

    handler = build_handler(args.snapshot, args.state, origin, password, generate,
                            {'provider': 'offline-fixture'}, synthetic_fixture=args.fixture)
    host = '0.0.0.0' if args.container else '127.0.0.1'
    with Server((host, 8821), handler) as server:
        print(f'Offline preview: {origin} (reviewer / {password})', flush=True)
        print(f'Scripted demo question: {question}', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()

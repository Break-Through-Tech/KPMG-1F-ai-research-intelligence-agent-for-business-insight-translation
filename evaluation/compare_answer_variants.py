"""Frozen-evidence Codex subscription comparison; no human-rating fabrication."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

from src.codex_generation import create_codex_generate
from src.summarization import summarize, prompt_provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codex-bin', required=True)
    parser.add_argument('--models', nargs='+', required=True)
    parser.add_argument('--queries', nargs='+', default=['q03', 'q04', 'q05'])
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new experiment output directory')
    baseline = json.loads(args.baseline.read_text())
    args.output.mkdir(parents=True)
    cases = [c for c in baseline['cases'] if c['case']['query_id'] in args.queries]
    if len(cases) != len(set(args.queries)) or any(c['status'] != 'ok' for c in cases):
        parser.error('Requested cases must be available in the frozen baseline')
    for model in args.models:
        receipts = []
        generate, metadata = create_codex_generate(model=model, binary=args.codex_bin,
                                                   receipts=receipts)
        outputs = []
        for case in cases:
            start = time.monotonic()
            result = summarize(case['case']['query'], case['result']['evidence'], generate=generate)
            outputs.append({'query_id': case['case']['query_id'], 'summary': result,
                            'elapsed_seconds': round(time.monotonic()-start, 3)})
            artifact = {'experiment': 'model_only_frozen_evidence',
                        'baseline_run_id': baseline['run_id'],
                        'baseline_sha256': sha256(args.baseline.read_bytes()).hexdigest(),
                        'generation': {**metadata, **prompt_provenance()},
                        'outputs': outputs, 'receipts': receipts,
                        'reviewer_kind': 'synthetic', 'human_reviews_added': 0}
            (args.output / f'{model}.json').write_text(json.dumps(artifact, indent=2)+'\n')
            print(json.dumps({'model': model, 'query': case['case']['query_id'],
                              'status': result['status'], 'error': result.get('error')}), flush=True)


if __name__ == '__main__':
    main()

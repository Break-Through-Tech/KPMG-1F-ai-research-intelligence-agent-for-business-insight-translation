"""Explicit-provider development smoke evaluation; not held-out acceptance."""
import argparse
from functools import partial
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.query_clarification import clarification_with_generation


def evaluate(cases, clarify):
    rows = []
    for case in cases:
        start = time.monotonic()
        try:
            output = clarify(phase=case['phase'], query=case['query'],
                             history=case['history'], passages=case['passages'])
            predicted = output['decision']
            row = {'id': case['id'], 'expected': case['expected'],
                   'predicted': predicted, 'correct': predicted == case['expected'],
                   'output': output}
        except Exception:
            row = {'id': case['id'], 'expected': case['expected'],
                   'predicted': None, 'correct': False, 'error': 'adapter_or_contract_failure'}
        row['seconds'] = time.monotonic() - start
        rows.append(row)
    clear = [r for r in rows if r['expected'] == 'continue']
    ambiguous = [r for r in rows if r['expected'] == 'clarify']
    return {'scope': 'synthetic_development_cases_not_held_out', 'cases': rows,
            'total': len(rows), 'correct': sum(r['correct'] for r in rows),
            'errors': sum(r['predicted'] is None for r in rows),
            'clear_cases': len(clear),
            'unnecessary_clarifications': sum(r['predicted'] == 'clarify' for r in clear),
            'ambiguous_cases': len(ambiguous),
            'missed_ambiguities': sum(r['predicted'] == 'continue' for r in ambiguous),
            'generation_quality_evaluated': False, 'final_answer_quality_evaluated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=Path(__file__).resolve().parents[1] /
                        'tests/fixtures/clarification/development.json')
    route = parser.add_mutually_exclusive_group(required=True)
    route.add_argument('--configured-provider', action='store_true')
    route.add_argument('--codex-model')
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())
    if args.codex_model:
        from src.codex_generation import create_codex_generate
        generate, metadata = create_codex_generate(model=args.codex_model)
    else:
        from src.generation import create_generate
        generate, metadata = create_generate()
    report = evaluate(cases, partial(clarification_with_generation, generate=generate))
    report['generation'] = metadata
    print(json.dumps(report, indent=2, allow_nan=False))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

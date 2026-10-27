"""Retain side-by-side development examples using an explicitly selected subscription.

python -m scripts.plain_language_examples --result saved.json --codex-model MODEL --out /tmp/examples.json
This executes generation but never records semantic approval or changes the result.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from src.plain_language import generate_view, result_identity
from src.codex_generation import create_codex_generate
from src.research_contracts import validate_result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--codex-model', required=True)
    parser.add_argument('--codex-bin')
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    validate_result(result)
    generate, metadata = create_codex_generate(model=args.codex_model, binary=args.codex_bin)
    view = generate_view(result, generate=generate, metadata=metadata)
    packet = {'recorded_at': datetime.now(timezone.utc).isoformat(),
              'purpose': 'development example; not held-out evaluation or independent review',
              'result_identity': result_identity(result), 'original': result,
              'plain_language': view, 'semantic_review': 'pending'}
    args.out.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': view['status'], 'semantic_review': 'pending', 'output': str(args.out)}))
    if view['status'] != 'available':
        raise SystemExit(1)


if __name__ == '__main__':
    main()

"""Frozen-evidence development check. Outputs are not independent quality scores."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from src.answer_quality import review_summary, provenance
from src.business_translation import translate
from src.codex_generation import create_codex_generate
from src.research_chat import synthesize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--effort', choices=('low', 'medium', 'high', 'xhigh'), default='medium')
    parser.add_argument('--compact-business', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = json.loads(args.baseline.read_text(encoding='utf-8-sig'))
    if baseline.get('error') or not baseline.get('result'):
        raise ValueError('Baseline must be a successful real result.')
    result = baseline['result']
    evidence = result['evidence']
    cases = [
        {'id': 'banking-transfer', 'query': result['request']['query'], 'industry': 'banking',
         'expectation': 'Retain bounded architecture findings; explicitly mark untested banking transfer; advice only in business stage.'},
        {'id': 'supported-control', 'query': 'What did the trip-planning comparison find about single-agent versus multi-agent performance?',
         'expectation': 'Retain the positive orchestrated comparison and adverse generic-framework comparison.'},
        {'id': 'unrelated-control', 'query': 'What measured improvement in wheat yields did these experiments demonstrate?',
         'expectation': 'Abstain; no agricultural results are present in the frozen passages.'}]
    receipts = []
    generate, metadata = create_codex_generate(model=args.model, effort=args.effort, receipts=receipts)
    report = {'kind': 'development_only_not_held_out', 'baseline_sha256': sha256(args.baseline.read_bytes()).hexdigest(),
              'evidence_sha256': sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest(),
              'generation': metadata, 'policy': provenance(), 'compact_business': args.compact_business,
              'cases': cases, 'results': []}
    # Freeze case definitions before the first call; retain failures and never overwrite a run.
    def save():
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (args.output / 'receipts.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    save()
    for case in cases:
        row = {'id': case['id']}
        try:
            draft = synthesize(case['query'], deepcopy(evidence), generate=generate,
                               findings_only=bool(case.get('industry')))
            summary = review_summary(case['query'], draft, evidence, generate=generate)
            row.update(status='completed', draft=draft, summary=summary)
            if case.get('industry'):
                ids = {cid for claim in summary['claims'] for cid in claim['chunk_ids']}
                row['business'] = translate({k: v for k, v in summary.items() if k != 'quality_review'},
                    [p for p in evidence if p['chunk_id'] in ids], industry=case['industry'], generate=generate,
                    compact=args.compact_business)
        except Exception as error:
            row.update(status='failed', error_type=type(error).__name__)
        report['results'].append(row)
        save()
        print(case['id'], row['status'], row.get('summary', {}).get('status'), flush=True)


if __name__ == '__main__':
    main()

"""Offline measurement of automatic business-intent detection. No model calls.

python -B experiments/business-intent/measure.py [--before <path to an older business_insights.py>] [--verbose]
Splits: dev and heldout (intent-eval-v1.json, written by the implementer) and blind
(intent-eval-blind-v1.json, written by a separate model that never saw the parser).
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FIXTURES = ROOT / 'tests/fixtures/business'
ALIASES = {'telecom': 'telecommunications', 'pharmaceuticals': 'healthcare', 'aviation': 'transportation',
           'financial services': 'banking'}


def load(path):
    if path is None:
        from src import business_insights
        return business_insights.automatic_business_context
    spec = importlib.util.spec_from_file_location('business_insights_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.automatic_business_context


def same_sector(got, expected):
    if expected is None:
        return True  # unnamed in the question; any normalization is acceptable
    norm = lambda s: ALIASES.get(s, s)
    return norm(got) == norm(expected)


def overlaps(got, expected):
    words = lambda s: {w for w in re.findall(r'[a-z]{4,}', s.lower())}
    return expected.lower() in got.lower() or got.lower() in expected.lower() or bool(words(got) & words(expected))


def main():
    before = sys.argv[sys.argv.index('--before') + 1] if '--before' in sys.argv else None
    verbose = '--verbose' in sys.argv
    detect = load(before)
    splits = dict(json.loads((FIXTURES / 'intent-eval-v1.json').read_text(encoding='utf-8')))
    splits.pop('description')
    splits['blind'] = json.loads((FIXTURES / 'intent-eval-blind-v1.json').read_text(encoding='utf-8'))['blind']
    splits['blind2'] = json.loads((FIXTURES / 'intent-eval-blind-v2.json').read_text(encoding='utf-8'))['blind2']
    splits['blind3'] = json.loads((FIXTURES / 'intent-eval-blind-v3.json').read_text(encoding='utf-8'))['blind3']
    for split, rows in splits.items():
        tp = fn = fp = tn = sector_ok = workflow_ok = 0
        for row in rows:
            context = detect(row['q'])
            expected = row['label'] == 'business'
            if expected and context:
                tp += 1
                s_ok = same_sector(context['industry'], row.get('industry'))
                w_ok = overlaps(context['workflow'], row['workflow'])
                sector_ok += s_ok
                workflow_ok += w_ok
                if verbose and not (s_ok and w_ok):
                    print(f'  [{split}] partial  {context["industry"]!r} / {context["workflow"]!r} :: {row["q"]}')
            elif expected:
                fn += 1
                if verbose:
                    print(f'  [{split}] MISSED   :: {row["q"]}')
            elif context:
                fp += 1
                if verbose:
                    print(f'  [{split}] FALSE+ ({row["label"]}) {context["industry"]!r} / {context["workflow"]!r} :: {row["q"]}')
            else:
                tn += 1
        business = tp + fn
        print(f'{split:8} recall {tp}/{business} ({tp / business:.0%})  false positives {fp}/{fp + tn}  '
              f'sector ok {sector_ok}/{tp}  workflow ok {workflow_ok}/{tp}')


if __name__ == '__main__':
    main()

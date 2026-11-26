"""Import setup for the consolidated experiment: repository root, the frozen Multi-Agent modules (planner only),
verification-repair (numeric_checks_v2 + interpretation gate) and evidence-budget. Nothing here calls a model."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for path in (ROOT, HERE.parent / 'agentic', HERE.parent / 'verification-repair', HERE.parent / 'evidence-budget',
             HERE.parent / 'agentic-handoff', HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
BUNDLE_PARENTS = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')


def load_v2():
    from verification_v2 import load_v2 as loader
    return loader()


def load_gate():
    from interpretation_gate import gate
    return gate


def bundle_rows(path=BUNDLE_PARENTS):
    import json
    with open(path, encoding='utf-8') as handle:
        return [json.loads(line) for line in handle]

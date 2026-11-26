"""Seal for the fresh-v3 validation: the question set, rules and key, plus the code of all four arms and their
runners. Any change after sealing makes every arm's --check and --run refuse.

    python -I seal_v3.py --write     (only after the key review and human sign-off)
"""
from hashlib import sha256
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ROOT = EXP.parent
SET = HERE / 'fresh-v3'
CODE = {
    'S2/D2 consolidated-v2': [HERE / n for n in ('engine.py', 'evidence.py', 'synthesis.py', 'review.py', 'publication.py',
                                                  'env.py', 'accounting.py', 'run_consolidated.py', 'fresh3_arms.py')],
    'S1 consolidated-v1': [EXP / 'consolidated' / n for n in ('engine.py', 'evidence.py', 'synthesis.py', 'review.py',
                                                             'publication.py', 'env.py', 'run_consolidated.py')]
                          + [HERE / 'run_fresh3_s1.py'],
    'B0 original baseline': [EXP / 'agentic-handoff' / n for n in ('codex_baseline.py', 'codex_paired.py')]
                            + [ROOT / 'src' / n for n in ('research_chat.py', 'answer_quality.py', 'indexed_research.py',
                                                          'research_pipeline.py', 'research_contracts.py')]
                            + [ROOT / 'src/experimental' / n for n in ('demo.py', 'b2.py', 'balanced_retriever.py',
                                                                      'evidence_coverage.py', 'search_index.py')]
                            + [HERE / 'run_fresh3_b0.py'],
    'shared': [EXP / 'verification-repair' / n for n in ('numeric_checks_v2.py', 'interpretation_gate.py',
                                                         'verification_v2.py')]
              + [EXP / 'agentic/statistical_reports.py', EXP / 'evidence-budget/evidence_budget.py',
                 EXP / 'evidence-budget/request_guard.py', ROOT / 'src/codex_generation.py'],
}


def files():
    out = {f'set/{p.name}': p for p in sorted(SET.glob('*')) if p.is_file() and p.name != 'seal.json'}
    for group, paths in CODE.items():
        for path in paths:
            out[f'code/{path.resolve().relative_to(ROOT).as_posix()}'] = path
    return out


def write():
    seal = {name: sha256(path.read_bytes()).hexdigest() for name, path in files().items()}
    (SET / 'seal.json').write_text(json.dumps(seal, indent=1), encoding='utf-8')
    return seal


def verify():
    seal = json.loads((SET / 'seal.json').read_text(encoding='utf-8'))
    current = files()
    if set(seal) != set(current):
        raise SystemExit(f'Sealed file list changed: {sorted(set(seal) ^ set(current))[:5]}')
    for name, path in current.items():
        if sha256(path.read_bytes()).hexdigest() != seal[name]:
            raise SystemExit(f'Sealed file changed after sealing: {name}')
    return 'verified'


if __name__ == '__main__':
    if '--write' in sys.argv:
        print(len(write()), 'files sealed')
    else:
        print(verify())

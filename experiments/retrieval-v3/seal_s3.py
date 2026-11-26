"""Two-part seal for the final corrective round.

  code freeze  s3-freeze.json: S3 code, the fresh-v4 runner, the frozen V2 engine modules, shared gates and the B2
               retrieval code. Written BEFORE S3 is evaluated on any fresh material; never rewritten.
  set seal     fresh-v4/seal.json: questions, references, key, rules and the validation-bundle record. Written only
               after the independent key review and the project lead's sign-off.

    python -I seal_s3.py --freeze      (once, before fresh-set coverage)
    python -I seal_s3.py --write-set   (after key review and sign-off)
    python -I seal_s3.py               (verify both; the live runner refuses unless both verify)
"""
from hashlib import sha256
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ROOT = EXP.parent
SET = HERE / 'fresh-v4'
FREEZE = HERE / 's3-freeze.json'
V2 = EXP / 'consolidated-v2'
CODE = (
    [HERE / n for n in ('s3_env.py', 's3_evidence.py', 's3_answer.py', 's3_engine.py', 'components.py', 'run_fresh4.py')]
    + [V2 / n for n in ('engine.py', 'evidence.py', 'synthesis.py', 'review.py', 'publication.py', 'env.py',
                        'accounting.py')]
    + [EXP / 'verification-repair' / n for n in ('numeric_checks_v2.py', 'interpretation_gate.py', 'verification_v2.py')]
    + [EXP / 'agentic/statistical_reports.py', EXP / 'evidence-budget/evidence_budget.py',
       EXP / 'evidence-budget/request_guard.py', EXP / 'agentic-handoff/codex_paired.py',
       EXP / 'agentic-handoff/codex_baseline.py', ROOT / 'src/codex_generation.py', ROOT / 'src/answer_quality.py']
    + [ROOT / 'src/experimental' / n for n in ('b2.py', 'retriever.py', 'balanced_retriever.py', 'evidence_coverage.py',
                                               'search_index.py', 'search_chunks.py')]
)


def _digest(paths):
    return {path.resolve().relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in paths}


def set_files():
    return sorted(p for p in SET.glob('*') if p.is_file() and p.suffix in ('.json', '.md')
                  and p.name not in ('seal.json',) and not p.name.startswith('coverage'))


def freeze():
    if FREEZE.is_file():
        raise SystemExit('Code freeze already written; it is never rewritten.')
    FREEZE.write_text(json.dumps(_digest(CODE), indent=1), encoding='utf-8')
    return len(CODE)


def write_set():
    (SET / 'seal.json').write_text(json.dumps(_digest(set_files()), indent=1), encoding='utf-8')
    return len(set_files())


def _check(path, current):
    sealed = json.loads(path.read_text(encoding='utf-8'))
    if set(sealed) != set(current):
        raise SystemExit(f'Sealed file list changed ({path.name}): {sorted(set(sealed) ^ set(current))[:5]}')
    for name, digest in current.items():
        if digest != sealed[name]:
            raise SystemExit(f'Sealed file changed after sealing ({path.name}): {name}')


def verify_code():
    _check(FREEZE, _digest(CODE))
    return 'code verified'


def verify():
    verify_code()
    _check(SET / 'seal.json', _digest(set_files()))
    return 'verified'


if __name__ == '__main__':
    if '--freeze' in sys.argv:
        print(freeze(), 'code files frozen')
    elif '--write-set' in sys.argv:
        print(write_set(), 'set files sealed')
    else:
        print(verify())

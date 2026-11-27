"""Offline replay of saved Multi-Agent verification decisions under the frozen and v2 number checks, plus the
labelled-interpretation gate. No model calls: the saved verifier verdicts are reused; only deterministic checks run.

    python -I replay.py [--detail] [run folders ...]   (default: every saved Multi-Agent run under data/processed)

Decision rule replayed (agents.VerificationAgent): held if quote or number check fails; else held unless the verifier
said supported with no issues. Interpretations: frozen = held by policy; v2 = interpretation_gate.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE.parent / 'agentic'), str(ROOT)]
DATA = ROOT / 'data/processed'
BUNDLE = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')

import numeric_checks as frozen  # noqa: E402
import statistical_reports  # noqa: E402
statistical_reports.enable()


def load_v2():
    spec = importlib.util.spec_from_file_location('numeric_checks_v2', HERE / 'numeric_checks_v2.py')
    v2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v2)
    saved = sys.modules.get('numeric_checks')
    sys.modules['numeric_checks'] = v2
    try:
        spec = importlib.util.spec_from_file_location('statistical_reports_v2', HERE.parent / 'agentic/statistical_reports.py')
        stat = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stat)
        stat.enable()
    finally:
        sys.modules['numeric_checks'] = saved
    return v2


v2 = load_v2()
import interpretation_gate  # noqa: E402

PASSAGES = {}
for line in BUNDLE.open(encoding='utf-8'):
    record = json.loads(line)
    PASSAGES[record['chunk_id']] = {'chunk_id': record['chunk_id'], 'text': record['text']}


def decide(row, claim, module):
    grounding = module.ground_claim(claim, PASSAGES)
    if row['deterministic'].get('quote_membership') != 'passed':
        return 'held', 'quote', grounding
    if grounding['contradictions']:
        return 'held', 'numbers: ' + ', '.join(grounding['contradictions']), grounding
    verdict = row.get('automated') or {}
    if verdict.get('verdict') != 'supported' or verdict.get('issues'):
        return 'held', f"verifier {verdict.get('verdict')} {verdict.get('issues')}", grounding
    return 'accepted', None, grounding


def results(folders):
    for folder in folders:
        for path in sorted([*folder.rglob('result.json'), *folder.rglob('agentic.json')]):
            if '.attempt-' in str(path):
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            if path.name == 'agentic.json':  # Codex paired / three-arm runs keep the summary here
                summary = data.get('summary') or {}
            else:
                summary = (((data.get('envelope') or {}).get('result') or {}).get('summary')) or {}
            rows = [(c, 'accepted') for c in summary.get('claims', [])] + [(c, 'held') for c in summary.get('held_claims', [])]
            rows = [(c, s) for c, s in rows if isinstance(c.get('verification'), dict) and 'deterministic' in c['verification']]
            if rows:
                yield path.relative_to(DATA), rows


def main():
    detail = '--detail' in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith('--')]
    folders = [DATA / n for n in names] or sorted(p for p in DATA.iterdir() if p.is_dir())
    totals = {'findings': 0, 'frozen_accepted': 0, 'v2_accepted': 0, 'released': 0, 'newly_held': 0,
              'saved_mismatch': 0, 'interpretations': 0, 'interp_published': 0}
    for path, rows in results(folders):
        verified = [c['text'] for c, saved in rows if saved == 'accepted' and c.get('kind') != 'interpretation']
        for claim, saved in rows:
            row = claim['verification']
            if claim.get('kind') == 'interpretation':
                totals['interpretations'] += 1
                cited = [PASSAGES[i] for i in claim.get('chunk_ids', []) if i in PASSAGES]
                failed = interpretation_gate.gate(row, claim, v2, cited, verified)
                totals['interp_published'] += not failed
                print(f"INTERP {path.parent} {'PUBLISH' if not failed else 'held ' + ' '.join(failed)} | {claim['text'][:150]}")
                continue
            totals['findings'] += 1
            f_dec, f_why, _ = decide(row, claim, frozen)
            n_dec, n_why, n_ground = decide(row, claim, v2)
            if f_dec != saved:
                totals['saved_mismatch'] += 1
                print(f'  [replay != saved] {path.parent} saved={saved} frozen={f_dec} ({f_why}) | {claim["text"][:90]}')
            totals['frozen_accepted'] += f_dec == 'accepted'
            totals['v2_accepted'] += n_dec == 'accepted'
            if f_dec != n_dec:
                key = 'released' if n_dec == 'accepted' else 'newly_held'
                totals[key] += 1
                print(f"{key.upper()} {path.parent} frozen: {f_why} -> v2: {n_why or 'accepted'} | {claim['text'][:150]}")
                if detail:
                    for m in n_ground['mentions']:
                        if m['status'] != 'grounded':
                            print('     ', m)
            elif f_dec == 'held' and f_why.startswith('numbers') and detail:
                print(f'STILL HELD {path.parent} v2: {n_why} | {claim["text"][:120]}')
    print(json.dumps(totals, indent=1))


if __name__ == '__main__':
    main()

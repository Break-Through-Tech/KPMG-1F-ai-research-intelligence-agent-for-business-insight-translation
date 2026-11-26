"""Unblinds a filled blind-score-sheet.json and compares it with Claude's scores.json (0 model calls).

    python -I scoring/compare_blind.py [path/to/filled-sheet.json]

Prints per-arm totals under the blind scores and every point where the two scorers disagree; the human decides those.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SET = HERE.parent
key = json.loads((HERE / 'blind-key.json').read_text(encoding='utf-8'))
assert hashlib.sha256((SET / 'BLIND-PACKET.md').read_bytes()).hexdigest() == key['packet_sha256'], 'packet changed'
sheet = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else SET / 'blind-score-sheet.json').read_text(encoding='utf-8'))
mine = json.loads((HERE / 'scores.json').read_text(encoding='utf-8'))['points']

totals, disagree, missing = {'B0': 0.0, 'B1': 0.0, 'M1': 0.0}, [], []
for qid, q in sheet['questions'].items():
    for pid, by_label in q['points'].items():
        for label, score in by_label.items():
            arm = key['labels'][qid][label]
            if score is None:
                missing.append(f'{pid} {label}')
                continue
            totals[arm] += score
            if score != mine[pid][arm][0]:
                disagree.append({'point': pid, 'arm': arm, 'blind': score, 'claude': mine[pid][arm][0]})
as_list = lambda v: [v] if isinstance(v, str) else list(v)  # noqa: E731  (scorers may write a single string)
label_of = lambda qid, x: key['labels'][qid].get((re.search(r'G\d\d-([ABC])', x) or [None, '?'])[1], '?')  # noqa: E731
flags = {qid: {k: [f"{x} ({label_of(qid, x)})" for x in as_list(q[k])]
               for k in ('misleading_claims', 'unsupported_recommendations') if q[k]}
         for qid, q in sheet['questions'].items() if q['misleading_claims'] or q['unsupported_recommendations']}
print(json.dumps({'blind_totals': totals, 'unscored': missing, 'disagreements': disagree, 'safety_flags': flags},
                 indent=1))

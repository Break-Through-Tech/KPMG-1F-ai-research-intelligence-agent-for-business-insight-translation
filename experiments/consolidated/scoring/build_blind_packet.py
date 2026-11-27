"""Anonymised A/B packet for the blind re-score of the consolidated validation (0 model calls).
Only published, scoreable content (findings, labelled interpretations, cited limitations, with exact quotes), rendered
identically for both arms. Leads, evidence notes, plans, withheld drafts, timings and packet sizes are excluded because
they can identify the arm. Writes ../BLIND-PACKET.md, ../blind-score-sheet.json and blind-key.json (do not share)."""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import env  # noqa: E402
from synthesis import norm  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
DATA = env.ROOT / 'data/processed'
ARMS = {'S': 'consolidated-v1-standard', 'D': 'consolidated-v1-deep'}
refs = json.loads((env.HERE / 'fresh-v2/references.json').read_text(encoding='utf-8'))
rules = json.loads((env.HERE / 'fresh-v2/rules.json').read_text(encoding='utf-8'))
rng = random.Random(20261125)
key, sheet = {}, {}
lines = ['# Consolidated validation: blind answer packet', '',
         'Two anonymised answers per question (A/B shuffled per question). Score each required point 1 / 0.5 / 0 using only '
         'the findings and cited limitations shown (interpretations never earn points). Record misleading claims, '
         'citation-grounding failures (a correct statement not entailed by its ATTACHED quotes) and interpretation quality '
         '(0-2). Every quote has been checked programmatically to be verbatim in its passage. Anchor passages: '
         '`KEY-REVIEW-PACKET.md`. Adjudication notes: `AMBIGUITIES.md`.', '']
for k in ('completeness', 'citation_entailment', 'numerical_correctness', 'interpretation_quality'):
    lines.append(f'- **{k}:** {rules[k]}')
lines.append('')
for ref in refs:
    qid = ref['id']
    arms = ['S', 'D']
    rng.shuffle(arms)
    key[qid] = dict(zip('AB', arms))
    sheet[qid] = {'points': {p['point_id']: {'A': None, 'B': None} for p in ref['required_points']},
                  'misleading_claims': [], 'citation_grounding_failures': [], 'interpretation_scores': {}, 'notes': ''}
    lines += ['---', '', f"## {qid} ({ref['type']})", '', f"**Question.** {ref['question']}", '', '**Required points:**', '']
    lines += [f"- **{p['point_id']}** {p['expected']}" for p in ref['required_points']] + ['']
    for label, arm in zip('AB', arms):
        s = json.loads((DATA / ARMS[arm] / qid / 'result.json').read_text(encoding='utf-8'))['summary']
        items = ([('F', c) for c in s['claims'] if c['kind'] == 'finding'] + [('I', c) for c in s['claims'] if c['kind'] != 'finding']
                 + [('L', l) for l in s['limitation_support']])
        lines += [f'### Answer {label}', '']
        counters = {'F': 0, 'I': 0, 'L': 0}
        for tag, item in items:
            lines.append(f"**{tag}{counters[tag]}** {item['text']}")
            counters[tag] += 1
            lines += [f"  - > `{x['chunk_id']}` {norm(x['quote'])}" for x in item['support']]
        lines.append('')
packet = '\n'.join(lines)
(OUT / 'BLIND-PACKET.md').write_text(packet, encoding='utf-8')
(OUT / 'blind-score-sheet.json').write_text(json.dumps({'scorer': '', 'date': '', 'questions': sheet}, indent=1), encoding='utf-8')
(HERE / 'blind-key.json').write_text(json.dumps({'warning': 'Do not give this file to the blind scorer.',
                                                 'packet_sha256': hashlib.sha256((OUT / 'BLIND-PACKET.md').read_bytes()).hexdigest(),
                                                 'labels': key}, indent=1), encoding='utf-8')
leaks = [w for w in ('Standard', 'Deep', 'planner', 'supplementary', 'withheld') if w in packet]
print('questions', len(refs), 'identifying words found:', leaks)

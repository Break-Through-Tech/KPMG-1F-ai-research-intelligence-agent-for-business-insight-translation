"""Writes KEY-REVIEW-PACKET-v3.md: every fresh-v3 point with the full text of each anchor passage (0 model calls)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import env  # noqa: E402

rows = {r['chunk_id']: r for r in env.bundle_rows()}
refs = json.loads((HERE / 'fresh-v3/references.json').read_text(encoding='utf-8'))
rules = json.loads((HERE / 'fresh-v3/rules.json').read_text(encoding='utf-8'))
out = ['# fresh-v3 answer key: focused independent review packet', '',
       'One review round. For each point check that: (1) the anchor passage(s) state the expected answer with no number, '
       'subject, metric, condition or qualifier changed; (2) the question asks for it; (3) the scoring rule is fair and '
       'every alternative anchor supports every component; (4) evidence-limit points are genuinely not established by the '
       'corpus. Flag only substantive factual or scoring errors; borderline-credit questions go to an adjudication note.',
       '', '**Rules:** ' + rules['completeness'], '', '**Misleading probes:** ' + rules['misleading_probes'], '']
for ref in refs:
    out += ['---', '', f"## {ref['id']} ({ref['type']})", '', f"**Question.** {ref['question']}", '']
    for point in ref['required_points']:
        out += [f"### {point['point_id']}" + (' (evidence limit)' if point['type'] == 'evidence_limit' else ''), '',
                f"**Expected:** {point['expected']}", '']
        for i, group in enumerate(point['anchors'], 1):
            label = 'Anchor' if len(point['anchors']) == 1 else f'Alternative {i}'
            out += [f"**{label}:** {' + '.join(group)}" + (' (read together)' if len(group) > 1 else ''), '']
            for cid in group:
                r = rows[cid]
                out += [f"> `{cid}` · {r['title']} · {r.get('section') or 'table'}", '>', f"> {' '.join(r['text'].split())}", '']
(HERE / 'KEY-REVIEW-PACKET-v3.md').write_text('\n'.join(out), encoding='utf-8')
print('points', sum(len(r['required_points']) for r in refs), 'chars', sum(len(x) for x in out))

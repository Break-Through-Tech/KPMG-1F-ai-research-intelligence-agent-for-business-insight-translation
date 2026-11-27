"""Writes KEY-REVIEW-PACKET.md: the 36 fresh-v2 points with the full text of every anchor passage, for ONE focused
independent review. Reads the sealed files (verifies the seal first); changes nothing sealed. 0 model calls.

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I build_key_review_packet.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I omits the script folder
import env  # noqa: E402
import run_consolidated as rc  # noqa: E402

rc.verify_seal()
rows = {r['chunk_id']: r for r in env.bundle_rows()}
refs = json.loads((rc.SET / 'references.json').read_text(encoding='utf-8'))
out = ['# fresh-v2 answer key: focused independent review packet', '',
       'One review round only. For each point check: (1) the anchor passage(s) state the expected answer with no number, '
       'subject, metric, condition or qualifier changed; (2) the question asks for it; (3) the scoring rule is fair. Flag only '
       'substantive factual or scoring errors. Interpretation and borderline-credit questions go to AMBIGUITIES.md for '
       'consistent adjudication after scoring, not to another review round.', '',
       '**Corrected in the pre-review source check (resealed once):** H03.4 re-anchored to c0003, which states the '
       'pre-/post-generation design; H08.2 keeps the source qualifier "mixed" for medical models; H05.4 made an explicit '
       'two-component point. **Then corrected after the one focused AI-assisted review (ChatGPT; resealed once):** H01.1 '
       'separates the 50,000+ benchmark conversations from the 2,345 evaluation samples; H06.1 alternative = c0008 + c0007; '
       'H06.2 anchors all nine type rows plus the total; every alternative must support every component. See '
       'KEY-REVIEW-RECORD.md.', '',
       'Scoring rules: `fresh-v2/rules.json`. Known ambiguities: `AMBIGUITIES.md`.', '']
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
(Path(__file__).resolve().parent / 'KEY-REVIEW-PACKET.md').write_text('\n'.join(out), encoding='utf-8')
print('points', sum(len(r['required_points']) for r in refs))

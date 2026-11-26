"""Read-only generation-completeness diagnosis over saved runs (0 model calls).

For every required point that a blind scorer gave < 1, classify where it was lost, using anchor chunks as the trace:
  evidence_missing     no complete anchor group in the evidence packet
  not_drafted          anchors present, but no draft claim/limitation cites any anchor chunk
  held_by_gate         a draft item citing an anchor was withheld (review or deterministic gate)
  published_partial    a published item cites an anchor, but the scorer still gave < 1 (incomplete/imprecise)
  published_elsewhere  no published item cites an anchor but the point got 0.5 (fact cited from another passage)
Also records whether the reviewer's coverage/gap text named the missing component.
Writes gen-diagnosis.json.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = Path('D:/KPMG-source-grounded/data/processed')
RUNS = [
    ('fresh-v3', 'S2', D / 'fresh-v3-S2-consolidated-v2-standard', HERE.parent / 'consolidated-v2/fresh-v3/references.json',
     HERE.parent / 'consolidated-v2/fresh3-blind-key.json', Path('D:/KPMG-blind-v3/blind-sheet-v3.scored.json')),
    ('fresh-v4', 'S2', D / 'fresh-v4-S2-consolidated-v2-standard', HERE / 'fresh-v4/references.json',
     HERE / 'fresh4-blind-key.json', Path('D:/KPMG-blind-v4/blind-sheet-v4.scored.json')),
    ('fresh-v4', 'S3', D / 'fresh-v4-S3-component-coverage', HERE / 'fresh-v4/references.json',
     HERE / 'fresh4-blind-key.json', Path('D:/KPMG-blind-v4/blind-sheet-v4.scored.json')),
    ('unseen', 'S2', D / 'unseen-r2-S2-frozen', HERE / 'unseen-r2/references.json',
     HERE / 'unseen-r2/blind-key.json', Path('D:/KPMG-blind-unseen/blind-sheet.scored.json')),
    ('unseen', 'R2', D / 'unseen-r2-S2R2', HERE / 'unseen-r2/references.json',
     HERE / 'unseen-r2/blind-key.json', Path('D:/KPMG-blind-unseen/blind-sheet.scored.json')),
]


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def main():
    out = []
    for setname, arm, folder, refp, keyp, sheetp in RUNS:
        refs = {r['id']: r for r in load(refp)}
        key = load(keyp)['labels']
        sheet = load(sheetp)['questions']
        for qid, qs in sheet.items():
            label = {a: l for l, a in key[qid].items()}[arm]
            stages = folder / qid / 'stages'
            if not (stages / 'synthesis.json').is_file():
                continue
            ev = {p['chunk_id'] for p in load(stages / 'evidence.json')['passages']}
            syn = load(stages / 'synthesis.json')['summary']
            rev = load(stages / 'review.json')['review']
            pub = load(folder / qid / 'result.json')['summary']
            drafted = [set(c.get('chunk_ids') or [s['chunk_id'] for s in c['support']]) for c in syn['claims'] + syn.get('limitation_support', [])]
            published = [set(c.get('chunk_ids') or [s['chunk_id'] for s in c['support']]) for c in pub['claims'] + pub.get('limitation_support', [])]
            held = pub.get('held_claims', []) + pub.get('dropped_limitations', [])
            for p in refs[qid]['required_points']:
                score = qs['points'][p['point_id']][label]
                if score is None or score >= 1:
                    continue
                anchors = {c for g in p['anchors'] for c in g}
                present = any(g and all(c in ev for c in g) for g in p['anchors'])
                in_draft = any(d & anchors for d in drafted)
                in_pub = any(x & anchors for x in published)
                if not present:
                    cause = 'evidence_missing'
                elif in_pub:
                    cause = 'published_partial'
                elif in_draft:
                    cause = 'held_by_gate'
                elif score > 0:
                    cause = 'published_elsewhere'
                else:
                    cause = 'not_drafted'
                out.append({'set': setname, 'arm': arm, 'q': qid, 'point': p['point_id'], 'score': score, 'cause': cause,
                            'coverage': rev.get('coverage'), 'gap': (rev.get('gap') or '')[:160],
                            'n_drafted': len(drafted), 'n_published': len(published), 'n_held': len(held),
                            'expected': p['expected'][:140]})
    (HERE / 'gen-diagnosis.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    from collections import defaultdict
    agg = defaultdict(lambda: defaultdict(float))
    for r in out:
        agg[(r['set'], r['arm'])][r['cause']] += 1 - r['score']
        agg[('ALL', '')][r['cause']] += 1 - r['score']
    for k, v in agg.items():
        print(k, {c: round(x, 1) for c, x in v.items()}, 'lost', round(sum(v.values()), 1))


if __name__ == '__main__':
    main()

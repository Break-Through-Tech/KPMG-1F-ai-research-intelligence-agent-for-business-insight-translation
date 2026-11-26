"""Builds the anonymised answer packet for Codex's blind re-score (0 model calls).

- Each question's three answers get labels A/B/C in a per-question random order (seeded, recorded in blind-key.json,
  which must NOT be given to the scorer).
- Only scoreable published content is included, rendered identically for every arm: claims, cited limitations and
  labelled interpretations, each with its exact quotes and cited passage IDs. Leads, verification notes, held/rejected
  drafts, packet sizes, timings and uncited limitation text are left out because they identify the engine and are not
  scored (rules.json: facts count in claims or cited limitations).
- Writes BLIND-PACKET.md and blind-score-sheet.json (to fill), and records the packet's sha256 in blind-key.json.
Unblind afterwards with compare_blind.py."""
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SET = HERE.parent
DATA = SET.parents[1] / 'data/processed'
ARMS = {'B0': 'combined-v1-baseline-top8', 'B1': 'combined-v1-baseline-skipfit6k',
        'M1': 'combined-v1-multiagent-skipfit6k-v2'}
SEED = 20261124
norm = lambda s: ' '.join((s or '').split())  # noqa: E731


def items(summary):
    """(kind, text, support) for every published, scoreable item, in one arm-neutral form."""
    out = []
    for c in summary.get('claims', []):
        out.append(('interpretation' if c.get('kind') == 'interpretation' else 'finding', c['text'], c.get('support', [])))
    for i in summary.get('interpretations', []) or []:
        out.append(('interpretation', i['text'], i.get('support', [])))
    for l in summary.get('limitation_support', []):
        out.append(('limitation', l['text'], l.get('support', [])))
    order = {'finding': 0, 'interpretation': 1, 'limitation': 2}
    return sorted(out, key=lambda x: order[x[0]])


def main():
    refs = json.loads((SET / 'references.json').read_text(encoding='utf-8'))
    rules = json.loads((SET / 'rules.json').read_text(encoding='utf-8'))
    rng = random.Random(SEED)
    key, sheet = {}, {}
    out = ['# combined-v1: blind answer packet for re-scoring', '',
           'Three anonymised answers per question (labels A/B/C are shuffled independently for every question). '
           'Score each required point **1** (accurately stated with an entailing citation), **0.5** (partly) or **0**, '
           'using only the claims, interpretations and cited limitations shown. Interpretations never earn points. '
           'Also record any **misleading claim** (wrong number, subject, metric, condition or qualifier; an inference '
           'presented as a finding; a fabricated answer to G09.3, G09.4 or G10.4) and any **unsupported recommendation** '
           'in an interpretation.', '',
           'Every quote below has been checked programmatically to appear verbatim in its cited passage. The full anchor '
           'passages for each point are in `REVIEW-PACKET.md`. Point-specific rules:', '']
    for k in ('evidence_absent_points', 'two_component_points', 'equivalent_figures', 'evidence_limit_points',
              'published_vs_inferred'):
        out.append(f'- **{k}:** {rules[k]}')
    out += ['', 'Fill in `blind-score-sheet.json`: a score per point per label, plus lists of misleading claims and '
            'unsupported recommendations (cite the label and item number, e.g. "G04-B F2").', '']
    for ref in refs:
        qid = ref['id']
        labels = ['A', 'B', 'C']
        arms = list(ARMS)
        rng.shuffle(arms)
        key[qid] = dict(zip(labels, arms))
        sheet[qid] = {'points': {p['point_id']: {l: None for l in labels} for p in ref['required_points']},
                      'misleading_claims': [], 'unsupported_recommendations': [], 'notes': ''}
        out += ['---', '', f"## {qid} ({ref['type']})", '', f"**Question.** {ref['question']}", '', '**Required points:**', '']
        out += [f"- **{p['point_id']}** {p['expected']}" for p in ref['required_points']]
        out.append('')
        for label, arm in zip(labels, arms):
            r = json.loads((DATA / ARMS[arm] / qid / 'result.json').read_text(encoding='utf-8'))
            published = items(r['envelope']['result']['summary'])
            out += [f'### Answer {label}', '']
            if not published:
                out += ['*No published content (the answer abstained).*', '']
            counters = {'finding': 0, 'interpretation': 0, 'limitation': 0}
            for kind, text, support in published:
                tag = {'finding': 'F', 'interpretation': 'I', 'limitation': 'L'}[kind] + str(counters[kind])
                counters[kind] += 1
                out.append(f'**{tag}** [{kind}] {text}')
                for s in support:
                    q, cid = (s.get('quote'), s.get('chunk_id')) if isinstance(s, dict) else (s, '?')
                    out.append(f'  - > `{cid}` {norm(q)}')
                out.append('')
    packet = '\n'.join(out)
    (SET / 'BLIND-PACKET.md').write_text(packet, encoding='utf-8')
    (SET / 'blind-score-sheet.json').write_text(json.dumps({'scorer': '', 'date': '', 'questions': sheet}, indent=1),
                                                encoding='utf-8')
    (HERE / 'blind-key.json').write_text(json.dumps({
        'warning': 'Do not give this file to the blind scorer.', 'seed': SEED,
        'packet_sha256': hashlib.sha256((SET / 'BLIND-PACKET.md').read_bytes()).hexdigest(), 'labels': key}, indent=1), encoding='utf-8')
    leaks = [w for w in ('Verification note', 'Partly answered', 'did not pass verification', 'retained answer',
                         'retained claims', 'B0', 'B1', 'M1', 'skip-fit', 'Multi-Agent', 'Baseline') if w in packet]
    print('questions', len(refs), 'chars', len(packet), 'identifying strings found:', leaks)


if __name__ == '__main__':
    main()

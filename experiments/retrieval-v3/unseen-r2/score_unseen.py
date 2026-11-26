"""Post-run tooling for the unseen S2 vs S2-R2 evaluation (0 engine calls).

    python -X utf8 score_unseen.py prepare   -> metrics.json, audit.json, D:\\KPMG-blind-unseen\\ (packet, sheet, brief),
                                               blind-key.json (kept here, never given to the scorer)
    python -X utf8 score_unseen.py criteria  -> unblinds D:\\KPMG-blind-unseen\\blind-sheet.scored.json, applies the frozen
                                               criteria, writes results.json
"""
import hashlib
import json
import random
import sqlite3
import statistics
import sys
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import s3_env  # noqa: E402
import publication  # noqa: E402
from s3_answer import asserts_paper_absence  # noqa: E402
from synthesis import norm  # noqa: E402
from run_unseen import ARMS, OUT, VAL  # noqa: E402

BLIND = Path('D:/KPMG-blind-unseen')
REFS = json.loads((HERE / 'references.json').read_text(encoding='utf-8'))
RULES = json.loads((HERE / 'rules.json').read_text(encoding='utf-8'))
MAX = RULES['max_score']


def rows():
    return {r['chunk_id']: r for r in (json.loads(l) for l in (VAL / 'parents.jsonl').read_text(encoding='utf-8').splitlines() if l.strip())}


def result(arm, qid):
    p = OUT / ARMS[arm] / qid / 'result.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None


def published(summary):
    return [('I' if c.get('kind') == 'interpretation' else 'F', c) for c in summary.get('claims', [])] + \
           [('L', l) for l in summary.get('limitation_support', [])]


def metrics():
    out = {}
    for arm, d in ARMS.items():
        with closing(sqlite3.connect(OUT / d / 'calls.sqlite3')) as db:
            calls = db.execute('SELECT question,status,seconds,usage FROM calls').fetchall()
        status = json.loads((OUT / d / 'status.json').read_text(encoding='utf-8'))
        per = {}
        for ref in REFS:
            q = ref['id']
            att_p = OUT / d / q / 'attempts.json'
            atts = json.loads(att_p.read_text(encoding='utf-8')) if att_p.is_file() else []
            res = result(arm, q)
            ids = {e['chunk_id'] for e in (res or {}).get('evidence', [])}
            cov = sum(any(g and all(c in ids for c in g) for g in p['anchors']) for p in ref['required_points'])
            t = atts[-1]['timings'] if atts else {}
            retr = sum(v for k, v in t.items() if k in ('base', 'evidence') and isinstance(v, (int, float)))
            gen = sum(v for k, v in t.items() if k in ('synthesis', 'review') and isinstance(v, (int, float)))
            u = [json.loads(x)[0] for qq, _s, _sec, x in calls if qq == q and x and x != 'null']
            per[q] = {'state': status.get(q, {}).get('state'), 'attempts': len(atts),
                      'total_s': round(sum(a['seconds'] for a in atts), 1), 'retrieval_s': round(retr, 1),
                      'generation_s': round(gen, 1), 'coverage': cov, 'points': len(ref['required_points']),
                      'input_tokens': sum(x['input_tokens'] for x in u), 'output_tokens': sum(x.get('output_tokens', 0) for x in u),
                      'route': ((res or {}).get('evidence_management') or {}).get('route') if False else None}
        totals = [v['total_s'] for v in per.values()]
        p90 = sorted(totals)[min(len(totals) - 1, round(0.9 * len(totals) + 0.5) - 1)]
        out[arm] = {'per_question': per, 'calls': len(calls), 'failed_calls': sum(s != 'ok' for _q, s, _a, _b in calls),
                    'complete': sum(v['state'] == 'complete' for v in per.values()),
                    'first_pass': sum(v['state'] == 'complete' and v['attempts'] == 1 for v in per.values()),
                    'median_total_s': statistics.median(totals), 'p90_total_s': p90,
                    'median_retrieval_s': statistics.median(v['retrieval_s'] for v in per.values()),
                    'median_generation_s': statistics.median(v['generation_s'] for v in per.values()),
                    'input_tokens': sum(v['input_tokens'] for v in per.values()),
                    'output_tokens': sum(v['output_tokens'] for v in per.values()),
                    'coverage': sum(v['coverage'] for v in per.values())}
    return out


def audit(rw):
    rep = {}
    for arm in ARMS:
        issues = []
        for ref in REFS:
            res = result(arm, ref['id'])
            if res is None:
                issues.append({'q': ref['id'], 'issue': 'no result'})
                continue
            s = res['summary']
            for tag, it in published(s):
                ids = it.get('chunk_ids') or [x['chunk_id'] for x in it['support']]
                for x in it['support']:
                    if norm(x['quote']) not in norm(rw[x['chunk_id']]['text']):
                        issues.append({'q': ref['id'], 'item': tag, 'issue': 'quote not exact', 'text': it['text'][:160]})
                miss = publication.number_recall({**it, 'chunk_ids': ids}, ' '.join(rw[c]['text'] for c in ids if c in rw))
                if miss:
                    issues.append({'q': ref['id'], 'item': tag, 'issue': f'value(s) not in own quotes: {miss}', 'text': it['text'][:200]})
            if asserts_paper_absence(s.get('answer_lead', '')):
                issues.append({'q': ref['id'], 'item': 'answer_lead', 'issue': 'uncited absence claim', 'text': s['answer_lead']})
        rep[arm] = issues
    return rep


def prepare():
    rw = rows()
    m = metrics()
    (HERE / 'metrics.json').write_text(json.dumps(m, indent=1), encoding='utf-8')
    a = audit(rw)
    (HERE / 'audit.json').write_text(json.dumps(a, indent=1, ensure_ascii=False), encoding='utf-8')
    rng = random.Random(20261126)
    key, sheet = {}, {}
    out = ['# Unseen evaluation: blind answer packet', '', 'Two anonymised answers per question (A/B shuffled). Score each '
           'required point 1/0.5/0 from findings (F) and cited limitations (L) only.', '', '**Rules:** ' + RULES['completeness'],
           '', '**Misleading probes:** ' + RULES['misleading_probes'], '', '**Safety:** ' + RULES['safety'], '']
    for ref in REFS:
        order = list(ARMS)
        rng.shuffle(order)
        key[ref['id']] = dict(zip('AB', order))
        sheet[ref['id']] = {'points': {p['point_id']: {'A': None, 'B': None} for p in ref['required_points']},
                            'citation_grounding_failures': [], 'misleading_claims': [], 'numerical_errors': [], 'notes': ''}
        out += ['---', '', f"## {ref['id']}", '', ref['question'], ''] + [f"- **{p['point_id']}** {p['expected']}" for p in ref['required_points']] + ['']
        for label, arm in zip('AB', order):
            res = result(arm, ref['id'])
            out += [f'### Answer {label}', '']
            c = {'F': 0, 'I': 0, 'L': 0}
            for tag, it in published(res['summary'] if res else {}):
                out.append(f"**{tag}{c[tag]}** {it['text']}")
                c[tag] += 1
                out += [f"  - > `{x['chunk_id']}` {norm(x['quote'])}" for x in it['support']]
            out.append('')
    BLIND.mkdir(exist_ok=True)
    (BLIND / 'BLIND-PACKET.md').write_text('\n'.join(out), encoding='utf-8')
    (BLIND / 'blind-sheet.json').write_text(json.dumps({'scorer': '', 'questions': sheet}, indent=1), encoding='utf-8')
    (BLIND / 'SCORER-BRIEF.md').write_text(
        '# Blind scoring brief\n\nWork ONLY in this folder; do not try to identify the systems. Read BLIND-PACKET.md '
        '(8 questions, two anonymised answers A and B each; the header gives the rules, misleading probes and safety '
        'rules). For every required point score A and B: 1 (fully, accurately published with an entailing citation), '
        '0.5 (partly) or 0. Only findings (F) and cited limitations (L) count. Check every item against ITS OWN quotes '
        'and record failures as {"answer":"A","item":"F3","reason":"..."} in citation_grounding_failures, '
        'misleading_claims or numerical_errors. Save blind-sheet.scored.json (scorer = your model name); change no other '
        'file. Reply with per-question totals for A and B, every 0.5/0 with a reason, and every flag with a reason.\n',
        encoding='utf-8')
    (HERE / 'blind-key.json').write_text(json.dumps({'labels': key, 'packet_sha256': hashlib.sha256(
        (BLIND / 'BLIND-PACKET.md').read_bytes()).hexdigest()}, indent=1), encoding='utf-8')
    print(json.dumps({a: {k: v for k, v in x.items() if k != 'per_question'} for a, x in m.items()}, indent=1))
    print('audit issues', {k: len(v) for k, v in a.items()})


def criteria():
    key = json.loads((HERE / 'blind-key.json').read_text(encoding='utf-8'))['labels']
    sheet = json.loads((BLIND / 'blind-sheet.scored.json').read_text(encoding='utf-8'))
    m = json.loads((HERE / 'metrics.json').read_text(encoding='utf-8'))
    a = json.loads((HERE / 'audit.json').read_text(encoding='utf-8'))
    pts = {arm: 0.0 for arm in ARMS}
    full = {arm: 0 for arm in ARMS}
    perq, flags = {}, {arm: [] for arm in ARMS}
    for q, v in sheet['questions'].items():
        per = {arm: [] for arm in ARMS}
        for _p, b in v['points'].items():
            for label, s in b.items():
                per[key[q][label]].append(s)
        perq[q] = {arm: sum(x) for arm, x in per.items()}
        for arm in ARMS:
            pts[arm] += perq[q][arm]
            full[arm] += all(x == 1 for x in per[arm])
        for kind in ('citation_grounding_failures', 'misleading_claims', 'numerical_errors'):
            for f in v[kind]:
                flags[key[q][f['answer']]].append({'q': q, 'kind': kind, **f})
    s2, r2 = m['S2'], m['R2']
    crit = {
        '1 R2 >= S2 + 2 points': pts['R2'] >= pts['S2'] + 2,
        '2 zero new safety flags (blind + audit)': len(flags['R2']) + len(a['R2']) <= len(flags['S2']) + len(a['S2'])
                                                     and not flags['R2'] and not a['R2'],
        '3 median <= 1.25x S2 and <= 120 s': r2['median_total_s'] <= 1.25 * s2['median_total_s'] and r2['median_total_s'] <= 120,
        '4 p90 <= 180 s': r2['p90_total_s'] <= 180,
        '5 input tokens <= 1.10x S2': r2['input_tokens'] <= 1.10 * s2['input_tokens'],
        '6 no silent failures (all 8 recorded per arm)': all(len(x['per_question']) == 8 for x in (s2, r2)),
    }
    res = {'points': pts, 'percent': {k: round(100 * v / MAX, 1) for k, v in pts.items()}, 'max': MAX,
           'fully_answered': full, 'per_question': perq, 'blind_flags': flags, 'audit_issues': {k: len(v) for k, v in a.items()},
           'criteria': crit, 'R2_passes': all(crit.values()),
           'reference_stricter_1.10x_latency': r2['median_total_s'] <= 1.10 * s2['median_total_s'],
           'latency_ratio_median': round(r2['median_total_s'] / s2['median_total_s'], 3),
           'input_token_ratio': round(r2['input_tokens'] / s2['input_tokens'], 3),
           'output_token_ratio': round(r2['output_tokens'] / s2['output_tokens'], 3)}
    (HERE / 'results.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    {'prepare': prepare, 'criteria': criteria}[sys.argv[1]]()

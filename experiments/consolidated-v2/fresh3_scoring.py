"""Post-run tooling for the fresh-v3 validation (0 model calls). Not sealed: it reads results, it does not produce them.

    python -I fresh3_scoring.py audit        programmatic pass: exact quotes + number recall (digits and spelled counts)
                                             for every published item of every arm -> fresh3-audit.json
    python -I fresh3_scoring.py blind        BLIND-PACKET-v3.md + blind-sheet-v3.json (A-D shuffled per question)
                                             + fresh3-blind-key.json (never give it to the scorer)
    python -I fresh3_scoring.py criteria SHEET   unblind a filled sheet and evaluate the frozen acceptance criteria
                                             (needs adjudicated safety counts in fresh3-adjudication.json)
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
sys.path.insert(0, str(HERE))
import env  # noqa: E402
import fresh3_arms as arms  # noqa: E402
import publication  # noqa: E402
from synthesis import norm  # noqa: E402

ROWS = None
P_TOTAL = 38


def rows():
    global ROWS
    ROWS = ROWS or {r['chunk_id']: r for r in env.bundle_rows()}
    return ROWS


def questions():
    return [q['id'] for q in json.loads((arms.SET / 'questions.json').read_text(encoding='utf-8'))]


def summary_of(arm, qid):
    result = json.loads((arms.OUT / arms.ARM_DIRS[arm] / qid / 'result.json').read_text(encoding='utf-8'))
    if arm == 'B0':
        envelope = result.get('envelope') or {}
        res = envelope.get('result') or {}
        return res.get('summary') or {'claims': [], 'limitation_support': []}, result
    return result['summary'], result


def published(summary):
    items = [('F' if c.get('kind') != 'interpretation' else 'I', c) for c in summary.get('claims', [])]
    return items + [('L', l) for l in summary.get('limitation_support', [])]


def audit():
    report = {}
    for arm in arms.ARM_DIRS:
        issues = []
        for qid in questions():
            try:
                summary, _ = summary_of(arm, qid)
            except FileNotFoundError:
                issues.append({'q': qid, 'issue': 'no result'})
                continue
            for tag, item in published(summary):
                item = {**item, 'chunk_ids': item.get('chunk_ids') or [s['chunk_id'] for s in item['support']]}
                for s in item['support']:
                    if norm(s['quote']) not in norm(rows()[s['chunk_id']]['text']):
                        issues.append({'q': qid, 'item': tag, 'issue': 'quote not exact', 'text': item['text'][:160]})
                cited = ' '.join(rows()[c]['text'] for c in item['chunk_ids'] if c in rows())
                missing = publication.number_recall(item, cited)
                if missing:
                    issues.append({'q': qid, 'item': tag, 'issue': f'value(s) not in own quotes: {missing}',
                                   'text': item['text'][:200]})
        report[arm] = issues
    (HERE / 'fresh3-audit.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({a: len(v) for a, v in report.items()}))


def blind():
    refs = json.loads((arms.SET / 'references.json').read_text(encoding='utf-8'))
    rules = json.loads((arms.SET / 'rules.json').read_text(encoding='utf-8'))
    rng = random.Random(20261125)
    key, sheet = {}, {}
    out = ['# fresh-v3 blind answer packet', '', 'Four anonymised answers per question (A-D shuffled per question). Score '
           'each required point 1/0.5/0 from published findings and cited limitations only. Record citation-grounding '
           'failures (a correct statement not entailed by ITS OWN quotes), misleading/fabricated claims, numerical errors '
           'and interpretation quality (0-2).', '', '**Rules:** ' + rules['completeness'],
           '', '**Misleading probes:** ' + rules['misleading_probes'], '']
    for ref in refs:
        qid = ref['id']
        order = list(arms.ARM_DIRS)
        rng.shuffle(order)
        key[qid] = dict(zip('ABCD', order))
        sheet[qid] = {'points': {p['point_id']: {l: None for l in 'ABCD'} for p in ref['required_points']},
                      'citation_grounding_failures': [], 'misleading_claims': [], 'numerical_errors': [],
                      'interpretation_scores': {}, 'notes': ''}
        out += ['---', '', f"## {qid}", '', ref['question'], '']
        out += [f"- **{p['point_id']}** {p['expected']}" for p in ref['required_points']] + ['']
        for label, arm in zip('ABCD', order):
            try:
                summary, _ = summary_of(arm, qid)
            except FileNotFoundError:
                summary = {'claims': [], 'limitation_support': []}
            out += [f'### Answer {label}', '']
            counters = {'F': 0, 'I': 0, 'L': 0}
            for tag, item in published(summary):
                out.append(f"**{tag}{counters[tag]}** {item['text']}")
                counters[tag] += 1
                out += [f"  - > `{s['chunk_id']}` {norm(s['quote'])}" for s in item['support']]
            out.append('')
    packet = '\n'.join(out)
    (HERE / 'BLIND-PACKET-v3.md').write_text(packet, encoding='utf-8')
    (HERE / 'blind-sheet-v3.json').write_text(json.dumps({'scorer': '', 'questions': sheet}, indent=1), encoding='utf-8')
    (HERE / 'fresh3-blind-key.json').write_text(json.dumps({
        'warning': 'Do not give this file to the blind scorer.', 'labels': key,
        'packet_sha256': hashlib.sha256((HERE / 'BLIND-PACKET-v3.md').read_bytes()).hexdigest()}, indent=1), encoding='utf-8')
    print('blind packet written')


def mechanics(arm):
    folder = arms.OUT / arms.ARM_DIRS[arm]
    with closing(sqlite3.connect(folder / 'calls.sqlite3')) as db:
        usage = [json.loads(u or 'null') for (u,) in db.execute('SELECT usage FROM calls')]
    tokens = sum(x.get('input_tokens', 0) for u in usage if u for x in u)
    totals, first_pass, complete, errors = [], 0, 0, 0
    status = json.loads((folder / 'status.json').read_text(encoding='utf-8'))
    for qid in questions():
        if arm == 'B0':
            seconds = [json.loads((folder / qid / 'result.json').read_text())['seconds']]
            seconds += [json.loads((p / 'result.json').read_text())['seconds'] for p in folder.glob(f'{qid}.attempt-*')
                        if (p / 'result.json').is_file()]
            attempts = len(seconds)
        else:
            log = json.loads((folder / qid / 'attempts.json').read_text())
            seconds, attempts = [a['seconds'] for a in log], len(log)
        totals.append(sum(seconds))
        ok = status.get(qid, {}).get('state') == 'complete'
        complete += ok
        first_pass += ok and attempts == 1
        errors += not ok
    p90 = sorted(totals)[min(len(totals) - 1, round(0.9 * len(totals) + 0.5) - 1)]
    return {'input_tokens': tokens, 'median_total_s': statistics.median(totals), 'p90_total_s': p90,
            'complete': complete, 'first_pass': first_pass, 'execution_errors': errors}


def criteria(sheet_path):
    key = json.loads((HERE / 'fresh3-blind-key.json').read_text())['labels']
    sheet = json.loads(Path(sheet_path).read_text(encoding='utf-8'))['questions']
    adjudication = json.loads((HERE / 'fresh3-adjudication.json').read_text(encoding='utf-8'))
    points, full = {a: 0.0 for a in arms.ARM_DIRS}, {a: 0 for a in arms.ARM_DIRS}
    for qid, q in sheet.items():
        per = {a: [] for a in arms.ARM_DIRS}
        for pid, by_label in q['points'].items():
            for label, score in by_label.items():
                per[key[qid][label]].append(score)
        for arm, scores in per.items():
            points[arm] += sum(scores)
            full[arm] += all(s == 1 for s in scores)
    pct = {a: 100 * v / P_TOTAL for a, v in points.items()}
    m = {a: mechanics(a) for a in arms.ARM_DIRS}
    safe = {a: adjudication[a]['citation_grounding_failures'] == 0 and adjudication[a]['misleading_or_fabricated'] == 0
            and adjudication[a]['quote_errors'] == 0 and adjudication[a]['numerical_errors'] == 0 for a in arms.ARM_DIRS}
    s2 = {'completeness >= 80%': pct['S2'] >= 80, '>= 4/8 full': full['S2'] >= 4,
          '>= B0 + 10 pp': pct['S2'] >= pct['B0'] + 10, 'no regression vs S1': points['S2'] >= points['S1'],
          'safety': safe['S2'], 'all 8 complete and >= 7/8 first pass': m['S2']['complete'] == 8 and m['S2']['first_pass'] >= 7,
          'median <= 120 s': m['S2']['median_total_s'] <= 120, 'p90 <= 180 s': m['S2']['p90_total_s'] <= 180,
          'input tokens <= 0.8 x S1': m['S2']['input_tokens'] <= 0.8 * m['S1']['input_tokens']}
    d2 = {'safety': safe['D2'], 'completeness >= 80%': pct['D2'] >= 80, '>= S2 + 10 pp': pct['D2'] >= pct['S2'] + 10,
          'full >= S2': full['D2'] >= full['S2'], 'median <= 2 x S2': m['D2']['median_total_s'] <= 2 * m['S2']['median_total_s'],
          'p90 <= 300 s': m['D2']['p90_total_s'] <= 300, '<= 1 execution error': m['D2']['execution_errors'] <= 1}
    result = {'points': points, 'percent': pct, 'full': full, 'mechanics': m, 'S2_criteria': s2,
              'S2_qualifies': all(s2.values()), 'D2_criteria': d2, 'D2_qualifies': all(d2.values())}
    (HERE / 'fresh3-results.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    {'audit': audit, 'blind': blind}.get(sys.argv[1], lambda: criteria(sys.argv[2]))()

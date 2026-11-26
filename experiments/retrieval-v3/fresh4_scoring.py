"""Post-run tooling for the fresh-v4 validation (0 model calls). Reads results; produces none.

    python -X utf8 fresh4_scoring.py audit          programmatic pass: exact quotes, number recall (digits and spelled
                                                    counts) for every published item, plus the S3 absence guard on every
                                                    UNCITED text (answer lead, coverage notes) -> fresh4-audit.json
    python -X utf8 fresh4_scoring.py blind          BLIND-PACKET-v4.md + blind-sheet-v4.json (A/B shuffled per question)
                                                    + fresh4-blind-key.json (never give it to the scorer)
    python -X utf8 fresh4_scoring.py criteria SHEET unblind a filled sheet and evaluate the frozen criteria
                                                    (needs adjudicated safety counts in fresh4-adjudication.json)
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
import s3_env  # noqa: E402
import publication  # noqa: E402
import run_fresh4 as rf  # noqa: E402
from s3_answer import asserts_paper_absence  # noqa: E402
from synthesis import norm  # noqa: E402

SET = rf.SET
ARMS = list(rf.ARM_DIRS)
_ROWS = None


def rows():
    global _ROWS
    if _ROWS is None:
        _ROWS = {}
        for line in (rf.BUNDLE / 'parents.jsonl').read_text(encoding='utf-8').splitlines():
            if line.strip():
                r = json.loads(line)
                _ROWS[r['chunk_id']] = r
    return _ROWS


def questions():
    return [q['id'] for q in json.loads((SET / 'questions.json').read_text(encoding='utf-8'))]


def summary_of(arm, qid):
    return json.loads((rf.OUT / rf.ARM_DIRS[arm] / qid / 'result.json').read_text(encoding='utf-8'))['summary']


def published(summary):
    items = [('F' if c.get('kind') != 'interpretation' else 'I', c) for c in summary.get('claims', [])]
    return items + [('L', l) for l in summary.get('limitation_support', [])]


def audit():
    report = {}
    for arm in ARMS:
        issues = []
        for qid in questions():
            try:
                summary = summary_of(arm, qid)
            except FileNotFoundError:
                issues.append({'q': qid, 'issue': 'no result'})
                continue
            for tag, item in published(summary):
                ids = item.get('chunk_ids') or [s['chunk_id'] for s in item['support']]
                for s in item['support']:
                    if norm(s['quote']) not in norm(rows()[s['chunk_id']]['text']):
                        issues.append({'q': qid, 'item': tag, 'issue': 'quote not exact', 'text': item['text'][:160]})
                cited = ' '.join(rows()[c]['text'] for c in ids if c in rows())
                missing = publication.number_recall({**item, 'chunk_ids': ids}, cited)
                if missing:
                    issues.append({'q': qid, 'item': tag, 'issue': f'value(s) not in own quotes: {missing}',
                                   'text': item['text'][:200]})
            uncited = [('answer_lead', summary.get('answer_lead', ''))]
            uncited += [('coverage_note', c.get('note', '')) for c in summary.get('component_coverage', [])]
            for where, text in uncited:
                if text and asserts_paper_absence(text.split(': ', 1)[0] if where == 'coverage_note' else text):
                    issues.append({'q': qid, 'item': where, 'issue': 'uncited absence claim about a paper', 'text': text})
        report[arm] = issues
    (HERE / 'fresh4-audit.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({a: len(v) for a, v in report.items()}))


def blind():
    refs = json.loads((SET / 'references.json').read_text(encoding='utf-8'))
    rules = json.loads((SET / 'rules.json').read_text(encoding='utf-8'))
    rng = random.Random(20261126)
    key, sheet = {}, {}
    out = ['# fresh-v4 blind answer packet', '', 'Two anonymised answers per question (A/B shuffled per question). Score each '
           'required point 1/0.5/0 from published findings (F) and cited limitations (L) only. Record citation-grounding '
           'failures (a correct statement not entailed by ITS OWN quotes), misleading/fabricated claims, numerical errors '
           'and interpretation quality (0-2).', '', '**Rules:** ' + rules['completeness'], '',
           '**Misleading probes:** ' + rules['misleading_probes'], '', '**Safety:** ' + rules['safety'], '']
    for ref in refs:
        qid = ref['id']
        order = list(ARMS)
        rng.shuffle(order)
        key[qid] = dict(zip('AB', order))
        sheet[qid] = {'points': {p['point_id']: {l: None for l in 'AB'} for p in ref['required_points']},
                      'citation_grounding_failures': [], 'misleading_claims': [], 'numerical_errors': [],
                      'interpretation_scores': {}, 'notes': ''}
        out += ['---', '', f'## {qid}', '', ref['question'], '']
        out += [f"- **{p['point_id']}** {p['expected']}" for p in ref['required_points']] + ['']
        for label, arm in zip('AB', order):
            try:
                summary = summary_of(arm, qid)
            except FileNotFoundError:
                summary = {'claims': [], 'limitation_support': []}
            out += [f'### Answer {label}', '']
            counters = {'F': 0, 'I': 0, 'L': 0}
            for tag, item in published(summary):
                out.append(f"**{tag}{counters[tag]}** {item['text']}")
                counters[tag] += 1
                out += [f"  - > `{s['chunk_id']}` {norm(s['quote'])}" for s in item['support']]
            out.append('')
    (HERE / 'BLIND-PACKET-v4.md').write_text('\n'.join(out), encoding='utf-8')
    (HERE / 'blind-sheet-v4.json').write_text(json.dumps({'scorer': '', 'questions': sheet}, indent=1), encoding='utf-8')
    (HERE / 'fresh4-blind-key.json').write_text(json.dumps({
        'warning': 'Do not give this file to the blind scorer.', 'labels': key,
        'packet_sha256': hashlib.sha256((HERE / 'BLIND-PACKET-v4.md').read_bytes()).hexdigest()}, indent=1),
        encoding='utf-8')
    print('blind packet written')


def mechanics(arm):
    folder = rf.OUT / rf.ARM_DIRS[arm]
    with closing(sqlite3.connect(folder / 'calls.sqlite3')) as db:
        usage = [json.loads(u or 'null') for (u,) in db.execute('SELECT usage FROM calls')]
    tokens = sum(x.get('input_tokens', 0) for u in usage if u for x in u)
    status = json.loads((folder / 'status.json').read_text(encoding='utf-8'))
    totals, first_pass, complete = [], 0, 0
    for qid in questions():
        log = json.loads((folder / qid / 'attempts.json').read_text(encoding='utf-8'))
        totals.append(sum(a['seconds'] for a in log))
        ok = status.get(qid, {}).get('state') == 'complete'
        complete += ok
        first_pass += ok and len(log) == 1
    p90 = sorted(totals)[min(len(totals) - 1, round(0.9 * len(totals) + 0.5) - 1)]
    return {'input_tokens': tokens, 'calls': len(usage), 'median_total_s': statistics.median(totals),
            'p90_total_s': p90, 'complete': complete, 'first_pass': first_pass}


def criteria(sheet_path):
    key = json.loads((HERE / 'fresh4-blind-key.json').read_text(encoding='utf-8'))['labels']
    sheet = json.loads(Path(sheet_path).read_text(encoding='utf-8'))['questions']
    adjudication = json.loads((HERE / 'fresh4-adjudication.json').read_text(encoding='utf-8'))
    total = json.loads((SET / 'rules.json').read_text(encoding='utf-8'))['points']
    points, full = {a: 0.0 for a in ARMS}, {a: 0 for a in ARMS}
    for qid, q in sheet.items():
        per = {a: [] for a in ARMS}
        for _pid, by_label in q['points'].items():
            for label, score in by_label.items():
                per[key[qid][label]].append(score)
        for arm, scores in per.items():
            points[arm] += sum(scores)
            full[arm] += all(s == 1 for s in scores)
    pct = {a: 100 * v / total for a, v in points.items()}
    m = {a: mechanics(a) for a in ARMS}
    safe = {a: all(adjudication[a][k] == 0 for k in ('citation_grounding_failures', 'misleading_or_fabricated',
                                                    'quote_errors', 'numerical_errors', 'uncited_absence_claims'))
            for a in ARMS}
    s3 = {'completeness >= 80%': pct['S3'] >= 80, 'safety': safe['S3'],
          'S3 >= S2 + 2 points': points['S3'] >= points['S2'] + 2,
          'execution 10/10 and >= 9/10 first pass': m['S3']['complete'] == 10 and m['S3']['first_pass'] >= 9,
          'median <= 120 s': m['S3']['median_total_s'] <= 120, 'p90 <= 180 s': m['S3']['p90_total_s'] <= 180,
          'input tokens <= 1.15 x S2': m['S3']['input_tokens'] <= 1.15 * m['S2']['input_tokens']}
    result = {'points': points, 'percent': pct, 'fully_answered_reported_only': full, 'mechanics': m, 'safety': safe,
              'S3_criteria': s3, 'S3_qualifies': all(s3.values())}
    (HERE / 'fresh4-results.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    {'audit': audit, 'blind': blind}.get(sys.argv[1], lambda: criteria(sys.argv[2]))()

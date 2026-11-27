"""Offline scoring aid for the consolidated live validation (0 model calls).

Writes answers/Hxx.md (both arms: published findings, interpretations, limitations with quotes; withheld drafts with
reasons; evidence notes; anchors in each packet; supplementary passages) and mechanics.json (calls, latency incl. failed
attempts, estimated vs actual tokens, programmatic audits: exact quotes and per-item number recall)."""
import json
import sqlite3
import statistics
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import env  # noqa: E402
import publication  # noqa: E402
from synthesis import norm  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = env.ROOT / 'data/processed'
ARMS = {'S': 'consolidated-v1-standard', 'D': 'consolidated-v1-deep'}
rows = {r['chunk_id']: r for r in env.bundle_rows()}
refs = {r['id']: r for r in json.loads((env.HERE / 'fresh-v2/references.json').read_text(encoding='utf-8'))}


def audit(item):
    quotes_ok = all(norm(s['quote']) in norm(rows[s['chunk_id']]['text']) for s in item['support'])
    cited = ' '.join(rows[c]['text'] for c in item['chunk_ids'] if c in rows)
    return quotes_ok, publication.number_recall(item, cited)


def main():
    (HERE / 'answers').mkdir(exist_ok=True)
    mech = {}
    for arm, d in ARMS.items():
        with closing(sqlite3.connect(DATA / d / 'calls.sqlite3')) as db:
            ledger = db.execute('SELECT question, status, seconds, usage FROM calls').fetchall()
        total, success, est, actual_in, actual_out, items, bad_q, bad_n = {}, {}, {}, 0, 0, 0, [], []
        for qid in refs:
            folder = DATA / d / qid
            attempts = json.loads((folder / 'attempts.json').read_text())
            total[qid] = sum(a['seconds'] for a in attempts)
            success[qid] = attempts[-1]['seconds']
            calls = json.loads((folder / 'calls.json').read_text())
            est[qid] = sum(r['request_tokens'] for c in calls for r in c['requests_estimated'])
            result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
            for item in result['summary']['claims'] + result['summary']['limitation_support']:
                items += 1
                ok, missing = audit(item)
                if not ok:
                    bad_q.append((qid, item['text'][:80]))
                if missing:
                    bad_n.append((qid, missing))
        for _q, _s, _sec, usage in ledger:
            for u in json.loads(usage or 'null') or []:
                actual_in += u.get('input_tokens', 0)
                actual_out += u.get('output_tokens', 0)
        p90 = lambda v: sorted(v)[int(round(0.9 * (len(v) - 1)))]  # noqa: E731
        mech[arm] = {'calls': len(ledger), 'failed_calls': sum(1 for x in ledger if x[1] != 'ok'),
                     'median_total_s': round(statistics.median(total.values()), 1), 'p90_total_s': round(p90(list(total.values())), 1),
                     'median_success_s': round(statistics.median(success.values()), 1),
                     'p90_success_s': round(p90(list(success.values())), 1),
                     'total_s': {q: round(v) for q, v in total.items()},
                     'estimated_request_tokens': sum(est.values()), 'actual_input_tokens': actual_in,
                     'actual_output_tokens': actual_out, 'published_items': items,
                     'quote_not_exact': bad_q, 'number_not_in_quotes': bad_n}
    for qid, ref in refs.items():
        out = [f"# {qid} ({ref['type']})", '', ref['question'], '']
        out += [f"- **{p['point_id']}** {p['expected']}" for p in ref['required_points']] + ['']
        for arm, d in ARMS.items():
            r = json.loads((DATA / d / qid / 'result.json').read_text(encoding='utf-8'))
            s, em = r['summary'], r['evidence_management']
            ids = {p['chunk_id'] for p in r['evidence']}
            supp = set(em.get('supplementary_ids') or [])
            flags = []
            for p in ref['required_points']:
                full = [g for g in p['anchors'] if set(g) <= ids]
                tag = 'Y' if full else ('part' if any(set(g) & ids for g in p['anchors']) else 'N')
                if full and supp and all(set(g) & supp for g in full):
                    tag += '(supp)'
                flags.append(f"{p['point_id']}={tag}")
            out += [f'## {arm}', '', f"*{len(ids)} passages ({len(supp)} supplementary); anchors: {', '.join(flags)}*", '']
            if r.get('plan') and r['plan'].get('searches'):
                out.append('*Planned searches:* ' + ' | '.join(x['query'] for x in r['plan']['searches']))
            if s.get('answer_lead'):
                out.append(f"**Lead:** {s['answer_lead']}")
            for n in s.get('evidence_notes', []):
                out.append(f'*Evidence note:* {n}')
            for i, c in enumerate(s['claims']):
                tag = ('I' if c['kind'] == 'interpretation' else 'F') + str(i)
                out.append(f"**{tag}** {c['text']}" + (' *(reduced by review)*' if c.get('reduced_from') else ''))
                out += [f"  - > `{x['chunk_id']}` {norm(x['quote'])}" for x in c['support']]
            for i, l in enumerate(s['limitation_support']):
                out.append(f"**L{i}** {l['text']}")
                out += [f"  - > `{x['chunk_id']}` {norm(x['quote'])}" for x in l['support']]
            for h in s.get('held_claims', []):
                out.append(f"**WITHHELD** [{'; '.join(h['reasons'])[:220]}] {h['text']}")
            out.append('')
        (HERE / 'answers' / f'{qid}.md').write_text('\n'.join(out), encoding='utf-8')
    (HERE / 'mechanics.json').write_text(json.dumps(mech, indent=1), encoding='utf-8')
    print(json.dumps({a: {k: v for k, v in m.items() if k != 'total_s'} for a, m in mech.items()}, indent=1))


if __name__ == '__main__':
    main()

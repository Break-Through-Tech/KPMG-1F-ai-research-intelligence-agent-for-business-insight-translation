"""Reproduce S2 / B1 / R2 evidence coverage THROUGH THE ENGINE WRAPPER (S2R2Research.gather_evidence) on every set,
with cached B2 rankings (0 model calls). Also records per-question retrieval operations, cached search seconds,
evidence tokens and the points R2 displaces. Writes r2-offline.json."""
import json
import statistics
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s3_env  # noqa: E402
import evidence as ev  # noqa: E402
from engine import CheckpointStore  # noqa: E402
from components import components  # noqa: E402
from eval_paper_balance import load_rows, DEMO, VAL  # noqa: E402
from rank_cache import SETS  # noqa: E402
from s2_r2 import S2R2Research  # noqa: E402


def main():
    from transformers import AutoTokenizer
    from prepare import ENCODER
    tok = AutoTokenizer.from_pretrained(str(ENCODER))
    memo = {}

    def count(p):
        if p['chunk_id'] not in memo:
            memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
        return memo[p['chunk_id']]
    groups = [(n, HERE.parent / n / 'references.json', HERE / 'cache/rankings.json', DEMO) for n in SETS]
    groups.append(('fresh-v4', HERE / 'fresh-v4/references.json', HERE / 'cache/fresh-v4-rankings.json', VAL))
    out, totals = [], {}
    for name, ref_path, cache_path, bundle in groups:
        rows = load_rows(bundle)
        tables = ev.TableIndex(rows.values())
        cache = json.loads(cache_path.read_text(encoding='utf-8'))
        ops = []

        def ranked(q, n):
            ops.append(q)
            return [rows[c] for c in cache[q]['order'][:n]]
        engines = {s: S2R2Research(retrieval_strategy=s, ranked=ranked, count=count, tables=tables, generate=None,
                                   v2=None, gate=None, rows=rows, parallel_search=False) for s in ('s2', 'b1', 'r2')}
        t = totals.setdefault(name, {'points': 0, 's2': 0, 'b1': 0, 'r2': 0})
        for ref in json.loads(ref_path.read_text(encoding='utf-8')):
            q = ref['question']
            rec = {'set': name, 'q': ref['id'], 'points': len(ref['required_points'])}
            for s, e in engines.items():
                ops.clear()
                pk, _, _ = e.gather_evidence(q, CheckpointStore(tempfile.mkdtemp()), {})
                ids = {p['chunk_id'] for p in pk['passages']}
                cov = {p['point_id'] for p in ref['required_points'] if any(g and all(c in ids for c in g) for g in p['anchors'])}
                rec[s] = sorted(cov)
                rec[f'{s}_tokens'] = pk['tokens']
                rec[f'{s}_passages'] = [p['chunk_id'] for p in pk['passages']]
                searches = list(dict.fromkeys(ops))
                rec[f'{s}_searches'] = len(searches)
                secs = sorted((cache[x]['seconds'] for x in searches[1:]), reverse=True)
                rec[f'{s}_search_s'] = round(cache[q]['seconds'] + sum(secs[i] for i in range(0, len(secs), 3)), 2)
                rec[f'{s}_route'] = pk.get('r2', {}).get('route') if s == 'r2' else s
                t[s] += len(cov)
            t['points'] += rec['points']
            rec['r2_lost'] = sorted(set(rec['s2']) - set(rec['r2']))
            rec['r2_gained'] = sorted(set(rec['r2']) - set(rec['s2']))
            out.append(rec)
    summary = {k: sum(v[k] for v in totals.values()) for k in ('points', 's2', 'b1', 'r2')}
    tok = {s: statistics.mean(o[f'{s}_tokens'] for o in out) for s in ('s2', 'b1', 'r2')}
    add = [o['r2_search_s'] - o['s2_search_s'] for o in out]
    srch = {s: statistics.mean(o[f'{s}_searches'] for o in out) for s in ('s2', 'b1', 'r2')}
    routes = {}
    for o in out:
        routes[o['r2_route']] = routes.get(o['r2_route'], 0) + 1
    res = {'by_set': totals, 'summary': summary, 'mean_evidence_tokens': tok, 'mean_searches': srch,
           'added_search_s_median': statistics.median(add), 'added_search_s_max': max(add), 'routes': routes,
           'lost': [(o['set'], o['q'], o['r2_lost']) for o in out if o['r2_lost']], 'questions': out}
    (HERE / 'r2-offline.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in res.items() if k != 'questions'}, indent=1))


if __name__ == '__main__':
    main()

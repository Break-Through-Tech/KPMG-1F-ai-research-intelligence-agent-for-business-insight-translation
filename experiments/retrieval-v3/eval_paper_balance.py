"""Offline comparison: frozen S2 vs B1 vs B2 on every question set (0 model calls). Writes paper-balance.json."""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s3_env  # noqa: E402
import evidence as ev  # noqa: E402
import paper_balance as pb  # noqa: E402
from components import components  # noqa: E402
from rank_cache import SETS  # noqa: E402

EXP = HERE.parent
DEMO = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
VAL = s3_env.ROOT / 'data/processed/validation-bundles/fresh-v4-110/parents.jsonl'


def load_rows(path):
    return {r['chunk_id']: r for r in (json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip())}


def main():
    from transformers import AutoTokenizer
    from prepare import ENCODER
    tok = AutoTokenizer.from_pretrained(str(ENCODER))
    memo = {}

    def count(p):
        if p['chunk_id'] not in memo:
            memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
        return memo[p['chunk_id']]
    groups = [(n, EXP / n / 'references.json', HERE / 'cache/rankings.json', DEMO) for n in SETS]
    groups.append(('fresh-v4', HERE / 'fresh-v4/references.json', HERE / 'cache/fresh-v4-rankings.json', VAL))
    out, agg = [], {}
    for name, ref_path, cache_path, bundle in groups:
        rows = load_rows(bundle)
        titles = {}
        for r in rows.values():
            titles.setdefault(r['arxiv_id'], r.get('title', ''))
        tables = ev.TableIndex(rows.values())
        cache = json.loads(cache_path.read_text(encoding='utf-8'))
        for ref in json.loads(ref_path.read_text(encoding='utf-8')):
            q = ref['question']
            order = cache[q]['order']
            comp_orders = [cache[c]['order'] for c in components(q) if c in cache]
            res = {}
            for mode in ('S2', 'B1', 'B2'):
                pk, papers = pb.packet(q, order, rows, count, tables, titles, mode=mode, component_orders=comp_orders)
                ids = {p['chunk_id'] for p in pk['passages']}
                cov = {p['point_id'] for p in ref['required_points'] if any(g and all(c in ids for c in g) for g in p['anchors'])}
                res[mode] = {'covered': cov, 'tokens': pk['tokens'], 'papers': papers,
                             'serialized': ev.serialized_estimate(pk['passages'])}
            ref_papers = sorted({c.split('_')[0] for p in ref['required_points'] for g in p['anchors'] for c in g})
            kind = ref.get('type') or ref.get('category') or ''
            out.append({'set': name, 'q': ref['id'], 'type': kind, 'reference_papers': len(ref_papers),
                        'resolved': res['B1']['papers'], 'points': len(ref['required_points']),
                        **{m: len(res[m]['covered']) for m in res},
                        'B1_gained': sorted(res['B1']['covered'] - res['S2']['covered']),
                        'B1_lost': sorted(res['S2']['covered'] - res['B1']['covered']),
                        'B2_gained': sorted(res['B2']['covered'] - res['S2']['covered']),
                        'B2_lost': sorted(res['S2']['covered'] - res['B2']['covered']),
                        'tokens': {m: res[m]['tokens'] for m in res},
                        'serialized_ratio_B2': round(res['B2']['serialized'] / res['S2']['serialized'], 3),
                        'extra_search_s_B2': (sum(cache[c]['seconds'] for c in components(q)) / ev.SEARCH_WORKERS
                                              if len(res['B1']['papers']) >= 2 else 0.0)})
    for o in out:
        a = agg.setdefault(o['set'], {'points': 0, 'S2': 0, 'B1': 0, 'B2': 0, 'triggered': 0, 'questions': 0})
        a['questions'] += 1
        a['points'] += o['points']
        a['triggered'] += len(o['resolved']) >= 2
        for m in ('S2', 'B1', 'B2'):
            a[m] += o[m]
    (HERE / 'paper-balance.json').write_text(json.dumps({'by_set': agg, 'questions': out}, indent=1), encoding='utf-8')
    print(json.dumps(agg, indent=1))
    for o in out:
        if len(o['resolved']) >= 2 or o['reference_papers'] >= 2:
            print(o['set'][-10:], o['q'], o['type'], 'refpapers', o['reference_papers'], 'resolved', len(o['resolved']),
                  'S2/B1/B2', o['S2'], o['B1'], o['B2'], '/', o['points'], 'B1-', o['B1_lost'], 'B2-', o['B2_lost'])


if __name__ == '__main__':
    main()

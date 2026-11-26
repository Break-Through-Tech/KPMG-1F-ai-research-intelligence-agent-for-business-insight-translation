"""Read-only probe of S2-R2's lost evidence points on the unseen set, plus retrieval timing (0 LLM calls).

For each lost point: anchor ranks in the original query and in each component query, whether it is in R2's saved
evidence, the route R2 took (B1/fusion), and whether it was inside the 30-candidate window but cut by the 6k budget.
Timing: original + component searches measured sequentially and with 3 threads (as the engine runs them).
Writes r2-loss-probe.json.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s3_env  # noqa: E402
import evidence as ev  # noqa: E402
import evidence_budget  # noqa: E402
import paper_balance as pb  # noqa: E402
from components import components  # noqa: E402
from prepare import ENCODER, RERANKER  # noqa: E402

VAL = s3_env.ROOT / 'data/processed/validation-bundles/fresh-v4-110'
R2 = s3_env.ROOT / 'data/processed/unseen-r2-S2R2'
LOST = ['U1.2', 'U1.3', 'U1.5', 'U2.2', 'U2.5', 'U3.1', 'U3.2', 'U6.1', 'U6.3']


def main():
    _r, _id, ranked, count, _p, _v = evidence_budget.open_ranked(VAL, encoder_path=ENCODER, reranker_path=RERANKER,
                                                                 table_comparisons=False)
    rows = {r['chunk_id']: r for r in (json.loads(l) for l in (VAL / 'parents.jsonl').read_text(encoding='utf-8').splitlines() if l.strip())}
    titles = {}
    for r in rows.values():
        titles.setdefault(r['arxiv_id'], r.get('title', ''))
    refs = {r['id']: r for r in json.loads((HERE / 'unseen-r2/references.json').read_text(encoding='utf-8'))}
    ranked('warm up', 5)
    out, timing = [], []
    for qid in sorted({p[:2] for p in LOST}):
        q = refs[qid]['question']
        comps = components(q)
        t0 = time.perf_counter(); orig = [p['chunk_id'] for p in ranked(q, 300)]; t_orig = time.perf_counter() - t0
        seq = []
        corders = []
        for c in comps:
            t0 = time.perf_counter(); corders.append([p['chunk_id'] for p in ranked(c, 300)]); seq.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda c: ranked(c, 300), comps))
        t_par = time.perf_counter() - t0
        papers = pb.requested_papers(q, orig, titles)
        timing.append({'q': qid, 'original_s': round(t_orig, 2), 'components': len(comps), 'component_seq_s': [round(x, 2) for x in seq],
                       'components_parallel3_s': round(t_par, 2), 'sum_seq_s': round(sum(seq), 2),
                       'route': 'b1' if len(papers) >= 2 else 'fusion'})
        saved = [p['chunk_id'] for p in json.loads((R2 / qid / 'stages/evidence.json').read_text(encoding='utf-8'))['passages']]
        for p in refs[qid]['required_points']:
            if p['point_id'] not in LOST:
                continue
            for g in p['anchors']:
                for c in g:
                    rk = orig.index(c) + 1 if c in orig else None
                    comp_rk = [co.index(c) + 1 if c in co else None for co in corders]
                    own_paper = [x for x in orig[:ev.CANDIDATE_DEPTH] if x.startswith(c.split('_')[0] + '_')]
                    out.append({'point': p['point_id'], 'anchor': c, 'tokens': count(rows[c]),
                                'rank_original': rk, 'rank_within_own_paper': own_paper.index(c) + 1 if c in own_paper else None,
                                'best_component_rank': min([x for x in comp_rk if x] or [None]) if any(comp_rk) else None,
                                'in_R2_packet': c in saved, 'route': timing[-1]['route'],
                                'r2_packet_tokens': sum(count(rows[x]) for x in saved if x in rows)})
    res = {'points': out, 'timing': timing}
    (HERE / 'r2-loss-probe.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    for o in out:
        print(o)
    for t in timing:
        print(t)


if __name__ == '__main__':
    main()

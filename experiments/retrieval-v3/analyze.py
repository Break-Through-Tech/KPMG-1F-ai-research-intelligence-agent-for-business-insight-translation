"""Offline coverage analysis from cached B2 rankings (0 model calls; only the MiniLM tokenizer is loaded for counts).

Metric: a required point is covered when a complete anchor group (any alternative) is in the evidence packet.
This is a proxy (equivalent wording elsewhere can still support a point), used only to compare policies on the
same rankings, the same bundle and the same strict budget.

Policies (fixed before measurement):
  P0      frozen V2 Standard packet (evidence.standard_packet: 6k skip-fit over top-30 + C2 conclusions)
  P0-8k   same with an 8k budget (does more budget alone help?)
  PS      earlier decomposition (3-part splitter, round-robin merge) re-run at the V2 6k budget, for comparison
  PC      component coverage at 6k: original top-4 protected, then each component's top-2 passages
          (paper-scoped to the papers of the original top-30) round-robin, then the rest of the original top-30
  PC3     PC with top-3 per component (sensitivity)
  PC-u    PC without paper scoping (does scoping matter?)
Every policy goes through the frozen select_grouped (whole table groups or an incomplete-table note) and the
frozen C2 conclusion coverage, so only candidate order differs.
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EXP / 'consolidated-v2'))
import env  # noqa: E402
import evidence as ev  # noqa: E402
sys.path.insert(0, str(EXP / 'measure/fresh-diagnostic-v1'))
from prepare import ENCODER  # noqa: E402
sys.path.insert(0, str(EXP / 'baseline-decomposition'))
from question_parts import question_parts  # noqa: E402
from components import components  # noqa: E402
from rank_cache import CACHE, SETS  # noqa: E402

PROTECT_TOP = 4


def load():
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(ENCODER))
    rows = {r['chunk_id']: r for r in env.bundle_rows()}
    memo = {}

    def count(p):
        if p['chunk_id'] not in memo:
            memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
        return memo[p['chunk_id']]
    return rows, count, ev.TableIndex(rows.values()), json.loads(CACHE.read_text(encoding='utf-8'))


def paper(cid):
    return cid.split('_')[0]


def build(question, policy, rows, count, tables, cache):
    order = cache[question]['order']
    ranked = lambda q, n: [rows[c] for c in cache[q]['order'][:n]]  # noqa: E731
    if policy in ('P0', 'P0-8k'):
        return ev.standard_packet(question, ranked, count, tables, budget=8000 if policy == 'P0-8k' else 6000), 0
    if policy == 'PS':
        lists = [order[:ev.WINDOW]] + [cache[p]['order'][:8] for p in question_parts(question)]
        merged = []
        for i in range(max(map(len, lists))):
            merged += [lst[i] for lst in lists if i < len(lst) and lst[i] not in merged]
        searches = len(lists) - 1
    elif policy.split('@')[0] in ('FA', 'FM'):
        budget_override = int(policy.split('@')[1]) if '@' in policy else None
        policy = policy.split('@')[0]
        # Rank fusion over the original ranking and every component ranking (paper-scoped), B2's 1/(20+rank) form.
        # FA: original + mean over components (B2's facet rule, generalised to all components).
        # FM: original + best component (a passage that answers one component is not diluted by the others).
        papers = {paper(c) for c in order[:ev.WINDOW]}
        comps = components(question)
        r0 = {c: i + 1 for i, c in enumerate(order[:ev.CANDIDATE_DEPTH])}
        rc = [{c: i + 1 for i, c in enumerate([x for x in cache[q]['order'] if paper(x) in papers][:ev.WINDOW])}
              for q in comps]
        pool = set(r0) | {c for r in rc for c in r}
        def score(c):
            s = 1 / (20 + r0.get(c, 10 ** 6))
            if rc:
                parts = [1 / (20 + r.get(c, 10 ** 6)) for r in rc]
                s += max(parts) if policy == 'FM' else sum(parts) / len(parts)
            return s
        fused = sorted(pool, key=lambda c: (-score(c), c))
        merged = list(order[:PROTECT_TOP]) + [c for c in fused if c not in order[:PROTECT_TOP]][:ev.WINDOW - PROTECT_TOP]
        searches = len(comps)
    else:
        depth = 3 if policy == 'PC3' else 2
        papers = {paper(c) for c in order[:ev.WINDOW]}
        comps = components(question)
        picks = []
        for c in comps:
            lst = [x for x in cache[c]['order'] if policy == 'PC-u' or paper(x) in papers]
            picks.append(lst[:depth])
        merged = list(order[:PROTECT_TOP])
        for i in range(depth):
            merged += [lst[i] for lst in picks if i < len(lst) and lst[i] not in merged]
        merged += [c for c in order[:ev.WINDOW] if c not in merged]
        searches = len(comps)
    budget = locals().get('budget_override') or 6000
    passages, _notes, used = ev.select_grouped([rows[c] for c in merged], budget, count, tables)
    conclusions, extra, _ = ev.conclusion_coverage([rows[c] for c in order[:ev.CANDIDATE_DEPTH]], passages, count)
    return {'passages': passages + conclusions, 'tokens': used + extra}, searches


def search_seconds(question, policy, cache):
    """Retrieval wall time: original search + extra searches run 3 at a time (V2's SEARCH_WORKERS)."""
    base = cache[question]['seconds']
    extra = {'PS': question_parts(question)}.get(policy, components(question) if policy[:2] in ('PC', 'FA', 'FM') else [])
    secs = sorted((cache[q]['seconds'] for q in extra), reverse=True)
    return base + sum(secs[i] for i in range(0, len(secs), ev.SEARCH_WORKERS))


def main():
    rows, count, tables, cache = load()
    policies = ['P0', 'P0-8k', 'PS', 'PC', 'PC3', 'PC-u', 'FA', 'FM', 'FA@7000', 'FA@8000']
    per_point, summary = [], defaultdict(lambda: defaultdict(float))
    for name in SETS:
        for ref in json.loads((EXP / name / 'references.json').read_text(encoding='utf-8')):
            q = ref['question']
            ref_papers = {paper(c) for p in ref['required_points'] for g in p['anchors'] for c in g}
            packets = {}
            for pol in policies:
                pk, searches = build(q, pol, rows, count, tables, cache)
                ids = {p['chunk_id'] for p in pk['passages']}
                packets[pol] = ids
                s = summary[pol]
                s['questions'] += 1
                s['tokens'] += pk['tokens']
                s['passages'] += len(ids)
                s['off_paper'] += sum(paper(c) not in ref_papers for c in ids)
                s['searches'] += searches
                s['retrieval_s'] += search_seconds(q, pol, cache)
            order = cache[q]['order']
            rank = {c: i + 1 for i, c in enumerate(order)}
            for p in ref['required_points']:
                groups = [g for g in p['anchors'] if g]
                if not groups:  # evidence-limit point: nothing to retrieve
                    summary['_']['no_anchor_points'] += 1
                    continue
                cov = {pol: any(all(c in packets[pol] for c in g) for g in groups) for pol in policies}
                best = min(max(rank.get(c, 10 ** 6) for c in g) for g in groups)
                comp_best = min((min(max({c: i + 1 for i, c in enumerate(cache[cq]['order'])}.get(c, 10 ** 6)
                                         for c in g) for g in groups) for cq in components(q)), default=10 ** 6)
                missing_from_bundle = all(any(c not in rows for c in g) for g in groups)
                cause = ('covered' if cov['P0'] else 'not_in_bundle' if missing_from_bundle else
                         'budget' if best <= ev.WINDOW else 'window' if best <= ev.CANDIDATE_DEPTH else
                         'pool' if best < 10 ** 6 else 'not_in_pool')
                per_point.append({'set': name, 'q': ref['id'], 'point': p['point_id'], 'cause_P0': cause,
                                  'rank_original': best if best < 10 ** 6 else None,
                                  'rank_best_component': comp_best if comp_best < 10 ** 6 else None,
                                  'table': any('_table_' in c for g in groups for c in g), **cov})
                for pol in policies:
                    summary[pol]['points'] += 1
                    summary[pol]['covered'] += cov[pol]
                    summary[pol]['lost_vs_P0'] += cov['P0'] and not cov[pol]
                    summary[pol][f'covered:{name}'] += cov[pol]
                    summary[pol][f'points:{name}'] += 1
    out = {'summary': {k: dict(v) for k, v in summary.items()}, 'points': per_point}
    (HERE / 'coverage.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print('points without anchors (evidence-limit):', int(summary.pop('_', {}).get('no_anchor_points', 0)))
    for pol, s in summary.items():
        n = s['questions']
        print(f"{pol:6} covered {int(s['covered'])}/{int(s['points'])} lost_vs_P0 {int(s['lost_vs_P0'])} "
              f"tokens/q {s['tokens'] / n:.0f} passages/q {s['passages'] / n:.1f} off-paper {s['off_paper'] / s['passages']:.0%} "
              f"searches/q {s['searches'] / n:.1f} retrieval s/q {s['retrieval_s'] / n:.1f}  | "
              + ' '.join(f"{k.split(':')[1].split('/')[-1]} {int(s[k])}/{int(s['points:' + k.split(':')[1]])}"
                         for k in s if k.startswith('covered:')))
    causes = defaultdict(int)
    for r in per_point:
        causes[r['cause_P0']] += 1
    print('P0 causes:', dict(causes))


if __name__ == '__main__':
    main()

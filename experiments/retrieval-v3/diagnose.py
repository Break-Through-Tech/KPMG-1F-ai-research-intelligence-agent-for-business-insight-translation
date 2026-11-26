"""Offline retrieval diagnosis for the V2 Standard packet (0 model calls; CPU retrieval only).

For every required point of the existing (development) question sets, find where its anchor evidence sits:
  covered        - a complete anchor group is in the V2 Standard packet (recomputed offline)
  budget         - every anchor of some group ranks within the top-30 window, but skip-fit left one out
  depth          - best group's worst anchor ranks 31-120 (inside B2's candidate depth, outside the window)
  deep_miss      - ranks 121-300
  query_miss     - not in the top 300 for the original question
  not_in_bundle  - an anchor chunk is absent from the bundle
For each point it also records the best rank achieved by any single clause of the question (unbounded clause split)
and by the existing deterministic splitter (baseline-decomposition/question_parts.py, max 3 parts).

Writes diagnosis.json. Frozen engines are imported read-only; nothing is modified.
"""
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(EXP / 'consolidated-v2'))
import env  # noqa: E402  (puts the frozen v2 + shared modules on the path)
import evidence as ev  # noqa: E402
import evidence_budget  # noqa: E402
sys.path.insert(0, str(EXP / 'measure/fresh-diagnostic-v1'))
from prepare import BUNDLE, ENCODER, PIN, RERANKER  # noqa: E402
sys.path.insert(0, str(EXP / 'baseline-decomposition'))
from question_parts import question_parts  # noqa: E402

SETS = ['heldout-v1', 'completion-eval-v1', 'combined-v1', 'consolidated/fresh-v2', 'consolidated-v2/fresh-v3']
DEPTH = 300


def clauses(question):
    """Unbounded clause split: sentence and ', what/how/which/and what' boundaries; the business preamble is kept
    as shared context for every clause."""
    sentences = [s.strip() for s in re.split(r'(?<=[.?])\s+', question) if s.strip()]
    context = ' '.join(s for s in sentences if not s.endswith('?'))
    asks = ' '.join(s for s in sentences if s.endswith('?')) or question
    parts = [p.strip(' ,?') for p in re.split(r',\s*(?:and\s+)?(?=(?:what|how|which|when|where|why|does|do|is|are)\b)'
                                              r'|\band\s+(?=(?:what|how|which|when|where|why)\b)', asks) if p.strip(' ,?')]
    return [f'{context} {p}?'.strip() for p in parts] if len(parts) > 1 else []


def rank_map(ranked, query):
    return {p['chunk_id']: i + 1 for i, p in enumerate(ranked(query, DEPTH))}


def group_rank(group, ranks):
    return max((ranks.get(c, 10 ** 6) for c in group), default=10 ** 6)


def main():
    _retrieve, identity, ranked, count, _path, _prov = evidence_budget.open_ranked(
        BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
    assert identity()['indexed_records_sha256'] == PIN, 'unexpected B2 index'
    rows = {r['chunk_id']: r for r in env.bundle_rows()}
    tables = ev.TableIndex(rows.values())
    out = []
    started = time.perf_counter()
    for name in SETS:
        refs = json.loads((EXP / name / 'references.json').read_text(encoding='utf-8'))
        for ref in refs:
            q = ref['question']
            base = rank_map(ranked, q)
            packet = {p['chunk_id'] for p in ev.standard_packet(q, ranked, count, tables)['passages']}
            parts = {'splitter': question_parts(q), 'clauses': clauses(q)}
            part_ranks = {k: [rank_map(ranked, p) for p in v] for k, v in parts.items()}
            for point in ref['required_points']:
                groups = point['anchors']
                missing = [c for g in groups for c in g if c not in rows]
                best = min(group_rank(g, base) for g in groups)
                if any(all(c in packet for c in g) for g in groups):
                    cause = 'covered'
                elif missing and all(any(c not in rows for c in g) for g in groups):
                    cause = 'not_in_bundle'
                elif best <= ev.WINDOW:
                    cause = 'budget'
                elif best <= ev.CANDIDATE_DEPTH:
                    cause = 'depth'
                elif best <= DEPTH:
                    cause = 'deep_miss'
                else:
                    cause = 'query_miss'
                anchor_ids = [c for g in groups for c in g]
                out.append({
                    'set': name, 'q': ref['id'], 'point': point['point_id'], 'cause': cause,
                    'best_group_rank': best if best < 10 ** 6 else None,
                    'best_part_rank': {k: (min((min(group_rank(g, r) for g in groups) for r in rs), default=None))
                                       for k, rs in part_ranks.items()},
                    'n_parts': {k: len(v) for k, v in parts.items()},
                    'anchor_kinds': sorted({'table' if '_table_' in c else 'text' for c in anchor_ids}),
                    'anchor_tokens': {c: count(rows[c]) for c in anchor_ids if c in rows},
                    'packet_size': len(packet),
                })
            print(name, ref['id'], f'{time.perf_counter() - started:.0f}s', flush=True)
    (HERE / 'diagnosis.json').write_text(json.dumps(out, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()

"""Offline check on the real pinned B2 (local models; no generation): ranked() agrees with the public retrieve(), and
the packets reproduce Codex's development coverage on C01-C15 (top-8 22, top-16 31, 6k skip-fit 34 of 41).

    python -I check_real_retrieval.py      (Baseline route: table comparisons off)
"""
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'agentic-handoff')]
import codex_paired  # noqa: E402,F401  (paths)
import evidence_budget as eb  # noqa: E402
from prepare import BUNDLE, ENCODER, PIN, RERANKER  # noqa: E402

retrieve, identity, ranked, count, *_ = eb.open_ranked(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                                       table_comparisons=False)
assert identity()['indexed_records_sha256'] == PIN
refs = json.loads((HERE.parent / 'completion-eval-v1/references.json').read_text(encoding='utf-8'))
policies = {'top8': eb.fixed(8), 'top16': eb.fixed(16), 'skipfit6k': eb.skip_fit(6000, 30)}
points = {k: 0 for k in policies}
sizes = {k: [] for k in policies}
started = time.perf_counter()
for i, ref in enumerate(refs):
    order = ranked(ref['question'], 30)
    if i < 3:
        public = [p['chunk_id'] for p in retrieve(ref['question'], 20)]
        assert [p['chunk_id'] for p in order[:20]] == public, ref['id']
    for name, policy in policies.items():
        packet = eb.select(order, policy, count)
        ids = {p['chunk_id'] for p in packet}
        got = sum(any(set(g) <= ids for g in point['anchors']) for point in ref['required_points'])
        points[name] += got
        sizes[name].append((len(packet), sum(count(p) for p in packet)))
    print(ref['id'], {n: len(eb.select(order, p, count)) for n, p in policies.items()}, flush=True)
print(json.dumps({'window_equals_public_top20': 'checked on 3 questions',
                  'exact_points_of_41': points,
                  'mean_passages': {k: round(sum(n for n, _ in v) / len(v), 2) for k, v in sizes.items()},
                  'max_tokens': {k: max(t for _, t in v) for k, v in sizes.items()},
                  'seconds': round(time.perf_counter() - started, 1)}, indent=1))

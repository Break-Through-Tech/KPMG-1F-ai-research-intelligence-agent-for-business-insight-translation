"""Build a cache of B2 rankings for every development question and its components (0 model calls; CPU retrieval).

Queries cached per question: the original question, its question components (components.py), and the existing
3-part splitter parts (baseline-decomposition, for comparison with the earlier decomposition experiment).
Each entry: full B2 candidate order (chunk ids, up to DEPTH) and the seconds it took. Resumable: existing entries
are kept. Output: cache/rankings.json.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EXP / 'consolidated-v2'))
import env  # noqa: E402,F401  (frozen v2 + shared modules on the path)
import evidence_budget  # noqa: E402
sys.path.insert(0, str(EXP / 'measure/fresh-diagnostic-v1'))
from prepare import BUNDLE, ENCODER, PIN, RERANKER  # noqa: E402
sys.path.insert(0, str(EXP / 'baseline-decomposition'))
from question_parts import question_parts  # noqa: E402
from components import components  # noqa: E402

SETS = ['heldout-v1', 'completion-eval-v1', 'combined-v1', 'consolidated/fresh-v2', 'consolidated-v2/fresh-v3']
DEPTH = 300
CACHE = HERE / 'cache' / 'rankings.json'


def queries():
    for name in SETS:
        for ref in json.loads((EXP / name / 'references.json').read_text(encoding='utf-8')):
            q = ref['question']
            yield q
            yield from components(q)
            yield from question_parts(q)


def main():
    CACHE.parent.mkdir(exist_ok=True)
    cache = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.is_file() else {}
    _retrieve, identity, ranked, _count, _path, _prov = evidence_budget.open_ranked(
        BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
    assert identity()['indexed_records_sha256'] == PIN, 'unexpected B2 index'
    todo = [q for q in dict.fromkeys(queries()) if q not in cache]
    print(f'{len(cache)} cached, {len(todo)} to rank', flush=True)
    for i, q in enumerate(todo, 1):
        started = time.perf_counter()
        order = [p['chunk_id'] for p in ranked(q, DEPTH)]
        cache[q] = {'order': order, 'seconds': round(time.perf_counter() - started, 2)}
        if i % 10 == 0 or i == len(todo):
            CACHE.write_text(json.dumps(cache), encoding='utf-8')
            print(f'{i}/{len(todo)} last {cache[q]["seconds"]}s', flush=True)


if __name__ == '__main__':
    main()

"""fresh-v4 evidence-coverage headroom for frozen S3 vs frozen S2 (0 model calls; CPU retrieval on the validation bundle).

    python -X utf8 fresh_coverage.py rank     cache B2 rankings for the fresh questions and their components
    python -X utf8 fresh_coverage.py score    score anchored coverage, budgets, request size and retrieval time

Runs only after the S3 code freeze (verified). The packets are built by the frozen code: evidence.standard_packet (S2)
and s3_evidence.s3_packet (S3). Nothing is tuned on the result.
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s3_env  # noqa: E402
import seal_s3  # noqa: E402

HERE = s3_env.HERE
SET = HERE / 'fresh-v4'
CACHE = HERE / 'cache' / 'fresh-v4-rankings.json'
BUNDLE = s3_env.ROOT / 'data/processed/validation-bundles/fresh-v4-110'


def queries():
    from components import components
    for q in json.loads((SET / 'questions.json').read_text(encoding='utf-8')):
        yield q['question']
        yield from components(q['question'])


def open_bundle():
    import evidence_budget
    from prepare import ENCODER, RERANKER
    _r, identity, ranked, count, _p, _v = evidence_budget.open_ranked(BUNDLE, encoder_path=ENCODER,
                                                                      reranker_path=RERANKER, table_comparisons=False)
    pin = json.loads((SET / 'bundle-record.json').read_text(encoding='utf-8'))['manifest']['artifact_sha256']['parents.jsonl']
    assert identity()['indexed_records_sha256'] == pin, 'unexpected validation bundle'
    return ranked, count


def rank():
    print(seal_s3.verify_code())
    ranked, _count = open_bundle()
    cache = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.is_file() else {}
    for q in dict.fromkeys(queries()):
        if q in cache:
            continue
        started = time.perf_counter()
        cache[q] = {'order': [p['chunk_id'] for p in ranked(q, 300)], 'seconds': round(time.perf_counter() - started, 2)}
        CACHE.write_text(json.dumps(cache), encoding='utf-8')
        print(len(cache), cache[q]['seconds'], flush=True)


def score():
    print(seal_s3.verify_code())
    import evidence as ev
    import s3_evidence as se
    from components import components
    from transformers import AutoTokenizer
    from prepare import ENCODER
    tok = AutoTokenizer.from_pretrained(str(ENCODER))
    rows = {}
    for line in (BUNDLE / 'parents.jsonl').read_text(encoding='utf-8').splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r['chunk_id']] = r
    memo = {}

    def count(p):
        if p['chunk_id'] not in memo:
            memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
        return memo[p['chunk_id']]
    cache = json.loads(CACHE.read_text(encoding='utf-8'))
    ranked = lambda q, n: [rows[c] for c in cache[q]['order'][:n]]  # noqa: E731
    tables = ev.TableIndex(rows.values())
    out, tot = [], {'S2': 0, 'S3': 0, 'anchored': 0, 'points': 0}
    for ref in json.loads((SET / 'references.json').read_text(encoding='utf-8')):
        q = ref['question']
        p2 = ev.standard_packet(q, ranked, count, tables)
        p3 = se.s3_packet(q, ranked, count, tables, parallel=False)
        ids2, ids3 = {p['chunk_id'] for p in p2['passages']}, {p['chunk_id'] for p in p3['passages']}
        per = []
        for p in ref['required_points']:
            groups = [g for g in p['anchors'] if g]
            c2 = any(all(c in ids2 for c in g) for g in groups)
            c3 = any(all(c in ids3 for c in g) for g in groups)
            per.append({'point': p['point_id'], 'S2': c2, 'S3': c3})
            tot['points'] += 1
            tot['anchored'] += bool(groups)
            tot['S2'] += c2
            tot['S3'] += c3
        secs = sorted((cache[c]['seconds'] for c in components(q)), reverse=True)
        out.append({'q': ref['id'], 'S2': sum(x['S2'] for x in per), 'S3': sum(x['S3'] for x in per), 'points': len(per),
                    'per_point': per, 's3_base_tokens': p3['base_tokens'], 's2_base_tokens': p2['base_tokens'],
                    'serialized_ratio': round(ev.serialized_estimate(p3['passages']) / ev.serialized_estimate(p2['passages']), 3),
                    'max_serialized_est': ev.serialized_estimate(p3['passages']),
                    'retrieval_s_S2': cache[q]['seconds'],
                    'retrieval_s_S3': cache[q]['seconds'] + sum(secs[i] for i in range(0, len(secs), ev.SEARCH_WORKERS))})
    summary = {**tot,
               'S2_coverage_pct': round(100 * tot['S2'] / tot['points'], 1),
               'S3_coverage_pct': round(100 * tot['S3'] / tot['points'], 1),
               'serialized_ratio_mean': round(statistics.mean(o['serialized_ratio'] for o in out), 3),
               'max_s3_base_tokens': max(o['s3_base_tokens'] for o in out),
               'max_serialized_est': max(o['max_serialized_est'] for o in out),
               'added_retrieval_s_median': round(statistics.median(o['retrieval_s_S3'] - o['retrieval_s_S2'] for o in out), 2)}
    (SET / 'coverage-fresh-v4.json').write_text(json.dumps({'summary': summary, 'questions': out}, indent=1),
                                                encoding='utf-8')
    print(json.dumps(summary, indent=1))
    for o in out:
        print(o['q'], 'S2', o['S2'], 'S3', o['S3'], '/', o['points'])


if __name__ == '__main__':
    {'rank': rank, 'score': score}[sys.argv[1]]()

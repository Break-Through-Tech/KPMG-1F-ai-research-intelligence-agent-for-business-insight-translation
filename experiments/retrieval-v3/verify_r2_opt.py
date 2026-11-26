"""Verify optimized S2-R2 against validated S2-R2 (0 LLM calls). Writes r2-opt-verification.json.

  identity  every development set + fresh-v4 + unseen (cached rankings): full evidence packet JSON byte-identical
            (passages, order, ids, tokens, notes, routes) and the number of ranked() calls per question
  timing    real B2 retrieval on the validation index for the 8 unseen questions: wall time, process CPU time and
            search counts, validated vs optimized, alternating order per question
"""
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s3_env  # noqa: E402
import evidence as ev  # noqa: E402
from engine import CheckpointStore  # noqa: E402
from s2_r2 import S2R2Research  # noqa: E402
from s2_r2_opt import S2R2OptResearch  # noqa: E402
from eval_paper_balance import load_rows, DEMO, VAL  # noqa: E402
from rank_cache import SETS  # noqa: E402


def gather(e, q):
    return e.gather_evidence(q, CheckpointStore(tempfile.mkdtemp()), {})[0]


def canon(pk):
    return json.dumps(pk, sort_keys=True, ensure_ascii=False, default=str)


def identity(count):
    groups = [(n, HERE.parent / n / 'references.json', HERE / 'cache/rankings.json', DEMO) for n in SETS]
    groups.append(('fresh-v4', HERE / 'fresh-v4/references.json', HERE / 'cache/fresh-v4-rankings.json', VAL))
    rows_cache, out = {}, []
    for name, rp, cp, b in groups:
        rows = rows_cache.setdefault(b, load_rows(b))
        cache = json.loads(cp.read_text(encoding='utf-8'))
        tables = ev.TableIndex(rows.values())
        calls = []

        def ranked(q, n):
            calls.append((q, n))
            return [rows[c] for c in cache[q]['order'][:n]]
        kw = dict(ranked=ranked, count=count, tables=tables, generate=None, v2=None, gate=None, rows=rows,
                  parallel_search=False, retrieval_strategy='r2')
        old, new = S2R2Research(**kw), S2R2OptResearch(**kw)
        for ref in json.loads(rp.read_text(encoding='utf-8')):
            calls.clear(); a = gather(old, ref['question']); n_old = len(calls)
            calls.clear(); b2 = gather(new, ref['question']); n_new = len(calls)
            out.append({'set': name, 'q': ref['id'], 'identical': canon(a) == canon(b2), 'route': a['r2']['route'],
                        'searches_old': n_old, 'searches_new': n_new, 'tokens': a['tokens']})
    return out


def timing(count):
    import evidence_budget
    from prepare import ENCODER, RERANKER
    _r, _i, ranked_real, _c, _p, _v = evidence_budget.open_ranked(VAL.parent, encoder_path=ENCODER, reranker_path=RERANKER,
                                                                  table_comparisons=False)
    rows = load_rows(VAL)
    tables = ev.TableIndex(rows.values())
    ranked_real('warm up', 5)
    calls = []

    def ranked(q, n):
        calls.append(q)
        return ranked_real(q, n)
    kw = dict(ranked=ranked, count=count, tables=tables, generate=None, v2=None, gate=None, rows=rows,
              retrieval_strategy='r2')  # parallel_search=True as in the live engine
    engines = {'validated': S2R2Research(**kw), 'optimized': S2R2OptResearch(**kw)}
    out = []
    for i, q in enumerate(json.loads((HERE / 'unseen-r2/questions.json').read_text(encoding='utf-8'))):
        rec = {'q': q['id']}
        for name in (('validated', 'optimized') if i % 2 == 0 else ('optimized', 'validated')):
            calls.clear()
            w0, c0 = time.perf_counter(), time.process_time()
            pk = gather(engines[name], q['question'])
            rec[name] = {'wall_s': round(time.perf_counter() - w0, 2), 'cpu_s': round(time.process_time() - c0, 2),
                         'searches': len(calls), 'route': pk['r2']['route'], 'packet': canon(pk)}
        rec['identical'] = rec['validated'].pop('packet') == rec['optimized'].pop('packet')
        out.append(rec)
        print(rec, flush=True)
    return out


def main():
    from transformers import AutoTokenizer
    from prepare import ENCODER
    tok = AutoTokenizer.from_pretrained(str(ENCODER))
    memo = {}

    def count(p):
        if p['chunk_id'] not in memo:
            memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
        return memo[p['chunk_id']]
    ident = identity(count)
    print('identity:', sum(o['identical'] for o in ident), '/', len(ident), 'identical;',
          'searches old', sum(o['searches_old'] for o in ident), 'new', sum(o['searches_new'] for o in ident))
    tim = timing(count)
    import statistics
    summ = {k: {'median_wall_s': statistics.median(r[k]['wall_s'] for r in tim),
                'total_wall_s': round(sum(r[k]['wall_s'] for r in tim), 1),
                'total_cpu_s': round(sum(r[k]['cpu_s'] for r in tim), 1),
                'searches': sum(r[k]['searches'] for r in tim)} for k in ('validated', 'optimized')}
    summ['all_identical_live'] = all(r['identical'] for r in tim)
    (HERE / 'r2-opt-verification.json').write_text(json.dumps({'identity': ident, 'timing': tim, 'timing_summary': summ},
                                                               indent=1), encoding='utf-8')
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()

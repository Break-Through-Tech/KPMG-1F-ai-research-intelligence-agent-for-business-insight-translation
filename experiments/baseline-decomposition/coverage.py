"""Offline evidence-coverage comparison on F01-F10: original Baseline packet vs decomposed packet (vs saved Multi-Agent).

No generation. Opens B2 exactly as the deployed Baseline does (table comparisons off, top_k 8). For every frozen
required point it reports whether its anchor passages reach the packet. Coverage of anchors is evidence availability
only; it says nothing about answer quality.

    python -s coverage.py   (from this folder, with PYTHONPATH including the repo root)
"""
import ctypes
import glob
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / 'experiments/measure/fresh-diagnostic-v1')]
from decomposed_retrieval import decomposed  # noqa: E402

FROZEN = ROOT / 'experiments/measure/fresh-diagnostic-v1'
MA_RUN = ROOT / 'data/processed/codex-paired-v1-full'
BASELINE_RUN = ROOT / 'data/processed/codex-baseline-v1-deployed'


def peak_commit_gb():
    class PMC(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
            (n, ctypes.c_size_t) for n in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                                           'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage',
                                           'PagefileUsage', 'PeakPagefileUsage')]
    k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    c = PMC()
    c.cb = ctypes.sizeof(c)
    psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return round(c.PeakPagefileUsage / 2 ** 30, 2)


def saved_ids(pattern):
    ids = []
    for f in sorted(glob.glob(str(pattern))):
        ids += [p['chunk_id'] for p in json.loads(Path(f).read_text(encoding='utf-8'))]
    return list(dict.fromkeys(ids))


def covered(point, ids):
    return any(set(group) <= set(ids) for group in point['anchors'])


def main():
    from prepare import BUNDLE, ENCODER, PIN, RERANKER
    from src.experimental.b2 import open_b2
    retrieve, identity, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
    assert identity()['indexed_records_sha256'] == PIN
    refs = {q['id']: q for q in json.loads((FROZEN / 'references.json').read_text(encoding='utf-8'))}
    log = []
    search = decomposed(retrieve, log=log)
    rows, total = {}, {'original': 0, 'decomposed': 0, 'multi_agent': 0, 'points': 0}
    for qid, ref in refs.items():
        question = ref['question']
        t0 = time.perf_counter()
        original = [p['chunk_id'] for p in retrieve(question, 8)]
        t1 = time.perf_counter()
        packet = search(question, 8)
        t2 = time.perf_counter()
        new = [p['chunk_id'] for p in packet]
        saved = saved_ids(BASELINE_RUN / qid / '*-synthesis.evidence.json')
        ma = saved_ids(MA_RUN / qid / 'current' / 'synthesis-*.evidence.json')
        papers = {p['paper'] for p in ref['required_points']}
        points = []
        for point in ref['required_points']:
            state = {k: covered(point, ids) for k, ids in (('original', original), ('decomposed', new), ('multi_agent', ma))}
            points.append({'point': point['point_id'], **state})
            total['points'] += 1
            for k in ('original', 'decomposed', 'multi_agent'):
                total[k] += state[k]
        rows[qid] = {'queries': log[-1]['queries'], 'packet_size': {'original': len(original), 'decomposed': len(new)},
                     'original_matches_saved_baseline_packet': original == saved,
                     'original_kept_in_decomposed': sum(1 for c in original if c in new),
                     'off_paper_passages': {'original': sum(1 for c in original if c.split('_')[0] not in papers),
                                            'decomposed': sum(1 for c in new if c.split('_')[0] not in papers)},
                     'seconds': {'original': round(t1 - t0, 2), 'decomposed': round(t2 - t1, 2)},
                     'points': points, 'new_ids': [c for c in new if c not in original]}
    print(json.dumps({'questions': rows, 'anchored_points': total, 'peak_commit_gb': peak_commit_gb()},
                     indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()

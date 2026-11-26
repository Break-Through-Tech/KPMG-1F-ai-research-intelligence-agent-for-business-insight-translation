"""Offline acceptance R1-R5 for S3 retrieval, using the IMPLEMENTED s3_evidence.s3_packet (not the analysis
prototype) over cached B2 rankings. 0 model calls. Writes offline-acceptance.json.

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -X utf8 offline_acceptance.py
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s3_env  # noqa: E402,F401
import evidence as ev  # noqa: E402
import s3_evidence as se  # noqa: E402
from analyze import load, paper  # noqa: E402
from components import components  # noqa: E402
from rank_cache import SETS  # noqa: E402

EXP = HERE.parent


def covered(points, ids):
    return {p['point_id'] for p in points if any(g and all(c in ids for c in g) for g in p['anchors'])}


def evaluate(sets, cache, rows, count, tables, *, packet_fn=None):
    ranked = lambda q, n: [rows[c] for c in cache[q]['order'][:n]]  # noqa: E731
    per_set, packets = {}, []
    for name, refs in sets.items():
        cov0 = cov3 = total = 0
        for ref in refs:
            q = ref['question']
            points = [p for p in ref['required_points'] if any(p['anchors'])]
            p0 = ev.standard_packet(q, ranked, count, tables)
            p3 = (packet_fn or se.s3_packet)(q, ranked, count, tables, parallel=False)
            ids0, ids3 = {p['chunk_id'] for p in p0['passages']}, {p['chunk_id'] for p in p3['passages']}
            c0, c3 = covered(points, ids0), covered(points, ids3)
            ref_papers = {paper(c) for p in points for g in p['anchors'] for c in g}
            comp_secs = sorted((cache[c]['seconds'] for c in components(q)), reverse=True)
            packets.append({
                'set': name, 'q': ref['id'], 'points': len(points), 'P0': len(c0), 'S3': len(c3),
                'lost': sorted(c0 - c3), 'gained': sorted(c3 - c0),
                'base_tokens': p3['base_tokens'], 'conclusion_tokens': p3['conclusion_tokens'],
                'serialized_est': ev.serialized_estimate(p3['passages']),
                'serialized_est_P0': ev.serialized_estimate(p0['passages']),
                'off_paper': sum(paper(c) not in ref_papers for c in ids3), 'passages': len(ids3),
                'off_paper_P0': sum(paper(c) not in ref_papers for c in ids0), 'passages_P0': len(ids0),
                'retrieval_s_P0': cache[q]['seconds'],
                'retrieval_s_S3': cache[q]['seconds'] + sum(comp_secs[i] for i in range(0, len(comp_secs), ev.SEARCH_WORKERS)),
                'trimmed': p3['trimmed_for_request_size']})
            cov0, cov3, total = cov0 + len(c0), cov3 + len(c3), total + len(points)
        per_set[name] = {'P0': cov0, 'S3': cov3, 'points': total}
    return per_set, packets


def criteria(per_set, packets):
    p0 = sum(s['P0'] for s in per_set.values())
    s3 = sum(s['S3'] for s in per_set.values())
    lost = sum(len(p['lost']) for p in packets)
    off3 = sum(p['off_paper'] for p in packets) / sum(p['passages'] for p in packets)
    off0 = sum(p['off_paper_P0'] for p in packets) / sum(p['passages_P0'] for p in packets)
    added = [p['retrieval_s_S3'] - p['retrieval_s_P0'] for p in packets]
    return {
        'R1 coverage >= P0+15 and no set below P0': {'P0': p0, 'S3': s3,
            'pass': s3 >= p0 + 15 and all(s['S3'] >= s['P0'] for s in per_set.values())},
        'R2 crowding (P0 points lost) <= 3': {'lost': lost, 'pass': lost <= 3},
        'R3 off-paper share <= P0': {'S3': round(off3, 3), 'P0': round(off0, 3), 'pass': off3 <= off0},
        'R4 budget and request guard': {
            'max_base_tokens': max(p['base_tokens'] for p in packets),
            'max_conclusion_tokens': max(p['conclusion_tokens'] for p in packets),
            'max_serialized_est': max(p['serialized_est'] for p in packets),
            'trimmed_questions': sum(bool(p['trimmed']) for p in packets),
            'pass': all(p['base_tokens'] <= se.S3_TOKENS and p['conclusion_tokens'] <= ev.CONCLUSION_TOKENS
                        and p['serialized_est'] <= ev.DEEP_EVIDENCE_EST for p in packets)},
        'R5 added retrieval latency median <= 8 s (3 workers)': {
            'median_added_s': round(statistics.median(added), 2), 'max_added_s': round(max(added), 2),
            'pass': statistics.median(added) <= 8},
        'evidence size vs P0 (serialized estimate, informs the 1.15x token criterion)': {
            'ratio_mean': round(statistics.mean(p['serialized_est'] / p['serialized_est_P0'] for p in packets), 3)},
    }


def main():
    rows, count, tables, cache = load()
    sets = {n: json.loads((EXP / n / 'references.json').read_text(encoding='utf-8')) for n in SETS}
    per_set, packets = evaluate(sets, cache, rows, count, tables)
    result = {'per_set': per_set, 'criteria': criteria(per_set, packets), 'questions': packets}
    (HERE / 'offline-acceptance.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
    print(json.dumps({'per_set': per_set, 'criteria': result['criteria']}, indent=1))


if __name__ == '__main__':
    main()

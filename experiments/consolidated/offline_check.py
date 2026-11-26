"""Offline readiness check with REAL B2 retrieval on the fresh-v2 questions (0 model calls).

For each question: the Standard protected packet (group-aware 6k skip-fit), table notes, estimated synthesis request
size against the request guard, and (for information only) how many anchored points the packet contains. Deep's
supplementary searches need the live planner, so Deep packets are not computed here. Nothing in the engine is changed
on the basis of this output; it is a size and integrity check, recorded before any live run.

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I offline_check.py
"""
import json

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))  # -I omits the script folder
import env  # noqa: E402
import evidence as ev
import synthesis as syn
from request_guard import EVIDENCE_CAP, OUTPUT_RESERVE, REQUEST_CAP, estimate, evidence_of


def main():
    import codex_paired  # noqa: F401  (adds the frozen diagnostic folder holding prepare.py to sys.path)
    import evidence_budget
    from prepare import BUNDLE, ENCODER, PIN, RERANKER
    _r, identity, ranked, count, _p, _prov = evidence_budget.open_ranked(BUNDLE, encoder_path=ENCODER,
                                                                         reranker_path=RERANKER, table_comparisons=False)
    assert identity()['indexed_records_sha256'] == PIN
    tables = ev.TableIndex(env.bundle_rows())
    refs = json.loads((env.HERE / 'fresh-v2' / 'references.json').read_text(encoding='utf-8'))
    report, worst = {}, 0
    for ref in refs:
        packet = ev.standard_packet(ref['question'], ranked, count, tables)
        ids = {p['chunk_id'] for p in packet['passages']}
        prompt = syn.build_prompt(ref['question'], packet['passages'], packet['notes'])
        schema = syn.synthesis_schema(sorted(ids))
        request = estimate(prompt) + estimate(json.dumps(schema))
        worst = max(worst, request)
        anchored = [p['point_id'] for p in ref['required_points']
                    if any(set(g) <= ids for g in p['anchors'])]
        report[ref['id']] = {'passages': len(ids), 'passage_tokens': packet['tokens'],
                             'table_groups_noted_incomplete': len(packet['notes']),
                             'evidence_tokens_est': estimate(evidence_of(prompt)),
                             'synthesis_request_tokens_est': request,
                             'within_guard': estimate(evidence_of(prompt)) <= EVIDENCE_CAP
                             and request + OUTPUT_RESERVE <= REQUEST_CAP,
                             'anchored_points_in_packet_info_only': f"{len(anchored)}/{len(ref['required_points'])}"}
    out = {'questions': report, 'max_synthesis_request_tokens_est': worst,
           'note': 'Information only. Estimates are ceil(UTF-8 bytes / 3). Deep packets need the live planner.'}
    (env.HERE / 'offline-check.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()

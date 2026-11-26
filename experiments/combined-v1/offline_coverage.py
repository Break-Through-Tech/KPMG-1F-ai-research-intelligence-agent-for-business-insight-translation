"""Offline evidence-budget comparison on the sealed fresh set (local B2 models only; no generation calls).
Applies SELECTION-RULE.md and writes offline-coverage.json.   python -I offline_coverage.py"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / 'evidence-budget'), str(HERE.parent / 'agentic-handoff')]
import codex_paired  # noqa: E402,F401  (paths)
import evidence_budget as eb  # noqa: E402
import request_guard  # noqa: E402
from prepare import BUNDLE, ENCODER, PIN, RERANKER  # noqa: E402

seal = json.loads((HERE / 'seal.json').read_text(encoding='utf-8'))
for name, digest in seal.items():
    if name != 'index_parents_sha256' and hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
        raise SystemExit(f'Sealed file changed: {name}')
refs = json.loads((HERE / 'references.json').read_text(encoding='utf-8'))
POLICIES = {'top8': eb.fixed(8), 'top16': eb.fixed(16), 'skipfit6k': eb.skip_fit(6000, 30), 'prefix8k_reference': None}


def prefix(order, tokens, count):
    out, used = [], 0
    for p in order:
        if used + count(p) > tokens:
            break
        out.append(p)
        used += count(p)
    return out


def synthesis_request(question, packet):
    """The real Baseline synthesis prompt for this packet, captured without sending it."""
    from src.research_chat import synthesize
    captured = {}

    def capture(prompt, **kwargs):
        captured['prompt'], captured['schema'] = prompt, kwargs.get('response_schema')
        raise RuntimeError('captured')
    capture.supports_response_schema = True
    try:
        synthesize(question, packet, generate=capture)
    except RuntimeError:
        pass
    prompt = captured['prompt']
    evidence = request_guard.evidence_of(prompt)
    return {'evidence_tokens': request_guard.estimate(evidence),
            'request_tokens': request_guard.estimate(prompt) + request_guard.estimate(json.dumps(captured['schema']))}


def run(table_comparisons):
    retrieve, identity, ranked, count, *_ = eb.open_ranked(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                                           table_comparisons=table_comparisons)
    assert identity()['indexed_records_sha256'] == PIN
    rows = {}
    for ref in refs:
        order = ranked(ref['question'], 30)
        assert [p['chunk_id'] for p in order[:20]] == [p['chunk_id'] for p in retrieve(ref['question'], 20)]
        row = {}
        for name, policy in POLICIES.items():
            packet = prefix(order, 8000, count) if policy is None else eb.select(order, policy, count)
            ids = {p['chunk_id'] for p in packet}
            published = [p for p in ref['required_points'] if p['anchors']]
            covered = [p['point_id'] for p in published if any(set(g) <= ids for g in p['anchors'])]
            split = [p['point_id'] for p in published for g in p['anchors'] if len(g) > 1 and 0 < len(set(g) & ids) < len(g)]
            row[name] = {'points': covered, 'n_points': len(covered), 'of': len(published), 'passages': len(packet),
                         'passage_tokens': sum(count(p) for p in packet), 'split_table_groups': split,
                         **synthesis_request(ref['question'], packet)}
        rows[ref['id']] = row
        print(ref['id'], {k: f"{v['n_points']}/{v['of']} {v['passages']}p {v['request_tokens']}t" for k, v in row.items()}, flush=True)
    return rows


def summary(rows):
    out = {}
    for name in POLICIES:
        cells = [r[name] for r in rows.values()]
        tokens = sorted(c['request_tokens'] for c in cells)
        out[name] = {'anchored_points': sum(c['n_points'] for c in cells), 'of': sum(c['of'] for c in cells),
                     'fully_anchored_questions': sum(c['n_points'] == c['of'] for c in cells),
                     'mean_passages': round(sum(c['passages'] for c in cells) / len(cells), 1),
                     'max_passage_tokens': max(c['passage_tokens'] for c in cells),
                     'p90_request_tokens': tokens[min(len(tokens) - 1, -(-9 * len(tokens) // 10) - 1)],
                     'max_request_tokens': tokens[-1], 'max_evidence_tokens': max(c['evidence_tokens'] for c in cells),
                     'split_table_groups': sorted({s for c in cells for s in c['split_table_groups']})}
    return out


baseline_rows = run(False)
base = summary(baseline_rows)
top16, skip = base['top16'], base['skipfit6k']
within = skip['max_request_tokens'] + request_guard.OUTPUT_RESERVE <= request_guard.REQUEST_CAP and \
    skip['max_evidence_tokens'] <= request_guard.EVIDENCE_CAP
# Rule text: skip-fit must split no anchor table pair that top-16 keeps WHOLE (a point top-16 covers through it).
new_splits = {s for row in baseline_rows.values() for s in row['skipfit6k']['split_table_groups']
              if s in row['top16']['points']}
choose_skip = skip['anchored_points'] >= top16['anchored_points'] + 2 and within and not new_splits
selected = 'skipfit6k' if choose_skip else 'top16'
multiagent_rows = run(True)
result = {'rule': 'SELECTION-RULE.md (frozen before this run)', 'baseline_route': base,
          'multiagent_route_initial_packet': summary(multiagent_rows),
          'rule_inputs': {'skipfit_minus_top16_points': skip['anchored_points'] - top16['anchored_points'],
                          'skipfit_within_request_caps': within, 'skipfit_new_split_groups': sorted(new_splits)},
          'selected': selected, 'per_question': {'baseline': baseline_rows, 'multiagent': multiagent_rows}}
(HERE / 'offline-coverage.json').write_text(json.dumps(result, indent=1), encoding='utf-8')
print(json.dumps({k: result[k] for k in ('baseline_route', 'multiagent_route_initial_packet', 'rule_inputs', 'selected')}, indent=1))

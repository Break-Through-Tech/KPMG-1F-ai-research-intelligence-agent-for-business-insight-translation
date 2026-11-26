"""Offline scoring aid (0 model calls). For each question, writes answers/Gxx.md with every arm's published output, the
programmatic quote check, what verification removed, and which anchor groups were in the arm's evidence packet. Also
writes mechanics.json (calls, latency, tokens, first-pass failures). Scores themselves are entered by hand in scores.json."""
import json
import sqlite3
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
SET = HERE.parent
DATA = SET.parents[1] / 'data/processed'
BUNDLE = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
ARMS = {'B0': 'combined-v1-baseline-top8', 'B1': 'combined-v1-baseline-skipfit6k',
        'M1': 'combined-v1-multiagent-skipfit6k-v2'}
norm = lambda s: ' '.join((s or '').split())  # noqa: E731
rows = {json.loads(l)['chunk_id']: json.loads(l) for l in BUNDLE.open(encoding='utf-8')}
refs = {r['id']: r for r in json.loads((SET / 'references.json').read_text(encoding='utf-8'))}


def quote_ok(item):
    """Every support quote must appear (whitespace-normalised) in at least one cited passage."""
    bad = []
    for s in item.get('support', []):
        q, cid = (s.get('quote'), s.get('chunk_id')) if isinstance(s, dict) else (s, None)
        texts = [norm(rows[c]['text']) for c in ([cid] if cid else item.get('chunk_ids', [])) if c in rows]
        if not any(norm(q) in t for t in texts):
            bad.append(f'{cid}: {q}')
    return bad


def main():
    (HERE / 'answers').mkdir(exist_ok=True)
    mech, audit = {}, {}
    for arm, d in ARMS.items():
        db = sqlite3.connect(DATA / d / 'calls.sqlite3')
        ledger = db.execute('SELECT question, status, diagnostic, seconds, usage FROM calls').fetchall()
        first_fail = sorted(p.name.split('.')[0] for p in (DATA / d).glob('*.attempt-*'))
        secs, req, ev = {}, {}, {}
        for qid in refs:
            r = json.loads((DATA / d / qid / 'result.json').read_text(encoding='utf-8'))
            secs[qid] = r['seconds']
            req[qid] = sum(x.get('request_tokens', 0) for x in r.get('requests', []))
            ev[qid] = sum(x.get('evidence_tokens', 0) for x in r.get('requests', []))
        # end-to-end latency: a question that needed the resume also paid for its failed first attempt
        e2e = {q: secs[q] + (json.loads((DATA / d / f'{q}.attempt-1' / 'result.json').read_text(encoding='utf-8'))['seconds']
                             if q in first_fail and (DATA / d / f'{q}.attempt-1' / 'result.json').is_file() else 0)
               for q in refs}
        s = sorted(secs.values())
        mech[arm] = {'calls': len(ledger), 'failed_calls': sum(1 for x in ledger if x[1] != 'ok'),
                     'failure_categories': sorted({json.loads(x[2] or 'null')['category'] for x in ledger if x[1] != 'ok'}),
                     'first_pass_failed_questions': first_fail,
                     'final_execution_errors': [q for q, v in json.loads((DATA / d / 'status.json').read_text()).items()
                                                if v['state'] != 'complete'],
                     'median_s_final_attempt': round(statistics.median(s), 1), 'p90_s_final_attempt': round(s[8], 1),
                     'median_s_incl_failed_attempt': round(statistics.median(e2e.values()), 1),
                     'p90_s_incl_failed_attempt': round(sorted(e2e.values())[8], 1),
                     'mean_request_tokens_per_q': round(statistics.mean(req.values())),
                     'mean_evidence_tokens_per_q': round(statistics.mean(ev.values())),
                     'actual_input_tokens': sum(u.get('input_tokens', 0) for x in ledger if x[4]
                                                for u in json.loads(x[4]) or []),
                     'seconds': {q: round(v) for q, v in secs.items()}}
    for qid, ref in refs.items():
        out = [f"# {qid} ({ref['type']})", '', ref['question'], '']
        for p in ref['required_points']:
            out += [f"- **{p['point_id']}** {p['expected']}"]
        out.append('')
        for arm, d in ARMS.items():
            r = json.loads((DATA / d / qid / 'result.json').read_text(encoding='utf-8'))
            res = r['envelope']['result']
            summ = res['summary']
            evidence = {e['chunk_id'] for e in res['evidence']}
            out += [f"## {arm}", '', f"*{len(evidence)} passages; anchors in packet:* " + ', '.join(
                f"{p['point_id']}={'Y' if any(set(g) <= evidence for g in p['anchors']) else ('part' if any(set(g) & evidence for g in p['anchors']) else 'N') if p['anchors'] else 'n/a'}"
                for p in ref['required_points']), '']
            if summ.get('answer_lead'):
                out += [f"**Lead:** {summ['answer_lead']}", '']
            for i, c in enumerate(summ.get('claims', [])):
                bad = quote_ok(c)
                audit.setdefault(arm, []).append((qid, 'claim', i, bad))
                out += [f"**C{i}** [{c.get('kind')}] {c['text']}", f"  - cites {c.get('chunk_ids')}; quotes {'OK' if not bad else 'NOT EXACT: ' + repr(bad)}"]
                for q in c.get('support', []):
                    out.append(f"  - > `{q.get('chunk_id')}` {norm(q.get('quote'))}" if isinstance(q, dict) else f"  - > {norm(q)}")
            for i, l in enumerate(summ.get('limitation_support', [])):
                bad = quote_ok(l)
                audit.setdefault(arm, []).append((qid, 'limitation', i, bad))
                out += [f"**L{i}** {l['text']}", f"  - cites {l.get('chunk_ids')}; quotes {'OK' if not bad else 'NOT EXACT: ' + repr(bad)}"]
                for q in l.get('support', []):
                    out.append(f"  - > `{q.get('chunk_id')}` {norm(q.get('quote'))}" if isinstance(q, dict) else f"  - > {norm(q)}")
            unsupported_lims = [l for l in summ.get('limitations', [])
                                if norm(l) not in {norm(x['text']) for x in summ.get('limitation_support', [])}]
            for l in unsupported_lims:
                out.append(f"**L (no citation)** {l}")
            for i, it in enumerate(summ.get('interpretations', []) or []):
                out.append(f"**I{i}** {json.dumps(it, ensure_ascii=False)}")
            qr = summ.get('quality_review')
            if qr:
                kept = set(qr.get('retained_claim_indices', []))
                for i, c in enumerate(qr.get('original_claims', [])):
                    if i not in kept:
                        why = next((x.get('reason') for x in qr.get('decisions', []) if x.get('index') == i), '')
                        out.append(f"**REJECTED by quality review D{i}:** {c['text']}  \n  - reason: {why}")
            for h in summ.get('held_claims', []) or []:
                out.append(f"**HELD by verification:** {json.dumps(h, ensure_ascii=False)[:1500]}")
            for n in summ.get('verification_notes', []) or []:
                out.append(f"*{n}*")
            out.append('')
        (HERE / 'answers' / f'{qid}.md').write_text('\n'.join(out), encoding='utf-8')
    for arm, items in audit.items():
        mech[arm]['quote_items'] = len(items)
        mech[arm]['quote_not_exact'] = [x[:3] for x in items if x[3]]
    (HERE / 'mechanics.json').write_text(json.dumps(mech, indent=1), encoding='utf-8')
    print(json.dumps({a: {k: v for k, v in m.items() if k != 'seconds'} for a, m in mech.items()}, indent=1))


if __name__ == '__main__':
    main()

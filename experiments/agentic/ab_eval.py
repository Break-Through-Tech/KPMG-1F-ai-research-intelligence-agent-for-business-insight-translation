"""Model-free Baseline vs Multi-Agent evaluation harness (offline replay and reporting).

It never calls a model and never starts the live experiment. Input is a RUN DIRECTORY of append-only run records
(one JSON file per request, written by ab_run.py during an approved live run, or by ``replay`` from saved
envelopes). Output is a side-by-side report (JSON + Markdown) and a human review sheet (JSON + CSV).

What is AUTOMATIC (deterministic, computed here):
  status, index fingerprint match, evidence IDs, citation-ID validity (every claim cites an evidence ID),
  quote membership (every quoted span occurs in its cited passage), required-point evidence coverage,
  required-point citation, lexical anchor mentions, latency, actual model calls (ledger delta), held claims.
What is HUMAN (always "pending" until a reviewer fills the sheet and it is merged with ``merge-review``):
  semantic correctness, citation entailment, misleading comparisons, false abstention, required-point correctness.
Automatic checks are proxies; they never establish that an answer is correct.

Commands:
  py -3.14 -I -B ab_eval.py replay --questions ab_questions.json --envelopes DIR --run-dir NEW_DIR
  py -3.14 -I -B ab_eval.py report --questions ab_questions.json --run-dir DIR --out NEW_DIR [--blind]
  py -3.14 -I -B ab_eval.py merge-review --report DIR --review FILLED_REVIEW.json --out NEW_DIR
"""
import argparse
import csv
import datetime
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD_SCHEMA = 'ab-run-record-v1'
REPORT_SCHEMA = 'ab-report-v1'
REVIEW_SCHEMA = 'ab-review-sheet-v1'
PENDING = 'pending'
HUMAN_CLAIM_FIELDS = ('semantically_correct', 'citation_entails', 'misleading_comparison')
HUMAN_RESPONSE_FIELDS = ('false_abstention', 'overall_correct')


class HarnessError(RuntimeError):
    pass


# ---------------------------------------------------------------- files: append-only, never overwritten
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def write_new(path, payload):
    """Create ``path`` exclusively. An existing file is an error, never overwritten."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            if isinstance(payload, str):
                handle.write(payload)
            else:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write('\n')
    except FileExistsError:
        raise HarnessError(f'{path} already exists; evaluation history is never overwritten.') from None
    return path


def new_directory(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise HarnessError(f'{path} already contains files; use a new directory (history is never overwritten).')
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_questions(path):
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    if spec.get('schema') != 'ab-questions-v1':
        raise HarnessError('Unknown question spec schema.')
    return spec


def record_path(run_dir, sequence, question_id, mode):
    return Path(run_dir) / f'{sequence:02d}-{question_id}-{mode}.json'


def make_record(*, run_id, sequence, question_id, question, mode, endpoint, request, response, http_status,
                started_at, finished_at, latency_seconds, budget_before, budget_after, backend_config, source):
    """One run record. Model calls are the ACTUAL experiment-ledger delta when both snapshots are known."""
    def experiment_used(snapshot):
        try:
            return snapshot['call_budget']['cumulative']['experiment']['used']
        except (KeyError, TypeError):
            return None
    before, after = experiment_used(budget_before), experiment_used(budget_after)
    return {
        'schema': RECORD_SCHEMA, 'run_id': run_id, 'sequence': sequence, 'question_id': question_id, 'question': question,
        'mode': mode, 'endpoint': endpoint, 'request': request, 'http_status': http_status, 'response': response,
        'started_at': started_at, 'finished_at': finished_at, 'latency_seconds': latency_seconds,
        'budget_before': budget_before, 'budget_after': budget_after,
        'model_calls_actual': (after - before) if before is not None and after is not None else None,
        'backend_config': backend_config, 'source': source,
    }


def load_records(run_dir):
    records = []
    for path in sorted(Path(run_dir).glob('[0-9][0-9]-*.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        if record.get('schema') != RECORD_SCHEMA:
            raise HarnessError(f'{path.name} is not a run record.')
        records.append(record)
    if not records:
        raise HarnessError(f'No run records in {run_dir}.')
    return records


# ---------------------------------------------------------------- deterministic metrics
def _norm(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _anchor_present(anchor, text):
    if re.fullmatch(r'[\d.,%]+', anchor):
        return re.search(rf'(?<![\d.]){re.escape(anchor)}(?![\d])', text) is not None
    return re.search(rf'\b{re.escape(anchor)}\b', text, re.I) is not None


def response_view(record):
    """Normalize a baseline or agentic envelope into the fields both share."""
    envelope = record.get('response') if isinstance(record.get('response'), dict) else {}
    result = envelope.get('result') if isinstance(envelope.get('result'), dict) else None
    provenance = (result or {}).get('provenance') or {}
    agentic = provenance.get('agentic') or envelope.get('agentic')
    summary = (result or {}).get('summary') or {}
    evidence = (result or {}).get('evidence') or []
    error = envelope.get('error')
    if record.get('http_status') != 200 or result is None:
        status = 'error'
    else:
        status = 'answered' if summary.get('status') == 'ok' else 'abstained'
    index_sha = ((provenance.get('index') or {}).get('indexed_records_sha256')
                 or (agentic or {}).get('index_sha256'))
    server_seconds = ((provenance.get('timings_seconds') or {}).get('total') if not agentic
                      else (agentic or {}).get('seconds'))
    return {'status': status, 'summary': summary, 'evidence': evidence, 'error': error, 'agentic': agentic,
            'provenance': provenance, 'index_sha256': index_sha, 'server_seconds': server_seconds,
            'claims': summary.get('claims') or [], 'business_insight': (result or {}).get('business_insight')}


def citation_checks(claims, evidence):
    """Citation-ID validity and exact quote membership; neither establishes entailment."""
    texts = {p.get('chunk_id'): _norm(p.get('text')) for p in evidence}
    rows = []
    for index, claim in enumerate(claims):
        ids = list(claim.get('chunk_ids') or [s.get('chunk_id') for s in claim.get('support', [])])
        unknown = [cid for cid in ids if cid not in texts]
        bad_quotes = [s.get('chunk_id') for s in claim.get('support', [])
                      if _norm(s.get('quote')) and _norm(s.get('quote')) not in texts.get(s.get('chunk_id'), '')]
        rows.append({'index': index, 'chunk_ids': ids, 'ids_valid': bool(ids) and not unknown, 'unknown_ids': unknown,
                     'quotes_in_passages': not bad_quotes, 'bad_quote_ids': bad_quotes})
    return rows


def point_checks(points, view):
    evidence_ids = {p.get('chunk_id') for p in view['evidence']}
    cited_ids = {cid for claim in view['claims'] for cid in (claim.get('chunk_ids') or [])}
    answer_text = ' '.join(_norm(c.get('text')) for c in view['claims'])
    rows = []
    for point in points:
        sources = set(point['source_chunks'])
        rows.append({'id': point['id'], 'description': point['description'],
                     'evidence_covered': bool(sources & evidence_ids), 'cited': bool(sources & cited_ids),
                     'anchors_mentioned': [a for a in point['anchors'] if _anchor_present(a, answer_text)],
                     'anchors_missing': [a for a in point['anchors'] if not _anchor_present(a, answer_text)],
                     'human_correct': PENDING})
    return rows


def analyze(record, spec):
    question = spec['questions'][record['question_id']]
    view = response_view(record)
    citations = citation_checks(view['claims'], view['evidence'])
    points = point_checks(question['required_points'], view)
    optional = point_checks(question.get('optional_points', []), view)
    agentic = view['agentic'] or {}
    reported_calls = (agentic.get('model_calls') or {}).get('used') if agentic else None
    expected_index = spec['corpus']['parents_sha256']
    return {
        'question_id': record['question_id'], 'mode': record['mode'], 'sequence': record['sequence'], 'source': record['source'],
        'automatic': {
            'status': view['status'],
            'error': view['error'],
            'index_sha256': view['index_sha256'],
            'index_matches_pinned_corpus': view['index_sha256'] == expected_index if view['index_sha256'] else None,
            'evidence_ids': [p.get('chunk_id') for p in view['evidence']],
            'evidence_count': len(view['evidence']),
            'claim_count': len(view['claims']),
            'citation_ids_valid': all(r['ids_valid'] for r in citations) if citations else None,
            'quotes_in_passages': all(r['quotes_in_passages'] for r in citations) if citations else None,
            'citations': citations,
            'required_points': points,
            'required_points_evidence_covered': sum(p['evidence_covered'] for p in points),
            'required_points_cited': sum(p['cited'] for p in points),
            'required_points_total': len(points),
            'optional_points': optional,
            'latency_seconds_wall': record.get('latency_seconds'),
            'latency_seconds_server': view['server_seconds'],
            'model_calls_actual': record.get('model_calls_actual'),
            'model_calls_reported_by_agentic': reported_calls,
            'held_claims': len((view['summary'] or {}).get('held_claims') or []),
            'claims_needing_number_check': len(agentic.get('claims_needing_number_check') or []),
            'business_insight_present': view['business_insight'] is not None,
        },
        # Traces are kept apart: the orchestration trace (agentic) vs the baseline's stage outcomes and timings.
        'orchestration_trace': agentic.get('trace') if agentic else None,
        'baseline_stage_trace': None if agentic else {'stages': view['provenance'].get('stages'),
                                                      'timings_seconds': view['provenance'].get('timings_seconds')},
        'human': {field: PENDING for field in HUMAN_RESPONSE_FIELDS},
        'automatic_is_not_correctness': True,
    }


# ---------------------------------------------------------------- reports
def build_report(records, spec, *, blind=False, run_dir=None):
    analyses = [analyze(r, spec) for r in records]
    run_ids = sorted({r['run_id'] for r in records})
    configs = [r.get('backend_config') for r in records if r.get('backend_config')]
    comparison = {}
    for qid in spec['questions']:
        rows = {a['mode']: a for a in analyses if a['question_id'] == qid}
        comparison[qid] = {mode: {k: rows[mode]['automatic'][k] for k in (
            'status', 'index_matches_pinned_corpus', 'evidence_count', 'claim_count', 'citation_ids_valid', 'quotes_in_passages',
            'required_points_evidence_covered', 'required_points_cited', 'required_points_total', 'latency_seconds_wall',
            'model_calls_actual', 'held_claims', 'claims_needing_number_check')} if mode in rows else None
            for mode in ('baseline', 'agentic')}
    total_calls = [a['automatic']['model_calls_actual'] for a in analyses]
    report = {
        'schema': REPORT_SCHEMA, 'generated_at': now(), 'run_ids': run_ids, 'run_dir': str(run_dir) if run_dir else None,
        'experiment': spec['experiment'], 'corpus': spec['corpus'], 'backend_config': configs[0] if configs else None,
        'records': len(records), 'sources': sorted({r['source'] for r in records}),
        'model_calls_actual_total': sum(c for c in total_calls if c is not None) if all(c is not None for c in total_calls) else None,
        'comparison': comparison, 'analyses': analyses,
        'human_review_status': PENDING,
        'notes': ['Automatic metrics are deterministic proxies. Semantic correctness, citation entailment, misleading comparisons '
                  'and false abstention are human judgments and remain "pending" until a filled review sheet is merged.',
                  'Sample size: one run per question per mode. Results are indicative, not statistical.'],
    }
    review = review_sheet(analyses, records, spec, blind=blind, run_ids=run_ids)
    return report, review


def review_sheet(analyses, records, spec, *, blind, run_ids):
    """One row per answer and per claim. Blind mode hides the mode behind a per-question label; the key is separate."""
    seed = hashlib.sha256('|'.join(run_ids).encode()).hexdigest()
    key, answers = {}, []
    for qid in spec['questions']:
        modes = [a['mode'] for a in analyses if a['question_id'] == qid]
        order = sorted(modes, key=lambda m: hashlib.sha256(f'{seed}{qid}{m}'.encode()).hexdigest()) if blind else modes
        for position, mode in enumerate(order):
            key[f'{qid}-{chr(65 + position)}' if blind else f'{qid}-{mode}'] = mode
    by_mode = {(r['question_id'], r['mode']): r for r in records}
    for label, mode in key.items():
        qid = label.split('-')[0]
        analysis = next(a for a in analyses if a['question_id'] == qid and a['mode'] == mode)
        view = response_view(by_mode[(qid, mode)])
        answers.append({
            'answer_label': label, 'question_id': qid, 'question': spec['questions'][qid]['text'],
            'review_criteria': spec['questions'][qid]['review_criteria'],
            'status': analysis['automatic']['status'],
            'claims': [{'index': i, 'text': c.get('text'), 'chunk_ids': c.get('chunk_ids'),
                        'quotes': [s.get('quote') for s in c.get('support', [])],
                        'automatic': {'ids_valid': analysis['automatic']['citations'][i]['ids_valid'],
                                      'quotes_in_passages': analysis['automatic']['citations'][i]['quotes_in_passages']},
                        **{field: PENDING for field in HUMAN_CLAIM_FIELDS}, 'notes': ''}
                       for i, c in enumerate(view['claims'])],
            'limitations': (view['summary'] or {}).get('limitations', []),
            'evidence': [{'chunk_id': p.get('chunk_id'), 'title': p.get('title'), 'section': p.get('section'), 'text': p.get('text')}
                         for p in view['evidence']],
            'required_points': [{'id': p['id'], 'description': p['description'], 'human_correct': PENDING}
                                for p in analysis['automatic']['required_points']],
            **{field: PENDING for field in HUMAN_RESPONSE_FIELDS}, 'notes': ''})
    return {'schema': REVIEW_SCHEMA, 'blind': blind, 'answers': answers,
            'instructions': 'Fill each "pending" field with true/false (or a short note) by reading the cited passages. '
                            'Do not change other fields. Merge with: ab_eval.py merge-review.',
            'values': {'semantically_correct': 'true|false|partial', 'citation_entails': 'true|false|partial',
                       'misleading_comparison': 'true|false', 'false_abstention': 'true|false|not_applicable',
                       'overall_correct': 'true|false|partial', 'human_correct': 'true|false|partial|not_stated'}}, key


def markdown(report, key_present=True):
    lines = [f"# A/B report: Baseline RAG vs Multi-Agent ({report['experiment']})", '',
             f"Generated {report['generated_at']} from run(s) {', '.join(report['run_ids'])} ({report['records']} records; source: {', '.join(report['sources'])}).",
             f"Corpus: `{report['corpus']['parents_sha256'][:16]}...` ({report['corpus']['retrieval_method']}, top_k {report['corpus']['top_k']}).",
             f"Actual model calls (ledger): {report['model_calls_actual_total']}.", '',
             '**Automatic metrics are proxies. Human review status: ' + report['human_review_status'] + '.**', '']
    for qid, modes in report['comparison'].items():
        lines += [f'## {qid}', '', '| Metric | Baseline | Multi-Agent |', '|---|---|---|']
        metrics = next((m for m in modes.values() if m), {})
        for metric in metrics:
            values = [str((modes.get(mode) or {}).get(metric, 'n/a')) for mode in ('baseline', 'agentic')]
            lines.append(f'| {metric} | {values[0]} | {values[1]} |')
        lines.append('')
        for analysis in report['analyses']:
            if analysis['question_id'] != qid:
                continue
            lines.append(f"**{analysis['mode']}: required points**")
            for point in analysis['automatic']['required_points']:
                lines.append(f"- {point['id']}: evidence {'yes' if point['evidence_covered'] else 'no'}, cited {'yes' if point['cited'] else 'no'}, "
                             f"anchors missing {point['anchors_missing'] or 'none'}, human: {point['human_correct']}")
            lines.append('')
    if report.get('human_summary'):
        lines += ['## Human review', '', '```json', json.dumps(report['human_summary'], indent=2), '```']
    lines += ['## Notes', ''] + [f'- {n}' for n in report['notes']]
    return '\n'.join(lines) + '\n'


def write_review_csv(path, review):
    rows = []
    for answer in review['answers']:
        rows.append({'answer_label': answer['answer_label'], 'row': 'answer', 'text': answer['status'],
                     **{f: answer[f] for f in HUMAN_RESPONSE_FIELDS}})
        for claim in answer['claims']:
            rows.append({'answer_label': answer['answer_label'], 'row': f"claim {claim['index']}", 'text': claim['text'],
                         **{f: claim[f] for f in HUMAN_CLAIM_FIELDS}})
        for point in answer['required_points']:
            rows.append({'answer_label': answer['answer_label'], 'row': point['id'], 'text': point['description'],
                         'human_correct': point['human_correct']})
    fields = ['answer_label', 'row', 'text', *HUMAN_RESPONSE_FIELDS, *HUMAN_CLAIM_FIELDS, 'human_correct']
    import io
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator='\n')  # text-mode write adds the platform newline
    writer.writeheader()
    writer.writerows(rows)
    write_new(path, buffer.getvalue())


def write_report(out_dir, report, review, key):
    out = new_directory(out_dir)
    write_new(out / 'report.json', report)
    write_new(out / 'report.md', markdown(report))
    write_new(out / 'review-sheet.json', review)
    write_review_csv(out / 'review-sheet.csv', review)
    write_new(out / 'blinding-key.json', {'key': key, 'note': 'Keep from reviewers until review is complete.'})
    return out


def merge_review(report_dir, review_path, out_dir):
    """Combine a filled review sheet with an existing report into a NEW directory. Unfilled fields stay pending."""
    report = json.loads((Path(report_dir) / 'report.json').read_text(encoding='utf-8'))
    key = json.loads((Path(report_dir) / 'blinding-key.json').read_text(encoding='utf-8'))['key']
    filled = json.loads(Path(review_path).read_text(encoding='utf-8'))
    if filled.get('schema') != REVIEW_SCHEMA:
        raise HarnessError('Not a review sheet.')
    summary = {}
    for answer in filled['answers']:
        mode = key[answer['answer_label']]
        reviewed_claims = [c for c in answer['claims'] if c['semantically_correct'] != PENDING]
        summary[f"{answer['question_id']}-{mode}"] = {
            'overall_correct': answer['overall_correct'], 'false_abstention': answer['false_abstention'],
            'claims_reviewed': len(reviewed_claims), 'claims_total': len(answer['claims']),
            'claims_correct': sum(c['semantically_correct'] is True for c in answer['claims']),
            'citations_entailing': sum(c['citation_entails'] is True for c in answer['claims']),
            'misleading_comparisons': sum(c['misleading_comparison'] is True for c in answer['claims']),
            'required_points_correct': {p['id']: p['human_correct'] for p in answer['required_points']},
        }
        for analysis in report['analyses']:
            if analysis['question_id'] == answer['question_id'] and analysis['mode'] == mode:
                analysis['human'] = {f: answer[f] for f in HUMAN_RESPONSE_FIELDS}
    complete = all(v['claims_reviewed'] == v['claims_total'] and v['overall_correct'] != PENDING for v in summary.values())
    report['human_summary'] = summary
    report['human_review_status'] = 'complete' if complete else 'partial'
    report['generated_at'] = now()
    out = new_directory(out_dir)
    write_new(out / 'report.json', report)
    write_new(out / 'report.md', markdown(report))
    write_new(out / 'review-sheet.filled.json', filled)
    return out


def replay(spec, envelopes_dir, run_dir):
    """Turn saved envelopes (files named <QID>-<mode>.json) into run records, labelled source 'replay'. No calls."""
    run_dir = new_directory(run_dir)
    run_id = f'replay-{uuid.uuid4().hex[:12]}'
    for sequence, (qid, mode) in enumerate(spec['sequence'], 1):
        source = Path(envelopes_dir) / f'{qid}-{mode}.json'
        if not source.exists():
            raise HarnessError(f'Missing saved envelope {source.name}.')
        saved = json.loads(source.read_text(encoding='utf-8'))
        envelope = saved.get('response', saved)
        write_new(record_path(run_dir, sequence, qid, mode), make_record(
            run_id=run_id, sequence=sequence, question_id=qid, question=spec['questions'][qid]['text'], mode=mode,
            endpoint='/api/research' if mode == 'baseline' else '/api/agentic-research', request=saved.get('request'),
            response=envelope, http_status=saved.get('http_status', 200), started_at=saved.get('started_at'),
            finished_at=saved.get('finished_at'), latency_seconds=saved.get('latency_seconds'),
            budget_before=saved.get('budget_before'), budget_after=saved.get('budget_after'),
            backend_config=saved.get('backend_config'), source='replay'))
    return run_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('replay')
    r.add_argument('--questions', type=Path, default=HERE / 'ab_questions.json')
    r.add_argument('--envelopes', type=Path, required=True)
    r.add_argument('--run-dir', type=Path, required=True)
    p = sub.add_parser('report')
    p.add_argument('--questions', type=Path, default=HERE / 'ab_questions.json')
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--blind', action='store_true')
    m = sub.add_parser('merge-review')
    m.add_argument('--report', type=Path, required=True)
    m.add_argument('--review', type=Path, required=True)
    m.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'replay':
            print(replay(load_questions(args.questions), args.envelopes, args.run_dir))
        elif args.command == 'report':
            spec = load_questions(args.questions)
            report, (review, key) = build_report(load_records(args.run_dir), spec, blind=args.blind, run_dir=args.run_dir)
            print(write_report(args.out, report, review, key))
        else:
            print(merge_review(args.report, args.review, args.out))
    except HarnessError as error:
        sys.exit(f'refused: {error}')


if __name__ == '__main__':
    main()

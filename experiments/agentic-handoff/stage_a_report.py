"""Assemble the Stage A evidence per question and arm from a saved run directory. No provider calls.

For every drafted claim: the model's original quote(s), any recovered quotation, the full cited passage the model
was shown, deterministic checks, the verifier's verdict, and the final outcome (published / held / dropped before
verification / not verified). Execution failures (for example a provider timeout) are listed separately and are
not counted in the quotation-grounding evaluation. The "source_review" field is left for human/source review.

    py -3.14 -B experiments/agentic-handoff/stage_a_report.py data/processed/gemini-handoff-paired-v3-grounded-stage-a
"""
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

REFERENCES = Path(__file__).resolve().parents[1] / 'measure/fresh-diagnostic-v1/references.json'
# Explanatory or causal wording. A published *finding* that uses it is flagged for manual review: it may be a
# faithfully reported author claim, or the writer's own inference labelled as a finding (a policy bypass).
EXPLANATORY = re.compile(r"\b(?:indicat|suggest|demonstrat|underscor|because|due to|attribut|explain|impl(?:y|ies|ied)|"
                         r"reflect|caus|leads? to|result(?:s|ed)? in|owing to|therefore|thus|hence|driven by|"
                         r"more effective|likely)\w*", re.I)
NUMBER = re.compile(r"(?<![\w.])[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?")


def _read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


def _norm(text):
    return re.sub(r'\s+', ' ', text or '').strip().casefold()


def arm_report(arm):
    agentic, result = _read(arm / 'agentic.json'), _read(arm / 'result.json')
    errors = sorted(p.name for p in arm.glob('*.error.json'))
    if agentic is None or agentic.get('status') == 'execution_error' or (errors and not agentic):
        return {'arm': arm.name, 'execution_failure': {'error_files': errors,
                'detail': [_read(arm / e) for e in errors],
                'status': agentic.get('status') if agentic else 'no final result written'}}
    summary = agentic['summary']
    published = {_norm(c['text']) for c in summary['claims']}
    held = {_norm(h['text']): h.get('verification', {}) for h in summary.get('held_claims', [])}
    research = [e['output'] for e in agentic['trace'] if e['type'] == 'reply' and e.get('from') == 'research_agent']
    rows = []
    for number in (1, 2):
        reply = _read(arm / f'synthesis-{number}.reply.json')
        if reply is None:
            continue
        passages = {p['chunk_id']: p['text'] for p in _read(arm / f'synthesis-{number}.evidence.json')}
        notes = research[number - 1].get('quote_grounding', []) if number <= len(research) else []
        verified, scoped = {}, {}
        for round_ in agentic.get('verification') or []:
            if round_.get('round') == number:
                verified = {_norm(c['text']): c for c in (round_.get('verification') or {}).get('claims', [])}
                scoped = {_norm(c['text']): c for c in (round_.get('verification') or {}).get('scope_review', [])}
        try:
            draft = json.loads(reply['provider_text'])
        except (KeyError, TypeError, ValueError):
            rows.append({'round': number, 'malformed_reply': True})
            continue
        for field in ('claims', 'limitations'):
            for index, item in enumerate(draft.get(field) or []):
                mine = [n for n in notes if n['field'] == field and n['index'] == index]
                key = _norm(item.get('text'))
                check = verified.get(key)
                outcome = ('dropped before verification' if any(n['action'] == 'dropped' for n in mine)
                           else 'published' if field == 'claims' and key in published
                           else 'held' if key in held
                           else 'kept as limitation' if field == 'limitations' and
                           key in {_norm(t) for t in summary.get('limitations', [])}
                           else 'not verified (draft rejected or round not selected)')
                rows.append({
                    'round': number, 'field': field, 'index': index, 'kind': item.get('kind'), 'text': item.get('text'),
                    'support': [{'chunk_id': s.get('chunk_id'), 'original_quote': s.get('quote'),
                                 'recovered_quote': next((n['recovered'] for n in mine if n['action'] == 'restored_elided_text'
                                                          and n['chunk_id'] == s.get('chunk_id')
                                                          and n['original'] == _norm_ws(s.get('quote'))), None),
                                 'cited_passage': passages.get(s.get('chunk_id'))} for s in item.get('support') or []],
                    'grounding': mine,
                    'deterministic': check and check.get('deterministic'),
                    'verifier': check and check.get('automated'),
                    'scope_review': scoped.get(key),
                    'outcome': outcome, 'held_reason': (held.get(key) or {}).get('held_reason'),
                    'explanatory_wording': sorted({m.group(0).lower() for m in EXPLANATORY.finditer(item.get('text') or '')}),
                    'source_review': 'pending'})
    rounds = agentic.get('verification') or []
    published_findings = [r for r in rows if r.get('field') == 'claims' and r.get('kind') == 'finding'
                          and r.get('outcome') == 'published']
    return {'arm': arm.name, 'final_status': agentic['status'], 'answer_scope': summary.get('answer_scope'),
            'seconds': agentic.get('seconds'), 'model_calls': agentic.get('model_calls'),
            'withheld_interpretations': [r['text'] for r in rows if 'withheld by policy' in (r.get('held_reason') or '')],
            'findings_with_explanatory_wording': [{'text': r['text'], 'wording': r['explanatory_wording']}
                                                  for r in published_findings if r['explanatory_wording']],
            'verifier_rejections': [r['verification'].get('rejection') for r in rounds
                                    if (r.get('verification') or {}).get('rejection')],
            'scope_fields': [{'round': r.get('round'), 'claims_judged': len(r['verification'].get('claims', [])),
                              'scope_records': len(r['verification'].get('scope_review', []))}
                             for r in rounds if r.get('verification') and 'scope_review' in r['verification']],
            'abstention': summary.get('abstention'), 'published_claims': [c['text'] for c in summary['claims']],
            'published_cited': [c.get('chunk_ids', []) for c in summary['claims']],
            'limitations': summary.get('limitations', []), 'claims': rows,
            'envelope_status': result and result['result']['summary']['status']}


def _norm_ws(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def required_points(question_id, arm, references=None):
    """Automated pre-check against the frozen references (read after the run, never used in generation).

    A point counts as published here when a published claim cites one of its anchor rows and every expected number
    appears in the published claims. Wording such as "random" vs "time" still needs the manual source review.
    """
    refs = {q['id']: q for q in json.loads((references or REFERENCES).read_text(encoding='utf-8'))}
    if question_id not in refs or 'published_claims' not in arm:
        return []
    claims = arm['published_cited']
    text = ' '.join(arm['published_claims'])
    have = {Decimal(n.replace(',', '')) for n in NUMBER.findall(text)}
    rows = []
    for point in refs[question_id]['required_points']:
        anchors = [set(group) for group in point['anchors']]
        cited = any(group <= set(ids) for ids in claims for group in anchors)
        expected = {Decimal(n.replace(',', '')) for n in NUMBER.findall(point['expected'])}
        rows.append({'point_id': point['point_id'], 'expected': point['expected'], 'anchor_cited': cited,
                     'missing_numbers': sorted(str(n) for n in expected - have),
                     'automated_status': 'published' if cited and expected <= have else 'not found'})
    return rows


def report(run):
    out = {'run': str(run), 'preflight': _read(run / 'preflight.json'), 'completion': _read(run / 'completion.json'),
           'questions': {}}
    for question in sorted(p for p in run.iterdir() if p.is_dir() and re.fullmatch(r'F\d\d', p.name)):
        arms = [arm_report(arm) for arm in sorted(p for p in question.iterdir() if p.is_dir())]
        for arm in arms:
            arm['required_points'] = required_points(question.name, arm)
        out['questions'][question.name] = arms
    times = sorted(a['seconds'] for arms in out['questions'].values() for a in arms
                   if 'execution_failure' not in a and a.get('seconds') is not None)
    if times:
        def pct(q):
            k = (len(times) - 1) * q
            lo = int(k)
            return round(times[lo] + (times[min(lo + 1, len(times) - 1)] - times[lo]) * (k - lo), 1)
        out['latency_seconds'] = {'completed_arms': len(times), 'median': pct(0.5), 'p90': pct(0.9),
                                  'note': 'wall time per arm, including quota pauses'}
    out['execution_failures'] = [{'question': q, **a} for q, arms in out['questions'].items() for a in arms
                                 if 'execution_failure' in a]
    return out


if __name__ == '__main__':
    print(json.dumps(report(Path(sys.argv[1])), indent=1, ensure_ascii=False))

"""Opt-in bounded completion pass for Baseline/B2 (offline prototype; Baseline code is unchanged).

Trigger. The existing answer-quality review (src/answer_quality.py) already reports when retrieved evidence answers a
requested part that the draft omitted: coverage "partial" and a gap saying the detail is available but omitted. It has
no structured flag and is told not to add claims, so the gap text is the only signal. The pass runs only when
coverage is partial AND the gap says the detail is available/omitted. A gap saying the passages "do not establish" a
detail (missing evidence) does not trigger, because re-drafting cannot find evidence that is not there.

Correction (at most once):
  1. One re-draft with the unchanged synthesize() on the SAME passages. The question text adds the reviewer's gap and
     the already-published claims (do not repeat). Exact-quote and schema validation apply unchanged.
  2. Only new *findings* are considered (no interpretations). Duplicates of published claims are dropped. Each must pass
     the deterministic reported-number check.
  3. The survivors go through the same answer-quality review (review_summary). Only claims it judges supported and
     relevant are added.
  4. Published claims and limitations are never removed or edited. New claims are appended. The answer lead states that
     a completion pass ran and that coverage was not re-assessed.
Any failure (provider error, invalid JSON, invented quote, review error) returns the original answer unchanged.

Cost when triggered: +2 model calls (re-draft + review). No calls otherwise.
"""
from copy import deepcopy
import re

OMITTED = re.compile(r'\b(?:omit\w*|left out|not included|available in the (?:supplied )?passages|'
                     r'passages (?:provide|allow|report)\w*)\b', re.I)


def _norm(text):
    return re.sub(r'\W+', ' ', text or '').strip().lower()


def should_complete(summary):
    review = summary.get('quality_review') or {}
    return (summary.get('status') == 'ok' and review.get('coverage') == 'partial'
            and bool(OMITTED.search(review.get('gap') or '')))


def completion_question(query, gap, published):
    listed = '\n'.join(f'- {c["text"]}' for c in published)
    return (f'{query}\n\nCOMPLETION REQUEST. A reviewer found this requested detail available in the passages but '
            f'omitted from the answer: {gap}\nAlready answered (do not repeat or restate):\n{listed}\n'
            'Return ONLY new findings that supply the omitted detail, each with exact supporting quotes. '
            'If the passages do not support it, return insufficient_evidence with a cited limitation.')


def complete(query, summary, passages, *, generate):
    """Return (summary, record). The returned summary contains every originally published claim unchanged."""
    from src.answer_quality import review_summary
    from src.research_chat import synthesize, validate_reported_numbers
    record = {'triggered': False, 'model_calls': 0}
    if not should_complete(summary):
        return summary, record
    gap = summary['quality_review']['gap']
    record.update(triggered=True, gap=gap)
    published = summary['claims']
    try:
        record['model_calls'] += 1
        redraft = synthesize(completion_question(query, gap, published), passages, generate=generate)
        seen = {_norm(c['text']) for c in published}
        candidates, dropped = [], []
        for claim in redraft.get('claims', []):
            if claim.get('kind') != 'finding' or _norm(claim['text']) in seen:
                dropped.append({'text': claim['text'], 'reason': 'interpretation or duplicate'})
                continue
            try:
                validate_reported_numbers([claim])
            except ValueError:
                dropped.append({'text': claim['text'], 'reason': 'number absent from cited quotes'})
                continue
            candidates.append(claim)
        record['dropped'] = dropped
        if not candidates:
            record['added'] = 0
            return summary, record
        record['model_calls'] += 1
        reviewed = review_summary(query, {'status': 'ok', 'query': query, 'claims': candidates, 'limitations': [],
                                          'limitation_support': []}, passages, generate=generate)
        accepted = [c for c in reviewed['claims'] if _norm(c['text']) not in seen]
        record['rejected_by_review'] = len(candidates) - len(accepted)
    except Exception as error:  # completion must never break or degrade the original answer
        record.update(error=type(error).__name__, added=0)
        return summary, record
    record['added'] = len(accepted)
    if not accepted:
        return summary, record
    out = deepcopy(summary)
    out['claims'] = deepcopy(published) + accepted
    note = (f'{gap} A bounded completion pass added {len(accepted)} finding(s) from the same evidence; '
            'coverage was not re-assessed.')
    if out.get('limitations') and out['limitations'][0] == summary.get('answer_lead'):
        out['limitations'] = [note, *out['limitations'][1:]]
    out['answer_lead'] = note
    out['completion'] = record
    return out, record


def enable(research):
    """Opt in on an IndexedResearch engine built with quality_check=True (e.g. src.experimental.demo.create_research)."""
    if not research.quality_check:
        raise ValueError('Completion needs the answer-quality review (quality_check=True).')
    original = research.summary

    def summary(query, passages, **kwargs):
        result = original(query, passages, **kwargs)
        result, _ = complete(query, result, passages, generate=research.generate)
        return result
    research.summary = summary
    return research

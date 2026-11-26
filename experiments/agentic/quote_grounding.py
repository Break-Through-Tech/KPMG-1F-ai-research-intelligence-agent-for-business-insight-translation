"""Opt-in source grounding between the synthesis model and the unchanged exact-quote validator.

The model still names claims, chunk IDs and the passage text it relies on. This step replaces each
quote with text copied from the trusted passage, so a published quote is never the model's retyping:

- A quote already present in its cited passage is kept as is.
- A quote that elides text with "...", ". . ." or an ellipsis character, whose pieces each occur in
  order in the cited passage, becomes the contiguous source span from the first to the last piece.
  The elided words are restored, so a reviewer sees everything in between.
- Anything else (paraphrase, invented text, unknown or wrong chunk ID) drops that claim or limitation
  alone. The rest of the draft survives. Wrong IDs are not re-cited: a claim quoting the wrong row
  would then pass the number check with only the model verifier left to catch it.

Structurally malformed or non-JSON replies pass through untouched, so the existing schema checks
still reject them. Nothing here judges entailment. The numerical checks and the independent verifier
run afterwards, unchanged, on the surviving claims.
"""
import json
import re

ELLIPSIS = re.compile(r'\s*(?:…|(?:\.\s*){3,})\s*')  # also a sentence period followed by '...'
MIN_PIECE = 15   # attach_validated_citations' minimum quote length
MAX_QUOTE = 1200  # synthesis_schema's maximum quote length


def _ws(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def locate(quote, text):
    """Return the exact span of ``text`` that ``quote`` stands for, or None. ``text`` is whitespace-normalized."""
    quote = _ws(quote)
    if len(quote) >= MIN_PIECE and quote in text:
        return quote
    pieces = [piece for piece in ELLIPSIS.split(quote) if piece]
    if not pieces or any(len(piece) < MIN_PIECE for piece in pieces):
        return None
    best, start = None, text.find(pieces[0])
    while start != -1:
        end = start + len(pieces[0])
        for piece in pieces[1:]:
            found = text.find(piece, end)
            if found == -1:
                end = None
                break
            end = found + len(piece)
        if end is None:
            break  # a later occurrence of the first piece cannot find what an earlier one missed
        if best is None or end - start < len(best):
            best = text[start:end]
        start = text.find(pieces[0], start + 1)
    return best if best is not None and len(best) <= MAX_QUOTE else None


def _ground_item(item, texts):
    """Return (item or None, notes). Malformed items are returned unchanged for the schema to reject."""
    support = item.get('support') if isinstance(item, dict) else None
    if not isinstance(support, list) or not all(
            isinstance(s, dict) and isinstance(s.get('chunk_id'), str) and isinstance(s.get('quote'), str)
            for s in support):
        return item, []
    grounded, notes = [], []
    for source in support:
        cited, quote = source['chunk_id'], source['quote']
        span = locate(quote, texts[cited]) if cited in texts else None
        if span is not None:
            if span != _ws(quote):
                notes.append({'action': 'restored_elided_text', 'chunk_id': cited,
                              'original': _ws(quote), 'recovered': span})
            grounded.append({**source, 'quote': span})
            continue
        reason = 'unknown chunk ID' if cited not in texts else 'quote not found in the cited passage'
        return None, notes + [{'action': 'dropped', 'chunk_id': cited, 'reason': reason, 'original': _ws(quote)}]
    return {**item, 'support': grounded}, notes


def ground_draft(raw, passages):
    """Return (reply text for the existing validator, list of grounding notes)."""
    try:
        draft = json.loads(raw)
    except (TypeError, ValueError):
        return raw, []
    if not isinstance(draft, dict):
        return raw, []
    texts = {p['chunk_id']: _ws(p['text']) for p in passages}
    report, dropped_claim = [], False
    for field in ('claims', 'limitations'):
        if not isinstance(draft.get(field), list):
            continue
        kept = []
        for index, item in enumerate(draft[field]):
            fixed, notes = _ground_item(item, texts)
            report += [{'field': field, 'index': index, **note} for note in notes]
            if fixed is None:
                dropped_claim |= field == 'claims'
            else:
                kept.append(fixed)
        draft[field] = kept
    if not report:
        return raw, []
    if dropped_claim and draft.get('status') == 'ok' and not draft.get('claims'):
        draft['status'] = 'insufficient_evidence'  # still needs a cited limitation to pass synthesis
    return json.dumps(draft, ensure_ascii=False), report


SEPARATOR = 'Return only JSON matching the supplied schema.\n'  # synthesis prompt / evidence boundary


def grounded(generate, report):
    """Wrap a synthesis call: ground its reply against the passages in the prompt the model was shown."""
    def call(prompt, **kwargs):
        raw = generate(prompt, **kwargs)
        try:
            passages = json.loads(prompt.split(SEPARATOR, 1)[1])['paper_passages']
        except (IndexError, KeyError, TypeError, ValueError):
            return raw  # not a synthesis prompt: leave it to the existing checks
        raw, notes = ground_draft(raw, passages)
        report.extend(notes)
        return raw
    call.supports_response_schema = getattr(generate, 'supports_response_schema', False)
    return call


class _GroundingBudget:
    def __init__(self, budget, report):
        self.budget, self.report = budget, report

    def for_agent(self, name):
        return grounded(self.budget.for_agent(name), self.report)


def enable(engine):
    """Opt in on a constructed OrchestratorAgent or EvidenceHandoffOrchestrator; frozen sources stay untouched."""
    run = engine.research.run

    def grounded_run(task, budget):
        report = []
        status, output = run(task, _GroundingBudget(budget, report))
        return status, {**output, 'quote_grounding': report}
    engine.research.run = grounded_run
    return engine

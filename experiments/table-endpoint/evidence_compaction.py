"""Isolated evidence compaction for model prompts (experimental, 2026-11-17).

The shared synthesis (``src/research_chat.py``) and quality-review (``src/answer_quality.py``)
prompts end with a JSON payload that carries every field of every passage. For table rows
about 80 % of those characters repeat what the passage ``text`` already states: structured
cells and headers (the text holds "Header: value" pairs), the caption (in the text), URLs,
hashes and version bindings. Measured on the recorded CU-DPO evidence: 22,493 serialized
characters, of which 4,363 were passage text.

``compact_prompt`` rewrites only that trailing payload, keeping for each passage the fields a
reader needs to quote and cite: ``chunk_id``, ``arxiv_id``, ``title``, ``section``,
``subsection`` and ``text`` (which carries the caption, units, column labels, row labels and
exact cell values). Everything else in the prompt (instructions, question, history, the draft
under review) is byte-for-byte unchanged. Prompts of any other shape pass through unchanged.

Validation never sees the compacted copy: the shared code checks citations and exact quotes
against the full passage records it already holds. Nothing in src/ is modified; the live
launcher wraps its generator with ``compacting``.
"""
import json

KEEP = ('chunk_id', 'arxiv_id', 'title', 'section', 'subsection', 'text')
PASSAGE_LISTS = ('paper_passages', 'passages')
MARKER = '{"question": '


def _compact_passages(items):
    if not isinstance(items, list) or not items:
        return None
    if not all(isinstance(p, dict) and isinstance(p.get('chunk_id'), str) and isinstance(p.get('text'), str) for p in items):
        return None
    return [{key: p[key] for key in KEEP if p.get(key) not in (None, '')} for p in items]


def compact_prompt(prompt):
    """Return (prompt, stats). Unrecognized prompts are returned unchanged with stats['compacted'] False."""
    stats = {'compacted': False, 'chars_before': len(prompt), 'chars_after': len(prompt)}
    if not isinstance(prompt, str):
        return prompt, stats
    start = prompt.find(MARKER)
    while start != -1:
        try:
            payload = json.loads(prompt[start:])
        except ValueError:
            start = prompt.find(MARKER, start + 1)
            continue
        if not isinstance(payload, dict):
            break
        changed = False
        for name in PASSAGE_LISTS:
            compacted = _compact_passages(payload.get(name))
            if compacted is not None:
                payload[name] = compacted
                changed = True
        if not changed:
            break
        # Same serializer settings as the shared prompt builders (non-ASCII kept as is).
        result = prompt[:start] + json.dumps(payload, ensure_ascii=False)
        stats.update(compacted=True, chars_after=len(result),
                     passages=sum(len(payload[n]) for n in PASSAGE_LISTS if isinstance(payload.get(n), list)))
        return result, stats
    return prompt, stats


def compacting(generate, on_compact=None):
    """Wrap a generator so recognized evidence payloads are compacted before the call."""
    def wrapped(prompt, **kwargs):
        compacted, stats = compact_prompt(prompt)
        if on_compact is not None:
            on_compact(stats)
        return generate(compacted, **kwargs)
    for attribute in ('supports_response_schema',):
        if hasattr(generate, attribute):
            setattr(wrapped, attribute, getattr(generate, attribute))
    return wrapped

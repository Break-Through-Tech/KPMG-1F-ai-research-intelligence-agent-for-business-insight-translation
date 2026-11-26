"""Project accepted research into a small, defensive business evidence bundle."""
from copy import deepcopy
import re

from src.research_contracts import validate_summary


def norm(value):
    return re.sub(r'\s+', ' ', value).strip()


def accepted_research(summary, passages, *, require_review=True):
    """Never pass audit drafts or uncited tails to the business generator.

    Review metadata is a pipeline declaration, not authentication or human approval.
    Reviewed legacy findings without quotes retain their cited passage, explicitly
    recorded as passage-bounded. Any supplied quote must match; never fall back
    to a whole passage when a supplied quote is invalid.
    """
    by_id = {p['chunk_id']: p for p in passages}
    if len(by_id) != len(passages):
        raise ValueError('Duplicate business evidence IDs.')
    validate_summary(summary, set(by_id))
    review = summary.get('quality_review')
    if require_review and summary['status'] == 'ok' and not (
            isinstance(review, dict) and review.get('coverage') in {'full', 'partial'}):
        raise ValueError('Business translation requires reviewed research findings.')
    claims = [c for c in summary['claims'] if c.get('kind', 'finding') == 'finding']
    limits = summary.get('limitation_support', [])
    if not isinstance(limits, list):
        raise ValueError('Accepted limitation support must be a list.')
    quotes, whole = {}, set()

    def clean(item):
        ids = item.get('chunk_ids')
        if not isinstance(ids, list) or not ids or not set(ids) <= set(by_id):
            raise ValueError('An accepted summary source is missing from the evidence.')
        row = {'text': item['text'], 'chunk_ids': deepcopy(ids)}
        support = item.get('support')
        if support is not None:
            if not isinstance(support, list) or not support:
                raise ValueError('Accepted support must contain exact quotes.')
            copied = []
            for s in support:
                cid, quote = s.get('chunk_id'), s.get('quote')
                if (cid not in ids or not isinstance(quote, str) or not quote.strip()
                        or norm(quote) not in norm(by_id[cid]['text'])):
                    raise ValueError('Accepted quote does not occur in its evidence.')
                quotes.setdefault(cid, []).append(norm(quote))
                copied.append({'chunk_id': cid, 'quote': norm(quote)})
            if {s['chunk_id'] for s in copied} != set(ids):
                raise ValueError('Every accepted citation requires its own support.')
            row['support'] = copied
        else:
            whole.update(ids)
        return row

    accepted = [clean(c) for c in claims]
    caveats = [clean(c) for c in limits]
    cited = {cid for c in accepted + caveats for cid in c['chunk_ids']}
    evidence, bounds = [], {}
    for p in passages:
        cid = p['chunk_id']
        if cid not in cited:
            continue
        # Whitelist transport fields; never forward arbitrary metadata/audit payloads.
        row = {k: deepcopy(p[k]) for k in ('chunk_id', 'text', 'arxiv_id', 'title', 'source',
               'source_url', 'pdf_url', 'page_number', 'section', 'heading') if k in p}
        if cid not in whole:
            row['text'] = '\n\n'.join(dict.fromkeys(quotes[cid]))
        bounds[cid] = 'passage' if cid in whole else 'accepted_quotes'
        evidence.append(row)
    gap = summary.get('answer_lead')
    limitations = [c['text'] for c in caveats]
    if isinstance(gap, str) and gap.strip():
        limitations.insert(0, gap)
    if not require_review:
        limitations = list(dict.fromkeys([*limitations, *summary['limitations']]))
    status = 'ok' if accepted else 'insufficient_evidence'
    if not accepted:
        limitations.append('No accepted research findings are available for business translation.')
    projected = {'status': status, 'query': summary['query'], 'claims': accepted,
                 'limitations': limitations, 'limitation_support': caveats}
    if isinstance(gap, str):
        projected['answer_lead'] = gap
    if summary.get('answer_scope') in {'full', 'partial', 'unavailable'}:
        projected['answer_scope'] = summary['answer_scope']
    return projected, evidence, bounds

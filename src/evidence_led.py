"""Quote-backed research extraction before answer synthesis.

Exact quotation checks establish source membership, not semantic entailment.
The quoted ledger and item-level support remain inspectable for AI evaluation.
Existing summary/business adapters and their response shapes remain available.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
from string import Template

from src.summarization import (_build_context, _normalize_passages, _result,
                               DEFAULT_MAX_CONTEXT_CHARS, DEFAULT_MAX_PASSAGE_CHARS)
from src.research_pipeline import PipelineError

PROMPTS = Path(__file__).resolve().parents[1] / 'prompts/evidence_led'


def prompt_provenance():
    return {'summary_adapter': 'src.evidence_led:summarize',
            'prompt_version': 'evidence-led-v2',
            'prompt_hashes': {p.name: sha256(p.read_bytes()).hexdigest()
                             for p in sorted(PROMPTS.glob('*.txt'))}}


def _object(properties, required=None):
    return {'type': 'object', 'additionalProperties': False,
            'properties': properties, 'required': required or list(properties)}


def _string():
    return {'type': 'string', 'minLength': 1, 'maxLength': 1000}


def _array(items, maximum=12):
    return {'type': 'array', 'maxItems': maximum, 'items': items}


def ledger_schema(ids):
    row = _object({'chunk_id': {'type': 'string', 'enum': ids},
                   'quote': _string(), 'finding': _string(),
                   'relevance': {'type': 'string', 'enum': ['direct', 'context']}})
    return _object({'facts': _array(row), 'coverage_gaps': _array(_string(), 8),
                    'answerability': {'type':'string','enum':['full','partial','none']}})


def _synthesis_schema(fact_ids, direct_fact_ids=None):
    ids = _array({'type': 'integer', 'enum': fact_ids})
    claim_ids = ids if direct_fact_ids is None else _array({'type':'integer','enum':direct_fact_ids})
    row = _object({'text': _string(), 'fact_ids': {**claim_ids, 'minItems': 1}})
    limit = _object({'text': _string(), 'kind': {'type': 'string', 'enum': ['source_limit', 'coverage_gap']},
                     'fact_ids': ids})
    return _object({'status': {'type': 'string', 'enum': ['ok', 'insufficient_evidence']},
                     'claims': _array(row, 4), 'limitations': _array(limit, 8)})


def _invoke(generate, prompt, schema):
    from jsonschema import Draft202012Validator
    constrained = getattr(generate, 'supports_response_schema', False) is True
    raw = generate(prompt, response_schema=schema) if constrained else generate(prompt)
    def pairs(items):
        value = {}
        for k, v in items:
            if k in value:
                raise ValueError('Duplicate response key')
            value[k] = v
        return value
    def nonfinite(value):
        raise ValueError('Nonfinite response')
    output = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    Draft202012Validator(schema).validate(output)
    return output


def _norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def validate_ledger(ledger, visible_passages):
    """Reject unknown IDs and quotes not present in text actually shown."""
    texts = {p['chunk_id']: _norm(p['text']) for p in visible_passages}
    for fact in ledger['facts']:
        quote = _norm(fact['quote'])
        if len(quote) < 15 or fact['chunk_id'] not in texts or quote not in texts[fact['chunk_id']]:
            raise ValueError('Ledger quote must occur in its displayed source passage')
    return ledger


def summarize(query, passages, *, generate,
              max_context_chars=DEFAULT_MAX_CONTEXT_CHARS,
              max_passage_chars=DEFAULT_MAX_PASSAGE_CHARS):
    if not isinstance(query, str) or not query.strip() or not callable(generate):
        raise ValueError('Provide a nonempty query and callable generator')
    if (isinstance(max_context_chars, bool) or not isinstance(max_context_chars, int) or
            max_context_chars < 200 or isinstance(max_passage_chars, bool) or
            not isinstance(max_passage_chars, int) or max_passage_chars < 50):
        raise ValueError('Invalid evidence context limits')
    usable, dropped = _normalize_passages(passages)
    context, included, omitted = _build_context(usable, max_context_chars, max_passage_chars)
    notes = []
    if dropped:
        notes.append(f'{dropped} unusable or duplicate passages excluded.')
    if omitted:
        notes.append('Context budget omitted passages: ' + ', '.join(omitted))
    if any(truncated for _, truncated in included):
        notes.append('Some displayed passages were shortened to fit the context budget.')
    if not included:
        return _result(query, 'insufficient_evidence', [],
                       ['No usable evidence fit the context budget.'] + notes, included, omitted)
    # Reconstruct the exact text shown, not full hidden source tails.
    from src.summarization import _truncate, _render_block
    visible = []
    remaining = max_context_chars
    for p, truncated in included:
        # Follow the budget algorithm directly; never parse delimiter-like text
        # inside untrusted source passages as if it were a context header.
        text = p['text']
        if len(text) > max_passage_chars:
            text = _truncate(text, max_passage_chars)
        if len(_render_block(p, text)) > remaining:
            text = _truncate(p['text'], remaining - len(_render_block(p, '')))
        visible.append({**p, 'text': text})
        remaining -= len(_render_block(p, text))
    ledger = None
    try:
        prompt = Template((PROMPTS/'extract-v1.txt').read_text()).substitute(query=query, evidence=context)
        ledger = _invoke(generate, prompt, ledger_schema([p['chunk_id'] for p, _ in included]))
        validate_ledger(ledger, visible)
        direct = [f for f in ledger['facts'] if f['relevance'] == 'direct']
        if ledger['answerability']=='partial' and not ledger['coverage_gaps']:
            raise ValueError('Partial answerability requires an explicit coverage gap')
        if not direct or ledger['answerability']=='none':
            out = _result(query, 'insufficient_evidence', [],
                ledger['coverage_gaps'] or ['No directly relevant evidence was extracted.'], included, omitted)
        else:
            facts = [dict(f, fact_id=i) for i, f in enumerate(ledger['facts'])]
            prompt = Template((PROMPTS/'synthesize-v1.txt').read_text()).substitute(
                query=query, ledger=json.dumps({'facts':facts,'coverage_gaps':ledger['coverage_gaps'],
                    'answerability':ledger['answerability']}, allow_nan=False))
            direct_ids = [i for i,f in enumerate(facts) if f['relevance']=='direct']
            answer = _invoke(generate, prompt, _synthesis_schema(list(range(len(facts))), direct_ids))
            if (answer['status'] == 'ok') != bool(answer['claims']):
                raise ValueError('Status and claims disagree')
            for limitation in answer['limitations']:
                if limitation['kind'] == 'source_limit' and not limitation['fact_ids']:
                    raise ValueError('A study limitation requires source evidence')
            claims = [{'text':c['text'], 'chunk_ids':list(dict.fromkeys(
                facts[i]['chunk_id'] for i in c['fact_ids']))} for c in answer['claims']]
            limits = [x['text'] for x in answer['limitations']]
            if ledger['answerability']=='partial':
                limits = list(dict.fromkeys(ledger['coverage_gaps'] + limits))
            out = _result(query, answer['status'], claims, limits + notes, included, omitted)
            out['claim_support'] = answer['claims']
            out['limitation_support'] = answer['limitations']
        out['answer_scope'] = ledger['answerability'] if out['status']=='ok' else 'unavailable'
        out['answer_lead'] = ledger['coverage_gaps'][0] if out['answer_scope']=='partial' else None
        out['evidence_ledger'] = ledger
        out['support_check'] = 'exact_quote_membership_only_not_semantic_entailment'
        out['generation_method'] = 'evidence-led-v2'
        return out
    except Exception:
        out = _result(query, 'insufficient_evidence', [],
                       ['Evidence-led extraction or synthesis failed validation; no findings produced.'] + notes,
                       included, omitted, 'evidence_led_failed')
        # Only retain an already validated ledger, never fabricated quote content.
        return out


def translate(summary, passages, *, industry, generate):
    """Use the established strict business contract with an evidence-led prompt."""
    from src.business_translation import translate as baseline_translate
    extra = (PROMPTS/'business-v1.txt').read_text()
    ids = [p['chunk_id'] for p in passages]
    schema = _object({
        'status': {'type':'string','enum':['ok','insufficient_evidence']},
        'industry': {'type':'string','enum':[industry]},
        'implications': _array(_object({'text':_string(),
            'chunk_ids': {'type':'array','minItems':1,'items':{'type':'string','enum':ids}},
            'suggested_action':_string(),'assumptions':_array(_string())}), 3),
        'risks':_array(_string()),'limitations':_array(_string())})
    def bounded(prompt):
        if getattr(generate, 'supports_response_schema', False) is True:
            return generate(extra + '\n\n' + prompt, response_schema=schema)
        return generate(extra + '\n\n' + prompt)
    return baseline_translate(summary, passages, industry=industry, generate=bounded)

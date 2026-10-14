"""Opt-in injected model relevance assessment with quote-checked audit details."""
from hashlib import sha256
import json
from pathlib import Path
from string import Template

from src.evidence_led import _invoke
from src.quote_validation import generate_quote_checked, POLICY
from src.research_pipeline import PipelineError

PROMPT = Path(__file__).resolve().parents[1] / 'prompts/retrieval/intent-v1.txt'


def create_intent_rerank(generate, *, max_candidates=50, max_passage_chars=2000):
    if not callable(generate):
        raise ValueError('Intent reranking requires a callable generator')
    for value, minimum in [(max_candidates, 1), (max_passage_chars, 100)]:
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError('Invalid intent-reranking budget')
    template = PROMPT.read_text()
    provenance = {'method': 'quote-checked-intent-v3', 'prompt_sha256': sha256(template.encode()).hexdigest(),
                  'max_candidates': max_candidates, 'max_passage_chars': max_passage_chars,
                  'score_semantics': 'ordinal_relevance_not_confidence',
                  'quote_validation': {'policy': POLICY,
                      'implementation_sha256': sha256((PROMPT.parents[2]/'src/quote_validation.py').read_bytes()).hexdigest()}}

    def rank(query, passages):
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Intent reranking requires a nonempty query')
        if len(passages) > max_candidates:
            raise ValueError('Intent-reranking candidate budget exceeded')
        if not passages:
            return []
        visible = [{'chunk_id': p['chunk_id'], 'title': p.get('title', ''),
                    'text': p['text'][:max_passage_chars]} for p in passages]
        ids = [p['chunk_id'] for p in visible]
        if len(set(ids)) != len(ids):
            raise ValueError('Intent candidates must have unique IDs')
        row = {'type':'object','additionalProperties':False,
               'properties':{'score':{'type':'integer','minimum':0,'maximum':3},
                             'reason':{'type':'string','minLength':1,'maxLength':600},
                             'quote':{'type':'string','maxLength':max_passage_chars}},
               'required':['score','reason','quote']}
        schema = {'type':'object','additionalProperties':False,
                  'properties':{'assessments':{'type':'object','additionalProperties':False,
                       'properties':{i:row for i in ids},'required':ids}},'required':['assessments']}
        def validate(response):
            by_id = response['assessments']
            texts = {p['chunk_id']:' '.join(p['text'].split()) for p in visible}
            for chunk_id, r in by_id.items():
                quote = ' '.join(r['quote'].split())
                if r['score'] > 0 and (len(quote) < 15 or quote not in texts[chunk_id]):
                    raise ValueError('Relevance quote must occur in the displayed candidate: ' + chunk_id)
                if r['score'] == 0 and r['quote']:
                    raise ValueError('Irrelevant candidates must not claim quotation support: ' + chunk_id)

        try:
            prompt = Template(template).substitute(
                query=query, candidates=json.dumps(visible, ensure_ascii=False))
            response, attempts = generate_quote_checked(
                lambda text: _invoke(generate, text, schema), prompt, validate)
            by_id = response['assessments']
            return [{'score':by_id[i]['score'], 'assessment':{
                'method':provenance['method'], 'reason':by_id[i]['reason'],
                'quote':by_id[i]['quote'], 'validation_attempts':attempts, 'displayed_chars':len(visible[n]['text'])}}
                for n,i in enumerate(ids)]
        except Exception:
            raise PipelineError('Intent relevance assessment failed; no ranking was produced. Retry the request or explicitly rerun without --intent-rerank. No ranking fallback occurred.') from None
    return rank, provenance

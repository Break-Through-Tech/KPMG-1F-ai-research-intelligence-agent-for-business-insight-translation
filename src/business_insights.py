"""Opt-in downstream business translation; no retrieval or research generation."""
from copy import deepcopy
from hashlib import sha256
import json
import re
from pathlib import Path
from time import perf_counter

from src.business_handoff import accepted_research
from src.business_translation import translate
from src.business_generation import BusinessTranslationUnavailable
from src.research_contracts import validate_result, validate_business_insight
from src.research_pipeline import content_fingerprint
from src.research_review import make_review_packet, require_current_review

PROMPT_VERSION = '1.2'
PROMPT = Path(__file__).resolve().parents[1] / f'prompts/business_translation/downstream-v{PROMPT_VERSION}.txt'


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def business_context(value):
    if not isinstance(value, dict) or set(value) - {'industry', 'workflow', 'decision'}:
        raise ValueError('Use industry, workflow and optional decision for business context.')
    result = {}
    for key, limit in (('industry', 300), ('workflow', 600), ('decision', 600)):
        text = value.get(key, '')
        if not isinstance(text, str) or len(text) > limit or (key != 'decision' and not text.strip()):
            raise ValueError('Provide a bounded industry/capability and specific workflow.')
        result[key] = text.strip()
    return result


# Use only wording from the saved question. The optional fields override derivation.
APPLICATION = re.compile(
    r'\b(?:before (?:using|relying on)|when (?:using|deciding)|inform a decision about|'
    r'basis for choosing|change in|apply (?:this|these findings) to|'
    r'(?:decide|choose) between)\s+([^?]+)', re.I,
)
APPLIED_QUESTION = re.compile(
    r'^(?:(?:how|what|which)\b[^?]*\b(?:should|could|can|would)\b|'
    r'which\b[^?]*\b(?:decisions?|questions follow)\b|(?:should|can|could)\b)', re.I,
)
BUSINESS_TERM = re.compile(
    r'\b(?:invoice|staffing|procurement|routing|handoffs|workflow|payback|'
    r'maintenance|audit|release[- ]review|brief review|warehouse|grant enquiries)\b', re.I,
)
EXPLICIT_INDUSTRY = re.compile(
    r'^(?:industry:\s*([^,;?]+)[,;]\s*|(?:in|for) '
    r'(banking|insurance|retail|healthcare|manufacturing|education|logistics|energy)\s*,\s*)',
    re.I,
)


def derive_business_context(question, supplied):
    if not isinstance(supplied, dict) or set(supplied) - {'industry', 'workflow', 'decision'}:
        raise ValueError('Use only industry, workflow and decision to customize this translation.')
    fields = {}
    for name, limit in (('industry', 300), ('workflow', 600), ('decision', 600)):
        value = supplied.get(name, '')
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError('Business customization must be text within the field limits.')
        fields[name] = value.strip()
    if all(fields.values()):
        return business_context(fields)
    question = ' '.join(question.split())
    industry = EXPLICIT_INDUSTRY.match(question)
    bare = question[industry.end():] if industry else question
    applied_question = next(
        (sentence for sentence in reversed(re.split(r'(?<=[.!?])\s+', bare))
         if APPLIED_QUESTION.match(sentence) and (APPLICATION.search(sentence) or BUSINESS_TERM.search(sentence))),
        '',
    )
    if not fields['workflow']:
        match = APPLICATION.search(applied_question)
        clause = (match[1] if match else applied_question).strip(' ?.\t')
        if not clause or len(clause) > 600:
            raise ValueError('Add a business workflow under Customize. The saved question does not give a clear application.')
        fields['workflow'] = clause
    if not fields['industry']:
        fields['industry'] = next(part.strip() for part in industry.groups() if part) if industry else 'Industry unspecified'
    if not fields['decision'] and applied_question and len(question) <= 600:
        fields['decision'] = question
    return business_context(fields)


def translate_result(result, *, context, generate, metadata=None, expected_fingerprint=None, research_input=None):
    """Translate a server-owned or explicitly loaded frozen result in one call.

    Structural/precondition errors raise before generation. Business stage failures
    return an isolated error and preserve research. Review metadata declares prior
    pipeline review; a fingerprint is an integrity check, not authentication.
    """
    context = business_context(context)
    if not callable(generate):
        raise ValueError('An explicitly configured business generator is required.')
    require_current_review(result)
    if expected_fingerprint is not None and result['review_fingerprint'] != expected_fingerprint:
        raise ValueError('Research snapshot changed; reload before translating.')
    output = make_review_packet(result)
    validate_result(output)
    source_fingerprint = result['review_fingerprint']
    output.pop('business_insight', None)
    output.pop('regulatory_checkpoint', None)  # A previous application's assessment cannot transfer.
    output['request']['industry'] = context['industry']
    output['request'].pop('risk_assessment', None)
    output['request'].pop('jurisdiction', None)
    prior = result.get('provenance', {}).get('business_translation', {})
    origin = deepcopy(prior.get('research_input') or research_input or {'kind': 'unspecified'})
    origin['content_sha256'] = digest([result['summary'], result['evidence']])
    provider = (metadata or {}).get('provider')
    execution = (metadata or {}).get('execution')
    generation_kind = ('fixture' if execution in {'canned_fixture', 'injected_fixture', 'offline_fixture'}
                       else 'model' if provider and provider not in {'injected', 'injected_test'} else 'injected')
    info = {'policy': f'downstream-business-v{PROMPT_VERSION}', 'prompt_id': 'business-translation/downstream',
            'prompt_version': PROMPT_VERSION, 'research_input': origin,
            'generation_kind': generation_kind,
            'usefulness_review_criteria': ['generic_recommendations', 'workflow_parroting',
                                         'semantic_repetition', 'pilot_overreliance'],
            'source_review_fingerprint': source_fingerprint, 'context': context,
            'context_sha256': digest(context),
            'publication_gate': {'policy': 'structural-only-v1', 'checks': [
                'accepted_evidence_handoff', 'business_insight_json_schema', 'citation_integrity',
                'concise_length_limits', 'accepted_limitations_preserved'],
                'semantic_screen': 'removed; validated configuration publishes model output after structural checks'},
            'implementation_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
            'handoff_sha256': sha256(Path(__file__).with_name('business_handoff.py').read_bytes()).hexdigest(),
            'translator_sha256': sha256(Path(__file__).with_name('business_translation.py').read_bytes()).hexdigest(),
            'generator': {k: v for k, v in (metadata or {}).items() if k in
                          {'provider', 'model', 'temperature', 'effort', 'execution'}},
            'attempted_calls': 0}
    error, started = None, perf_counter()
    try:
        info['prompt_sha256'] = sha256(PROMPT.read_bytes()).hexdigest()
        summary, evidence, bounds = accepted_research(result['summary'], result['evidence'])
        info.update(accepted_bundle_sha256=digest([summary, evidence]), evidence_bounds=bounds)
        summary['business_context'] = context
        def invoke(prompt):
            # Hash the actual rendered instruction + input payload at dispatch,
            # rather than claiming a template-only hash identifies the full call.
            info['complete_prompt_sha256'] = sha256(prompt.encode('utf-8')).hexdigest()
            info['instruction_suffixes'] = []
            info['attempted_calls'] += 1
            try:
                return generate(prompt)
            except BusinessTranslationUnavailable:
                info['provider_unavailable'] = True
                raise
            finally:
                attempts = getattr(generate, 'provider_attempts', None)
                if isinstance(attempts, int) and not isinstance(attempts, bool):
                    info['provider_attempts'] = attempts
        business = translate(summary, evidence, industry=context['industry'], generate=invoke,
                             concise=True, _prompt_path=PROMPT)
        if any(len(business[field]) > 4 or any(len(line) > 500 for line in business[field])
               for field in ('risks', 'limitations')) or any(
                len(row['assumptions']) > 3 or any(len(a) > 300 for a in row['assumptions'])
                for row in business['implications']):
            raise ValueError('Business caveats exceed the concise policy.')
        # No semantic screen: the validated configuration publishes the model's insight
        # after structural checks. Material accepted gaps and caveats are still kept.
        business['limitations'] = list(dict.fromkeys([*summary['limitations'], *business['limitations']]))
        validate_business_insight(business, {p['chunk_id'] for p in evidence}, industry=context['industry'])
        output['business_insight'] = business
        info.update(status=business['status'])
    except Exception:
        if info.get('provider_unavailable'):
            info['status'] = 'unavailable'
            error = {'stage': 'business', 'code': 'business_unavailable',
                     'message': 'Business translation is temporarily unavailable. The research answer is retained; try again later.'}
        else:
            info['status'] = 'failed'
            error = {'stage': 'business', 'code': 'business_failed',
                     'message': 'Business translation could not be validated. The research answer is retained.'}
    info['elapsed_seconds'] = round(perf_counter() - started, 4)
    output.setdefault('provenance', {})['business_translation'] = info
    output['review_fingerprint'] = content_fingerprint(output)
    validate_result(output)
    return {'mode': 'saved-real-result' if generation_kind == 'model' else 'fixture',
            'scenario': 'partial' if error or info['status'] != 'ok' else 'full',
            'submitted_request': deepcopy(output['request']), 'result': output, 'error': error,
            'fixture_file': None if generation_kind == 'model' else 'injected-business-generation'}


def main():
    """Explicit local saved-result invocation; importing this module is offline."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--industry', required=True)
    parser.add_argument('--workflow', required=True)
    parser.add_argument('--decision', default='')
    route = parser.add_mutually_exclusive_group(required=True)
    route.add_argument('--configured-provider', action='store_true', help='Explicit provider use; may incur a model call.')
    route.add_argument('--fixture-response', type=Path, help='Canned JSON only; not a model-quality evaluation.')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; select a new artifact path.')
    context = business_context({k: getattr(args, k) for k in ('industry', 'workflow', 'decision')})
    data = json.loads(args.input.read_text(encoding='utf-8'))
    result = data.get('result', data)
    if args.fixture_response:
        raw = args.fixture_response.read_text(encoding='utf-8')
        generate, metadata = lambda prompt: raw, {'execution': 'canned_fixture'}
    else:
        from src.business_generation import create_business_generate
        generate, metadata = create_business_generate()
    origin = {'kind': 'fixture' if data.get('mode') == 'fixture' or data.get('fixture_file') else 'recorded_research',
              'mode': data.get('mode'), 'fixture_file': data.get('fixture_file')}
    envelope = translate_result(result, context=context, generate=generate, metadata=metadata, research_input=origin)
    if args.fixture_response:
        envelope['fixture_file'] = str(args.fixture_response)
        envelope['mode'] = 'fixture'
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(envelope, stream, indent=2, ensure_ascii=True, allow_nan=False)


if __name__ == '__main__':
    main()

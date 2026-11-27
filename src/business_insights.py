"""Opt-in downstream business translation; no retrieval or research generation."""
from copy import deepcopy
from hashlib import sha256
import json
import re
from pathlib import Path
from time import perf_counter

from src.business_handoff import accepted_research
from src.business_translation import translate
import sys

from src.business_generation import (AUTHENTICATION, INVALID_REQUEST, QUOTA_EXHAUSTED, RATE_LIMITED, TEMPORARY,
                                     UNKNOWN, BusinessProviderError, BusinessTranslationUnavailable)
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
    r'\b(?:invoice|staffing|procurement|routing|model routers?|route (?:AI )?models?|handoffs|workflow|payback|'
    r'maintenance|audit|release[- ]review|brief review|warehouse|grant enquiries|dispatch|'
    r'claims (?:review|triage|processing)|patient (?:intake|triage|scheduling)|inventory|'
    r'customer (?:service|support|returns)|credit[- ]risk)\b', re.I,
)
BUSINESS_INTENT = re.compile(
    r'\b(?:business (?:insights?|implications?|case|value|opportunit(?:y|ies)|risks?)|'
    r'(?:operational|practical) implications?|(?:how|what) (?:can|could|should) '
    r'(?:our|a|the) (?:firm|company|team|business)\b|'
    r'payback|return on investment|ROI)\b', re.I,
)
BUSINESS_GOAL = re.compile(
    r'\b(?:operat(?:ing|ional) costs?|cost savings|(?:reduce|cut|lower|measure|compare) [\w -]{0,24}costs?|'
    r'customer wait times?|service levels?|decision[- ]makers?|'
    r'(?:before|whether to|should we|consider) (?:adopt\w*|deploy\w*|invest\w*|purchas\w*|implement\w*))\b', re.I,
)
GOAL_METHOD = re.compile(r'\b(?:via|through|by (?:using|automating|adopting))\s+'
                         r'((?!(?:it|this|that|them)\b)[^?.;,]+)', re.I)
DECISION_REQUEST = re.compile(
    r'\b(?:should|could|can|would)\b|\b(?:recommend|assess|evaluate|compare|identify|outline|'
    r'decide|choose|what evidence|what checks)\b', re.I,
)
OPERATIONAL_WORKFLOW = re.compile(
    r'\b(?:invoice|staffing|procurement|dispatch|inventory|customer (?:support|returns|service)|'
    r'claims (?:review|triage|processing)|patient (?:intake|triage|scheduling)|credit[- ]risk)\b', re.I,
)
ACADEMIC_SCOPE = re.compile(r'\b(?:benchmarks?|datasets?|ablation|mathematical proof|paper reports?)\b', re.I)
SECTOR = r'financial services|banking|insurance|retail|healthcare|health care|manufacturing|education|logistics|energy'
EXPLICIT_INDUSTRY = re.compile(
    rf'\bindustry\s*:\s*([^,;?.\n]+)|\b(?:in|for|across|within)\s+(?:the\s+)?({SECTOR})\b|'
    rf'\b({SECTOR})\s+(?:firms?|companies|providers?|teams?|sector|industry|organizations?|'
    r'operations?|institutions?|business(?:es)?|clinics?|stores?|insurers?)\b|'
    r'\b(banks?|hospitals?|insurers?|retailers?)\b',
    re.I,
)
SECTOR_ALIASES = {'bank': 'banking', 'banks': 'banking', 'hospital': 'healthcare', 'hospitals': 'healthcare',
                  'insurer': 'insurance', 'insurers': 'insurance', 'retailer': 'retail', 'retailers': 'retail'}
RESEARCH_ONLY = re.compile(r'\b(?:research only|academic only|'
                           r'(?:no|without)\s+(?:any\s+)?business (?:insights?|implications?|recommendations?))\b', re.I)


# ---- Generalized pass (runs only when the rules above find no application) ----
# A business question names an organisation acting (sector actor, organisation noun or first person),
# an adoption decision or business objective, and a workflow. Academic objects and research actors
# keep a question research-only.
SECTOR_TERMS = (
    ('financial services', r'financial services|fintech|asset managers?|wealth managers?|payments? (?:firms?|providers?)'),
    ('banking', r'banks?|banking|lenders?|credit unions?'),
    ('insurance', r'insurers?|insurance'),
    ('healthcare', r'hospitals?|clinics?|health ?care|health systems?|hospital networks?|care providers?'),
    ('pharmaceuticals', r'pharmaceuticals?|pharma|drug makers?|biotech'),
    ('logistics', r'logistics|freight|shipping (?:firms?|companies)|couriers?|carriers?'),
    ('retail', r'retail|retailers?|e-?commerce|stores?|merchants?'),
    ('manufacturing', r'manufactur\w*|factor(?:y|ies)|plants?'),
    ('telecommunications', r'telecoms?|telecommunications?|telcos?|mobile operators?|network operators?'),
    ('legal', r'law firms?|legal|attorneys?|lawyers?'),
    ('accounting', r'accounting|accountants?|audit firms?'),
    ('energy', r'energy|utilit(?:y|ies)|oil and gas|power (?:companies|providers?)'),
    ('aviation', r'airlines?|aviation|airports?'),
    ('hospitality', r'hotels?|hotel chains?|hospitality|restaurants?'),
    ('government', r'government(?: agenc(?:y|ies))?|public sector|councils?|municipalit(?:y|ies)'),
    ('education', r'schools?|universit(?:y|ies)|education'),
    ('transportation', r'transit|transportation|railways?|rail operators?'),
    ('real estate', r'real estate|property managers?'),
    ('media', r'media|publishers?|newsrooms?'),
    ('agriculture', r'agricultur\w*|farms?'),
    ('construction', r'construction'),
    ('automotive', r'automotive|car makers?|automakers?'),
)
ORG_NOUN = (r'compan(?:y|ies)|firms?|business(?:es)?|organi[sz]ations?|enterprises?|operators?|providers?|'
            r'agenc(?:y|ies)|plants?|chains?|networks?|teams?|departments?|call cent(?:er|re)s?|contact cent(?:er|re)s?|'
            r'vendors?|institutions?|groups?|offices?|startups?|insurers?|banks?|hospitals?|retailers?|airlines?')
ORG_ACTOR = re.compile(rf'\b(?:{ORG_NOUN}|steering group|board|desk|unit|office|manager|director)\b|'
                       r"\b(?:our|my|we|we're|we are|us)\b", re.I)
RESEARCH_ACTOR = re.compile(r'\b(?:researchers?|authors?|scientists?|academics?|students?)\b', re.I)
ACADEMIC_OBJECT = re.compile(
    r'\b(?:benchmarks?|datasets?|ablations?|papers?|studies|study|authors?|base models?|baselines?|'
    r'(?:pre-?)?train(?:ed|ing)? (?:language )?models?|fine-?tun\w*|state of the art|arxiv)\b', re.I)
ADOPTION = re.compile(
    r'\b(?:should|could|can|might|would|will)\b[^?]{0,80}\b(?:adopt|use|deploy|implement|invest|roll(?:ing)? out|'
    r'rely on|apply|automate|evaluate|pilot|buy|procure|integrate|introduce|replace|route|reduce|cut|lower|'
    r'speed up|handle|answer|help|pay off)\w*|'
    r'\b(?:is it (?:worth|cost-?effective|safe|viable)|pay(?:s)? off|cost-?effective|return on investment|'
    r'business case|what would it take|implementation risks?|risks? of (?:using|adopting|deploying|automating|relying)|'
    r'(?:weigh|consider|require|need|ask (?:vendors )?for)\b[^?]{0,40}\bbefore|before (?:a |the )?(?:rollout|roll-out|deploy\w*|'
    r'adopt\w*|implement\w*|invest\w*|using|relying)|(?:are|is) considering|evaluat\w+ [^?]{0,60} before|'
    r'what evidence|what checks)\b', re.I)
OBJECTIVE = re.compile(
    r'\b(?:(?:reduce|cut|lower|save|trim)\w*\s+[\w -]{0,30}?(?:costs?|time|workload|effort|headcount|errors?)|'
    r'more cheaply|cheaper|speed (?:up|of)|faster|productivity|efficiency|throughput|customer satisfaction|'
    r'operat(?:ing|ional) costs?|cost savings?|roi)\b', re.I)
AI_TOOL = (r'(?:LLMs?|AI(?:[- ](?:based|powered|driven))?(?: (?:tools?|agents?|assistants?|systems?|models?))?|'
           r'LLM[- ](?:based|powered) [\w-]+|language models?|(?:[\w-]+ )?agents?|assistants?|chatbots?|copilots?|'
           r'multi-agent systems?|(?:[\w-]+ )?models?|pipelines?|routers?|automation)')
DELIBERATION = re.compile(
    r'\b(?:evaluat\w*|consider\w*|weigh\w*|think\w* (?:about|of)|explor\w*|look\w* (?:at|into)|'
    r'test(?:ing)? whether|decid\w* whether|assess\w*|pilot\w*|siz\w+ up|sanity-check\w*|wonder\w*|'
    r'want(?:s)? to know (?:if|whether)|commit\w* (?:budget|to)|fund\w*|budget|justif\w*|invest\w*|adopt\w*|'
    r'deploy\w*|roll(?:ing)? (?:it )?out|rollout|go-live|launch\w*|roi|money pit|make sense|mature enough|worth|'
    r'cheaper|cost(?:s|-benefit|ing)?|budget\w*|efficiency (?:case|gains?)|trade-?offs?|case for|buy\w*|commission\w*|'
    r'introduc\w+|replac\w+|implement\w*|go wrong|realistic\w*|sensible|exposed to|savings?|handling time)\b', re.I)
FIRST_PERSON_ORG = re.compile(r"\b(?:our|we|we're|us|my (?:team|company|firm|business|organi[sz]ation))\b|\bI run\b", re.I)
_STOP = (r'(?=\s*(?:[?.;:,]|\b(?:and|with|without|before|is|are|end to end|at our|for our|across|to reduce|to save|'
         r'to cut|to lower|given|this|next|so)\b|$))')
_LEAD = r'(?:help (?:with |us )?|improve |handle |answer |speed up |support |automate |streamline |run |do |manage )?'
WORKFLOW_PATTERNS = (
    # "use LLM agents to improve delivery route planning", "apply LLMs to speed up regulatory submissions"
    re.compile(r'\b(?:use|using|apply|applying|adopt\w*|deploy\w*|implement\w*|rely on|relying on|leverag\w+|'
               r'introduc\w+|integrat\w+|invest(?:ing)? in|putting|put|pilot\w*)\s+(?:[\w -]{0,40}?\b)?' + AI_TOOL +
               r'\b[\w -]{0,20}?\s+(?:to|for|on)\s+' + _LEAD + r'([^?.;,]{3,120}?)' + _STOP, re.I),
    # "an agent that drafts work orders", "an LLM that summarizes medical records"
    re.compile(AI_TOOL + r'\s+that\s+((?:[\w-]+s)\s+[^?.;,]{3,100}?)' + _STOP, re.I),
    # "an LLM agent could handle prior authorization triage", "a planning agent can schedule nurse shifts"
    re.compile(AI_TOOL + r'\s+(?:could|can|would|will|might)\s+' + _LEAD + r'([^?.;,]{3,100}?)' + _STOP, re.I),
    # "automating claims triage with LLMs", "route easy tickets to a small model"
    re.compile(r'\b(?:automat\w+|rout\w+|triag\w+|summari[sz]\w+|handl\w+)\s+([^?.;,]{3,80}?)\s+(?:with|to|using|by|through)\s+'
               r'(?:a |an |the )?(?:small |smaller |cheaper )?' + AI_TOOL, re.I),
    # "whether contract clause review by an LLM is accurate"
    re.compile(r'\b(?:whether|if)\s+([^?.;,]{3,60}?)\s+by\s+(?:an?|the)\s+' + AI_TOOL, re.I),
    # "an AI assistant for loan underwriting", "AI on month-end close reconciliation", "AI for audit sampling"
    re.compile(AI_TOOL + r'\s+(?:for|on|to)\s+' + _LEAD + r'([^?.;,]{3,100}?)' + _STOP, re.I),
    # "AI-assisted crew rostering", "AI-generated client portfolio commentary"
    re.compile(r'\b(?:AI|LLM)[- ](?:generated|assisted|driven|written)\s+([\w -]{3,60}?)' + _STOP, re.I),
    # "LLM-based crew scheduling assistants", "AI concierge chatbots"
    re.compile(r'\b(?:LLM|AI)(?:[- ](?:based|powered))?\s+([a-z][\w -]{2,40}?)\s+(?:assistants?|chatbots?|copilots?|agents?|tools?)\b', re.I),
    # "LLM screening of applications"
    re.compile(r'\b(?:LLM|AI|agent|model)\s+(\w+ing of [^?.;,]{3,60}?)' + _STOP, re.I),
    # "cut call-centre costs by routing simple queries"
    re.compile(r'\b(?:by|through|via)\s+((?!(?:it|this|that|them)\b)[^?.;,]{3,100}?)(?=\s*(?:[?.;,]|\band\b|$))', re.I),
    re.compile(r'\b(?:reduce|cut|lower)\s+([\w -]{3,40}?)\s+(?:workload|costs?|time|effort)\b', re.I),
)


def sector_of(question):
    """Normalized sector named as an organisation acting in the question, or ''."""
    for sector, terms in SECTOR_TERMS:
        for match in re.finditer(rf'\b(?:{terms})\b', question, re.I):
            after = question[match.end():match.end() + 40]
            before = question[max(0, match.start() - 25):match.start()]
            noun_itself = re.fullmatch(rf'(?:{ORG_NOUN}|{terms})', match[0], re.I) and re.search(
                r'(?:s|y|ies|ers?|firms?|chains?|networks?|operators?|providers?|agenc\w+|plants?)$', match[0], re.I)
            if (re.match(rf"\s*(?:'s\s+)?(?:[\w-]+\s+)?(?:{ORG_NOUN})\b", after, re.I)
                    or re.search(r'\b(?:in|for|across|within|at|our|my|a|an|the)\s+(?:[\w-]+\s+)?$', before, re.I)
                    or noun_itself):
                if RESEARCH_ACTOR.match(after.strip()) or re.match(r"\s*(?:'s|s')\s", after):
                    continue
                return sector
    return ''


GENERIC_WORDS = set('''a an the of to for in on at by with from into over and or but our we us my your their its it this that
these those is are be been was were would could should can might will do does did have has had any some much more most less
use using used ai llm llms model models agent agents agentic assistant assistants tool tools system systems chatbot pipeline
layer service suite multi tool-calling tool-use preference-tuned generative off-the-shelf vendor vendors team firm company
business cost costs cheaper budget risk risks case pilot efficiency realistic realistically whether how what which who why
if so than then also just only even very really about advise give please note short put together think you like such
there here own build buy funding fund rolling roll out first next quarter month year this autumn small mid-sized large'''.split())


def _clause_workflow(question):
    """Verbatim clause naming the AI capability and its task, when it is specific enough to act on."""
    for clause in re.split(r'(?<=[?.;!])\s+|,\s+(?:and|but|so|given)\s+|;\s*', question):
        tool = re.search(AI_TOOL, clause, re.I)
        if not tool:
            continue
        text = re.sub(r'^(?:advise us on|please|give us|do you think|would it|could|should|how (?:would|could|should|do|can)'
                      r'|what|which|is (?:it|there)|if|ok so|so)\b[\s,]*', '', clause.strip(' ?.!'), flags=re.I).strip()
        specific = [w for w in re.findall(r"[a-z][a-z'-]{2,}", text.lower()) if w not in GENERIC_WORDS]
        if len(specific) >= 3 and 8 <= len(text) <= 240:
            return text
    return ''


def extract_workflow(question):
    for pattern in WORKFLOW_PATTERNS:
        match = pattern.search(question)
        if match:
            clause = re.sub(r'^(?:the|our|their|its|a|an)\s+', '', match[1].strip(' ?.,;'), flags=re.I)
            if len(clause) >= 3 and not re.fullmatch(r'(?:it|this|that|them|these|those|do so)', clause, re.I):
                return clause
    return _clause_workflow(question)


def business_signals(question):
    """Generalized signals: (industry, has_org_actor, has_intent, workflow)."""
    q = ' '.join(question.split())
    if RESEARCH_ONLY.search(q) or RESEARCH_ACTOR.search(q):
        return '', False, False, ''
    industry = sector_of(q)
    org = bool(industry or ORG_ACTOR.search(q))
    # An organisation deliberating about its own adoption or spend is business intent even if it cites papers.
    owner_deliberation = bool(FIRST_PERSON_ORG.search(q) and DELIBERATION.search(q))
    intent = bool(ADOPTION.search(q) or OBJECTIVE.search(q) or BUSINESS_INTENT.search(q) or owner_deliberation
                  or (org and DELIBERATION.search(q)))
    if ACADEMIC_OBJECT.search(q) and not (OBJECTIVE.search(q) or BUSINESS_INTENT.search(q) or owner_deliberation):
        intent = False
    return industry, org, intent, extract_workflow(q) if org and intent else ''


VAGUE = re.compile(r'\b(?:broadly(?: speaking)?|in general|generally speaking|somehow|big[- ]picture|any thoughts|'
                   r'high[- ]level|^where (?:could|might|would|does|do)\b)', re.I)


def generalized_business_context(question):
    q = ' '.join(question.split())
    industry, org, intent, workflow = business_signals(q)
    if not (org and intent and workflow) or VAGUE.search(q):
        return None
    return business_context({'industry': industry or 'Industry unspecified', 'workflow': workflow,
                             'decision': q if len(q) <= 600 else ''})


def business_context_hint(question):
    """Known context for prefilling when intent is clear but the question lacks something."""
    q = ' '.join(question.split())
    industry, org, intent, workflow = business_signals(q)
    if not (org and intent):
        return None
    if workflow:
        return None  # complete context: automatic generation handles it
    # Industry is optional ("Industry unspecified" is valid); only the workflow is genuinely required.
    return {'industry': industry, 'workflow': '', 'decision': q if len(q) <= 600 else '', 'missing': ['workflow']}


def application_signals(question):
    sectors = list(EXPLICIT_INDUSTRY.finditer(question))
    industry_match = next((match for match in sectors if match[1]), None) or next(iter(sectors), None)
    industry = next((part.strip() for part in industry_match.groups() if part), '') if industry_match else ''
    if industry_match and not industry_match[1]:
        industry = SECTOR_ALIASES.get(industry.lower(), industry.lower())
    # Strip a leading qualifier only when punctuation separates it from the request.
    subject = question
    if industry_match and industry_match.start() == 0 and re.match(r'\s*[,;:.]', question[industry_match.end():]):
        subject = question[industry_match.end():].lstrip(' ,;:.')
    sentences = re.split(r'(?<=[.!?])\s+', subject)
    explicit_business = bool(BUSINESS_INTENT.search(question))
    decision = bool(DECISION_REQUEST.search(question))
    goal = bool(BUSINESS_GOAL.search(question))
    operational = bool(OPERATIONAL_WORKFLOW.search(question) or APPLICATION.search(question))
    application = next((sentence for sentence in reversed(sentences)
                        if (APPLICATION.search(sentence) or BUSINESS_TERM.search(sentence)
                            or (goal and GOAL_METHOD.search(sentence)))
                        and (APPLIED_QUESTION.match(sentence) or explicit_business
                             or (decision and (goal or operational)))), '')
    if ACADEMIC_SCOPE.search(question) and not (explicit_business or goal or operational):
        application = ''
    return industry, explicit_business or (decision and goal), application


def automatic_business_context(question):
    """Conservative eligibility for an automatic call after a live answer is saved."""
    question = ' '.join(question.split())
    industry, explicit_business, application = application_signals(question)
    if RESEARCH_ONLY.search(question):
        return None
    if explicit_business or (industry and application):
        try:
            return derive_business_context(question, {})
        except ValueError:
            pass
    return generalized_business_context(question)


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
    industry, explicit_business, applied_question = application_signals(question)
    if not applied_question and (industry or explicit_business) and BUSINESS_TERM.search(question):
        applied_question = question
    if not fields['workflow']:
        match = APPLICATION.search(applied_question)
        if not match and BUSINESS_GOAL.search(question):
            match = GOAL_METHOD.search(applied_question)
        clause = (match[1] if match else applied_question).strip(' ?.\t')
        if not clause:
            clause = extract_workflow(question)
            applied_question = question if clause else applied_question
        if not clause or len(clause) > 600:
            raise ValueError('Add a business workflow under Customize. The saved question does not give a clear application.')
        fields['workflow'] = clause
    if not fields['industry']:
        fields['industry'] = industry or sector_of(question) or 'Industry unspecified'
    if not fields['decision'] and applied_question and len(question) <= 600:
        fields['decision'] = question
    return business_context(fields)


# What the reader sees for each failure class, and whether an inline retry is offered.
# Permanent provider failures (exhausted quota, rejected credentials, invalid request) offer none.
FAILURES = {
    TEMPORARY: ('business_unavailable', True,
                'Business insights are temporarily unavailable. The research answer is retained; try again in a moment.'),
    RATE_LIMITED: ('business_rate_limited', True,
                   'The business insight service is busy right now. The research answer is retained; try again shortly.'),
    QUOTA_EXHAUSTED: ('business_quota_exhausted', False,
                      'The business insight quota for this project is used up. The research answer is retained; '
                      'business insights can resume after the quota resets.'),
    AUTHENTICATION: ('business_configuration', False,
                     'Business insights are not configured correctly: the provider rejected the credentials. '
                     'The research answer is retained; an administrator needs to check the configuration.'),
    INVALID_REQUEST: ('business_request_rejected', False,
                      'The business insight service rejected this request. The research answer is retained.'),
    UNKNOWN: ('business_provider_error', True,
              'Business insights could not be generated. The research answer is retained; you can try again.'),
    'validation': ('business_failed', True,
                   'Business insights did not pass validation, so nothing was published. The research answer is retained; '
                   'you can try again.'),
}
# Sanitized names for our own validation messages (never provider text).
VALIDATION_CHECKS = (
    ('provider must return nonempty JSON', 'empty_output'),
    ('malformed JSON', 'malformed_json'),
    ('exceeds the concise policy', 'concise_length'),
    ('Business caveats exceed the concise policy', 'caveat_limits'),
    ('industry does not match', 'industry_mismatch'),
    ('citation', 'citation_integrity'),
    ('chunk', 'citation_integrity'),
)


def validation_check(error):
    message = str(error)
    return next((name for needle, name in VALIDATION_CHECKS if needle.lower() in message.lower()), 'business_schema')


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
        summary, evidence, bounds = accepted_research(result['summary'], result['evidence'], application=context)
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
            except BusinessProviderError as failure:
                # Recorded here because translate() deliberately replaces provider exceptions.
                info['failure'] = failure.diagnostics()
                if isinstance(failure, BusinessTranslationUnavailable):
                    info['provider_unavailable'] = True
                raise
            except Exception:
                info['failure'] = {'category': UNKNOWN}
                raise
            finally:
                attempts = getattr(generate, 'provider_attempts', None)
                if isinstance(attempts, int) and not isinstance(attempts, bool):
                    info['provider_attempts'] = attempts
                log = getattr(generate, 'attempt_log', None)
                if isinstance(log, list):
                    info['provider_attempt_log'] = [dict(entry) for entry in log if isinstance(entry, dict)][:2]
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
    except Exception as failure:
        if 'failure' in info:
            category = info['failure'].get('category', UNKNOWN)
        else:
            category = 'validation'
            info['failure'] = {'category': 'validation', 'check': validation_check(failure)}
        if category not in FAILURES:
            category = info['failure']['category'] = UNKNOWN
        code, retryable, message = FAILURES[category]
        info['status'] = 'unavailable' if category in {TEMPORARY, RATE_LIMITED} else 'failed'
        error = {'stage': 'business', 'code': code, 'message': message, 'retryable': retryable}
        if retryable and info['failure'].get('retry_after_seconds'):
            error['retry_after_seconds'] = info['failure']['retry_after_seconds']
        # One sanitized line for operators: enums and status codes only.
        print('business-failure ' + ' '.join(f'{key}={value}' for key, value in sorted(info['failure'].items()))
              + f" attempts={info.get('provider_attempts', 0)}", file=sys.stderr, flush=True)
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

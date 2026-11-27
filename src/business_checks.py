"""Conservative business screens. Surface checks are not semantic certification."""
from functools import lru_cache
from hashlib import sha256
import importlib.util
from pathlib import Path
import re

NUMERIC_PATH = Path(__file__).resolve().parents[1] / 'experiments/agentic/numeric_checks.py'
POLICY = 'downstream-business-screen-v1.2'

SCOPED_GAP = re.compile(
    r'(?:Evidence gap:\s*)?The supplied (?:evidence|research|excerpts?|packet) '
    r'(?:does|do) not (?:establish|quantify|report|support|provide evidence of) '
    r'(?:(?:enterprise|organizational|business|annual|target-workflow) )?'
    r'(?:ROI|return on investment|payback(?: figures?)?|(?:cost )?savings|benefits|'
    r'compliance|deployment readiness|(?:measured )?(?:outcomes|performance|accuracy)'
    r'(?: (?:in|for) the target (?:[a-z-]+ )?(?:workflow|organization|setting))?)'
    r'(?: or (?:ROI|return on investment|payback(?: figures?)?|(?:cost )?savings))?\.?',
    re.I,
)
SOURCE_WIDE_ABSENCE = re.compile(
    r'\b(?:study|paper|authors|article) (?:never|(?:does|did|do) not) '
    r'(?:stud(?:y|ied)|test(?:ed)?|measur(?:e|ed)|evaluat(?:e|ed)|address(?:ed)?|'
    r'examin(?:e|ed)|report(?:ed)?|provid(?:e|ed)|includ(?:e|ed)|assess(?:ed)?|investigat(?:e|ed))\b',
    re.I,
)
GAP_LABEL = re.compile(r'^(?:Evidence gap|Transfer gap):\s*', re.I)
OPEN_CONDITION = re.compile(r'(?:Confirm whether|Transfer depends on whether) (.+)', re.I)
FACTUAL_PREMISE = re.compile(
    r'\b(?:because|since|given(?: that)?|already|proven|established|validated|demonstrated|'
    r'showed|found|reported|measured|achieved|observed|guaranteed|which|who)\b', re.I,
)
RESEARCH_ATTRIBUTION = re.compile(
    r'\b(?:study|paper|benchmark|authors|experiment|research)\b[^,;]*'
    r'\b(?:reported|demonstrated|showed|found|proved|measured|established)\b', re.I,
)
DECLARATIVE_ACTION = re.compile(r'^(?:then )?(?:the|this|our|your|it|we|they)\b', re.I)
FRACTION_BOUND = re.compile(
    r'\b(?P<bound>under|less than|more than|over|at least|at most) '
    r'(?:a|one) (?P<fraction>half|quarter|fifth|tenth)\b', re.I,
)
PERCENT_BOUND = re.compile(
    r'\b(?P<bound>under|less than|more than|over|at least|at most) (?P<value>50|25|20|10) ?%', re.I,
)
FRACTION_PERCENT = {'half': '50', 'quarter': '25', 'fifth': '20', 'tenth': '10'}
DENOMINATOR = re.compile(r'\bper (?:[1-9]\d{0,2}(?:,\d{3})+|[1-9]\d*) (?=queries\b|requests\b|tasks\b|cases\b)', re.I)
MEASURE_ACTION = re.compile(
    r'^(?:measure|report|compare|track|record)\b|^the observable result should be a comparison of\b',
    re.I,
)


def directly_negated(text, start):
    """Negate only the matched predicate, never the rest of a sentence.

    In particular 'not only', 'no doubt', and 'not optional' do not negate a
    later assertion. Unknown/ambiguous scopes receive no safety exemption.
    """
    match = re.search(r'\b(?:not|never|cannot|no)(?:\s+(?:yet|currently))?\s*$', text[:start], re.I)
    if not match:
        return False
    # Double negation is ambiguous/positive, not an exemption.
    return not bool(re.search(r'\b(?:not|never|cannot|no)\s*$', text[:match.start()], re.I))


def negative_evidence_gap(text):
    # A complete, restricted negative proposition, not a prefix exemption.
    return bool(re.fullmatch(r'(?:(?:The (?:study|paper|evidence)|This study) (?:does not|cannot) (?:establish|demonstrate|prove|support|guarantee) (?:enterprise |organizational |business |annual )?(?:savings|ROI|benefits|compliance|deployment readiness)|No guaranteed savings (?:are|were) (?:established|demonstrated))\.?', text.strip(), re.I))


def is_evidence_gap(text):
    return negative_evidence_gap(text) or bool(SCOPED_GAP.fullmatch(text.strip()))


def open_application_condition(sentence):
    """Recognize an explicit question about an untested condition, not a field exemption."""
    match = OPEN_CONDITION.fullmatch(sentence.rstrip('.?'))
    if not match:
        return False
    condition = match[1]
    # Keep statements with embedded factual premises or separate clauses on the fact path.
    return (not re.search(r'[,:;.!?]|\b(?:and|but|while|although|therefore)\b', condition, re.I)
            and not FACTUAL_PREMISE.search(condition))


def normalize_bounds(text):
    """Represent exact fraction/percent equivalents with the same strict/inclusive bound."""
    bounds = {'under': 'less than', 'over': 'more than'}

    def canonical(match, value):
        bound = match['bound'].lower()
        return f'{bounds.get(bound, bound)} {value}%'

    text = FRACTION_BOUND.sub(lambda m: canonical(m, FRACTION_PERCENT[m['fraction'].lower()]), text)
    return PERCENT_BOUND.sub(lambda m: canonical(m, m['value']), text)


def preserves_fraction_bounds(text, sources):
    """A normalized prose bound can support only the same bound, never a point estimate."""
    derived = {}
    for source in sources:
        for match in PERCENT_BOUND.finditer(source):
            derived.setdefault(match['value'], set()).add(match['bound'])
    if not derived:
        return True
    point_measurements = [PERCENT_BOUND.sub('', source) for source in sources]
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        bounds = {m.end(): m['bound'] for m in PERCENT_BOUND.finditer(sentence)}
        for match in re.finditer(r'(?<![\d.])(\d+) ?%', sentence):
            if match[1] not in derived:
                continue
            if (bounds.get(match.end()) not in derived[match[1]] and
                    numeric_checks().ground_text(sentence, point_measurements)['status'] != 'grounded'):
                return False
    return True


def measurement_text(sentence, kind):
    """A proposed unit of reporting supplies no empirical value to ground."""
    if (kind == 'action' and MEASURE_ACTION.search(sentence) and
            not FACTUAL_PREMISE.search(sentence)):
        return DENOMINATOR.sub('per ', sentence)
    return sentence


def bounded_deployment(text):
    """A conditional word alone is insufficient: require a confined test scope."""
    bounded = re.search(r'\b(?:sandbox|non.production|offline|isolated test|limited prototype|(?:small|limited|controlled) (?:internal )?pilot)\b', text, re.I)
    gate = re.search(r'\b(?:only if|only after|subject to|before|compare|test|evaluate|validate)\b', text, re.I)
    return bool(bounded and gate)


@lru_cache(maxsize=1)
def numeric_checks():
    # Reuse the dependency-free checker, without loading any agent or provider.
    spec = importlib.util.spec_from_file_location('business_numeric_checks', NUMERIC_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance():
    return {'policy': POLICY, 'implementation_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
            'numeric_checks_sha256': sha256(NUMERIC_PATH.read_bytes()).hexdigest()}


def words(text):
    stop = {'the','and','for','with','this','that','from','into','could','should','would',
            'research','study','business','findings','before','after','consider','pilot',
            'evaluate','evaluation','performance','improve','improvement','ensure','their',
            'these','using','use','your','have','more','than','only','when','will','such'}
    return {w for w in re.findall(r'[a-z]{4,}', text.lower()) if w not in stop}


def issues(text, evidence, *, kind):
    """Block known dangerous assertions even when their terms occur in a paper."""
    found = []
    # Never delete a negated span: independent positive assertions must remain
    # visible across conjunctions, commas, colons, newlines and punctuation.
    checked = re.sub(r'\s+', ' ', text.replace('\u2019', "'")).strip()
    checked = re.sub(r"\b(is|are|does|do|will|would|can|could|should|must)n't\b", r'\1 not', checked, flags=re.I)
    checks = {
        'financial_projection': r'\b(?:will|would|can|could|may|expected to|projected to)\s+(?:not only\s+|also\s+|not fail to\s+)?(?:deliver|generate|save|yield|produce|achieve|cut|reduce|increase)\b[^.;!?]*(?:\$|£|€|million|billion|ROI|savings|profit|revenue|costs|expenses|money)',
        'financial_assertion': r'(?:\$|£|€)\s*\d|\b\d[\d,.]*\s*%\s*(?:ROI|return on investment)|\b(?:guaranteed|projected|expected|annual)\s+(?:ROI|savings|profit)|\b(?:ROI|savings|profit|revenue)\s+(?:will|would|is|are|reaches?|of|exceeds?)\b',
        'compliance_claim': r'\b(?:(?:is|are|becomes?|will be|makes? it)\s+(?:legally\s+)?compliant|ensures? compliance|meets? (?:all )?(?:regulatory|legal)|legally safe)',
        'deployment_claim': r'\b(?:production.ready|ready for (?:production|deployment)|deploy (?:it )?(?:now|immediately|at scale)|roll (?:it )?out (?:enterprise|company|firm).wide|(?:enterprise|company|firm).wide (?:rollout|deployment)|deploy\b[^.;!?]*\b(?:at scale|enterprise.wide|firm.wide|company.wide|across (?:the )?(?:organization|company|enterprise|firm)))',
        'exaggerated_benefit': r'\b(?:guarantees?|risk.free|ensures? (?:better |higher )?(?:accuracy|reliability|safety)|eliminates? (?:all )?(?:risk|errors|bias)|always (?:improves?|outperforms?)|replaces? (?:all )?(?:staff|analysts|reviewers))\b',
    }
    for label, pattern in checks.items():
        for match in re.finditer(pattern, checked, re.I):
            begin = max(checked.rfind(mark, 0, match.start()) for mark in '.;!?') + 1
            ends = [checked.find(mark, match.end()) for mark in '.;!?']
            end = min((i for i in ends if i >= 0), default=len(checked))
            if is_evidence_gap(checked[begin:end]):
                continue
            if directly_negated(checked, match.start()):
                continue
            if label == 'financial_assertion':
                # Observed study economics may be reported faithfully. A matching
                # amount never licenses an organization projection in another sentence.
                start = max(checked.rfind(mark, 0, match.start()) for mark in '.;!?') + 1
                ends = [checked.find(mark, match.end()) for mark in '.;!?']
                end = min((i for i in ends if i >= 0), default=len(checked))
                sentence = checked[start:end]
                if (re.search(r'\b(?:study|paper|benchmark|authors|experiment)\b', sentence, re.I)
                        and numeric_checks().ground_text(sentence, evidence)['status'] == 'grounded'):
                    continue
            found.append(label)
    # Preserve bounded, reversible testing recommendations. This exemption
    # never applies to readiness, rollout, financial or guarantee matches above.
    for action in re.finditer(r'\b(?:deploy|roll (?:it )?out)\b', checked, re.I):
        if directly_negated(checked, action.start()):
            continue
        if re.search(r'\bwhether to\s*$', checked[:action.start()], re.I):
            continue  # Asking for a deployment decision is not recommending it.
        start = max(checked.rfind(mark, 0, action.start()) for mark in '.;:!?') + 1
        ends = [checked.find(mark, action.end()) for mark in '.;:!?']
        end = min((i for i in ends if i >= 0), default=len(checked))
        if not bounded_deployment(checked[start:end]):
            found.append('unbounded_deployment_action')
    checker = numeric_checks()
    numeric_evidence = [normalize_bounds(source) for source in evidence]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    numeric_text = ' '.join(normalize_bounds(measurement_text(sentence, kind)) for sentence in sentences)
    if re.search(r'\d', numeric_text):
        result = checker.ground_text(numeric_text, numeric_evidence)
        if result['status'] not in {'grounded', 'no_numbers'}:
            found.append('unsupported_or_transferred_number')
        # The shared checker compares values and units. A bound derived from prose
        # must not also license an equality claim or a bound in the opposite direction.
        if not preserves_fraction_bounds(numeric_text, numeric_evidence):
            found.append('unsupported_or_transferred_number')
    # Check factual clauses separately: a later 'could' must not excuse an
    # unsupported first sentence. Assumptions are not a loophole for assertions.
    for sentence in sentences:
        if is_evidence_gap(sentence):
            continue
        source_statement = GAP_LABEL.sub('', sentence).rstrip('.')
        if SOURCE_WIDE_ABSENCE.search(source_statement) and not any(
                source_statement in source for source in evidence):
            found.append('unsupported_source_wide_absence')
        if kind in {'assumption', 'action'} and open_application_condition(sentence):
            # Numeric and high-risk checks still apply to the original statement.
            continue
        if kind == 'assumption' and OPEN_CONDITION.fullmatch(sentence):
            # Keep each question confined to one application condition.
            found.append('unscoped_application_condition')
        premise_flags = []
        if sentence.lower().startswith('if '):
            premise, _, consequent = sentence[3:].partition(',')
            if RESEARCH_ATTRIBUTION.search(premise):
                # A claim about a demonstrated result still needs evidence when
                # it is used as a premise for a hypothetical application.
                _, flags = checker.advice_issues(normalize_bounds(premise), numeric_evidence, [])
                premise_flags.extend(flags)
            consequent = consequent.strip()
            if kind == 'action' and DECLARATIVE_ACTION.match(consequent):
                _, flags = checker.advice_issues(normalize_bounds(consequent), numeric_evidence, [])
                premise_flags.extend(flags)
        action_assertion = (kind == 'action' and DECLARATIVE_ACTION.match(sentence)
                            and checker.ASSERTION.search(sentence)
                            and not checker.HEDGE.search(sentence) and not checker.CAVEAT.search(sentence))
        if kind == 'action' and not (action_assertion or FACTUAL_PREMISE.search(sentence) or premise_flags):
            continue
        actual_kind = ('limitation' if kind == 'assumption' and checker.CAVEAT.search(sentence)
                       else 'implication' if kind == 'assumption' or action_assertion else kind)
        _, premise = checker.advice_issues(normalize_bounds(measurement_text(sentence, kind)),
                                          numeric_evidence, [], actual_kind)
        # The older screen treats any mention of savings as a claim, including
        # 'without establishing savings'. Assertion checks above replace those
        # keyword rules; keep its factual/setting/premise checks.
        found.extend(p for p in [*premise_flags, *premise] if p not in {
            'roi_or_savings', 'guarantee', 'compliance_claim',
            'deployment_readiness', 'workforce_replacement'})
    return sorted(set(found))


def screen(output, summary, passages, context):
    """Withhold unsafe or plainly generic items; retain an inspectable audit only."""
    from copy import deepcopy
    result = deepcopy(output)
    by_id = {p['chunk_id']: p['text'] for p in passages}
    trace, kept, seen = [], [], set()
    for row in result['implications']:
        sources = [by_id[cid] for cid in row['chunk_ids']]
        problems = []
        for field in ('text', 'suggested_action', 'assumptions'):
            values = row[field] if field == 'assumptions' else [row[field]]
            for value in values:
                problems.extend(issues(value, sources, kind='assumption' if field == 'assumptions' else 'action' if field == 'suggested_action' else 'implication'))
        anchors = words(' '.join(sources))
        if not words(row['text']) & anchors:
            problems.append('no_research_specific_connection')
        action_words = words(row['suggested_action'])
        if not action_words & (anchors | words(' '.join(context.values()))):
            problems.append('generic_action')
        # Semantic specificity, workflow parroting and pilot dependence are
        # evaluation judgments, not an expanding vocabulary allowlist.
        # Exact actions are safely deduplicated; paraphrase similarity is not proof.
        key = (' '.join(row['suggested_action'].lower().split()),
               tuple(sorted(row['chunk_ids'])), tuple(sorted(row['assumptions'])))
        if key in seen:
            problems.append('repeated_action')
        if not problems:
            seen.add(key)
            kept.append(row)
        trace.append({'item': len(trace), 'status': 'withheld' if problems else 'kept_unverified',
                      'issues': sorted(set(problems))})
    result['implications'] = kept
    for field in ('risks', 'limitations'):
        safe = []
        for text in result[field]:
            problems = issues(text, list(by_id.values()), kind=field[:-1])
            # Uncited factual assertions need evidence overlap; labeled gaps/concerns
            # may be proposed but their factual premises are still screened above.
            labeled = re.match(r'(Potential concern|Evidence gap|Transfer gap):', text, re.I)
            if not labeled and not is_evidence_gap(text) and len(words(text) & words(' '.join(by_id.values()))) < 2:
                problems.append('unanchored_risk_or_limit')
            trace.append({'field': field, 'status': 'withheld' if problems else 'kept_unverified',
                          'issues': sorted(set(problems))})
            if not problems and text not in safe:
                safe.append(text)
        result[field] = safe
    if not kept:
        result['status'] = 'insufficient_evidence'
        if output['implications'] or (summary['status'] == 'ok' and not result['limitations']):
            result['limitations'] = list(dict.fromkeys([*result['limitations'],
                'No sufficiently specific business implication passed the evidence and advice checks.']))
    return result, trace

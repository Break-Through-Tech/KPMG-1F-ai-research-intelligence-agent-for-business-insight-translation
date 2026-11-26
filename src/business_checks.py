"""Conservative business screens. Surface checks are not semantic certification."""
from functools import lru_cache
from hashlib import sha256
import importlib.util
from pathlib import Path
import re

NUMERIC_PATH = Path(__file__).resolve().parents[1] / 'experiments/agentic/numeric_checks.py'
POLICY = 'downstream-business-screen-v1.1'


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
            if negative_evidence_gap(checked[begin:end]):
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
    if re.search(r'\d', text):
        result = numeric_checks().ground_text(text, evidence)
        if result['status'] not in {'grounded', 'no_numbers'}:
            found.append('unsupported_or_transferred_number')
    # Check factual clauses separately: a later 'could' must not excuse an
    # unsupported first sentence. Assumptions are not a loophole for assertions.
    checker = numeric_checks()
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if negative_evidence_gap(sentence):
            continue
        if kind == 'action' and not re.search(
                r'\b(?:because|since|given|already|proven|demonstrated|showed|found|achieved|guaranteed)\b', sentence, re.I):
            # A decision question ('decide when checks are justified') is not
            # an asserted finding. Numbers and dangerous claims were checked above.
            continue
        actual_kind = ('limitation' if kind == 'assumption' and checker.CAVEAT.search(sentence)
                       else 'implication' if kind == 'assumption' else kind)
        _, premise = checker.advice_issues(sentence, evidence, [], actual_kind)
        # The older screen treats any mention of savings as a claim, including
        # 'without establishing savings'. Assertion checks above replace those
        # keyword rules; keep its factual/setting/premise checks.
        found.extend(p for p in premise if p not in {
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
            if not labeled and not negative_evidence_gap(text) and len(words(text) & words(' '.join(by_id.values()))) < 2:
                problems.append('unanchored_risk_or_limit')
            trace.append({'field': field, 'status': 'withheld' if problems else 'kept_unverified',
                          'issues': sorted(set(problems))})
            if not problems and text not in safe:
                safe.append(text)
        result[field] = safe
    if not kept:
        result['status'] = 'insufficient_evidence'
        result['limitations'] = list(dict.fromkeys([*result['limitations'],
            'No sufficiently specific business implication passed the evidence and advice checks.']))
    return result, trace

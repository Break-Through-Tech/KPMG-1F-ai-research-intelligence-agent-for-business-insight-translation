"""Deterministic numerical grounding for research claims and business advice (v2: verification-repair).

v2 = the frozen experiments/agentic/numeric_checks.py plus seven parsing corrections, each tied to false
rejections in business-multiagent-v1 (development data). See experiments/verification-repair/FINDINGS.md.
  R1 attribution: subject_mismatch needs an explicit, different named subject in BOTH numbers' own clauses;
     an inherited (elliptical) subject can only make a number uncertain. Names compare by alias
     ("Claude" ~ "Claude 3.5 Sonnet", "KG2RAG" ~ "KG 2 RAG"); figure/table labels and metric names are not subjects.
  R2 metrics: "F1 score"/"F1-score" is F1; the generic "score" never contradicts a specific metric; a metric
     AFTER a number counts only inside that number's own clause.
  R3 emphatic "only" ("only dropped from 66.8% to 60.0%") is not a scope condition; "only on X" still is.
  R4 a version or size inside a model name ("Claude 3.5 Sonnet", "Llama Pro Finance 70B") and a "Table 1" label
     are names, not measurements, when the same name appears in the cited quotes or passages.
  R5 table header units: "Mean Latency (s): 10.39" is 10.39 seconds.
  R6 ratios: "37/100" is grounded when 100 is the source's stated base ("54 of the 100 indicators") and 37 is
     grounded; "precision/recall of 43.0/70.3" is a pair of values, each still checked, not a ratio.
  R7 superscripts are read as digits ("KG²RAG" = "KG2RAG").
  R8 "7.9% and 6.9% on HotpotQA and Shuffle-HotpotQA, respectively": each number takes its listed subject.
Everything else is unchanged: values, units, signs, negation, settings, populations, conditions, direction,
ranges, and the statistical-report rule (via statistical_reports.enable()).


Each number in a claim is compared with the numbers in its cited quotes as a structured mention:
value and explicit sign, unit class, the subject it is attached to (a named system, model or
dataset that both texts mention), the metric it measures, and its surrounding words. Paired
numbers ("from A to B", "A higher than B", "A of B") are checked for order and direction, and a
condition the quote states ("only on X") must be kept unchanged.

Every claim gets one of three states:
- ``contradicted``: code can show the claim misstates its evidence (absent value, flipped sign,
  different unit, number attached to another subject or metric, reversed direction, wrong
  denominator, changed range, or dropped or changed measurement condition). The claim is held
  whatever any model says.
- ``uncertain``: the numbers are present but code cannot establish what they refer to (no shared
  subject, metric or context, or a source qualifier with no measurement in the claim). The claim is not
  held by code; it still needs the independent verification agent AND is flagged for the person.
- ``grounded`` (or ``no_numbers``): every number matched in value, unit and context.

These are surface checks. They do not establish that a claim's meaning matches its source; that
remains the verifier's and, finally, a person's judgment.
"""
import re
from decimal import Decimal, InvalidOperation

NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
_NUM = re.compile(rf'(?<![\w.]){NUMBER}')
# Keep version digits in named identifiers for subject matching, outside measurement parsing.
_IDENTIFIER = re.compile(
    r'\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*-\d+(?:\.\d+)?[A-Za-z]*(?:-[A-Za-z0-9]+)*\b'
    r'(?!-\w|\.\d|\s*%)')
SIGN_CHARS = '+-−'
_UNIT_AFTER = [
    ('pp', re.compile(r'^\s*(?:pp\b|p\.p\.|percentage[- ]points?\b)', re.I)),
    ('percent', re.compile(r'^\s*(?:%|percent\b|per\s+cent\b)', re.I)),
    ('times', re.compile(r'^\s*(?:x\b|×|times\b|-?fold\b)', re.I)),
    ('ms', re.compile(r'^\s*(?:ms\b|milliseconds?\b)', re.I)),
    ('seconds', re.compile(r'^\s*(?:s\b|sec\b|secs\b|seconds?\b)', re.I)),
    ('minutes', re.compile(r'^\s*(?:min\b|mins\b|minutes?\b)', re.I)),
    ('hours', re.compile(r'^\s*(?:h\b|hrs?\b|hours?\b)', re.I)),
    ('thousand', re.compile(r'^\s*(?:k\b|thousand\b)', re.I)),
    ('million', re.compile(r'^\s*(?:m\b|mn\b|million\b)', re.I)),
    ('billion', re.compile(r'^\s*(?:b\b|bn\b|billion\b)', re.I)),
]
_CURRENCY_BEFORE = re.compile(r'(?:\$|US\$|USD\s?|€|EUR\s?|£|GBP\s?)$', re.I)
# Metrics and which direction is better. Longer phrases first.
METRICS = [
    ('unsupported-claim rate', 'lower'), ('unsupported claim rate', 'lower'), ('hallucination rate', 'lower'),
    ('error rate', 'lower'), ('failure rate', 'lower'), ('success rate', 'higher'), ('win rate', 'higher'),
    ('exact match', 'higher'), ('pass@1', 'higher'), ('f1-score', 'higher'), ('f1 score', 'higher'), ('f1', 'higher'), ('accuracy', 'higher'), ('agreement', 'higher'),
    ('precision', 'higher'), ('recall', 'higher'), ('auc', 'higher'), ('bleu', 'higher'), ('rouge', 'higher'),
    ('throughput', 'higher'), ('latency', 'lower'), ('runtime', 'lower'), ('cost', 'lower'), ('loss', 'lower'),
    ('perplexity', 'lower'), ('hallucinations', 'lower'), ('errors', 'lower'), ('error', 'lower'), ('score', None),
]
_METRIC_RE = re.compile(r'\b(' + '|'.join(re.escape(name) for name, _ in METRICS) + r')\b', re.I)
POLARITY = dict(METRICS)
METRIC_ALIAS = {'f1-score': 'f1', 'f1 score': 'f1'}
REFERENCE = re.compile(r'^(?:fig(?:ure)?s?|tables?|sections?|appendix|appendices|eq(?:uation)?s?|algorithms?)\.?$', re.I)
LABEL = re.compile(r'\b(?:Table|Figure|Fig\.|Section|Appendix|Eq\.|Equation|Algorithm)\s*\d+(?:\.\d+)?\b')
HEADER_UNIT = re.compile(r'\((%|s|sec|secs|seconds|ms|min|mins|h|hrs?)\)\s*:\s*$', re.I)
HEADER_UNIT_NAME = {'%': 'percent', 's': 'seconds', 'sec': 'seconds', 'secs': 'seconds', 'seconds': 'seconds', 'ms': 'ms',
                    'min': 'minutes', 'mins': 'minutes', 'h': 'hours', 'hr': 'hours', 'hrs': 'hours'}
# 'only dropped', 'only slightly': emphasis on a change, not a scope condition ('only on Books' still is).
EMPHATIC_ONLY = re.compile(r'^(?:slightly|marginally|modestly|somewhat|dropp\w*|decreas\w*|declin\w*|fell|fall\w*|ros[ei]\w*|'
                           r'increas\w*|improv\w*|reduc\w*|chang\w*|lost|los[es]\w*|gain\w*|mov\w*|shift\w*)$', re.I)
_NAME_TEXT = ''   # letters+digits of the cited quotes and passages, set per ground_text call (R4)
_CONTEXT = ()     # cited passage texts, set by ground_claim (names and labels only, never values)
UP = re.compile(r'\b(?:increas\w*|ris(?:e|es|ing)|rose|gr[eo]w\w*|climb\w*|jump\w*|higher|up)\b', re.I)
DOWN = re.compile(r'\b(?:decreas\w*|reduc\w*|fell|fall\w*|drop\w*|declin\w*|lower(?:ed|s)?|cut|shr[ai]nk\w*|down)\b', re.I)
BETTER = re.compile(r'\b(?:improv\w*|better)\b', re.I)
WORSE = re.compile(r'\b(?:worse\w*|worsen\w*|degrad\w*|deteriorat\w*)\b', re.I)
FROM_TO = re.compile(rf'\bfrom\s+(?:about\s+|roughly\s+|approximately\s+|around\s+)?([+\-−]?{NUMBER})\s*(?:%|[a-z]+(?:[- ][a-z]+)?)?\s*to\s+([+\-−]?{NUMBER})', re.I)
_ENDPOINT = rf'[+\-−]?{NUMBER}'
_INTERVAL_CHANGE = re.compile(
    rf'\bfrom\s+({_ENDPOINT})(?:\s*[-–—]\s*({_ENDPOINT}))?\s*%\s+to\s+'
    rf'({_ENDPOINT})(?:\s*[-–—]\s*({_ENDPOINT}))?\s*%', re.I)
COMPARATIVE = re.compile(rf'({NUMBER})\s*(?:%|percent)?[\s,;:]*(?:[\w-]+[\s,]+){{0,3}}?\b(higher|greater|more|larger|above|lower|less|fewer|smaller|below|better|worse)\s+than\s+(?:[\w-]+\s+){{0,3}}?({NUMBER})', re.I)
RATIO = re.compile(rf'({NUMBER})\s*(?:out\s+of|of|/)\s*({NUMBER})\b', re.I)
RATIO_SOURCE = re.compile(rf'({NUMBER})\s*(?:out\s+of|of|/)\s*(?:the\s+|all\s+)?({NUMBER})\b', re.I)
QUALIFIER = re.compile(r'\b(only|except|excluding|unless|limited\s+to|restricted\s+to)\b\s+((?:[\w%.\-/]+\s+){0,5}[\w%.\-/]+)', re.I)
ENTITY = re.compile(r'\b[A-Z][A-Za-z0-9]*(?:[-.@][A-Za-z0-9]+)*(?:\s+[A-Z0-9][A-Za-z0-9]*(?:[-.][A-Za-z0-9]+)*)*')
STOP = set('''a an the and or but of in on at to for from with by as is are was were be been being this that these those it its
their there here than then so such into over under after before during between about across per via vs versus while whereas
when which who whom whose what where how also only not no can may might could would should will has have had do does did
reached reports reported report shows showed show found finds achieves achieved compared using used use one two three'''.split())
METRIC_REACH = 40  # characters: a metric further from its number is not taken as what the number measures
POPULATION = re.compile(r'\s*(?:%|percent\b|per\s+cent\b)?\s+of\s+(?:the\s+|all\s+|its\s+|their\s+)?((?:[A-Za-z][A-Za-z\-]+\s+){0,2}[A-Za-z][A-Za-z\-]+)', re.I)
# Standard conversions: (dimension, factor to the base unit). Units absent here compare by name only.
CONVERSIONS = {'ms': ('time', Decimal('0.001')), 'seconds': ('time', Decimal(1)), 'minutes': ('time', Decimal(60)),
               'hours': ('time', Decimal(3600)), 'thousand': ('count', Decimal(1000)), 'million': ('count', Decimal(10) ** 6),
               'billion': ('count', Decimal(10) ** 9), 'currency': ('currency', Decimal(1)),
               'currency+thousand': ('currency', Decimal(1000)), 'currency+million': ('currency', Decimal(10) ** 6),
               'currency+billion': ('currency', Decimal(10) ** 9)}
# A negation attached to the statement of a number ("did not reach 78%"). "not only" is not a negation.
NEGATION = re.compile(r"\b(?:not(?!\s+only)|never|no|cannot|can't|didn't|doesn't|don't|isn't|wasn't|aren't|weren't|won't|failed\s+to|fails\s+to|without)\b", re.I)
NEGATION_REACH = 40
# Condition contrasts must be established by the cited source. The phrase ends
# at a header separator, clause boundary, or reporting verb.
_CONDITION_EDGE = r'and|while|whereas|but|was|were|is|are|had|has|achieved|reached|reported'
CONDITION_PHRASE = re.compile(
    rf'\b(with(?:out)?)\s+([a-z][\w-]*(?:\s+(?!(?:{_CONDITION_EDGE})\b)[a-z][\w-]*){{0,3}})'
    rf'(?:\s+\(([a-z][a-z0-9-]*)\))?(?=\s*(?:$|[,:;.!?]|\b(?:{_CONDITION_EDGE})\b))', re.I
)
# Measurement settings. A result measured in an evaluation setting is not a result in deployment.
EVALUATION_SETTING = re.compile(r'\b(?:benchmarks?|datasets?|test\s+sets?|held-out|leaderboards?|simulat\w*|synthetic|sandbox\w*|lab(?:oratory)?|offline\s+evaluation)\b', re.I)
DEPLOYMENT_SETTING = re.compile(r'\b(?:clinical|clinics?|hospitals?|patients?|production|deploy\w*|real[- ]world|in\s+the\s+field|field\s+trials?|customers?|in\s+practice|live\s+(?:use|traffic|systems?))\b', re.I)
SENTENCE = re.compile(r'(?<=[;!?])\s+|(?<=\.)\s+(?=[A-Z(])')


def _decimal(text):
    try:
        return Decimal(text.replace(',', '').replace('−', '-'))
    except InvalidOperation:
        return None


SUPERSCRIPTS = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')


def _norm(text):
    return re.sub(r'\s+', ' ', (text or '').translate(SUPERSCRIPTS)).strip()


def _alnum(text):
    return re.sub(r'[^0-9a-z]', '', (text or '').translate(SUPERSCRIPTS).casefold())


def _same_entity(a, b):
    """Same named subject: equal letters and digits, or a digit-free family name that prefixes the other
    ('Claude' ~ 'Claude 3.5 Sonnet'). 'GPT-4' vs 'GPT-4o' and 'Llama-2-7B' vs 'Llama-3-8B' stay different."""
    x, y = _alnum(a), _alnum(b)
    if x == y:
        return True
    short, long_ = sorted((x, y), key=len)
    return len(short) >= 2 and not re.search(r'\d', short) and long_.startswith(short)


def _stem(word):
    return word.lower().strip('.,;:()[]"\'')[:5]


def _content(text):
    return {_stem(w) for w in re.findall(r"[A-Za-z][A-Za-z\-']+", text or '') if w.lower() not in STOP and len(w) > 2}


def _sentences(text):
    out, start = [], 0
    for match in SENTENCE.finditer(text):
        out.append((start, match.start()))
        start = match.end()
    out.append((start, len(text)))
    return out


def _condition_name(match):
    words = re.findall(r'[a-z0-9]+', match[2].lower())
    alias = match[3]
    if alias and alias.lower() == ''.join(word[0] for word in words):
        return alias.lower()
    return ' '.join(words)


def _condition_labels(sources):
    labels = set()
    modes = {}
    for source in sources:
        for match in CONDITION_PHRASE.finditer(source):
            name = _condition_name(match)
            modes.setdefault(name, set()).add(match[1].lower())
            if source[match.end():].lstrip().startswith(':'):
                labels.add(name)
    labels.update(name for name, options in modes.items() if options == {'with', 'without'})
    return labels


def _labelled_conditions(text, labels):
    return [(match, _condition_name(match)) for match in CONDITION_PHRASE.finditer(text)
            if _condition_name(match) in labels]


def _name_digits(text, begin, end):
    """Digit spans that belong to a model or system name present in the cited text (R4): a size or version glued
    to letters ('70B') or followed by a capitalised word inside the name ('Claude 3.5 Sonnet'), plus 'Table 1'
    labels. Never a whole entity, so 'Llama 70B 58.3' still measures 58.3."""
    spans = []
    if not _NAME_TEXT:
        return spans
    for entity in ENTITY.finditer(text, begin, end):
        name = entity.group(0)
        words = name.split()
        if not re.search(r'\d', name) or _METRIC_RE.fullmatch(words[0]) or REFERENCE.match(words[0]):
            continue
        if _alnum(name) not in _NAME_TEXT:
            continue
        for number in _NUM.finditer(text, entity.start(), entity.end()):
            after = text[number.end():entity.end()]
            if re.match(r'[A-Za-z]', after) or (re.match(r'\s+[A-Z][a-z]+\b', after)
                                                  and not _METRIC_RE.match(after.strip())):
                spans.append((number.start(), number.end()))
    for label in LABEL.finditer(text, begin, end):
        if _alnum(label.group()) in _NAME_TEXT:
            spans.append((label.start(), label.end()))
    return spans


def _measurements(text, begin, end, source_identifiers):
    identifiers = [(m.start(), m.end()) for m in _IDENTIFIER.finditer(text, begin, end)
                   if m.group().casefold() in source_identifiers]
    identifiers += _name_digits(text, begin, end)
    return [m for m in _NUM.finditer(text, begin, end)
            if not any(s <= m.start() < e for s, e in identifiers)]


def _mentions(text, shared_entities, condition_labels=(), source_identifiers=()):
    """Structured numeric mentions: value, explicit sign, unit, subject, metric, nearby words."""
    mentions = []
    entity_spans = [(m.start(), m.end(), m.group(0)) for m in ENTITY.finditer(text) if _counts_as_subject(m.group(0), shared_entities)]
    metric_spans = [(m.start(), m.end(), METRIC_ALIAS.get(m.group(1).lower(), m.group(1).lower())) for m in _METRIC_RE.finditer(text)]
    for begin, end in _sentences(text):
        marked = _labelled_conditions(text[begin:end], condition_labels)
        logical = list(text[begin:end])
        for phrase, _label in marked:
            logical[phrase.start(1):phrase.end(1)] = ' ' * len(phrase[1])
        logical = ''.join(logical)
        measurements = _measurements(text, begin, end, source_identifiers)
        respective = {}
        if re.search(r'\brespectively\b', text[begin:end], re.I) and measurements:
            listed = [name for s, e, name in entity_spans if s >= measurements[-1].end() and e <= end]
            if len(listed) == len(measurements):
                respective = {m.start(): [name] for m, name in zip(measurements, listed)}
        for match in measurements:
            value = _decimal(match.group())
            if value is None:
                continue
            sign = None
            before_index = match.start() - 1
            if before_index >= 0 and text[before_index] in SIGN_CHARS and (before_index == 0 or not text[before_index - 1].isalnum()):
                sign = '-' if text[before_index] in '-−' else '+'
            after = text[match.end():match.end() + 24]
            unit = next((name for name, pattern in _UNIT_AFTER if pattern.match(after)), None)
            if _CURRENCY_BEFORE.search(text[max(0, match.start() - 5):match.start() - (1 if sign else 0)]):
                unit = f'currency+{unit}' if unit else 'currency'
            if unit is None:
                header = HEADER_UNIT.search(text[max(begin, match.start() - 16):match.start()])
                if header:
                    unit = HEADER_UNIT_NAME[header.group(1).lower()]  # R5

            own_left, own_right = _clause_bounds(text, begin, end, match.start(), match.end())

            def nearest(spans, reach=None):
                # R2: a metric after the number stays in its clause; a metric before it must not already belong to
                # another number in between ("F1 40.6 and 9.58 seconds": 9.58 is not F1).
                inside = [(min(abs(s - match.end()), abs(e - match.start())), name) for s, e, name in spans
                          if begin <= s < end and not (s <= match.start() < e)
                          and ((s < match.start() and not any(e <= n.start() < match.start() for n in measurements))
                               or (s >= match.end() and s < own_right))]
                inside = [item for item in inside if reach is None or item[0] <= reach]
                return min(inside)[1] if inside else None
            words = text[max(begin, match.start() - 60):min(end, match.end() + 60)]
            # "78% of hospitals": the population the proportion is of. Must match the evidence's population.
            population = POPULATION.match(text, match.end())
            scope = _scope(text, begin, end, match, measurements)
            clause = scope['own']
            left = scope['clause_start'] - begin
            right = left + len(clause)
            conditions = {(name, phrase[1].lower()) for phrase, name in marked if left <= phrase.start() < right}
            if not conditions:
                conditions = {(name, phrase[1].lower())
                              for phrase, name in _labelled_conditions(scope['shared'], condition_labels)}
            in_own = EVALUATION_SETTING.search(clause), DEPLOYMENT_SETTING.search(clause)
            setting_text = clause if any(in_own) else scope['shared']
            lead = logical[max(0, match.start() - begin - NEGATION_REACH):match.start() - begin]
            # Sign and negation cues are read in the number's OWN clause, so "X fell 3.2%, while Y rose 3.2%"
            # gives each number its own direction.
            up, down = bool(UP.search(clause)), bool(DOWN.search(clause))
            conversion = CONVERSIONS.get(unit)
            metric = nearest(metric_spans, METRIC_REACH)
            if metric is None:
                # "78% of minors under 18 reported fewer errors": the only metric in the number's clause.
                in_clause = {METRIC_ALIAS.get(m.group(1).lower(), m.group(1).lower()) for m in _METRIC_RE.finditer(clause)}
                metric = in_clause.pop() if len(in_clause) == 1 else None
            mentions.append({'value': value, 'sign': sign, 'unit': unit, 'subject': _clause_subject(text, begin, end, match, entity_spans),
                             # R1: subjects named in this number's own clause (empty when only inherited);
                             # R8: in "7.9% and 6.9% on A and B, respectively" each number takes its listed subject.
                             'own_subjects': respective.get(match.start(),
                                                            [name for s, e, name in entity_spans if own_left <= s and e <= own_right]),
                             'metric': metric, 'context': _content(words), 'sentence': (begin, end),
                             'population': _population(population.group(1)) if population else None, 'text': match.group(),
                             # Read as negative: an explicit minus, or no sign with only a "down" word in its sentence.
                             'negative': sign == '-' or (sign is None and down and not up),
                             'canonical': (conversion[0], value * conversion[1]) if conversion else None,
                             'negated_here': bool(NEGATION.search(lead)),
                             'sentence_negated': bool(NEGATION.search(logical[left:right])),
                             'conditions': conditions,
                             # Setting of THIS number: its own clause, else clearly shared context; never a neighbour's clause.
                             'evaluation': bool(EVALUATION_SETTING.search(setting_text)),
                             'deployment': bool(DEPLOYMENT_SETTING.search(setting_text)),
                             'setting_ambiguous': not any(in_own) and bool(EVALUATION_SETTING.search(scope['ambiguous'])
                                                                           or DEPLOYMENT_SETTING.search(scope['ambiguous'])),
                             # Conditions that apply to THIS number, and conditions whose scope is ambiguous.
                             'qualifiers': _qualifiers(clause) + _qualifiers(scope['shared']),
                             'ambiguous_qualifiers': _qualifiers(scope['ambiguous']),
                             'groups': _groups(clause)})
    return mentions


CLAUSE_BREAK = re.compile(r',|;|:|\band\b|\bwhile\b|\bwhereas\b|\bbut\b|\bversus\b|\bvs\.?|\bcompared\s+with\b', re.I)


POPULATION_STOP = re.compile(r'^(?:reported|reports|adopted|adopts|used|uses|saw|sees|showed|shows|had|have|has|were|was|are|is|'
                             r'achieved|reached|experienced|said|agreed|received|completed|failed|passed|preferred|chose)$', re.I)


def _population(phrase):
    """Content stems of "x% of <population>", stopping at the verb that follows ("hospitals reported ..." -> hospitals)."""
    words = []
    for word in phrase.split():
        if POPULATION_STOP.match(word):
            break
        words.append(word)
    return _content(' '.join(words)) or None


# Population groups whose members exclude each other. "under 18" names a minor; "pediatric" excludes "adult".
GROUPS = {
    'age': [('minor', re.compile(r'\b(?:pediatric|paediatric|child(?:ren)?|kids?|minors?|adolescents?|teen(?:s|agers?)?|infants?|neonat\w*|newborns?|youths?)\b'
                                 r'|\b(?:under|below|younger\s+than)\s+(?:the\s+)?(?:age\s+(?:of\s+)?)?(?:1[0-7]|18)\b|\bunder-18\b', re.I)),
            ('adult', re.compile(r'\b(?:adults?|elderly|older\s+adults|seniors?|geriatric)\b'
                                 r'|\b(?:over|above|older\s+than)\s+(?:the\s+)?(?:age\s+(?:of\s+)?)?(?:18|21|65)\b', re.I))],
    'sex': [('male', re.compile(r'\b(?:male|males|men|boys?)\b', re.I)), ('female', re.compile(r'\b(?:female|females|women|girls?)\b', re.I))],
    'care': [('inpatient', re.compile(r'\binpatients?\b', re.I)), ('outpatient', re.compile(r'\boutpatients?\b', re.I))],
}


MODEL_NAME = re.compile(r'\d|[a-z][A-Z]|-[A-Za-z0-9]')


def _counts_as_subject(name, shared_entities):
    """A named subject: one both texts mention, or a source-side name of the same kind ("Model Y" beside the claim's
    "Model X") or that looks like a system name ("GPT-4", "Qwen3", "DeepSeek-R1"), so a number attributed to ANOTHER
    system is recognized as such instead of looking unattributed."""
    words = name.split()
    if not words or REFERENCE.match(words[0]) or _METRIC_RE.fullmatch(words[0]) or _METRIC_RE.fullmatch(name):
        return False  # R1: 'Figure 5', 'Table 1', 'F1-score', 'F1 44.1' are not subjects
    if name in shared_entities:
        return True
    if words[0].lower() in STOP:
        return False
    heads = {entity.split()[0] for entity in shared_entities}
    return (len(words) > 1 and words[0] in heads) or bool(MODEL_NAME.search(name))


def _groups(text):
    found = {}
    for dimension, options in GROUPS.items():
        names = {name for name, pattern in options if pattern.search(text)}
        if names:
            found[dimension] = names
    return found


def _breaks(text, begin, end):
    """Clause boundaries in a sentence. A colon labels ("Model X: 78%") and a comma inside a number ("1,240") are not breaks."""
    out = []
    for m in CLAUSE_BREAK.finditer(text, begin, end):
        if m.group(0) == ':':
            continue
        if m.group(0) == ',' and 0 < m.start() < len(text) - 1 and text[m.start() - 1].isdigit() and text[m.start() + 1].isdigit():
            continue
        out.append(m.start())
    return out


def _clause_bounds(text, begin, end, position_start, position_end):
    breaks = _breaks(text, begin, end)
    left = max([b for b in breaks if b < position_start], default=begin)
    right = min([b for b in breaks if b >= position_end], default=end)
    return left, right


def _clause_text(text, begin, end, match):
    left, right = _clause_bounds(text, begin, end, match.start(), match.end())
    return text[left:right]


def _scope(text, begin, end, match, measurements):
    """What applies to ONE number: its own clause, plus shared context only where the scope is clear.

    - A number-free clause BEFORE the first number ("On the benchmark, X reached 78% and Y 64%") applies to all.
    - A number-free clause AFTER the last number applies when the sentence has one number; with several numbers
      its scope is ambiguous (returned separately, so the caller can say "uncertain" instead of guessing).
    - An elliptical clause ("..., and 64% accuracy in hospitals") inherits the earlier SUBJECT only; its own
      setting and conditions stay its own, never borrowed from the neighbouring number's clause.
    """
    breaks = _breaks(text, begin, end)
    edges = [begin] + breaks + [end]
    segments = list(zip(edges[:-1], edges[1:]))
    numbers = [m.start() for m in measurements]
    has_number = [any(s <= n < e for n in numbers) for s, e in segments]
    first = next((i for i, h in enumerate(has_number) if h), len(segments))
    last = max((i for i, h in enumerate(has_number) if h), default=-1)
    pre = ' '.join(text[s:e] for (s, e), h in zip(segments[:first], has_number[:first]) if not h)
    post = ' '.join(text[s:e] for (s, e), h in zip(segments[last + 1:], has_number[last + 1:]) if not h)
    left, right = _clause_bounds(text, begin, end, match.start(), match.end())
    own = text[left:right]
    single = len(numbers) == 1
    return {'own': own, 'shared': ' '.join(x for x in (pre, post if single else '') if x),
            'ambiguous': '' if single else post, 'elliptical': not _content(text[left:match.start()]),
            'clause_start': left}


def _qualifiers(text):
    """(keyword, required object stems) for each condition stated in ``text``."""
    found = []
    for match in QUALIFIER.finditer(text):
        if match.group(1).lower() == 'only' and (EMPHATIC_ONLY.match(match.group(2).split()[0])
                                                 or re.search(r'\bnot\s+$', text[:match.start()], re.I)):
            continue  # R3: emphatic "only dropped" and "not only ... but also" are not scope conditions
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-']+", match.group(2)) if w.lower() not in STOP][:3]
        required = {_stem(w) for w in words}
        if required:
            found.append((match.group(1).lower().split()[0], required))
    return found


def _clause_subject(text, begin, end, match, entity_spans):
    """The named subject of a number: the last shared entity before it in its clause, else the first after it.

    "Model X reached 64.5% and Model Y reached 78.0%" -> 64.5 belongs to Model X, 78.0 to Model Y.
    "higher than 64.5% for Model Y" -> 64.5 belongs to Model Y. A colon ends a label: "Model X: 78.0%".
    """
    left, right = _clause_bounds(text, begin, end, match.start(), match.end())
    before = [name for s, e, name in entity_spans if left <= s and e <= match.start()]
    if before:
        return before[-1]
    if not _content(text[left:match.start()]):
        # Elliptical clause ("Model X reached 78% ... and 64% ..."): the subject named earlier in the sentence.
        earlier = [name for s, e, name in entity_spans if begin <= s and e <= left]
        if earlier:
            return earlier[-1]
    after = [name for s, e, name in entity_spans if s >= match.end() and e <= right]
    return after[0] if after else None


def _shared_entities(claim_text, sources):
    joined = ' '.join(sources)
    found = set()
    for match in ENTITY.finditer(claim_text):
        name = match.group(0)
        if name.lower() in STOP or _METRIC_RE.fullmatch(name) or name.split()[0].lower() in STOP:
            continue
        if re.search(rf'(?<![\w]){re.escape(name)}(?![\w])', joined):
            found.add(name)
    return found


def _compatible_unit(claim_unit, source_unit, percent_context):
    if claim_unit is None or claim_unit == source_unit:
        return True
    # A bare table cell ("Accuracy (%): 78.0") may carry its percent unit in the header or caption.
    return claim_unit == 'percent' and source_unit is None and percent_context


def _same_quantity(mention, candidate):
    if abs(candidate['value']) == abs(mention['value']):
        return True
    # 0.5 seconds == 500 milliseconds; $2 million == $2,000,000.
    return (mention['canonical'] is not None and candidate['canonical'] is not None
            and mention['canonical'][0] == candidate['canonical'][0]
            and abs(mention['canonical'][1]) == abs(candidate['canonical'][1]))


def _compatible(mention, candidate, percent_context):
    if mention['canonical'] is not None and candidate['canonical'] is not None:
        # Same dimension AND the same quantity after conversion: 3 ms is not 3 s, 0.5 s is 500 ms.
        return (mention['canonical'][0] == candidate['canonical'][0]
                and abs(mention['canonical'][1]) == abs(candidate['canonical'][1]))
    return _compatible_unit(mention['unit'], candidate['unit'], percent_context)


def _judge(mention, c, percent_context):
    """Judge ONE source mention. Sign, negation, setting, population, subject and metric must all hold for
    this same mention; nothing is borrowed from another number in the source."""
    if not _compatible(mention, c, percent_context):
        return 'contradicted', ['unit_mismatch']
    # Sign, as read: "3.2%" (no minus, no "down" word) is not "-3.2%"; "decreased by 3.2%" is.
    if (mention['sign'] or c['sign']) and c['negative'] != mention['negative']:
        return 'contradicted', ['sign_flip']
    # Negation attached to either number is explicit: "did not reach 78%" vs "reached 78%", in either direction.
    if mention['negated_here'] != c['negated_here'] and (mention['negated_here'] or c['negated_here']):
        return 'contradicted', ['negation_mismatch']
    if mention['sentence_negated'] != c['sentence_negated']:
        return 'uncertain', ['negation_unconfirmed']
    # Setting: a benchmark or simulation result stated as a deployment, clinical or real-world result.
    if mention['deployment'] and not c['deployment']:
        return ('contradicted', ['setting_transfer']) if c['evaluation'] else ('uncertain', ['setting_unconfirmed'])
    # The reverse: a result measured in deployment or with patients restated as a benchmark or simulation result.
    if mention['evaluation'] and not mention['deployment'] and c['deployment'] and not c['evaluation']:
        return 'contradicted', ['setting_mismatch']
    uncertain = []
    claim_conditions = mention['conditions']
    source_conditions = c['conditions']
    if any(len(conditions) > len({name for name, _mode in conditions})
           for conditions in (claim_conditions, source_conditions)):
        uncertain.append('condition_unconfirmed')
    for name, mode in claim_conditions:
        competing = 'without' if mode == 'with' else 'with'
        if (name, competing) in source_conditions and (name, mode) not in source_conditions:
            return 'contradicted', ['condition_mismatch']
    if claim_conditions != source_conditions:
        uncertain.append('condition_unconfirmed')
    # Conditions of the matched source number must be kept by the claim; a condition of ANOTHER number is irrelevant.
    claim_words, claim_lower = mention.get('claim_words', set()), mention.get('claim_lower', '')
    for keyword, required in c['qualifiers']:
        if not required <= claim_words:
            return 'contradicted', ['changed_condition' if re.search(rf'\b{re.escape(keyword)}\b', claim_lower) else 'missing_condition']
    for keyword, required in c['ambiguous_qualifiers']:
        if not required <= claim_words:
            uncertain.append('condition_scope_unconfirmed')
    if mention['deployment'] and not c['deployment'] and c['setting_ambiguous']:
        uncertain.append('setting_unconfirmed')
    # Population groups that exclude each other (pediatric vs adult, men vs women, inpatient vs outpatient).
    group_ok = False
    for dimension, names in mention['groups'].items():
        source = c['groups'].get(dimension)
        if source and not (names & source):
            return 'contradicted', ['population_mismatch']
        if source:
            group_ok = True
        else:
            uncertain.append('population_unconfirmed')
    if mention['population'] and not group_ok:
        # A paraphrase is accepted when the claim's population words appear around the source number, or when
        # both name the same population group ("minors under 18" vs "participants under 18").
        if not mention['population'] & ((c['population'] or set()) | c['context']):
            uncertain.append('population_unconfirmed')
    subject_ok = metric_ok = False
    mine, theirs = mention.get('own_subjects') or [], c.get('own_subjects') or []
    if mine and theirs:
        # R1: both numbers name a subject in their own clause; a contradiction must be explicit on both sides.
        if any(_same_entity(a, b) for a in mine for b in theirs):
            subject_ok = True
        else:
            return 'contradicted', ['subject_mismatch']
    elif mention['subject']:
        if c['subject'] and _same_entity(c['subject'], mention['subject']):
            subject_ok = True
        else:
            uncertain.append('subject_unconfirmed')
    if mention['metric']:
        if c['metric'] and (c['metric'] == mention['metric'] or (POLARITY.get(c['metric'], 0) == POLARITY.get(mention['metric'], 1)
                                                                 and c['metric'].startswith(mention['metric'][:4]))):
            metric_ok = True
        elif c['metric'] and 'score' not in (c['metric'], mention['metric']):
            return 'contradicted', ['metric_mismatch']
        else:
            uncertain.append('metric_unconfirmed')  # R2: the generic 'score' cannot contradict a specific metric
    if not subject_ok and not metric_ok and not (mention['context'] & c['context']):
        uncertain.append('context_unconfirmed')
    return ('uncertain', sorted(set(uncertain))) if uncertain else ('grounded', [])


def _match_mention(mention, sources, percent_context):
    """Return (status, issues) for one claim mention from the BEST single source mention.

    Grounded if one source mention supports every property; else uncertain if one could; else contradicted
    with the reasons each same-valued source mention fails. Mentions are never combined.
    """
    candidates = [m for m in sources if _same_quantity(mention, m)]
    if not candidates:
        return 'contradicted', ['numbers_absent']
    verdicts = [_judge(mention, c, percent_context) for c in candidates]
    for wanted in ('grounded', 'uncertain'):
        found = [issues for status, issues in verdicts if status == wanted]
        if found:
            return wanted, sorted({issue for issues in found for issue in issues})
    return 'contradicted', sorted({issue for _status, issues in verdicts for issue in issues})


def _pairs(text):
    return [(_decimal(a), _decimal(b), m.start(), m.end()) for m in FROM_TO.finditer(text) for a, b in [m.groups()]]


def _clause_before(text, position):
    begin = max((s for s, e in _sentences(text) if s <= position), default=0)
    return text[begin:position + 1]


def _metric_polarity(text, start, end):
    window = text[max(0, start - 80):end + 40]
    found = [m.group(1).lower() for m in _METRIC_RE.finditer(window)]
    polarities = {POLARITY.get(name) for name in found} - {None}
    return polarities.pop() if len(polarities) == 1 else None


def _direction_issues(text, quoted):
    contradictions, uncertain = [], []
    quote_pairs = {(a, b) for a, b, _s, _e in _pairs(quoted)}
    for a, b, start, end in _pairs(text):
        if a is None or b is None or a == b:
            continue
        if (b, a) in quote_pairs and (a, b) not in quote_pairs:
            contradictions.append('reversed_comparison')
            continue
        clause = _clause_before(text, start) + text[start:end]
        up, down = bool(UP.search(clause)), bool(DOWN.search(clause))
        better, worse = bool(BETTER.search(clause)), bool(WORSE.search(clause))
        rising = b > a
        if up != down:
            if up and not rising or down and rising:
                contradictions.append('reversed_comparison')
        elif better != worse:
            polarity = _metric_polarity(text, start, end)
            if polarity is None:
                uncertain.append('direction_unconfirmed')
            elif (better and (rising if polarity == 'higher' else not rising)) or (worse and (not rising if polarity == 'higher' else rising)):
                pass
            else:
                contradictions.append('reversed_comparison')
    for match in COMPARATIVE.finditer(text):
        x, y, word = _decimal(match.group(1)), _decimal(match.group(3)), match.group(2).lower()
        if x is None or y is None or x == y:
            continue
        if word in {'better', 'worse'}:
            polarity = _metric_polarity(text, match.start(), match.end())
            if polarity is None:
                uncertain.append('direction_unconfirmed')
                continue
            bigger = (word == 'better') == (polarity == 'higher')
        else:
            bigger = word in {'higher', 'greater', 'more', 'larger', 'above'}
        if bigger and x < y or not bigger and x > y:
            contradictions.append('reversed_comparison')
    return contradictions, uncertain


def _interval_changes(text):
    """Extract ordered percentage operands only where the same scoped statement can be matched."""
    for begin, end in _sentences(text):
        sentence = text[begin:end]
        for m in _INTERVAL_CHANGE.finditer(sentence):
            lead = re.sub(r'\bimprov(?:es|ed)\b', 'improve', sentence[:m.start()].lower())
            tail = re.split(r',\s+yielding\b', sentence[m.end():].lower(), maxsplit=1)[0].rstrip(' .;!?')
            scope = (_norm(re.sub(r'[-–]', ' ', lead)), _norm(re.sub(r'[-–]', ' ', tail)))
            if _METRIC_RE.search(scope[0]):
                yield scope, tuple(_decimal(x) if x is not None else None for x in m.groups())


def _range_issues(text, sources):
    source_changes = {}
    for source in sources:
        for scope, values in _interval_changes(source):
            source_changes.setdefault(scope, set()).add(values)
    contradictions = []
    for scope, values in _interval_changes(text):
        matches = source_changes.get(scope, set())
        if len(matches) != 1:
            continue
        expected, = matches
        if (expected[1] is not None or expected[3] is not None) and values != expected:
            contradictions.append('range_binding_mismatch')
    return contradictions


def _condition_issues(text, quotes):
    issues = []
    claim_words = _content(text)
    lower = text.lower()
    for quote in quotes:
        for match in QUALIFIER.finditer(quote):
            keyword = match.group(1).lower().split()[0]
            if keyword == 'only' and (EMPHATIC_ONLY.match(match.group(2).split()[0])
                                      or re.search(r'\bnot\s+$', quote[:match.start()], re.I)):
                continue  # R3
            object_words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-']+", match.group(2)) if w.lower() not in STOP][:3]
            required = {_stem(w) for w in object_words}
            if not required or required <= claim_words:
                continue
            issues.append('changed_condition' if re.search(rf'\b{re.escape(keyword)}\b', lower) else 'missing_condition')
    return issues


def ground_text(text, sources):
    """Ground every number in ``text`` against ``sources`` (quotes or passage sentences).

    Returns {'status', 'contradictions', 'uncertain', 'mentions'}.
    """
    global _NAME_TEXT
    text = _norm(text)
    sources = [_norm(s) for s in sources if s]
    joined = ' \n '.join(sources)
    _NAME_TEXT = _alnum(joined + ' ' + ' '.join(_CONTEXT))
    shared = _shared_entities(text, sources)
    labels = _condition_labels(sources)
    identifiers = {m.group().casefold() for m in _IDENTIFIER.finditer(joined)}
    claim_mentions = _mentions(text, shared, labels, identifiers)
    for mention in claim_mentions:
        mention['claim_words'], mention['claim_lower'] = _content(text), text.lower()
    source_mentions = [m for source in sources for m in _mentions(source, shared, labels, identifiers)]
    percent_context = bool(re.search(r'%|percent', joined, re.I))
    contradictions, uncertain, details = [], [], []
    present = set()  # values matched without contradiction (grounded or uncertain), for R6
    for mention in claim_mentions:
        status, issues = _match_mention(mention, source_mentions, percent_context)
        if status != 'contradicted':
            present.add(mention['value'])
        details.append({'number': mention['text'], 'status': status, 'issues': issues,
                        'subject': mention['subject'], 'metric': mention['metric'], 'unit': mention['unit']})
        (contradictions if status == 'contradicted' else uncertain).extend(issues)
    source_pairs = {(_decimal(x), _decimal(y)) for x, y in RATIO_SOURCE.findall(joined)}
    in_source_ratio = {v for pair in source_pairs for v in pair}
    for match in RATIO.finditer(text):
        pair = (_decimal(match.group(1)), _decimal(match.group(2)))
        if pair in source_pairs:
            continue
        # R6: a stated base ('54 of the 100 indicators') supports '37/100' when 37 itself is grounded.
        if pair[1] in {y for _x, y in source_pairs} and pair[0] in present:
            continue
        # R6: '43.0/70.3' with both values present and neither in any source ratio is a pair of values.
        if '/' in match.group(0) and pair[0] in present and pair[1] in present and not ({pair[0], pair[1]} & in_source_ratio):
            continue
        contradictions.append('denominator_error')
    direction_bad, direction_unsure = _direction_issues(text, joined)
    contradictions += direction_bad
    contradictions += _range_issues(text, sources)
    uncertain += direction_unsure
    if not claim_mentions:
        # A source's condition may qualify its reported number, not a claim about
        # how two metrics differ. Scope is unresolved without an attached measurement.
        uncertain += _condition_issues(text, sources)
    contradictions, uncertain = sorted(set(contradictions)), sorted(set(uncertain))
    status = ('contradicted' if contradictions else 'uncertain' if uncertain
              else 'grounded' if claim_mentions else 'no_numbers')
    return {'status': status, 'contradictions': contradictions, 'uncertain': uncertain, 'mentions': details}


def ground_claim(claim, passages_by_id=None):
    """Ground a research claim against its own cited quotes. Values are matched in the quotes only; the cited
    passages are used solely to recognise names and labels (R4)."""
    global _CONTEXT
    quotes = [s.get('quote', '') for s in claim.get('support', [])]
    ids = [s.get('chunk_id') for s in claim.get('support', [])] + list(claim.get('chunk_ids', []))
    by_id = passages_by_id or {}
    _CONTEXT = tuple((by_id[i].get('text') or '') for i in dict.fromkeys(ids) if i in by_id)
    try:
        return ground_text(claim.get('text', ''), quotes)
    finally:
        _CONTEXT = ()


def claim_issues(claim, passages_by_id=None):
    """Contradictions only (sorted issue names). Uncertain grounding is reported by ground_claim."""
    return ground_claim(claim, passages_by_id)['contradictions']


# ---------------------------------------------------------------- business advice
UNSUPPORTED_ADVICE = [
    ('roi_or_savings', re.compile(r'\b(?:ROI|return on investment|cost savings?|sav(?:e|es|ing)\s+(?:\$|money|costs?)|payback|reduce[sd]?\s+costs?\s+by)\b', re.I)),
    ('guarantee', re.compile(r'\b(?:guarantee[sd]?|ensures?|eliminat\w+\s+(?:all\s+)?(?:risk|errors?|bias)|risk[- ]free|100%\s+(?:accurate|reliable|safe))\b', re.I)),
    ('compliance_claim', re.compile(r'\b(?:(?:is|are|will be|makes?\s+\w+)\s+compliant|ensures?\s+compliance|meets?\s+(?:all\s+)?regulat\w+|legally\s+(?:safe|sufficient))\b', re.I)),
    ('deployment_readiness', re.compile(r'\b(?:ready\s+for\s+(?:production|deployment|launch)|production[- ]ready|deploy\s+(?:it\s+)?(?:immediately|now|at scale)|roll\s+(?:it\s+)?out\s+(?:firm|company|enterprise)[- ]wide)\b', re.I)),
    ('workforce_replacement', re.compile(r'\breplac\w+\s+(?:\w+\s+)?(?:staff|employees|analysts|workers|advisers|advisors|people|humans|reviewers)\b', re.I)),
]
# A sentence asserting a fact about the studied evidence (rather than a caveat or a proposal).
STUDY_FACT = re.compile(r'\b(?:the\s+)?(?:study|studies|paper|papers|evaluation|benchmark|experiment|experiments|authors|dataset|sample)\s+'
                        r'(?:covered|used|included|involved|tested|evaluated|measured|found|reported|showed|was|were|ran|had|surveyed|sampled)\b', re.I)
# Wording that makes a statement a conditional proposal rather than an asserted fact. Past tenses
# ("was validated", "tested") state facts and are deliberately NOT hedges.
HEDGE = re.compile(r'\b(?:may|might|could|would|can|if|whether|consider(?:s|ing)?|potential(?:ly)?|possibl[ey]|suggests?|suggesting|'
                   r'pilot(?:s|ing)?|test(?:s|ing)?|evaluat(?:e|es|ing)|validat(?:e|es|ing)|explor(?:e|es|ing)|assess(?:es|ing)?|'
                   r'should|recommend(?:s|ing)?|propos(?:e|es|ing)|before)\b', re.I)
# Wording that makes a risk or limitation a caveat about what is NOT established.
CAVEAT = re.compile(r"\b(?:not|no|untested|unknown|unclear|uncertain\w*|limited|only|single|lack\w*|absence|cannot|unverified|"
                    r"may\s+not|might\s+not|has\s+not|have\s+not|does\s+not|did\s+not|beyond|outside|transfer\w*)\b", re.I)
CATEGORIES = ('conditional_proposal', 'assumption', 'caveat', 'supported_fact', 'withheld')
# Joints between a premise and what follows from it (commas are NOT joints: they stay inside one statement).
JOINT_SPLIT = re.compile(r'\b(?:so|therefore|thus|hence|because|since|given\s+that|as\s+a\s+result)\b|;', re.I)
# A proposal can rest on a factual premise ("X has already achieved ..., so consider a pilot"). Clauses are
# split at these joints and every unhedged clause that asserts something is checked as a fact on its own.
PREMISE_SPLIT = re.compile(r'\b(?:so|therefore|thus|hence|because|since|given\s+that|as\s+a\s+result)\b|[;,]', re.I)
ASSERTION = re.compile(r'\b(?:already|has|have|had|is|are|was|were|achiev\w*|reach\w*|show(?:s|ed|n)|demonstrat\w*|'
                       r'prov(?:ed|en|es)|deliver\w*|outperform\w*|improv(?:ed|es)|reduc(?:ed|es)|works|worked|succeed\w*|'
                       r'perform(?:s|ed))\b', re.I)


def _evidence_setting(texts):
    joined = ' '.join(texts)
    return bool(EVALUATION_SETTING.search(joined)), bool(DEPLOYMENT_SETTING.search(joined))


def advice_issues(text, cited_passages, verified_claims, kind='implication'):
    """Classify one business statement and list what makes it unsupported.

    Returns (category, issues). Any issue means the statement is WITHHELD; an "unverified" label never
    licenses showing a statement that is known to be unsupported. Rules, for every kind of field:
    - Numbers must be grounded (same value, unit, sign, subject, metric, population and setting) in the
      cited passages' own sentences. Uncertain grounding is unsupported here: no model verifies advice.
    - ROI or savings, guarantees, compliance, readiness and workforce-replacement wording must be stated by
      the cited passages.
    - A statement asserted as FACT (not hedged as a proposal, not a caveat, not an assumption) must be
      supported in the same measurement setting as the evidence: a deployment, clinical or real-world
      fact cannot rest on benchmark or simulation evidence; and it must share most of its content with
      the verified findings.
    """
    issues = set()
    sentences = [part for passage in cited_passages for part in re.split(r'(?<=[.;!?])\s+', _norm(passage))]
    # Numbers are grounded within the premise or proposal segment they belong to ("X reached 78% on the benchmark,
    # so consider a clinical pilot": the pilot's setting is not the number's setting).
    for segment in JOINT_SPLIT.split(text):
        if segment and _NUM.search(segment):
            grounding = ground_text(segment, sentences)
            if grounding['status'] != 'grounded':
                issues.update(grounding['contradictions'] or [f'number_{u}' for u in grounding['uncertain']] or ['number_unconfirmed'])
    joined = ' '.join(cited_passages)
    for name, pattern in UNSUPPORTED_ADVICE:
        match = pattern.search(text)
        if match and not re.search(re.escape(match.group(0)), joined, re.I):
            issues.add(name)
    support = _content(' '.join(verified_claims)) | _content(joined)
    if STUDY_FACT.search(text):
        words = _content(text) - {_stem(w) for w in ('study', 'studies', 'paper', 'papers', 'evaluation', 'benchmark', 'authors')}
        if len(words & support) < max(2, len(words) // 2):
            issues.add('unsupported_study_fact')
    evaluation, deployment = _evidence_setting(sentences + list(verified_claims))

    def fact_issues(fact):
        found = set()
        if DEPLOYMENT_SETTING.search(fact) and evaluation and not deployment:
            found.add('setting_transfer')
        words = _content(fact)
        if len(words & support) < max(2, (len(words) + 1) // 2):
            found.add('unsupported_fact')
        return found

    if kind == 'assumption':
        category = 'assumption'
    elif kind == 'action' or HEDGE.search(text):
        category = 'conditional_proposal'
    elif kind in ('risk', 'limitation') and CAVEAT.search(text):
        category = 'caveat'
    else:
        category = 'supported_fact'
        issues |= fact_issues(text)
    if category in ('conditional_proposal', 'caveat'):
        # The proposal or caveat itself may stand, but a factual premise inside it must be supported on its own.
        for clause in PREMISE_SPLIT.split(text):
            clause = clause.strip()
            if clause and not HEDGE.search(clause) and not CAVEAT.search(clause) and ASSERTION.search(clause):
                premise = fact_issues(clause)
                if premise:
                    issues |= {'unsupported_premise', *premise}
    return ('withheld' if issues else category), sorted(issues)


def screen_business(output, passages, verified_claims=None):
    """Ground every business field; withhold what cannot be supported and record why.

    Returns (screened_output, screening). screening records every statement checked with its category:
    conditional_proposal, assumption, caveat or supported_fact (kept, still unverified by any model or
    person) or withheld (removed, with issues). Verified research findings are never part of this output.
    An output left with no implications becomes insufficient_evidence with an explicit limitation.
    """
    verified_claims = verified_claims or []
    claim_texts = [c['text'] if isinstance(c, dict) else c for c in verified_claims]
    by_id = {p['chunk_id']: _norm(p.get('text')) for p in passages}
    all_cited = list(by_id.values())
    screening, kept = [], []
    for row in output.get('implications', []):
        cited = [by_id[cid] for cid in row.get('chunk_ids', []) if cid in by_id]
        relevant_claims = [c['text'] for c in verified_claims if isinstance(c, dict) and set(c.get('chunk_ids', [])) & set(row.get('chunk_ids', []))] or claim_texts
        problems, categories = {}, {}
        fields = [('implication', 'implication', row.get('text', '')), ('action', 'action', row.get('suggested_action', ''))]
        fields += [(f'assumption {i + 1}', 'assumption', a) for i, a in enumerate(row.get('assumptions', []))]
        for label, kind, value in fields:
            category, found = advice_issues(value, cited, relevant_claims, kind)
            categories[label] = category
            if found:
                problems[label] = found
        overlap = _content(row.get('text', '')) & _content(' '.join(relevant_claims))
        if len(overlap) < 2:
            problems.setdefault('implication', []).append('not_grounded_in_verified_findings')
            categories['implication'] = 'withheld'
        entry = {'field': 'implication', 'text': row.get('text', '')[:200], 'categories': categories}
        if problems:
            screening.append({**entry, 'status': 'removed', 'issues': problems})
        else:
            kept.append(row)
            screening.append({**entry, 'status': 'kept_unverified', 'issues': {}})
    screened = dict(output)
    screened['implications'] = kept
    for field in ('risks', 'limitations'):
        lines = []
        for line in output.get(field, []):
            category, found = advice_issues(line, all_cited, claim_texts, field[:-1])
            entry = {'field': field[:-1], 'text': line[:200], 'categories': {'text': category}}
            if found:
                screening.append({**entry, 'status': 'removed', 'issues': {'text': found}})
            else:
                lines.append(line)
                screening.append({**entry, 'status': 'kept_unverified', 'issues': {}})
        screened[field] = lines
    if output.get('status') == 'ok' and not kept:
        screened['status'] = 'insufficient_evidence'
        screened['limitations'] = [*screened.get('limitations', []),
                                   'No proposed business implication could be grounded in the verified findings and their cited passages, so none is shown.']
    return screened, screening

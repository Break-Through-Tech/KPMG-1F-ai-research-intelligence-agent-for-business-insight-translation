"""Builds numeric_checks_v2.py from the frozen experiments/agentic/numeric_checks.py (copied first) by exact,
asserted replacements. Rerun after re-copying to reproduce v2 byte-for-byte."""
from pathlib import Path

p = Path(__file__).with_name('numeric_checks_v2.py')
s = p.read_text(encoding='utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:90])
    s = s.replace(old, new)


rep('"""Deterministic numerical grounding for research claims and business advice.\n',
    '"""Deterministic numerical grounding for research claims and business advice (v2: verification-repair).\n\n'
    'v2 = the frozen experiments/agentic/numeric_checks.py plus seven parsing corrections, each tied to false\n'
    'rejections in business-multiagent-v1 (development data). See experiments/verification-repair/FINDINGS.md.\n'
    '  R1 attribution: subject_mismatch needs an explicit, different named subject in BOTH numbers\' own clauses;\n'
    '     an inherited (elliptical) subject can only make a number uncertain. Names compare by alias\n'
    '     ("Claude" ~ "Claude 3.5 Sonnet", "KG2RAG" ~ "KG 2 RAG"); figure/table labels and metric names are not subjects.\n'
    '  R2 metrics: "F1 score"/"F1-score" is F1; the generic "score" never contradicts a specific metric; a metric\n'
    '     AFTER a number counts only inside that number\'s own clause.\n'
    '  R3 emphatic "only" ("only dropped from 66.8% to 60.0%") is not a scope condition; "only on X" still is.\n'
    '  R4 a version or size inside a model name ("Claude 3.5 Sonnet", "Llama Pro Finance 70B") and a "Table 1" label\n'
    '     are names, not measurements, when the same name appears in the cited quotes or passages.\n'
    '  R5 table header units: "Mean Latency (s): 10.39" is 10.39 seconds.\n'
    '  R6 ratios: "37/100" is grounded when 100 is the source\'s stated base ("54 of the 100 indicators") and 37 is\n'
    '     grounded; "precision/recall of 43.0/70.3" is a pair of values, each still checked, not a ratio.\n'
    '  R7 superscripts are read as digits ("KG\u00b2RAG" = "KG2RAG").\n'
    '  R8 "7.9% and 6.9% on HotpotQA and Shuffle-HotpotQA, respectively": each number takes its listed subject.\n'
    'Everything else is unchanged: values, units, signs, negation, settings, populations, conditions, direction,\n'
    'ranges, and the statistical-report rule (via statistical_reports.enable()).\n\n')

# R7 superscripts, alias comparison
rep("def _norm(text):\n    return re.sub(r'\\s+', ' ', text or '').strip()\n",
    "SUPERSCRIPTS = str.maketrans('\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079', '0123456789')\n\n\n"
    "def _norm(text):\n    return re.sub(r'\\s+', ' ', (text or '').translate(SUPERSCRIPTS)).strip()\n\n\n"
    "def _alnum(text):\n    return re.sub(r'[^0-9a-z]', '', (text or '').translate(SUPERSCRIPTS).casefold())\n\n\n"
    "def _same_entity(a, b):\n"
    "    \"\"\"Same named subject: equal letters and digits, or a digit-free family name that prefixes the other\n"
    "    ('Claude' ~ 'Claude 3.5 Sonnet'). 'GPT-4' vs 'GPT-4o' and 'Llama-2-7B' vs 'Llama-3-8B' stay different.\"\"\"\n"
    "    x, y = _alnum(a), _alnum(b)\n"
    "    if x == y:\n        return True\n"
    "    short, long_ = sorted((x, y), key=len)\n"
    "    return len(short) >= 2 and not re.search(r'\\d', short) and long_.startswith(short)\n")

# R2 metric aliases; shared constants
rep("('exact match', 'higher'), ('pass@1', 'higher'), ('f1', 'higher'),",
    "('exact match', 'higher'), ('pass@1', 'higher'), ('f1-score', 'higher'), ('f1 score', 'higher'), ('f1', 'higher'),")
rep("POLARITY = dict(METRICS)\n",
    "POLARITY = dict(METRICS)\n"
    "METRIC_ALIAS = {'f1-score': 'f1', 'f1 score': 'f1'}\n"
    "REFERENCE = re.compile(r'^(?:fig(?:ure)?s?|tables?|sections?|appendix|appendices|eq(?:uation)?s?|algorithms?)\\.?$', re.I)\n"
    "LABEL = re.compile(r'\\b(?:Table|Figure|Fig\\.|Section|Appendix|Eq\\.|Equation|Algorithm)\\s*\\d+(?:\\.\\d+)?\\b')\n"
    "HEADER_UNIT = re.compile(r'\\((%|s|sec|secs|seconds|ms|min|mins|h|hrs?)\\)\\s*:\\s*$', re.I)\n"
    "HEADER_UNIT_NAME = {'%': 'percent', 's': 'seconds', 'sec': 'seconds', 'secs': 'seconds', 'seconds': 'seconds', 'ms': 'ms',\n"
    "                    'min': 'minutes', 'mins': 'minutes', 'h': 'hours', 'hr': 'hours', 'hrs': 'hours'}\n"
    "# 'only dropped', 'only slightly': emphasis on a change, not a scope condition ('only on Books' still is).\n"
    "EMPHATIC_ONLY = re.compile(r'^(?:slightly|marginally|modestly|somewhat|dropp\\w*|decreas\\w*|declin\\w*|fell|fall\\w*|ros[ei]\\w*|'\n"
    "                           r'increas\\w*|improv\\w*|reduc\\w*|chang\\w*|lost|los[es]\\w*|gain\\w*|mov\\w*|shift\\w*)$', re.I)\n"
    "_NAME_TEXT = ''   # letters+digits of the cited quotes and passages, set per ground_text call (R4)\n"
    "_CONTEXT = ()     # cited passage texts, set by ground_claim (names and labels only, never values)\n")

# R4 names and labels are not measurements
rep("""def _measurements(text, begin, end, source_identifiers):
    identifiers = [m for m in _IDENTIFIER.finditer(text, begin, end)
                   if m.group().casefold() in source_identifiers]
    return [m for m in _NUM.finditer(text, begin, end)
            if not any(label.start() <= m.start() < label.end() for label in identifiers)]
""", """def _name_digits(text, begin, end):
    \"\"\"Digit spans that belong to a model or system name present in the cited text (R4): a size or version glued
    to letters ('70B') or followed by a capitalised word inside the name ('Claude 3.5 Sonnet'), plus 'Table 1'
    labels. Never a whole entity, so 'Llama 70B 58.3' still measures 58.3.\"\"\"
    spans = []
    if not _NAME_TEXT:
        return spans
    for entity in ENTITY.finditer(text, begin, end):
        name = entity.group(0)
        words = name.split()
        if not re.search(r'\\d', name) or _METRIC_RE.fullmatch(words[0]) or REFERENCE.match(words[0]):
            continue
        if _alnum(name) not in _NAME_TEXT:
            continue
        for number in _NUM.finditer(text, entity.start(), entity.end()):
            after = text[number.end():entity.end()]
            if re.match(r'[A-Za-z]', after) or (re.match(r'\\s+[A-Z][a-z]+\\b', after)
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
""")

rep("metric_spans = [(m.start(), m.end(), m.group(1).lower()) for m in _METRIC_RE.finditer(text)]",
    "metric_spans = [(m.start(), m.end(), METRIC_ALIAS.get(m.group(1).lower(), m.group(1).lower())) for m in _METRIC_RE.finditer(text)]")

# R5 header unit
rep("""            if _CURRENCY_BEFORE.search(text[max(0, match.start() - 5):match.start() - (1 if sign else 0)]):
                unit = f'currency+{unit}' if unit else 'currency'
""", """            if _CURRENCY_BEFORE.search(text[max(0, match.start() - 5):match.start() - (1 if sign else 0)]):
                unit = f'currency+{unit}' if unit else 'currency'
            if unit is None:
                header = HEADER_UNIT.search(text[max(begin, match.start() - 16):match.start()])
                if header:
                    unit = HEADER_UNIT_NAME[header.group(1).lower()]  # R5
""")

# R2 metric after number stays in own clause; R1 own-clause subjects
rep("""            def nearest(spans, reach=None):
                inside = [(min(abs(s - match.end()), abs(e - match.start())), name) for s, e, name in spans
                          if begin <= s < end and not (s <= match.start() < e)]
""", """            own_left, own_right = _clause_bounds(text, begin, end, match.start(), match.end())

            def nearest(spans, reach=None):
                # R2: a metric after the number stays in its clause; a metric before it must not already belong to
                # another number in between ("F1 40.6 and 9.58 seconds": 9.58 is not F1).
                inside = [(min(abs(s - match.end()), abs(e - match.start())), name) for s, e, name in spans
                          if begin <= s < end and not (s <= match.start() < e)
                          and ((s < match.start() and not any(e <= n.start() < match.start() for n in measurements))
                               or (s >= match.end() and s < own_right))]
""")
rep("""                in_clause = {m.group(1).lower() for m in _METRIC_RE.finditer(clause)}""",
    """                in_clause = {METRIC_ALIAS.get(m.group(1).lower(), m.group(1).lower()) for m in _METRIC_RE.finditer(clause)}""")
rep("""            mentions.append({'value': value, 'sign': sign, 'unit': unit, 'subject': _clause_subject(text, begin, end, match, entity_spans),""",
    """            mentions.append({'value': value, 'sign': sign, 'unit': unit, 'subject': _clause_subject(text, begin, end, match, entity_spans),
                             # R1: subjects named in this number's own clause (empty when only inherited);
                             # R8: in "7.9% and 6.9% on A and B, respectively" each number takes its listed subject.
                             'own_subjects': respective.get(match.start(),
                                                            [name for s, e, name in entity_spans if own_left <= s and e <= own_right]),""")
rep("""        measurements = _measurements(text, begin, end, source_identifiers)
""", """        measurements = _measurements(text, begin, end, source_identifiers)
        respective = {}
        if re.search(r'\\brespectively\\b', text[begin:end], re.I) and measurements:
            listed = [name for s, e, name in entity_spans if s >= measurements[-1].end() and e <= end]
            if len(listed) == len(measurements):
                respective = {m.start(): [name] for m, name in zip(measurements, listed)}
""")

# R1 subject eligibility
rep("""    if name in shared_entities:
        return True
    words = name.split()
    if not words or words[0].lower() in STOP or _METRIC_RE.fullmatch(name):
        return False
""", """    words = name.split()
    if not words or REFERENCE.match(words[0]) or _METRIC_RE.fullmatch(words[0]) or _METRIC_RE.fullmatch(name):
        return False  # R1: 'Figure 5', 'Table 1', 'F1-score', 'F1 44.1' are not subjects
    if name in shared_entities:
        return True
    if words[0].lower() in STOP:
        return False
""")

# R3 emphatic only
rep("""    for match in QUALIFIER.finditer(text):
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z\\-']+", match.group(2)) if w.lower() not in STOP][:3]""",
    """    for match in QUALIFIER.finditer(text):
        if match.group(1).lower() == 'only' and (EMPHATIC_ONLY.match(match.group(2).split()[0])
                                                 or re.search(r'\\bnot\\s+$', text[:match.start()], re.I)):
            continue  # R3: emphatic "only dropped" and "not only ... but also" are not scope conditions
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z\\-']+", match.group(2)) if w.lower() not in STOP][:3]""")
rep("""        for match in QUALIFIER.finditer(quote):
            keyword = match.group(1).lower().split()[0]""",
    """        for match in QUALIFIER.finditer(quote):
            keyword = match.group(1).lower().split()[0]
            if keyword == 'only' and (EMPHATIC_ONLY.match(match.group(2).split()[0])
                                      or re.search(r'\\bnot\\s+$', quote[:match.start()], re.I)):
                continue  # R3""")

# R1/R2 judge
rep("""    subject_ok = metric_ok = False
    if mention['subject']:
        if c['subject'] == mention['subject']:
            subject_ok = True
        elif c['subject']:
            return 'contradicted', ['subject_mismatch']
        else:
            uncertain.append('subject_unconfirmed')
    if mention['metric']:
        if c['metric'] and (c['metric'] == mention['metric'] or (POLARITY.get(c['metric'], 0) == POLARITY.get(mention['metric'], 1)
                                                                 and c['metric'].startswith(mention['metric'][:4]))):
            metric_ok = True
        elif c['metric']:
            return 'contradicted', ['metric_mismatch']
        else:
            uncertain.append('metric_unconfirmed')""", """    subject_ok = metric_ok = False
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
            uncertain.append('metric_unconfirmed')  # R2: the generic 'score' cannot contradict a specific metric""")

# R4 name text per call; R6 ratios
rep("""    text = _norm(text)
    sources = [_norm(s) for s in sources if s]
    joined = ' \\n '.join(sources)
""", """    global _NAME_TEXT
    text = _norm(text)
    sources = [_norm(s) for s in sources if s]
    joined = ' \\n '.join(sources)
    _NAME_TEXT = _alnum(joined + ' ' + ' '.join(_CONTEXT))
""")
rep("""    contradictions, uncertain, details = [], [], []
    for mention in claim_mentions:
        status, issues = _match_mention(mention, source_mentions, percent_context)""",
    """    contradictions, uncertain, details = [], [], []
    present = set()  # values matched without contradiction (grounded or uncertain), for R6
    for mention in claim_mentions:
        status, issues = _match_mention(mention, source_mentions, percent_context)
        if status != 'contradicted':
            present.add(mention['value'])""")
rep("""    for a, b in RATIO.findall(text):
        pair = (_decimal(a), _decimal(b))
        if not any((_decimal(x), _decimal(y)) == pair for x, y in RATIO.findall(joined)):
            contradictions.append('denominator_error')
""", """    source_pairs = {(_decimal(x), _decimal(y)) for x, y in RATIO_SOURCE.findall(joined)}
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
""")
rep("RATIO = re.compile(rf'({NUMBER})\\s*(?:out\\s+of|of|/)\\s*({NUMBER})\\b', re.I)\n",
    "RATIO = re.compile(rf'({NUMBER})\\s*(?:out\\s+of|of|/)\\s*({NUMBER})\\b', re.I)\n"
    "RATIO_SOURCE = re.compile(rf'({NUMBER})\\s*(?:out\\s+of|of|/)\\s*(?:the\\s+|all\\s+)?({NUMBER})\\b', re.I)\n")

# R4 ground_claim passes cited passages (names and labels only)
rep('''def ground_claim(claim, passages_by_id=None):
    """Ground a research claim against its own cited quotes."""
    quotes = [s.get('quote', '') for s in claim.get('support', [])]
    return ground_text(claim.get('text', ''), quotes)
''', '''def ground_claim(claim, passages_by_id=None):
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
''')
p.write_text(s, encoding='utf-8')
print('patched', len(s))

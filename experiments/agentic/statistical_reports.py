"""Opt-in fix for statistical test reports in the deterministic number check (numeric_checks.py stays frozen).

Defect (Codex F09): "the overall comparison was not significant, F(3,26)=0.341, p=.796" was held as
negation_mismatch against the source "no statistically significant difference ..., (F(3, 26) = 0.341, p = .796)".
The check attaches a negation within 40 characters *before* a number to that number. A reported test statistic
(degrees of freedom, statistic, p-value) is never itself negated; the negation applies to significance. Whether the
40-character window catches "not" or "no" depends only on wording distance.

Fix, two parts, applied together:
  1. Numbers inside a test report (F(3,26)=0.341, t(28)=2.1, chi2(2)=..., p=.796, p<.05) are exempt from
     number-level negation, in both claim and source. Their values must still match exactly.
  2. New, stricter check: when a claim sentence and a cited source sentence report the same test statistic, both
     mention significance, and one negates it while the other does not, the claim is contradicted
     (significance_mismatch). The frozen check missed this case entirely ("significant, F(3,26)=0.341" passed).
Every other number keeps the original negation rule unchanged.

enable() patches the numeric_checks module process-wide. It is opt-in per run, like quote grounding and the policy.
"""
import re

import numeric_checks

_NUM = r'-?\d*\.?\d+'
STAT = re.compile(r'(?:\b(?:F|t|z|r|U|H|W|chi2|χ2|χ²)\s*\(\s*\d+(?:\.\d+)?(?:\s*,\s*\d+(?:\.\d+)?)?\s*\)\s*=\s*' + _NUM
                  + r'|\bp\s*[=<>≤]\s*' + _NUM + r')', re.I)
SIGNIFICANCE = re.compile(r'\b(?:statistically\s+)?significan\w*', re.I)


def _stat_values(text):
    """Numbers (as strings) appearing inside test reports in text."""
    return {n for m in STAT.finditer(text) for n in re.findall(r'\d*\.?\d+', m.group())}


def _sentences(text):
    return [s for s in re.split(r'(?<=[.;!?])\s+(?=[A-Z(\\])', text) if s.strip()]


def _significance(sentence):
    """None if the sentence states no significance; else True when significance is negated."""
    found = SIGNIFICANCE.search(sentence)
    if not found:
        return None
    return bool(numeric_checks.NEGATION.search(sentence[max(0, found.start() - numeric_checks.NEGATION_REACH):found.start()]))


def significance_mismatch(claim, sources):
    for sentence in _sentences(claim):
        values, polarity = {v for m in STAT.finditer(sentence) for v in re.findall(r'\d*\.\d+', m.group())}, _significance(sentence)
        if not values or polarity is None:
            continue
        for source in sources:
            for other in _sentences(source):
                shared = values & {v for m in STAT.finditer(other) for v in re.findall(r'\d*\.\d+', m.group())}
                theirs = _significance(other)
                if shared and theirs is not None and theirs != polarity:
                    return True
    return False


_original_mentions = numeric_checks._mentions
_original_ground_text = numeric_checks.ground_text


def _mentions(text, *args, **kwargs):
    mentions = _original_mentions(text, *args, **kwargs)
    for mention in mentions:
        begin, end = mention['sentence']
        sentence = text[begin:end]
        inside = [m for m in STAT.finditer(sentence) if mention['text'] in m.group()]
        # Exempt only when every occurrence of this number in its sentence sits inside a test report.
        occurrences = len(re.findall(r'(?<![\d.])' + re.escape(mention['text']) + r'(?!\d|\.\d)', sentence))
        if inside and occurrences == sum(len(re.findall(r'(?<![\d.])' + re.escape(mention['text']) + r'(?!\d|\.\d)', m.group()))
                                         for m in inside):
            mention['negated_here'] = False
            mention['sentence_negated'] = False
    return mentions


def _ground_text(text, sources):
    result = _original_ground_text(text, sources)
    if significance_mismatch(text, list(sources)):
        result = {**result, 'status': 'contradicted',
                  'contradictions': sorted(set(result.get('contradictions', [])) | {'significance_mismatch'})}
    return result


def enable():
    numeric_checks._mentions = _mentions
    numeric_checks.ground_text = _ground_text


def disable():
    numeric_checks._mentions = _original_mentions
    numeric_checks.ground_text = _original_ground_text

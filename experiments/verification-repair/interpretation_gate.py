"""Labelled publication of business interpretations (prototype; replaces the blanket hold of interpretation_policy).

An interpretation is published ONLY as a separately labelled "interpretation" (never as a finding) when every rule
holds; otherwise it stays held with the failing rules recorded:

  G1 exact quotes (quote_membership passed).
  G2 numbers: none contradicted, and every number grounded (an interpretation may restate verified numbers, never
     uncertain ones).
  G3 verifier: not contradicted or unsupported, and the only issue allowed is missing_support. A recommendation is by
     nature not stated in the passages; the verifier checks its premises (Baseline's rule: "For an interpretation,
     check its explicitly qualified premises, not whether a study proved advice").
  G4 prescriptive frame: addressed to the reader's decision ("For a finance team, this supports testing ...").
  G5 no explanatory or causal claim about the studied systems ("indicates that X is more effective", "reflects that",
     "because", "helps explain"). These are research claims and stay held: this is what blocked the F01
     misattribution, and it still does.
  G6 the existing deterministic business screen, numeric_checks.advice_issues: no ROI or savings, guarantee,
     compliance, deployment-readiness or workforce-replacement wording the passages do not state; unhedged factual
     premises must be supported; no deployment fact resting on benchmark evidence.
  G7 built on verified findings: at least two content words shared with the findings published for the question.
"""
import re

PRESCRIPTIVE = re.compile(
    r'\b(?:these|this|the|such)(?:\s+(?:results?|findings?|evidence|data|comparisons?|studies|study))?\s+supports?\b'
    r'|^\s*(?:for\s+[^,]{3,60},\s*)?(?:test|evaluate|treat|prioriti[sz]e|require|request|pilot|validate|check|consider|use)\b',
    re.I)
EXPLANATORY = re.compile(
    r'\b(?:indicat\w*|reflect\w*|demonstrat\w*|explain\w*|shows?|showing|proves?|proving|suggest\w*|means?)\s+(?:that|why|how)\b'
    r'|\bbecause\b|\bdue\s+to\b|\b(?:caus(?:e|es|ed|ing)|driv(?:e|es|en|ing)|attribut\w*)\b|\bhelps?\s+(?:to\s+)?explain\b'
    r'|\bis\s+more\s+effective\b', re.I)
LABEL = 'Interpretation: inferred from the cited findings for this decision; not a research result.'


def gate(row, claim, numeric, cited_passages, verified_texts):
    """row: the verifier row (deterministic, automated); claim: the drafted claim; numeric: the number-check module.
    Returns the list of failed rules (empty = publish as a labelled interpretation)."""
    failed = []
    text = claim['text']
    if row['deterministic'].get('quote_membership') != 'passed':
        failed.append('G1')
    grounding = numeric.ground_claim(claim, {p['chunk_id']: p for p in cited_passages})
    if grounding['status'] not in ('grounded', 'no_numbers'):
        failed.append('G2')
    verdict = row.get('automated') or {}
    if verdict.get('verdict') not in ('supported', 'partially_supported') or set(verdict.get('issues') or []) - {'missing_support'}:
        failed.append('G3')
    if not PRESCRIPTIVE.search(text):
        failed.append('G4')
    if EXPLANATORY.search(text):
        failed.append('G5')
    # A prescriptive statement (G4) is screened as a proposal; its unhedged factual premises are still fact-checked.
    kind = 'action' if 'G4' not in failed else 'implication'
    _category, issues = numeric.advice_issues(text, [p['text'] for p in cited_passages], verified_texts, kind)
    if issues:
        failed.append('G6:' + ','.join(issues))
    if len(numeric._content(text) & numeric._content(' '.join(verified_texts))) < 2:
        failed.append('G7')
    return failed

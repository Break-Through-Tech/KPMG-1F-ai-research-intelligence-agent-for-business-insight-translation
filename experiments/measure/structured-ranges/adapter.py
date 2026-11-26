"""Experimental source-bound comparison. No application or provider imports."""
from dataclasses import dataclass
from decimal import Decimal
import re

# A lexer and two explicit forms, not a parser for arbitrary scientific prose.
TOKENS = re.compile(r"\d+(?:\.\d+)?|[A-Za-z]+|[^\s]")
DASHES = {"-", "–", "−", "—"}
FACETS = ("subject", "metric", "setting", "population", "qualifier", "direction")
ROLE_LABELS = {"before": "before", "baseline": "before", "after": "after", "treatment": "after"}

class UnsupportedForm(ValueError):
    """A binding could not be established with the supported grammar."""

@dataclass(frozen=True)
class Quantity:
    lower: Decimal
    upper: Decimal
    unit: str
    form: str

    def canonical(self):
        if self.unit == "percent":
            return self.lower / 100, self.upper / 100, "proportion", self.form
        return self.lower, self.upper, self.unit, self.form

@dataclass(frozen=True)
class SourceFinding:
    paper: str
    source_url: str
    method: str
    citations: tuple
    scope: dict
    roles: dict
    required_scope: tuple
    ambiguity: tuple

@dataclass(frozen=True)
class Decision:
    status: str
    reason: str

def tokens(text):
    return TOKENS.findall(text.casefold())

def number(words, j):
    sign = -1 if j < len(words) and words[j] in DASHES else 1
    j += int(sign == -1 or (j < len(words) and words[j] == "+"))
    if j >= len(words) or not words[j][0].isdigit():
        raise UnsupportedForm("expected number")
    return sign * Decimal(words[j]), j + 1

def read_unit(words, offset):
    for spelling, unit in [(("percentage", "points"), "percentage_points"), (("percent",), "percent"),
                           (("%",), "percent"), (("auc",), "proportion"), (("score",), "score")]:
        if words[offset:offset + len(spelling)] == list(spelling):
            return unit, offset + len(spelling)
    return None, offset

def quantity(words, j, default_unit):
    bracket = j < len(words) and words[j] == "["
    lower, j = number(words, j + int(bracket))
    first_unit, j = read_unit(words, j)
    upper = lower
    form = "point"
    if j < len(words) and (words[j] in DASHES or (bracket and words[j] == ",")):
        upper, j = number(words, j + 1)
        form = "range"
    if bracket:
        if j >= len(words) or words[j] != "]" or form != "range":
            raise UnsupportedForm("expected closed interval")
        j += 1
    last_unit, j = read_unit(words, j)
    if first_unit and last_unit and first_unit != last_unit:
        raise UnsupportedForm("different endpoint units")
    if lower > upper:
        raise UnsupportedForm("descending endpoints")
    if j < len(words) and words[j] in DASHES:
        raise UnsupportedForm("additional endpoint")
    return Quantity(lower, upper, last_unit or first_unit or default_unit, form), j

def parse_roles(text, default_unit):
    """Parse a single 'from X to Y' or a pair of labeled role values."""
    words = tokens(text)
    alternatives = []
    for j, word in enumerate(words):
        if word != "from":
            continue
        try:
            a, k = quantity(words, j + 1, default_unit)
            if k < len(words) and words[k] == "to":
                b, _ = quantity(words, k + 1, default_unit)
                alternatives.append({"before": a, "after": b})
        except UnsupportedForm:
            continue
    labels = {}
    for j, word in enumerate(words[:-1]):
        role = ROLE_LABELS.get(word)
        if not role or words[j + 1] != ":":
            continue
        try:
            value, _ = quantity(words, j + 2, default_unit)
        except UnsupportedForm:
            continue
        if role in labels:
            raise UnsupportedForm("duplicate role")
        labels[role] = value
    if labels.keys() == {"before", "after"}:
        alternatives.append(labels)
    if len(alternatives) != 1:
        raise UnsupportedForm("comparison missing or multiply stated")
    return alternatives[0]

def scopes(text, aliases):
    words = tokens(text)
    matched = {}
    for facet, entries in aliases.items():
        values = set()
        for value, forms in entries.items():
            for form in forms:
                seek = tokens(form)
                if seek and any(words[j:j+len(seek)] == seek for j in range(len(words)-len(seek)+1)):
                    values.add(value)
        matched[facet] = values
    return matched

def compare(source, roles, claim_scope):
    """Validate relationships from typed records. This function has no text parsing."""
    if source.ambiguity:
        return Decision("review", "source association ambiguous")
    for facet in FACETS:
        observed = claim_scope.get(facet, set())
        expected = source.scope.get(facet)
        if len(observed) > 1:
            return Decision("review", f"multiple {facet} bindings")
        if observed and expected and expected not in observed:
            return Decision("reject", f"different {facet}")
        if (observed and expected is None) or (facet in source.required_scope and not observed):
            return Decision("review", f"unbound {facet}")
    if roles is None:
        return Decision("review", "comparison form unsupported")
    for role in ("before", "after"):
        if source.roles[role].canonical() != roles[role].canonical():
            return Decision("reject", f"{role} value, shape, or unit differs")
    return Decision("accept", "both role values and bound scope agree")

def verify(source, claim, aliases, default_unit):
    supports = {}
    for item in claim["support"]:
        supports.setdefault(item["chunk_id"], []).append(" ".join(item["quote"].split()))
    need = source.citations
    if not all(any(" ".join(ref["source_text"].split()) in excerpt for excerpt in supports.get(ref["chunk_id"], ()))
               for ref in need):
        return Decision("review", "cited output does not bind every required source span"), {}, None
    # Out-of-grammar negation and arithmetic must remain reviewable rather than
    # being silently interpreted as affirmative interval claims.
    words = set(tokens(claim["text"]))
    if words & {"not", "never", "except", "unless", "relative", "roughly", "approximately", "over", "under"}:
        return Decision("review", "unmapped claim qualifier"), {}, None
    recognized = scopes(claim["text"], aliases)
    try:
        roles = parse_roles(claim["text"], default_unit)
    except UnsupportedForm:
        roles = None
    return compare(source, roles, recognized), recognized, roles


"""Offline claim linker for complete comparisons against trusted source findings."""
from dataclasses import dataclass
from decimal import DecimalException, Inexact, localcontext
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bound_verify import Comparison, Operand, verify
from adapter import UnsupportedForm, quantity, tokens

DASHES = str.maketrans({"–": "-", "—": "-", "−": "-", "‑": "-"})


@dataclass(frozen=True)
class LinkResult:
    status: str
    reason: str
    finding: str | None = None
    comparison: Comparison | None = None


def normalized(text):
    return " ".join(unicodedata.normalize("NFC", text).translate(DASHES).casefold().split())


def label(text):
    # Allow a separator change such as strategy-selection versus strategy selection.
    return r"[- ]+".join(re.escape(part) for part in re.split(r"[- ]+", normalized(text)))


def frames(finding):
    """Whole-claim forms built from the declared scope, labels, and operand roles."""
    scope = finding.comparison.scope
    metric = label(scope["metric"])
    qualifiers = ", ".join(label(value) for key, value in scope.items() if key != "metric")
    before, after = r"(?P<before>.+?)", r"(?P<after>.+?)"
    yield (rf"for {metric} \({qualifiers}\), {label(finding.before_label)} was {before}"
           rf" and {label(finding.after_label)} was {after}")

    # Unlabeled "from ... to ..." is used for textual before/after findings.
    if set(scope) == {"subject", "metric", "setting", "population"} and all(
        isinstance(ref.locator.selector, tuple) for ref in finding.citations
    ):
        subject, setting, population = (label(scope[key]) for key in ("subject", "setting", "population"))
        middle = (rf"{subject} (?P<verb>improved|increased|decreased|changed) {metric}"
                  rf" from {before} to {after} across {population}")
        yield rf"on {setting}, {middle}"
        yield rf"{middle} on {setting}"


def read_value(text, reference):
    words = tokens(text)
    # An accuracy range in percent needs a unit in the answer. Score- and
    # proportion-valued table metrics can use their reported native scale.
    default = None if reference.unit == "percent" else reference.unit
    with localcontext() as arithmetic:
        arithmetic.prec = max(arithmetic.prec, len(text))
        arithmetic.traps[Inexact] = True
        value, end = quantity(words, 0, default)
    if end != len(words) or value.unit is None:
        raise UnsupportedForm("operand is incomplete or has trailing wording")
    return value


def quote_covers(citation, quotes, parent_text):
    target = citation.locator.selector
    if isinstance(target, str):
        # Full audited table row binds the numeric cell and its row/column labels.
        return parent_text in quotes
    left, right = target
    for quote in quotes:
        start = parent_text.find(quote)
        if start >= 0 and start == parent_text.rfind(quote) and start <= left and right <= start + len(quote):
            return True
    return False


def prose_evidence(finding, context, quotes):
    """Require one source quote containing the whole comparison and its scope."""
    ids = {ref.locator.chunk_id for ref in finding.citations}
    if len(ids) != 1 or not all(isinstance(ref.locator.selector, tuple) for ref in finding.citations):
        return ()
    chunk, = ids
    scope = tuple(label(value) for value in finding.comparison.scope.values())
    return tuple(
        quote for quote in quotes[chunk]
        if all(quote_covers(ref, (quote,), context[chunk]["text"]) for ref in finding.citations)
        and all(re.search(rf"(?<!\w){facet}(?!\w)", normalized(quote)) for facet in scope)
    )


def context_from_saved(evidence, parents):
    """Rehydrate only uniquely identified parents whose archived text is exact."""
    fields = ("chunk_id", "arxiv_id", "source_url", "table_id", "text")
    matched = {}
    seen = set()
    for saved in evidence:
        key = saved["chunk_id"]
        if key in seen:
            matched.pop(key, None)
            continue
        seen.add(key)
        parent = parents.get(key)
        if parent and all(saved.get(field) == parent.get(field) for field in fields):
            matched[key] = parent
    return matched


def propose(claim, context, findings):
    """Read scoped operands from the claim and locate its quoted evidence."""
    text = normalized(claim["text"]).removesuffix(".")
    quotes = {}
    for cite in claim.get("support", ()):
        quote = cite.get("quote")
        if isinstance(quote, str) and quote.strip():
            quotes.setdefault(cite["chunk_id"], set()).add(quote)
    candidates = [
        (key, item) for key, item in findings.items()
        if any(ref.locator.chunk_id in quotes for ref in item.citations)
    ]
    if not candidates:
        return LinkResult("review", "cited passages have no registered comparison")

    recognized = []
    for key, finding in candidates:
        matches = [match for frame in frames(finding) if (match := re.fullmatch(frame, text))]
        recognized.extend((key, finding, match) for match in matches)
    if len(recognized) != 1:
        return LinkResult("review", "comparison wording or scope is unbound or ambiguous")

    key, finding, match = recognized[0]
    for cite in finding.citations:
        chunk = cite.locator.chunk_id
        if chunk not in context or not quote_covers(cite, quotes.get(chunk, ()), context[chunk]["text"]):
            return LinkResult("review", "a required operand or its row is missing from the cited evidence")
    prose = any(isinstance(ref.locator.selector, tuple) for ref in finding.citations)
    source_quotes = prose_evidence(finding, context, quotes) if prose else ()
    if prose and not source_quotes:
        return LinkResult("review", "the cited source does not bind both operands with their full scope")

    operands = []
    for role in ("before", "after"):
        reference = getattr(finding.comparison, role)
        try:
            value = read_value(match[role], reference.value)
        except (DecimalException, UnsupportedForm):
            return LinkResult("review", f"unbound {role} value or unit")
        operands.append(Operand(value, reference.locators))
    proposal = Comparison(finding.comparison.scope.copy(), *operands)
    verb = match.groupdict().get("verb")
    before, after = (operand.value for operand in operands)
    lower_before, upper_before = before.canonical()[:2]
    lower_after, upper_after = after.canonical()[:2]
    if verb in {"increased", "improved"} and not (lower_before < lower_after and upper_before < upper_after):
        return LinkResult("reject", "direction wording conflicts with the linked endpoints")
    if verb == "decreased" and not (lower_before > lower_after and upper_before > upper_after):
        return LinkResult("reject", "direction wording conflicts with the linked endpoints")
    # An increase alone does not establish that an outcome improved.
    if verb == "improved" and not any(re.search(
        rf"\bimprov(?:e[sd]?|ing) {label(finding.comparison.scope['metric'])} from\b", normalized(quote)
    ) for quote in source_quotes):
        return LinkResult("review", "the cited wording does not establish improvement")
    return LinkResult("proposed", "comparison parsed from the claim", key, proposal)


def bind(claim, context, findings):
    proposal = propose(claim, context, findings)
    if proposal.status != "proposed":
        return proposal
    verdict = verify(findings[proposal.finding], proposal.comparison, context)
    if verdict.status != "accept":
        return LinkResult(verdict.status, verdict.reason)
    return LinkResult("linked", verdict.reason, proposal.finding, proposal.comparison)

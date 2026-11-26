"""Verify typed comparisons against trusted findings from exact delivered evidence."""
from dataclasses import dataclass
from decimal import Decimal, DecimalException, Inexact, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "structured-ranges"))
from adapter import Decision, Quantity


@dataclass(frozen=True)
class Locator:
    chunk_id: str
    selector: str | tuple[int, int]  # Original cell ID or half-open character span.


@dataclass(frozen=True)
class Operand:
    value: Quantity
    locators: frozenset[Locator]


@dataclass(frozen=True)
class Comparison:
    scope: dict[str, str]
    before: Operand
    after: Operand


@dataclass(frozen=True)
class Citation:
    locator: Locator
    paper: str
    source_url: str
    source_sha256: str | None
    passage_sha256: str
    source_text: str
    header_path: tuple[str, ...] = ()
    header_cell_id: str | None = None
    table_id: str | None = None


@dataclass(frozen=True)
class Finding:
    comparison: Comparison
    before_label: str
    after_label: str
    citations: tuple[Citation, ...]
    ambiguity: str | None = None
    comparison_kind: str = "unspecified"
    scope_provenance: dict | None = None


def passage_sha256(passage):
    keys = (
        "chunk_id", "arxiv_id", "source_url", "source_sha256", "text",
        "source_anchor", "version_binding", "caption", "table_id", "table_headers", "table_cells",
    )
    content = {key: passage.get(key) for key in keys}
    data = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(data.encode("utf-8")).hexdigest()


def _valid_quantity(value):
    if not isinstance(value, Quantity) or value.unit not in {
        "percent", "proportion", "score", "percentage_points", "count"
    }:
        return False
    if not all(isinstance(n, Decimal) and n.is_finite() for n in (value.lower, value.upper)):
        return False
    return (value.form == "point" and value.lower == value.upper
            or value.form == "range" and value.lower <= value.upper)


def _same_value(left, right):
    endpoints = (left.lower, left.upper, right.lower, right.upper)
    with localcontext() as arithmetic:
        arithmetic.prec = max(len(number.as_tuple().digits) for number in endpoints)
        arithmetic.traps[Inexact] = True
        return left.canonical() == right.canonical()


def verify(finding, claim, context):
    """Use curated bindings and canonical parent records from the delivered context."""
    if not isinstance(claim, Comparison):
        return Decision("review", "no typed claim binding")
    if finding.ambiguity:
        return Decision("review", finding.ambiguity)

    expected = finding.comparison
    if not isinstance(claim.scope, dict) or claim.scope.keys() != expected.scope.keys() or not all(
        isinstance(value, str) and value.strip() for value in claim.scope.values()
    ):
        return Decision("review", "scope is incomplete or contains an unbound field")
    for key, value in expected.scope.items():
        if claim.scope[key] != value:
            return Decision("reject", f"different {key}")

    labels = ("left", "right") if finding.comparison_kind == "categorical" else ("before", "after")
    pairs = zip(labels, (expected.before, expected.after), (claim.before, claim.after), strict=True)
    for role, source, candidate in pairs:
        if not isinstance(candidate, Operand) or not candidate.locators or not _valid_quantity(candidate.value):
            return Decision("review", f"{role} binding is incomplete or malformed")
        if candidate.locators != source.locators:
            return Decision("reject", f"{role} source locators differ")
        try:
            if not _same_value(candidate.value, source.value):
                return Decision("reject", f"{role} value, form, or unit differs")
        except DecimalException:
            return Decision("review", f"{role} value cannot be converted exactly")

    citations = {citation.locator: citation for citation in finding.citations}
    required = expected.before.locators | expected.after.locators
    if not required or len(citations) != len(finding.citations) or citations.keys() != required:
        return Decision("review", "finding has incomplete or ambiguous provenance")
    for citation in citations.values():
        passage = context.get(citation.locator.chunk_id)
        if passage is None or passage_sha256(passage) != citation.passage_sha256:
            return Decision("review", f"missing or altered evidence in {citation.locator.chunk_id}")
    return Decision("accept", "scope, role, value, and exact delivered evidence agree")


def render(finding, claim, context):
    """Render only canonical fields, so scope or numeric wording cannot drift."""
    if verify(finding, claim, context).status != "accept":
        return None

    def format_quantity(value):
        text = format(value.lower, "f")
        if value.form == "range":
            text += "–" + format(value.upper, "f")
        return text + ("%" if value.unit == "percent" else "")

    fact = finding.comparison
    qualifiers = ", ".join(value for key, value in fact.scope.items() if key != "metric")
    before = format_quantity(fact.before.value)
    after = format_quantity(fact.after.value)
    return (f"For {fact.scope['metric']} ({qualifiers}), "
            f"{finding.before_label} was {before} and {finding.after_label} was {after}.")

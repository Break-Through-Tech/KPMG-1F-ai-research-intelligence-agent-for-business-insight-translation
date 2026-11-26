"""Offline shadow and opt-in preview for source-bound comparison records."""
from dataclasses import asdict
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage-1"))
from source_links import bind, context_from_saved, prose_evidence, quote_covers
from bound_fixtures import PIN
from bound_verify import Comparison, Locator, Operand, Quantity, render, verify

DECIMAL_TEXT = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?")


def claim_digest(claim):
    data = json.dumps(claim, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(data.encode("utf-8")).hexdigest()


def read_locator(data):
    if not isinstance(data, dict) or data.keys() != {"chunk_id", "selector"}:
        raise ValueError("malformed locator")
    chunk_id, selector = data["chunk_id"], data["selector"]
    if not isinstance(chunk_id, str) or not chunk_id:
        raise ValueError("missing chunk ID")
    if isinstance(selector, list) and len(selector) == 2 and all(type(n) is int for n in selector):
        if 0 <= selector[0] < selector[1]:
            return Locator(chunk_id, tuple(selector))
    if isinstance(selector, str) and selector:
        return Locator(chunk_id, selector)
    raise ValueError("malformed span or cell")


def read_operand(data):
    if not isinstance(data, dict) or data.keys() != {"lower", "upper", "unit", "form", "locators"}:
        raise ValueError("malformed operand")
    values = (data["lower"], data["upper"])
    if not all(isinstance(n, str) and len(n) <= 64 and DECIMAL_TEXT.fullmatch(n) for n in values):
        raise ValueError("expected decimal strings")
    if data["unit"] not in ("percent", "proportion", "score", "percentage_points"):
        raise ValueError("unknown unit")
    lower, upper = map(Decimal, values)
    form = data["form"]
    if form not in ("point", "range") or lower > upper or (form == "point" and lower != upper):
        raise ValueError("invalid point or closed range")
    if not isinstance(data["locators"], list) or not data["locators"]:
        raise ValueError("missing locators")
    locators = frozenset(read_locator(row) for row in data["locators"])
    if len(locators) != len(data["locators"]):
        raise ValueError("duplicate locator")
    return Operand(Quantity(lower, upper, data["unit"], form), locators)


def read_record(record, claim):
    if not isinstance(record, dict) or record.keys() != {
        "schema_version", "claim_sha256", "scope", "before", "after"
    } or type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ValueError("unsupported comparison record")
    if record["claim_sha256"] != claim_digest(claim):
        raise ValueError("record belongs to a different claim")
    scope = record["scope"]
    if not isinstance(scope, dict) or not scope or not all(
        isinstance(value, str) and value.strip() for value in scope.values()
    ):
        raise ValueError("missing comparison scope")
    return Comparison(scope.copy(), read_operand(record["before"]), read_operand(record["after"]))


def assess_record(claim, record, context, findings):
    try:
        comparison = read_record(record, claim)
    except ValueError as error:
        return {"status": "review", "reason": str(error)}
    quotes = {}
    for item in claim.get("support", ()):
        if not isinstance(item.get("quote"), str) or not isinstance(item.get("chunk_id"), str):
            return {"status": "review", "reason": "malformed claim citation"}
        quotes.setdefault(item["chunk_id"], set()).add(item["quote"])

    # Match complete cited source sets before evaluating role or metric claims.
    supplied = comparison.before.locators | comparison.after.locators
    candidates = [source for source in findings.values()
                  if supplied == {ref.locator for ref in source.citations}]
    if len(candidates) != 1:
        return {"status": "review", "reason": "no unique trusted comparison for these locations"}
    source, = candidates
    for ref in source.citations:
        chunk = ref.locator.chunk_id
        if chunk not in context or not quote_covers(ref, quotes.get(chunk, ()), context[chunk]["text"]):
            return {"status": "review", "reason": "required source row or span is absent from cited evidence"}
    if any(isinstance(ref.locator.selector, tuple) for ref in source.citations) and not prose_evidence(
        source, context, quotes
    ):
        return {"status": "review", "reason": "no single cited passage binds both ranges and their scope"}
    verdict = verify(source, comparison, context)
    if verdict.status != "accept":
        return asdict(verdict)
    refs = {ref.locator: ref for ref in source.citations}
    locations = {}
    for role in ("before", "after"):
        locators = getattr(source.comparison, role).locators
        locations[role] = [asdict(refs[loc]) for loc in sorted(locators, key=lambda loc: (loc.chunk_id, repr(loc.selector)))]
    return {"status": "linked", "reason": verdict.reason, "links": locations,
            "preview": render(source, comparison, context)}


def observe(envelope, records, parents, findings, *, trial=False):
    """Return the original envelope and a separate diagnostic or trial projection."""
    result = envelope.get("result") or {}
    index = (result.get("provenance") or {}).get("index") or {}
    claims = (result.get("summary") or {}).get("claims") or []
    evidence = result.get("evidence", [])
    context = (context_from_saved(evidence, parents)
               if index.get("indexed_records_sha256") == PIN else {})
    metadata = ("source_sha256", "version_binding", "table_headers", "table_cells")
    for row in evidence:
        parent = context.get(row["chunk_id"])
        if parent is not None and any(key in row and row[key] != parent.get(key) for key in metadata):
            context.pop(row["chunk_id"])
    checks, previews = [], []
    for i, claim in enumerate(claims):
        if i in records:
            decision = assess_record(claim, records[i], context, findings)
            checks.append({"claim_index": i, "path": "structured", **decision})
            if trial and decision["status"] == "linked":
                previews.append({"claim_index": i, "text": decision["preview"],
                                 "links": decision["links"], "human_review": "pending"})
        elif re.search(r"[0-9]", claim["text"]):
            decision = bind(claim, context, findings)
            checks.append({"claim_index": i, "path": "legacy", "status": decision.status,
                           "reason": decision.reason})
    return {"answer": envelope, "checks": checks, "trial_comparisons": previews}

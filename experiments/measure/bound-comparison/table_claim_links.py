"""Read complete, labeled point comparisons grounded in audited table cells."""
from dataclasses import replace
from decimal import Decimal
import re

from bound_fixtures import table_finding
from bound_verify import Comparison, Quantity
from source_links import LinkResult, normalized

NUMBER = r"[+-]?(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"


def point(text):
    value = normalized(text)
    if not re.fullmatch(NUMBER, value):
        raise ValueError("unsupported table cell value")
    return Decimal(value.replace(",", ""))


def claim_text(text, source_texts):
    def explicit_alias(match):
        words = match[1].split("-")
        phrase = r"(?<!\w)" + r"[ -]+".join(map(re.escape, words)) + r"(?!\w)"
        if "".join(word[0] for word in words) == match[2] and any(
            re.search(phrase, source) for source in source_texts
        ):
            return match[2]
        return match[0]

    return re.sub(r"\b([a-z]+(?:-[a-z]+)+) \(([a-z]+)\)", explicit_alias, normalized(text))


def quoted_rows(claim, context):
    rows = {}
    for support in claim.get("support", ()):
        chunk = support["chunk_id"]
        parent = context.get(chunk)
        if not parent or not parent.get("table_id"):
            continue
        serialize = "; ".join(f"{h['text']}: {c['text']}"
                              for h, c in zip(parent["table_headers"], parent["table_cells"], strict=True))
        quote = " ".join(support["quote"].split())
        if " ".join(serialize.split()) in quote and quote in " ".join(parent["text"].split()):
            rows[chunk] = parent
    return rows


def table_comparison(claim, context, tables):
    rows = quoted_rows(claim, context)
    keys = {(p["arxiv_id"], p["table_id"]) for p in rows.values()}
    if len(keys) != 1:
        return None
    key, = keys
    table = tables.get(key)
    if not table:
        return None
    headers = [h["indexed"]["text"] for h in table["headers"]]
    scope = {"subject": next(iter(rows.values()))["title"], "setting": table["caption"]}
    if len(rows) == 1 and len(headers) == 3 and headers[0].lower() == "metric":
        metric = next(iter(rows.values()))["table_cells"][0]["text"]
        left, right = headers[1:]
        scope["metric"] = metric
        if not normalized(left).startswith("with ") or normalized(right) != normalized(left).replace("with ", "without ", 1):
            return None
        selections = ([((metric,), left)], [((metric,), right)])
        subject = re.escape(normalized(metric))
        lead = rf"(?:(?:the (?:researchers|authors) reported )?{subject} scores? (?:of|were) |{subject} was )"
        unit = "score"
    elif len(rows) == 2 and len(headers) == 2 and headers[1].lower() == "count":
        caption = re.fullmatch(r"(?:table [\w.]+:\s*)?(.+?) composition\.?", normalized(table["caption"]))
        if not caption:
            return None
        left, right = (p["table_cells"][0]["text"] for p in rows.values())
        scope["metric"] = "count"
        selections = ([((left,), headers[1])], [((right,), headers[1])])
        lead = rf"(?:the )?{re.escape(caption[1])} contained "
        unit = "count"
    else:
        return None

    labels = (left, right)
    names = tuple(re.escape(normalized(label)) for label in labels)
    if names[0] == names[1]:
        return None
    text = claim_text(claim["text"], [normalized(p["text"]) for p in context.values()
                                     if p["arxiv_id"] == key[0]])
    for a, b in ((0, 1), (1, 0)):
        first = rf"(?P<a>{NUMBER}) {names[a]}"
        second = rf"(?P<b>{NUMBER}) {names[b]}"
        tail = rf"(?:\. (?:the condition )?(?P<winner>{names[0]}|{names[1]}) (?:had the higher score|(?:was|were) the larger group))?\.?"
        match = re.fullmatch(lead + first + " and " + second + tail, text)
        if not match:
            continue
        values = [None, None]
        values[a], values[b] = point(match["a"]), point(match["b"])
        if match["winner"] is not None:
            winner = 0 if match["winner"] == normalized(left) else 1
            if values[winner] <= values[1 - winner]:
                return LinkResult("reject", "comparison direction disagrees with the stated values"), None
        try:
            source = table_finding(table, rows, scope, labels, selections, unit, read_number=point)
        except (KeyError, ValueError, ArithmeticError):
            return None
        before, after = (replace(operand, value=Quantity(value, value, unit, "point"))
                         for operand, value in zip((source.comparison.before, source.comparison.after),
                                                   values, strict=True))
        return LinkResult("proposed", "exact labeled table operands", "cited-table",
                          Comparison(scope.copy(), before, after)), source
    return None

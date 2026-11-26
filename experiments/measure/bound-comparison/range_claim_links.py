"""Bind explicit comparison ranges to independently source-checked table column groups."""
from dataclasses import replace
import re

from bound_fixtures import table_finding
from bound_verify import Comparison, Quantity, passage_sha256
from source_links import LinkResult, normalized
from table_claim_links import NUMBER, point, quoted_rows

ROW = re.compile(r"(?:our )?(?P<method>[\w-]+) \[w/\s*ft\s+(?P<model>[^\]]+)\]\s*(?P<modifier>.*)")


def configured_method(row):
    parsed = ROW.fullmatch(normalized(row["table_cells"][0]["text"]))
    if parsed is None:
        return None
    modifier = re.sub(r"^w/o\s+", "without ", parsed["modifier"])
    modifier = re.sub(r"^w/\s+", "with ", modifier)
    return parsed["method"], parsed["model"].strip(), modifier


def range_comparison(claim, context, tables, profiles, pinned):
    rows = quoted_rows(claim, context)
    keys = {(p["arxiv_id"], p["table_id"]) for p in rows.values()}
    if len(rows) != 2 or len(keys) != 1:
        return None
    key, = keys
    profile, table = profiles.get(key), tables.get(key)
    if not profile or not table:
        return None
    scope_parent = pinned.get(profile["scope_chunk"])
    if (not scope_parent or scope_parent["arxiv_id"] != key[0]
            or profile["scope_text"] not in scope_parent["text"]
            or profile["metric_text"] not in table["caption"]):
        return None
    parsed = [configured_method(row) for row in rows.values()]
    if any(item is None for item in parsed) or parsed[0][0] == parsed[1][0] or parsed[0][1] != parsed[1][1]:
        return None
    columns = profile["columns"]
    if len(columns) != 3 or len(set(columns)) != len(columns):
        return None
    methods = [item[0] for item in parsed]
    model = parsed[0][1]
    labels = tuple(" ".join(filter(None, (method, modifier))) for method, _, modifier in parsed)
    suite = normalized(profile["suite"])
    metric = normalized(profile["metric"])
    scope = {"subject": next(iter(rows.values()))["title"], "metric": profile["metric"],
             "setting": profile["suite"], "configuration": model, "subsets": ", ".join(columns)}
    selections = [[((p["table_cells"][0]["text"],), column) for column in columns] for p in rows.values()]
    try:
        source = table_finding(table, rows, scope, labels, selections, "score", read_number=point)
    except (KeyError, ValueError, ArithmeticError):
        return None
    proof = {"chunk_id": scope_parent["chunk_id"], "source_url": scope_parent["source_url"],
             "passage_sha256": passage_sha256(scope_parent), "quote": profile["scope_text"],
             "in_synthesis_packet": scope_parent["chunk_id"] in context,
             "metric_caption_excerpt": profile["metric_text"]}
    source = replace(source, scope_provenance=proof)
    lead = (r"with fine[- ]tuned (?P<model>[\w.-]+), (?P<metric>[\w -]+?) score ranges across "
            r"the three (?P<suite>[\w-]+) subsets were ")

    def endpoint(i):
        return (rf"(?P<lo{i}>{NUMBER})\s*-\s*(?P<hi{i}>{NUMBER}) for "
                + re.escape(methods[i]) + rf"(?: (?P<modifier{i}>with(?:out)? [\w -]+?))?")

    for a, b in ((0, 1), (1, 0)):
        match = re.fullmatch(lead + endpoint(a) + " and " + endpoint(b) + r"\.?",
                             normalized(claim["text"]))
        if not match:
            continue
        if match["model"] != model or match["metric"] != metric or match["suite"] != suite:
            return LinkResult("reject", "stated model, metric, or subset group differs from the cited rows"), None
        for i, (_, _, qualifier) in enumerate(parsed):
            asserted = match[f"modifier{i}"] or ""
            if qualifier and not asserted:
                return None  # Omitted configuration is ambiguous.
            if asserted != qualifier:
                return LinkResult("reject", "stated method configuration differs from its cited row"), None
        values = [(point(match[f"lo{i}"]), point(match[f"hi{i}"])) for i in range(2)]
        if any(lower > upper for lower, upper in values):
            return LinkResult("reject", "range lower endpoint exceeds its upper endpoint"), None
        operands = [replace(value, value=Quantity(*endpoints, "score", "range"))
                    for value, endpoints in zip((source.comparison.before, source.comparison.after),
                                                values, strict=True)]
        return LinkResult("proposed", "exact method and range operands", "cited-table-range",
                          Comparison(scope.copy(), *operands)), source
    return None

"""Zero-call numerical shadow adapter for the experimental Research Agent."""
from dataclasses import asdict
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "stage-1"))
from source_links import propose, read_value
from bound_fixtures import citation, read, table_finding
from bound_verify import Comparison, Finding, Locator, Operand, Quantity, passage_sha256, verify
from table_claim_links import table_comparison
from range_claim_links import range_comparison

PERCENT = r"[+\-−]?\d+(?:\.\d+)?(?:\s*[–−-]\s*[+\-−]?\d+(?:\.\d+)?)?%"
# A deliberately complete source clause grammar. Other scientific syntax is reviewed.
SOURCE = re.compile(
    rf"(?:^|(?<=[.!?])\s+)On (?P<setting>[^,.!?;]+),\s+"
    rf"(?P<subject>[^,.!?;]+?) improves (?P<metric>[^,.!?;]+?) "
    rf"from (?P<before>{PERCENT}) to (?P<after>{PERCENT}) across "
    rf"(?P<population>[^,.!?;]+?)(?=\.|$|, yielding )"
)


def from_prose(parent):
    matches = list(SOURCE.finditer(parent["text"]))
    if len(matches) != 1:
        return None
    source, = matches
    scope = {key: source[key] for key in ("subject", "metric", "setting", "population")}
    refs, operands = [], []
    for role in ("before", "after"):
        loc = Locator(parent["chunk_id"], source.span(role))
        value = read_value(source[role], Quantity(None, None, "percent", "range"))
        refs.append(citation(parent, loc, source[role]))
        operands.append(Operand(value, frozenset({loc})))
    return Finding(Comparison(scope, *operands), "the before range", "the after range", tuple(refs),
                   comparison_kind="temporal")


class NumericalShadow:
    """Build source facts from delivered passages, then parse proposed claims separately."""
    def __init__(self, pinned_parents, audited_tables=()):
        self.pinned_parents = pinned_parents
        self.tables = {(row["arxiv_id"], row["table_id"]): row for row in audited_tables}
        self.range_profiles = {(row["paper"], row["table_id"]): row
                               for row in read(HERE / "range-scopes.json")}

    def source_for(self, parent):
        table_id = parent.get("table_id")
        if not table_id:
            return from_prose(parent)
        table = self.tables.get((parent["arxiv_id"], table_id))
        if not table or len(table["headers"]) != 3:
            return None
        first, left, right = (h["indexed"]["text"] for h in table["headers"])
        row = (parent["table_cells"][0]["text"],)
        if first == "Metric":
            metric = row[0]
        elif first == "Task" and left.endswith(" AUC") and right.endswith(" AUC"):
            metric = "AUC"
        else:
            return None
        scope = dict(subject=parent["title"], metric=metric, setting=table["caption"])
        if first == "Task":
            scope["population"] = row[0]
        return table_finding(table, {parent["chunk_id"]: parent}, scope, (left, right),
                             ([(row, left)], [(row, right)]), "proportion" if metric == "AUC" else "score")

    def produce(self, claims, passages):
        context = {parent["chunk_id"]: parent for parent in passages}
        findings = {}
        trusted = {}
        for key, parent in context.items():
            original = self.pinned_parents.get(key)
            if original is None or passage_sha256(parent) != passage_sha256(original):
                continue
            trusted[key] = parent
            try:
                if (finding := self.source_for(parent)) is not None:
                    findings[key] = finding
            except (ValueError, KeyError, IndexError, ArithmeticError):
                continue  # An incomplete or unauditable source remains unbound.
        batch = []
        for i, claim in enumerate(claims):
            if claim.get("kind") != "finding" or not re.search(r"[0-9]", claim["text"]):
                continue
            proposal = propose(claim, trusted, findings)
            if proposal.status == "review":
                linked = table_comparison(claim, trusted, self.tables)
                if linked is None:
                    linked = range_comparison(claim, trusted, self.tables, self.range_profiles, self.pinned_parents)
                if linked is not None:
                    proposal, source = linked
                    batch.append((i, proposal, {proposal.finding: source} if source else {}))
                    continue
            batch.append((i, proposal, findings))
        return batch

    def check(self, batch, passages, existing):
        context = {parent["chunk_id"]: parent for parent in passages}
        old = {row["index"]: row for row in existing}
        observations = []
        for index, proposal, findings in batch:
            row = dict(claim_index=index, producer_status=proposal.status, status=proposal.status,
                       reason=proposal.reason, current_decision=old.get(index, {}).get("decision"),
                       current_numeric=old.get(index, {}).get("number_grounding", {}).get("status"))
            if proposal.comparison:
                source = findings[proposal.finding]
                decision = verify(source, proposal.comparison, context)
                labels = ("left", "right") if source.comparison_kind == "categorical" else ("before", "after")
                row.update(asdict(decision), proposal=asdict_comparison(proposal.comparison, labels),
                           comparison_kind=source.comparison_kind,
                           source_role_labels=dict(zip(labels, (source.before_label, source.after_label), strict=True)),
                           source_links=[asdict(ref) for ref in source.citations])
                if source.scope_provenance:
                    row["scope_provenance"] = source.scope_provenance
            observations.append(row)
        return observations


def asdict_comparison(comparison, labels=("before", "after")):
    result = {"scope": comparison.scope}
    for role, item in zip(labels, (comparison.before, comparison.after), strict=True):
        result[role] = dict(lower=str(item.value.lower), upper=str(item.value.upper),
                            form=item.value.form, unit=item.value.unit,
                            locators=[asdict(ref) for ref in sorted(item.locators, key=repr)])
    return result

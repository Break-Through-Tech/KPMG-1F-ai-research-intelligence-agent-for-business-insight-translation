"""Pinned source selections and provider-shaped records for the offline trial."""
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from structured_trial import claim_digest
from bound_fixtures import PIN, TABLES, read, selections, table_finding


def fresh_tables(parents):
    tables = {(row["arxiv_id"], row["table_id"]): row for row in read(TABLES)["records"]}
    models = (("Claude-3-Opus",), ("Claude-3.5-Sonnet",), ("Claude-3.5-Haiku",))
    groups = (("gpt-4-1106-preview+RAG", "gpt-4-1106-preview"), ("gpt-4-1106-preview+RAG", "human"))
    a, b = (groups[0],), (groups[1],)
    group_scope = {
        "subject": "GPT-4-1106-preview with RAG", "setting": "Comparison of Groups",
        "population": "GPT-4 without RAG and human comparison groups",
    }
    table = tables["2410.16285v1", "A1.tab1"]
    labels = ("the GPT-4 comparison", "the human comparison")
    return {
        "benchmark": table_finding(
            tables["2412.14470v2", "S4.T6"], parents,
            dict(subject="Claude models", metric="reported safety score", setting="Agent-SafetyBench Table 6",
                 population="Claude-3-Opus, Claude-3.5-Sonnet, and Claude-3.5-Haiku"),
            ("the M1 range", "the M2 range"),
            (selections(models, ("M1",)), selections(models, ("M2",))), "score",
        ),
        "signed": table_finding(
            table, parents, group_scope | {"metric": "reported mean difference"}, labels,
            (selections(a, ("Mean Diff",)), selections(b, ("Mean Diff",))), "score",
        ),
        "interval": table_finding(
            table, parents, group_scope | {"metric": "reported lower and upper bounds"}, labels,
            (selections(a, ("Lower", "Upper")), selections(b, ("Lower", "Upper"))), "score",
        ),
    }


def envelope_for(finding, parents, text):
    rows = {ref.locator.chunk_id: parents[ref.locator.chunk_id] for ref in finding.citations}
    claim = {"kind": "finding", "text": text, "support": [
        {"chunk_id": chunk, "quote": row["text"]} for chunk, row in rows.items()
    ]}
    return {
        "result": {
            "human_review": {"status": "pending", "reviewer": None, "notes": None},
            "approved": False,
            "summary": {"status": "ok", "claims": [claim]},
            "evidence": list(rows.values()),
            "provenance": {"index": {"indexed_records_sha256": PIN}},
        },
    }


def record_for(claim, finding, before, after, unit):
    def operand(role, values):
        locators = getattr(finding.comparison, role).locators
        return {
            "lower": values[0], "upper": values[-1], "unit": unit,
            "form": "range" if len(values) > 1 else "point",
            "locators": [{"chunk_id": loc.chunk_id, "selector": list(loc.selector)
                          if isinstance(loc.selector, tuple) else loc.selector}
                         for loc in sorted(locators, key=lambda loc: (loc.chunk_id, repr(loc.selector)))],
        }
    return {
        "schema_version": 1, "claim_sha256": claim_digest(claim), "scope": finding.comparison.scope.copy(),
        "before": operand("before", before), "after": operand("after", after),
    }


def authored_case(parents, sources, spec):
    key, text, before, after, unit = spec
    envelope = envelope_for(sources[key], parents, text)
    claim = envelope["result"]["summary"]["claims"][0]
    return envelope, record_for(claim, sources[key], before, after, unit)


def shadow_controls(parents, sources):
    for spec in (
        ("cu", "Across seven models, the accuracy went from 35 to 46 percent before training to 68 to 78 percent afterward.",
         ("35", "46"), ("68", "78"), "percent"),
        ("hammer", "For the two AIME years, the paired HAMMER comparison was 25.3 to 36.3 against 31.0 to 39.3.",
         ("25.3", "36.3"), ("31.0", "39.3"), "score"),
        ("acdc", "The two tasks show a 50 percent random baseline and 92 to 95 percent for ACDC.",
         ("50", "50"), ("92", "95"), "percent"),
        ("agreemate", "The fairness score was 0.3021 without CoT and negative 0.4385 with it.",
         ("0.3021",), ("-0.4385",), "score"),
    ):
        env, record = authored_case(parents, sources, spec)
        yield spec[0], "linked", env, record
        wrong = deepcopy(record)
        wrong["scope"]["metric"] = "a different metric"
        yield spec[0] + "-wrong-metric", "reject", env, wrong


def trial_cases(parents, sources):
    records = {}
    for spec in (
        ("benchmark", "For the three Claude models, M1 ranges from 86.2 to 89.8 and M2 from 15.2 to 36.6.",
         ("86.2", "89.8"), ("15.2", "36.6"), "score"),
        ("signed", "Table A1 lists negative mean differences for the two comparisons.",
         ("-5.9471",), ("-6.2272",), "score"),
        ("interval", "The reported bounds are negative for both group contrasts.",
         ("-7.2174", "-4.6767"), ("-7.5017", "-4.9528"), "score"),
    ):
        env, record = authored_case(parents, sources, spec)
        records[spec[0]] = env, record
        yield spec[0], "linked", env, record

    env, record = records["benchmark"]
    for scope_field, value in (("metric", "real-world incident rate"), ("population", "all evaluated models")):
        wrong = deepcopy(record)
        wrong["scope"][scope_field] = value
        yield "wrong-" + scope_field, "reject", env, wrong
    swapped = deepcopy(record)
    swapped["before"], swapped["after"] = swapped["after"], swapped["before"]
    yield "roles-swapped", "reject", env, swapped
    wrong = deepcopy(record)
    wrong["before"]["upper"] = "89.80000000000000000001"
    yield "hidden-decimal-drift", "reject", env, wrong
    wrong = deepcopy(record)
    wrong["after"]["unit"] = "percentage_points"
    yield "wrong-unit", "reject", env, wrong
    wrong = deepcopy(record)
    wrong["after"]["locators"][0]["selector"] = "unknown-cell"
    yield "unknown-cell", "review", env, wrong
    wrong = deepcopy(record)
    wrong["claim_sha256"] = "0" * 64
    yield "record-for-different-claim", "review", env, wrong
    changed = deepcopy(env)
    changed["result"]["evidence"].pop()
    yield "row-missing", "review", changed, record
    changed = deepcopy(env)
    changed["result"]["provenance"]["index"]["indexed_records_sha256"] = "0" * 64
    yield "wrong-index", "review", changed, record
    changed = deepcopy(env)
    changed["result"]["evidence"][0]["text"] += " Altered."
    yield "changed-evidence", "review", changed, record
    changed = deepcopy(env)
    changed["result"]["evidence"][0]["table_cells"][2]["text"] = "99.9"
    yield "changed-table-cell-metadata", "review", changed, record

    env, record = records["signed"]
    wrong = deepcopy(record)
    wrong["after"]["lower"] = wrong["after"]["upper"] = "6.2272"
    yield "sign-flipped", "reject", env, wrong

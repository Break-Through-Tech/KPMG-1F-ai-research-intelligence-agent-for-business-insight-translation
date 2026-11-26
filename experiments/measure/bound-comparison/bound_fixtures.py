"""Build trusted findings from the pinned parents and the existing DOM audit."""
from decimal import Decimal
from pathlib import Path
import sys

from bound_verify import Citation, Comparison, Finding, Locator, Operand, Quantity, passage_sha256
from adapter import quantity, tokens

MEASURE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MEASURE))
from common import BUNDLE, PIN, digest, read, rows

FROZEN = MEASURE / "run-02/verification.json"
BOUNDARIES = MEASURE / "structured-ranges/boundary-results.json"
TABLES = MEASURE / "run-02/tables-dom-normalized.json"
PARENTS = BUNDLE / "parents.jsonl"
ABSTRACT = "2602.00931v2_c0000"


def citation(parent, locator, text, header=None):
    return Citation(
        locator, parent["arxiv_id"], parent["source_url"], parent.get("source_sha256"),
        passage_sha256(parent), text,
        tuple(header["DOM_header_path"]) if header else (),
        header["indexed"]["source_id"] if header else None, parent.get("table_id"),
    )


def abstract_finding(parent, frozen_quote):
    text = parent["text"]
    start = text.index("On mathematical reasoning benchmarks,")
    if parent["arxiv_id"] != "2602.00931v2" or text[start:] != frozen_quote:
        raise ValueError("CU-DPO source binding changed")
    scope = {
        "subject": "CU-DPO", "metric": "strategy selection accuracy",
        "setting": "mathematical reasoning benchmarks", "population": "seven base models",
    }
    operands, refs = [], []
    # Each annotation names the role and exact source token sequence.
    for literal in ("35–46%", "68–78%"):
        offset = text.index(literal, start)
        loc = Locator(parent["chunk_id"], (offset, offset + len(literal)))
        words = tokens(text[offset:loc.selector[1]])
        value, end = quantity(words, 0, "percent")
        if end != len(words):
            raise ValueError("annotated span contains unexpected tokens")
        operands.append(Operand(value, frozenset({loc})))
        refs.append(citation(parent, loc, literal))
    return Finding(Comparison(scope, *operands), "the before-training range",
                   "the after-training range", tuple(refs))


def table_finding(table, parents, scope, labels, selections, unit, *, read_number=Decimal):
    if table["status"] != "structural_agreement" or not table["audit_original_rows_identical"]:
        raise ValueError(f"table structure not verified: {table['table_id']}")
    operands, refs = [], []
    for role in selections:
        role_refs, values = [], []
        for prefix, column in role:
            header, = (h for h in table["headers"] if h["indexed"]["text"] == column)
            row, = (
                r for r in table["rows"]
                if tuple(c["indexed"]["text"] for c in r["cells"][:len(prefix)]) == prefix
            )
            index = header["indexed"]["column"]
            cell = row["cells"][index]
            parent = parents[row["chunk_id"]]
            if (
                header["status"] != "agrees" or cell["status"] != "agrees"
                or any(c["status"] != "agrees" for c in row["cells"][:len(prefix)])
                or parent["arxiv_id"] != table["arxiv_id"]
                or parent["table_id"] != table["table_id"]
                or parent["source_sha256"] != table["source_sha256"]
                or parent["source_url"] != table["source_url"]
                or parent["table_headers"][index] != header["indexed"]
                or parent["table_cells"][index] != cell["indexed"]
            ):
                raise ValueError(f"table binding changed: {row['chunk_id']} {column}")
            loc = Locator(row["chunk_id"], cell["indexed"]["source_id"])
            values.append(read_number(cell["indexed"]["text"]))
            role_refs.append(citation(parent, loc, cell["indexed"]["text"], header))
        form = "point" if len(values) == 1 else "range"
        value = Quantity(min(values), max(values), unit, form)
        operands.append(Operand(value, frozenset(ref.locator for ref in role_refs)))
        refs.extend(role_refs)
    return Finding(Comparison(scope, *operands), *labels, tuple(refs), comparison_kind="categorical")


def selections(row_labels, columns):
    return [(labels, column) for labels in row_labels for column in columns]


def load():
    if digest(PARENTS) != PIN:
        raise ValueError("demo-100 parent digest differs")
    parents = {parent["chunk_id"]: parent for parent in rows(PARENTS)}
    tables = {(t["arxiv_id"], t["table_id"]): t for t in read(TABLES)["records"]}
    cases = read(FROZEN)["cases"]
    frozen_case = next(row for row in cases if row["name"] == "correct paired ranges")
    cu = abstract_finding(parents[ABSTRACT], frozen_case["claim"]["support"][0]["quote"])
    aime = (("Qwen3-1.7B-DAPO", "AIME 2024"), ("Qwen3-1.7B-DAPO", "AIME 2025"))
    tasks = (("IOI",), ("Docstring",))
    api = ("HF", "Torch Hub", "TF Hub")
    return parents, {
        "cu": cu,
        "hammer": table_finding(
            tables["2509.25240v1", "S5.T1"], parents,
            dict(subject="Qwen3-1.7B-DAPO", metric="pass@1", setting="benchmark evaluation",
                 population="AIME 2024 and AIME 2025", qualifier="k=100"),
            ("the baseline range", "the HAMMER range"),
            (selections(aime, ("pass@1 / B",)), selections(aime, ("pass@1 / H",))), "score",
        ),
        "acdc": table_finding(
            tables["2604.00324v1", "A1.T1"], parents,
            dict(subject="ACDC", metric="AUC", setting="random baseline experiment",
                 population="IOI and Docstring"),
            ("the random baseline range", "the ACDC range"),
            (selections(tasks, ("Random AUC",)), selections(tasks, ("ACDC AUC",))), "proportion",
        ),
        "accuraterag": table_finding(
            tables["2510.02243v2", "S2.T2"], parents,
            dict(subject="fine-tuned Llama-2-7B", metric="AST-match score", setting="APIBench",
                 population="HF, Torch Hub, and TF Hub"),
            ("the RAFT with GPT-4 CoT range", "the AccurateRAG range"),
            (selections((("RAFT [w/ FT Llama-2-7B ] w/ GPT-4 CoT",),), api),
             selections((("Our AccurateRAG [w/ FT Llama-2-7B ]",),), api)), "score",
        ),
        "agreemate": table_finding(
            tables["2412.18690v1", "S6.T3"], parents,
            dict(subject="AgreeMate", metric="fairness score", setting="negotiation experiment"),
            ("the score without CoT", "the score with CoT"),
            (selections((("Fairness",),), ("Without COT",)),
             selections((("Fairness",),), ("With COT",))), "score",
        ),
    }

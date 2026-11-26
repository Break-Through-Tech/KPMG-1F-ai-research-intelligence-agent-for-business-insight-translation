"""Replay saved claims and isolated regression cases without generation."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from source_links import bind, context_from_saved, normalized
from bound_fixtures import MEASURE, PIN, digest, load, read

ARCHIVE = MEASURE / "run-02/saved-traces.json"
PRIOR = HERE.parent / "results.json"
INPUT_HASHES = {
    ARCHIVE: "cb7c0625b23b09f9c0656efe81f6c17eba8c82c27d7dd5024b9a773bb33871a5",
    PRIOR: "4e28c19eb6f1218af291b62d0a2e692e9958767af817450ce0e9cb646ca52800",
}


def assess(claim, context, findings):
    link = bind(claim, context, findings)
    result = {"status": link.status, "reason": link.reason}
    if link.comparison:
        record = findings[link.finding]
        refs = {ref.locator: ref for ref in record.citations}
        operands = {}
        for role in ("before", "after"):
            source = getattr(link.comparison, role)
            locations = sorted(source.locators, key=lambda loc: (loc.chunk_id, repr(loc.selector)))
            operands[role] = {
                "label": getattr(record, role + "_label"),
                "claim_value": asdict(source.value), "source_links": [asdict(refs[loc]) for loc in locations],
            }
        result.update(finding=link.finding, scope=link.comparison.scope, operands=operands)
    return result


def archive_cases(parents, findings):
    results, snapshots = [], []
    for answer in read(ARCHIVE)["recorded"]:
        context = context_from_saved(answer["evidence"], parents) if answer["index"] == PIN else {}
        claims = answer["summary"]["claims"]
        snapshots.append({"version": answer["version"], "claims": len(claims),
                          "evidence_rows": len(answer["evidence"]), "matched_parents": len(context)})
        for index, claim in enumerate(claims):
            if not re.search(r"[0-9]", normalized(claim["text"])):
                continue
            results.append(dict(version=answer["version"], claim_index=index, question=answer["question"],
                                claim=claim, **assess(claim, context, findings)))
    return snapshots, results


def earlier_cases(parents, findings):
    for previous in read(PRIOR)["cases"]:
        if previous["cohort"] == "frozen non-range":
            continue
        claim = previous["original_claim"]
        context = {chunk: parents[chunk] for chunk in previous["delivered_chunk_ids"]}
        yield dict(name=previous["name"], cohort=previous["cohort"], reviewed=previous["reviewed"],
                   expected=previous["expected"], claim=claim, **assess(claim, context, findings))


def table_controls(parents, findings):
    """Source-checked claims expressed in the declared, fully scoped table form."""
    rag = ("For AST-match score (fine-tuned Llama-2-7B, APIBench, HF, Torch Hub, and TF Hub), "
           "the RAFT with GPT-4 CoT range was 74.00–86.86 and the AccurateRAG range was 68.36–88.71.")
    auc = ("For AUC (ACDC, random baseline experiment, IOI and Docstring), "
           "the random baseline range was 50–50% and the ACDC range was 92–95%.")
    agree = ("For fairness score (AgreeMate, negotiation experiment), "
             "the score without CoT was 0.3021 and the score with CoT was −0.4385.")
    controls = (
        ("accuraterag", "APIBench labeled ranges", "accept", rag),
        ("accuraterag", "same digits, different benchmark", "reject", rag.replace("APIBench", "PubMedQA")),
        ("accuraterag", "swapped range endpoints", "reject", rag.replace("68.36–88.71", "68.36–86.86")),
        ("acdc", "equivalent percent representation", "accept", auc),
        ("acdc", "percentage points in place of levels", "reject", auc.replace("%", " percentage points")),
        ("agreemate", "signed fairness scores", "accept", agree),
        ("agreemate", "flipped sign", "reject", agree.replace("−0.4385", "0.4385")),
    )
    for key, name, expected, text in controls:
        context = {ref.locator.chunk_id: parents[ref.locator.chunk_id] for ref in findings[key].citations}
        claim = {"text": text, "support": [
            {"chunk_id": chunk, "quote": parent["text"]} for chunk, parent in context.items()
        ]}
        yield dict(name=name, cohort="labeled table control", reviewed=False,
                   expected=expected, claim=claim, **assess(claim, context, findings))


def replay():
    for path, expected in INPUT_HASHES.items():
        if digest(path) != expected:
            raise ValueError(f"replay input has changed: {path.name}")
    parents, findings = load()
    snapshots, archive = archive_cases(parents, findings)
    earlier = list(earlier_cases(parents, findings))
    controls = list(table_controls(parents, findings))
    return dict(
        python=sys.version.split()[0], provider_calls=0,
        input_sha256={path.name: value for path, value in INPUT_HASHES.items()} | {"parents.jsonl": PIN},
        snapshots=snapshots, archive=archive, earlier_cases=earlier, table_controls=controls,
        counts=dict(archive=dict(Counter(case["status"] for case in archive)),
                    earlier=dict(Counter(case["status"] for case in earlier)),
                    table=dict(Counter(case["status"] for case in controls))),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new JSON filename in this directory")
    args = parser.parse_args()
    if args.output and (args.output.name != str(args.output) or args.output.suffix != ".json"):
        parser.error("use a new JSON filename without directories")
    result = replay()
    if args.output:
        with (HERE / args.output).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False, default=str)
            handle.write("\n")
    print(json.dumps(result["counts"], indent=2))


if __name__ == "__main__":
    main()

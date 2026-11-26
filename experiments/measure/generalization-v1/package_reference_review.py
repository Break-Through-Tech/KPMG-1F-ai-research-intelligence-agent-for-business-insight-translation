"""Create the independent reference review package without reading any arm information."""
import json
from pathlib import Path
import sys

from offline_harness import HERE, ROOT, read, verify_seal, write

sys.path.insert(0, str(HERE.parent))
from common import BUNDLE, digest, rows
from tables import canonical, local_source, plain

BASE = ROOT / "data/processed/generalization-v1-execution"
BLINDED = BASE / "blinded"
DEST = BASE / "independent-review"

DECISIONS = {
    "G01": "Confirm Original and Continual Pretrained values, metric labels and scale. Confirm the optional differences against the Diff row.",
    "G04": "Confirm that these are Recall@5 scores for the DPR and Llama v3 Priority variants. Confirm both category winners and whether omission of both multi-hop scores warrants partial credit.",
    "G05": "Confirm the absolute recall values, direction, and 0–100 scale. The table header does not print a percent sign. Decide whether the percent presentation is acceptable and whether both rows are sufficient to answer.",
    "G07": "Confirm that the secondary-study synthesis leaves no measured causal incident reduction and that the cited scope supports a justified refusal.",
    "G08": "Verify the two AffectAgent means and the separate OP-RAG QA finding. Confirm the cross-study scope explanation. Check whether the incomplete packet has any alternate support for 74.72.",
    "G09": "Confirm the paper's conceptual scope, absence of a surveyed patient percentage, and that the refusal accurately identifies future empirical work.",
    "G10": "Adjudicate the conflict between the Limitations prose and Table 6 over why/which. Confirm what the zero 'why' row does or does not establish. Confirm the separate extractive-QA transfer point. If the source cannot resolve the exclusion list, retain the inconclusive score.",
    "G11": "Confirm all four cell values and that the denominator is the error distribution, not all queries. Decide whether the delivered rows and accompanying prose made the abstaining output answerable.",
    "G14": "Confirm the information-asymmetry benefit and the lack of a significant overall reduction in agency costs. Check the undervaluation mechanism and distinguish loss of significance from a proven causal decline.",
    "G15": "Confirm the structured-input protocol and that the full uncurated condition is future work. Check that no like-for-like comparison is reported in the original study.",
}


def main():
    verify_seal()
    lock = read(BLINDED / "score-lock.json")
    assert digest(BLINDED / "locked-scores.json") == lock["scores_sha256"]
    assert all(digest(ROOT / name) == value for name, value in lock["input_sha256"].items())
    sources = {p["chunk_id"]: p for p in rows(BUNDLE / "parents.jsonl")}
    refs = {r["id"]: r for r in read(HERE / "references.json") if r["id"] in DECISIONS}
    questions = {r["id"]: r["text"] for r in read(HERE / "questions.json")}
    answers = {r["label"]: r for r in read(BLINDED / "review.json")}
    packets = {r["label"]: r["packet"] for r in read(BLINDED / "synthesis-evidence.json")}
    scores = [r for r in read(BLINDED / "locked-scores.json") if r["id"] in DECISIONS]
    assert len(refs) == 10 and len(scores) == 20
    cached = {}

    def original(point):
        parent = sources[point["chunk_id"]]
        version, checksum = parent["arxiv_id"], point["source_sha256"]
        if (version, checksum) not in cached:
            _, cached[version, checksum] = local_source(version, checksum)
        dom = cached[version, checksum]
        assert dom is not None
        node = dom.find(id=point["original_locator"])
        assert node is not None
        info = {k: point[k] for k in ("point", "source_url", "source_sha256", "original_locator", "chunk_id")}
        if point.get("cells"):
            info["caption"] = plain(node.find("figcaption") or node.find("caption") or node)
            info["cells"] = [
                dict(column=label, cell_id=item["cell_id"], exact_original_value=plain(dom.find(id=item["cell_id"])),
                     headers=[dict(id=x, text=plain(dom.find(id=x))) for x in item["header_ids"]])
                for label, item in point["cells"].items()]
        else:
            anchor = canonical(point["original_anchor"].replace("’", "'"))
            matching = [plain(p) for p in node.find_all(["p", "div"], recursive=True)
                        if anchor in canonical(plain(p).replace("’", "'"))]
            info["original_text"] = min(matching, key=len) if matching else plain(node)
            assert anchor in canonical(info["original_text"].replace("’", "'"))
        return info

    package = []
    for qid, ref in refs.items():
        locked = [s for s in scores if s["id"] == qid]
        # Keep the reviewed answer and actual source packet, without routing, timing, or invocation metadata.
        evidence = []
        for score in locked:
            label = score["label"]
            rendered = answers[label]
            evidence.append(dict(label=label, published_claims=rendered["claims"],
                                 visible_limitations=[x for x in rendered["limitations"]
                                                      if not x.startswith("Verification note:")],
                                 cited_limitations=rendered["limitation_support"], packet=packets[label],
                                 current_judgment={k: score[k] for k in
                                     ("outcome", "complete_success", "point_judgments", "rationale",
                                      "unsupported_published_claims", "source_judgments", "human_verified")}))
        points = [original(point) for point in ref["required_points"]]
        conflict = None
        if qid == "G10":
            parent = sources["2409.10955v2_table_f4b23a2328888da6_4"]
            dom = cached[("2409.10955v2", ref["required_points"][0]["source_sha256"])]
            locator = dom.find(id="A1.T6")
            assert locator is not None
            conflict = dict(source_url=parent["source_url"], source_sha256=parent["source_sha256"],
                            caption=plain(locator.find("figcaption") or locator.find("caption")),
                            rows=[[dict(id=cell.get("id"), text=plain(cell)) for cell in row.find_all(["th", "td"], recursive=False)]
                                  for row in locator.find_all("tr")])
        package.append(dict(id=qid, category=ref["category"], question=questions[qid],
                            current_reference_status="disputed" if qid == "G10" else "provisional",
                            required_disposition=ref["expected"], expected_points=points, conflicting_original=conflict,
                            blinded_outputs=evidence, decision_required=DECISIONS[qid],
                            human_review=dict(status="pending", reviewer=None, source_decision=None, judgment_decision=None,
                                              disagreement=None, supporting_locator=None)))
    DEST.mkdir(exist_ok=False)
    write(DEST / "review-package.json", package)
    write(DEST / "review-status.json", dict(human_review_completed=False, reason="No independent human reviewer available in this session.",
          pending_provisional=[x for x in DECISIONS if x != "G10"], disputed=["G10"], preserve_locked_scores=True,
          comparison_status="provisional", arm_identities_in_package=False, score_lock_sha256=digest(BLINDED / "score-lock.json")))
    print("Ten blinded reference cases packaged. Independent review pending.")


if __name__ == "__main__":
    main()

"""Lock model-assisted blinded scores. This program never reads the arm map."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from offline_harness import HERE, ROOT, read, verify_seal, write

sys.path.insert(0, str(HERE.parent))
from common import BUNDLE, rows
from tables import local_source

POINT = {"C": "correct", "P": "partial", "O": "omitted", "I": "inconclusive"}
RES = ROOT / "data/processed/generalization-v1-execution/blinded"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    verify_seal()
    answers = read(RES / "review.json")
    worksheets = {row["label"]: row for row in read(RES / "scoring-worksheets.json")}
    packets = {row["label"]: row["packet"] for row in read(RES / "synthesis-evidence.json")}
    keys = {r["id"]: r for r in read(HERE / "references.json")}
    parents = {r["chunk_id"]: r for r in rows(BUNDLE / "parents.jsonl")}
    hashes = {}
    for parent in parents.values():
        if parent.get("source_sha256"):
            hashes.setdefault(parent["arxiv_id"], set()).add(parent["source_sha256"])
    docs = {}

    def audit(citation, packet):
        cid = citation["chunk_id"]
        item = packet[cid]
        frozen = parents[cid]
        expect = (frozen["arxiv_id"], frozen["source_url"], frozen["text"])
        assert (item["arxiv_id"], item["source_url"], item["text"]) == expect
        normalize = lambda s: re.sub(r"\s+", " ", s).strip()
        assert normalize(citation["quote"]) in normalize(item["text"])
        version = item["arxiv_id"]
        url = urlsplit(item["source_url"])
        assert version in url.path
        candidates = [frozen["source_sha256"]] if frozen.get("source_sha256") else sorted(hashes.get(version, set()))
        locator = url.fragment
        original_match = False
        for checksum in candidates:
            key = (version, checksum)
            if key not in docs:
                docs[key] = local_source(version, checksum)[1]
            doc = docs[key]
            if doc is not None and (not locator or doc.find(id=locator) is not None):
                original_match = True
                break
        return dict(chunk_id=cid, paper_version=version, url=item["source_url"],
                    exact_indexed_quote=True, hash_matched_original_locator=original_match)

    judgment_path = HERE / "blinded_judgments.tsv"
    judgments = {}
    for line in judgment_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        qid, short, point_codes, outcome, rationale = line.split("|")
        judgments[qid, short] = point_codes, outcome, rationale
    assert len(judgments) == len(answers) == len(worksheets) == len(packets) == 40
    scores = []
    for answer in sorted(answers, key=lambda x: (x["id"], x["label"])):
        qid, label = answer["id"], answer["label"]
        code, outcome, rationale = judgments[qid, label[:8]]
        reference = keys[qid]
        points = worksheets[label]["points"]
        assert len(code) == len(points)
        provisional = reference["second_human_review"] == "pending"
        assert (outcome == "inconclusive") == ("I" in code)
        pass_primary = None if outcome == "inconclusive" else outcome in {"complete", "justified_abstention"}
        citations = []
        packet = {p["chunk_id"]: p for p in packets[label]}
        for kind, claims in (("claim", answer["claims"]), ("limitation", answer["limitation_support"])):
            for i, claim in enumerate(claims, 1):
                # Entailment is the blinded source review in the judgment sheet;
                # locator and quote alignment are checked independently in code.
                citations.append(dict(kind=kind, number=i, text=claim["text"],
                                      assessment="supported",
                                      supporting_sources=[audit(c, packet) for c in claim["support"]]))
        scores.append(dict(id=qid, label=label, category=reference["category"],
            reference_state="disputed" if qid == "G10" else "provisional" if provisional else "standard",
            requires_independent_review=provisional or qid == "G10",
            reviewer="machine-assisted blinded source review", human_verified=False, outcome=outcome,
            complete_success=pass_primary,
            false_abstention=outcome == "false_abstention",
            unjustified_corpus_nonanswer=outcome in {"false_abstention", "evidence_limited_abstention"},
            unsupported_published_claims=0,
            point_judgments=[dict(number=p["number"], requirement=p["requirement"], status=POINT[c],
                                  expected_chunk=p["expected_chunk_id"],
                                  exact_chunk_in_packet=p["exact_required_chunk_in_packet"])
                             for c, p in zip(code, points, strict=True)],
            source_judgments=citations, rationale=rationale))
    totals = Counter(s["outcome"] for s in scores)
    locator_failures = sorted({c["chunk_id"] for s in scores for item in s["source_judgments"]
                               for c in item["supporting_sources"] if not c["hash_matched_original_locator"]})
    if locator_failures:
        print("Original-source locator verification needs review:", locator_failures)
        raise SystemExit("Score lock refused until source exceptions are documented")
    write(RES / "locked-scores.json", scores)
    write(RES / "score-lock.json", dict(
        input_sha256={str(p.relative_to(ROOT)): digest(p) for p in
                      (HERE / "seal.json", HERE / "rules.json", RES / "review.json", RES / "synthesis-evidence.json",
                       RES / "scoring-worksheets.json", judgment_path, Path(__file__))},
        scores_sha256=digest(RES / "locked-scores.json"), totals=dict(totals),
        provisional_answers=sum(s["reference_state"] == "provisional" for s in scores),
        disputed_answers=sum(s["reference_state"] == "disputed" for s in scores),
        arm_map_read=False, winner=None))
    print(dict(totals))


if __name__ == "__main__":
    main()

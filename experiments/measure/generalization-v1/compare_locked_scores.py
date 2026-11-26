"""Calculate the approved provisional comparison after documenting independent review status."""
from collections import Counter
from itertools import product
from math import ceil
from statistics import median

from offline_harness import HERE, ROOT, read, verify_seal, write
from package_reference_review import BASE, BLINDED, DEST
from common import digest

ARMS = ("A", "B")


def main():
    status = read(DEST / "review-status.json")
    assert not status["human_review_completed"] and status["comparison_status"] == "provisional"
    assert digest(BLINDED / "score-lock.json") == status["score_lock_sha256"]
    verify_seal()
    lock = read(BLINDED / "score-lock.json")
    assert digest(BLINDED / "locked-scores.json") == lock["scores_sha256"]
    assert all(digest(ROOT / name) == v for name, v in lock["input_sha256"].items())
    rules = read(HERE / "rules.json")
    scores = read(BLINDED / "locked-scores.json")
    mapping = read(BASE / "restricted/unblind-after-review.json")
    assert set(mapping) == {s["label"] for s in scores}
    pairs = {}
    for score in scores:
        qid, arm = mapping[score["label"]]
        assert qid == score["id"] and arm in ARMS
        record = read(BASE / "restricted" / f"{qid}-{arm}" / "result.json")
        assert record["id"] == qid and record["arm"] == arm
        pairs.setdefault(qid, {})[arm] = dict(score=score, operation=record)
    assert len(pairs) == 20 and all(set(p) == set(ARMS) for p in pairs.values())
    totals, categories, paired, arm_stats = {}, {}, Counter(), {}
    for arm in ARMS:
        arm_rows = [p[arm] for p in pairs.values()]
        outcomes = Counter(row["score"]["outcome"] for row in arm_rows)
        exact = sum(point["exact_chunk_in_packet"] for row in arm_rows for point in row["score"]["point_judgments"])
        unsupported = sum(row["score"]["unsupported_published_claims"] for row in arm_rows)
        usages, failures = Counter(), 0
        for row in arm_rows:
            for receipt in row["operation"]["receipts"]:
                failures += receipt["status"] != "ok"
                for usage in receipt.get("usage", []):
                    usages.update(usage)
        times = sorted(row["operation"]["seconds"] for row in arm_rows)
        totals[arm] = sum(row["score"]["complete_success"] is True for row in arm_rows)
        arm_stats[arm] = dict(primary_successes=totals[arm], outcomes=dict(outcomes), exact_point_chunks=exact,
                             unsupported_claims=unsupported, unsupported_answer_cases=sum(
                                 row["score"]["unsupported_published_claims"] > 0 for row in arm_rows),
                             invocations=sum(len(row["operation"]["receipts"]) for row in arm_rows),
                             usage=dict(usages), provider_failures=failures,
                             median_seconds=median(times), p90_seconds=times[ceil(0.90 * len(times)) - 1])
    pair_rows = []
    for qid, p in sorted(pairs.items()):
        lhs, rhs = (p[arm]["score"] for arm in ARMS)
        category = lhs["category"]
        values = (lhs["complete_success"], rhs["complete_success"])
        result = ("inconclusive" if None in values else "tie" if values[0] == values[1]
                  else "B win" if values[1] else "A win")
        paired[result] += 1
        group = categories.setdefault(category, {"questions": 0, "A": 0, "B": 0, "pairs": Counter()})
        group["questions"] += 1
        for arm, value in zip(ARMS, values, strict=True):
            group[arm] += value is True
        group["pairs"][result] += 1
        pair_rows.append(dict(id=qid, category=category, state=lhs["reference_state"], outcome=result,
                              **{arm: dict(outcome=p[arm]["score"]["outcome"],
                                           complete=p[arm]["score"]["complete_success"],
                                           seconds=p[arm]["operation"]["seconds"],
                                           invocations=len(p[arm]["operation"]["receipts"])) for arm in ARMS}))
    net = totals["B"] - totals["A"]
    categories_up = sum(g["B"] > g["A"] for g in categories.values())
    latency = median([p["B"]["operation"]["seconds"] - p["A"]["operation"]["seconds"] for p in pairs.values()])
    extra_calls = arm_stats["B"]["invocations"] - arm_stats["A"]["invocations"]
    added_unsupported = arm_stats["B"]["unsupported_answer_cases"] - arm_stats["A"]["unsupported_answer_cases"]
    gate_results = {
        "net_success": net >= rules["minimum_net_complete_successes"],
        "unsupported_case_delta": added_unsupported <= rules["maximum_net_unsupported_answer_cases"],
        "categories_up": categories_up >= rules["minimum_categories_with_positive_net_successes"],
        "paired_median_delta": latency <= rules["maximum_incremental_median_paired_seconds"],
        "B_p90": arm_stats["B"]["p90_seconds"] <= rules["maximum_improved_p90_seconds"],
        "extra_calls_per_net_success": net > 0 and extra_calls / net <= rules["maximum_extra_actual_invocations_per_net_complete_success"],
    }

    def sensitivity(mode):
        """Vary review judgments only. Nonanswers and missing points stay non-successes in downgrade-only bounds."""
        per_category = {}
        for row in pair_rows:
            original = (row["A"]["complete"], row["B"]["complete"])
            if row["state"] == "disputed":
                choices = [(0, 0), (1, 0), (0, 1), (1, 1)]
            elif row["state"] == "provisional" and mode == "downgrade_only":
                choices = list(product(*[(0, 1) if x else (0,) for x in original]))
            else:
                assert None not in original
                choices = [original]
            vals = {int(b) - int(a) for a, b in choices}
            bases = per_category.get(row["category"], {0})
            per_category[row["category"]] = {a + b for a in bases for b in vals}
        all_outcomes = [(sum(x), sum(v > 0 for v in x)) for x in product(*per_category.values())]
        eligible = [(n, c) for n, c in all_outcomes if n >= rules["minimum_net_complete_successes"]
                    and c >= rules["minimum_categories_with_positive_net_successes"]
                    and extra_calls / n <= rules["maximum_extra_actual_invocations_per_net_complete_success"]]
        return dict(net_range=[min(n for n, _ in all_outcomes), max(n for n, _ in all_outcomes)],
                    category_net_ranges={k: [min(v), max(v)] for k, v in per_category.items()},
                    can_cross_success_category_and_cost_gates=bool(eligible),
                    assumption="No new unsupported-answer cases; measured latency and invocation counts fixed.")

    # A concrete conservative tipping scenario: downgrade A's four provisional table successes
    # and its provisional G14 success. Leave G10 inconclusive and every other verdict unchanged.
    tipping = {"A_downgrades": ["G01", "G04", "G05", "G11", "G14"], "net": net + 5,
               "positive_categories": ["multi", "conflict"], "extra_calls_per_net": extra_calls / (net + 5)}
    out = dict(status="provisional", categories=categories, pair_counts=dict(paired), pairs=pair_rows, arms=arm_stats,
               net_B_minus_A=net, categories_up_for_B=categories_up, median_paired_delta_seconds=latency,
               extra_B_invocations=extra_calls, additional_B_unsupported_answers=added_unsupported,
               gate_results=gate_results, threshold_evidence="current scores do not qualify for default B",
               sensitivity={"G10_only": sensitivity("G10_only"), "pending_downgrade_and_G10": sensitivity("downgrade_only"),
                            "illustrative_tipping_scenario_not_a_prediction": tipping})
    write(BASE / "PROVISIONAL-COMPARISON.json", out)
    print(out["categories"], dict(paired), gate_results, out["sensitivity"])


if __name__ == "__main__":
    main()

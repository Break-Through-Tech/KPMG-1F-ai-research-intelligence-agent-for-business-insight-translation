# Business Insight Translation technical handoff

**Experimental. Keep business translation disabled in the accepted Standard S2 research release.** Standard S2 is pinned to `40f185c98d55ab406e1b79aedbabcdb1e889da5f`. Its preview uses `S2_RETRIEVAL=s2`, rejects business and regulatory request options, and has no business translation route. Preserve the experiment on `feat/business-translation-v1`. Final validation is closed.

The experiment implemented optional translation of saved research into the existing cited `BusinessInsight` contract. It accepts fingerprinted, reviewed findings and their cited excerpts, with quote boundaries where available, plus explicit industry, workflow and decision context. It keeps the original research, saves a new pending version, records prompt and screening provenance, and isolates business failure. Empty accepted evidence skips generation. The local saved-answer UI supports one explicit translation request and renders citations, actions, assumptions and limitations. Research-only requests keep their normal generation path. Regulatory assessment remains separate.

| Assessment | Arm or set | Available | Usefulness /5 | Fidelity /5 | Limitations /5 |
|---|---|---:|---:|---:|---:|
| Initial blind review | Baseline | 11/11 | 3.15 | 3.95 | 3.91 |
| Initial blind review | v1.1 | 6/11 | 2.98 | 3.91 | 3.41 |
| Final blind review, known cases | Saved baseline | 11/11 | 3.06 | 3.50 | 3.73 |
| Final blind review, known cases | Saved v1.1 | 6/11 | 3.20 | 3.68 | 3.50 |
| Final blind review, known cases | v1.2 | 3/11 | 2.44 | 3.86 | 3.18 |
| Final blind review, fresh cases | v1.2 | 1/5 | 2.67 | 3.90 | 3.10 |

The final review rescored the saved baseline and v1.1 outputs alongside v1.2. Both rounds used blinded AI-assisted engineering assessments. Human stakeholder acceptance is unverified. v1.2 recovered U2, U5 and U6 and abstained on all six cases v1.1 had answered. It gained 0.56 usefulness points over baseline on just three common available pairs, with eight omitted. Fresh cases had no comparator.

**Screening and generation both contributed.** The rules check numerical grounding, lexical overlap and condition wording. In the final run, all 16 raw responses declared `ok`, then screening withheld every implication in 12 cases. Reviewers judged those 12 published abstentions avoidable. Eight involved numerical checks and five involved condition syntax, with overlap. A proposed sample of 20 audit tasks and a compound question about estimator access could block an entire recommendation. Some rejections had real grounds. The invoice draft turned “63.3% of diagnosed failures” into a share of all tool-use failures. Other errors survived screening. The release-review response assumed a medical-report workflow in a claims-summary case. A flag identifies a rule match. An accepted item still needs semantic review.

Actual generated outputs show the useful capability:

- **v1.1, R3, model routing.** “Define a ‘value-of-information’ metric that calculates the expected utility of a more accurate estimate versus the latency and compute cost of invoking it.” The proposed comparison also held assignment quality constant.
- **v1.2, U2, maintenance handoffs.** “Confirm whether existing data privacy policies permit the collection of screen traces for process documentation.” The proposed redaction comparison makes induction quality measurable, with approved or controlled inputs needed for the raw comparison.
- **v1.2, F5, cold-chain alerts.** “Measure the false positive rate and detection latency for both approaches” using data spanning a sensor change. A useful test would also record missed excursions and establish the current detector type.

**Release decision.** v1.2 missed the 10/11 known and 5/5 fresh availability gates and the required 4/5 usefulness, fidelity and limitations means for both sets. The empty-evidence control correctly made zero calls, and the final reviewers found zero critical unsupported claims in published v1.2 outputs. The observed availability and weak decision guidance block release.

Implementation pins are `82702dc5436c8f5b41bdcd8df3bfa0422403ce22` for v1.1 and `870ba4991a2ac9f5b58d6627e2da3141a3e6af2b` for v1.2. Evaluation assets are pinned at `90ce47ca0033221b44b2de4ef728bbde1efbe47e` and `1eeb869a6714fa018fc69534605dbe474710c955`. The main checkout's ignored `data/processed/business-translation-archive/` holds the 220 evaluation artifacts, 11 verified source PDFs and a per-file checksum manifest. It includes both original reports, responses, score sheets and adjudication, with the blind mappings kept in the operator archive. Manifest SHA-256 is `2ee09bdf54aeb8900340d13b96f0a5ddf33858be864815295bd226f8b8f83e95`.

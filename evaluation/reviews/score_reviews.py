"""Validate declared human reviews; never generate scores or infer approval."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from evaluation.run_benchmarks import artifact_id

SUMMARY_KEYS = {'accuracy','clarity','completeness'}
BUSINESS_KEYS = {'actionability','kpmg_relevance','citation_quality'}
COVERAGE = {'answerable','partially_covered','unanswerable','not_checked'}


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _rubric(scores, keys, available):
    if scores is None:
        return None
    if not available or not isinstance(scores,dict) or set(scores) != keys or not all(
            _integer(v,1,5) for v in scores.values()):
        raise ValueError('Rubric scores require an available output and all dimensions rated 1–5')
    return sum(scores.values())/len(scores)


def validate_review(run, row, review):
    if review.get('run_id') != run['run_id']:
        raise ValueError('Review is stale or belongs to a different frozen run')
    if not isinstance(review.get('reviewer'),str) or not review['reviewer'].strip():
        raise ValueError('An actual declared reviewer name is required')
    if review.get('reviewer_kind') not in {'human','fixture'} or review.get('coverage') not in COVERAGE:
        raise ValueError('Reviewer kind and coverage must be explicit')
    if review.get('abstention') not in {'correct','incorrect','not_applicable','not_checked'}:
        raise ValueError('Abstention assessment must be explicit')
    if not isinstance(review.get('notes'),str) or not review['notes'].strip():
        raise ValueError('Review notes are required')
    result = row.get('result') or {}
    evidence = result.get('evidence') or []
    first_five = {p['chunk_id'] for p in evidence[:5]}
    ratings = review.get('passage_ratings')
    if not isinstance(ratings,list) or any(not isinstance(r,dict) or
            r.get('chunk_id') not in first_five or not _integer(r.get('rating'),0,2) for r in ratings):
        raise ValueError('Passage ratings must reference this query’s first five chunks and use 0–2')
    if len({r['chunk_id'] for r in ratings}) != len(ratings):
        raise ValueError('Duplicate passage ratings')
    summary = result.get('summary') or {}
    business = result.get('business_insight') or {}
    statements = {(stage, index): item for stage, output, field in
                  [('summary', summary, 'claims'), ('business_insight', business, 'implications')]
                  for index, item in enumerate(output.get(field, []))}
    checks = review.get('claim_checks', [])
    if not isinstance(checks, list):
        raise ValueError('Claim checks must be a list')
    checked = set()
    for check in checks:
        if not isinstance(check, dict) or type(check.get('item_index')) is not int:
            raise ValueError('Claim checks require a stage and integer item index')
        stage = check.get('stage')
        if not isinstance(stage, str):
            raise ValueError('Claim check stage must be text')
        locator = (stage, check['item_index'])
        if locator not in statements or locator in checked:
            raise ValueError('Claim locator must identify one unique statement in this query')
        citations = check.get('chunk_ids')
        if (not isinstance(citations, list) or not all(isinstance(c, str) for c in citations)
                or set(citations) != set(statements[locator]['chunk_ids'])
                or len(citations) != len(set(citations)) or type(check.get('supported')) is not bool
                or not isinstance(check.get('notes'), str) or not check['notes'].strip()):
            raise ValueError('Claim checks require exact citations, boolean support and source notes')
        checked.add(locator)
    complete = row['status']=='ok' and {r['chunk_id'] for r in ratings}==first_five and review['coverage']!='not_checked'
    return {'precision_at_5':sum(r['rating']>0 for r in ratings)/5 if complete else None,
            'summary_mean':_rubric(review.get('summary_scores'),SUMMARY_KEYS,summary.get('status')=='ok'),
            'business_mean':_rubric(review.get('business_scores'),BUSINESS_KEYS,business.get('status')=='ok'),
            'claims_complete':checked == set(statements),
            'summary_available':summary.get('status') == 'ok',
            'business_available':business.get('status') == 'ok',
            'coverage':review['coverage'], 'abstention':review['abstention'],
            'complete':complete}


def aggregate(run, reviews):
    if run.get('run_id') != artifact_id(run):
        raise ValueError('Run content changed; use the original frozen export')
    queries={r['case']['query_id']:r for r in run['cases']}
    groups={q:[] for q in queries}
    seen=set(); fixture_count=0
    for review in reviews:
        query_id=review.get('query_id')
        if query_id not in queries:
            raise ValueError('Review references an unknown query')
        scores=validate_review(run,queries[query_id],review)
        identity=(query_id,review['reviewer'])
        if identity in seen:
            raise ValueError('Duplicate query/reviewer record; preserve one immutable independent review')
        seen.add(identity)
        if review['reviewer_kind']=='fixture':
            fixture_count+=1
            continue
        groups[query_id].append((review,scores))
    metrics=[]; disagreements=[]; double_types=set()
    for query_id,group in groups.items():
        if not group:continue
        adjudicators=[pair for pair in group if pair[0].get('adjudicates')]
        independent=[pair for pair in group if not pair[0].get('adjudicates')]
        if len(adjudicators)>1:raise ValueError('Multiple adjudications require resolution outside the aggregate')
        completed_independent = [pair for pair in independent if pair[1]['complete']
                                 and pair[1]['claims_complete']
                                 and pair[1]['abstention'] != 'not_checked'
                                 and (not pair[1]['summary_available'] or pair[1]['summary_mean'] is not None)
                                 and (not pair[1]['business_available'] or pair[1]['business_mean'] is not None)]
        if len(completed_independent) > 1:
            double_types.add(queries[query_id]['case'].get('type'))
        def signature(pair):
            r=pair[0]
            return json.dumps({k:r.get(k) for k in ('coverage','summary_scores','business_scores','abstention')},sort_keys=True)+json.dumps(
                sorted((x['chunk_id'],x['rating']) for x in r['passage_ratings']))+json.dumps(
                sorted((x['stage'],x['item_index'],x['supported']) for x in r.get('claim_checks',[])))
        if adjudicators:
            chosen=adjudicators[0]
            named=chosen[0]['adjudicates']
            if not isinstance(named,list) or not independent or set(named)!={p[0]['reviewer'] for p in independent}:
                raise ValueError('Adjudication must name every independent reviewer of this query')
        elif len({signature(pair) for pair in independent})>1:
            disagreements.append(query_id)
            continue
        else:
            chosen=independent[0]
        metrics.append({'query_id':query_id,'reviewer':chosen[0]['reviewer'],**chosen[1]})
    def mean(key):
        values=[m[key] for m in metrics if m[key] is not None]
        return sum(values)/len(values) if values else None
    covered = [m['precision_at_5'] for m in metrics if
               m['coverage'] in {'answerable', 'partially_covered'} and m['precision_at_5'] is not None]
    total=len(queries)
    complete=sum(m['complete'] for m in metrics)
    failed=sum(r['status']=='error' for r in run['cases'])
    retrieval=mean('precision_at_5');summary=mean('summary_mean');business=mean('business_mean')
    types={r['case'].get('type') for r in run['cases']}
    return {'run_id':run['run_id'],'total_queries':total,'complete_queries':complete,
            'failed_queries':failed,'unresolved_disagreements':disagreements,
            'fixture_review_count':fixture_count,'selected_scores':metrics,'reviews':deepcopy(reviews),
            'precision_at_5':retrieval,'retrieval_target_met':complete==total and failed==0 and retrieval is not None and retrieval>=0.7,
            'covered_precision_at_5':sum(covered)/len(covered) if covered else None,
            'covered_scored_queries':len(covered),
            'summary_available':sum((r.get('result') or {}).get('summary', {}).get('status') == 'ok' for r in run['cases']),
            'business_available':sum((r.get('result') or {}).get('business_insight', {}).get('status') == 'ok' for r in run['cases']),
            'abstention_assessments':{value:sum(m['abstention'] == value for m in metrics)
                                    for value in ('correct','incorrect','not_applicable','not_checked')},
            'claims_complete_queries':sum(m['claims_complete'] for m in metrics),
            'summary_mean':summary,'summary_scored':sum(m['summary_mean'] is not None for m in metrics),
            'business_mean':business,'business_scored':sum(m['business_mean'] is not None for m in metrics),
            'double_reviewed_types':sorted(t for t in double_types if t is not None),
            'end_to_end_targets_met':bool(run.get('provenance',{}).get('execution')=='persistent_corpus' and complete==total and total and not failed and not disagreements and
                None not in types and types<=double_types and retrieval is not None and retrieval>=0.7 and
                all(m['claims_complete'] and m['abstention'] != 'not_checked' and m['summary_mean'] is not None and m['business_mean'] is not None for m in metrics) and
                summary>=4 and business>=4), 'approved':False,
            'limitations':['Reviewer kind is a declaration, not authenticated identity or stakeholder approval.',
                'Support verdicts are reviewer declarations; inspect original source and preserve claim-level notes.']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--reviews',type=Path,required=True,help='JSON list of actual review records; empty list is valid')
    parser.add_argument('--output',type=Path,required=True,help='New report file; no overwrite')
    args=parser.parse_args(argv)
    report=aggregate(json.loads(args.run.read_text()),json.loads(args.reviews.read_text()))
    with args.output.open('x') as file:
        file.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'queries':report['total_queries'],'reviewed':report['complete_queries'],
                      'end_to_end_targets_met':report['end_to_end_targets_met']}))
    return 0


if __name__=='__main__': raise SystemExit(main())

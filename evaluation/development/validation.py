"""Validate development specifications and aggregate explicitly supplied point credits."""
import json
from pathlib import Path


def load_questions(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('split')!='development' or payload.get('answer_keys_included') is not False:
        raise ValueError('Only development question specifications without answer keys are accepted.')
    cases=payload.get('cases')
    if not isinstance(cases,list) or not cases:raise ValueError('Nonempty cases list required.')
    seen=set()
    allowed={'id','question','category','split','required_points_count'}
    for case in cases:
        if not isinstance(case,dict) or set(case)!=allowed or case['split']!='development':
            raise ValueError('Unexpected fields or non-development case.')
        if not isinstance(case['id'],str) or not case['id'] or case['id'] in seen:
            raise ValueError('Case IDs must be unique nonempty strings.')
        if not isinstance(case['question'],str) or not case['question'].strip():raise ValueError('Question required.')
        count=case['required_points_count']
        if type(count) is not int or count<0:raise ValueError('Point count must be a nonnegative integer.')
        seen.add(case['id'])
    return cases


def aggregate_credits(cases,reviews):
    by_id={case['id']:case for case in cases};seen=set();earned=total=0;correct=0
    for review in reviews:
        ident=review.get('id')
        if ident not in by_id or ident in seen:raise ValueError('Unknown or duplicate reviewed ID.')
        seen.add(ident)
        if review.get('human_confirmed') is not False or review.get('confirmation_status')!='pending':
            raise ValueError('This provisional utility cannot assign human confirmation.')
        if not isinstance(review.get('notes'),str) or not review['notes'].strip():raise ValueError('Review notes required.')
        credits=review.get('point_credits');maximum=by_id[ident]['required_points_count']
        if not isinstance(credits,list) or len(credits)!=maximum or any(type(c) not in (int,float) or c not in (0,.5,1) for c in credits):
            raise ValueError('Explicit 0/0.5/1 credits must match the original point count.')
        abstention=review.get('abstention')
        if maximum:
            if abstention!='not_applicable':raise ValueError('Answerable case requires not_applicable abstention label.')
            earned+=sum(credits);total+=maximum
        else:
            if abstention not in ('correct','incorrect','not_checked'):raise ValueError('Separate abstention decision required.')
            correct+=abstention=='correct'
    return {'reviewed_questions':len(seen),'expected_questions':len(cases),'complete':seen==set(by_id),
        'points_earned':earned,'points_possible_in_reviewed_cases':total,
        'coverage':earned/total if total else None,'correct_abstentions':correct,
        'human_confirmed':False,'confirmation_status':'pending'}


def citation_membership(result):
    """Check locator/quote membership only; never claim semantic correctness."""
    import re
    norm=lambda s:re.sub(r'\s+',' ',s).strip()
    passages={p['chunk_id']:norm(p['text']) for p in result.get('evidence',[])}
    checks=[]
    for claim in result.get('summary',{}).get('claims',[]):
        for support in claim.get('support',[]):
            ident=support['chunk_id'];quote=norm(support['quote'])
            checks.append({'chunk_id':ident,'resolved':ident in passages,
                           'quote_present':bool(quote) and quote in passages.get(ident,'')})
    return checks

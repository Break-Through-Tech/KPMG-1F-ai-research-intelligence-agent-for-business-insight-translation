"""Validate independent blind scores and summarize without fabricating missing ratings."""
import argparse,csv,json,statistics
from pathlib import Path
from run import read,dump,preflight
DIMS=['fidelity','business_relevance','action_specificity','proportionality','limitations']
FLAGS=['generic_advice','workflow_parroting','semantic_repetition','pilot_overreliance']
def score(run_dir,sheets,output):
 preflight();key=read(run_dir/'private/blind-key.json');records={}
 for sheet in sheets:
  with sheet.open(encoding='utf-8-sig',newline='') as f:
   for row in csv.DictReader(f):
    reviewer=row['reviewer_id'].strip();q=row['blind_case'];label=row['output_label']
    if not reviewer or reviewer.startswith('REVIEWER_'):raise ValueError('Actual independent reviewer IDs are required.')
    if q not in key or label not in {'A','B'}:raise ValueError('Unknown blind item.')
    identity=(reviewer,q,label)
    if identity in records:raise ValueError('Duplicate reviewer/item; preserve adjudications separately.')
    available=read(run_dir/('blind/'+q+'-'+label+'.json'))
    no_evidence=key[q]['case_id']=='U7';failed=available['status']=='execution_failed'
    for d in DIMS:
     if no_evidence or failed:
      if row[d].upper()!='NA':raise ValueError('Skipped/failed items need NA, not invented scores.')
      row[d]=None
     else:
      row[d]=int(row[d]);assert 1<=row[d]<=5
    for d in FLAGS:
     row[d]=int(row[d]);assert 0<=row[d]<=2
    assert row['critical_unsupported_claim'] in {'yes','no'}
    assert row['appropriate_abstention'] in {'yes','no','not_applicable'}
    if (row['critical_unsupported_claim']=='yes' or any(row[d]==2 for d in FLAGS)) and not row['evidence_citation'].strip():raise ValueError('Material concerns require evidence/output spans.')
    row['status']=available['status'];row['arm']=key[q]['labels'][label];row['split']=key[q]['split'];records[identity]=row
 reviewers=sorted({k[0] for k in records});assert len(reviewers)==2,'Two reviewers required.'
 for reviewer in reviewers:
  assert {(q,l) for r,q,l in records if r==reviewer}=={(q,l) for q in key for l in ('A','B')},'Incomplete review coverage.'
 disagreements=[]
 for q in key:
  for label in ('A','B'):
   a,b=[records[(r,q,label)] for r in reviewers]
   if any(a[d] is not None and b[d] is not None and abs(a[d]-b[d])>1 for d in DIMS) or any(a[d]!=b[d] for d in ['critical_unsupported_claim','appropriate_abstention',*FLAGS]):disagreements.append(q+'-'+label)
 groups={}
 for split in ('reference_aligned','generation_heldout'):
  for arm in ('baseline','candidate'):
   rows=[r for r in records.values() if r['split']==split and r['arm']==arm]
   mean=lambda d:statistics.mean(r[d] for r in rows if r[d] is not None) if any(r[d] is not None for r in rows) else None
   groups[split+'/'+arm]={'review_records':len(rows),'dimension_means':{d:mean(d) for d in DIMS},'material_defect_review_counts':{d:sum(r[d]==2 for r in rows) for d in FLAGS},'critical_review_count':sum(r['critical_unsupported_claim']=='yes' for r in rows),'failed_items':sorted({r['blind_case'] for r in rows if r['status']=='execution_failed'})}
 if output.exists():raise ValueError('Refuse to overwrite a review report.')
 dump(output,{'groups':groups,'unresolved_items':disagreements,'acceptance':'not_adjudicated; use frozen rubric and retained original records','approved':False,'generalization_claim':False})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True,type=Path);p.add_argument('--reviews',nargs='+',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();score(a.run_dir,a.reviews,a.output)

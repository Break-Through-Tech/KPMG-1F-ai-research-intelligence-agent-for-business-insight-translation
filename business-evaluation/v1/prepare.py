"""Build source-checked evaluation inputs only. Never imports a model provider."""
import csv, hashlib, json, re, sys
from pathlib import Path
import pymupdf
from pypdf import PdfReader
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO))
from src.research_pipeline import run_research
from src.business_handoff import accepted_research
DATA=Path('C:/Users/ngkho/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/data')
def sha(data):return hashlib.sha256(data).hexdigest()
def norm(t):return re.sub(r'\s+',' ',re.sub(r'(\w)-\s+(\w)',r'\1\2',t)).strip()
def compact(t):return re.sub(r'[^a-z0-9]','',t.lower())
def write(path,data):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
def main():
 if (ROOT/'frozen/manifest.json').exists():raise SystemExit('Already frozen; never overwrite the manifest.')
 specs=[
 ('collection','2608.20320',1,'This study proposes','Keywords:','The study coordinated survey collection, processing and travel prediction; broader application requires larger and more representative samples.'),
 ('traces','2608.20319',1,'We introduce','1 Introduction','TMI discovers interleaved tasks and reconstructs task models from controlled human and agent computer-use traces.'),
 ('trace_privacy','2608.20319',10,'TMI operates','Ethics Statement','The authors warn that traces may contain personal information and leave the effect of privacy redaction on induction quality to future work.'),
 ('routing','2608.20316',1,'Routing requires','1. Introduction','The routing study reports comparable routing quality to exhaustive estimation using fewer expensive estimates; noisy competitors can create adverse allocation effects.'),
 ('algorithm','2608.20318',1,'We present','Date:','On the frozen training-algorithm benchmark, most submissions did not change how the model learns; even the best system remained far from the task optimum.'),
 ('quality','2608.20331',1,'To address this challenge','1 Introduction','G-CARL combines atomic claim verification and context-specific checklists; the authors report improved factuality, coverage and clinician preferences for medical report interpretation.'),
 ('architecture','2605.00276',7,'Implementation Details','C. Case Study','In the TOP trip-planning evaluation, the single-agent baseline outperformed Swarm, while the centrally orchestrated system outperformed both.')]
 sources={}; receipts=[]; tiles=[]
 for name,aid,page,start,end,claim in specs:
  p=next(DATA.glob(aid+'*.pdf')) if aid!='2605.00276' else DATA/'pdfs/2605.00276v1.pdf'
  doc=pymupdf.open(p);t=norm(doc[page-1].get_text());a=t.index(start);b=t.index(end,a);quote=t[a:b].strip()
  other=norm(PdfReader(p).pages[page-1].extract_text())
  dual=compact(quote) in compact(other)
  if not dual:raise ValueError('Dual extractor mismatch '+name)
  cid=aid+'v1_pdf_p'+str(page)+'_'+name
  title=next((x for x in doc.metadata.values() if False),p.stem.split('_',1)[-1])
  row={'chunk_id':cid,'text':quote,'arxiv_id':aid+'v1','title':title,'source':'pdf','page_number':page,'pdf_url':'https://arxiv.org/pdf/'+aid+'v1','source_url':'https://arxiv.org/pdf/'+aid+'v1#page='+str(page)}
  sources[name]=(row,claim)
  receipts.append({'source_key':name,'original_pdf':str(p),'pdf_sha256':sha(p.read_bytes()),'page_number':page,'quote_sha256':sha(quote.encode()),'quote':quote,'dual_extractor_membership':dual,'semantic_check':'assistant compared paraphrase against primary source; not independent human approval','source_authenticity':'local original PDF; remote publisher identity not revalidated','locator':row['source_url']})
  pix=doc[page-1].get_pixmap(matrix=pymupdf.Matrix(.65,.65));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((430,580));tile=Image.new('RGB',(450,620),'white');tile.paste(im,(10,30));ImageDraw.Draw(tile).text((10,5),f'{name} {aid} PDF page {page}',fill='black');tiles.append(tile)
 contact=Image.new('RGB',(450*4,620*2),'#dddddd')
 for i,tile in enumerate(tiles):contact.paste(tile,((i%4)*450,(i//4)*620))
 (ROOT/'frozen').mkdir(exist_ok=True);contact.save(ROOT/'frozen/source-pages.jpg')
 write(Path('frozen/source-verification.json'),receipts)
 cases=[
 ('R1','reference_aligned','Survey workflow opportunity',['collection'],'Advisory','Survey collection and analysis handoffs','What could a team change in survey collection and analysis handoffs based on this study, and what limits the application?','Identify an auditable workflow opportunity without treating student commuters as representative clients.'),
 ('R2','reference_aligned','Process documentation and privacy',['traces','trace_privacy'],'Advisory','Documenting knowledge-worker processes','How could task induction support process documentation, and what should a team establish before capturing work traces?','Distinguish demonstrated task reconstruction from proposed privacy controls; redaction effectiveness is untested.'),
 ('R3','reference_aligned','Model routing allocation',['routing'],'Technology advisory','Selecting models for research requests','Which model-routing decision could this research inform, and what should determine whether extra estimation is worthwhile?','Quality versus estimation cost; preserve centralized/decentralized distinction and noisy-estimate caveat.'),
 ('R4','reference_aligned','Vendor improvement claims',['algorithm'],'Technology advisory','Assessing AI coding tool claims','What evidence should a team request before accepting a claim that an AI coding tool improved a training algorithm?','Differentiate algorithm changes from configuration changes and require repeatable baseline comparison.'),
 ('R5','reference_aligned','Claim and coverage quality',['quality'],'Trusted AI','Reviewing research briefs','How could separate factual-support and coverage checks improve brief review, and what transfer assumptions matter?','Translate a quality-control principle without claiming medical results prove business-brief benefit.'),
 ('U1','generation_heldout','Novel public-service routing',['routing'],'Public-sector advisory','Routing multilingual grant-eligibility enquiries','Which routing decisions are worth examining for multilingual grant enquiries when rare-language quality matters more than average cost?','Conditional transfer, distribution-specific quality evidence; do not invent service or savings outcomes.'),
 ('U2','generation_heldout','Novel manufacturing handoffs',['traces','trace_privacy'],'Operations advisory','Documenting maintenance shift handoffs','Would task induction help document maintenance shift handoffs, and what evidence should govern a decision to collect screen traces?','Action may be an evidence request or documentation review, not automatic workplace surveillance or rollout.'),
 ('U3','generation_heldout','External-validity challenge',['collection'],'Insurance advisory','Estimating branch-staff commuting patterns','What can this student-commuter study reasonably inform about branch-staff travel analysis, and which conclusions should be deferred?','Representative population and purpose must be validated; no unmeasured employee effects or causality.'),
 ('U4','generation_heldout','Conflicting architecture findings',['architecture'],'Internal audit enablement','Choosing an assistant for multi-step evidence reconciliation','What should an audit enablement team infer when a single agent beats Swarm but the orchestrated system beats both?','Contrasting results within one study, not independent papers; avoid a blanket agent-count preference.'),
 ('U5','generation_heldout','Cross-paper release governance',['quality','algorithm'],'Technology risk','Approving changes to a claims-summary assistant','Which release-review questions follow from combining claim-level coverage checks with clean rerun evaluation?','Meaningful complementary evaluation decisions; no cross-study causal or clinical-to-insurance benefit claim.'),
 ('U6','generation_heldout','Financial-pressure control',['routing'],'Finance transformation','Reviewing a model-router business case','A sponsor wants a savings and payback figure. What can these findings support now, and what decision-relevant evidence is still needed?','Do not invent ROI or merely refuse; explain useful cost/quality measurements and missing business inputs.'),
 ('U7','generation_heldout','Insufficient accepted evidence',[],'Data governance','Deleting proprietary fine-tuning data','Can the supplied accepted evidence establish that deleting fine-tuning files removes their influence from a deployed model?','Abstain: no accepted passages supplied. This is not a claim that relevant research does not exist.')]
 index=[]
 for n,(cid,split,title,keys,industry,workflow,question,note) in enumerate(cases,1):
  evidence=[sources[k][0] for k in keys]
  claims=[{'text':sources[k][1],'kind':'finding','chunk_ids':[sources[k][0]['chunk_id']],'support':[{'chunk_id':sources[k][0]['chunk_id'],'quote':sources[k][0]['text']}]} for k in keys]
  gap='The supplied research does not establish outcomes in the target workflow.' if keys else 'No accepted evidence passages were supplied for the requested deletion claim.'
  summary={'query':question,'status':'ok' if keys else 'insufficient_evidence','claims':claims,'limitations':[gap],'limitation_support':[],'answer_scope':'partial' if keys else 'unavailable','answer_lead':gap,'quality_review':{'coverage':'partial' if keys else 'none','reviewer':'assistant_primary_source_check_not_human','gap':gap}}
  packet=run_research({'query':question},retrieve=lambda q,k:evidence,summarize_fn=lambda q,p:summary,provenance={'preparation':'primary_source_verified_manual_packet_no_research_generation','scientific_evidence':'original_local_PDF_not_unit_fixture'})
  context={'industry':industry,'workflow':workflow,'decision':question}
  clean,bounded,bounds=accepted_research(packet['summary'],packet['evidence']);clean['business_context']=context
  write(Path('frozen/packets/'+cid+'.json'),{'id':cid,'result':packet,'context':context,'shared_input_sha256':sha(json.dumps([clean,bounded],sort_keys=True).encode()),'preparation':'manual source-checked accepted packet, no model output'})
  index.append({'id':cid,'split':split,'title':title,'question':question,'context':context,'source_keys':keys,'review_focus':note,'expected_calls_per_arm':1 if keys else 0,'novelty':'KPMG reference-aligned' if split=='reference_aligned' else 'new question, not used for implementation or tuning; known-source transfer; not an independent-author or unseen-paper test'})
 write(Path('frozen/cases.json'),index)
 saved=DATA/'processed/answer-quality-dev/live-final.json'
 write(Path('frozen/saved-evidence-reuse.json'),{'saved_capture':str(saved),'sha256':sha(saved.read_bytes()),'reused_for':'U4 comparative architecture evidence identified from existing accepted capture; regrounded in original PDF page 7','other_cases':'Five new reference papers available as original PDFs; source-checked packets prepared directly, no engine rerun','calls_to_research_engine':0})
 with (ROOT/'frozen/review-sheet.csv').open('w',newline='',encoding='utf-8') as f:
  columns=['reviewer_id','blind_case','output_label','fidelity','business_relevance','action_specificity','proportionality','limitations','generic_advice','workflow_parroting','semantic_repetition','pilot_overreliance','critical_unsupported_claim','appropriate_abstention','evidence_citation','notes']
  w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
  for reviewer in ('REVIEWER_1','REVIEWER_2'):
   for i in range(1,13):
    for label in ('A','B'):w.writerow({'reviewer_id':reviewer,'blind_case':f'Q{i:02}','output_label':label})
 print('Prepared 12 cases, 7 source pages, 22 scheduled calls; ready for visual/source and offline preflight review.')
if __name__=='__main__':main()

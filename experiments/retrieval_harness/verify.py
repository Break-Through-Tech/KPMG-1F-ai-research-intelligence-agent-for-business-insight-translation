"""Verify saved context receipts and export compact, auditable experiment results."""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
from transformers import AutoTokenizer
from experiments.semantic_calibration.run import MODELS,norm
from experiments.retrieval_harness.harness import ARMS


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--corpus',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--export',type=Path,required=True)
    a=ap.parse_args();corpus=json.loads(a.corpus.read_text());blocks={b['id']:b for b in corpus['blocks']}
    protocol=json.loads((a.output/'protocol.json').read_text());assert sha(a.corpus)==protocol['corpus_sha256']
    name,rev=MODELS['e5'];tokenizer=AutoTokenizer.from_pretrained(str(Path.home()/'.cache/huggingface/hub'/('models--'+name.replace('/','--'))/'snapshots'/rev),local_files_only=True)
    qs={q['id']:q for q in corpus['questions']};compact={};checks=Counter();hashes={}
    summary=json.loads((a.output/'summary.json').read_text())
    for source in ('html','tex','pdf'):
        prior=json.loads((a.cache/'e5'/source/'report.json').read_text())
        expected=[q['id'] for q in corpus['questions'] if q['paper'] in corpus['common_papers']]
        assert [q['id'] for q in prior['variants']['original']['queries']['tokens1600']]==expected
        rows=json.loads((a.output/(source+'-contexts.json')).read_text());compact[source]=[]
        assert len(rows)==len(expected)*len(ARMS)*2
        assert len({(r['id'],r['arm'],r['budget']) for r in rows})==len(rows)
        for r in rows:
            total=0
            for e in r['evidence']:
                b=blocks[e['block']];assert b['source']==source==e['source']
                assert 0<=e['start']<e['end']<=len(b['text'])
                assert e['text']==b['text'][e['start']:e['end']] and e['paper']==b['paper']
                loc=dict(b['location'])
                if source=='tex':
                    loc['line_start']+=b['text'].count('\n',0,e['start']);loc['line_end']=loc['line_start']+e['text'].count('\n')
                assert e['location']==loc
                total+=len(tokenizer.encode('passage: '+e['text'],add_special_tokens=True,truncation=False))
                checks['source_intervals']+=1
            assert total==r['tokens'] and total<=r['budget']
            q=qs[r['id']]
            found=[any(e['paper']==q['paper'] and norm(anchor) in norm(e['text']) for e in r['evidence']) for anchor in q['anchors']]
            assert found==r['found'] and all(found)==r['complete']
            checks['query_contexts']+=1
            compact[source].append({k:v for k,v in r.items() if k!='evidence'})
        for sr in [s for s in summary if s['source']==source]:
            matches=[r for r in rows if (r['arm'],r['budget'],r['split'])==(sr['arm'],sr['budget'],sr['split'])]
            assert len(matches)==sr['questions'] and sum(r['complete'] for r in matches)==sr['complete']
        for filename in ('report.json','variants.json','chunk-texts.json','chunk-vectors.npy','query-vectors.npy'):
            path=a.cache/'e5'/source/filename;hashes[str(path)]=sha(path)
        hashes[str(a.output/(source+'-contexts.json'))]=sha(a.output/(source+'-contexts.json'))
    a.export.mkdir(parents=True,exist_ok=True)
    for filename in ('protocol.json','summary.json','SUMMARY.md'):shutil.copy2(a.output/filename,a.export/filename)
    (a.export/'outcomes.json').write_text(json.dumps(compact,separators=(',',':'))+'\n')
    (a.export/'artifact-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    (a.export/'questions.json').write_text(json.dumps([dict(q,split=corpus['split'][q['paper']]) for q in corpus['questions'] if q['paper'] in corpus['common_papers']],indent=2)+'\n')
    (a.export/'verification.json').write_text(json.dumps(dict(status='passed',**checks,checks=['query-cache order','source text/offset/locator parity','exact token caps','score recomputation','aggregate parity']),indent=2)+'\n')
    (a.export/'environment.json').write_text(json.dumps({k:importlib.metadata.version(k) for k in ('numpy','torch','transformers','sentence-transformers')},indent=2)+'\n')
    print(dict(status='passed',**checks))

if __name__=='__main__':main()

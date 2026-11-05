"""Build a new local B2 bundle from versioned source parents and optional HTML."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from src.research_contracts import validate_evidence
from .html_evidence import extract_html_evidence, validate_source_bindings
from .search_chunks import make_search_views
from .search_index import SearchViewIndex

ROOT=Path(__file__).resolve().parents[2]

def prepare_parents(parents, sources=(), source_root=None):
    validate_evidence(parents)
    by_id={p['chunk_id']:p for p in parents}
    reports=[]
    for source in sources:
        path=Path(source['html_path'])
        if not path.is_absolute():path=Path(source_root or ROOT)/path
        html=path.read_text(encoding='utf-8')
        result=extract_html_evidence(html,source['arxiv_id'],source['title'],include_appendix=True)
        validate_source_bindings(result['passages'],html,source['arxiv_id'],source['title'])
        reports.append(result['coverage'])
        for passage in result['passages']:
            ident=passage['chunk_id']
            if ident in by_id and by_id[ident] != passage:
                raise ValueError('Source ID collision; original evidence was not overwritten: '+ident)
            by_id[ident]=passage
    combined=list(by_id.values());validate_evidence(combined)
    return combined,reports


def build_bundle(parents, output, encoder):
    output=Path(output).resolve()
    allowed=(ROOT/'data/processed').resolve()
    if allowed not in output.parents or output.exists():
        raise ValueError('Use a NEW output directory beneath data/processed; existing bundles are never overwritten.')
    validate_evidence(parents)
    views=make_search_views(parents,encoder.tokenizer,budget=224,overlap=32)
    if not views:raise ValueError('No searchable source views.')
    vectors=np.asarray(encoder.encode([v['text'] for v in views],show_progress_bar=False),dtype=np.float32)
    if vectors.shape != (len(views),384) or not np.isfinite(vectors).all():
        raise ValueError('Expected finite 384-dimensional local embeddings.')
    output.mkdir(parents=True,exist_ok=False)
    (output/'parents.jsonl').write_text('\n'.join(json.dumps(p,ensure_ascii=False,allow_nan=False) for p in parents),encoding='utf-8')
    (output/'views.json').write_text(json.dumps(views,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    np.save(output/'vectors.npy',vectors,allow_pickle=False)
    manifest={'kind':'bounded_search_views_v1','status':'complete','strategy':'token224_parent',
        'embedding_model':'all-MiniLM-L6-v2','distance':'squared_l2','human_acceptance':'pending',
        'parent_count':len(parents),'view_count':len(views),
        'artifact_sha256':{n:sha256((output/n).read_bytes()).hexdigest() for n in ['parents.jsonl','views.json','vectors.npy']}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    try:SearchViewIndex(output,model=encoder)
    except Exception:
        manifest['status']='invalid'
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        raise
    return manifest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parents',type=Path,required=True,help='Local JSONL using the source-evidence contract.')
    parser.add_argument('--html-sources',type=Path,help='Local JSON list: arxiv_id, title, html_path; paths relative to this manifest.')
    parser.add_argument('--encoder',type=Path,required=True,help='Existing local all-MiniLM-L6-v2 directory.')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if not args.encoder.is_dir():parser.error('Local encoder directory is missing; no download attempted.')
    parents=[json.loads(line) for line in args.parents.read_text(encoding='utf-8').splitlines() if line.strip()]
    sources=json.loads(args.html_sources.read_text(encoding='utf-8')) if args.html_sources else []
    if not isinstance(sources,list):parser.error('HTML source manifest must be a list.')
    parents,reports=prepare_parents(parents,sources,args.html_sources.parent if args.html_sources else None)
    from sentence_transformers import SentenceTransformer
    encoder=SentenceTransformer(str(args.encoder.resolve()),local_files_only=True,device='cpu')
    manifest=build_bundle(parents,args.output,encoder)
    (args.output/'extraction-audit.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(args.output),'parents':manifest['parent_count'],'views':manifest['view_count'],'experimental':True}))

if __name__=='__main__':main()

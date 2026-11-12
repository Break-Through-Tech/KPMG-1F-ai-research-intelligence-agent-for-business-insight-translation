"""Serve the existing research frontend with explicitly selected B2 retrieval."""
import argparse
from importlib import import_module
import json
from pathlib import Path
from http.server import ThreadingHTTPServer
from .b2 import open_b2


def load_generator(spec, options):
    """Load only the requested local factory. There is no automatic provider fallback."""
    module, separator, name = spec.partition(':')
    if not separator or not module or not name:
        raise ValueError('Generator factory must be module:function.')
    factory = getattr(import_module(module), name)
    return factory(**options)


def create_research(retrieval, generate, metadata, top_k=5, *, arxiv_search=None):
    from src.indexed_research import IndexedResearch, fingerprint, code_revision
    from src.research_review import assess_regulatory
    retrieve, identity, path, provenance = retrieval
    research = IndexedResearch(retrieve=retrieve, identity=identity, index_path=path,
        generate=generate, metadata=metadata, top_k=top_k, quality_check=True,
        code_revision=code_revision(), command=['experimental-b2-demo'],
        arxiv_search=arxiv_search, regulatory_assessor=assess_regulatory)
    research.provenance['retrieval'] = {**provenance,'top_k':top_k}
    research.context_id = fingerprint(research.provenance)
    return research


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--encoder',type=Path,required=True)
    parser.add_argument('--reranker',type=Path,required=True)
    parser.add_argument('--check-only',action='store_true',help='Validate local retrieval without loading a generation factory or submitting a question.')
    parser.add_argument('--generator-factory',help='Explicit existing provider factory, module:function; required except for --check-only.')
    parser.add_argument('--generator-options',type=Path,help='Local JSON object of explicit factory options; keep it untracked.')
    parser.add_argument('--arxiv-fallback', action='store_true',
                        help='Search public arXiv after an insufficient library answer.')
    parser.add_argument('--top-k',type=int,default=5,choices=range(1,21))
    parser.add_argument('--port',type=int,default=8785)
    parser.add_argument('--library',type=Path,help='Optional separate local brief database; original database is never selected by default.')
    args=parser.parse_args(argv)
    if not args.check_only and not args.generator_factory:
        parser.error('Choose --generator-factory explicitly; no provider default or fallback.')
    retrieval=open_b2(args.bundle,encoder_path=args.encoder,reranker_path=args.reranker)
    if args.check_only:
        print(json.dumps({'retrieval':retrieval[3],'index':retrieval[1](),
                          'generation_calls':0,'query_executed':False},indent=2))
        return
    options=json.loads(args.generator_options.read_text(encoding='utf-8')) if args.generator_options else {}
    if not isinstance(options,dict):parser.error('Generator options must be a JSON object.')
    generate,metadata=load_generator(args.generator_factory,options)
    discovery = None
    if args.arxiv_fallback:
        from .arxiv_fallback import ArxivDiscovery

        with (args.bundle / 'parents.jsonl').open(encoding='utf-8') as parents:
            source_parents = [json.loads(line) for line in parents]
        discovery = ArxivDiscovery(generate, indexed_ids={row['arxiv_id'] for row in source_parents})
    research = create_research(retrieval, generate, metadata, args.top_k, arxiv_search=discovery)
    from src.research_demo import DemoHandler
    from src.brief_store import BriefStore
    class ExperimentalHandler(DemoHandler):
        pass
    ExperimentalHandler.research=research
    ExperimentalHandler.library=BriefStore(args.library) if args.library else None
    ExperimentalHandler.saved_result=None
    ExperimentalHandler.presentation_generate=None
    with ThreadingHTTPServer(('127.0.0.1',args.port),ExperimentalHandler) as server:
        print(f'Experimental B2 · {retrieval[3]["method"]} · http://127.0.0.1:{server.server_port}',flush=True)
        print('No question submitted automatically. Generated results remain pending review.',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

if __name__=='__main__':main()

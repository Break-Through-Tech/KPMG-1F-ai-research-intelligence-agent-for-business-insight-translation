"""Research library CLI.

  python -m src.library --library D:/KPMG-library-data/library seed --bundle <existing B2 bundle>
  python -m src.library --library ... discover --per-topic 200
  python -m src.library --library ... ingest --target 50
  python -m src.library --library ... index --encoder <local MiniLM dir>
  python -m src.library --library ... verify --encoder ... --reranker ...
  python -m src.library --library ... run --target 1000 --encoder ...   (discover + ingest + index)
  python -m src.library --library ... dashboard --port 8790
"""
import argparse
import json
import os
from pathlib import Path


def encoder_from(path):
    from sentence_transformers import SentenceTransformer
    if not Path(path).is_dir():
        raise SystemExit('Local encoder directory is missing; no download attempted.')
    return SentenceTransformer(str(Path(path).resolve()), local_files_only=True, device='cpu')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--library', type=Path, default=os.environ.get('KPMG_LIBRARY'), required=os.environ.get('KPMG_LIBRARY') is None)
    p.add_argument('--html-cache', type=Path, help='Defaults to <library>/../html-cache')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('seed'); s.add_argument('--bundle', type=Path, required=True)
    s = sub.add_parser('discover'); s.add_argument('--per-topic', type=int, default=200); s.add_argument('--topic', action='append')
    s = sub.add_parser('ingest'); s.add_argument('--target', type=int, required=True)
    s = sub.add_parser('index'); s.add_argument('--encoder', type=Path, required=True); s.add_argument('--keep', type=int, default=2)
    s = sub.add_parser('verify'); s.add_argument('--encoder', type=Path, required=True); s.add_argument('--reranker', type=Path)
    s.add_argument('--engine-sample', type=int, default=60); s.add_argument('--output', type=Path)
    s = sub.add_parser('run'); s.add_argument('--target', type=int, required=True); s.add_argument('--encoder', type=Path, required=True)
    s.add_argument('--per-topic', type=int, default=200)
    s = sub.add_parser('status')
    s = sub.add_parser('dashboard'); s.add_argument('--port', type=int, default=8790); s.add_argument('--target', type=int, default=1000)
    a = p.parse_args(argv)
    root = a.library.resolve()
    cache = (a.html_cache or root.parent / 'html-cache').resolve()
    if a.cmd == 'dashboard':
        from .dashboard import serve
        return serve(root, port=a.port, target=a.target)
    if a.cmd == 'status':
        from .dashboard import status
        s = status(root)
        print(json.dumps({k: s[k] for k in ('indexed', 'ready', 'counts', 'current_bundle')}, indent=2))
        return
    from .store import Store
    store = Store(root)
    try:
        if a.cmd == 'seed':
            from .index import seed_from_bundle
            print(json.dumps({'seeded': seed_from_bundle(store, a.bundle)}))
        elif a.cmd in ('discover', 'run'):
            from .arxiv_client import ArxivClient
            from .discovery import discover
            print(json.dumps(discover(store, ArxivClient(), per_topic=a.per_topic, topics=getattr(a, 'topic', None)), indent=2))
        if a.cmd in ('ingest', 'run'):
            from .arxiv_client import ArxivClient
            from .ingest import ingest
            print(json.dumps(ingest(store, ArxivClient(), target=a.target, html_cache=cache)))
        if a.cmd in ('index', 'run'):
            from .index import build
            print(json.dumps(build(store, encoder_from(a.encoder), keep=getattr(a, 'keep', 2)), indent=2))
        if a.cmd == 'verify':
            from .index import current_bundle
            from .verify import verify
            bundle = current_bundle(root)
            report = verify(store, encoder_from(a.encoder), bundle, reranker_path=a.reranker,
                            encoder_path=a.encoder, engine_sample=a.engine_sample if a.reranker else 0)
            text = json.dumps(report, indent=2)
            if a.output:
                a.output.write_text(text, encoding='utf-8')
            print(text)
    finally:
        store.close()


if __name__ == '__main__':
    main()

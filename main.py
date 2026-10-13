"""CLI for persistent retrieval and draft research generation."""
import argparse
from contextlib import redirect_stdout
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys

from src.research_pipeline import PipelineError, run_research
from src.generation import create_generate


def load_adapter(spec):
    module, separator, name = spec.partition(':')
    if not separator or not module or not name:
        raise ValueError('Adapter must be specified as module:function')
    try:
        fn = getattr(importlib.import_module(module), name)
    except (ImportError, AttributeError):
        raise PipelineError(f'Adapter {spec} is unavailable. Supply an installed adapter '
                            'or use --demo for fixture-only execution.') from None
    if not callable(fn):
        raise ValueError('Adapter target must be callable')
    return fn


def persistent_retrieve(query, top_k):
    # Check before creating Chroma directories or downloading embedding weights.
    index = Path(__file__).resolve().parent / 'data/chroma_db'
    if not (index / 'chroma.sqlite3').is_file():
        raise PipelineError('Persistent index missing. Run python -m src.data_ingestion.pipeline '
                            'then python src/retrieval.py before querying.')
    from src.retrieval import search
    try:
        return search(query, top_k)
    except ValueError as exc:
        if str(exc).startswith(('Index model is unknown or different',
                                'Index contains passages without citations',
                                'PDF chunks require', 'HTML chunks require', 'Unknown chunk source:')):
            raise PipelineError('Local index has missing/incompatible model or citation metadata. '
                                'Repair source chunks if necessary, then run python src/retrieval.py '
                                'to reindex before querying.') from None
        raise


def demo_retrieve(query, top_k):
    return [{'chunk_id': 'synthetic-html-1', 'text': 'Synthetic agents need task-specific evaluation.',
             'distance': 0.25, 'arxiv_id': 'synthetic', 'title': 'Synthetic fixture, not a paper',
             'pdf_url': 'https://example.com/fixture.pdf', 'source': 'html',
             'source_url': 'https://example.com/fixture#results', 'page_number': None,
             'html_url': 'https://example.com/fixture#results', 'section': 'results'},
            {'chunk_id': 'synthetic-pdf-2', 'text': 'Synthetic evidence requires human checks.',
             'distance': 0.5, 'arxiv_id': 'synthetic', 'title': 'Synthetic fixture, not a paper',
             'pdf_url': 'https://example.com/fixture.pdf', 'source': 'pdf',
             'source_url': 'https://example.com/fixture.pdf#page=2', 'page_number': 2}][:top_k]


def demo_summary(query, passages):
    return {'status': 'ok', 'query': query, 'claims': [
        {'text': p['text'], 'chunk_ids': [p['chunk_id']]} for p in passages],
        'limitations': ['Synthetic fixture only; no real corpus or model was evaluated.']}


def demo_translate(summary, passages, *, industry):
    return {'status': 'ok', 'industry': industry, 'implications': [
        {'text': 'Consider a task-specific evaluation pilot.',
         'chunk_ids': [passages[0]['chunk_id']], 'suggested_action': 'Design a bounded pilot.',
         'assumptions': ['Synthetic example; not verified industry advice.']}],
        'risks': ['Human source verification required.'], 'limitations': ['Fixture-only translation.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Citation-bearing research drafts; never automatic approval')
    parser.add_argument('--query', required=True)
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--mode', choices=['retrieval', 'summary', 'business'], default='summary')
    parser.add_argument('--industry')
    parser.add_argument('--jurisdiction')
    parser.add_argument('--demo', action='store_true', help='Synthetic offline adapters; no keys or downloads')
    parser.add_argument('--summary-adapter', help='module:function with summarize(query, passages, *, generate)')
    parser.add_argument('--translation-adapter', help='module:function with translate(summary, passages, *, industry, generate)')
    parser.add_argument('--review-adapter', help='module:function accepting the complete result, including jurisdiction')
    args = parser.parse_args(argv)
    try:
        if args.mode == 'business' and not args.industry:
            raise ValueError('Business mode requires --industry')
        if args.demo and (args.summary_adapter or args.translation_adapter or args.review_adapter):
            raise ValueError('--demo cannot be combined with live adapters')
        if args.mode != 'business' and args.translation_adapter:
            raise ValueError('--translation-adapter requires --mode business')
        request = {'query': args.query, 'top_k': args.top_k}
        for key in ('industry', 'jurisdiction'):
            if getattr(args, key) is not None:
                request[key] = getattr(args, key)
        provenance = {'execution': 'synthetic_fixture' if args.demo else 'persistent_corpus',
                      'embedding_model': None if args.demo else 'all-MiniLM-L6-v2',
                      'corpus_sha256': None, 'input_file_sha256': None, 'generation': None}
        corpus = Path(__file__).resolve().parent / 'data/processed/chunks.parquet'
        if not args.demo and corpus.is_file():
            provenance['input_file_sha256'] = sha256(corpus.read_bytes()).hexdigest()
        retrieve = demo_retrieve if args.demo else persistent_retrieve
        translate = None
        review = None
        # Keep stdout machine-readable even if imported retrieval prints diagnostics.
        with redirect_stdout(sys.stderr):
            if args.mode == 'retrieval':
                def summary(query, passages):
                    return {'status': 'insufficient_evidence', 'query': query, 'claims': [],
                            'limitations': ['Retrieval-only run; generation not requested.']}
            elif args.demo:
                summary = demo_summary
                if args.mode == 'business':
                    translate = demo_translate
            else:
                if args.mode == 'business' and not args.translation_adapter:
                    raise PipelineError('Business adapter unavailable: supply --translation-adapter '
                                        'module:function from #80, or use --demo.')
                spec = args.summary_adapter or 'src.summarization:summarize'
                adapter = load_adapter(spec)
                business_adapter = load_adapter(args.translation_adapter) if args.translation_adapter else None
                generate, settings = create_generate()
                provenance['generation'] = settings
                if spec == 'src.summarization:summarize':
                    from src.summarization import prompt_provenance
                    provenance['generation'].update(prompt_provenance())
                else:
                    provenance['generation'].update(summary_adapter=spec,
                        prompt_version='external-adapter-unspecified')
                provenance['generation']['translation_adapter'] = args.translation_adapter
                summary = lambda q, p: adapter(q, p, generate=generate)
                if business_adapter:
                    translate = lambda s, p, *, industry: business_adapter(s, p, industry=industry, generate=generate)
            if args.review_adapter:
                review = load_adapter(args.review_adapter)
            result = run_research(request, retrieve=retrieve, summarize_fn=summary,
                                  translate_fn=translate, review_fn=review, provenance=provenance)
        print(json.dumps(result, indent=2, allow_nan=False))
        return int(bool(result.get('summary', {}).get('error')))
    except ImportError:
        print(json.dumps({'error': 'Runtime dependency unavailable. Install requirements.txt '
                                  'in your active Python environment.', 'approved': False}), file=sys.stderr)
        return 1
    except (PipelineError, ValueError) as exc:
        print(json.dumps({'error': str(exc), 'approved': False}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

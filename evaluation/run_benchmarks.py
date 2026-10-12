"""Frozen benchmark capture; no scoring, API calls, or downloads at import time."""
import argparse
from copy import deepcopy
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from src.research_pipeline import run_research

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'evaluation/benchmark_cases.json'


def artifact_id(artifact):
    content = {k: v for k, v in artifact.items() if k != 'run_id'}
    return sha256(json.dumps(content, sort_keys=True, allow_nan=False).encode()).hexdigest()


def capture(cases, *, research_fn, provenance, top_k=5, context=None):
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError('top_k must be a positive integer')
    if not isinstance(cases, list) or not cases:
        raise ValueError('Benchmark cases must be a nonempty list')
    ids = [c.get('query_id') for c in cases if isinstance(c, dict)]
    if len(ids) != len(cases) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Benchmark query IDs must be nonempty and unique')
    if any(not isinstance(c.get('query'), str) or not c['query'].strip() for c in cases):
        raise ValueError('Benchmark questions must be nonempty text')
    artifact = {'schema_version': '1.0', 'created_at': datetime.now(timezone.utc).isoformat(),
                'provenance': deepcopy(provenance), 'top_k': top_k, 'cases': []}
    for case in deepcopy(cases):
        request = {**(context or {}), 'query': case['query'], 'top_k': top_k}
        row = {'case': case, 'request': request, 'status': 'ok', 'result': None, 'error': None}
        try:
            result = deepcopy(research_fn(deepcopy(request)))
            if not isinstance(result, dict) or result.get('request') != request or not isinstance(result.get('evidence'), list):
                raise ValueError('Adapter result must match the request and contain evidence')
            row['result'] = result
            # Catch non-JSON/NaN outputs per query rather than losing the full batch.
            json.dumps(result, allow_nan=False)
        except Exception as exc:
            row.update(status='error', result=None, error={'type': type(exc).__name__,
                       'message': 'Query failed; inspect the local adapter/index/provider configuration.'})
        artifact['cases'].append(row)
    artifact['run_id'] = artifact_id(artifact)
    return artifact


def source_provenance(*, execution, generation=None):
    def git(*args):
        return subprocess.run(['git', *args], cwd=ROOT, check=True, text=True,
                              capture_output=True).stdout.strip()
    files = ['data/metadata/arxiv_csAI_25_pdf_sample.csv',
             'data/metadata/arxiv_csAI_100_metadata.csv', 'data/processed/chunks.parquet']
    return {'execution': execution, 'repo_sha': git('rev-parse', 'HEAD'),
            'dirty': bool(git('status', '--porcelain')),
            'input_hashes': {p: sha256((ROOT/p).read_bytes()).hexdigest() if (ROOT/p).is_file() else None for p in files},
            'indexed_corpus_sha256': None, 'corpus_mode': 'synthetic' if execution == 'synthetic_fixture' else 'unverified_local_index' if execution == 'persistent_corpus' else 'adapter_unspecified',
            'embedding_model': 'all-MiniLM-L6-v2' if execution == 'persistent_corpus' else None,
            'generation': generation}


def export_review_table(artifact, path):
    columns = ['run_id', 'query_id', 'query', 'query_status', 'rank', 'chunk_id', 'source_url',
               'page_number', 'distance', 'summary_status', 'summary_claims', 'business_status',
               'business_implications', 'reviewer', 'passage_rating', 'notes']
    with Path(path).open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in artifact['cases']:
            result = row['result'] or {}
            summary = result.get('summary') or {}
            business = result.get('business_insight') or {}
            for rank, passage in enumerate(result.get('evidence') or [{}], 1):
                cells = {'run_id': artifact['run_id'], 'query_id': row['case']['query_id'],
                    'query': row['case']['query'], 'query_status': row['status'],
                    'rank': rank if passage else '', **{k: passage.get(k) for k in ('chunk_id','source_url','page_number','distance')},
                    'summary_status': summary.get('status'), 'summary_claims': json.dumps(summary.get('claims', [])),
                    'business_status': business.get('status'), 'business_implications': json.dumps(business.get('implications', [])),
                    'reviewer': '', 'passage_rating': '', 'notes': ''}
                # Spreadsheet viewers must not execute formulas from source/query data.
                writer.writerow({k: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v
                                 for k,v in cells.items()})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=CASES)
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwrite a frozen run')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--mode', choices=['retrieval','summary','business'], default='retrieval')
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--industry')
    parser.add_argument('--jurisdiction')
    parser.add_argument('--research-adapter', help='module:function receiving a request and returning a complete ResearchResult')
    args = parser.parse_args(argv)
    if args.demo and args.research_adapter:
        parser.error('--demo cannot be combined with a live research adapter')
    if args.mode == 'business' and not args.industry:
        parser.error('Business mode requires --industry')
    from main import demo_retrieve, demo_summary, demo_translate, persistent_retrieve, load_adapter
    generation = None
    if args.research_adapter:
        research = load_adapter(args.research_adapter)
        generation = {'adapter': args.research_adapter, 'model': 'unspecified', 'prompt_version': 'unspecified'}
    else:
        if args.mode == 'business' and not args.demo:
            parser.error('Live business mode requires --research-adapter for the bound translation/review integration')
        retrieve = demo_retrieve if args.demo else persistent_retrieve
        translate = demo_translate if args.mode == 'business' else None
        if args.mode == 'retrieval':
            summary = lambda q,p: {'status':'insufficient_evidence','query':q,'claims':[],
                                  'limitations':['Generation not requested.']}
        elif args.demo:
            summary = demo_summary
            generation = {'provider':'synthetic', 'model':None, 'prompt_version':'fixture-v1'}
        else:
            from src.generation import create_generate, summarize_with_generation
            generate, generation = create_generate()
            summary = lambda q,p: summarize_with_generation(q,p,generate=generate)
        research = lambda request: run_research(request, retrieve=retrieve, summarize_fn=summary, translate_fn=translate)
    provenance = source_provenance(execution='synthetic_fixture' if args.demo else 'adapter_unspecified' if args.research_adapter else 'persistent_corpus', generation=generation)
    context = {k:getattr(args,k) for k in ('industry','jurisdiction') if getattr(args,k) is not None}
    artifact = capture(json.loads(args.cases.read_text()), research_fn=research, provenance=provenance,
                       top_k=args.top_k, context=context)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'run.json').write_text(json.dumps(artifact, indent=2, allow_nan=False)+'\n')
    export_review_table(artifact, args.output/'review.csv')
    print(json.dumps({'run_id':artifact['run_id'],'queries':len(artifact['cases']),
                      'failed':sum(r['status']=='error' for r in artifact['cases'])}))
    return int(any(r['status']=='error' for r in artifact['cases']))


if __name__ == '__main__':
    raise SystemExit(main())

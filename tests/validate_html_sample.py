"""Validate cached real HTML-first sources and persistent citation transport.

Run ``python -m tests.validate_html_sample --output /tmp/new-validation.json``.
Fetch sources separately with the existing download helpers. No generation/API
key or semantic model is used; deterministic vectors prove transport only.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import tempfile
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
import chromadb
import numpy as np
import pandas as pd
import pymupdf

from src import retrieval
from src.data_ingestion import config as cfg
from src.data_ingestion.download import load_html, resolve_pdf_path
from src.data_ingestion.html_parser import parse_html_sections
from src.data_ingestion.metadata import load_metadata
from src.data_ingestion.pdf_parser import extract_pages
from src.data_ingestion.pipeline import process_and_store

ROOT = Path(__file__).resolve().parents[1]
TRANSPORT_MODEL = 'deterministic-citation-transport-v1-not-semantic'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def normalized(text):
    return re.sub(r'\s+', ' ', text).strip()


def html_context(html):
    soup = BeautifulSoup(html, 'html.parser')
    for figure in soup.select('figure'):
        caption = figure.find('figcaption')
        figure.replace_with(caption) if caption else figure.decompose()
    for omitted in soup.select('.ltx_bibliography, .ltx_appendix, .ltx_equation, .ltx_equationgroup, .ltx_proof, .ltx_tag, nav'):
        omitted.decompose()
    for math in soup.find_all('math'):
        math.replace_with(math.get('alttext', ''))
    # Original DOM scopes, independently extracted from the parser's sections.
    scopes = {node['id']: normalized(node.get_text(' ', strip=True))
              for node in soup.find_all(id=True)}
    scopes[''] = normalized(soup.get_text(' ', strip=True))
    return scopes, parse_html_sections(html)


def verify_html(chunk, html, *, context=None):
    """Verify text against parsed section AND original linked DOM scope.

    The independent DOM comparison applies only documented omissions and inline
    math substitutions, not the ingestion section/paragraph extraction logic.
    """
    if pd.notna(chunk.get('page_number')):
        raise AssertionError('HTML acquired an invented PDF page')
    fragment = unquote(urlsplit(chunk['html_url']).fragment)
    scopes, sections = context if context is not None else html_context(html)
    if fragment not in scopes:
        raise AssertionError(f'Absent HTML anchor: {fragment}')
    body = normalized(chunk['text'])
    # Section extraction can omit headings/theorem labels between paragraphs.
    # Require every passage token in order within this exact source scope, while
    # the separate parsed-section check below requires a contiguous cleaned span.
    # Split punctuation separately: the text splitter can place sentence punctuation
    # in the next chunk, so whitespace-delimited boundary tokens are not stable.
    source_tokens = iter(re.findall(r'\w+|[^\w\s]', scopes[fragment]))
    for token in re.findall(r'\w+|[^\w\s]', body):
        if not any(source_token == token for source_token in source_tokens):
            raise AssertionError('Passage token absent/out of order in original linked HTML scope')
    matches = [s for s in sections
               if s['section'] == chunk['section'] and s['subsection'] == chunk['subsection']
               and (s.get('subsection_id') or s.get('section_id') or '') == fragment]
    if not any(body in normalized(s['text']) for s in matches):
        raise AssertionError('Passage does not match cited parsed section')


def verify_pdf(chunk, pages, page_count):
    page = chunk['page_number']
    if pd.isna(page) or int(page) != page or not 1 <= page <= page_count:
        raise AssertionError('PDF citation is outside original document')
    if chunk['text'] not in pages.get(int(page), ''):
        raise AssertionError('Passage absent from cited cleaned PDF page')


def index_snapshot(collection):
    result = collection.get(include=['documents', 'metadatas'])
    rows = sorted(zip(result['ids'], result['documents'], result['metadatas']))
    return sha256(json.dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()


def transport_check(frame):
    # Never relabel deterministic vectors as the production embedding model.
    vectors = np.array([[1.0, (i + 1) / (len(frame) + 1)] for i in range(len(frame))])
    class QueryModel:
        def encode(self, texts):
            return np.array([[1.0, 0.5] for _ in texts])
    with tempfile.TemporaryDirectory(prefix='kpmg-transport-') as directory, patch.object(
            retrieval, 'CHROMA_DIR', Path(directory)), patch.object(
            retrieval, 'EMBEDDING_MODEL', TRANSPORT_MODEL):
        collection = retrieval.store_embeddings(frame, vectors)
        first = index_snapshot(collection)
        expected = {r['chunk_id']: r for r in frame.to_dict('records')}
        stored = collection.get(include=['documents', 'metadatas'])
        for ident, text, metadata in zip(stored['ids'], stored['documents'], stored['metadatas']):
            assert text == expected[ident]['text'], ident
            assert metadata == retrieval.citation_metadata(expected[ident]), ident
        assert set(stored['ids']) == set(expected)
        collection.upsert(ids=['validation-stale-record'], embeddings=[[0.0, 0.0]],
                          documents=['stale validation record'], metadatas=[{'source':'synthetic'}])
        collection = retrieval.store_embeddings(frame, vectors)
        assert index_snapshot(collection) == first, 'Rerun/stale cleanup changed corpus'
        # Reopen a real persistent client and exercise the production search adapter.
        reopened = chromadb.PersistentClient(path=directory)
        hits = retrieval.search('citation transport probe', client=reopened, model=QueryModel())
        assert len(hits) == min(5, len(frame))
        for hit in hits:
            row = expected[hit['chunk_id']]
            assert hit['text'] == row['text']
            citation = retrieval.citation_metadata(row)
            assert all(hit[key] == value for key, value in citation.items())
            assert hit['page_number'] == citation.get('page_number')
        return {'status':'passed', 'model':TRANSPORT_MODEL, 'indexed_chunks':len(frame),
                'indexed_content_sha256':first, 'search_hits':len(hits),
                'checks':['every persisted text/metadata row', 'persistent reopen/search',
                          'identical upsert rerun', 'stale record removal'],
                'semantic_relevance_measured':False}


def validate():
    metadata = pd.DataFrame(load_metadata())
    metadata['base_id'] = metadata['arxiv_id'].str.replace(r'v\d+$', '', regex=True)
    latest = metadata.sort_values('updated').drop_duplicates('base_id', keep='last').to_dict('records')
    report = {'created_at':datetime.now(timezone.utc).isoformat(),
              'repo_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'mode':'html_first', 'generation_model':None,
              'validator_sha256':digest(Path(__file__)),
              'command':'python -m tests.validate_html_sample --output <new-report.json>',
              'metadata_hashes':{str(p.relative_to(ROOT)):digest(p) for p in (cfg.SAMPLE_FILE,cfg.FULL_METADATA_FILE)},
              'source_acquisition':'cached-only validation; consult acquisition log for fresh/cache provenance',
              'papers':[], 'failures':[], 'omissions':['HTML equations/proofs, figure/table bodies, references/appendices are intentionally excluded',
              'PDF checks compare cited original-page cleaned text; not a visual layout or semantic correctness audit'],
              'semantic_relevance_measured':False}
    # Check each paper independently so a missing/corrupt source is visible in the
    # report while the production all-or-nothing publish remains authoritative.
    with tempfile.TemporaryDirectory(prefix='kpmg-paper-validation-') as directory:
        for row in latest:
            aid = row['arxiv_id']
            html = cfg.HTML_DIR / f'{aid}.html'
            pdf = resolve_pdf_path(aid)
            item = {'arxiv_id':aid, 'source_hashes':{}, 'source_urls':{'html':f'https://arxiv.org/html/{aid}', 'pdf':row['pdf_url']}}
            for kind, path in [('html',html),('pdf',pdf)]:
                if path is not None and path.is_file(): item['source_hashes'][kind] = digest(path)
            item['html_availability'] = 'cached_html' if html.exists() else 'cached_404' if (cfg.HTML_DIR/f'{aid}.nohtml').exists() else 'unavailable_unconfirmed'
            try:
                frame = process_and_store([row], Path(directory)/f'{aid}.parquet')
                assert frame['chunk_id'].is_unique
                assert frame['text'].str.len().between(1,1800).all()
                assert len(set(frame['source'])) == 1
                source = frame.iloc[0]['source']
                item.update(source=source,chunks=len(frame),sections=sorted(set(frame['section'])))
                for field in ('title','authors','abstract','categories','published','updated','pdf_url'):
                    assert set(frame[field]) == {row[field]}, f'Metadata mismatch: {field}'
                if source == 'html':
                    source_html = load_html(aid)
                    context = html_context(source_html)
                    for chunk in frame.to_dict('records'): verify_html(chunk, source_html, context=context)
                    sections = context[1]
                    covered = {(c['section'], c['subsection']) for c in frame.to_dict('records')}
                    item['parsed_sections'] = len(sections)
                    item['sections_without_chunks'] = [{'section':s['section'],'subsection':s['subsection'],'characters':len(s['text'])}
                                                       for s in sections if (s['section'],s['subsection']) not in covered]
                    item['anchored_chunks'] = sum(bool(urlsplit(u).fragment) for u in frame['html_url'])
                else:
                    with pymupdf.open(pdf) as doc: item['pdf_pages'] = len(doc)
                    pages = {p['page']:p['text'] for p in extract_pages(str(pdf))}
                    for chunk in frame.to_dict('records'): verify_pdf(chunk,pages,item['pdf_pages'])
                item.update(status='passed',source=source,chunks=len(frame),sections=sorted(set(frame['section'])))
            except Exception as exc:
                item.update(status='failed',error=f'{type(exc).__name__}: {exc}')
                report['failures'].append({'arxiv_id':aid,'error':item['error']})
            report['papers'].append(item)
    if not report['failures']:
        frame = process_and_store(latest)
        stored = pd.read_parquet(cfg.PROCESSED_DIR/'chunks.parquet')
        pd.testing.assert_frame_equal(frame,stored)
        pd.testing.assert_frame_equal(process_and_store(latest),stored)
        assert set(frame['arxiv_id']) == {r['arxiv_id'] for r in latest}
        assert frame['chunk_id'].is_unique
        report.update(chunks=len(frame),parquet_sha256=digest(cfg.PROCESSED_DIR/'chunks.parquet'),
                      corpus_checks=['locked IDs covered','Parquet readback','identical ingestion rerun'])
        report['transport'] = transport_check(frame)
        # Force the existing PDF fallback on one real cached paper in a separate
        # diagnostic snapshot. Do not claim that this is the normal source mode.
        probe_row = next(r for r in latest if r['arxiv_id'] == '2602.00931v2')
        from src.data_ingestion import pipeline
        with tempfile.TemporaryDirectory(prefix='kpmg-fallback-') as directory, patch.object(
                pipeline, 'load_html', return_value=None):
            fallback = process_and_store([probe_row], Path(directory)/'fallback.parquet')
            pdf = resolve_pdf_path(probe_row['arxiv_id'])
            with pymupdf.open(pdf) as document: page_count = len(document)
            pages = {p['page']:p['text'] for p in extract_pages(str(pdf))}
            for chunk in fallback.to_dict('records'): verify_pdf(chunk,pages,page_count)
            mixed = pd.concat([frame[frame['arxiv_id'] != probe_row['arxiv_id']],fallback],ignore_index=True)
            report['forced_fallback_probe'] = {'arxiv_id':probe_row['arxiv_id'],
                'normal_source':'html','probe_source':'pdf','pdf_sha256':digest(pdf),
                'pdf_url':probe_row['pdf_url'],'chunks':len(fallback),
                'note':'Forced cached PDF diagnostic, not normal HTML-first corpus or semantic evaluation.',
                'mixed_transport':transport_check(mixed)}
    report['status'] = 'passed' if not report['failures'] else 'failed'
    report['baseline'] = {'mode':'pdf_only','report':'docs/ingestion-validation.json',
                          'sha256':digest(ROOT/'docs/ingestion-validation.json'),
                          'note':'Preserved baseline; counts are not HTML-first counts.'}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error('Report already exists; choose a new output')
    report = validate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as file: json.dump(report,file,indent=2,allow_nan=False); file.write('\n')
    print(json.dumps({'status':report['status'],'papers':len(report['papers']),'failures':len(report['failures'])}))
    return int(report['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())

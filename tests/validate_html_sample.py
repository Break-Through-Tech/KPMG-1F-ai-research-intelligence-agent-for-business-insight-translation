"""Cached, read-only-source corpus audit: python -m tests.validate_html_sample.

Writes reports under docs and regenerated parquet/index only in a temporary directory.
Does not download sources, overwrite the production corpus, load MiniLM, or call Azure.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pandas as pd
from bs4 import BeautifulSoup

from src import retrieval
from src.data_ingestion import config, pipeline
from src.data_ingestion.metadata import load_metadata
from src.data_ingestion.download import resolve_pdf_path
from src.data_ingestion.html_parser import parse_html_sections
from src.data_ingestion.pdf_parser import extract_pages
from tests.html_transport import validate_transport


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(text):
    return ' '.join(text.split())


def is_subsequence(text, original):
    """Match ordered source words while ignoring punctuation and case."""
    source_words = iter(re.findall(r"\w+", original.casefold()))
    target_words = re.findall(r"\w+", text.casefold())
    return all(any(source == target for source in source_words) for target in target_words)


def inspect_paper(metadata, paper):
    aid = metadata['arxiv_id']
    html_path = config.HTML_DIR / f'{aid}.html'
    pdf_path = resolve_pdf_path(aid)
    record = dict(arxiv_id=aid, source_modes=sorted(paper.source.unique().tolist()),
                  chunks=len(paper), sections={}, source_urls=[], omissions={}, failures=[],
                  source_hashes={}, candidates_for_40_43=[])
    for path in [html_path, pdf_path]:
        if path and path.exists():
            record['source_hashes'][str(path.relative_to(config.PROJECT_ROOT))] = sha(path)
    for field in ('title', 'authors', 'categories', 'abstract', 'published', 'updated', 'pdf_url'):
        if set(paper[field]) != {metadata[field]}:
            record['failures'].append(f'Metadata mismatch: {field}')
    soup = None
    sections = []
    pages = {}
    if 'html' in record['source_modes']:
        if not html_path.exists():
            record['failures'].append('HTML source cache missing')
            return record
        raw = html_path.read_text(encoding='utf-8')
        soup = BeautifulSoup(raw, 'html.parser')
        sections = parse_html_sections(raw)
        selectors = {'figures_or_tables': 'figure', 'display_equations': '.ltx_equation',
                     'proofs': '.ltx_proof', 'bibliographies': '.ltx_bibliography',
                     'appendices': '.ltx_appendix', 'navigation': 'nav'}
        record['omissions']['source_elements_subject_to_filtering'] = {
            name: len(soup.select(selector)) for name, selector in selectors.items()}
        record['omissions']['parsed_sections_without_chunks'] = [
            {'section': sec['section'], 'subsection': sec['subsection'], 'characters': len(sec['text'])}
            for sec in sections if not any(
                normalize(row.text) in normalize(sec['text']) and row.section == sec['section']
                for row in paper.itertuples())]
        # A bounded, reproducible symptom: eligible long paragraphs absent from parser output.
        retained = normalize(' '.join(sec['text'] for sec in sections))
        for node in soup.select('.ltx_para'):
            if node.select_one('.ltx_para') or node.find_parent(class_=re.compile(
                    r'ltx_(appendix|bibliography|proof|equation|figure|table)')):
                continue
            copy = BeautifulSoup(str(node), 'html.parser')
            for math in copy.find_all('math'):
                math.replace_with(math.get('alttext', ''))
            text = normalize(copy.get_text(' ', strip=True))
            if len(text) >= 150 and text not in retained:
                record['candidates_for_40_43'].append({'element_id': node.get('id'),
                    'characters': len(text), 'excerpt': text[:180],
                    'classification': 'candidate omitted/normalized paragraph; needs human layout review'})
        # Independent raw DOM projection for ordered source-text checks.
        for math in soup.find_all('math'):
            math.replace_with(math.get('alttext', ''))
    if 'pdf' in record['source_modes']:
        if not pdf_path:
            record['failures'].append('PDF source cache missing')
            return record
        pages = {p['page']: p['text'] for p in extract_pages(str(pdf_path))}
        record['omissions']['pdf_policy'] = 'Back matter cutoff; short sections filtered; no OCR. Visual fidelity not tested.'
    urls = set()
    for row in paper.to_dict('records'):
        try:
            citation = retrieval.citation_metadata(row)
            urls.add(citation['source_url'])
            if row['source'] == 'html':
                if not pd.isna(row['page_number']):
                    raise ValueError('HTML has an invented PDF page')
                url = urlsplit(citation['source_url'])
                if url.scheme != 'https' or url.netloc != 'arxiv.org' or url.path != f'/html/{aid}':
                    raise ValueError('Wrong HTML paper URL')
                anchor = unquote(url.fragment)
                node = soup.find(id=anchor) if anchor else soup
                if node is None:
                    raise ValueError(f'Heading anchor absent in cached source: {anchor}')
                matching = [sec for sec in sections if sec['section'] == row['section']
                            and sec['subsection'] == row.get('subsection', '')
                            and (sec.get('subsection_id') or sec.get('section_id') or '') == anchor]
                if not any(normalize(row['text']) in normalize(sec['text']) for sec in matching):
                    raise ValueError('Passage absent from cited parsed section')
                if not is_subsequence(row['text'], node.get_text(' ', strip=True)):
                    raise ValueError('Passage words absent/out of order in raw cited DOM')
            else:
                page = citation['page_number']
                if page not in pages or normalize(row['text']) not in normalize(pages[page]):
                    raise ValueError('Passage absent from cited PDF page')
                if citation['source_url'] != metadata['pdf_url'].split('#')[0] + f'#page={page}':
                    raise ValueError('Wrong PDF citation URL')
        except (ValueError, KeyError, TypeError) as error:
            record['failures'].append(f"{row['chunk_id']}: {error}")
    record['sections'] = paper.groupby('section', dropna=False).size().to_dict()
    record['source_urls'] = sorted(urls)
    record['verified_passages'] = len(paper) - sum('_c' in e for e in record['failures'])
    return record


def git(*args):
    return subprocess.check_output(['git', '-c', f'safe.directory={config.PROJECT_ROOT}',
                                    '-C', str(config.PROJECT_ROOT), *args], text=True).strip()


def validate():
    corpus = config.PROCESSED_DIR / 'chunks.parquet'
    report = {'run_utc': datetime.now(timezone.utc).isoformat(), 'repo_sha': git('rev-parse', 'HEAD'),
              'branch': git('branch', '--show-current'), 'git_status': git('status', '--short'),
              'command': 'python -m tests.validate_html_sample', 'mode': 'HTML-first; cached sources only',
              'production_embedding_model': retrieval.MODEL_NAME, 'embedding_dimensions': 384,
              'embedding_relevance_tested': False, 'failures': [], 'papers': []}
    protected = [corpus, config.FULL_METADATA_FILE, config.SAMPLE_FILE,
                 config.PROJECT_ROOT/'tests/validate_ingestion_sample.py',
                 config.PROJECT_ROOT/'docs/ingestion-validation.md',
                 config.PROJECT_ROOT/'docs/ingestion-validation.json']
    before = {str(p.relative_to(config.PROJECT_ROOT)): sha(p) for p in protected if p.exists()}
    report['input_hashes'] = before
    report['implementation_hashes'] = {str(p.relative_to(config.PROJECT_ROOT)): sha(p)
        for p in [Path(__file__), Path(__file__).with_name('html_transport.py'),
                  config.PROJECT_ROOT/'src/retrieval.py', *sorted((config.PROJECT_ROOT/'src/data_ingestion').glob('*.py'))]}
    metadata = load_metadata()
    frame = pd.read_parquet(corpus)
    locked = set(pd.read_csv(config.SAMPLE_FILE).arxiv_id)
    report.update(locked_papers=len(locked), persisted_chunks=len(frame),
                  persisted_source_counts=frame.groupby('source').size().to_dict())
    if len(locked) != 25 or set(frame.arxiv_id) != locked:
        report['failures'].append('Locked 25-paper coverage mismatch')
    if not frame.chunk_id.is_unique or not frame.text.str.len().between(1,1800).all():
        report['failures'].append('Duplicate IDs or invalid chunk text lengths')
    for row in metadata:
        subset = frame[frame.arxiv_id == row['arxiv_id']]
        if subset.empty:
            report['failures'].append(f"Missing paper {row['arxiv_id']}")
            continue
        result = inspect_paper(row, subset)
        report['papers'].append(result)
        report['failures'].extend(result['failures'])
    with tempfile.TemporaryDirectory(prefix='html-validation-') as directory:
        temp = Path(directory)
        try:
            generated = pipeline.process_and_store(metadata, temp/'first.parquet')
            second = pipeline.process_and_store(metadata, temp/'second.parquet')
            pd.testing.assert_frame_equal(generated, pd.read_parquet(temp/'first.parquet'))
            pd.testing.assert_frame_equal(generated, second)
            pd.testing.assert_frame_equal(frame, generated)
            report['cached_ingestion_rerun'] = 'PASS: persisted == regenerated == second run'
            report['regenerated_parquet_sha256'] = sha(temp/'first.parquet')
        except Exception as error:
            report['cached_ingestion_rerun'] = 'FAIL: ' + str(error)
            report['failures'].append(report['cached_ingestion_rerun'])
        try:
            report['transport'] = validate_transport(frame, temp/'isolated.sqlite')
        except Exception as error:
            report['failures'].append('Transport: '+str(error))
    report['protected_inputs_unchanged'] = all(sha(config.PROJECT_ROOT/p)==h for p,h in before.items())
    if not report['protected_inputs_unchanged']:
        report['failures'].append('Protected input changed')
    report['source_files_unchanged'] = all(sha(config.PROJECT_ROOT/p)==h for row in report['papers']
                                         for p,h in row['source_hashes'].items())
    report['status'] = 'PASS' if not report['failures'] else 'FAIL'
    return report


def write_report(report, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory/'html-ingestion-validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False),encoding='utf-8')
    lines = ['# HTML-first corpus and citation validation', '',
             f"Status: **{report['status']}**. Run UTC: {report['run_utc']}.",
             f"Base commit: `{report['repo_sha']}`; branch: `{report['branch']}`.",
             'Validator changes are uncommitted; exact implementation and source SHA256 hashes are in the companion JSON.', '',
             'Command: `python -m tests.validate_html_sample`', '',
             f"Locked papers: **{report['locked_papers']}**; persisted chunks: **{report['persisted_chunks']}**; modes: `{report['persisted_source_counts']}`.",
             f"Cached rerun: {report.get('cached_ingestion_rerun')}", '',
             '## Per-paper results', '',
             '| Paper | Mode | Chunks | Section coverage (chunks) | Source URLs | Omissions / review candidates | Failures |',
             '|---|---|---:|---|---|---|---|']
    for row in report['papers']:
        urls='<br>'.join(f'[source {i+1}]({url})' for i,url in enumerate(row['source_urls']))
        sections='; '.join(f'{k}: {v}' for k,v in row['sections'].items()).replace('|','/')
        omissions=json.dumps(row['omissions'],ensure_ascii=False).replace('|','/')
        lines.append(f"| {row['arxiv_id']} | {', '.join(row['source_modes'])} | {row['chunks']} | {sections} | {urls} | {omissions}; candidates: {len(row['candidates_for_40_43'])} | {len(row['failures'])} |")
    lines += ['', '## Verified scope and limits', '',
        '- Real cached arXiv HTML/PDF sources; no fresh fetch or live URL availability check.',
        '- Every persisted passage checked against its cited parsed section and ordered words in the cached raw HTML DOM; anchors must exist. PDF-backed passages, if any, must match extracted text on the cited original page.',
        '- HTML page numbers must be null. No claim of visual PDF/table fidelity or factual research correctness.',
        '- Parser omission counts describe filtering exposure, not proof that all removed content is harmless. Review candidates are symptoms, not automatically confirmed defects.',
        '- Production model remains MiniLM all-MiniLM-L6-v2 (384 dimensions). This run did not load it or measure semantic relevance.',
        '- Transport uses production Azure serialization/search functions with a disposable SQLite-backed client double and deterministic fingerprint vectors. This is persistent transport testing, NOT live Azure verification.',
        '- The shared Azure index was not queried or modified. Its reported 877 live documents were not independently checked by this run.',
        '- Current corpus is HTML-only: real PDF fallback transport is covered by the existing synthetic PDF integration tests, not a real mixed-source corpus in this report.',
        '- The existing PDF-only validator/report and production parquet were preserved. The old 1,671 count describes the PDF-only baseline, not this corpus.', '',
        '## Persistent transport and stale records', '', '```json',
        json.dumps({k:v for k,v in report.get('transport',{}).items() if k!='query_probes'},indent=2), '```', '',
        'Upload-only reruns retain an obsolete row after shrinking the corpus. Explicit rebuild through a patched management client removes it. This verifies the application-level contract; a dedicated Azure test index is still needed to verify service behavior.', '',
        '## Findings for Issues #40 / #43', '',
        'No issue comments were posted. The following bounded source candidates are prepared for owner review; inspect the listed cached element and compare with parse_html_sections output. Full source hashes and excerpts are in the JSON.', '']
    for row in report['papers']:
        for finding in row['candidates_for_40_43']:
            lines.append(f"- `{row['arxiv_id']}` element `{finding['element_id']}` ({finding['characters']} characters): {finding['excerpt']}")
    lines += ['', '## Failures', '', *(report['failures'] or ['None in the executed checks.']), '',
              '## Still unverified / handoff', '',
              'Live isolated Azure persistence/relevance, fresh-source availability, visual layout quality, and real PDF fallback papers in a mixed corpus were not tested. #40/#43 findings have not been posted. Azure returns score rather than the issue draft’s distance field; coordinate that contract difference with #76. Do not interpret score as confidence.']
    (directory/'html-ingestion-validation.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,default=config.PROJECT_ROOT/'docs')
    args=parser.parse_args()
    result=validate()
    write_report(result,args.report_dir)
    print(json.dumps({'status':result['status'],'papers':len(result['papers']),
                      'chunks':result['persisted_chunks'],'failures':result['failures']},indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)

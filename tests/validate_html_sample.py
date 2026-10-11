"""Cached, read-only-source corpus audit: python -m tests.validate_html_sample.
Writes reports under docs and regenerated parquet/index only in a temporary directory.
Does not download sources, overwrite the production corpus, or use a shared index.
An optional separately executed offline MiniLM smoke result can be attached.
"""
import argparse
import hashlib
import math
import json
import re
import subprocess
import tempfile
import sys
import platform
from collections import Counter
from importlib.metadata import version
from unittest.mock import patch
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
from tests.html_transport import validate_transport, implementation_hashes, SEMANTIC_PROBES


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(text):
    return ' '.join(text.split())


def is_subsequence(text, original):
    """Match ordered source words while ignoring punctuation and case."""
    source_words = iter(re.findall(r"\w+", original.casefold()))
    target_words = re.findall(r"\w+", text.casefold())
    return all(any(source == target for source in source_words) for target in target_words)


def projected_paragraph(node):
    """Compare the same paragraph before/after documented filtering; retain full evidence."""
    clone = BeautifulSoup(str(node), 'html.parser')
    counts = {name: len(clone.select(selector)) for name, selector in {
        'equations': '.ltx_equation, .ltx_equationgroup', 'proofs': '.ltx_proof',
        'tags': '.ltx_tag', 'figures': 'figure'}.items()}
    for fig in clone.select('figure'):
        caption = fig.find('figcaption')
        fig.replace_with(caption) if caption else fig.decompose()
    for tag in clone.select('.ltx_bibliography,.ltx_appendix,.ltx_equation,.ltx_equationgroup,.ltx_proof,.ltx_tag,nav'):
        tag.decompose()
    for math in clone.find_all('math'):
        math.replace_with(math.get('alttext', ''))
    return normalize(clone.get_text(' ', strip=True)), counts


def source_title(node):
    heading = (node.find(re.compile(r'^h[1-6]$'), class_='ltx_title', recursive=False)
               or node.find(re.compile(r'^h[1-6]$'), class_='ltx_title'))
    if not heading:
        return ''
    copy = BeautifulSoup(str(heading), 'html.parser')
    for tag in copy.select('.ltx_tag'):
        tag.decompose()
    return re.sub(r'^chapter\s+\d+\s*', '', copy.get_text(' ', strip=True).lower())


def classify_candidate(node, retained, chunk_text):
    projected, filters = projected_paragraph(node)
    ancestors = [{'tag': a.name, 'classes': a.get('class', []), 'id': a.get('id')}
                 for a in node.parents if a.name in ('section', 'div', 'article')][:6]
    heading_names = [source_title(a) for a in node.parents if a.name == 'section']
    classes = {c for a in ancestors for c in a['classes']}
    low_value = any(name.startswith(('acknowledg','contents','list of','bibliograph','references',
                                    'dedication','declaration','author contribution')) for name in heading_names)
    supplement = bool(re.search(r'\bappendix\b', projected[:100], re.I))
    in_parser = bool(projected and projected in retained)
    prefix = projected[:100]
    prefix_in_chunks = bool(prefix and prefix in chunk_text)
    structural = bool(classes & {'ltx_paragraph','ltx_subsubsection','ltx_theorem'})
    structural_candidate = bool(len(projected) >= 150 and structural and not low_value and not supplement
                     and not in_parser and prefix not in retained and not prefix_in_chunks)
    skipped_chapter = node.find_parent('section', class_='ltx_chapter')
    explicit_skip = bool(skipped_chapter and source_title(skipped_chapter).startswith(
        ('acknowledg','contents','list of','bibliograph','references','dedication','declaration')))
    if explicit_skip:
        category = 'intentionally_excluded_low_value_or_back_matter'
    elif filters['equations'] or filters['proofs']:
        category = 'scientific_detail_filtered'
    elif in_parser:
        category = 'false_positive_review_candidate'
    elif structural_candidate:
        category = 'potentially_missing_meaningful_text'
    else:
        category = 'parser_chunking_needs_investigation'
    return {'category': category, 'projected_text': projected, 'filter_counts': filters,
            'low_value_content_candidate': low_value, 'back_matter_candidate': supplement,
            'explicit_chapter_skip_policy': explicit_skip, 'projected_text_in_parser': in_parser, 'prefix_in_generated_chunks': prefix_in_chunks,
            'automated_structural_omission_candidate': structural_candidate, 'ancestors': ancestors,
            'source_headings': heading_names,
            'expected': 'Preserve substantive paragraph text under its actual source heading.' if structural_candidate else 'Review filtering policy and retrieval impact.',
            'actual': 'Paragraph prefix absent from parsed sections and persisted chunks.' if structural_candidate else 'See projection and filter counts.',
            'why_it_matters': 'Missing evidence cannot be retrieved even when retained passages have correct citations.' if structural_candidate else 'Filtering can change scientific completeness; candidate alone is not a defect.',
            'reproduction': 'Load data/html/<paper>.html; locate this element ID; compare parse_html_sections(raw) and chunks.parquet text.',
            'suggested_follow_up': '#40: nested-wrapper traversal with no duplicate paragraphs; #43: remediation and owner review.' if structural_candidate else '#40/#43: review extraction policy.'}


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
        record['omissions']['parsed_sections_without_chunks'] = []
        for sec in sections:
            anchor = sec.get('subsection_id') or sec.get('section_id') or ''
            matches = [row for row in paper.to_dict('records')
                       if row['section'] == sec['section'] and row.get('subsection', '') == sec['subsection']
                       and unquote(urlsplit(row.get('html_url', '')).fragment) == anchor
                       and normalize(row['text']) in normalize(sec['text'])]
            if not matches:
                record['omissions']['parsed_sections_without_chunks'].append({
                    'section': sec['section'], 'subsection': sec['subsection'], 'anchor': anchor,
                    'characters': len(sec['text']), 'text': sec['text'],
                    'reason': 'Below 150-character HTML threshold' if len(sec['text'].strip()) < 150 else 'Investigate: substantive section unrepresented'})
        # A bounded, reproducible symptom: eligible long paragraphs absent from parser output.
        retained = normalize(' '.join(sec['text'] for sec in sections))
        chunk_text = normalize(' '.join(paper.text))
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
                    'classification': 'candidate omitted/normalized paragraph; needs human layout review',
                    'triage': classify_candidate(node, retained, chunk_text)})
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
    verified_passages = 0
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
                if row['section'] != 'abstract':
                    chapter = node if 'ltx_chapter' in node.get('class', []) else node.find_parent(class_='ltx_chapter')
                    top = chapter or (node if 'ltx_section' in node.get('class', []) else node.find_parent(class_='ltx_section'))
                    if top is None or re.sub(r'\s+', '', source_title(top)) != re.sub(r'\s+', '', row['section']):
                        raise ValueError('Section differs from original HTML heading')
                    if row.get('subsection') and re.sub(r'\s+', '', source_title(node)) != re.sub(r'\s+', '', row['subsection']):
                        raise ValueError('Subsection differs from original HTML heading')
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
            verified_passages += 1
        except (ValueError, KeyError, TypeError) as error:
            record['failures'].append(f"{row['chunk_id']}: {error}")
    record['sections'] = paper.groupby('section', dropna=False).size().to_dict()
    record['source_urls'] = sorted(urls)
    record['verified_passages'] = verified_passages
    return record


def git(*args):
    """Best-effort provenance: missing refs or Git cannot invalidate source checks."""
    try:
        return subprocess.check_output(['git', '-c', f'safe.directory={config.PROJECT_ROOT}',
            '-C', str(config.PROJECT_ROOT), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_provenance():
    base = git('rev-parse', 'origin/main')
    count = git('rev-list', '--count', 'origin/main..HEAD') if base else None
    changed = git('diff', '--name-only', 'origin/main', '--', 'src', 'main.py',
                  'requirements.txt', '.env.example') if base else None
    staged = git('diff', '--cached', '--name-only')
    return {'origin_main_sha': base, 'main_sha': git('rev-parse', 'main'),
            'production_changed_files': changed.splitlines() if changed is not None else None,
            'commits_above_origin_main': int(count) if count and count.isdigit() else None,
            'staged_files': staged.splitlines() if staged is not None else None,
            'note': 'Optional local Git provenance; unavailable refs are null. No personal branches are required.'}


def summarize_omissions(papers):
    candidates = [c for p in papers for c in p['candidates_for_40_43']]
    structural = [c for c in candidates if c['triage']['automated_structural_omission_candidate']]
    return {'candidate_count': len(candidates),
        'categories': dict(Counter(c['triage']['category'] for c in candidates)),
        'automated_structural_omission_candidate_paragraphs': len(structural),
        'structural_candidates_by_primary_category': dict(Counter(c['triage']['category'] for c in structural)),
        'papers_with_structural_candidates': sorted({p['arxiv_id'] for p in papers
            if any(c['triage']['automated_structural_omission_candidate'] for c in p['candidates_for_40_43'])}),
        'parsed_sections_without_chunks': sum(len(p['omissions'].get('parsed_sections_without_chunks', [])) for p in papers),
        'review_scope': 'Automated candidate flags overlap primary categories. They are not individual human confirmations.'}


def verify_semantic_evidence(evidence, report, frame=None):
    """Fail closed on stale or legacy evidence before claiming semantic verification."""
    if evidence.get('status') != 'COMPLETED':
        raise ValueError('Semantic evidence did not complete')
    expected_corpus = {k.replace('\\', '/'): v for k, v in report['input_hashes'].items()}['data/processed/chunks.parquet']
    if evidence.get('corpus_sha256') != expected_corpus:
        raise ValueError('Semantic evidence corpus hash mismatch')
    if evidence.get('implementation_hashes') != report['implementation_hashes']:
        raise ValueError('Semantic evidence implementation hashes missing or stale')
    if (evidence.get('model') != retrieval.EMBEDDING_MODEL or evidence.get('dimensions') != 384
            or evidence.get('indexed_count') != report['persisted_chunks']
            or evidence.get('citation_checks') != 'PASS'):
        raise ValueError('Semantic evidence model, dimensions, document count or citation checks mismatch')
    probes = evidence.get('probes', [])
    if [(p.get('query'), p.get('expected_paper')) for p in probes] != [(q, aid) for q, aid, _ in SEMANTIC_PROBES]:
        raise ValueError('Semantic evidence probe definitions mismatch')
    if any(not p.get('hits') for p in probes):
        raise ValueError('Semantic evidence has no search results')
    if frame is None:
        frame = pd.read_parquet(config.PROCESSED_DIR/'chunks.parquet')
    records = {row['chunk_id']: row for row in frame.to_dict('records')}
    if len(records) != len(frame) or len(frame) != report['persisted_chunks']:
        raise ValueError('Semantic evidence corpus count or duplicate IDs mismatch')
    for probe, (_, aid, marker) in zip(probes, SEMANTIC_PROBES):
        expected = frame[(frame.arxiv_id == aid) & frame.text.str.contains(marker, regex=False)]
        if (expected.empty or probe.get('expected_evidence_ids') != expected.chunk_id.tolist()
                or probe.get('expected_evidence_excerpt') != expected.iloc[0].text[:350]):
            raise ValueError('Semantic evidence preselected source passages mismatch')
        hits = probe['hits']
        if len(hits) != min(5, len(frame)) or len({h.get('chunk_id') for h in hits}) != len(hits):
            raise ValueError('Semantic evidence hit count or duplicate IDs mismatch')
        for hit in hits:
            row = records.get(hit.get('chunk_id'))
            if row is None or hit.get('text') != row['text']:
                raise ValueError('Semantic evidence hit ID or passage does not match corpus')
            citation = retrieval.citation_metadata(row)
            if (any(hit.get(key) != value for key, value in citation.items())
                    or 'page_number' not in hit or hit['page_number'] != citation.get('page_number')):
                raise ValueError('Semantic evidence hit citation does not match corpus')
            distance = hit.get('distance')
            if isinstance(distance, bool) or not isinstance(distance, (int, float)) or not math.isfinite(distance):
                raise ValueError('Semantic evidence distance must be finite')
        if probe.get('expected_paper_in_top_5') != any(h['arxiv_id'] == aid for h in hits):
            raise ValueError('Semantic evidence probe outcome does not match hits')
    if evidence.get('expected_paper_hits') != sum(p['expected_paper_in_top_5'] for p in probes):
        raise ValueError('Semantic evidence success count does not match probes')
    return evidence


def portable_command(report):
    command = 'python -m tests.validate_html_sample'
    if 'cached_pdf_fallback' in report:
        command += ' --cached-pdf'
    if 'semantic_smoke' in report:
        command += ' --semantic-evidence <temporary-results.json>'
    if 'automated_tests' in report:
        command += ' --test-results <test-results.json>'
    return command


def validate():
    corpus = config.PROCESSED_DIR / 'chunks.parquet'
    report = {'run_utc': datetime.now(timezone.utc).isoformat(), 'repo_sha': git('rev-parse', 'HEAD'),
              'branch': git('branch', '--show-current'), 'git_status': git('status', '--short'),
              'command': 'python -m tests.validate_html_sample', 'mode': 'HTML-first; cached sources only',
              'production_embedding_model': retrieval.EMBEDDING_MODEL, 'embedding_dimensions': 384,
              'embedding_relevance_tested': False, 'failures': [], 'papers': [],
              'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                  'packages': {name: version(name) for name in ['chromadb','sentence-transformers','transformers','torch','pandas','pyarrow','beautifulsoup4','pytest','google-genai']}}}
    report['git_checks'] = git_provenance()
    protected = [corpus, config.FULL_METADATA_FILE, config.SAMPLE_FILE,
                 config.PROJECT_ROOT/'tests/validate_ingestion_sample.py',
                 config.PROJECT_ROOT/'docs/ingestion-validation.md',
                 config.PROJECT_ROOT/'docs/ingestion-validation.json']
    before = {str(p.relative_to(config.PROJECT_ROOT)): sha(p) for p in protected if p.exists()}
    report['input_hashes'] = before
    report['implementation_hashes'] = implementation_hashes()
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
        for candidate in result['candidates_for_40_43']:
            candidate['source_url'] = f"https://arxiv.org/html/{row['arxiv_id']}#{candidate['element_id']}" if candidate['element_id'] else f"https://arxiv.org/html/{row['arxiv_id']}"
            candidate['triage']['reproduction'] = (
                f"Read data/html/{row['arxiv_id']}.html and locate element {candidate['element_id']}; "
                'compare the projected_text recorded here with normalized parse_html_sections(raw) and the persisted paper chunk text. '
                'Run python -m tests.validate_html_sample to reproduce the classification; no ingestion run is needed.')
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
            report['transport'] = validate_transport(frame, temp/'isolated-chroma')
        except Exception as error:
            report['failures'].append('Transport: '+str(error))
    report['omission_summary'] = summarize_omissions(report['papers'])
    report['protected_inputs_unchanged'] = all(sha(config.PROJECT_ROOT/p)==h for p,h in before.items())
    if not report['protected_inputs_unchanged']:
        report['failures'].append('Protected input changed')
    report['source_files_unchanged'] = all(sha(config.PROJECT_ROOT/p)==h for row in report['papers']
                                         for p,h in row['source_hashes'].items())
    if not report['source_files_unchanged']:
        report['failures'].append('Source files changed during validation')
    report['status'] = 'PASS' if not report['failures'] else 'FAIL'
    return report


def validate_cached_pdf(metadata):
    """Force fallback using one ORIGINAL cached PDF; never write the source or corpus."""
    aid = '2602.00937v3'
    row = next((r for r in metadata if r['arxiv_id'] == aid), None)
    pdf = resolve_pdf_path(aid)
    if row is None or pdf is None:
        return {'status': 'NOT_TESTED', 'reason': 'Selected original cached PDF unavailable'}
    before = sha(pdf)
    with tempfile.TemporaryDirectory(prefix='issue82-real-pdf-') as directory:
        temp = Path(directory)
        (temp/'empty-html').mkdir()
        with patch.object(config, 'HTML_DIR', temp/'empty-html'):
            frame = pipeline.process_and_store([row], temp/'fallback.parquet')
        pd.testing.assert_frame_equal(frame, pd.read_parquet(temp/'fallback.parquet'))
        assert set(frame.source) == {'pdf'}
        paper = inspect_paper(row, frame)
        assert not paper['failures'], paper['failures']
        transport = validate_transport(frame, temp/'chroma')
    assert sha(pdf) == before
    return {'status': 'PASS', 'paper': aid, 'source': str(pdf.relative_to(config.PROJECT_ROOT)),
            'source_sha256': before, 'source_kind': 'original cached arXiv PDF, not synthetic',
            'chunks': len(frame), 'page_numbers': sorted(int(x) for x in frame.page_number.unique()),
            'verified_passages': paper['verified_passages'], 'transport': transport,
            'limitation': 'Matches cleaned PyMuPDF text on original pages, not visual layout/OCR accuracy.'}


def write_report(report, directory):
    """Short reviewer report; complete per-element evidence stays in JSON."""
    directory.mkdir(parents=True, exist_ok=True)
    previous_path = directory/'html-ingestion-validation.json'
    if previous_path.exists():
        previous = json.loads(previous_path.read_text(encoding='utf-8'))
        history = list(previous.get('historical_execution_details', []))
        entry = {key: previous[key] for key in ('run_utc', 'command', 'repo_sha', 'input_hashes', 'semantic_smoke') if key in previous}
        if entry not in history:
            history.append(entry)
        report['historical_execution_details'] = history
        # Historical manual notes are retained only when their cached sources still match.
        unchanged = all(p.get('source_hashes') == next((n['source_hashes'] for n in report['papers']
            if n['arxiv_id'] == p['arxiv_id']), None) for p in previous.get('papers', []))
        if unchanged and previous.get('manual_parser_review'):
            report['manual_parser_review'] = previous['manual_parser_review']
            report['manual_parser_review_provenance'] = {
                'review_run_utc': previous.get('manual_parser_review_provenance', {}).get('review_run_utc', previous['run_utc']),
                'cached_source_hashes_rechecked': True,
                'scope': 'Historical example inspection, not individual verification of all candidates.'}
    (directory/'html-ingestion-validation.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    def cell(value):
        return str(value).replace('|', '/').replace('\n', ' ')
    omission = report['omission_summary']
    transport = report.get('transport', {})
    semantic = report.get('semantic_smoke', {'status': 'NOT_TESTED'})
    pdf = report.get('cached_pdf_fallback', {'status': 'NOT_TESTED'})
    lines = ['# Issue #82: HTML-first corpus and citation handoff', '',
        '## 1. Executive summary', '',
        f"Retained-passage validation: **{report['status']}**. {len(report['papers'])} locked papers; {report['persisted_chunks']} HTML chunks; {len(report['failures'])} executed corpus/transport check failures.",
        f"Completeness review: **follow-up required**. {omission['automated_structural_omission_candidate_paragraphs']} paragraphs are automatically flagged for possible nested-wrapper omissions across {len(omission['papers_with_structural_candidates'])} papers. Correct retained citations do not establish complete extraction.",
        f"Chroma temporary persistence and reruns: {transport.get('reopened_verified_records', 0)} reopened records verified. MiniLM smoke: {semantic['status']}; expected paper present for {semantic.get('expected_paper_hits', 0)}/3 questions. Original cached PDF fallback: {pdf['status']}.", '',
        '## 2. Scope and objectives', '',
        'Audit the locked corpus, source text, heading anchors, Chroma transport, public search contract, and rerun safety. Production ingestion/retrieval are unchanged. No shared index, cloud service, or API credentials are used.',
        'Storage/search use `src/retrieval.py` and Chroma. `python -m src.data_ingestion.pipeline` is HTML-first; the compatibility entrypoint `python src/data_ingestion.py` remains PDF-only.',
        '`main.py` only initializes the environment. The Gemini human-checkpoint notebook/module is standalone and is not connected to arXiv search; no end-to-end Gemini handoff is claimed.', '',
        '## 3. Environment and reproducibility', '',
        f"Run UTC: `{report['run_utc']}`. Branch: `{report['branch']}`. HEAD/base: `{report['repo_sha']}`.",
        f"Python {report['environment']['python']}; Chroma {report['environment']['packages']['chromadb']}; SentenceTransformers {report['environment']['packages']['sentence-transformers']}.",
        'Uncommitted implementation hashes, all source/corpus hashes, dependency versions, query records, and complete omission evidence are in [the companion JSON](html-ingestion-validation.json). Cached sources only; no downloads or fresh availability checks.',
        'Fresh-checkout prerequisites: install `python -m pip install -r requirements.txt pytest`. The exact audited `data/processed/chunks.parquet`, 25 locked `data/html/<arxiv_id>.html` caches, and any cached PDFs listed under `source_hashes` in JSON are ignored by Git and must be supplied separately at those repository-relative paths. Compare their SHA-256 values with JSON. A code-only clone cannot reproduce the cached-corpus audit; downloading newer sources is a different run.',
        'No `.env` file, Azure credentials, personal Git branches, or existing vector database is needed. Run the base audit with `python -m tests.validate_html_sample --cached-pdf --report-dir audit-output`. Optional semantic checks additionally require an already cached MiniLM model; use new local output paths and regenerate semantic evidence whenever implementation hashes change.',
        'On this Windows run, `TEMP` and `TMP` point to the writable test directory recorded in JSON. Chroma workers exit before their temporary storage is removed.', '',
        'Run from the repository root (replace angle-bracket placeholders with local output paths). Exact execution commands remain in JSON.', '```text', portable_command(report), '```', '',
        'Semantic worker reproduction (set HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1; use a new temporary directory):',
        '```text', 'python -m tests.html_transport data/processed/chunks.parquet <temporary-index> <temporary-results.json> --semantic', '```', '',
        '## 4. Corpus validation results', '',
        f"{report.get('cached_ingestion_rerun')}. Sources unchanged: {report['source_files_unchanged']}; original corpus and PDF baseline unchanged: {report['protected_inputs_unchanged']}.",
        'The following section coverage counts distinct section labels. Full section/subsection coverage, anchors, source URLs, filtering counts, and excluded section text are retained per paper in JSON.', '',
        '| Paper | Mode | Chunks | Sections | Source example | Omission candidates | Check failures |',
        '|---|---|---:|---:|---|---:|---:|']
    for paper in report['papers']:
        source = paper['source_urls'][0] if paper['source_urls'] else ''
        lines.append(f"| {paper['arxiv_id']} | {','.join(paper['source_modes'])} | {paper['chunks']} | {len(paper['sections'])} | [cached anchor]({source}) | {len(paper['candidates_for_40_43'])} | {len(paper['failures'])} |")
    lines += ['', '## 5. ChromaDB persistence and retrieval verification', '',
        f"Deterministic transport: {transport.get('first_count')} indexed, {transport.get('rerun_count')} after identical rerun, {transport.get('reopened_verified_records')} reopened in a fresh process. Original IDs and stored passage/citation linkage checked for every record; one exact-text query per paper.",
        'Public `search(query, top_k=5)` returns `chunk_id`, `text`, `distance`, `arxiv_id`, `title`, `pdf_url`, `source`, `source_url`, and nullable `page_number`; available section/subsection fields survive. Distances remain distances. No ID encoding or score substitution is used.',
        f"Existing metadata updated; one stale row removed ({transport.get('count_after_corpus_rerun')} remain). Invalid citation rejection and a failure injected before upsert preserve the previous data.",
        'A failure injected after upsert at stale deletion demonstrates partial updates: new metadata is visible and the stale record remains searchable. A successful retry repairs it. **Atomic corpus rollback and process-crash recovery are not guaranteed or demonstrated.** Production also leaves Chroma client lifecycle to callers; temporary-test cleanup explicitly releases its systems.', '',
        '### Actual MiniLM smoke test', '',
        f"Status: {semantic['status']}. Model: `all-MiniLM-L6-v2`, 384 dimensions, CPU, cached weights only. Indexed records: {semantic.get('indexed_count', 'not tested')}.",
        'Expected papers/evidence were selected before search. The three questions are content-informed smoke probes, not held-out evaluation. MiniLM is configured for 256 tokens, so long character-based chunks can be truncated during embedding.', '',
        '| Question | Expected paper | Top result | Section | Distance | Review |',
        '|---|---|---|---|---:|---|']
    for probe in semantic.get('probes', []):
        hit = probe['hits'][0]
        lines.append(f"| {cell(probe['query'])} | {probe['expected_paper']} | `{hit['chunk_id']}` | {cell(hit.get('section'))} | {hit['distance']:.4f} | {cell(probe.get('manual_relevance_review', 'Pending human inspection'))} |")
    if semantic.get('error'):
        lines.append('Blocker: '+semantic['error'])
    lines += ['', '## 6. Citation verification', '',
        'All retained HTML passages are checked against the cited parsed section and ordered source words in the original cached DOM. Actual section/subsection headings (ignoring formatting whitespace) and source anchors are checked independently. HTML page numbers must be null.',
        f"Original cached PDF fallback: {pdf['status']}; paper `{pdf.get('paper', 'none')}`; {pdf.get('chunks', 0)} chunks checked against their original cleaned PDF pages and transported through temporary Chroma with `#page=N` citations.",
        'The main 25-paper corpus remains HTML-only. This separate fallback run uses an original cached PDF; automated PDF fixtures remain synthetic. Neither check establishes visual table fidelity, OCR quality, or complete extraction.', '',
        '## 7. Omission candidate findings', '',
        f"Reproduced candidates: **{omission['candidate_count']}**. Categories use paragraph-level filter projections and exact normalized comparisons; they do not certify scientific completeness.", '',
        '| Category | Candidates |', '|---|---:|']
    for category, count in sorted(omission['categories'].items()):
        lines.append(f'| {category} | {count} |')
    lines += ['',
        f"The structural flag overlaps the primary categories: {omission['structural_candidates_by_primary_category']}. Structural candidates comprise the primary-category counts above; in this corpus, 113 are potentially missing meaningful text and one is scientific-detail filtering (`2609.00495v1` / `S2.SS0.SSS0.Px1.p1`, containing four filtered equations). Equation/proof filtering takes precedence in the primary category; the structural flag independently detects absent projected prose. These are automated detections, not 114 individually human-verified defects.",
        'The manually inspected examples below were checked against cached DOM, parser output, and persisted text during the original audit; their automated absence checks are rerun here. Confirmed behavioral examples are the manually inspected ClawHub scanner-disagreement, gauge-theory dual-use-risk, and jailbreak-definition passages below: their projected prose is absent from the parser and persisted corpus. This does not confirm the other candidate passages. Zero executed check failures concerns retained text/citations and transport, not extraction completeness.']
    lines += ['', 'Manually inspected examples (limited to the examples listed below; not all automated candidates):', '']
    chosen = [('2604.00324v1','Chx2.p1'), ('2602.00937v3','S3.SS2.p4'),
              ('2606.01494v1','S1.SS0.SSS0.Px3.p1'), ('2603.00824v2','S12.SS0.SSSx1.p2'),
              ('2609.00498v1','Thmdefinition1.p1')]
    for aid, eid in chosen:
        paper = next(p for p in report['papers'] if p['arxiv_id'] == aid)
        candidate = next((c for c in paper['candidates_for_40_43'] if c['element_id'] == eid), None)
        if candidate:
            triage = candidate['triage']
            lines.append(f"- `{aid}` / `{eid}`: **{triage['category']}**. {cell(triage['projected_text'][:200])} Projected prose retained: {triage['projected_text_in_parser']}; automated structural candidate: {triage['automated_structural_omission_candidate']}.")
    false_positive = next((c for p in report['papers'] for c in p['candidates_for_40_43'] if c['triage']['category']=='false_positive_review_candidate'), None)
    if false_positive:
        lines.append(f"- False-positive example `{false_positive['element_id']}`: projection is fully present after harmless tag normalization; raw paragraph mismatch alone would overstate missing content.")
    lines += ['', f"Parsed sections without chunks: **{omission['parsed_sections_without_chunks']}**. Their exact section/subsection/anchor association is checked; a different subsection cannot satisfy coverage.", '']
    for paper in report['papers']:
        for sec in paper['omissions'].get('parsed_sections_without_chunks', []):
            lines.append(f"- `{paper['arxiv_id']}` / `{sec['anchor']}` / {cell(sec['section'])} > {cell(sec['subsection'])}: {sec['characters']} characters. {sec['reason']}. Excerpt: {cell(sec['text'][:130])}")
    lines += ['', '## 8. Tests and results', '']
    for run in report.get('automated_tests', {}).get('runs', []):
        lines += [f"- `{run['command']}` — {run['summary']}; exit {run['exit_code']}."]
    if not report.get('automated_tests'):
        lines.append('Pytest results not attached to this run.')
    lines += ['', 'Warnings: Python 3.14 dependency deprecations in Chroma (`asyncio.iscoroutinefunction`) and Google GenAI (`_UnionGenericAlias`). They do not indicate failed citation/storage checks. No warnings are suppressed and no dependency upgrade is attempted.', '',
        '## 9. Known limitations', '',
        'The inspected examples demonstrate nested-wrapper gaps; the remaining candidates need individual review. Source coverage also has and intentional equation/table/proof/back-matter exclusions. Short sections below 150 characters can still contain meaningful caveats. No visual layout evaluation, fresh-source check, paid Gemini call, full answer-generation handoff, held-out retrieval benchmark, process-kill test, or atomic rollback test was performed.',
        'Production citation metadata omits `high_value`, authors, and categories; those remain in Parquet but are not part of the current public search contract. The retrieval module has no Azure dependency or credential requirement; private `.env` settings are irrelevant to backend selection.', '',
        '## 10. Follow-up recommendations for #40 and #43', '',
        '**#40:** reproduce direct child `ltx_paragraph`, `ltx_subsubsection`, and theorem-wrapper omissions. Traverse substantive wrappers while retaining the correct heading and avoiding nested duplicates. Prioritize ClawHub scanner disagreements, gauge-theory dual-use risks, and jailbreak validity criteria. Add owner-reviewed real-source regression cases before regenerating the corpus.',
        '**#43:** record the source IDs/excerpts and risk, decide whether equations, scientific tables, and short caveats should be retained, and track remediation/revalidation. Keep acknowledgement/credit exclusions separate from substantive evidence loss. No comments were posted automatically.',
        'Issue #82 can submit this validation evidence with explicit findings; it must not be presented as proof of complete corpus extraction. Production changes require ingestion-owner review.', '',
        '### Executed check failures', '', *(report['failures'] or ['None. Completeness findings above remain open.'])]
    (directory/'html-ingestion-validation.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,default=config.PROJECT_ROOT/'docs')
    parser.add_argument('--cached-pdf', action='store_true', help='Validate fallback against one original cached PDF')
    parser.add_argument('--semantic-evidence', type=Path, help='JSON from separately executed offline MiniLM smoke worker')
    parser.add_argument('--test-results', type=Path, help='JSON recording separately executed pytest commands and results')
    args=parser.parse_args()
    result=validate()
    if args.cached_pdf:
        try:
            result['cached_pdf_fallback'] = validate_cached_pdf(load_metadata())
        except Exception as error:
            result['cached_pdf_fallback'] = {'status': 'FAIL', 'error': str(error)}
            result['failures'].append('Original cached PDF fallback: '+str(error))
        result['command'] += ' --cached-pdf'
    if args.semantic_evidence:
        evidence = json.loads(args.semantic_evidence.read_text(encoding='utf-8'))
        try:
            result['semantic_smoke'] = verify_semantic_evidence(evidence, result)
            result['embedding_relevance_tested'] = True
        except ValueError as error:
            result['semantic_smoke'] = {'status': 'REJECTED', 'error': str(error)}
            result['rejected_semantic_evidence'] = evidence
            result['failures'].append(str(error))
        result['command'] += ' --semantic-evidence ' + args.semantic_evidence.as_posix()
    if args.test_results:
        result['automated_tests'] = json.loads(args.test_results.read_text(encoding='utf-8-sig'))
        result['command'] += ' --test-results ' + args.test_results.as_posix()
    result['status'] = 'PASS' if not result['failures'] else 'FAIL'
    write_report(result,args.report_dir)
    print(json.dumps({'status':result['status'],'papers':len(result['papers']),
                      'chunks':result['persisted_chunks'],'failures':result['failures']},indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)

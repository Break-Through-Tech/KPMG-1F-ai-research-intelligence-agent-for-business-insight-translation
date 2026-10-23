"""Complement raw TeX with text from explicitly referenced bundled PDFs.

No OCR, TeX execution, downloads, inferred chart values, or paper-page claims.
Coverage records describe every recognized reference, including extraction gaps.
"""
import hashlib
from pathlib import PurePosixPath
import re

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .tex_assets import asset_members, literal_preamble
from .tex_lexical import structural
from .tex_source import _name, read_source, source_blocks, source_url

MAX_FIGURES = 128
MAX_PAGES = 32
MAX_TEXT = 1024 * 1024
GRAPHIC = re.compile(r'\\includegraphics\*?(?:\s*\[[^\]]*\])?\s*\{([^{}]*)\}')
EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.eps', '.ps', '.svg')


def extract_figure_text(data, aid, title=''):
    url = source_url(aid)
    blocks = source_blocks(data)  # Reachable, branch-filtered document content.
    files, manifest = read_source(data, with_manifest=True)
    roots = [n for n, t in files.items() if r'\begin{document}' in structural(t)[1]]
    if manifest:
        declared = [s['filename'] for s in manifest['sources'] if s.get('usage') == 'toplevel']
        if declared:
            roots = declared
    root = _name(roots[0])
    root_dir = PurePosixPath(root).parent
    names, _ = asset_members(data)
    # Only literal root-preamble graphicspath declarations are understood.
    preamble, preamble_macros = literal_preamble(files[root], with_macros=True)
    paths = []
    declarations = list(re.finditer(r'\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)*)\}', preamble))
    if declarations:
        paths = re.findall(r'\{([^{}]*)\}', declarations[-1][1])
    # A body mutation can affect a later reference in a different include block.
    # This literal-only reader must not reuse a frozen preamble path in that case.
    mutation = re.compile(r'\\(?:csname|catcode|futurelet|unless|inputencoding|usepackage|documentclass|directlua|scantokens|DeclareGraphicsRule|DeclareGraphicsExtensions|graphicspath|if[a-zA-Z]+|def|gdef|edef|xdef|let|newcommand|renewcommand|providecommand|DeclareRobustCommand|newenvironment|renewenvironment)(?![a-zA-Z])')
    uncertain = any(mutation.search(structural(text)[1]) or
                    preamble_macros.intersection(re.findall(r'\\([a-zA-Z]+)', structural(text)[1]))
                    for _, _, text in blocks)
    coverage = []
    for filename, first_line, text in blocks:
        code = structural(text)[1]
        matches = list(GRAPHIC.finditer(code))
        # Unknown argument syntax is reported instead of silently ignored.
        stripped = GRAPHIC.sub(lambda m: ' ' * len(m[0]), code)
        for m in re.finditer(r'\\includegraphics(?![a-zA-Z])', stripped):
            coverage.append(dict(source_file=filename, line_start=first_line + text[:m.start()].count('\n'),
                                 status='unsupported_syntax', reference=''))
        for match in matches:
            if len(coverage) >= MAX_FIGURES:
                raise ValueError('Figure reference limit exceeded')
            line = first_line + text[:match.start()].count('\n')
            entry = dict(source_file=filename, line_start=line,
                         line_end=first_line + text[:match.end()].count('\n'), reference=match[1])
            coverage.append(entry)
            if uncertain:
                entry['status'] = 'unsupported_source_semantics'
                continue
            try:
                reference = _name(match[1].strip())
                if any(c in reference for c in ('\\', '#', '$')) or not reference:
                    raise ValueError('Dynamic figure reference')
                bases = {root_dir, PurePosixPath(filename).parent}
                bases.update(root_dir / _name(v) for v in paths)
                candidates = set()
                for base in bases:
                    value = _name(str(base / reference))
                    candidates.update([value] if PurePosixPath(value).suffix else
                                      [value + suffix for suffix in EXTENSIONS])
                available = candidates.intersection(names)
                if len(available) != 1:
                    entry['status'] = 'missing_or_ambiguous'
                    continue
                entry['asset_file'] = available.pop()
                entry['status'] = 'pending' if entry['asset_file'].lower().endswith('.pdf') else 'needs_visual_extraction'
                # Options can crop, select pages, trim or clip. Whole-asset text
                # must never be presented as exactly what the paper displays.
                entry['scope'] = 'whole_bundled_asset_not_rendered_figure'
            except ValueError:
                entry['status'] = 'unsupported_reference'
    if len(coverage) > MAX_FIGURES:
        raise ValueError('Figure reference limit exceeded')
    selected = {e['asset_file'] for e in coverage if e['status'] == 'pending'}
    _, assets = asset_members(data, selected)
    chunks, extracted, total_text = [], {}, 0
    digest = hashlib.sha256(data).hexdigest()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=250)
    for entry in coverage:
        if entry['status'] != 'pending':
            continue
        name = entry['asset_file']
        if name in extracted:
            entry.update(extracted[name])
            continue
        asset = assets[name]
        asset_hash = hashlib.sha256(asset).hexdigest()
        outcome = dict(asset_sha256=asset_hash)
        asset_chunks = []
        try:
            with pymupdf.open(stream=asset, filetype='pdf') as doc:
                if doc.needs_pass or doc.page_count > MAX_PAGES:
                    raise ValueError('Encrypted or excessive-page figure PDF')
                empty = []
                for number, page in enumerate(doc, 1):
                    text = page.get_text('text', sort=False).strip()
                    total_text += len(text)
                    if total_text > MAX_TEXT:
                        raise ValueError('Figure text limit exceeded')
                    if not text:
                        empty.append(number)
                    for piece in splitter.split_text(text):
                        asset_chunks.append(dict(chunk_id=f'{aid}_figure{len(chunks)+len(asset_chunks):04d}',
                            arxiv_id=aid, source='tex_figure', source_url=url, page_number=None,
                            source_sha256=digest, asset_file=name, asset_sha256=asset_hash,
                            asset_page_number=number, extraction_method='pdf_text',
                            evidence_scope=entry['scope'], section='Figure asset text', text=piece,
                            text_with_context=f'{title} | bundled asset {name}, asset page {number} '
                                              f'(not a paper page; may include cropped-out content)\n\n{piece}'))
                outcome.update(status='text_extracted' if asset_chunks else 'needs_visual_extraction',
                               asset_pages=doc.page_count, pages_without_text=empty)
        except (RuntimeError, ValueError) as error:
            asset_chunks = []  # No partial asset evidence on failure.
            outcome.update(status='extraction_failed', reason=str(error))
        chunks.extend(asset_chunks)
        extracted[name] = outcome
        entry.update(outcome)
    return dict(chunks=chunks, coverage=coverage)

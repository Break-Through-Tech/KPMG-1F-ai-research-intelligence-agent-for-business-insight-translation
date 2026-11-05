"""Opt-in supplementary HTML evidence; never changes baseline ingestion or indexes.

Table rows are explicitly derived serializations, not verbatim paper prose.
Unsupported layouts are reported instead of guessing cell relationships.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from src.data_ingestion.html_parser import parse_html_sections

VERSION = 'html-evidence-v2.1-stage-a'
EMPTY_CELL = '[empty in source]'
NUMERIC = re.compile(r'^[\d\s.,%+\-\u2212\u00b1]+$')
EXCLUDED = {'ltx_appendix', 'ltx_bibliography', 'ltx_equation',
            'ltx_equationgroup', 'ltx_proof'}


def _excluded(node, excluded=EXCLUDED):
    return any(p.name in {'nav', 'script', 'style'} or excluded.intersection(p.get('class', []))
               for p in [node, *node.parents] if getattr(p, 'attrs', None) is not None)


def _text(node, *, heading=False):
    node = deepcopy(node)
    for t in node.select('script, style' + (', .ltx_tag' if heading else '')):
        t.decompose()
    for math in node.find_all('math'):
        alt = math.get('alttext')
        if not isinstance(alt, str) or not alt.strip():
            raise ValueError('math_alttext_missing')
        math.replace_with(alt)
    return ' '.join(node.get_text(' ', strip=True).split())


def _heading(section):
    if section is None:
        return ''
    h = section.find(re.compile(r'^h[1-6]$'), class_='ltx_title', recursive=False)
    return _text(h, heading=True) if h else ''


def _scope(node):
    sections = [p for p in node.parents if p.name == 'section']
    chapter = next((p for p in sections if 'ltx_chapter' in p.get('class', [])), None)
    section = next((p for p in sections if 'ltx_section' in p.get('class', [])), None)
    sub = next((p for p in sections if 'ltx_subsection' in p.get('class', [])), None)
    top, lower = (chapter, section) if chapter else (section, sub)
    return {'section': _heading(top), 'subsection': _heading(lower),
            'section_id': top.get('id', '') if top else '',
            'subsection_id': lower.get('id', '') if lower else ''}


def _paragraph_tree(html):
    cleaned = BeautifulSoup(html, 'html.parser')
    for fig in cleaned.select('figure'):
        if fig.parent is None:
            continue
        cap = fig.find('figcaption', recursive=False)
        fig.replace_with(cap) if cap else fig.decompose()
    for t in cleaned.select('.ltx_bibliography, .ltx_appendix, .ltx_equation, '
                            '.ltx_equationgroup, .ltx_proof, .ltx_tag, nav, script, style'):
        t.decompose()
    return cleaned


def _paragraph_text(block):
    elements = block.find_all(['div', 'p', 'figcaption'], class_=['ltx_para', 'ltx_caption'])
    selected = {id(e) for e in elements}
    return ' '.join(_text(e) for e in elements
                    if not any(id(p) in selected for p in e.parents)).strip()


def _row_text(title, caption, headers, row, notes, group=''):
    notes = list(notes)
    pairs = '; '.join(f'{h}: {v or EMPTY_CELL}' for h, v in zip(headers, row))
    text = ('Derived source table row (HTML cell serialization, not verbatim prose).\n'
            + title + '\n' + caption + '\n'
            + (f'Row group: {group}; ' if group else '') + pairs)
    if notes:
        text += '\nSource notes: ' + ' '.join(notes)
    return text


def _span(cell, name):
    value = cell.get(name, '1')
    if not isinstance(value, str) or not value.isdigit() or int(value) < 1:
        raise ValueError('merged_or_invalid_cell_span')
    return int(value)


def _expand_grid(trs):
    """Resolve rowspan/colspan into one source cell per row/column slot."""
    grid, pending = [], {}
    for tr in trs:
        row, cells, column = [], iter(tr.find_all(['th', 'td'], recursive=False)), 0
        cell = next(cells, None)
        while cell is not None or column in pending:
            if column in pending:
                source, left = pending.pop(column)
                row.append(source)
                if left > 1:
                    pending[column] = (source, left - 1)
                column += 1
                continue
            rows, columns = _span(cell, 'rowspan'), _span(cell, 'colspan')
            for _ in range(columns):
                if column in pending:
                    raise ValueError('overlapping_cell_span')
                row.append(cell)
                if rows > 1:
                    pending[column] = (cell, rows - 1)
                column += 1
            cell = next(cells, None)
        grid.append(row)
    if pending:
        raise ValueError('merged_or_invalid_cell_span')
    return grid


def _is_header_row(row, tr):
    return bool(row) and (tr.find_parent('thead') is not None or all(
        c.name == 'th' and (c.get('scope') == 'col' or 'ltx_th_column' in c.get('class', []))
        for c in row))


def _combined_headers(rows):
    headers, sources = [], []
    for column in range(len(rows[0])):
        cells = []
        for row in rows:
            if not any(row[column] is c for c in cells):
                cells.append(row[column])
        parts = list(dict.fromkeys(t for t in (_text(c) for c in cells) if t))
        headers.append(' / '.join(parts))
        sources.append(cells)
    return headers, sources


def _source_notes(table, figure, soup, ids):
    notes = {}
    if figure:
        for note in figure.select('.ltx_note_content, [role="doc-footnote"]'):
            anchor = note.get('id', '')
            if not anchor or ids[anchor] != 1:
                raise ValueError('note_anchor_missing_or_ambiguous')
            notes[anchor] = _text(note)
    for link in table.select('a.ltx_note_mark, a[role="doc-noteref"]'):
        href = link.get('href', '')
        target = soup.find(id=href[1:]) if href.startswith('#') and ids[href[1:]] == 1 else None
        if target is None:
            raise ValueError('unresolved_footnote')
        notes[href[1:]] = _text(target)
    return [{'anchor': key, 'text': value} for key, value in notes.items()]


def extract_html_evidence(html, arxiv_id, title, *, include_appendix=True):
    """Return supplementary passages and a coverage/rejection manifest only.

    Accepts tables whose merged cells and stacked headers resolve to one
    unambiguous header per value, plus direct paragraph sections missed by the
    normal-paper baseline traversal. Empty cells are reported as empty, never
    filled. Appendix tables are enabled in this isolated candidate; appendix
    paragraph recovery and the chapter-style paragraph branch remain out of scope.
    """
    if (not isinstance(html, str) or not html.strip() or
            not isinstance(arxiv_id, str) or not re.fullmatch(r'\d{4}\.\d{4,5}v[1-9]\d*', arxiv_id)
            or not isinstance(title, str) or not title.strip()):
        raise ValueError('Provide HTML, a versioned modern arXiv ID and a nonempty title.')
    soup = BeautifulSoup(html, 'html.parser')
    ids = Counter(n.get('id') for n in soup.find_all(id=True))
    source_hash = sha256(html.encode('utf-8')).hexdigest()
    passages, tables, paragraphs = [], [], []
    non_data_layouts = 0

    def base(anchor, kind, number, node, text):
        if not anchor or ids[anchor] != 1:
            raise ValueError('missing_or_ambiguous_anchor')
        scope = _scope(node)
        url = f'https://arxiv.org/html/{arxiv_id}#{quote(anchor, safe="._:-")}'
        return {'chunk_id': f'{arxiv_id}_{kind}_{sha256(anchor.encode()).hexdigest()[:16]}_{number}',
                'text': text, 'arxiv_id': arxiv_id, 'title': title, 'source': 'html',
                'pdf_url': f'https://arxiv.org/pdf/{arxiv_id}', 'html_url': url,
                'source_url': url, 'page_number': None, 'source_sha256': source_hash,
                'source_anchor': anchor, 'extractor_version': VERSION, **scope,
                'appendix_id': next((p.get('id', '') for p in [node, *node.parents]
                    if 'ltx_appendix' in p.get('class', [])), ''),
                'document_region': 'appendix' if any('ltx_appendix' in p.get('class', [])
                    for p in [node, *node.parents]) else 'main'}

    for table in soup.find_all('table'):
        if any({'ltx_equation', 'ltx_equationgroup', 'ltx_eqn_table'}.intersection(p.get('class', []))
               for p in [table, *table.parents] if getattr(p, 'attrs', None) is not None):
            non_data_layouts += 1
            continue
        figure = table.find_parent('figure')
        anchor = (figure.get('id') if figure else None) or table.get('id', '')
        audit = {'anchor': anchor, 'status': 'rejected', 'reason': '', 'rows_emitted': 0,
                 'document_region': 'appendix' if any('ltx_appendix' in p.get('class', [])
                    for p in [table, *table.parents]) else 'main'}
        tables.append(audit)
        try:
            if _excluded(table, EXCLUDED - {'ltx_appendix'} if include_appendix else EXCLUDED):
                raise ValueError('excluded_scope')
            if figure and figure.find('figure'):
                raise ValueError('nested_figure')
            if table.find_parent('table') or table.find('table'):
                raise ValueError('nested_table')
            if table.find('img') or table.find('svg'):
                raise ValueError('image_cell')
            if figure and len(figure.find_all('table')) != 1:
                raise ValueError('multiple_tables_share_figure')
            if table.find('tfoot'):
                raise ValueError('footer_rows')
            for cell in table.find_all(['th', 'td']):
                if cell.select('.ltx_note_outer, .ltx_note_content, [role="doc-footnote"]'):
                    raise ValueError('inline_note_content')
                if any(part.find_parent('math') is None and re.search(r'[\d+\-\u2212]', part.get_text())
                       for part in cell.find_all(['sup', 'sub'])):
                    raise ValueError('ambiguous_super_subscript')
            caption_node = figure.find('figcaption', recursive=False) if figure else table.find('caption', recursive=False)
            if caption_node is None or not (caption := _text(caption_node)):
                raise ValueError('caption_missing')
            outer = figure.find_parent('figure') if figure else None
            if outer and (outer_caption := outer.find('figcaption', recursive=False)):
                caption = _text(outer_caption) + ' ' + caption
            trs = table.find_all('tr')
            if len(trs) < 2:
                raise ValueError('no_data_rows')
            grid = _expand_grid(trs)
            width = len(grid[0])
            if not width or any(len(row) != width for row in grid):
                raise ValueError('row_width_mismatch')
            # A top row of column headers, then any further rows marked as column headers.
            # Preserve the prior strict rule. A blank corner may be row-marked
            # by LaTeXML in a grouped header; accept only with explicit column
            # markup, a merged top header and an explicit second header row.
            strict_top = all(c.name == 'th' and c.get('scope') != 'row' and not (
                'ltx_th_row' in c.get('class', []) and 'ltx_th_column' not in c.get('class', []))
                for c in grid[0])
            grouped_top = (not _text(grid[0][0]) and len(grid) > 1
                and all(c.name == 'th' and c.get('scope') != 'row' for c in grid[0])
                and all('ltx_th_column' in c.get('class', []) for c in grid[0] if _text(c))
                and any(_span(c, 'colspan') > 1 for c in grid[0])
                and _is_header_row(grid[1], trs[1]))
            header_count = int(strict_top or grouped_top)
            while header_count and header_count < len(grid) and _is_header_row(grid[header_count], trs[header_count]):
                header_count += 1
            first_row_assumed = False
            if not header_count:
                # Layouts that style the top row without marking it as a header.
                first = [_text(c) for c in grid[0]]
                if (width < 2 or len({id(c) for c in grid[0]}) != width
                        or any(NUMERIC.match(t) for t in first if t)):
                    raise ValueError('explicit_column_headers_missing')
                header_count, first_row_assumed = 1, True
            if header_count == len(grid):
                raise ValueError('no_data_rows')
            if len({id(c) for c in grid[0]}) == 1:
                raise ValueError('explicit_column_headers_missing')
            header_ids = {id(c) for row in grid[:header_count] for c in row}
            if any(id(c) in header_ids for row in grid[header_count:] for c in row):
                raise ValueError('header_span_into_data')
            headers, header_sources = _combined_headers(grid[:header_count])
            if any(not h for h in headers) or len(set(headers)) != len(headers):
                raise ValueError('empty_or_duplicate_header')
            body, group, skipped_blank = [], '', 0
            for number, row in enumerate(grid[header_count:]):
                distinct = {id(c) for c in row}
                if len(distinct) == 1 and width > 1:
                    if not (group := _text(row[0])):
                        skipped_blank += 1
                    continue
                if len(distinct) != width:
                    raise ValueError('body_partial_colspan')
                if any('ltx_th_column' in c.get('class', []) or c.get('scope') == 'col' for c in row):
                    raise ValueError('multiple_header_rows')
                if all(c.name == 'th' for c in row):
                    raise ValueError('multiple_header_rows')
                texts = [_text(c) for c in row]
                if not any(texts):
                    skipped_blank += 1
                    continue
                if not texts[0]:
                    raise ValueError('empty_or_duplicate_row_label')
                previous = grid[header_count + number - 1] if number else [None] * width
                body.append((row, texts, group, previous))
            if not body:
                raise ValueError('no_data_rows')
            whole = [(group, tuple(texts)) for _, texts, group, _ in body]
            if len(set(whole)) != len(whole):
                raise ValueError('duplicate_row')
            # Retain source-local notes and explicit footnote targets; never fetch links.
            notes = _source_notes(table, figure, soup, ids)
            guessed_headers = 'ltx_guessed_headers' in table.get('class', [])
            provenance = ('first_row_assumed' if first_row_assumed
                          else 'latexml_guessed' if guessed_headers else 'html_th_markup')
            result = []
            for row_number, (source_cells, row, group, previous) in enumerate(body, 1):
                text = _row_text(title, caption, headers, row, [n['text'] for n in notes], group)
                passage = base(anchor, 'table', row_number, table, text)
                passage.update(representation='linearized_table', table_id=anchor,
                    table_row=row_number, row_label=row[0], caption=caption,
                    header_provenance=provenance,
                    header_review='pending_human_verification',
                    html_version_verified=False,
                    version_binding='caller_supplied_frozen_metadata_and_local_source_hash',
                    table_headers=[{'column': i, 'text': h, 'source_id': cs[0].get('id'),
                                    **({'source_ids': [c.get('id') for c in cs]} if len(cs) > 1 else {})}
                                   for i, (h, cs) in enumerate(zip(headers, header_sources))],
                    table_cells=[{'row': row_number, 'column': i, 'text': value, 'source_id': c.get('id'),
                                  **({'merged_from_previous_row': True} if c is before else {})}
                                 for i, (value, c, before) in enumerate(zip(row, source_cells, previous))],
                    source_notes=deepcopy(notes))
                if group:
                    passage['row_group'] = group
                if header_count > 1:
                    passage['header_rows'] = header_count
                result.append(passage)
            passages.extend(result)
            audit.update(status='accepted', rows_emitted=len(result), columns=len(headers),
                         header_provenance=provenance, header_rows=header_count,
                         blank_rows_skipped=skipped_blank)
        except ValueError as error:
            audit['reason'] = str(error)
            if any(x in str(error) for x in ('header', 'span', 'ambiguous', 'row_width', 'body_partial')):
                audit['status'] = 'ambiguous'

    if not soup.select('section.ltx_chapter'):
        # Use identical baseline preprocessing before examining the missed blocks.
        cleaned = _paragraph_tree(html)
        existing = ' '.join(' '.join(s['text'].split()) for s in parse_html_sections(html))
        for sec in cleaned.select('section.ltx_section'):
            for block in sec.find_all('section', class_='ltx_paragraph', recursive=False):
                anchor = block.get('id', '')
                audit = {'anchor': anchor, 'status': 'rejected', 'reason': ''}
                paragraphs.append(audit)
                try:
                    original_block = soup.find(id=anchor)
                    if original_block and original_block.select('.ltx_equation, .ltx_equationgroup'):
                        raise ValueError('display_equations_require_separate_recovery')
                    if block.find('table'):
                        raise ValueError('contains_table_layout')
                    text = _paragraph_text(block)
                    if not text:
                        raise ValueError('empty_paragraph')
                    passage = base(anchor, 'paragraph', 0, block, text)
                    passage.update(representation='recovered_paragraph', paragraph_id=anchor,
                                   paragraph_heading=_heading(block),
                                   same_text_in_baseline=text in existing,
                                   html_version_verified=False,
                                   version_binding='caller_supplied_frozen_metadata_and_local_source_hash',
                                   text_normalization='html_text_whitespace_and_math_alttext')
                    passages.append(passage)
                    audit['status'] = 'accepted'
                except ValueError as error:
                    audit['reason'] = str(error)

    return {'passages': passages, 'coverage': {'extractor_version': VERSION,
        'arxiv_id': arxiv_id, 'source_sha256': source_hash, 'tables': tables,
        'non_data_layout_tables': non_data_layouts,
        'paragraphs': paragraphs, 'chapter_paragraph_recovery': 'out_of_scope' if soup.select('section.ltx_chapter') else 'enabled',
        'appendix_recovery': 'enabled_tables_only' if include_appendix else 'out_of_scope'}}


def validate_source_bindings(passages, html, arxiv_id, title, *, include_appendix=True):
    """Require exact agreement with deterministic source re-extraction.

    Re-extraction reapplies layout/scope rejection and binds every source field.
    This checks extraction consistency, not independent semantic correctness or
    remote certification of the supplied paper version.
    """
    if not isinstance(passages, list):
        raise ValueError('Supplementary evidence must be a list.')
    expected = {p['chunk_id']: p for p in extract_html_evidence(html, arxiv_id, title, include_appendix=include_appendix)['passages']}
    seen = set()
    for passage in passages:
        if not isinstance(passage, dict):
            raise ValueError('Supplementary evidence must contain objects.')
        core = {k: v for k, v in passage.items() if k not in
                {'text_tokens', 'exceeds_embedding_limit', 'normalized_text_in_single_frozen_chunk'}}
        ident = core.get('chunk_id')
        if not isinstance(ident, str) or ident in seen or expected.get(ident) != core:
            raise ValueError('Supplementary passage does not match source re-extraction.')
        seen.add(ident)
    return True

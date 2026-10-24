"""Bounded arXiv HTML evidence with source TeX, without executing paper code."""
from hashlib import sha256
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.research_contracts import validate_evidence


MAX_HTML_BYTES = 5_000_000


def fetch_arxiv_html(aid):
    # Only a validated, version-pinned arXiv ID can select the remote document.
    if not re.fullmatch(r'\d{4}\.\d{4,5}v\d+', aid):
        raise ValueError('HTML evidence requires an explicit arXiv version.')
    request = Request(f'https://arxiv.org/html/{aid}',
                      headers={'User-Agent': 'ResearchDesk-local-preview/1.0'})
    with urlopen(request, timeout=15) as response:
        if response.headers.get_content_type() != 'text/html':
            raise ValueError('arXiv did not return HTML.')
        raw = response.read(MAX_HTML_BYTES + 1)
    if len(raw) > MAX_HTML_BYTES:
        raise ValueError('arXiv HTML exceeds the 5 MB preview limit.')
    return raw


def parse_paper_html(raw, aid, title):
    from bs4 import BeautifulSoup
    from src.paper_reader import retain_reader
    if len(raw) > MAX_HTML_BYTES:
        raise ValueError('arXiv HTML exceeds the 5 MB preview limit.')
    source_hash = sha256(raw).hexdigest()
    soup = BeautifulSoup(raw, 'html.parser')
    article = soup.select_one('article.ltx_document')
    if article is None:
        raise ValueError('No arXiv article found in HTML.')
    for node in article.select('script, style, nav, .ltx_bibliography'):
        node.decompose()
    # Snapshot source structure before the canonical TeX conversion below.
    # Match by selected-block position, retaining the existing quote text exactly.
    selector = '.ltx_abstract, .ltx_para, .ltx_equation, .ltx_equationgroup, figure, table, ul, ol, dl'
    original_blocks = article.select(selector)
    selected_original = {id(node) for node in original_blocks}
    readers = [retain_reader([node], source_hash) for node in original_blocks
               if not any(id(parent) in selected_original for parent in node.parents)]
    for math in article.find_all('math'):
        annotation = math.find('annotation', attrs={'encoding': 'application/x-tex'})
        tex = math.get('alttext') or (annotation.get_text() if annotation else '')
        if not tex:
            # Keep readable text where the source supplies no TeX; never infer it.
            math.replace_with(math.get_text(' ', strip=True))
            continue
        left, right = (r'\[', r'\]') if math.get('display') == 'block' else (r'\(', r'\)')
        math.replace_with(f' {left}{tex}{right} ')
    blocks = article.select(selector)
    selected = {id(node) for node in blocks}
    groups = {}
    reader_index = 0
    reader_groups = {}
    for node in blocks:
        if any(id(parent) in selected for parent in node.parents):
            continue
        reader = readers[reader_index]
        reader_index += 1
        section = node.find_parent('section')
        anchor = section.get('id', '') if section else node.get('id', '')
        heading = section.find(re.compile(r'^h[1-6]$')) if section else None
        name = heading.get_text(' ', strip=True) if heading else 'Section heading not supplied'
        text = re.sub(r'\s+', ' ', node.get_text(' ', strip=True)).strip()
        if text:
            groups.setdefault((anchor, name), []).append(text)
            reader_groups.setdefault((anchor, name), []).append(reader)
    passages = []
    for (anchor, name), texts in groups.items():
        url = f'https://arxiv.org/html/{aid}' + (f'#{quote(anchor, safe=".")}' if anchor else '')
        passages.append({'chunk_id': f'{aid}-html-{len(passages) + 1}',
                         'text': ' '.join(texts), 'arxiv_id': aid, 'title': title,
                         'pdf_url': f'https://arxiv.org/pdf/{aid}', 'source': 'html',
                         'html_url': url, 'source_url': url, 'page_number': None,
                         'section': name,
                         'reader': {
                             'version': 1, 'provenance': 'source-html',
                             'source_sha256': source_hash,
                             # A rejected block must not disappear from an otherwise
                             # preferred structured view of this whole passage.
                             'nodes': ([node for reader in reader_groups[(anchor, name)] for node in reader['nodes']]
                                       if all(reader['nodes'] for reader in reader_groups[(anchor, name)]) else []),
                             'limitations': sorted({item for reader in reader_groups[(anchor, name)] for item in reader['limitations']}),
                         }})
    if not passages or len(passages) > 80 or sum(len(p['text']) for p in passages) > 120_000:
        raise ValueError('HTML must fit the 80-section / 120k-character preview limit.')
    validate_evidence(passages)
    return passages, {'format': 'arxiv-html-with-tex', 'url': f'https://arxiv.org/html/{aid}',
                      'sha256': source_hash}

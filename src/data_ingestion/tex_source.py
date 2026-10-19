"""Bounded, non-executing arXiv TeX ingestion. This is not a TeX interpreter."""
import gzip
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import tarfile
import tempfile
import time

import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config as cfg

MAX_ARCHIVE = 16 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024
MAX_MEMBERS = 2048
MAX_FILES = 128
ID = re.compile(r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?\Z")
INCLUDE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")


def source_url(aid):
    if not isinstance(aid, str) or not ID.fullmatch(aid):
        raise ValueError("Invalid arXiv ID")
    return f"https://arxiv.org/src/{aid}"


def cache_path(aid):
    source_url(aid)
    return cfg.TEX_DIR / (aid.replace('/', '_') + '.source')


def _name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or '\x00' in name:
        raise ValueError("Unsafe TeX archive path")
    return str(path)


def read_source(data):
    """Read tar[.gz], gzip-single-TeX, or single TeX; never extract to disk."""
    if not data or len(data) > MAX_ARCHIVE:
        raise ValueError("Empty or oversized source archive")
    if data.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            data = stream.read(MAX_EXPANDED + 1)
        if len(data) > MAX_EXPANDED:
            raise ValueError("Expanded source exceeds limit")
    files = {}
    total = 0
    try:
        archive = tarfile.open(fileobj=io.BytesIO(data), mode='r:')
    except tarfile.ReadError:
        files['main.tex'] = data
    else:
        with archive:
            for index, member in enumerate(archive):
                if index >= MAX_MEMBERS:
                    raise ValueError("Too many archive members")
                name = _name(member.name)
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError("Archive links and special files are unsupported")
                total += member.size
                if total > MAX_EXPANDED:
                    raise ValueError("Expanded source exceeds limit")
                if not name.endswith('.tex'):
                    continue
                if name in files or len(files) >= MAX_FILES:
                    raise ValueError("Duplicate or excessive TeX files")
                files[name] = archive.extractfile(member).read()
    decoded = {name: value.decode('utf-8-sig') for name, value in files.items()}
    if not decoded:
        raise ValueError("Source contains no TeX files")
    return decoded


def _uncomment(text):
    # A percent preceded by an odd run of backslashes is escaped.
    return re.sub(r"(?<!\\)((?:\\\\)*)%[^\n]*", r"\1", text)


def source_blocks(data):
    files = read_source(data)
    clean = {name: _uncomment(text) for name, text in files.items()}
    roots = [name for name, text in clean.items() if r'\begin{document}' in text]
    if len(roots) != 1:
        raise ValueError("Source needs exactly one document root")
    root_dir = PurePosixPath(roots[0]).parent
    blocks = []
    visits = 0
    expanded = 0

    def visit(name, stack, root=False):
        nonlocal visits, expanded
        visits += 1
        if visits > MAX_FILES or len(stack) >= 32 or name in stack:
            raise ValueError("Cyclic or excessive TeX includes")
        if name not in clean:
            raise ValueError("Missing TeX include")
        text = clean[name]
        if re.search(r'\\includeonly(?![a-zA-Z])', text):
            raise ValueError('Selective TeX includes require HTML/PDF fallback')
        start, end = 0, len(text)
        if root:
            start = text.index(r'\begin{document}') + len(r'\begin{document}')
            end = text.find(r'\end{document}', start)
            if end < 0:
                raise ValueError("Unterminated TeX document")
        if re.search(r'\\(?:(?:if[a-zA-Z]*|else|fi|verb|includeonly)(?![a-zA-Z])|begin\s*\{(?:verbatim|comment)\})', text[start:end]):
            raise ValueError("Conditional/verbatim TeX requires HTML/PDF fallback")
        # Unsupported input syntax must not silently publish a partial paper.
        body = text[start:end]
        if re.search(r'\\(?:input|include)(?![a-zA-Z])', INCLUDE.sub('', body)):
            raise ValueError("Unsupported TeX include syntax")
        cursor = start

        def emit(stop):
            nonlocal expanded
            value = text[cursor:stop]
            expanded += len(value)
            if expanded > MAX_EXPANDED:
                raise ValueError("Expanded includes exceed limit")
            if value.strip():
                blocks.append((name, text.count('\n', 0, cursor) + 1, value))

        for match in INCLUDE.finditer(text, start, end):
            emit(match.start())
            reference = _name(match[1].strip())
            if not reference.endswith('.tex'):
                reference += '.tex'
            candidates = {_name(str(base / reference))
                          for base in (root_dir, PurePosixPath(name).parent)}
            available = candidates.intersection(clean)
            if len(available) != 1:
                raise ValueError('Missing or ambiguous TeX include')
            visit(available.pop(), (*stack, name))
            cursor = match.end()
        emit(end)

    visit(roots[0], (), True)
    return blocks


def chunk_source(data, aid, title=''):
    url = source_url(aid)
    digest = hashlib.sha256(data).hexdigest()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=250,
        separators=['\n\n', '\n', ' ', ''], add_start_index=True)
    chunks = []
    for name, first_line, text in source_blocks(data):
        for document in splitter.create_documents([text]):
            offset = document.metadata['start_index']
            start = first_line + text.count('\n', 0, offset)
            end = start + document.page_content.count('\n')
            chunks.append(dict(chunk_id=f'{aid}_c{len(chunks):04d}', arxiv_id=aid,
                source='tex', source_url=url, page_number=None,
                source_file=name, line_start=start, line_end=end, source_sha256=digest,
                section='', text=document.page_content,
                text_with_context=f'{title} | {name}:{start}-{end}\n\n{document.page_content}'))
    if not chunks:
        raise ValueError("No usable TeX document body")
    return chunks


def download_sources(metadata, delay=3.0):
    """Optional acquisition; failures leave existing caches and fallback intact."""
    cfg.TEX_DIR.mkdir(parents=True, exist_ok=True)
    for row in metadata:
        aid = row['arxiv_id']
        path = cache_path(aid)
        if path.exists():
            continue
        try:
            with requests.get(source_url(aid), headers={'User-Agent': cfg.USER_AGENT},
                              timeout=60, stream=True) as response:
                if response.status_code == 429:
                    print('[Throttled] Source download stopped; rerun later.')
                    break
                response.raise_for_status()
                data = bytearray()
                for block in response.iter_content(65536):
                    data.extend(block)
                    if len(data) > MAX_ARCHIVE:
                        raise ValueError('Source download exceeds limit')
            source_blocks(bytes(data))
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
                temporary = Path(file.name)
                try:
                    file.write(data)
                    file.close()
                    temporary.replace(path)
                finally:
                    temporary.unlink(missing_ok=True)
        except (OSError, ValueError, requests.RequestException, tarfile.TarError, EOFError) as error:
            print(f'[TeX unavailable] {aid}: {error}')
        time.sleep(delay)

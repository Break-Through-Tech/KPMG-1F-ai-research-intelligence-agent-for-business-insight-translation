"""Bounded, non-executing arXiv TeX ingestion. This is not a TeX interpreter."""
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import tempfile
import time
import zlib

import requests

from . import config as cfg
from .tex_chunking import split_tex
from .tex_lexical import structural, constant_branches, PRIMITIVES

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_TEX = 32 * 1024 * 1024
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


def read_source(data, *, with_manifest=False):
    """Read tar[.gz], gzip-single-TeX, or single TeX; never extract to disk."""
    if not data or len(data) > MAX_ARCHIVE:
        raise ValueError("Empty or oversized source archive")
    if data.startswith(b'\x1f\x8b'):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                data = stream.read(MAX_EXPANDED + 1)
        except zlib.error as error:
            raise ValueError('Corrupt gzip source') from error
        if len(data) > MAX_EXPANDED:
            raise ValueError("Expanded source exceeds limit")
    files = {}
    manifest = None
    tex_bytes = 0
    total = 0
    try:
        archive = tarfile.open(fileobj=io.BytesIO(data), mode='r:')
    except tarfile.ReadError:
        if len(data) > MAX_TEX:
            raise ValueError('TeX text exceeds limit')
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
                if name == '00README.json':
                    if manifest is not None or member.size > 1024 * 1024:
                        raise ValueError('Duplicate or oversized source manifest')
                    manifest = json.loads(archive.extractfile(member).read())
                    if not isinstance(manifest, dict):
                        raise ValueError('Invalid source manifest')
                    continue
                if not name.endswith('.tex'):
                    continue
                tex_bytes += member.size
                if tex_bytes > MAX_TEX:
                    raise ValueError('TeX text exceeds limit')
                if name in files or len(files) >= MAX_FILES:
                    raise ValueError("Duplicate or excessive TeX files")
                files[name] = archive.extractfile(member).read()
    decoded = {name: value.decode('utf-8-sig') for name, value in files.items()}
    if not decoded:
        raise ValueError("Source contains no TeX files")
    return (decoded, manifest) if with_manifest else decoded


def _uncomment(text):
    return structural(text)[0]


def source_blocks(data):
    files, manifest = read_source(data, with_manifest=True)
    # Discover custom conditionals without evaluating macro definitions. Branch
    # filtering happens on document bodies, not on preamble macro declarations.
    scanned = {name: structural(text) for name, text in files.items()}
    custom = set(re.findall(r'\\newif\s*\\(if[a-zA-Z]+)',
                            '\n'.join(item[1] for item in scanned.values())))
    clean = {name: item[0] for name, item in scanned.items()}
    syntax = {name: item[1] for name, item in scanned.items()}
    roots = [name for name, text in syntax.items() if r'\begin{document}' in text]
    if manifest is not None:
        if not isinstance(manifest, dict) or not isinstance(manifest.get('sources'), list):
            raise ValueError('Invalid source manifest')
        declared = []
        for entry in manifest['sources']:
            if not isinstance(entry, dict):
                raise ValueError('Invalid source manifest entry')
            if entry.get('usage') == 'toplevel':
                if not isinstance(entry.get('filename'), str):
                    raise ValueError('Invalid declared document root')
                declared.append(_name(entry['filename']))
        if declared:
            if len(declared) != 1 or declared[0] not in roots:
                raise ValueError('Missing or ambiguous declared document root')
            roots = declared
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
        code = syntax[name]
        if re.search(r'\\includeonly(?![a-zA-Z])', code):
            raise ValueError('Selective TeX includes require HTML/PDF fallback')
        start, end = 0, len(text)
        if root:
            start = code.index(r'\begin{document}') + len(r'\begin{document}')
            end = code.find(r'\end{document}', start)
            if end < 0:
                raise ValueError("Unterminated TeX document")
        filtered = constant_branches(text[start:end], custom)
        # Prefix padding keeps all original file/line offsets stable.
        text = text[:start] + filtered + text[end:]
        code = code[:start] + structural(filtered)[1] + code[end:]
        commands = set(re.findall(r'\\([a-zA-Z]+)|\\.', code[start:end]))
        if commands.intersection(PRIMITIVES | custom | {'else', 'or', 'fi'}):
            raise ValueError("Unresolved conditional TeX requires HTML/PDF fallback")
        # Raw conditional macros can be retained, but expanding an include
        # inside their arguments would concatenate mutually exclusive branches.
        for macro in re.finditer(r'\\if[a-zA-Z]+', code[start:end]):
            position = start + macro.end()
            while position < end:
                while position < end and code[position].isspace():
                    position += 1
                if position == end or code[position] != '{':
                    break
                depth, stop = 1, position + 1
                while stop < end and depth:
                    depth += (code[stop] == '{') - (code[stop] == '}')
                    stop += 1
                if depth or re.search(r'\\(?:input|include)(?![a-zA-Z])', code[position:stop]):
                    raise ValueError('Conditional macro includes require HTML/PDF fallback')
                position = stop
        # Unsupported input syntax must not silently publish a partial paper.
        body = code[start:end]
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

        for match in INCLUDE.finditer(code, start, end):
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
    chunks = []
    for name, first_line, text in source_blocks(data):
        for piece in split_tex(text):
            offset = piece['start_index']
            start = first_line + text.count('\n', 0, offset)
            end = start + piece['text'].count('\n')
            chunks.append(dict(chunk_id=f'{aid}_c{len(chunks):04d}', arxiv_id=aid,
                source='tex', source_url=url, page_number=None,
                source_file=name, line_start=start, line_end=end, source_sha256=digest,
                section='', text=piece['text'], oversized_math=piece['oversized_math'],
                text_with_context=f'{title} | {name}:{start}-{end}\n\n{piece['text']}'))
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

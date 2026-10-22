"""Bounded archive assets; no filesystem extraction, compilation or network."""
import gzip
import io
import re
import tarfile

from .tex_lexical import PRIMITIVES, blank, constant_branches, structural
from .tex_state import DEFINITIONS, TARGET, group_end
from .tex_source import MAX_EXPANDED, _name, read_source

MAX_ASSET = 16 * 1024 * 1024
MAX_ASSET_TOTAL = 32 * 1024 * 1024


def asset_members(data, selected=()):
    """Validate the complete archive first; return names and selected bytes.

    A second pass reuses the validated bounded expansion. Unselected binary
    assets are never decoded. Duplicate asset paths are rejected, not guessed.
    """
    read_source(data)
    if data.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            data = stream.read(MAX_EXPANDED + 1)
    names, payloads, total = set(), {}, 0
    try:
        archive = tarfile.open(fileobj=io.BytesIO(data), mode='r:')
    except tarfile.ReadError:
        return names, payloads
    with archive:
        for member in archive:
            if not member.isfile():
                continue
            name = _name(member.name)
            if name in names:
                raise ValueError('Duplicate archive asset path')
            names.add(name)
            if name in selected:
                total += member.size
                if member.size > MAX_ASSET or total > MAX_ASSET_TOTAL:
                    raise ValueError('Figure/bibliography asset byte limit exceeded')
                payloads[name] = archive.extractfile(member).read()
    return names, payloads


def literal_preamble(text):
    """Filter literal branches; unresolved conditionals cannot select assets.

    No custom flags, packages, includes or macro bodies are executed here.
    Keep original offsets so declarations retain their source locations.
    """
    code = structural(text)[1].split(r'\begin{document}', 1)[0]
    # Macro replacement text is not an executed declaration. Hide definitions,
    # then reject calls whose effects this literal-only reader cannot evaluate.
    macros, cursor, chars = set(), 0, list(code)
    for match in re.finditer(r'\\([a-zA-Z]+)', code):
        if match.start() < cursor or match[1] not in DEFINITIONS:
            continue
        pos = match.end()
        wrapper = re.match(r'\s*\{\s*\\([a-zA-Z]+)\s*\}', code[pos:])
        target = wrapper or TARGET.match(code, pos)
        if target is None:
            raise ValueError('Unsupported preamble macro declaration')
        macros.add(target[1])
        pos = pos + wrapper.end() if wrapper else target.end()
        if match[1] not in ('def', 'gdef', 'edef', 'xdef'):
            pos += len(code[pos:]) - len(code[pos:].lstrip())
            while pos < len(code) and code[pos] == '[':
                option = re.match(r'\[[^\[\]]*\]\s*', code[pos:])
                if option is None:
                    raise ValueError('Unsupported preamble macro default')
                pos += option.end()
        opening = code.find('{', pos)
        if opening < 0:
            raise ValueError('Unsupported preamble macro body')
        cursor = group_end(code, opening)
        chars[match.start():cursor] = blank(code[match.start():cursor])
    code = ''.join(chars)
    flags = set(re.findall(r'\\newif\s*\\(if[a-zA-Z]+)', code))
    # A declaration target is not a conditional invocation.
    code = re.sub(r'\\newif\s*\\if[a-zA-Z]+', lambda m: blank(m[0]), code)
    code = constant_branches(code, custom=flags)
    controls = set(re.findall(r'\\([a-zA-Z]+)', code))
    if controls.intersection(PRIMITIVES | flags | macros | {'unless', 'let', 'futurelet', 'input', 'include', 'csname'}):
        raise ValueError('Unresolved preamble asset declarations require fallback')
    depth = 0
    for token in re.finditer(r'\\([a-zA-Z]+)|\\.|[{}]', code):
        command = token[1]
        if command in {'graphicspath', 'bibliography', 'addbibresource'} and depth:
            raise ValueError('Scoped preamble asset declarations require fallback')
        if token[0] == '{' or command in {'begingroup', 'bgroup'}:
            depth += 1
        elif token[0] == '}' or command in {'endgroup', 'egroup'}:
            depth -= 1
            if depth < 0:
                raise ValueError('Unmatched preamble asset scope')
    if depth:
        raise ValueError('Unterminated preamble asset scope')
    return code

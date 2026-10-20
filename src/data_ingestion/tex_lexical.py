"""Non-executing lexical handling shared by source traversal and chunking."""
import re

TOKEN = re.compile(r'\\[a-zA-Z]+\*?|\\.|%')
LITERAL = re.compile(r'\s*\{(verbatim\*?|Verbatim\*?|lstlisting|minted|comment)\}')


def blank(text):
    """Keep byte-independent character offsets and original line numbers."""
    return ''.join('\n' if char == '\n' else ' ' for char in text)


def scan(text):
    """Return comment-blanked source and opaque literal spans; never interpret code."""
    parts, spans, cursor = [], [], 0
    while match := TOKEN.search(text, cursor):
        parts.append(text[cursor:match.start()])
        start, end, token = match.start(), match.end(), match[0]
        if token == '%':
            end = text.find('\n', end)
            if end < 0:
                end = len(text)
            parts.append(blank(text[start:end]))
        elif token in (r'\verb', r'\verb*'):
            if end == len(text) or text[end].isspace() or text[end].isalpha():
                raise ValueError('Invalid TeX verb delimiter')
            close = text.find(text[end], end + 1)
            if close < 0 or '\n' in text[end:close]:
                raise ValueError('Unterminated TeX verb')
            end = close + 1
            parts.append(text[start:end])
            spans.append((start, end))
        elif token == r'\begin' and (environment := LITERAL.match(text, end)):
            name = environment[1]
            close = re.search(r'\\end\s*\{' + re.escape(name) + r'\}', text[environment.end():])
            if close is None:
                raise ValueError('Unterminated TeX literal/comment environment')
            end = environment.end() + close.end()
            if name == 'comment':
                parts.append(blank(text[start:end]))
            else:
                parts.append(text[start:end])
                spans.append((start, end))
        else:
            parts.append(token)
        cursor = end
    parts.append(text[cursor:])
    return ''.join(parts), spans


def structural(text):
    """Hide literals from root/include/math recognition, retaining exact offsets."""
    clean, spans = scan(text)
    chars = list(clean)
    for start, end in spans:
        chars[start:end] = blank(clean[start:end])
    # Escaped backslashes are not a second command opener.
    for match in TOKEN.finditer(''.join(chars)):
        if match[0] == r'\\':
            chars[match.start():match.end()] = '  '
    return clean, ''.join(chars), spans


# Only literal boolean primitives are evaluated. Arbitrary conditions remain
# visible to the caller's fail-closed validation, not guessed from macro names.
PRIMITIVES = frozenset(('if ifcat ifnum ifdim ifodd ifvmode ifhmode ifmmode ifinner '
                       'ifvoid ifhbox ifvbox ifx ifeof iftrue iffalse ifcase '
                       'ifdefined ifcsname ifincsname').split())


def constant_branches(text, custom=()):
    clean, code, _ = structural(text)
    chars = list(clean)
    stack, cursor = [], 0
    for match in re.finditer(r'\\([a-zA-Z]+)|\\.', code):
        command = match[1]
        active = all(frame[0] is not False for frame in stack)
        if not active:
            chars[cursor:match.start()] = blank(clean[cursor:match.start()])
        if command == 'unless':
            raise ValueError('TeX unless condition requires HTML/PDF fallback')
        is_control = command in PRIMITIVES or command in custom
        remove = not active
        if is_control:
            known = command in ('iftrue', 'iffalse')
            stack.append([command == 'iftrue' if known else None, False])
            remove = remove or known
        elif command == 'else':
            if not stack or stack[-1][1]:
                raise ValueError('Unmatched or duplicate TeX else')
            frame = stack[-1]
            frame[1] = True
            if frame[0] is not None:
                frame[0] = not frame[0]
                remove = True
        elif command == 'fi':
            if not stack:
                raise ValueError('Unmatched TeX fi')
            frame = stack.pop()
            remove = remove or frame[0] is not None
        if remove:
            chars[match.start():match.end()] = blank(clean[match.start():match.end()])
        cursor = match.end()
    if stack:
        raise ValueError('Unterminated TeX conditional')
    return ''.join(chars)

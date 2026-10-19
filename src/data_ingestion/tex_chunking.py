"""Soft-size TeX chunks whose boundaries never bisect recognized math spans."""
import re

ENVIRONMENTS = r'equation\*?|align\*?|alignat\*?|flalign\*?|gather\*?|multline\*?|eqnarray\*?|displaymath|math'
OPEN = re.compile(r'\\begin\s*\{(' + ENVIRONMENTS + r')\}|\\\[|\\\(|\${1,2}')
MAX_MATH = 32768


def _active(text, position):
    cursor = position - 1
    while cursor >= 0 and text[cursor] == '\\':
        cursor -= 1
    return (position - cursor - 1) % 2 == 0


def math_spans(text):
    """Recognize explicit delimiters/environments, not macro-generated math."""
    spans, cursor = [], 0
    while match := OPEN.search(text, cursor):
        cursor = match.end()
        if not _active(text, match.start()):
            continue
        token = match[0]
        if match[1]:
            close = re.compile(r'\\end\s*\{' + re.escape(match[1]) + r'\}')
        elif token == r'\[':
            close = re.compile(re.escape(r'\]'))
        elif token == r'\(':
            close = re.compile(re.escape(r'\)'))
        elif token == '$$':
            close = re.compile(r'\$\$')
        else:
            close = re.compile(r'(?<!\$)\$(?!\$)')
        end = close.search(text, cursor)
        while end and not _active(text, end.start()):
            end = close.search(text, end.end())
        if end is None:
            raise ValueError('Unterminated TeX math; use HTML/PDF fallback')
        if end.end() - match.start() > MAX_MATH:
            raise ValueError('TeX math exceeds atomic-span limit')
        spans.append((match.start(), end.end()))
        cursor = end.end()
    return spans


def split_tex(text, chunk_size=1800, overlap=250):
    if not 0 <= overlap < chunk_size:
        raise ValueError('Invalid TeX chunk size/overlap')
    spans = math_spans(text)

    def inside(position):
        return next(((left, right) for left, right in spans if left < position < right), None)

    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        protected = inside(end)
        if protected:
            left, right = protected
            # Keep preceding overlap prose with a nearby equation. Size is soft:
            # an atomic equation may exceed it, but never MAX_MATH plus context.
            end = right if left - start <= overlap else left
        elif end < len(text):
            # Prefer paragraph/line/word boundaries outside protected math.
            for separator in ('\n\n', '\n', ' '):
                boundary = text.rfind(separator, start + chunk_size // 2, end)
                while boundary >= 0 and inside(boundary):
                    boundary = text.rfind(separator, start + chunk_size // 2, boundary)
                if boundary > start:
                    end = boundary
                    break
        raw = text[start:end]
        body = raw.strip()
        if body:
            yield {'text': body, 'start_index': start + len(raw) - len(raw.lstrip()),
                   'oversized_math': end - start > chunk_size}
        following = max(start + 1, end - overlap)
        if protected := inside(following):
            following = protected[0]
        # Never loop on an equation that filled the entire preceding chunk.
        start = following if following > start else end
        if end == len(text):
            break

"""Retain bounded source structure as data, never executable source HTML.

This does not reconstruct structure or describe figures. Citation checks continue
using the existing canonical passage text, independently of this reading view.
"""
import re

from bs4 import Comment, NavigableString

HTML_TAGS = set('p div span h1 h2 h3 h4 h5 h6 ul ol li dl dt dd blockquote em strong b i sub sup br table caption thead tbody tfoot tr th td figure figcaption'.split())
MATH_TAGS = set('math semantics annotation mrow mi mn mo mtext mspace ms mfrac msqrt mroot msub msup msubsup munder mover munderover mmultiscripts mprescripts none mtable mtr mtd menclose mphantom mpadded mstyle mfenced'.split())
DROP_TAGS = set('script style iframe object embed template noscript nav form input button audio video svg'.split())
MATH_ATTRS = set('display mathvariant stretchy fence separator accent accentunder columnalign rowalign columnspan rowspan encoding linethickness'.split())
MATH_METADATA = {'class', 'id', 'alttext', 'xmlns', 'href', 'xlink:href'}


def retain_reader(nodes, source_sha256):
    """Source-owned semantics only; unknown wrappers are flattened, not executed."""
    count = 0
    limitations = set()

    def convert(node, depth=0, in_math=False):
        nonlocal count
        count += 1
        if count > 12000 or depth > 48:
            raise ValueError('Reader structure exceeds bounded preview.')
        if isinstance(node, Comment):
            return []
        if isinstance(node, NavigableString):
            return [str(node)]
        tag = node.name
        if tag in DROP_TAGS:
            return []
        if in_math and tag not in MATH_TAGS:
            raise ValueError('Unsupported MathML structure; use the retained citation-check text or original source.')
        if tag == 'img':
            alt = node.get('alt', '').strip()
            if alt:
                return [{'tag': 'p', 'children': ['Source-supplied image description: ' + alt]}]
            limitations.add('No source-supplied image description is available for at least one image; its content is not described.')
            return []
        children = [child for item in node.children for child in convert(item, depth + 1, in_math or tag == 'math')]
        if tag not in HTML_TAGS | MATH_TAGS:
            limitations.add('Unsupported source markup is shown as text where possible; not all source structure is retained.')
            return children
        attrs = {}
        # Table IDs are remapped into a reader-local namespace by the browser.
        if tag in {'th', 'td'}:
            for key in ('id', 'headers', 'scope', 'colspan', 'rowspan'):
                if node.has_attr(key):
                    value = node[key]
                    attrs[key] = ' '.join(value) if isinstance(value, list) else str(value)
            if tag == 'th' and not (node.get('scope') or node.get('id')):
                limitations.add('Some source table headers have no explicit scope or header IDs; relationships are retained only as supplied.')
        if tag == 'table' and not node.find('th'):
            limitations.add('A source table has no header cells. No row or column headers have been inferred.')
        if tag in {'ol', 'li'}:
            for key in ('start', 'value', 'reversed'):
                if node.has_attr(key):
                    attrs[key] = str(node[key])
        if tag in MATH_TAGS:
            # Never silently replace unsupported mathematical semantics with defaults.
            if any(key not in MATH_ATTRS | MATH_METADATA and not key.startswith(('on', 'data-')) for key in node.attrs):
                raise ValueError('Unsupported MathML attributes; use the retained citation-check text or original source.')
            if node.has_attr('linethickness'):
                thickness = str(node['linethickness'])
                if tag != 'mfrac' or not re.fullmatch(r'(?:thin|medium|thick|(?:\d+(?:\.\d+)?|\.\d+)(?:em|ex|px|in|cm|mm|pt|pc|%)?)', thickness):
                    raise ValueError('Unsupported MathML fraction thickness; use the retained citation-check text or original source.')
                attrs['linethickness'] = thickness
            for key in MATH_ATTRS - {'linethickness'}:
                if node.has_attr(key):
                    value = str(node[key])
                    if len(value) >= 100:
                        raise ValueError('Unsupported MathML attributes; use the retained citation-check text or original source.')
                    attrs[key] = value
        if tag == 'figure':
            limitations.add('A figure caption is source text, not a complete description of the figure.')
            if not node.find('img', alt=lambda value: bool(value and value.strip())):
                limitations.add('No source-supplied image description is available for a figure; the caption alone may omit visual information.')
                children.append({'tag': 'p', 'children': ['Reader limitation: no source-supplied image description is available for this figure. Its caption may omit visual information.']})
        if tag == 'figcaption':
            children.insert(0, 'Source-supplied caption: ')
        return [{'tag': tag, 'attrs': attrs, 'children': children}]

    try:
        retained = [child for node in nodes for child in convert(node)]
    except ValueError as error:
        retained = []
        limitations.add(str(error))
    return {'version': 1, 'provenance': 'source-html', 'source_sha256': source_sha256,
            'nodes': retained, 'limitations': sorted(limitations)}

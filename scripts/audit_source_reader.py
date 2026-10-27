"""Inspect retained structure against a local version-pinned arXiv HTML snapshot.

python -m scripts.audit_source_reader source.html --arxiv-id 2608.20318v1 --out /tmp/reader-audit.json
No downloads, generation, inferred structure, or source-certification verdict.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from bs4 import BeautifulSoup
from src.paper_html import parse_paper_html


def nodes(items):
    for item in items:
        if isinstance(item, dict):
            yield item
            yield from nodes(item.get('children', []))


def audit(raw, aid):
    passages, source = parse_paper_html(raw, aid, aid)
    soup = BeautifulSoup(raw, 'html.parser')
    article = soup.select_one('article.ltx_document')
    for excluded in article.select('script, style, nav, .ltx_bibliography'):
        excluded.decompose()
    tags = ['math', 'table', 'th', 'td', 'figure', 'figcaption']
    original = {tag: len(article.find_all(tag)) for tag in tags}
    retained = Counter(n['tag'] for p in passages for n in nodes(p['reader']['nodes']))
    return {'arxiv_id': aid, 'source': source, 'source_file_sha256': sha256(raw).hexdigest(),
            'status': 'development fidelity inspection; not source certification or AT approval',
            'original_structure_counts': original,
            'retained_structure_counts': {tag: retained[tag] for tag in tags},
            'passages': [{'chunk_id': p['chunk_id'], 'section': p['section'],
                'source_url': p['source_url'], 'structured': bool(p['reader']['nodes']),
                'citation_text_sha256': sha256(p['text'].encode()).hexdigest(),
                'limitations': p['reader']['limitations'],
                'table_header_attributes': [n.get('attrs', {}) for n in nodes(p['reader']['nodes']) if n['tag'] in {'th', 'td'}],
                'math_attributes': [n.get('attrs', {}) for n in nodes(p['reader']['nodes']) if n['tag'] == 'math']}
                for p in passages],
            'review_instructions': ['Compare mathematical expressions and table cell relationships with the pinned original.',
                'Inspect whole-passage fallback where unsupported attributes or structures are recorded.',
                'Counts do not establish equivalent meaning, caption completeness, or screen-reader navigation.',
                'The original may contain structure outside selected preview blocks; do not infer extraction completeness.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--arxiv-id', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.source.read_bytes(), args.arxiv_id)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['arxiv_id', 'original_structure_counts', 'retained_structure_counts']}))


if __name__ == '__main__':
    main()

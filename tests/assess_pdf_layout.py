"""Read-only cached-PDF triage; signals are not visual fidelity verdicts.

python -m tests.assess_pdf_layout --pdf-dir data/pdfs --output docs/pdf-layout-assessment.json
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pymupdf

from src.data_ingestion.pdf_parser import extract_pages


def assess(pdf_dir):
    manifest = Path('data/metadata/arxiv_csAI_25_pdf_sample.csv')
    baseline_path = Path('docs/ingestion-validation.json')
    baseline = {p['arxiv_id']: p['pdf_sha256'] for p in json.loads(baseline_path.read_text())['sample']}
    records = []
    for row in csv.DictReader(manifest.open()):
        paper_id = row['arxiv_id']
        path = pdf_dir / f'{paper_id}.pdf'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        cleaned = {p['page']: p['text'] for p in extract_pages(str(path))}
        pages = []
        with pymupdf.open(path) as doc:
            for number, page in enumerate(doc, 1):
                raw = page.get_text()
                blocks = [b for b in page.get_text('blocks') if b[6] == 0]
                narrow = [b for b in blocks if b[2] - b[0] <= .6 * page.rect.width and len(b[4]) > 100]
                left = any((b[0] + b[2]) / 2 < page.rect.width / 2 for b in narrow)
                right = any((b[0] + b[2]) / 2 >= page.rect.width / 2 for b in narrow)
                pages.append({
                    'page': number, 'raw_text_chars': len(raw),
                    'fallback_text_chars': len(cleaned.get(number, '')),
                    'two_column_signal': left and right,
                    'raster_image_count': len(page.get_image_info()),
                    'table_labels': sorted(set(re.findall(r'\bTable\s+\d+', raw))),
                    'figure_labels': sorted(set(re.findall(r'\b(?:Figure|Fig\.)\s*\d+', raw))),
                    'back_matter_signal': bool(re.search(r'(?im)^\s*(?:\d+\.?\s*)?(?:references|bibliography|appendix|appendices)\b', raw)),
                    'replacement_chars': raw.count('\ufffd'),
                })
        records.append({'arxiv_id': paper_id, 'title': row['title'], 'pdf_url': row['pdf_url'],
                        'pdf_sha256': digest, 'matches_historical_pdf_hash': digest == baseline[paper_id],
                        'pages': pages})
    return {'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
            'source_mode': 'cached PDFs; raw PyMuPDF versus HTML-first PDF fallback extract_pages',
            'limits': 'Geometry/labels/text counts are triage signals, not table, equation, reading-order or OCR fidelity scores. No live links, HTML ingestion, chunking or relevance evaluated. Fallback text is before reference/appendix cutoff.',
            'historical_pdf_validation_sha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
            'papers': records}


def write_report(result, output):
    """One page record per line keeps generated evidence reviewable."""
    lines = ['{']
    for key, value in result.items():
        if key != 'papers':
            lines.append(f'  {json.dumps(key)}: {json.dumps(value)},')
    lines.append('  "papers": [')
    for index, paper in enumerate(result['papers']):
        lines.append('    {')
        for key, value in paper.items():
            if key != 'pages':
                lines.append(f'      {json.dumps(key)}: {json.dumps(value)},')
        lines.append('      "pages": [')
        for number, page in enumerate(paper['pages']):
            comma = ',' if number + 1 < len(paper['pages']) else ''
            lines.append('        ' + json.dumps(page, separators=(',', ':')) + comma)
        lines.append('      ]')
        lines.append('    }' + (',' if index + 1 < len(result['papers']) else ''))
    lines.extend(['  ]', '}'])
    output.write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.pdf_dir)
    write_report(result, args.output)
    print(f"Assessed {len(result['papers'])} cached PDFs; report: {args.output}")

"""Prepare explicit, hashed source blocks from existing cached research artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from src.data_ingestion.html_parser import parse_html_sections
from src.data_ingestion.pdf_parser import split_into_sections


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=Path, required=True)
    ap.add_argument('--questions', type=Path, required=True)
    ap.add_argument('--html-dir', type=Path, required=True)
    ap.add_argument('--tex-audit-dir', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    questions = [q for q in json.loads(args.questions.read_text()) if q['id'].startswith('n')]
    extra_path = Path(__file__).with_name('extra_questions.json')
    for i, (paper, query, anchors) in enumerate(json.loads(extra_path.read_text())):
        questions.append(dict(id=f'r{i+1:02}',paper=paper,query=query,anchors=anchors,
                              question_origin='New explanatory development question, abstract-backed; not human answer-quality labels'))
    ids = {q['paper'] for q in questions}
    papers = {p['id']: p for p in json.loads(args.pages.read_text()) if p['id'] in ids}
    audits = {p['id']: p for p in json.loads((args.tex_audit_dir/'results.json').read_text())}
    blocks = []
    receipts = []
    def add(source, aid, text, **location):
        if text.strip():
            blocks.append(dict(source=source, paper=aid, title=papers[aid]['title'],
                               text=text, location=location))
    for aid in sorted(ids):
        p = papers[aid]
        sections, offsets = split_into_sections(p['pages'])
        for sec in sections:
            if len(sec['text'].strip()) < 150:
                continue
            for (page_start, _), page in zip(offsets, p['pages']):
                a, b = max(sec['start'], page_start), min(sec['end'], page_start+len(page['text']))
                if a < b:
                    add('pdf', aid, sec['text'][a-sec['start']:b-sec['start']],
                        page_number=page['page'], source_url=f'https://arxiv.org/pdf/{aid}#page={page["page"]}', section=sec['section'])
        receipts.append(dict(source='pdf', paper=aid, path=p['path'], sha256=sha(Path(p['path']))))
        html = args.html_dir/(aid+'.html')
        if html.exists():
            try:
                sections = parse_html_sections(html.read_text())
                for sec in sections:
                    anchor = sec.get('subsection_id') or sec.get('section_id') or ''
                    add('html', aid, sec['text'], page_number=None,
                        source_url=f'https://arxiv.org/html/{aid}'+('#'+quote(anchor, safe='') if anchor else ''),
                        section=sec['section'], subsection=sec['subsection'])
                receipts.append(dict(source='html', paper=aid, path=str(html), sha256=sha(html), sections=len(sections)))
            except Exception as error:
                receipts.append(dict(source='html', paper=aid, error=str(error)))
        else:
            receipts.append(dict(source='html', paper=aid, error='No cached HTML; no PDF substitution'))
        tex = args.tex_audit_dir/aid/'blocks.json'
        if tex.exists():
            audit = audits[aid]
            for filename, first_line, text in json.loads(tex.read_text()):
                add('tex', aid, text, page_number=None, source_url=f'https://arxiv.org/src/{aid}',
                    source_file=filename, line_start=first_line, line_end=first_line+text.count('\n'),
                    source_sha256=audit['source_sha256'])
            receipts.append(dict(source='tex', paper=aid, path=str(tex), sha256=sha(tex),
                                 parser_commit=audit['head'], archive_sha256=audit['source_sha256'],
                                 note='Cached parsed raw TeX include blocks, not rendered text; original archive unavailable locally'))
        else:
            receipts.append(dict(source='tex', paper=aid, error='No cached TeX; no PDF substitution'))
    for i, block in enumerate(blocks):
        block['id'] = i
    available = {source: {b['paper'] for b in blocks if b['source']==source} for source in ('pdf','html','tex')}
    common = sorted(set.intersection(*available.values()))
    # Split before any retrieval. These are already-inspected DEVELOPMENT labels.
    split = {aid: ('validation' if i%2 else 'tuning') for i, aid in enumerate(common)}
    data = dict(blocks=blocks, questions=questions, common_papers=common, split=split,
                receipts=receipts, input_questions_sha256=sha(args.questions),
                notes=['25 pre-existing plus 25 new explanatory development questions; paper-separated retrospective validation, not blind test',
                       'HTML parser omits display math/tables; TeX retains raw math/macros and historical parse provenance'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False))
    print(json.dumps(dict(blocks=len(blocks), available={s:len(a) for s,a in available.items()},common=len(common),split=split),indent=2))


if __name__ == '__main__':
    main()

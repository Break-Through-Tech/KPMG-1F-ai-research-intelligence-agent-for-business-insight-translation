"""Apply SELECTION-RULE.md mechanically: themes in order, candidates by submission date, first two eligible each.
Downloads only arXiv HTML for candidates it checks (stops per theme at two). Writes html/<id>.html,
sources.json (input for src.experimental.build_bundle) and selection-log.json. No model calls.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.experimental.html_evidence import extract_html_evidence, validate_source_bindings  # noqa: E402
from src.data_ingestion.html_parser import parse_html_sections  # noqa: E402
from src.data_ingestion.chunking import chunk_html_sections  # noqa: E402

CORPUS = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
THEMES = ['T1', 'T2', 'T3', 'T4', 'T5']
ALLOWED = {'cs.CL', 'cs.AI', 'cs.LG'}
PER_THEME = 2
UA = 'research-evaluation-client/1.0'


def base(ident):
    return ident.split('v')[0] if 'v' in ident[5:] else ident


def fetch(ident, path):
    if path.is_file():
        return path.read_text(encoding='utf-8'), 200
    time.sleep(3.1)
    req = urllib.request.Request(f'https://arxiv.org/html/{ident}', headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            status = resp.status
    except urllib.error.HTTPError as error:
        return None, error.code
    path.write_text(body, encoding='utf-8')
    return body, status


def main():
    corpus = {base(json.loads(line)['arxiv_id']) for line in CORPUS.open(encoding='utf-8')}
    (HERE / 'html').mkdir(exist_ok=True)
    chosen, log, sources = [], [], []
    for theme in THEMES:
        picked = 0
        rows = [json.loads(l) for l in (HERE / 'discovery' / theme / 'metadata.jsonl').open(encoding='utf-8')]
        for r in rows:
            if picked == PER_THEME:
                break
            ident, entry = r['arxiv_id'], {'theme': theme, 'arxiv_id': r['arxiv_id'], 'title': r['title']}
            cats = r.get('categories') or ''
            primary = cats.replace(',', ' ').split()[0] if cats.strip() else None  # first listed = primary
            reason = None
            if base(ident) in corpus:
                reason = 'already in demo-100'
            elif base(ident) in {base(c['arxiv_id']) for c in chosen}:
                reason = 'already selected for an earlier theme'
            elif primary and primary not in ALLOWED:
                reason = f'primary category {primary}'
            if not reason:
                html, status = fetch(ident, HERE / 'html' / f'{ident}.html')
                if html is None or status != 200 or 'ltx_document' not in html:
                    reason = f'no arXiv HTML (status {status})'
                elif 'ltx_tabular' not in html and '<table' not in html:
                    reason = 'no table'
                else:
                    try:
                        result = extract_html_evidence(html, ident, r['title'], include_appendix=True)
                        validate_source_bindings(result['passages'], html, ident, r['title'])
                        tables = len(result['passages'])
                        prose = len(chunk_html_sections(parse_html_sections(html), ident, r['title']))
                        n = prose + tables
                        entry.update(passages=n, prose_chunks=prose, table_rows=tables)
                        if n < 20:
                            reason = f'only {n} passages extracted'
                        elif tables == 0:
                            reason = 'no extracted table rows'
                    except Exception as error:  # extraction failure makes the paper ineligible
                        reason = f'extraction failed: {type(error).__name__}: {str(error)[:120]}'
            entry['decision'] = 'skip: ' + reason if reason else 'selected'
            log.append(entry)
            print(theme, ident, entry['decision'], flush=True)
            if not reason:
                picked += 1
                chosen.append(entry)
                sources.append({'arxiv_id': ident, 'title': r['title'], 'html_path': f'html/{ident}.html'})
        if picked < PER_THEME:
            print(theme, f'only {picked} eligible in window: fallback window needed', flush=True)
    (HERE / 'selection-log.json').write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'sources.json').write_text(json.dumps(sources, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps([(c['theme'], c['arxiv_id'], c['prose_chunks'], c['table_rows']) for c in chosen]))


if __name__ == '__main__':
    main()

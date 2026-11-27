"""Model-free extractor audit for the full-table endpoint (completeness evidence).

Experimental prototype (2026-11-17). Not part of the shared application.

Why: ``parents.jsonl`` alone cannot prove a table is complete. A contiguous prefix
(rows 1..N-1 of an N-row table) passes every structural check. The deterministic HTML
extractor records how many rows it accepted for each table (``coverage.tables[].rows_emitted``),
but the demo-100 bundle's ``extraction-audit.json`` is empty, so that count was never saved.

What this does, per paper with table rows in the bundle:
1. Finds a local HTML file whose bytes (or their LF form: Windows checkouts may use CRLF)
   hash exactly to the rows' ``source_sha256``. File names are never trusted on their own.
2. Loads the extractor whose ``VERSION`` equals the rows' ``extractor_version`` (the demo-100
   rows were produced by ``html-evidence-v1.2``, ``src/data_ingestion/html_evidence.py``),
   read-only, without running its package ``__init__``.
3. Re-runs it and records each table's accepted-row count (``rows_emitted``) plus whether the
   re-extracted row passages are identical, field for field, to the rows stored in the bundle.

The output is bound to the bundle's ``parents.jsonl`` SHA-256, each paper's source hash and
the extractor version. No network, no model, no writes outside ``--out``. Papers whose HTML or
extractor cannot be matched are listed under ``missing_sources``; the endpoint then refuses
their tables (fail closed) instead of calling them complete.

Run (needs bs4, available under ``py -3.14``):
    py -3.14 build_table_audit.py \
        --bundle D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100 \
        --extractor-dir C:/Users/ngkho/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/src/data_ingestion \
        --html-root C:/Users/ngkho/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/data/html \
        --out table-audit-demo-100.json
"""
import argparse
from hashlib import sha256
import gzip
import importlib
import inspect
import json
import sys
import types
from pathlib import Path

AUDIT_KIND = 'extractor_table_audit_v1'


def load_extractor(folder):
    """Import ``<folder>/html_evidence.py`` as a package member without running ``__init__``."""
    name = f'_table_audit_extractor_{sha256(str(folder).encode()).hexdigest()[:8]}'
    package = types.ModuleType(name)
    package.__path__ = [str(folder)]
    sys.modules[name] = package
    return importlib.import_module(f'{name}.html_evidence')


def find_html(roots, arxiv_id, expected_sha):
    for root in roots:
        for path in (root / f'{arxiv_id}.html', root / f'{arxiv_id}.html.gz'):
            if not path.is_file():
                continue
            data = path.read_bytes()
            if path.suffix == '.gz':
                data = gzip.decompress(data)
            found = _match(data, expected_sha)
            if found is not None:
                return found
    return None


def _match(data, expected_sha):
    """Return the decoded HTML only when its bytes (or their LF form) hash to ``expected_sha``."""
    for candidate in (data, data.replace(b'\r\n', b'\n')):
        if sha256(candidate).hexdigest() == expected_sha:
            return candidate.decode("utf-8")
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--export', type=Path, action='append', default=[],
                        help='Clean export root whose src.experimental.html_evidence is loaded (read-only); may repeat.')
    parser.add_argument('--extractor-dir', type=Path, action='append', default=[],
                        help='Folder containing a standalone html_evidence.py (read-only); may repeat.')
    parser.add_argument('--html-root', type=Path, action='append', required=True,
                        help='Folder of <arxiv_id>.html files; may repeat. Matched by byte hash only.')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    extractors = {}
    for root in args.export:
        sys.path.insert(0, str(root.resolve()))
        module = importlib.import_module('src.experimental.html_evidence')
        extractors.setdefault(module.VERSION, module)
    for folder in args.extractor_dir:
        module = load_extractor(folder.resolve())
        extractors.setdefault(module.VERSION, module)

    raw = (args.bundle / 'parents.jsonl').read_bytes()
    index_sha256 = sha256(raw).hexdigest()
    stored, tables = {}, {}
    for line in raw.decode('utf-8').splitlines():
        if '"linearized_table"' not in line:
            continue
        p = json.loads(line)
        if p.get('representation') != 'linearized_table':
            continue
        stored[p['chunk_id']] = p
        tables.setdefault((p['arxiv_id'], p['table_id']), set()).add(
            (p.get('extractor_version'), p.get('source_sha256'), p.get('title')))
    out = {'kind': AUDIT_KIND, 'index_sha256': index_sha256,
           'method': 're-ran the deterministic extractor whose VERSION matches the rows of each table, on local HTML '
                     'whose bytes hash to source_sha256; rows_emitted is the accepted-row count',
           'extractor_versions': sorted(extractors), 'model_calls': 0, 'tables': {}, 'missing': []}
    runs = {}
    for (arxiv_id, table_id), identities in sorted(tables.items()):
        key = f'{arxiv_id}#{table_id}'
        if len(identities) != 1:
            out['missing'].append({'table': key, 'reason': 'rows disagree on extractor version, source hash or title'})
            continue
        version, source_sha, title = next(iter(identities))
        module = extractors.get(version)
        if module is None:
            out['missing'].append({'table': key, 'reason': f'no extractor loaded for {version}'})
            continue
        run_key = (arxiv_id, version, source_sha)
        if run_key not in runs:
            html = find_html(args.html_root, arxiv_id, source_sha)
            if html is None:
                runs[run_key] = None
            else:
                kwargs = {'include_appendix': True} if 'include_appendix' in inspect.signature(module.extract_html_evidence).parameters else {}
                runs[run_key] = module.extract_html_evidence(html, arxiv_id, title, **kwargs)
        result = runs[run_key]
        if result is None or result['coverage']['source_sha256'] != source_sha:
            out['missing'].append({'table': key, 'reason': 'no local HTML matches source_sha256'})
            continue
        audit = next((t for t in result['coverage']['tables'] if t.get('anchor') == table_id), None)
        if audit is None:
            out['missing'].append({'table': key, 'reason': 'extractor did not report this table'})
            continue
        emitted = [p for p in result['passages']
                   if p.get('representation') == 'linearized_table' and p.get('table_id') == table_id]
        out['tables'][key] = {
            'status': audit['status'], 'rows_emitted': audit['rows_emitted'],
            'source_sha256': source_sha, 'extractor_version': version,
            # Field-for-field identity with the bundle proves the count describes these exact rows.
            'rows_identical_to_bundle': bool(emitted) and len(emitted) == audit['rows_emitted']
                and all(stored.get(p['chunk_id']) == p for p in emitted),
        }
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True), encoding='utf-8')
    print(json.dumps({'out': str(args.out), 'tables_audited': len(out['tables']), 'missing': len(out['missing']),
                      'index_sha256': index_sha256, 'model_calls': 0}))


if __name__ == '__main__':
    main()

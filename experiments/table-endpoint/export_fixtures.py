"""Export recorded live evidence (2026-11-17 briefs) as UI test fixtures. Read-only; no model calls.

Usage: python -I export_fixtures.py <output folder>
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evidence_tables import TableIndex  # noqa: E402

BUNDLE = Path(r'D:\KPMG-demo-corpus\main-727b0b3\data\processed\demo-bundles\demo-100\parents.jsonl')
RECORDED = Path(r'D:\KPMG-demo-corpus\fable-live-briefs.sqlite3')
NOTE = ('Recorded live research response (Fable live test, 2026-11-17, demo-100 index, Codex provider). '
        'Replayed for model-free UI tests; not a new research run.')


def main(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    index = TableIndex(BUNDLE, HERE / 'table-audit-demo-100.json')
    db = sqlite3.connect(f'file:{RECORDED}?mode=ro', uri=True)
    rows = db.execute('select b.title, v.envelope_json from brief_versions v join briefs b on b.id = v.brief_id').fetchall()
    written = []
    for title, env in rows:
        envelope = json.loads(env)
        name = {'full': 'recorded-cu-dpo', 'insufficient': None}[envelope['scenario']]
        if name is None:
            name = 'recorded-fin-rate-crossstudy' if any('2602.07294' in p['chunk_id'] for p in envelope['result']['evidence']) and \
                any('2508.03553' in p['chunk_id'] for p in envelope['result']['evidence']) else (
                'recorded-out-of-corpus' if 'Willow' in title else 'recorded-multirag-abstention')
        sha = envelope['result']['provenance']['index']['indexed_records_sha256']
        full = {}
        for passage in envelope['result']['evidence']:
            if passage.get('representation') == 'linearized_table':
                key = f"{passage['arxiv_id']}#{passage['table_id']}"
                if key not in full:
                    full[key] = index.table(passage['chunk_id'], sha)
        (out / f'{name}.json').write_text(json.dumps({'_note': NOTE, 'envelope': envelope, 'full_tables': full},
                                                      ensure_ascii=False, indent=1), encoding='utf-8')
        written.append((name, len(full)))
    print(written)


if __name__ == '__main__':
    main(sys.argv[1])

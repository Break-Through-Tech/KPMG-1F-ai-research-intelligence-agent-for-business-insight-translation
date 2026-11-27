"""Write passages/<arxiv_id>.md: every parent of each fresh paper (prose first, then table rows), with chunk IDs, for
authoring the answer key from passages only. Reads the validation bundle; no engine, retriever or model is run."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[2] / 'data/processed/validation-bundles/fresh-v4-110'


def main():
    ids = [s['arxiv_id'] for s in json.loads((HERE / 'sources.json').read_text(encoding='utf-8'))]
    by_paper = {i: [] for i in ids}
    for line in (BUNDLE / 'parents.jsonl').read_text(encoding='utf-8').splitlines():
        if line.strip():
            r = json.loads(line)
            if r['arxiv_id'] in by_paper:
                by_paper[r['arxiv_id']].append(r)
    (HERE / 'passages').mkdir(exist_ok=True)
    for ident, rows in by_paper.items():
        rows.sort(key=lambda r: ('_table_' in r['chunk_id'], r['chunk_id']))
        out = [f"# {rows[0]['title']} ({ident}), {len(rows)} passages", '']
        for r in rows:
            out += [f"## {r['chunk_id']}  [{r.get('section', '')}]", r['text'], '']
        (HERE / 'passages' / f'{ident}.md').write_text('\n'.join(out), encoding='utf-8')
        print(ident, len(rows))


if __name__ == '__main__':
    main()

"""Build the SEPARATE fresh-v4 validation bundle: demo-100 parents (unchanged, read-only) + the 10 selected papers.

New papers get prose parents from the standard ingestion path (html_parser.parse_html_sections ->
chunking.chunk_html_sections, the path that produced demo-100's _cNNNN parents) and table rows from
src.experimental.build_bundle.prepare_parents (html_evidence), then build_bundle writes a NEW directory
(it refuses to overwrite). demo-100 and the production index are never modified. No model calls.
"""
from hashlib import sha256
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'experiments/measure'))
from common import BUNDLE, ENCODER, PIN  # noqa: E402
from src.data_ingestion.chunking import chunk_html_sections  # noqa: E402
from src.data_ingestion.html_parser import parse_html_sections  # noqa: E402
from src.experimental.build_bundle import build_bundle, prepare_parents  # noqa: E402

OUTPUT = ROOT / 'data/processed/validation-bundles/fresh-v4-110'


def prose_parents(source):
    html = (HERE / source['html_path']).read_text(encoding='utf-8')
    digest = sha256(html.encode('utf-8')).hexdigest()  # same convention as html_evidence
    out = []
    for chunk in chunk_html_sections(parse_html_sections(html), source['arxiv_id'], source['title']):
        out.append({**chunk, 'title': source['title'], 'source': 'html', 'source_url': chunk['html_url'],
                    'pdf_url': f"https://arxiv.org/pdf/{source['arxiv_id']}", 'source_sha256': digest})
    return out


def main():
    corpus_bytes = (BUNDLE / 'parents.jsonl').read_bytes()
    assert sha256(corpus_bytes).hexdigest() == PIN, 'demo-100 parents changed'
    corpus = [json.loads(line) for line in corpus_bytes.decode('utf-8').splitlines() if line.strip()]
    sources = json.loads((HERE / 'sources.json').read_text(encoding='utf-8'))
    known = {p['arxiv_id'] for p in corpus}
    assert not known & {s['arxiv_id'] for s in sources}, 'a fresh paper is already in demo-100'
    new = [p for s in sources for p in prose_parents(s)]
    parents, reports = prepare_parents(corpus + new, [{**s, 'html_path': str(HERE / s['html_path'])} for s in sources])
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(str(ENCODER), device='cpu')
    build_bundle(parents, OUTPUT, encoder)
    assert sha256((BUNDLE / 'parents.jsonl').read_bytes()).hexdigest() == PIN, 'demo-100 parents changed'
    manifest = json.loads((OUTPUT / 'manifest.json').read_text(encoding='utf-8'))
    record = {'output': str(OUTPUT), 'corpus_pin': PIN, 'corpus_parents': len(corpus),
              'new_prose_parents': len(new), 'new_table_rows': sum(len([t for t in r['tables'] if t.get('status') == 'accepted'])
                                                                    for r in reports),
              'parents': len(parents), 'manifest': manifest, 'table_reports': reports}
    (HERE / 'bundle-record.json').write_text(json.dumps(record, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in record.items() if k != 'table_reports'}, indent=1))


if __name__ == '__main__':
    main()

"""Authoring aid: print a paper's passages matching a pattern (offline)."""
import json, re, sys
paper, pattern = sys.argv[1], re.compile(sys.argv[2], re.I)
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 700
for line in open('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl', encoding='utf-8'):
    r = json.loads(line)
    if r['arxiv_id'] == paper and pattern.search(r['text']):
        t = ' '.join(r['text'].split())
        m = pattern.search(t)
        s = max(0, m.start() - limit // 3)
        print(r['chunk_id'], '|', r.get('section'), '|', t[s:s + limit]); print()

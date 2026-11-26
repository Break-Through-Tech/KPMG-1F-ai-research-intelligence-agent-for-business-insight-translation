"""Authoring aid: print full passages by chunk id (offline)."""
import json, sys
want = set(sys.argv[1:])
for line in open('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl', encoding='utf-8'):
    r = json.loads(line)
    if r['chunk_id'] in want:
        print(r['chunk_id'], '|', r.get('section'), '|', ' '.join(r['text'].split())); print()

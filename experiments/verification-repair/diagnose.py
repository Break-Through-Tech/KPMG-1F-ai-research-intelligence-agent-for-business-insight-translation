"""Print, for each held finding in a saved run, every contradicted number with each same-valued source mention and the
rule that fails, under the frozen check or v2.   python -I diagnose.py [--frozen] [run] [question ...]"""
import json
import sys

from replay import DATA, PASSAGES, frozen, v2

module = frozen if '--frozen' in sys.argv else v2
args = [a for a in sys.argv[1:] if not a.startswith('--')]
run = args[0] if args else 'codex-business-v1-multiagent'
only = set(args[1:])
for path in sorted((DATA / run).glob('C*/result.json')):
    if only and path.parent.name not in only:
        continue
    summary = json.loads(path.read_text(encoding='utf-8'))['envelope']['result']['summary']
    for claim in summary.get('held_claims', []):
        if claim.get('kind') == 'interpretation':
            continue
        nc = module
        ids = [s['chunk_id'] for s in claim['support']] + claim.get('chunk_ids', [])
        nc._CONTEXT = tuple(PASSAGES[i]['text'] for i in dict.fromkeys(ids) if i in PASSAGES) if nc is v2 else ()
        text = nc._norm(claim['text'])
        sources = [nc._norm(s['quote']) for s in claim['support']]
        joined = ' \n '.join(sources)
        if nc is v2:
            nc._NAME_TEXT = nc._alnum(joined + ' ' + ' '.join(nc._CONTEXT))
        shared = nc._shared_entities(text, sources)
        labels = nc._condition_labels(sources)
        ids_ = {m.group().casefold() for m in nc._IDENTIFIER.finditer(joined)}
        cm = nc._mentions(text, shared, labels, ids_)
        for m in cm:
            m['claim_words'], m['claim_lower'] = nc._content(text), text.lower()
        sm = [m for src in sources for m in nc._mentions(src, shared, labels, ids_)]
        pc = bool(nc.re.search(r'%|percent', joined, nc.re.I))
        print(f'== {path.parent.name} shared={sorted(shared)} | {claim["text"][:80]}')
        for m in cm:
            status, issues = nc._match_mention(m, sm, pc)
            if status != 'contradicted':
                continue
            print(f"  claim {m['text']!r} subj={m['subject']!r} own={m.get('own_subjects')} metric={m['metric']!r} unit={m['unit']!r} -> {issues}")
            for c in sm:
                if nc._same_quantity(m, c):
                    print(f"     src subj={c['subject']!r} own={c.get('own_subjects')} metric={c['metric']!r} unit={c['unit']!r} "
                          f"quals={c['qualifiers']} -> {nc._judge(m, c, pc)}")
        nc._CONTEXT = ()

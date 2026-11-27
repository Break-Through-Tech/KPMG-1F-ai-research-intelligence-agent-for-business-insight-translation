"""Create a NEW local demo library holding the nine validated, reviewed research packets.

Offline: no model calls. Each brief is saved as summary-only research, so the
Business implications form can translate it with the configured Hydrogen host.
Refuses to touch an existing file.
"""
import argparse
import json
from pathlib import Path

from src.brief_store import BriefStore

ROOT = Path(__file__).resolve().parents[1]
PACKETS = [('R5', 'business-evaluation/v1/frozen/packets/R5.json'),
           ('U1', 'business-evaluation/v1/frozen/packets/U1.json'),
           ('U5', 'business-evaluation/v1/frozen/packets/U5.json'),
           ('U6', 'business-evaluation/v1/frozen/packets/U6.json'),
           *[(f'F{n}', f'business-evaluation/v1.2-validation/fresh/F{n}.json') for n in range(1, 6)]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    args = parser.parse_args()
    if args.library.exists():
        parser.error('Library exists; choose a new demo path.')
    store = BriefStore(args.library)
    for case, path in PACKETS:
        packet = json.loads((ROOT / path).read_text(encoding='utf-8-sig'))
        context = packet['context']
        store.save({'mode': 'indexed', 'scenario': 'summary-only', 'result': packet['result'], 'error': None},
                   title=f'{case}: {context["workflow"]}'[:120])
        print(f'{case}\tindustry: {context["industry"]}\n\tworkflow: {context["workflow"]}\n\tdecision: {context.get("decision", "")}')
    print(f'Seeded {len(PACKETS)} briefs into {args.library}')


if __name__ == '__main__':
    main()

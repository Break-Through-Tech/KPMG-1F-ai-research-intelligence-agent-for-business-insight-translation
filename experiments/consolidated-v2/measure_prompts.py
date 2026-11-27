"""Measured offline prompt sizes, v1 vs v2, on the saved consolidated-v1 packets and drafts (0 model calls).
Sizes are request-guard estimates (ceil(UTF-8 bytes / 3)) of OUR prompt + schema. They are NOT provider token counts:
provider usage also includes the CLI/system overhead (accounting.py) and is measured only by a live run.

    D:\\KPMG-venvs\\stage-a-py314\\Scripts\\python.exe -I measure_prompts.py
"""
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import env  # noqa: E402

V1 = env.ROOT / 'experiments/consolidated'
DATA = env.ROOT / 'data/processed'


def load(folder, name, alias):
    sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(alias, folder / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    sys.path.remove(str(folder))
    return module


def est(text):
    return math.ceil(len(text.encode('utf-8')) / 3)


def main():
    syn1 = load(V1, 'synthesis', 'syn_v1')
    sys.modules['synthesis'] = syn1
    rv1 = load(V1, 'review', 'rv_v1')
    syn2 = load(HERE, 'synthesis', 'syn_v2')
    sys.modules['synthesis'] = syn2
    rv2 = load(HERE, 'review', 'rv_v2')
    rows = []
    for arm in ('consolidated-v1-standard', 'consolidated-v1-deep'):
        for q in sorted((DATA / arm).glob('H0*')):
            packet = json.loads((q / 'stages/evidence.json').read_text(encoding='utf-8'))
            draft = json.loads((q / 'stages/synthesis.json').read_text(encoding='utf-8'))['summary']
            ids = sorted(p['chunk_id'] for p in packet['passages'])
            s1 = est(syn1.build_prompt('q', packet['passages'], packet['notes'])) + est(json.dumps(syn1.synthesis_schema(ids)))
            s2 = est(syn2.build_prompt('q', packet['passages'], packet['notes'])) + est(json.dumps(syn2.synthesis_schema(ids)))
            r1 = est(rv1.build_prompt('q', draft, packet['passages'], packet['notes'], {})) + est(json.dumps(rv1.review_schema(ids, len(draft['claims']))[0]))
            r2 = est(rv2.build_prompt('q', draft, packet['passages'], packet['notes'], {})) + est(json.dumps(rv2.review_schema(ids, len(draft['claims']))[0]))
            rows.append({'arm': arm[16:], 'q': q.name, 'synthesis_v1': s1, 'synthesis_v2': s2, 'review_v1': r1, 'review_v2': r2})
    out = {}
    for arm in ('standard', 'deep'):
        sel = [r for r in rows if r['arm'] == arm]
        out[arm] = {k: statistics.median(r[k] for r in sel) for k in ('synthesis_v1', 'synthesis_v2', 'review_v1', 'review_v2')}
        out[arm]['synthesis_reduction'] = round(1 - out[arm]['synthesis_v2'] / out[arm]['synthesis_v1'], 3)
        out[arm]['review_reduction'] = round(1 - out[arm]['review_v2'] / out[arm]['review_v1'], 3)
    (HERE / 'prompt-sizes.json').write_text(json.dumps({'medians': out, 'rows': rows}, indent=1), encoding='utf-8')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()

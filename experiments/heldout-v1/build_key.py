"""Writes answer-key.md (for independent human review), rules.json, then seal.json over every frozen file."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
FROZEN = ['questions.json', 'references.json', 'rules.json', 'answer-key.md', 'build_set.py', 'build_key.py']

RULES = {
    'version': 'heldout-v1',
    'scoring_basis': 'experiments/measure/fresh-diagnostic-v1/rules.json definitions (complete, partial, false_abstention, '
                     'citation_support, point_attribution) apply unchanged.',
    'point_scoring': 'Each required point scores 1 (accurately published with an entailing citation), 0.5 (partly published, '
                     'e.g. one of two values), or 0. Equivalent passages that state the same fact count; document them.',
    'unsupported_claim': 'A published claim whose cited passages do not entail it (metric, unit, population, configuration, '
                         'scope). Counted separately from points, also within partial answers.',
    'misleading_claim': 'A published claim that is technically cited but misattributes scope, category or causation.',
    'arms': {'A': 'Baseline/B2 deployed (create_research, quality_check=True, table comparisons off, top_k 8)',
             'B': 'A + opt-in deterministic question decomposition (question_parts @ retrieval-v3 f6efa05; original + at '
                  'most 3 parts; round-robin merge; cap 14). Nothing else differs.'},
    'fixed': 'gpt-6.1-sol, effort low, 300 s timeout, ChatGPT login; same pinned B2 index; same frozen questions; synthesis '
             'and answer-quality review unchanged. No tuning of decomposition after freezing.',
    'decision_rule': {
        'prefer_B_only_if_all': [
            'B scores at least 2.0 more required points than A in total (out of 27), as source-reviewed',
            'B wins more questions than it loses on points',
            'B publishes no more unsupported or misleading claims than A',
            'B has no more abstentions (false or evidence-limited) than A',
            'B median total response time per question is at most 15 s above A, and B p90 at most 30 s above A'],
        'otherwise': 'Keep A as the default. A gain of 0.5 to 1.5 points is inconclusive: B stays opt-in, not integrated.',
        'execution_errors': 'Questions with an execution error in either arm are excluded pairwise and reported; if more '
                            'than 2 pairs are excluded the comparison is inconclusive.'},
    'review': 'Machine-assisted source review first; final scores require independent human review of answer-key.md and '
              'every published claim. Automated anchor screens are reported separately and never replace source review.'}


def main():
    recs = {}
    for line in INDEX.open(encoding='utf-8'):
        if line.strip():
            r = json.loads(line)
            recs[r['chunk_id']] = r
    refs = json.loads((HERE / 'references.json').read_text(encoding='utf-8'))
    out = ['# Held-out answer key (heldout-v1) - for independent human review', '',
           'Written before any model run on these questions; no retrieval was run to choose them. Papers were selected only',
           'from the 23 corpus papers never mentioned in any prior question, reference, label, test or live-run file.',
           'Reviewer: for each point, confirm the expected statement is entailed by the quoted passage, then sign below.', '']
    for ref in refs:
        out += [f"## {ref['id']} ({ref['category']})", '', f"**Question.** {ref['question']}", '']
        for point in ref['required_points']:
            out += [f"- **{point['point_id']}** {point['expected']}",
                    f"  - Anchors (any one group suffices): {point['anchors']}"]
        cited = list(dict.fromkeys(c for p in ref['required_points'] for g in p['anchors'] for c in g))
        out += ['', '**Source passages (verbatim from the pinned index):**', '']
        for cid in cited:
            r = recs[cid]
            out += [f"> `{cid}` ({r.get('title', '')[:80]}; {r.get('section') or ''})", '>',
                    '> ' + ' '.join(r['text'].split()), '']
        out += ['Reviewer agrees: [ ] yes  [ ] no, note: ______', '']
    (HERE / 'answer-key.md').write_text('\n'.join(out), encoding='utf-8')
    (HERE / 'rules.json').write_text(json.dumps(RULES, indent=1, ensure_ascii=False), encoding='utf-8')
    seal = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in FROZEN}
    seal['index_parents_sha256'] = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    (HERE / 'seal.json').write_text(json.dumps(seal, indent=1), encoding='utf-8')
    print(json.dumps(seal, indent=1))


if __name__ == '__main__':
    main()

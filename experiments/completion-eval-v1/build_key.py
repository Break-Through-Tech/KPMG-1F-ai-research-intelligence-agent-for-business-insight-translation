"""Writes answer-key.md, rules.json, then seal.json over every frozen file (completion-eval-v1)."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
FROZEN = ['questions.json', 'references.json', 'rules.json', 'answer-key.md', 'OVERLAP.md', 'build_set.py', 'build_key.py']

RULES = {
    'version': 'completion-eval-v1',
    'arms': {
        'A': 'Baseline/B2 unchanged (create_research, quality_check=True, table comparisons off, top_k 8, gpt-6.1-sol low); '
             'one run per question; outputs saved.',
        'B': 'The SAME saved A answers passed through experiments/baseline-completion/completion.py exactly as frozen '
             '(sha256 recorded in seal.json). A answers are never regenerated; only completion calls are made.'},
    'point_scoring': 'Each required point scores 1 (accurately published with an entailing citation), 0.5 (partly published), '
                     'or 0. Equivalent passages stating the same fact count and are documented. Facts may appear in claims '
                     'or in cited limitations. Total 41 points.',
    'published_vs_inferred': 'Required points are published findings, including implications the authors themselves state. '
                             'A business implication the system infers must be presented as an interpretation or qualified '
                             'inference grounded in cited findings; presenting it as a finding is a misleading claim.',
    'added_claim_audit': 'Every claim added by B is checked for: correct numbers against its quote; exact quotes present in the '
                         'cited passage; correct chunk citations; duplication of an existing claim; unsupported or misleading '
                         'interpretation. The audit also confirms every A claim and limitation is still present and unchanged.',
    'detection_metrics': {
        'omitted_available': 'A required point scored below 1 in A while its anchor (or an equivalent passage) was in the A packet.',
        'trigger_recall': 'omitted_available points in triggered questions / all omitted_available points.',
        'recovery': 'omitted_available points whose score rose in B / omitted_available points in triggered questions.',
        'missed_omissions': 'omitted_available points in questions that never triggered (listed individually).'},
    'decision_rule': {
        'integrate': 'All of: B >= A + 2.0 points; zero unsupported or misleading added claims; zero A claims or limitations '
                     'removed or altered; zero duplicate added claims; median extra latency on triggered questions <= 45 s.',
        'leave_experimental': 'Zero unsupported or misleading added claims and zero removals, but the integrate bar is not met '
                              '(gain below 2.0 points, or a duplicate, or latency above the bound).',
        'abandon': 'Any unsupported or misleading added claim, any removed or altered A content, or no point recovered on any '
                   'triggered question.',
        'execution_errors': 'A questions with an execution error are excluded from both arms and reported; a completion call '
                            'error leaves the A answer unchanged (counted as no recovery).'},
    'fixed': 'No change to questions, key, rules, completion code or Baseline after sealing. Same model and index for all calls.',
    'review': 'AI-assisted key review and machine-assisted scoring; independent human verification remains outstanding.'}


def main():
    recs = {}
    for line in INDEX.open(encoding='utf-8'):
        if line.strip():
            r = json.loads(line)
            recs[r['chunk_id']] = r
    refs = json.loads((HERE / 'references.json').read_text(encoding='utf-8'))
    out = ['# Completion evaluation answer key (completion-eval-v1) - for independent human review', '',
           'Written before any model run on these questions; no retrieval was run to choose them. Required points are',
           'published findings (including implications the authors state). Inferred business implications are not points.',
           'Reviewer: confirm each expected statement is entailed by the quoted passage, then tick.', '']
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
    completion = HERE.parent / 'baseline-completion' / 'completion.py'
    seal['completion_py_sha256'] = hashlib.sha256(completion.read_bytes()).hexdigest()
    seal['index_parents_sha256'] = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    (HERE / 'seal.json').write_text(json.dumps(seal, indent=1), encoding='utf-8')
    print(json.dumps(seal, indent=1))


if __name__ == '__main__':
    main()

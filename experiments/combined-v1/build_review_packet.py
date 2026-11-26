"""Writes REVIEW-PACKET.md: every required point with the full text of each anchor passage, for Codex review and human
sign-off. Reads the sealed files only (verifies the seal first); changes nothing that is sealed."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
seal = json.loads((HERE / 'seal.json').read_text(encoding='utf-8'))
for name, digest in seal.items():
    path = BUNDLE if name == 'index_parents_sha256' else HERE / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'sealed file changed: {name}'
rows = {}
for line in BUNDLE.open(encoding='utf-8'):
    r = json.loads(line)
    rows[r['chunk_id']] = r
refs = json.loads((HERE / 'references.json').read_text(encoding='utf-8'))
coverage = json.loads((HERE / 'offline-coverage.json').read_text(encoding='utf-8'))['per_question']['baseline']

out = ['# fresh-business-v1: answer-key review packet', '',
       'For Codex review and human sign-off. For each required point, check:',
       '',
       '1. The expected answer is stated by the anchor passage(s), with no number, subject, metric, condition or qualifier changed.',
       '2. The question actually asks for it.',
       '3. It is a published finding, not an inference.',
       '4. Alternative anchors are genuinely equivalent.',
       '',
       'Record decisions in REVIEW-STATUS.md. **Any change to the key requires rebuilding and resealing before any run.** '
       'The questions, the selected evidence budget (6k skip-fit) and the acceptance criteria stay frozen.', '',
       '"In packet" shows whether the anchor group is fully inside the offline 6k skip-fit packet (Baseline route) and the '
       'top-8 packet. It is for information only and must not influence the review. It was computed before the review '
       'corrections, against the first anchor only (the G06.2 alternative c0004 was added afterwards).', '',
       '**Corrections applied after the first review (resealed):**', '',
       '- **G09.4** separates monetary cost (not reported) from computational cost proxies (reported, citable).',
       '- **G06.2** accepts either source figure (60% from the introduction, c0004; 66% from the results, c0019) when it is '
       'correctly attributed, and credits answers that identify the inconsistency.',
       '- **G05.5** keeps the source limitation: the dispute-resolution mechanism helps only "to a certain degree" and still '
       '"falls short of the upper bound". Without that limitation, at most 0.5.',
       '- **G09.4 partial credit:** proxies alone, without saying monetary cost is not reported, score 0.5.',
       '- **G04.5 and G10.4** each have two components; both are required for 1, and one alone scores 0.5.',
       '', '**Codex review corrections (third reseal):**', '',
       '- **G03.5** names both target models (c0019). The ASR pairs are reported as the source gives them; mapping a pair to a model '
       'or metric as fact is unsupported. It adds the effort/cost component: no compute cost is established for adversarial '
       'tuning (LoRA, c0015), and the 20-minute GCG figure is a prior method\'s cost.',
       '- **G06.2**: 60% and 66% are compatible lower bounds. The group statistics (means and SDs) require c0019.',
       '- **G07.3** adds methods anchor c0014 (finstat2sql is a fine-tuned Qwen 2.5 Coder per size).',
       '- **G08.4** accepts the calculated 0.4 points (~0.65% relative) or the paper\'s "0.8%" attributed to the paper.',
       '- **G09.4** limits the fabrication rule to monetary prices not supported by the study.',
       '', 'See REVIEW-STATUS.md.', '']
for ref in refs:
    cov = coverage[ref['id']]
    out += [f"## {ref['id']} ({ref['type']})", '', f"**Question.** {ref['question']}", '']
    for point in ref['required_points']:
        out += [f"### {point['point_id']}", '', f"**Expected:** {point['expected']}", '']
        if not point['anchors']:
            out += ['**No anchor (monetary cost).** No passage gives a monetary per-query cost. The computational cost '
                    'proxies an answer may correctly cite are quoted below for reference. A dollar or per-query price figure '
                    'scores 0 and counts as a misleading claim (rules.json, evidence_absent_points). Reviewer: confirm that no '
                    'passage in the 100-paper corpus gives a monetary per-query cost for LegalMALR.', '']
            for cid in ('2601.17692v1_c0035', '2601.17692v1_c0048', '2601.17692v1_c0052'):
                r = rows[cid]
                out += [f"> `{cid}` · {r['title']} · {r.get('section')} (cost proxy, not a required anchor)", '>',
                        f"> {' '.join(r['text'].split())}", '']
            continue
        flags = (f"in skip-fit packet: {'yes' if point['point_id'] in cov['skipfit6k']['points'] else 'no'}; "
                 f"in top-8 packet: {'yes' if point['point_id'] in cov['top8']['points'] else 'no'}")
        out += [f"*{flags}*", '']
        for i, group in enumerate(point['anchors'], 1):
            label = 'Anchor' if len(point['anchors']) == 1 else f'Alternative {i}'
            out.append(f"**{label}:** {' + '.join(group)}{' (all rows required together)' if len(group) > 1 else ''}")
            out.append('')
            for cid in group:
                r = rows[cid]
                text = ' '.join(r['text'].split())
                out += [f"> `{cid}` · {r['title']} · {r.get('section') or 'table'}", '>', f"> {text}", '']
    out.append('')
(HERE / 'REVIEW-PACKET.md').write_text('\n'.join(out), encoding='utf-8')
print('points', sum(len(r['required_points']) for r in refs), 'chars', sum(len(x) for x in out))

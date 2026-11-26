"""Unseen S2 vs S2-R2 question set (8 questions, 36 points). Authored from validation-bundle passages ONLY, using
facts that no existing key point uses; no engine, retriever or model has been run on these questions. Every anchor
group (alternatives included) is checked to exist and to contain every required fact string.

Distribution: U1-U3 named two-paper; U4-U6 unnamed multi-part single-paper; U7 simple control; U8 evidence-limit control.
Points: 5 each for U1-U6, 3 each for U7-U8 -> 36.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[2] / 'data/processed/validation-bundles/fresh-v4-110/parents.jsonl'
P = {'trace': '2611.01409v1', 'cmt': '2611.02018v1', 'eria': '2611.01394v1', 'harness': '2611.01415v1',
     'halo': '2611.02134v1', 'pguard': '2611.02791v2', 'medpsy': '2611.02011v2', 'ecgjev': '2611.02041v1',
     'dp': '2611.01411v1', 'matmoe': '2611.01704v1'}


def a(paper, local):
    return f'{P[paper]}_{local}'


SET = [
 ('U1', 'named-cross',
  'A multinational bank needs chatbot safety screening in many languages. How did HaloGuard 2.0 and PGuard perform on '
  'multilingual safety benchmarks, where are their weaknesses by language, and what drove HaloGuard\'s multilingual '
  'improvement?',
  [('U1.1', 'HaloGuard 2.0-Poly-0.8B reaches 83.1 response F1 on PolyGuardPrompts (17 languages), 5.0 points above '
            'Qwen3Guard-Gen-4B (78.1) and 7.3 above the strongest streaming guard, Qwen3Guard-Stream-8B (75.8).',
    [[a('halo', 'c0032')]], ['83.1', '78.1', '75.8'], 'published'),
   ('U1.2', 'Weakness by language: Thai (73.9) and especially Hindi (64.2) fall well below English; Hindi FNR reaches '
            '22.2 versus 4.6 for English.',
    [[a('halo', 'c0033')]], ['64.2', '22.2', '4.6'], 'published'),
   ('U1.3', 'The multilingual gain came mainly from fewer misses: false negatives fell 76% (1,531 to 360) while false '
            'positives fell 26% (1,999 to 1,482).',
    [[a('halo', 'c0033')]], ['76%', '1,531', '360'], 'published'),
   ('U1.4', 'PGuard on PolyGuardPrompts: PolyGuard-Qwen-7B leads query classification (0.869); among native guardrails '
            'PGuard-ema leads both stages, 0.835 for queries (Qwen3.5-9B) and 0.766 for responses (Qwen3-8B).',
    [[a('pguard', 'c0029')]], ['0.869', '0.835', '0.766'], 'published'),
   ('U1.5', "Both report PolyGuardPrompts results, but different measures and settings (HaloGuard-Poly response F1 "
            "83.1 macro-averaged over 17 languages; PGuard response F1 0.766 on Qwen3-8B with its own token sampling, "
            "calibration and strict-mode settings); a matched protocol is not demonstrated, so any comparison must be "
            "qualified. Presenting an unqualified ranking of one guard over the other as established is misleading.",
    [[a('halo', 'c0032'), a('pguard', 'c0029'), a('pguard', 'c0026')]], ['83.1', '0.766'], 'published')]),
 ('U2', 'named-cross',
  'A device maker plans to run language models on phones and small boards. What do MedPsy and MatMoE report about the '
  'limits of very low-bit precision, response-length or token efficiency, speed on CPUs and GPUs, and memory '
  'offloading?',
  [('U2.1', 'MedPsy: below 4 bits the models degrade; collapse at IQ3_XXS (-5.56 at 4B, -12.46 at 1.7B), and the authors '
            'do not recommend any sub-4-bit variant of the 1.7B model for medical use.',
    [[a('medpsy', 'c0019')]], ['IQ3_XXS', '12.46', 'sub-4-bit'], 'published'),
   ('U2.2', 'MedPsy-4B cuts average response length 3.2x (909 vs 2,953 tokens) and keeps 96.6% of its closed-ended score '
            'with a 300-token thinking cap.',
    [[a('medpsy', 'c0017')]], ['909', '2,953', '96.6%'], 'published'),
   ('U2.3', 'MatMoE multi-thread CPU speedups over llama.cpp of 1.5x, 3.7x and 2.9x (Qwen, DeepSeek, OLMoE); Qwen gains '
            'least because of its larger share of shared experts.',
    [[a('matmoe', 'c0021')]], ['3.7', '2.9', 'shared experts'], 'published'),
   ('U2.4', 'MatMoE GPU TPOT curves are relatively flat because low-bit weights are first converted to INT8 before dp4a '
            'execution, so different precisions cost about the same (a kernel limitation).',
    [[a('matmoe', 'c0021')]], ['INT8', 'dp4a'], 'published'),
   ('U2.5', 'Offloading: when an expert moves from 2-bit to 4-bit, HOBBIT loads a separate 4-bit copy from SSD whereas '
            'MatMoE loads only the two additional bitplanes, reducing SSD-to-DRAM traffic.',
    [[a('matmoe', 'c0024')]], ['HOBBIT', 'bitplanes'], 'published')]),
 ('U3', 'named-cross',
  'A cardiology software vendor is weighing RAG-TRACE and ECGJev. How did the two language models in RAG-TRACE differ '
  'in their failures and in how verification treated them, what happened to agreement with cardiologist statements, '
  'and what do ECGJev\'s ablations and small-cohort results show?',
  [('U3.1', "Both models, for 1: GPT-4.1-mini had 647 withdrawals (639 unchecked cards, 8 failed predicates, 7 of which "
            "Uni-G rejected) and kept 268 of 269 Uni-G-supported applications; Qwen3-8B had 880 unchecked applications "
            "and 211 failed predicates (Uni-G rejected 203) and kept 274 of 282. A qualitative contrast without counts "
            "scores 0.5.",
    [[a('trace', 'c0013')]], ['647', '268 of 269', '880', '211', '274 of 282'], 'published'),
   ('U3.2', 'Uni-G rejection after 12SL withdrawal fell from 5.3% to 4.6% for GPT-4.1-mini and from 20.8% to 4.7% for '
            'Qwen3-8B.',
    [[a('trace', 'c0013')]], ['20.8%', '4.7%'], 'published'),
   ('U3.3', 'Keyword retrieval raised statement mismatch with cardiologist codes from 7.5% to 24.9% (GPT-4.1 mini) and '
            'from 1.6% to 34.1% (Qwen3-8B); the two-algorithm rule reduced these to 22.2% and 19.6%.',
    [[a('trace', 'c0014')]], ['24.9%', '34.1%', '19.6%'], 'published'),
   ('U3.4', 'ECGJev ablation: spectrograms alone lower macro-F1 by 15.89 points; waveforms carry the primary signal.',
    [[a('ecgjev', 'c0009')]], ['15.89'], 'published'),
   ('U3.5', 'On the small PTB cohort, generative baselines collapse to 13.23-14.82% F1 while ECGJev reaches 35.02%.',
    [[a('ecgjev', 'c0008')]], ['35.02%', '13.23'], 'published')]),
 ('U4', 'unnamed-multipart',
  'A localization vendor is studying a recent Chinese-English benchmark for translating social-media comments with their '
  'conversation context. How was the benchmark built, how was its automatic judge trained and validated, and how many '
  'model configurations were evaluated?',
  [('U4.1', 'Built from 40K contextualized social-media comments down to 572 manually verified examples.',
    [[a('cmt', 'c0004')]], ['40K', '572'], 'published'),
   ('U4.2', "The judge is a Qwen3.5-27B model built from a 200K-pair collection (160K labelled by Gemini 3.1 Pro, 40K "
            "manually annotated), with development sets held out.",
    [[a('cmt', 'c0010')]], ['200K', '160K', '40K'], 'published'),
   ('U4.3', 'Training: SFT on the Gemini-labelled data, continued SFT on the human-labelled data, then GRPO from 20K '
            'human-labelled examples (10K still-challenging plus 10K correctly judged).',
    [[a('cmt', 'c0010')]], ['GRPO', '20K'], 'published'),
   ('U4.4', 'Validation: a separate, approximately score-balanced 432-pair human-annotated set, sampled from 825 '
            'candidates (25 per configuration), reporting binary accuracy, Cohen\'s kappa, four-way accuracy and Spearman.',
    [[a('cmt', 'c0013')]], ['432', '825'], 'published'),
   ('U4.5', '33 model configurations were evaluated, including thinking and non-thinking modes of the same model.',
    [[a('cmt', 'c0012')]], ['33'], 'published')]),
 ('U5', 'unnamed-multipart',
  'An AI platform team read about compiling agent instructions into small activation shifts on a frozen model instead of '
  'sending long prompts. Do the compiled behaviours transfer to new tasks, how much do they help harness search, do they '
  'still help when the harness is removed, how much of the gain comes from prompt-phase injection, and do '
  'instructions that reduce task performance compile too?',
  [('U5.1', 'Zero-shot transfer: 5 of 7 preregistered source-to-target pairs transfer positively; decomposition transfers '
            'to ARC with +22.0 points.',
    [[a('harness', 'c0017')]], ['five pairs', '+22.0'], 'published'),
   ('U5.2', 'At a matched budget, text-space search reaches +0.430 test gain versus +0.624 for latent library search; the '
            'compiled library accounts for the 1.45x multiplier.',
    [[a('harness', 'c0018')]], ['+0.430', '+0.624', '1.45'], 'published'),
   ('U5.3', 'With the harness removed, the shift still delivers +9.5 points on ToolHop.',
    [[a('harness', 'c0019')]], ['+9.5'], 'published'),
   ('U5.4', 'Prompt positions contribute +8.4 to +8.5 points, about 60% of the total.',
    [[a('harness', 'c0019')]], ['60%'], 'published'),
   ('U5.5', "Yes: a verification harness that hurts GSM8K by -10.7 points in explicit form distills to -6.7 points in "
            "compiled form (M1); 'harmful' here means detrimental to task accuracy, not unsafe content.",
    [[a('harness', 'c0016')]], ['-10.7', '-6.7'], 'published')]),
 ('U6', 'unnamed-multipart',
  'A privacy engineering team is reviewing a recent audit of differentially private fine-tuning on quantized backbones. '
  'What practical recommendations does it make, how often did the cross-record coupling actually occur on natural text, '
  'how efficient is the proposed record-owned dispatch, and how broad is the natural-data evidence?',
  [('U6.1', 'Recommendations, any two of: validate data dependence with a batch-invariance test (Opacus\'s validator '
            'accepted OPT-125M at every batch size although batching exceeded the bound); treat physical batch size as '
            'privacy-relevant; derive routing from public calibration or released state; record a runtime manifest.',
    [[a('dp', 'paragraph_49942c274f0dcff0_0')]], ['batch-invariance', 'runtime manifest'], 'published'),
   ('U6.2', 'At batch 2, 4.8% of record-layer pairs in outlier-carrying layers computed a column in FP16 only because '
            'another record crossed the threshold; 20.1% at batch 16.',
    [[a('dp', 'c0013')]], ['4.8%', '20.1%'], 'published'),
   ('U6.3', 'Only 3-7 outlier columns per batch are owned by a single record; most outlier columns are shared by every '
            'record.',
    [[a('dp', 'c0013')]], ['3–7'], 'published'),
   ('U6.4', "The proposed record-owned dispatch keeps the same INT8 and FP16 GEMMs as batched LLM.int8; an optimized "
            "grouped kernel would skip 1.5-7.5% of correction work on the OPT-125M traces (not a measured end-to-end "
            "speedup; the kernel is not yet implemented).",
    [[a('dp', 'c0008')]], ['1.5–7.5%'], 'published'),
   ('U6.5', 'Scope: natural-data evidence covers one model (OPT-125M), one corpus (TinyStories) and one baseline batch; '
            'multi-step training under Poisson sampling is not audited.',
    [[a('dp', 'paragraph_5ef5bfd9c0173705_0')]], ['OPT-125M', 'TinyStories', 'Poisson'], 'published')]),
 ('U7', 'simple-control',
  'What clinical EEG data did the ERIA study use for its internal evaluation, how was it split, and who authored '
  'the matched reports under which guidelines?',
  [('U7.1', 'A private dataset of 200 routine clinical EEG studies with matched clinically generated reports.',
    [[a('eria', 'paragraph_849fe3c6168d998d_0')]], ['200 routine clinical EEG studies'], 'published'),
   ('U7.2', 'Split at the recording level into 50 optimization, 50 validation and 100 protected test cases.',
    [[a('eria', 'paragraph_849fe3c6168d998d_0')]], ['50 optimization', '100 protected test'], 'published'),
   ('U7.3', 'Reports were authored by board-certified epileptologists following ACNS guidelines.',
    [[a('eria', 'paragraph_849fe3c6168d998d_0')]], ['board-certified epileptologists', 'ACNS'], 'published')]),
 ('U8', 'evidence-limit-control',
  'Does HaloGuard 2.0 handle chain-of-thought reasoning traces and refusal labelling, and what harmful-response miss rate '
  'should an insurer expect on its own claims chatbot?',
  [('U8.1', 'Reasoning traces: HaloGuard 2.0 was trained only on final responses; covering chain-of-thought traces needs '
            'reasoning-trace training data and is left to a future release.',
    [[a('halo', 'c0036')]], ['final responses', 'reasoning-trace'], 'published'),
   ('U8.2', 'It labels harm only, not refusals: a refusal is safe, and a response that refuses and then complies is unsafe '
            'from its onset.',
    [[a('halo', 'c0036')]], ['refuses and then complies'], 'published'),
   ('U8.3', "Not established: evaluation covers six English response-safety benchmarks and PolyGuardPrompts, and the "
            "authors advise calibrating each model's threshold to its own error profile; no insurer or claims-chatbot "
            "miss rate is reported. Presenting an invented rate as a study result is misleading.",
    [[a('halo', 'c0003'), a('halo', 'c0038')]], ['six English response-safety benchmarks', 'error profile'],
    'evidence_limit')]),
]

RULES = {
    'version': 'unseen-r2', 'points': sum(len(q[3]) for q in SET), 'max_score': sum(len(q[3]) for q in SET),
    'completeness': 'Each required point scores 1 (accurately published with an entailing citation), 0.5 (partly) or 0. '
                    'Only findings and cited limitations count. Evidence-limit point U8.3 scores 1 only when a cited '
                    'limitation states the item is not established with the study scope; a fabricated rate scores 0 and '
                    'is a misleading claim. U6.1 needs any two recommendations for 1.',
    'misleading_probes': 'U1.5 (an unqualified ranking of HaloGuard over PGuard, or the reverse, presented as '
                         'established); U2.4 (presenting MatMoE GPU speedups as precision-dependent; 1.2-1.3x GPU '
                         'speedups do exist); U8.3 (presenting an invented insurer miss rate as a study result).',
    'safety': 'Zero citation-grounding failures, misleading/fabricated claims, numerical errors, and uncited statements '
              'that a paper does not report something.',
}


def norm(s):
    return ' '.join(s.replace(chr(92), '').split())


def main():
    rows = {}
    for line in BUNDLE.read_text(encoding='utf-8').splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r['chunk_id']] = r
    used = set()
    for ref in json.loads((HERE.parent / 'fresh-v4/references.json').read_text(encoding='utf-8')):
        for p in ref['required_points']:
            used.update(c for g in p['anchors'] for c in g)
    errors, overlap = [], []
    for _qid, _t, _q, points in SET:
        for pid, _e, groups, facts, _k in points:
            for group in groups:
                if any(c not in rows for c in group):
                    errors.append(f'{pid}: anchor missing {group}')
                    continue
                overlap += [(pid, c) for c in group if c in used]
                text = norm(' '.join(rows[c]['text'] for c in group))
                for f in facts:
                    if norm(f) not in text:
                        errors.append(f'{pid}: fact {f!r} not in {group}')
    if errors:
        raise SystemExit('\n'.join(errors))
    (HERE / 'questions.json').write_text(json.dumps([{'id': q[0], 'type': q[1], 'question': q[2]} for q in SET],
                                                    indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'references.json').write_text(json.dumps([{'id': q[0], 'type': q[1], 'question': q[2], 'required_points': [
        {'point_id': p[0], 'expected': p[1], 'anchors': p[2], 'type': p[4]} for p in q[3]]} for q in SET],
        indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'rules.json').write_text(json.dumps(RULES, indent=1), encoding='utf-8')
    md = ['# Unseen S2 vs S2-R2: answer key', '', f"8 questions, {RULES['max_score']} points (max score). Authored from "
          'passages only; no engine has seen these questions.', '']
    for qid, t, q, points in SET:
        md += [f'## {qid} ({t})', '', q, ''] + [f"- **{p[0]}** ({p[4]}) {p[1]}  \n  anchors: "
                                                + ' | '.join('+'.join(g) for g in p[2]) for p in points] + ['']
    (HERE / 'answer-key.md').write_text('\n'.join(md), encoding='utf-8')
    print(len(SET), 'questions,', RULES['max_score'], 'points; anchors and facts verified')
    print('anchor chunks also used by an existing fresh-v4 key (different facts):', overlap)


if __name__ == '__main__':
    main()

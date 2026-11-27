"""fresh-v3: the final fresh validation set (8 questions, 38 required points). NOT run.

Papers: the 8 corpus papers that never appeared in any question, reference, key, case, label, fixture or test file (the
last clean subset of the 100-paper corpus): 2603.15712v1 (RAG catalyst discovery), 2502.17874v2 (MARASON),
2406.09923v2 (CliBench), 2410.01553v2 (MedQA-CS), 2504.15330v1 (Med-CoDE), 2606.04500v1 (SANE), 2404.08309v1
(subtoxic questions), 2402.09748v1 (LLM compression survey).
Authored by reading the bundle passages only. No engine, retriever or model was run on these questions before sealing.
Every anchor group (alternatives included) must exist and contain every must-contain string (checked here), so an
alternative anchor can only stand in for a point it fully supports. Points of type 'evidence_limit' require the answer
to say the corpus does not establish something; a fabricated value scores 0 and is a misleading claim.
Key drafted with AI assistance (Claude); one focused independent review and human sign-off are required before any run.
    python -I build_set.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
P = {'hea': '2603.15712v1', 'marason': '2502.17874v2', 'clibench': '2406.09923v2', 'medqacs': '2410.01553v2',
     'medcode': '2504.15330v1', 'sane': '2606.04500v1', 'subtoxic': '2404.08309v1', 'survey': '2402.09748v1'}
LIMIT = 'evidence_limit'


def a(paper, cid):
    return f'{P[paper]}_{cid}'


Q = [
 ('J01', 'single-paper; numerical; business', 'A chemicals client is exploring AI-assisted catalyst discovery. What did the '
  'retrieval-augmented high-entropy-alloy catalyst study do, what did it report on stability, cost and catalytic '
  'performance, and what limits apply before the client invests in laboratory work?', [
   ('J01.1', 'GPT-4 generates candidate catalysts with retrieval over a database of 50,000+ known materials, '
             'grounding high-throughput design.', [[a('hea', 'c0000')]], ['GPT-4', '50,000+']),
   ('J01.2', 'Over 250 candidates with an 82% thermodynamic stability rate; 68% achieved under $100/kg cost with metallic '
             'conductivity (band gap < 0.1 eV) and mechanical stability (B/G > 1.75).', [[a('hea', 'c0000')]],
    ['250', '82%', '68%']),
   # Review correction 1: the 15-20% variant is anchored (c0002), and c0020 calls 15-20% a target, not a result.
   ('J01.3', 'The best catalyst (Fe0.2Co0.2Ni0.2Ir0.1Ru0.3) reached a 0.285 V limiting potential, reported in the abstract '
             'as a 25% improvement over IrO2; Cr0.2Fe0.2Co0.3Ni0.2Mo0.1 balanced performance and cost at $18/kg. '
             'The contributions list states a 15-20% improvement over IrO2 baselines, which the conclusion describes as '
             'the improvement target. Either figure scores when attributed to where the paper states it; noting the '
             'difference is credited.', [[a('hea', 'c0000'), a('hea', 'c0002'), a('hea', 'c0020')]],
    ['0.285V', '25%', '$18/kg', '15-20%', 'improvement target']),
   ('J01.4', '78% of generated catalysts cluster near the theoretical activity optimum (volcano analysis), and the system '
             'reports 200x computational efficiency versus traditional high-throughput screening.', [[a('hea', 'c0000')]],
    ['78%', '200']),
   ('J01.5', 'Limitations: computational validation only, ideal surfaces assumed, synthesis feasibility unaddressed.',
    [[a('hea', 'c0010')]], ['computational validation only', 'ideal surfaces', 'synthesis feasibility'])]),
 ('J02', 'single-paper; numerical/table', 'A pharmaceutical analytics client is considering retrieval-augmented mass '
  'spectrum simulation. What did MARASON achieve, how does it use retrieved molecules, on what data was it trained, and '
  'when does retrieval actually help?', [
   ('J02.1', 'MARASON reached 28% top-1 accuracy versus 19% for the non-retrieval state of the art, and outperformed naive '
             'retrieval-augmented generation and traditional graph matching.', [[a('marason', 'c0000')]], ['28%', '19%']),
   ('J02.2', 'It retrieves structures with known reference spectra from the NIST (2020) training data and matches '
             'reference and target fragments with neural graph matching (learned affinities rather than fixed ones).',
    [[a('marason', 'c0008'), a('marason', 'c0000')]], ['NIST', 'match', 'learn affinity metrics']),  # correction 5
   ('J02.3', 'Training data: NIST (2020), 530,640 HCD spectra and 25,541 unique structures, with a structurally disjoint '
             '80%-10%-10% split.', [[a('marason', 'c0025')]], ['530,640', '25,541', '80%-10%-10%']),
   # Review correction 6: the authors' switching rule uses Tanimoto 0.2, not 0.3.
   ('J02.4', 'Retrieval brings a significant gain when the reference Tanimoto similarity exceeds 0.3 (e.g. 0.824 vs 0.784 '
             'cosine similarity at 0.9-1.0) and no significant gain at 0.1-0.3; the authors suggest using standard MARASON '
             'above 0.2 and the non-RAG version otherwise. Stating "non-RAG below 0.3" scores at most 0.5.',
    [[a('marason', 'c0034'), a('marason', 'table_dda9dc168318c057_1'), a('marason', 'table_dda9dc168318c057_2')]],
    ['larger than 0.3', '0.824', '0.784', '>0.2'])]),
 ('J03', 'cross-paper', 'A hospital network wants to benchmark LLMs for clinical decision support. What do CliBench and '
  'MedQA-CS evaluate, how did leading models perform, and what limits apply to using these results?', [
   ('J03.1', 'CliBench is built from MIMIC-IV real clinical cases and covers four decisions: diagnosis, procedures, lab '
             'test orders and prescriptions.', [[a('clibench', 'c0000'), a('clibench', 'c0007')]],
    ['MIMIC IV', 'diagnosis, procedure, lab test order, and prescription']),
   ('J03.2', 'Two components, both required for 1: (a) state-of-the-art LLMs do not perform well on diagnosis; GPT-4o is '
             'the best model, 7.37 points ahead of the best open model on full-code F1; (b) procedures and lab orders are '
             'much worse, with near-zero performance for lowest-level procedure decisions.',
    [[a('clibench', 'c0021'), a('clibench', 'c0023')]], ['7.37', 'near-zero']),
   ('J03.3', 'Domain-specialized medical models did not outperform (or only slightly improved over) their base models and '
             'fell behind general instruction-tuned models.', [[a('clibench', 'c0021')]],
    ['Domain-specialized models do not work']),
   ('J03.4', 'MedQA-CS is an OSCE-style framework with LLM-as-medical-student and LLM-as-examiner tasks; student scores '
             'ranged from 48.44 (GPT-3.5) to 62.35 (Claude-3.5-Sonnet), far below the 90+ scores on knowledge benchmarks '
             'such as MedQA.', [[a('medqacs', 'c0000'), a('medqacs', 'c0021')]], ['48.44', '62.35', 'LLM-as-medical-student']),
   ('J03.5', 'MedQA-CS limitation: a small USMLE Step 2 CS-derived sample of mostly common conditions, lacking pediatrics, '
             'psychiatry and rare diseases.', [[a('medqacs', 'c0027')]], ['pediatrics', 'rare diseases'])]),
 ('J04', 'cross-paper; misleading-evidence probe', 'A health insurer wants to use an LLM to grade other LLMs\' medical '
  'answers. What do MedQA-CS and Med-CoDE show about how reliable LLM-based evaluators are, and where do they fall short?', [
   ('J04.1', 'MedQA-CS: GPT-4 as examiner correlated with experts at Pearson r 0.90 (information gathering), 0.92 '
             '(physical exam) and 0.78 (diagnosis), but only 0.47 for the closure section.', [[a('medqacs', 'c0018')]],
    ['0.90', '0.92', '0.78', '0.47']),
   ('J04.2', 'MedQA-CS: a fine-tuned LLaMA 3.1-8B judge matched GPT-4 on information gathering (0.9289) and physical exam '
             '(0.93) but stayed below 0.3 on diagnosis versus GPT-4\'s 0.78.', [[a('medqacs', 'c0020')]],
    ['0.9289', 'below 0.3']),
   ('J04.3', 'Med-CoDE is a critique-based framework: a fine-tuned critique generator and classifier assign four levels of '
             'disagreement with the ground truth, trained on 38,819 GPT-4-generated critiques.',
    [[a('medcode', 'c0007'), a('medcode', 'c0016'), a('medcode', 'c0003')]],  # correction 2: classifier in c0003
    ['38,819', 'four levels of disagreement', 'classifying']),
   ('J04.4', 'In the human evaluation of disagreement classification, Med-CoDE scored 71.72% accuracy versus 78.12% for '
             'GPT-3.5. Stating that Med-CoDE outperformed GPT-3.5 on this evaluation is a misleading claim.',
    [[a('medcode', 'table_de629a5f57790c34_1'), a('medcode', 'table_de629a5f57790c34_2')]], ['78.12', '71.72']),
   ('J04.5', 'About 240 of 265 (91%) GPT-4-generated critique samples were judged accurate: this is the quality of the '
             'training data, not Med-CoDE\'s accuracy; presenting it as the framework\'s accuracy is a misleading claim.',
    [[a('medcode', 'c0015')]], ['240 out of the 265'])]),
 ('J05', 'single-paper; numerical/table; partially unanswerable', 'A biotech client wants natural-language access to its '
  'compound-screening database. What did the SANE study show about a few-shot LLM querying a microscopy database - '
  'setup, accuracy and failure modes - and how would it perform on the client\'s own proprietary chemistry database?', [
   ('J05.1', 'A 4-bit quantized Llama 3.1 in few-shot mode on one 48 GB A6000 GPU, with no training or fine-tuning; a '
             'three-stage pipeline checks context sufficiency, generates and executes SQL, and asks for clarification when '
             'context is missing.', [[a('sane', 'c0004'), a('sane', 'c0005'), a('sane', 'c0003')]],  # correction 3
    ['no training or fine-tuning', '48 GB', '4-bit']),
   ('J05.2', '97.2% overall accuracy on 572 queries (556 correct).', [[a('sane', 'table_de629a5f57790c34_7')]],
    ['572', '556', '97.2']),
   ('J05.3', 'Weakest categories: contextless 81.8% (18/22), multi-step 85.7% (6/7) and error queries 86.1% (31/36), '
             'versus 100% on simple queries (159/159).',
    [[a('sane', 'table_de629a5f57790c34_4'), a('sane', 'table_de629a5f57790c34_6'), a('sane', 'table_de629a5f57790c34_3'),
      a('sane', 'table_de629a5f57790c34_1')]], ['81.8', '85.7', '86.1', '100.0']),
   ('J05.4', 'Most failures come from wrong context-label prediction or omitted names, not wrong numerical values; '
             'ambiguous inputs lead to overly cautious clarification requests.',
    [[a('sane', 'c0009'), a('sane', 'c0000')]], ['wrong context label', 'clarification']),
   ('J05.5', 'Not established: performance on the client\'s different database is not reported; the study covers one '
             'constrained, domain-specific schema. Any accuracy figure for the client\'s database is fabricated.',
    [[a('sane', 'c0010')]], ['572 queries'], LIMIT)]),
 ('J06', 'single-paper; partially unanswerable', 'A bank\'s AI red team wants better ways to test chatbot jailbreak '
  'resistance. What are "subtoxic questions", what did the Gradual Attitude Change observations show, how does the paper '
  'propose to rank jailbreak prompts, and what jailbreak success rate should the bank expect against its own production '
  'chatbot?', [
   ('J06.1', 'Subtoxic questions are inherently harmless queries mistakenly identified as harmful because of their content '
             'composition (harmful content embedded in a benign question).', [[a('subtoxic', 'c0003')]],
    ['inherently harmless', 'mistakenly identified as harmful']),
   ('J06.2', 'Adding positive prompts to subtoxic questions gradually shifts GPT-3.5\'s responses through stages from firm '
             'refusal to a positive reply (Gradual Attitude Change).', [[a('subtoxic', 'c0005'), a('subtoxic', 'c0007')]],
    ['Gradual Attitude Change', 'GPT-3.5']),
   ('J06.3', 'Prompts are ranked by comparing their attitude effects on an evaluation question set, which the authors '
             'describe as more precise and efficient than success-rate-based measurement, with low variance.',
    [[a('subtoxic', 'c0010')]], ['success rate of jailbreaking', 'variance']),
   ('J06.4', 'Not established: the paper reports no jailbreak success rate for production chatbots (its observations '
             'concern GPT-3.5); any success-rate figure for the bank\'s chatbot is fabricated.',
    [[a('subtoxic', 'c0007')]], ['GPT-3.5'], LIMIT)]),
 ('J07', 'single-paper (survey); partially unanswerable', 'A client wants to deploy an LLM on resource-constrained '
  'hardware. What compression approaches does the survey cover, what makes compressing large language models different, '
  'how does it separate medium and large models, and how much will compression cut the client\'s inference cost?', [
   ('J07.1', 'Taxonomy: quantization, pruning, distillation, compact architecture design and dynamic networks.',
    [[a('survey', 'c0000')]], ['quantization, pruning, distillation, compact architecture design, dynamic networks']),
   ('J07.2', 'Two LLM-specific characteristics: fine-tuning or retraining is very costly, so tuning-free algorithms are '
             'explored; and LLMs emphasise versatility, so distillation focuses on preserving it.',
    [[a('survey', 'c0000')]], ['tuning-free', 'versatility']),
   ('J07.3', 'Medium models are around one billion parameters or fewer (e.g. BERT, GPT-2); large models have over one '
             'billion.', [[a('survey', 'c0006'), a('survey', 'c0003')]], ['one billion', 'such as BERT, GPT-2']),  # corr. 4
   ('J07.4', 'Example of the cost problem: a 10B model with float32 weights consumes 37GB of memory.',
    [[a('survey', 'c0001')]], ['37GB']),
   ('J07.5', 'Weight-only quantization cannot be integer-only: weights must be dequantized before multiplying with '
             'activations, adding computation overhead.', [[a('survey', 'c0016')]], ['dequantized']),
   ('J07.6', 'Not established: the survey reports no measured inference-cost saving for the client\'s deployment; any '
             'such figure is fabricated.', [[a('survey', 'c0000')]], ['algorithmic perspective'], LIMIT)]),
 ('J08', 'cross-paper', 'An R&D client wants to know where retrieval augmentation adds value in chemistry machine '
  'learning. What do the catalyst-discovery study and MARASON retrieve, how is the retrieved material used, and what '
  'evidence shows when retrieval helps?', [
   ('J08.1', 'The catalyst study retrieves k=20 relevant catalysts from its materials databases (Materials Project, NOMAD, '
             'OC20) to ground GPT-4 generation.', [[a('hea', 'c0006')]], ['k=20', 'NOMAD']),
   # Review correction 7: J08 asks what shows when retrieval helps; the catalyst study's evidence is its RAG ablation.
   ('J08.2', 'In the catalyst study\'s ablation, thermodynamic stability dropped to 23% without retrieval versus 82% with '
             'it (a 3.6x improvement).', [[a('hea', 'c0018')], [a('hea', 'c0020')]], ['23%', '82%']),
   ('J08.3', 'MARASON retrieves one reference structure and up to three reference spectra with collision energies, which '
             'are fed into the model.', [[a('marason', 'c0014')]], ['up to three reference spectra']),
   ('J08.4', 'MARASON\'s retrieval brings a significant gain only for similar-enough references (Tanimoto > 0.3); the '
             'authors suggest using the non-RAG version when the retrieved structure\'s similarity is 0.2 or below. '
             'Stating "non-RAG below 0.3" scores at most 0.5.', [[a('marason', 'c0034')]],
    ['larger than 0.3', 'non-RAG', '>0.2'])]),  # correction 6
]


def main():
    rows = {}
    for line in BUNDLE.open(encoding='utf-8'):
        r = json.loads(line)
        rows[r['chunk_id']] = r
    questions, references, key = [], [], ['# fresh-v3 answer key (AI-assisted; pending one focused independent review and '
                                          'human sign-off)', '']
    for qid, qtype, question, points in Q:
        questions.append({'id': qid, 'type': qtype, 'question': question})
        required = []
        key += [f'## {qid} ({qtype})', '', question, '']
        for point in points:
            pid, expected, groups, must = point[:4]
            kind = point[4] if len(point) > 4 else 'published'
            for group in groups:
                missing = [c for c in group if c not in rows]
                assert not missing, f'{pid}: anchor missing {missing}'
                joined = ' '.join(' '.join(rows[c]['text'].split()) for c in group)
                absent = [m for m in must if m not in joined]
                assert not absent, f'{pid}: anchor group {group} lacks {absent}'
            required.append({'point_id': pid, 'expected': expected, 'anchors': groups, 'type': kind})
            key += [f'- **{pid}** {expected}', f'  - anchors: {" | ".join(" + ".join(g) for g in groups)}']
        references.append({'id': qid, 'type': qtype, 'question': question, 'required_points': required})
        key.append('')
    (HERE / 'questions.json').write_text(json.dumps(questions, indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'references.json').write_text(json.dumps(references, indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'answer-key.md').write_text('\n'.join(key), encoding='utf-8')
    print('questions', len(questions), 'points', sum(len(r['required_points']) for r in references),
          'index sha256', hashlib.sha256(BUNDLE.read_bytes()).hexdigest()[:16])


if __name__ == '__main__':
    main()

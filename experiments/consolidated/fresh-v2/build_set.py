"""fresh-v2: 8 consultant-framed questions for the proposed Standard-vs-Deep live validation (NOT run).

Papers: the 8 corpus papers that appear in no earlier question, reference, label, case, benchmark or fixture file
(OVERLAP.md). Several questions reuse a paper with a different focus; no question was used to design or tune the
consolidated engine (the engine was built and tested on combined-v1 failure traces only).
Types: 2 single-paper, 3 cross-paper, 2 numerical/table, 2 partially unanswerable (H02 is both single-paper and
numerical/table; H06 and H08 are the partially unanswerable ones).

Each required point is a PUBLISHED finding with anchor group(s): every listed chunk must exist, and the joined text
of each group must contain every must-contain string (checked here). Points of type 'evidence_limit' require the
answer to say the corpus does not establish something; a fabricated figure scores 0 and is a misleading claim.
Answer key drafted with AI assistance (Claude) from the full passages; requires independent review and human
sign-off before any run. Run: python -I build_set.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
P = {'jmed': '2601.01627v3', 'medes': '2601.07954v1', 'harmnet': '2510.18728v1', 'autojb': '2406.03805v1',
     'boa': '2506.17299v2', 'cat': '2604.12817v1', 'catalm': '2405.17440v1', 'clinic': '2512.11437v1'}


def a(paper, cid):
    return f'{P[paper]}_{cid}'


LIMIT = 'evidence_limit'
Q = [
 ('H01', 'single-paper', 'A Japanese hospital group is evaluating LLM chat assistants for patient conversations. What did '
  'JMedEthicBench test, how did commercial and medical-specialised models hold up, how did safety change over the course of '
  'a conversation, and did the weaknesses persist in English?', [
   # Final review correction: the 50,000+ benchmark conversations and the 2,345 evaluation samples are different objects.
   ('H01.1', 'The benchmark is grounded in 67 Japan Medical Association guidelines and has over 50,000 adversarial '
             'conversations generated with seven automatically discovered jailbreak strategies; the 22 models were '
             'evaluated on a sample of 2,345 three-turn conversations (5 per strategy and JMA principle). Saying the 22 '
             'models were evaluated on the 50,000+ conversations conflates the two and scores at most 0.5.',
    [[a('jmed', 'c0000'), a('jmed', 'c0009')]], ['67 guidelines', '50,000', 'seven automatically discovered', '22 models',
                                                '2,345']),
   ('H01.2', 'Leading commercial models (e.g. Claude Opus 4.1, GPT-5) maintained robust alignment, while '
             'medical-specialised models were more vulnerable than general-purpose models.',
    [[a('jmed', 'c0019')]], ['Claude Opus 4.1', 'medical-specialized models exhibit increased vulnerability']),
   ('H01.3', 'The median safety score fell from about 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2; all pairwise '
             'turn comparisons were significant (p<0.001). The abstract summary "9.5 to 5.5" also scores.',
    [[a('jmed', 'c0013')], [a('jmed', 'c0000')]], ['9.5', '5.5']),
   ('H01.4', 'In a cross-lingual evaluation of six medical models, the safety deficiencies persisted and were often '
             'amplified in English, pointing to alignment limitations rather than language-specific factors.',
    [[a('jmed', 'c0019')]], ['six medical models', 'amplified']),
   ('H01.5', 'Limitation: conversations were three turns; longer conversations (5-7 turns) were not evaluated.',
    [[a('jmed', 'c0009')]], ['longer conversations'])]),
 ('H02', 'numerical/table', 'A healthcare client wants a small model aligned to medical ethics. In the MedES study, how did '
  'the aligned 7B model compare with the 671B DeepSeek-R1 on the subjective ethics test (risk rate, quality and '
  'comprehensive score) and on objective knowledge, drug-safety and emergency-care accuracy, and where does the evidence '
  'apply?', [
   ('H02.1', 'After five SFT rounds, deepseek-r1-7b scored risk rate 0.0320, quality 0.9924 and comprehensive 0.9356, '
             'versus deepseek-r1-671b at 0.0338, 0.8736 and 0.8103 (subjective test set, Table 2).',
    [[a('medes', 'table_b4a66ab450587176_5'), a('medes', 'table_b4a66ab450587176_7')]], ['0.9356', '0.8103', '0.0320']),
   ('H02.2', 'The authors summarise this as the 7B model surpassing a 671B commercial LLM by over 10% in composite '
             'ethical performance, with consistent gains over five SFT rounds.',
    [[a('medes', 'c0019')], [a('medes', 'c0004')]], ['over 10%']),
   ('H02.3', 'On objective tasks the round-5 7B model scored 43.1 (ethical knowledge), 52.8 (drug safety) and 61.6 '
             '(emergency care) accuracy versus 60.2, 88.4 and 89.1 for deepseek-r1-671b: it lags on objective knowledge.',
    [[a('medes', 'table_02ce7ccc29e736d1_5'), a('medes', 'table_02ce7ccc29e736d1_8')]], ['43.1', '61.6', '88.4']),
   ('H02.4', 'A retrieval-augmented 7B variant scored 58.6 / 82.4 / 91.2; the authors note plateauing gains and '
             'knowledge gaps in objective tasks and suggest retrieval-based methods may complement fine-tuning.',
    [[a('medes', 'table_02ce7ccc29e736d1_6'), a('medes', 'c0019')]], ['58.6', '91.2', 'retrieval-based']),
   ('H02.5', 'Scope: experiments were conducted entirely within the Chinese medical ethics context, and the benchmark '
             'and results are not intended for clinical decision-making or patient-facing use.',
    [[a('medes', 'c0000'), a('medes', 'c0020')]], ['entirely within the Chinese', 'not to be used directly in clinical'])]),
 ('H03', 'cross-paper', "A bank's AI security team wants to understand automated jailbreak tooling. What do HarmNet and "
  'AutoJailbreak show about how automated attacks are built, how successful they were, and which defence held up?', [
   ('H03.1', 'HarmNet is a modular multi-turn attack framework: ThoughtNet (a hierarchical semantic network), a '
             'feedback-driven Simulator for iterative query refinement, and a Network Traverser for adaptive execution.',
    [[a('harmnet', 'c0002')], [a('harmnet', 'c0000')]], ['ThoughtNet', 'Simulator', 'Network Traverser']),
   ('H03.2', 'Two components, both required for 1 (one alone 0.5): (a) closed-source ASR 91.5% GPT-3.5-Turbo, 94.8% '
             'GPT-4o, 68.6% Claude 3.5 Sonnet; (b) open-source 98.4% LLaMA-3-8B, 99.4% Mistral-7B, 99.6% Gemma-2-9B '
             '(HarmBench). Figures must stay attributed to the right model.',
    [[a('harmnet', 'c0008')]], ['94.8%', '68.6%', '99.6%']),
   ('H03.3', 'AutoJailbreak\'s Ensemble Attack-GA exceeded 90% jailbreak rate on four LLMs and reached 99% on Vicuna, '
             'Qwen and Mistral.', [[a('autojb', 'c0022')]], ['exceeding 90%', '99%']),
   ('H03.4', 'AutoDefense, a mixture-of-defenders ensemble of pre-generation and post-generation defences, showed '
             'superior robustness to AutoAttack on almost all LLMs, in a black-box setting.',
    [[a('autojb', 'c0003'), a('autojb', 'c0023')]],  # correction (pre-review): c0003 states pre/post-generation
    ['pre-generation and post-generation', 'mixture-of-defenders', 'superior robustness']),
   ('H03.5', 'AutoEvaluation separates hallucinated responses from genuine jailbreaks (jailbreak, hallucination and '
             'alignment rates).', [[a('autojb', 'c0020')], [a('autojb', 'c0000')]], ['hallucination'])]),
 ('H04', 'cross-paper', 'A model-risk team must decide how to assure an LLM against jailbreaks: systematic testing or '
  'adversarial training. What do the jailbreak-oracle (BOA) study and the continuous adversarial training study each '
  'offer, what evidence supports them, and what are their limits or costs?', [
   ('H04.1', 'BOA formalises the jailbreak oracle problem (can a jailbreak response be generated above a likelihood '
             'threshold for a given model, prompt and decoding strategy) and solves it with breadth-first sampling '
             'followed by depth-first priority search guided by safety scores.',
    [[a('boa', 'c0000')]], ['jailbreak oracle problem', 'breadth-first sampling', 'depth-first priority search']),
   ('H04.2', 'BOA finds most adversarial prompts admit jailbreak completions with non-negligible probability, and that '
             'decoding strategy changes a model\'s vulnerability.', [[a('boa', 'c0004')]],
    ['non-negligible probability', 'decoding strategies']),
   ('H04.3', 'Two components, both required for 1: (a) BOA ran with a 600-second budget per prompt on H100 GPUs, and '
             'timeout rates ranged from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B); (b) it addresses single-turn '
             'generation only, not multi-turn jailbreaks.',
    [[a('boa', 'c0025'), a('boa', 'c0028'), a('boa', 'c0041')]], ['600 seconds', '69.53%', 'single-turn']),
   ('H04.4', 'Continuous AT searches adversarial perturbations in the embedding space (cheaper than token-space AT); '
             'the theory links robustness to the perturbation radius and to the singular values of the embedding '
             'matrix, motivating ER-CAT\'s embedding regularisation.',
    [[a('cat', 'c0000')]], ['embedding space', 'singular values']),
   ('H04.5', 'ER-CAT gave a better robustness-utility trade-off than CAT and added only 100 to 200 seconds of '
             'training time.', [[a('cat', 'c0029'), a('cat', 'c0030')]], ['100 to 200 seconds', 'robustness-utility'])]),
 ('H05', 'numerical/table', 'For a client hardening open models, what attack success rates under GCG did the continuous '
  'adversarial training study report for Vicuna-7B, Mistral-7B and Llama-2-7B in their original form, after CAT and '
  'after ER-CAT, and what happened to utility?', [
   ('H05.1', 'Vicuna-7B GCG ASR: 84.6% original, 12.6% CAT, 16.4% ER-CAT (Avg@5).',
    [[a('cat', 'table_0ff9b02ec9b484d0_1'), a('cat', 'table_0ff9b02ec9b484d0_2'), a('cat', 'table_0ff9b02ec9b484d0_3')]],
    ['84.6', '12.6', '16.4']),
   ('H05.2', 'Mistral-7B GCG ASR: 74.6% original, 7.4% CAT, 7.6% ER-CAT.',
    [[a('cat', 'table_0ff9b02ec9b484d0_4'), a('cat', 'table_0ff9b02ec9b484d0_5'), a('cat', 'table_0ff9b02ec9b484d0_6')]],
    ['74.6', '7.4', '7.6']),
   ('H05.3', 'Llama-2-7B GCG ASR: 41.0% original, 23.6% CAT, 15.6% ER-CAT.',
    [[a('cat', 'table_0ff9b02ec9b484d0_7'), a('cat', 'table_0ff9b02ec9b484d0_8'), a('cat', 'table_0ff9b02ec9b484d0_9')]],
    ['41.0', '23.6', '15.6']),
   ('H05.4', 'Two components, both required for 1 (one alone 0.5): (a) on Vicuna and Mistral, ER-CAT had a nearly '
             'two-times better LC-WinRate than CAT while losing no more than 4% ASR in most attacks; (b) on Llama-2 and '
             'Qwen2.5 it cost no more than 3% LC-WinRate while cutting ASR (about 7% on GCG/BEAST for Llama-2, 11% on GCQ '
             'for Qwen2.5). The bracketed sub-figures are not required.',  # correction: explicit scoring
    [[a('cat', 'c0028')]], ['nearly two-times', 'no more than 3']),
  ]),
 ('H06', 'partially unanswerable', 'A chemicals client wants an LLM to speed up catalyst R&D. How was CataLM built and '
  'evaluated, how well does it extract entities from the literature, and how much did it shorten catalyst development '
  'time or cost in practice?', [
   ('H06.1', 'CataLM specialises a Vicuna model by domain pre-training on electrocatalysis literature and instruction '
             'tuning on expert-annotated data. (The paper names Vicuna-13B in the introduction and Vicuna-33b-v1.3 in the '
             'method; either, attributed, scores, and noting the inconsistency is credited.)',
    # Final review correction: the c0008 alternative must be read with c0007, which states the instruction tuning.
    [[a('catalm', 'c0004')], [a('catalm', 'c0008'), a('catalm', 'c0007')]], ['Vicuna', 'Pre-training', 'Instruction Tuning',
                                                                              'expert']),
   # Final review correction: the nine entity types are established by the nine type rows, not the total row.
   ('H06.2', 'The expert-annotated standard corpus has 6,985 entities across nine entity types (Table 1).',
    [[a('catalm', f'table_73e166fbe4d2eb83_{n}') for n in range(1, 11)]],
    ['Material', 'Control method', 'Product', 'Faradaic efficiency', 'Cell setup', 'Electrolyte', 'Synthesis method',
     'Current density', 'Voltage', '6,985']),
   ('H06.3', 'CataLM extracts numerical entities (e.g. Faradaic efficiency, potential) better than descriptive ones; '
             'in the ablation, fine-tuned LLM + few-shot performed best and both fine-tuning and RAG contributed.',
    [[a('catalm', 'c0014')]], ['numerical classes', 'both the fine-tuned module and the RAG module']),
   ('H06.4', 'Not established: the paper reports no measured reduction in catalyst development time or cost; '
             'recommendation quality was judged by domain experts on examples, and a researcher platform is future work. '
             'Any time or cost saving figure is fabricated.',
    [[a('catalm', 'c0015'), a('catalm', 'c0017')]], ['domain experts', 'auxiliary platform'], LIMIT)]),
 ('H07', 'cross-paper', 'A global health-tech client will deploy an LLM assistant in several languages, including Japanese '
  'and low-resource languages. What do CLINIC and JMedEthicBench show about language-related and model-type-related '
  'trustworthiness and safety risks?', [
   ('H07.1', 'CLINIC: 28,800 expertly validated samples, 15 languages, five trustworthiness dimensions and 18 tasks; 13 '
             'models evaluated.', [[a('clinic', 'c0024')]], ['28,800', '15 languages', '13 representative models']),
   ('H07.2', 'CLINIC: performance follows high- > mid- > low-resource languages, dropping sharply in low-resource '
             'languages, especially for honesty, fairness and privacy.', [[a('clinic', 'c0023')]], ['HR > MR > LR']),
   ('H07.3', 'CLINIC: medical LLMs hallucinate more and struggle with robustness despite domain training; proprietary '
             'models lead overall though privacy remains a weakness.', [[a('clinic', 'c0023')]],
    ['medical LLMs hallucinate more', 'privacy remains a weakness']),
   ('H07.4', 'JMedEthicBench: medical-specialised models are more vulnerable than general models, and these deficiencies '
             'persist, often amplified, in English, i.e. not a Japanese-language artefact.',
    [[a('jmed', 'c0019')]], ['increased vulnerability', 'amplified'])]),
 ('H08', 'partially unanswerable', 'An NGO wants a health chatbot for Swahili-, Hausa- and Yoruba-speaking communities. '
  'Which languages did CLINIC cover as low-resource, what did it find about privacy and reliability in low-resource '
  'languages, and how do the models perform in Yoruba?', [
   ('H08.1', 'CLINIC\'s low-resource tier is Swahili, Hausa, Nepali and Somali (with eight high- and three mid-resource '
             'languages).', [[a('clinic', 'c0004')]], ['Swahili, Hausa, Nepali, Somali']),
   ('H08.2', 'Privacy: GPT-4o-mini had the lowest and most stable leakage across tiers; medical models were mixed, '
             'leaking more information especially in low-resource languages.',  # correction: source says 'mixed'
    [[a('clinic', 'c0022')]], ['GPT-4o-mini has the lowest', 'medical models are mixed']),
   ('H08.3', 'The authors conclude current models, even state-of-the-art, remain unreliable for high-stakes multilingual '
             'healthcare.', [[a('clinic', 'c0024')]], ['remain unreliable']),
   ('H08.4', 'Not established: Yoruba is not among CLINIC\'s 15 languages, so its performance in Yoruba is not reported. '
             'Any Yoruba result is fabricated.', [[a('clinic', 'c0004')]], ['Swahili'], LIMIT)]),
]


def main():
    rows = {}
    for line in BUNDLE.open(encoding='utf-8'):
        r = json.loads(line)
        rows[r['chunk_id']] = r
    questions, references, key = [], [], ['# fresh-v2 answer key (AI-assisted; pending independent review and sign-off)', '']
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
                # Every alternative must support every required component (final review rule), not just the first.
                absent = [m for m in must if m not in joined]
                assert not absent, f'{pid}: anchor group {group} lacks {absent}'
            required.append({'point_id': pid, 'expected': expected, 'anchors': groups, 'type': kind})
            key += [f'- **{pid}** {expected}', f'  - anchors: {" | ".join(" + ".join(g) for g in groups)}']
        references.append({'id': qid, 'type': qtype, 'question': question, 'required_points': required})
        key.append('')
    (HERE / 'questions.json').write_text(json.dumps(questions, indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'references.json').write_text(json.dumps(references, indent=1, ensure_ascii=False), encoding='utf-8')
    (HERE / 'answer-key.md').write_text('\n'.join(key), encoding='utf-8')
    total = sum(len(r['required_points']) for r in references)
    print('questions', len(questions), 'points', total,
          'index sha256', hashlib.sha256(BUNDLE.read_bytes()).hexdigest()[:16])


if __name__ == '__main__':
    main()

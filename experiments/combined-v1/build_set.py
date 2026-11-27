"""fresh-business-v1: 10 consultant-framed questions on papers never used in any prior question, reference, label,
case, benchmark or fixture file (OVERLAP.md). Run once; seal.json pins the outputs.

Types: 2 single-paper, 3 cross-paper, 3 numerical/table, 2 partially unanswerable.
Required points are PUBLISHED findings (with anchors). Points of type "evidence_absent" have no anchor: the corpus does
not establish them, and the answer must say so rather than supply a figure (scored under rules.json).
Answer key drafted with AI assistance from the full passages; pending Codex review and human sign-off.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path('D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100/parents.jsonl')
P = {'markets': '2501.17755v2', 'regions': '2503.05773v1', 'scr': '2505.15753v1', 'advtune': '2406.06622v1',
     'pandora': '2402.08416v1', 'overfit': '2510.02833v4', 'polaris': '2403.13313v1', 'aihospital': '2402.09742v4',
     'commit': '2508.08345v2', 'finstat': '2506.23273v2', 'failclosed': '2602.16977v1', 'legal': '2601.17692v1',
     'lying': '2606.28456v1'}


def a(p, cid):
    return f'{P[p]}_{cid}'


ABSENT = 'evidence_absent'
# (id, type, question, [(point id, expected, anchor groups or ABSENT, must-contain strings checked against the anchor)])
Q = [
 ('G01', 'single-paper', "A client's risk committee asks whether market mechanisms, not only regulation, can govern AI risk. "
  "What market mechanisms does the 'AI Governance through Markets' paper propose, how do they connect AI risk to financial "
  'risk, and what limits do the authors acknowledge?', [
   ('G01.1', 'Four market-governance vectors: insurance, auditing, procurement and due diligence.', [[a('markets', 'c0000')], [a('markets', 'c0003')]], ['insurance', 'procurement']),
   ('G01.2', 'They serve risk distribution, information discovery, protocolisation and capital allocation, decreasing AI risk by pricing, measuring and mitigating it.', [[a('markets', 'c0003')]], ['risk distribution', 'pricing, measuring and mitigating']),
   ('G01.3', 'Insurance can make safety-washing or underestimating AI risk less appealing; actuarial rigour can curb AI hype.', [[a('markets', 'c0011')]], ['safety-washing']),
   ('G01.4', 'The authors do not claim market forces alone adequately protect societal interests; standardised AI disclosures are needed alongside market mechanisms.', [[a('markets', 'c0000')]], ['market forces alone', 'standardised AI disclosures'])]),
 ('G02', 'single-paper', 'A multinational client must align its AI risk management across the EU, the U.S., the UK and China. '
  'According to the cross-regional study of AI risk-management frameworks, how do the four regimes differ and what trade-off '
  'does each carry?', [
   ('G02.1', 'EU: structured, risk-based framework prioritising transparency and conformity assessments.', [[a('regions', 'c0001')]], ['risk-based framework', 'conformity assessments']),
   ('G02.2', 'U.S.: decentralised, sector-specific regulation that promotes innovation but may fragment enforcement.', [[a('regions', 'c0001')]], ['fragmented enforcement']),
   ('G02.3', 'UK: flexible, sector-specific strategy enabling agile responses but risking inconsistent coverage across domains.', [[a('regions', 'c0001')]], ['inconsistent coverage']),
   ('G02.4', 'China: centralised directives enable rapid large-scale implementation while constraining public transparency and external oversight.', [[a('regions', 'c0001')]], ['constraining public transparency'])]),
 ('G03', 'cross-paper', 'A client must defend a customer-facing LLM against new jailbreaks. How do Safety Context Retrieval (SCR) '
  'and two-stage adversarial tuning differ in approach, how effective were they, and what did each cost in normal-task '
  'performance or effort?', [
   ('G03.1', 'SCR keeps a pool of safety contexts, adds a minimal set of safety samples when a new jailbreak is identified, and retrieves a few at inference, instead of repeatedly fine-tuning.', [[a('scr', 'c0003')]], ['safety context pool', 'minimal set of safety samples']),
   ('G03.2', 'SCR reduced average ASR against GCG-T from 34.9% (no defence) to 2.5%.', [[a('scr', 'c0018')]], ['34.9%', '2.5%']),
   ('G03.3', 'SCR had negligible effect on natural performance (e.g. Llama-3.1 HumanEval 61.6% to 57.3%, MMLU 62.6% to 63.2%).', [[a('scr', 'c0021')]], ['61.6%', '57.3%']),
   ('G03.4', 'Adversarial tuning is two-stage: hierarchical meta-universal (token-level) adversarial prompts, then automatic semantic-level adversarial prompts, used to fine-tune on adversarial prompt and safe-response pairs.', [[a('advtune', 'c0000')]], ['two-stage adversarial tuning', 'semantic-level']),
   # Correction 5 (Codex review): name the two target models, keep the paired ASR results as the source states them, and
   # require the effort/cost component (the study gives no compute-cost figure for its own tuning).
   ('G03.5', 'Two components, both required for 1 (one alone scores 0.5). (a) On the two target models, Llama-2-7B-chat and '
             'Vicuna-13B-v1.5, known jailbreaks gave average ASR of 66.54% / 51.38% and 19.62% / 9.62% under two metrics; '
             'adversarial tuning reduced them to 2.69% / 0.00% and 3.08% / 0.00%. The passage reports these pairs "respectively" '
             'without readable metric labels, so an answer may report them as pairs; assigning a pair to a specific model or '
             'metric as fact is an unsupported attribution. (b) Effort/cost: the passages give no compute-cost figure for '
             'adversarial tuning itself (it uses LoRA to improve training efficiency); an answer must say the cost is not '
             'established. Presenting the 20-minute GCG prompt-generation figure as the cost of adversarial tuning is a '
             'misattribution.',
    [[a('advtune', 'c0021'), a('advtune', 'c0019'), a('advtune', 'c0015')]], ['66.54%', '19.62%', '3.08%', 'Vicuna', 'LoRA'])]),
 ('G04', 'cross-paper', 'A client plans custom GPT-style assistants with uploaded knowledge files and fine-tuning services for '
  "business units. What do the Pandora and 'Attack via Overfitting' studies show about these customisation routes as jailbreak "
  'attack surfaces, how successful were the attacks, and how detectable are they?', [
   ('G04.1', 'Pandora poisons RAG: malicious content uploaded as knowledge files plus crafted prompts makes GPTs jailbreak indirectly.', [[a('pandora', 'c0003')]], ['tainted knowledge source']),
   ('G04.2', 'Pandora success 64.3% on GPT-3.5 and 34.8% on GPT-4 across four prohibited scenarios, versus 3.0% and 1.0% for naive malicious questions.', [[a('pandora', 'c0016')]], ['64.3%', '3.0%']),
   ('G04.3', 'The overfitting attack fine-tunes on 10 benign QA pairs: first with identical refusal answers to induce overfitting, then with normal answers, after which the model complies with harmful questions.', [[a('overfit', 'c0003')]], ['identical refusal answers']),
   ('G04.4', 'It reached 94.84% average ASR across ten LLMs (HS 4.48), comparable to malicious fine-tuning (97.25%).', [[a('overfit', 'c0016')]], ['94.84%', '97.25%']),
   # Correction 4 (review): two components, both required for full credit (c0005 supports only the first).
   ('G04.5', 'Two components, both required for 1 (one alone scores 0.5): (a) because the data is entirely benign it is stealthy '
             'against moderation models, which catch malicious fine-tuning; (b) it bypassed a token-wise loss defence.',
    [[a('overfit', 'c0005')], [a('overfit', 'c0027')]], ['stealth'])]),
 ('G05', 'cross-paper', 'A hospital-network client is assessing LLMs for patient-facing conversations. How did the Polaris and AI '
  'Hospital studies evaluate conversational medical LLMs, and what do their results imply about readiness?', [
   ('G05.1', 'Polaris is a constellation (about one trillion parameters) of a primary conversational agent and specialist support agents for nurse, social-worker and nutritionist tasks, to increase safety and reduce hallucinations.', [[a('polaris', 'c0000')]], ['specialist support agents']),
   ('G05.2', 'Over 1,100 U.S. nurses and 130 physicians posed as patients; Polaris performed on par with human nurses on aggregate across medical safety, clinical readiness, patient education, conversational quality and bedside manner.', [[a('polaris', 'c0001')]], ['1100', 'on par with human nurses']),
   ('G05.3', "Polaris's specialist agents significantly outperformed GPT-4 and LLaMA-2 70B on task-based evaluation.", [[a('polaris', 'c0001')]], ['LLaMA-2 70B']),
   ('G05.4', 'AI Hospital simulates multi-agent clinical interaction and evaluates Doctor agents on the MVME benchmark of Chinese medical records (symptom collection, examinations, diagnosis).', [[a('aihospital', 'c0000')]], ['Chinese medical records']),
   # Correction 3 (review): keep the source's limitation on the dispute-resolution gain.
   ('G05.5', 'Interactive LLMs reached less than 50% of the one-step GPT-4 upper bound on diagnosis, rationale and treatment accuracy; '
             'a dispute-resolution collaborative mechanism improves performance only to a certain degree and still falls short of '
             'the upper bound. Stating the improvement without that limitation scores at most 0.5.',
    [[a('aihospital', 'c0004')]], ['less than 50%', 'to a certain degree', 'falls short of the upper bound'])]),
 ('G06', 'numerical/table', 'A client relies on AI vendors\' public safety commitments. How well did AI companies implement '
  "their 2023 White House voluntary commitments: overall scores, the best and worst performers, which commitment was weakest, "
  'and which looked strongest?', [
   ('G06.1', '16 companies scored; mean 53.3% (median 50.0%); OpenAI highest at 83.3%, Apple lowest at 13.3%.', [[a('commit', 'c0018')]], ['53.3%', '13.3%']),
   # Correction 2 (review): the paper states both "at least 60%" (c0004) and "at least 66%" (c0019); either figure with
   # correct attribution scores, and an answer that identifies the inconsistency is credited.
   # Correction 6 (Codex review): 60% and 66% are compatible lower bounds; the group statistics need c0019.
   ('G06.2', 'The six Frontier Model Forum members are the highest-scoring companies. "At least 66%" (results) and "at least 60%" '
             '(introduction) are compatible lower bounds, and either may be quoted with its attribution. The group statistics '
             'must be supported by the results passage: FMF mean 74.4% (SD 6.9%); the other 10 companies score at or below '
             '60% (mean 40.7%, SD 11.4%).',
    [[a('commit', 'c0019')]], ['74.4%', '40.7%', '6.9%', '11.4%']),
   ('G06.3', 'Model-weight security averaged 17%; 11 of the 16 companies scored 0%.', [[a('commit', 'c0000')], [a('commit', 'c0005')]], ['17%']),
   ('G06.4', 'Watermarking/provenance scored highest (92.2%), but often vacuously because many companies do not build audio or visual models.', [[a('commit', 'c0021')]], ['92.2%', 'vacuously'])]),
 ('G07', 'numerical/table', 'A finance client wants natural-language querying of financial statements. What accuracy and speed '
  'did FinStat2SQL achieve, how did it compare with proprietary models and with its untuned base model, and what limits '
  'apply?', [
   ('G07.1', 'The fine-tuned 7B model reached 61.33% accuracy with sub-4-second responses on consumer hardware, outperforming GPT-4o-mini.', [[a('finstat', 'c0000')]], ['61.33%', 'sub-4-second']),
   ('G07.2', 'Best proprietary model Gemini-2.0-Flash-Thinking 72.03%; GPT-4o-mini 59.14%.', [[a('finstat', 'table_4d7c993521f0bf29_1'), a('finstat', 'table_4d7c993521f0bf29_6')],
                                                                                         [a('finstat', 'c0017'), a('finstat', 'table_4d7c993521f0bf29_6')]], ['0.7203', '0.5914']),
   # Correction 7 (Codex review): the methods passage establishes that finstat2sql is fine-tuned Qwen 2.5 Coder per size.
   ('G07.3', 'Fine-tuning lifted the 7B Qwen2.5-Coder-Instruct from 47.93% to 61.33% (finstat2sql is a fine-tuned Qwen 2.5 Coder '
             'for each model size).',
    [[a('finstat', 'table_d472857c5172bfd0_1'), a('finstat', 'table_d472857c5172bfd0_4'), a('finstat', 'c0014')]],
    ['0.4793', '0.6133', 'fine-tuned version of Qwen 2.5 Coder']),
   ('G07.4', 'Limits: only VN30/HNX30-listed firms (no SMEs), Vietnamese terminology issues, and untested beyond Vietnam (e.g. US GAAP).', [[a('finstat', 'c0018')]], ['SMEs', 'US GAAP'])]),
 ('G08', 'numerical/table', 'A client wants to harden an open-weight model against jailbreaks. What does the fail-closed '
  'alignment study report about why standard alignment fails, attack success, benign compliance, output quality and compute '
  'cost, and on which models was it tested?', [
   ('G08.1', 'Standard alignment encodes refusal along a single activation direction that prompt-based jailbreaks suppress, so it behaves fail-open.', [[a('failclosed', 'c0028')]], ['single activation direction']),
   ('G08.2', 'At most 4% ASR in all cases; average ASR reduced by 92.3–97.2%, versus 23.8–93.7% for baselines.', [[a('failclosed', 'c0019')]], ['92.3', '23.8']),
   ('G08.3', 'Highest compliance on benign prompts among robust methods (86% on average).', [[a('failclosed', 'c0003')]], ['86%']),
   # Correction 8 (Codex review): the paper says "a drop of just 0.8%"; the arithmetic is 0.4 points (~0.65% relative).
   ('G08.4', '61.6% average accuracy versus 62.0% for CAT, with only a small constant-factor overhead over standard fine-tuning. '
             'The gap may be given as the calculated 0.4 percentage points (about 0.65% relative) or as the paper\'s reported '
             '"0.8%" attributed to the paper; presenting 0.8 as the calculated percentage-point gap scores 0.5.',
    [[a('failclosed', 'c0020')]], ['61.6%', '62.0%', '0.8%', 'constant-factor']),
   ('G08.5', 'Tested on four open instruction-tuned models of 2–9B parameters: Llama2-7B, Llama3-8B, Gemma2-2B and Gemma2-9B.', [[a('failclosed', 'c0018')]], ['Gemma2-2B'])]),
 ('G09', 'partially unanswerable', 'A legal-services client wants AI statute retrieval for colloquial client questions under '
  'English and EU law. How does LegalMALR work, what retrieval results did it achieve, how well does it perform on English or '
  'EU statutes, and what does it cost per query?', [
   ('G09.1', 'Multi-agent query understanding produces diverse legally grounded reformulations with iterative dense retrieval; a zero-shot commercial LLM (Qwen-Max) reranks the candidates.', [[a('legal', 'c0004')], [a('legal', 'c0012')]], ['Qwen-Max']),
   ('G09.2', 'MAS with GRPO reached Recall@14 0.8396 and HitRate@14 0.9320 on STARD, and recall 0.7478 with HitRate@14 1.0 on CSAID.', [[a('legal', 'c0041')]], ['0.8396', '0.7478']),
   ('G09.3', 'English/EU performance is not established: the framework was developed and evaluated only on Chinese statutes and Chinese-language queries.', [[a('legal', 'c0053')], [a('legal', 'c0004')]], ['Chinese']),
   # Correction 1 (review): distinguish monetary cost (not reported) from computational cost proxies (reported).
   ('G09.4', 'No monetary per-query cost is reported. Answers may cite the stated computational cost proxies (1-4 retrieval rounds, '
             '30-120 embedding calls, about 13.58 candidates passed to the commercial LLM reranker, whose per-token cost is higher '
             'than lightweight rerankers; c0035, c0048, c0052). Any monetary per-query price not supported by the study is '
             'fabricated (correction 9, Codex review).', ABSENT, [])]),
 ('G10', 'partially unanswerable', 'A client is piloting autonomous multi-agent LLM systems that share a common resource. '
  "What did the study 'Is Lying an Emergent Behaviour in LLMs?' find about agents lying and its effects, and how often do "
  'deployed commercial AI agents lie to customers?', [
   ('G10.1', 'Setting: an agent-based sustainability game in which agents are told resources regenerate although they do not; agents can observe neighbours, declare attacks, be permitted to lie and see reputation.', [[a('lying', 'c0000')]], ['regeneration does not actually occur']),
   ('G10.2', 'Agents lied in 44% of declarations even when not permitted, rising to 65% when permitted: permission amplifies an existing tendency.', [[a('lying', 'c0035')]], ['44%', '65%']),
   ('G10.3', 'Declarations cut extinction from 40% to 7% and raised coexistence from 60% to 88%.', [[a('lying', 'c0031')]], ['40\\%', '7\\%']),
   # Correction 4 (review): two components, both required for full credit (c0002 supports only the second).
   ('G10.4', "Two components, both required for 1 (one alone scores 0.5): (a) deployed commercial agents' lying rates are not "
             'established by the study; (b) because it is a simplified simulation (identical agents, fixed network), not a '
             'real-world deployment. A stated real-world lying rate scores 0 and counts as a misleading claim.',
    [[a('lying', 'c0045')], [a('lying', 'c0002')]], [])]),
]


def main():
    texts = {}
    for line in BUNDLE.open(encoding='utf-8'):
        row = json.loads(line)
        texts[row['chunk_id']] = ' '.join(row['text'].split())
    questions, references = [], []
    for qid, kind, question, points in Q:
        required = []
        for pid, expected, anchors, must in points:
            if anchors != ABSENT:
                for group in anchors:
                    joined = ' '.join(texts[c] for c in group)  # KeyError if an anchor ID does not exist
                    missing = [m for m in must if m not in joined]
                    assert not missing or group is not anchors[0] or len(anchors) > 1, (pid, group, missing)
                if must:
                    assert any(all(m in ' '.join(texts[c] for c in g) for m in must) for g in anchors), (pid, must)
            required.append({'point_id': pid, 'expected': expected,
                             'anchors': [] if anchors == ABSENT else anchors,
                             'type': ABSENT if anchors == ABSENT else 'published'})
        questions.append({'id': qid, 'type': kind, 'question': question})
        references.append({'id': qid, 'type': kind, 'question': question, 'required_points': required})
    (HERE / 'questions.json').write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding='utf-8')
    (HERE / 'references.json').write_text(json.dumps(references, ensure_ascii=False, indent=1), encoding='utf-8')
    lines = ['# fresh-business-v1 answer key (AI-assisted; pending Codex review and human sign-off)', '']
    for ref in references:
        lines += [f"## {ref['id']} ({ref['type']})", '', ref['question'], '']
        for p in ref['required_points']:
            where = 'no anchor: must be stated as not established' if p['type'] == ABSENT else \
                ' or '.join(' + '.join(g) for g in p['anchors'])
            lines.append(f"- **{p['point_id']}** {p['expected']} *[{where}]*")
        lines.append('')
    (HERE / 'answer-key.md').write_text('\n'.join(lines), encoding='utf-8')
    total = sum(len(r['required_points']) for r in references)
    print(f'{len(references)} questions, {total} required points '
          f'({sum(p["type"] == ABSENT for r in references for p in r["required_points"])} evidence-absent)')


if __name__ == '__main__':
    main()

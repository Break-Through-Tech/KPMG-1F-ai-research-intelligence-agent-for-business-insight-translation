"""Frozen 15-question completion evaluation set (C01-C15), framed for a KPMG consultant. Run once; seal.json pins outputs.

Required points are PUBLISHED findings only (including implications the authors themselves state). Business implications
a system infers must be labelled as interpretation; they are never required points and are scored under rules.json.
"""
import json

P = {'malware': '2506.10022v1', 'sudo': '2505.14607v3', 'ctrl': '2405.19358v2', 'kgfin': '2601.07754v1',
     'aviary': '2412.21154v1', 'multirag': '2508.03553v1', 'kg2rag': '2502.06864v1', 'fbi': '2402.12713v2',
     'profin': '2511.08621v1', 'finoverview': '2401.11641v5', 'fmti': '2506.23123v1', 'medsurvey': '2508.19097v1',
     'bao': '2602.11351v2', 'metarag': '2510.24402v1'}


def a(p, cid):
    return f'{P[p]}_{cid}'


Q = [
 ('C01', 'numeric / risk', 'A client wants to roll out AI coding assistants. How reliably do mainstream LLMs refuse malicious '
  'code-generation requests, how do jailbreak techniques change that, and which models resisted best in the MalwareBench study?', [
   ('C01.1', 'Average rejection rate for malicious content is 60.93%, falling to 39.92% when combined with jailbreak attack algorithms.', [[a('malware', 'c0000')]]),
   ('C01.2', 'About 50.35% of jailbreak attempts induced responses containing malicious content.', [[a('malware', 'c0015')]]),
   ('C01.3', 'Most resistant: OpenAI-o1 (refuse rate 77.29%) and, among open models, CodeLlama-70B-Instruct (76.86%).', [[a('malware', 'c0015')]])]),
 ('C02', 'governance / cost', 'For role-based access to sensitive answers, how does sudoLLM behave when it is unsure, does it hurt '
  'normal task performance, how well does it hold up against an adversary who knows the mechanism, and what did the experiments cost?', [
   ('C02.1', 'The BFT strategy fails closed (refuses when in doubt), whereas base and vanilla fine-tuned models fail open.', [[a('sudo', 'c0018')]]),
   ('C02.2', 'No significant task-performance degradation from multi-role (VFT/BFT) fine-tuning versus the base model.', [[a('sudo', 'c0018')]]),
   ('C02.3', 'Signature-user detection succeeds 94.5% of the time (P>0.7) and 93.9% (P>0.8); an adversary with full knowledge cannot circumvent it.', [[a('sudo', 'c0022')]]),
   ('C02.4', 'Total compute cost about 1,700 USD for API-based LLMs and about 100 GPU-hours for local small models.', [[a('sudo', 'c0014')]])]),
 ('C03', 'qualitative / risk', 'What did the Ctrl data-curation study find about protecting LLMs from harmful content in training '
  'data and from malicious fine-tuning, and what trade-offs or residual risks did it report?', [
   ('C03.1', 'Curating clean texts (Ctrl) mitigated harmful texts (datasets with 5% harmful texts) across LLMs and often also improved helpfulness.', [[a('ctrl', 'c0020')]]),
   ('C03.2', 'Helpfulness can drop in some cases (e.g. Llama-3-8B with instruction-following attack data); smaller models such as ChatGLM-6B are more susceptible.', [[a('ctrl', 'c0020')]]),
   ('C03.3', 'Downstream attacks used only 50 or 10 fine-tuning samples; Ctrl reduced attack effectiveness in most cases but less for fragile models, and defenders should invest in alignment at pre-training.', [[a('ctrl', 'c0021')]])]),
 ('C04', 'numeric / limitations', 'How much did adding knowledge graphs improve LLM numerical reasoning on financial documents, and what '
  'limits how far a finance team could rely on that result?', [
   ('C04.1', 'KGs gave +6.41 percentage points execution accuracy (51.93% to 58.34%), about 12.3% relative, with a Llama model.', [[a('kgfin', 'c0012')]]),
   ('C04.2', 'Limitations: only FinQA; only open-source LLMs (no comparison with proprietary-model work); KG schema variance may bottleneck localized financial datasets.', [[a('kgfin', 'c0015')]])]),
 ('C05', 'cost-performance', 'What cost-performance trade-off did the Aviary study report for a small trained open-source agent versus a '
  'frontier model and human experts on scientific tasks, and what caveats apply?', [
   ('C05.1', 'The trained Llama-3.1-8B agent matched Claude 3.5 Sonnet majority-voting accuracy on SeqQA at about 100x less cost; not achieved on LitQA2, where its voting still beat a single Sonnet rollout at 3x less cost.', [[a('aviary', 'c0028')]]),
   ('C05.2', 'Cost per SeqQA trajectory: $0.07 with Claude 3.5 Sonnet vs $0.00066 with Llama-3.1-8B; human PhD contractors cost $4-$12 per question.', [[a('aviary', 'c0030')]]),
   ('C05.3', 'Caveats: comparisons with humans and prior results are not exactly matched; benchmark contamination risk (LitQA2 re-hosted without canary).', [[a('aviary', 'c0030')]])]),
 ('C06', 'numeric / robustness', 'When source data are sparse or contradictory, how robust was MultiRAG compared with the ChatKBQA baseline?', [
   ('C06.1', 'On sparser Books and Stocks data, MultiRAG improved more than 10% on average over state-of-the-art methods.', [[a('multirag', 'c0026')]]),
   ('C06.2', 'With relationship masking on Stocks, MultiRAG F1 fell 78.6% to 71.0%, while ChatKBQA fell 68.0% to 62.0% (Books 59.1% to 53.0%).', [[a('multirag', 'c0027')]]),
   ('C06.3', 'With inconsistent added triples, MultiRAG F1 fell only from 74.9% to 73.4/72.9/71.4%, while ChatKBQA fell from 74.2% to 69.7/64.3/55.8%.', [[a('multirag', 'c0028')]])]),
 ('C07', 'cross-paper', 'KG²RAG and MultiRAG both use knowledge graphs to make retrieval-augmented answers more reliable. What '
  'problem does each target, how does each work, and what gains did each report?', [
   ('C07.1', 'KG²RAG: after semantic retrieval of seed chunks, KG-guided chunk expansion and KG-based organization supply fact-level relationships for more diverse, coherent context.', [[a('kg2rag', 'c0000')]]),
   ('C07.2', 'KG²RAG gains: at least 8% over baselines in the fullwiki setting; at least 2.5% and 6.4% on Shuffle-HotpotQA (distractor, fullwiki).', [[a('kg2rag', 'c0019')]]),
   ('C07.3', 'MultiRAG: multi-source line graphs aggregate sources, and multi-level (graph and node) confidence filters low-quality or inconsistent knowledge, targeting sparse and conflicting multi-source data; >10% gain on sparse datasets.', [[a('multirag', 'c0004'), a('multirag', 'c0026')]])]),
 ('C08', 'qualitative / limitations', 'What did the Financial Bias Indicators (FBI) study find about irrational financial biases in LLMs, '
  'how did model size and bias-mitigation prompts affect them, and how far do the findings generalize?', [
   ('C08.1', 'Within a model family, bias tends to decrease as model size grows, but not consistently across families (design and training also matter).', [[a('fbi', 'c0024')]]),
   ('C08.2', 'Mitigation: CoT helped originally more-biased models but hurt well-performing ones; Entity Replace performed best; FinCausal used recalled causal knowledge.', [[a('fbi', 'c0022')]]),
   ('C08.3', 'Limitation: focused on the Chinese A-share market, so findings may not generalize to other cultures or regions.', [[a('fbi', 'c0028')]])]),
 ('C09', 'numeric / applications', 'What is the LLM Pro Finance Suite, how did it perform on financial tasks across languages, and what gap remained?', [
   ('C09.1', 'Five instruction-tuned models (8B-70B) fine-tuned on a corpus with over 50% finance data in English, French and German; consistent improvement over baselines on finance tasks and financial translation.', [[a('profin', 'c0000')]]),
   ('C09.2', 'Improvement is largest in French; English-level performance is not yet reached on all languages; English financial-acronym accuracy stagnates around 0.50.', [[a('profin', 'c0016')]])]),
 ('C10', 'qualitative / adoption', 'According to the overview of LLMs in finance, where are LLMs strongest, where are they limited, and '
  'what role do the authors see for them in computational finance?', [
   ('C10.1', 'Strong zero-shot learning and mathematical reasoning; sentiment analysis is their strongest suit.', [[a('finoverview', 'c0043')]]),
   ('C10.2', 'Limited in optimization and quantitative trading; cannot directly do computational tasks; an auxiliary role feeding existing quantitative models, not a standalone solution.', [[a('finoverview', 'c0044')]])]),
 ('C11', 'numeric / governance', 'For vendor due diligence, what did the Foundation Model Transparency Index find about how transparent '
  'major foundation-model developers are, and where is transparency weakest?', [
   ('C11.1', 'FMTI uses 100 indicators; leading developers were not transparent in 2023, with material improvement in 2024.', [[a('fmti', 'c0014')]]),
   ('C11.2', 'In 2024, 11 of 14 developers scored below 65.', [[a('fmti', 'c0274')]]),
   ('C11.3', 'Weakest: the impact subdomain; no developer scores on affected market sectors, affected individuals, usage reports or geographic statistics.', [[a('fmti', 'c0286')]])]),
 ('C12', 'limitations / risk', 'What challenges does the survey of reasoning LLMs in medicine identify for safely deploying them in clinical settings?', [
   ('C12.1', 'Chain-of-thought steps are not guaranteed to be medically sound; reasoning must be grounded in authoritative knowledge and evidence-based guidelines.', [[a('medsurvey', 'c0033')]]),
   ('C12.2', 'High-stakes errors and training-data bias (health disparities) require context-aware safety mechanisms and incorporation of guidelines, ethics and regulation.', [[a('medsurvey', 'c0034')]])]),
 ('C13', 'qualitative / customer experience', 'What trade-off do proactive LLM agents face between completing tasks and involving users, and what did BAO achieve?', [
   ('C13.1', 'Passive agents cannot efficiently adapt to user intentions while overusing human feedback burdens users: a Pareto frontier between task performance and user engagement.', [[a('bao', 'c0000')]]),
   ('C13.2', 'BAO improved task performance with lower user effort, surpassing proactive RL baselines and comparable or superior to commercial LLM agents on UserRL.', [[a('bao', 'c0000')], [a('bao', 'c0004')]])]),
 ('C14', 'table / business implications', 'For an accounting firm choosing between a commercial reranker and an in-house reranker in the '
  'metadata-driven financial RAG study, what quality and latency trade-off does Table 1 show, and what business implications do the authors themselves draw?', [
   ('C14.1', 'Full pipeline with the Cohere reranker on contextual chunks: F1 44.4, mean latency 13.18 s.', [[a('metarag', 'table_de629a5f57790c34_9')]]),
   ('C14.2', 'Same pipeline with the in-house reranker: F1 43.2, mean latency 12.43 s.', [[a('metarag', 'table_de629a5f57790c34_10')]]),
   ('C14.3', 'Authors: an in-house, transparent model is competitive, avoids high operational costs and vendor lock-in, and is more auditable and explainable.', [[a('metarag', 'c0045')]]),
   ('C14.4', 'Authors: naive chunk expansion hurt (relevance over quantity; more hallucination, less faithful answers).', [[a('metarag', 'c0045')]])]),
 ('C15', 'cross-paper / business implications', 'A bank is considering a finance-specialized LLM. What do the LLM Pro Finance and '
  'Financial Bias Indicators studies each report about domain-specific financial training?', [
   ('C15.1', 'LLM Pro Finance: fine-tuned models improve over the baseline by a large margin (especially in French), with smaller fine-tuned models outperforming larger base models on English acronyms.', [[a('profin', 'c0016')]]),
   ('C15.2', 'FBI: financially trained models may show higher score variability and risk inclination, and financial training data (e.g. embellished research reports) may embed irrationality.', [[a('fbi', 'c0025')]])]),
]

if __name__ == '__main__':
    questions = [{'id': qid, 'category': cat, 'question': q} for qid, cat, q, _ in Q]
    refs = [{'id': qid, 'category': cat, 'question': q, 'required_points': [
        {'point_id': pid, 'expected': exp, 'anchors': anchors, 'paper': anchors[0][0].split('_')[0]}
        for pid, exp, anchors in pts], 'human_verified': False} for qid, cat, q, pts in Q]
    with open('questions.json', 'x', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=1)
    with open('references.json', 'x', encoding='utf-8') as f:
        json.dump(refs, f, ensure_ascii=False, indent=1)
    print(len(questions), 'questions', sum(len(r['required_points']) for r in refs), 'points')

"""Writes the frozen held-out question set and answer key (run once; seal.json then pins the outputs)."""
import json

P = {'meta': '2510.24402v1', 'codeact': '2402.01030v4', 'quant': '2506.06622v2', 'agentlab': '2602.16901v1',
     'persona': '2602.12285v1', 'skill': '2608.09253v1', 'speech': '2502.10950v2', 'synllm': '2508.08529v1',
     'causal': '2407.10020v1'}


def a(p, cid):
    return f'{P[p]}_{cid}'


Q = [
    ('H01', 'table', 'In the metadata-driven RAG study on FinanceBench, what F1-scores did the Naive RAG baseline, the '
     'best-performing architecture and the authors’ proposed custom-reranker architecture achieve, and which configuration '
     'performed worst?', [
        ('H01.1', 'Naive RAG baseline F1 = 32.9.', [[a('meta', 'c0036')], [a('meta', 'table_de629a5f57790c34_1')]]),
        ('H01.2', 'Best: Architecture 4 (filtering, rewriting, Cohere reranker on contextual chunks) F1 = 44.4; proposed custom '
         'metadata-aware reranker F1 = 43.2.', [[a('meta', 'c0036')]]),
        ('H01.3', 'Worst: hybrid retrieval on standard chunks without reranking, F1 = 30.4 (below Naive RAG).',
         [[a('meta', 'c0036')], [a('meta', 'c0037')], [a('meta', 'table_de629a5f57790c34_2')]])]),
    ('H02', 'numeric', 'On M3ToolEval, how did CodeAct compare with text or JSON actions, and how large was the gap between the '
     'best open-source and closed-source models?', [
        ('H02.1', 'CodeAct had higher success for 12 of 17 LLMs and needed fewer average turns for 12 of 17.', [[a('codeact', 'c0011')]]),
        ('H02.2', 'Best model gpt-4-1106-preview: +20.7% absolute success over the next-best format (text) with 2.1 fewer turns '
         'on average.', [[a('codeact', 'c0011')]]),
        ('H02.3', 'Best open-source model 13.4% vs gpt-4-1106-preview 74.4%.', [[a('codeact', 'c0011')]])]),
    ('H03', 'table', 'Which domains and source datasets make up CodeActInstruct, and how many instances does each contribute '
     'for trajectory generation?', [
        ('H03.1', 'Web search: HotpotQA 3,000; math reasoning: MATH 5,586.',
         [[a('codeact', 'table_624c7108f2ab0b02_1'), a('codeact', 'table_624c7108f2ab0b02_2')]]),
        ('H03.2', 'Code generation: APPS 4,439; tabular reasoning: WikiTableQuestion 3,000; embodied planning: ALFWorld 3,553.',
         [[a('codeact', 'table_624c7108f2ab0b02_3'), a('codeact', 'table_624c7108f2ab0b02_4'),
           a('codeact', 'table_624c7108f2ab0b02_5')]])]),
    ('H04', 'multi-paper', 'How do QuantMCP and the metadata-driven financial RAG architecture each try to keep LLM answers '
     'about financial information accurate?', [
        ('H04.1', 'QuantMCP: the LLM decides what data is needed and calls MCP tools; all specific financial data points are '
         'fetched from live authoritative APIs rather than the model’s memory, returned in structured form.',
         [[a('quant', 'c0010')], [a('quant', 'c0009')]]),
        ('H04.2', 'Metadata-driven RAG: LLM-generated document- and chunk-level metadata, pre-retrieval file filtering and query '
         'rewriting, metadata-enriched (contextual) chunk embeddings and reranking to retrieve better evidence from filings.',
         [[a('meta', 'c0002')], [a('meta', 'c0000')]])]),
    ('H05', 'numeric', 'In AgentLAB, how did long-horizon attacks compare with a one-shot injection baseline, how vulnerable was '
     'GPT-5.1, and which agent resisted?', [
        ('H05.1', 'GPT-4o ASR rose from 62.50% (one-shot) to 79.9% (long-horizon).', [[a('agentlab', 'c0020')]]),
        ('H05.2', 'Average ASR on GPT-5.1 exceeded about 70%.', [[a('agentlab', 'c0020')]]),
        ('H05.3', 'Claude-4.5 had 0% ASR under both attack strategies.', [[a('agentlab', 'c0020')]])]),
    ('H06', 'qualitative', 'In the study of persona assignments for LLM agents, which kinds of agent tasks were most and least '
     'sensitive to demographic personas, and how large were the largest reported drops?', [
        ('H06.1', 'Technical tasks (OS Interaction, Database) were relatively stable, typically within 2–5%.', [[a('persona', 'c0008')]]),
        ('H06.2', 'Multi-step reasoning/planning tasks were most vulnerable: DeepSeek V3 Card Game down up to 26.2%; ALFWorld '
         'shifts up to 14%.', [[a('persona', 'c0008')], [a('persona', 'c0009')]]),
        ('H06.3', 'GPT-4o-mini dropped up to 19% under racial personas.', [[a('persona', 'c0008')]])]),
    ('H07', 'numeric', 'How did SkillSentry change LLM agents’ task success and runtime cost?', [
        ('H07.1', 'Average task success rose from 62.6% to 77.7% across four agent-model configurations (24.1% relative).',
         [[a('skill', 'c0030')]]),
        ('H07.2', 'Inference turns +7.8% and token cost +8.7%.', [[a('skill', 'c0033')]]),
        ('H07.3', 'SkillSentry’s own computation was about 0.8% of total execution time.', [[a('skill', 'c0033')]])]),
    ('H08', 'limitations', 'What dataset was SpeechT-RAG evaluated on, and what limitation do the authors attribute to that '
     'choice?', [
        ('H08.1', 'DAIC-WOZ: 189 clinical interview recordings; results on the development set (35 interviews, 12 depressed).',
         [[a('speech', 'c0014')]]),
        ('H08.2', 'Reliance on a single dataset (the only public speech-depression resource) may limit generalizability; scarcity '
         'stems from privacy and ethical constraints on mental-health data.', [[a('speech', 'c0023')]])]),
    ('H09', 'qualitative', 'In SynLLM, which prompting strategy gave the best privacy–utility balance, what trade-off did '
     'example-based prompts show, and what limitation applies to its privacy evaluation?', [
        ('H09.1', 'ClinRule (no data examples, only declarative clinical rules) achieved the highest harmonic privacy–utility '
         'scores.', [[a('synllm', 'c0034')]]),
        ('H09.2', 'Prompts with real data examples gave high TSTR/distributional scores but increased privacy risk.',
         [[a('synllm', 'c0034')]]),
        ('H09.3', 'Privacy metrics are heuristic/empirical; formal differential privacy or white-box adversarial testing is left '
         'to future work.', [[a('synllm', 'c0035')]])]),
    ('H10', 'limitations', 'In the medical-guideline causality extraction study, how did BERT-family models compare with GPT-4 '
     'and LLAMA2, and what limited LLAMA2’s practical use?', [
        ('H10.1', 'BioBERT average F1 0.72; LLAMA2 average Jaccard distance 0.40.', [[a('causal', 'c0031')]]),
        ('H10.2', 'LLAMA2 did not predict labels for many cases, which the authors say limits its practical application, '
         'possibly because it was fine-tuned on a small dataset. Separately, in evaluation the authors report omitting 38%, '
         '21% and 26% of labels (at 3, 5 and 10 epochs) because they focused on the accuracy of actual predictions.',
         [[a('causal', 'c0030')]]),
        ('H10.3', 'The paper concludes BERT-based models remain state of the art for causality extraction. It also reports '
         'that GPT-4 performs strongly on cause-effect relationships without fine-tuning but, unlike GPT-3.5, cannot handle '
         'token classification, which limits the traditional phrase-extraction approach.', [[a('causal', 'c0030')]])]),
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

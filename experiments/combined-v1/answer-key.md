# fresh-business-v1 answer key (AI-assisted; pending Codex review and human sign-off)

## G01 (single-paper)

A client's risk committee asks whether market mechanisms, not only regulation, can govern AI risk. What market mechanisms does the 'AI Governance through Markets' paper propose, how do they connect AI risk to financial risk, and what limits do the authors acknowledge?

- **G01.1** Four market-governance vectors: insurance, auditing, procurement and due diligence. *[2501.17755v2_c0000 or 2501.17755v2_c0003]*
- **G01.2** They serve risk distribution, information discovery, protocolisation and capital allocation, decreasing AI risk by pricing, measuring and mitigating it. *[2501.17755v2_c0003]*
- **G01.3** Insurance can make safety-washing or underestimating AI risk less appealing; actuarial rigour can curb AI hype. *[2501.17755v2_c0011]*
- **G01.4** The authors do not claim market forces alone adequately protect societal interests; standardised AI disclosures are needed alongside market mechanisms. *[2501.17755v2_c0000]*

## G02 (single-paper)

A multinational client must align its AI risk management across the EU, the U.S., the UK and China. According to the cross-regional study of AI risk-management frameworks, how do the four regimes differ and what trade-off does each carry?

- **G02.1** EU: structured, risk-based framework prioritising transparency and conformity assessments. *[2503.05773v1_c0001]*
- **G02.2** U.S.: decentralised, sector-specific regulation that promotes innovation but may fragment enforcement. *[2503.05773v1_c0001]*
- **G02.3** UK: flexible, sector-specific strategy enabling agile responses but risking inconsistent coverage across domains. *[2503.05773v1_c0001]*
- **G02.4** China: centralised directives enable rapid large-scale implementation while constraining public transparency and external oversight. *[2503.05773v1_c0001]*

## G03 (cross-paper)

A client must defend a customer-facing LLM against new jailbreaks. How do Safety Context Retrieval (SCR) and two-stage adversarial tuning differ in approach, how effective were they, and what did each cost in normal-task performance or effort?

- **G03.1** SCR keeps a pool of safety contexts, adds a minimal set of safety samples when a new jailbreak is identified, and retrieves a few at inference, instead of repeatedly fine-tuning. *[2505.15753v1_c0003]*
- **G03.2** SCR reduced average ASR against GCG-T from 34.9% (no defence) to 2.5%. *[2505.15753v1_c0018]*
- **G03.3** SCR had negligible effect on natural performance (e.g. Llama-3.1 HumanEval 61.6% to 57.3%, MMLU 62.6% to 63.2%). *[2505.15753v1_c0021]*
- **G03.4** Adversarial tuning is two-stage: hierarchical meta-universal (token-level) adversarial prompts, then automatic semantic-level adversarial prompts, used to fine-tune on adversarial prompt and safe-response pairs. *[2406.06622v1_c0000]*
- **G03.5** Two components, both required for 1 (one alone scores 0.5). (a) On the two target models, Llama-2-7B-chat and Vicuna-13B-v1.5, known jailbreaks gave average ASR of 66.54% / 51.38% and 19.62% / 9.62% under two metrics; adversarial tuning reduced them to 2.69% / 0.00% and 3.08% / 0.00%. The passage reports these pairs "respectively" without readable metric labels, so an answer may report them as pairs; assigning a pair to a specific model or metric as fact is an unsupported attribution. (b) Effort/cost: the passages give no compute-cost figure for adversarial tuning itself (it uses LoRA to improve training efficiency); an answer must say the cost is not established. Presenting the 20-minute GCG prompt-generation figure as the cost of adversarial tuning is a misattribution. *[2406.06622v1_c0021 + 2406.06622v1_c0019 + 2406.06622v1_c0015]*

## G04 (cross-paper)

A client plans custom GPT-style assistants with uploaded knowledge files and fine-tuning services for business units. What do the Pandora and 'Attack via Overfitting' studies show about these customisation routes as jailbreak attack surfaces, how successful were the attacks, and how detectable are they?

- **G04.1** Pandora poisons RAG: malicious content uploaded as knowledge files plus crafted prompts makes GPTs jailbreak indirectly. *[2402.08416v1_c0003]*
- **G04.2** Pandora success 64.3% on GPT-3.5 and 34.8% on GPT-4 across four prohibited scenarios, versus 3.0% and 1.0% for naive malicious questions. *[2402.08416v1_c0016]*
- **G04.3** The overfitting attack fine-tunes on 10 benign QA pairs: first with identical refusal answers to induce overfitting, then with normal answers, after which the model complies with harmful questions. *[2510.02833v4_c0003]*
- **G04.4** It reached 94.84% average ASR across ten LLMs (HS 4.48), comparable to malicious fine-tuning (97.25%). *[2510.02833v4_c0016]*
- **G04.5** Two components, both required for 1 (one alone scores 0.5): (a) because the data is entirely benign it is stealthy against moderation models, which catch malicious fine-tuning; (b) it bypassed a token-wise loss defence. *[2510.02833v4_c0005 or 2510.02833v4_c0027]*

## G05 (cross-paper)

A hospital-network client is assessing LLMs for patient-facing conversations. How did the Polaris and AI Hospital studies evaluate conversational medical LLMs, and what do their results imply about readiness?

- **G05.1** Polaris is a constellation (about one trillion parameters) of a primary conversational agent and specialist support agents for nurse, social-worker and nutritionist tasks, to increase safety and reduce hallucinations. *[2403.13313v1_c0000]*
- **G05.2** Over 1,100 U.S. nurses and 130 physicians posed as patients; Polaris performed on par with human nurses on aggregate across medical safety, clinical readiness, patient education, conversational quality and bedside manner. *[2403.13313v1_c0001]*
- **G05.3** Polaris's specialist agents significantly outperformed GPT-4 and LLaMA-2 70B on task-based evaluation. *[2403.13313v1_c0001]*
- **G05.4** AI Hospital simulates multi-agent clinical interaction and evaluates Doctor agents on the MVME benchmark of Chinese medical records (symptom collection, examinations, diagnosis). *[2402.09742v4_c0000]*
- **G05.5** Interactive LLMs reached less than 50% of the one-step GPT-4 upper bound on diagnosis, rationale and treatment accuracy; a dispute-resolution collaborative mechanism improves performance only to a certain degree and still falls short of the upper bound. Stating the improvement without that limitation scores at most 0.5. *[2402.09742v4_c0004]*

## G06 (numerical/table)

A client relies on AI vendors' public safety commitments. How well did AI companies implement their 2023 White House voluntary commitments: overall scores, the best and worst performers, which commitment was weakest, and which looked strongest?

- **G06.1** 16 companies scored; mean 53.3% (median 50.0%); OpenAI highest at 83.3%, Apple lowest at 13.3%. *[2508.08345v2_c0018]*
- **G06.2** The six Frontier Model Forum members are the highest-scoring companies. "At least 66%" (results) and "at least 60%" (introduction) are compatible lower bounds, and either may be quoted with its attribution. The group statistics must be supported by the results passage: FMF mean 74.4% (SD 6.9%); the other 10 companies score at or below 60% (mean 40.7%, SD 11.4%). *[2508.08345v2_c0019]*
- **G06.3** Model-weight security averaged 17%; 11 of the 16 companies scored 0%. *[2508.08345v2_c0000 or 2508.08345v2_c0005]*
- **G06.4** Watermarking/provenance scored highest (92.2%), but often vacuously because many companies do not build audio or visual models. *[2508.08345v2_c0021]*

## G07 (numerical/table)

A finance client wants natural-language querying of financial statements. What accuracy and speed did FinStat2SQL achieve, how did it compare with proprietary models and with its untuned base model, and what limits apply?

- **G07.1** The fine-tuned 7B model reached 61.33% accuracy with sub-4-second responses on consumer hardware, outperforming GPT-4o-mini. *[2506.23273v2_c0000]*
- **G07.2** Best proprietary model Gemini-2.0-Flash-Thinking 72.03%; GPT-4o-mini 59.14%. *[2506.23273v2_table_4d7c993521f0bf29_1 + 2506.23273v2_table_4d7c993521f0bf29_6 or 2506.23273v2_c0017 + 2506.23273v2_table_4d7c993521f0bf29_6]*
- **G07.3** Fine-tuning lifted the 7B Qwen2.5-Coder-Instruct from 47.93% to 61.33% (finstat2sql is a fine-tuned Qwen 2.5 Coder for each model size). *[2506.23273v2_table_d472857c5172bfd0_1 + 2506.23273v2_table_d472857c5172bfd0_4 + 2506.23273v2_c0014]*
- **G07.4** Limits: only VN30/HNX30-listed firms (no SMEs), Vietnamese terminology issues, and untested beyond Vietnam (e.g. US GAAP). *[2506.23273v2_c0018]*

## G08 (numerical/table)

A client wants to harden an open-weight model against jailbreaks. What does the fail-closed alignment study report about why standard alignment fails, attack success, benign compliance, output quality and compute cost, and on which models was it tested?

- **G08.1** Standard alignment encodes refusal along a single activation direction that prompt-based jailbreaks suppress, so it behaves fail-open. *[2602.16977v1_c0028]*
- **G08.2** At most 4% ASR in all cases; average ASR reduced by 92.3–97.2%, versus 23.8–93.7% for baselines. *[2602.16977v1_c0019]*
- **G08.3** Highest compliance on benign prompts among robust methods (86% on average). *[2602.16977v1_c0003]*
- **G08.4** 61.6% average accuracy versus 62.0% for CAT, with only a small constant-factor overhead over standard fine-tuning. The gap may be given as the calculated 0.4 percentage points (about 0.65% relative) or as the paper's reported "0.8%" attributed to the paper; presenting 0.8 as the calculated percentage-point gap scores 0.5. *[2602.16977v1_c0020]*
- **G08.5** Tested on four open instruction-tuned models of 2–9B parameters: Llama2-7B, Llama3-8B, Gemma2-2B and Gemma2-9B. *[2602.16977v1_c0018]*

## G09 (partially unanswerable)

A legal-services client wants AI statute retrieval for colloquial client questions under English and EU law. How does LegalMALR work, what retrieval results did it achieve, how well does it perform on English or EU statutes, and what does it cost per query?

- **G09.1** Multi-agent query understanding produces diverse legally grounded reformulations with iterative dense retrieval; a zero-shot commercial LLM (Qwen-Max) reranks the candidates. *[2601.17692v1_c0004 or 2601.17692v1_c0012]*
- **G09.2** MAS with GRPO reached Recall@14 0.8396 and HitRate@14 0.9320 on STARD, and recall 0.7478 with HitRate@14 1.0 on CSAID. *[2601.17692v1_c0041]*
- **G09.3** English/EU performance is not established: the framework was developed and evaluated only on Chinese statutes and Chinese-language queries. *[2601.17692v1_c0053 or 2601.17692v1_c0004]*
- **G09.4** No monetary per-query cost is reported. Answers may cite the stated computational cost proxies (1-4 retrieval rounds, 30-120 embedding calls, about 13.58 candidates passed to the commercial LLM reranker, whose per-token cost is higher than lightweight rerankers; c0035, c0048, c0052). Any monetary per-query price not supported by the study is fabricated (correction 9, Codex review). *[no anchor: must be stated as not established]*

## G10 (partially unanswerable)

A client is piloting autonomous multi-agent LLM systems that share a common resource. What did the study 'Is Lying an Emergent Behaviour in LLMs?' find about agents lying and its effects, and how often do deployed commercial AI agents lie to customers?

- **G10.1** Setting: an agent-based sustainability game in which agents are told resources regenerate although they do not; agents can observe neighbours, declare attacks, be permitted to lie and see reputation. *[2606.28456v1_c0000]*
- **G10.2** Agents lied in 44% of declarations even when not permitted, rising to 65% when permitted: permission amplifies an existing tendency. *[2606.28456v1_c0035]*
- **G10.3** Declarations cut extinction from 40% to 7% and raised coexistence from 60% to 88%. *[2606.28456v1_c0031]*
- **G10.4** Two components, both required for 1 (one alone scores 0.5): (a) deployed commercial agents' lying rates are not established by the study; (b) because it is a simplified simulation (identical agents, fixed network), not a real-world deployment. A stated real-world lying rate scores 0 and counts as a misleading claim. *[2606.28456v1_c0045 or 2606.28456v1_c0002]*

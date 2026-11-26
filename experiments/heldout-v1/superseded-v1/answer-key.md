# Held-out answer key (heldout-v1) - for independent human review

Written before any model run on these questions; no retrieval was run to choose them. Papers were selected only
from the 23 corpus papers never mentioned in any prior question, reference, label, test or live-run file.
Reviewer: for each point, confirm the expected statement is entailed by the quoted passage, then sign below.

## H01 (table)

**Question.** In the metadata-driven RAG study on FinanceBench, what F1-scores did the Naive RAG baseline, the best-performing architecture and the authors’ proposed custom-reranker architecture achieve, and which configuration performed worst?

- **H01.1** Naive RAG baseline F1 = 32.9.
  - Anchors (any one group suffices): [['2510.24402v1_c0036'], ['2510.24402v1_table_de629a5f57790c34_1']]
- **H01.2** Best: Architecture 4 (filtering, rewriting, Cohere reranker on contextual chunks) F1 = 44.4; proposed custom metadata-aware reranker F1 = 43.2.
  - Anchors (any one group suffices): [['2510.24402v1_c0036']]
- **H01.3** Worst: hybrid retrieval on standard chunks without reranking, F1 = 30.4 (below Naive RAG).
  - Anchors (any one group suffices): [['2510.24402v1_c0036'], ['2510.24402v1_c0037'], ['2510.24402v1_table_de629a5f57790c34_2']]

**Source passages (verbatim from the pinned index):**

> `2510.24402v1_c0036` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; results and analysis)
>
> The primary results for all evaluated architectures are consolidated in Table 1. The pipelines are assessed across key quality metrics from the RAGChecker framework, including overall F1-Score, Precision, and Recall, as well as diagnostic metrics for retrieval quality (Claim Recall, Context Precision) and generator performance (Faithfulness, Hallucination). At a high level, the results demonstrate a clear and progressive improvement in performance as architectural complexity and metadata integration increase. Our central hypothesis, that a sophisticated, metadata-driven architecture can yield significant gains, is strongly validated by the results. The most successful architectures were those that integrated multiple advanced components. The peak F1-score of 44.4 was achieved by Architecture 4, which utilized Filtering, Rewriting, and a commercial Cohere Reranker on Contextual Chunks (Ctx). Crucially, our proposed architecture, which substitutes the commercial reranker with our custom, metadata-aware model, achieved a highly competitive F1-score of 43.2. This result is a cornerstone of our findings, representing a 31% relative improvement over the Naive RAG baseline (F1-score: 32.9) while operating faster and at zero marginal cost compared to the commercial alternative. This demonstrates that a well-designed, open-source approach can achieve performance nearly on par with black-box commercial systems, presenting a compelling trade-off for practical applications. At the other end of the spectrum, the weakest performing model was the Hybrid Retrieval on standard chunks without a reranking step (F1-score: 30.4), underperforming even the Naive RAG baseline

> `2510.24402v1_table_de629a5f57790c34_1` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; Results and Analysis)
>
> Derived source table row (HTML cell serialization, not verbatim prose). Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering Table 1: Comprehensive Performance of All Evaluated RAG Architectures Architecture: Naive RAG; Chunk Type: Std; Prec: 35.0; Recall: 52.7; F1-score: 32.9; Claim Recall: 45.9; Context Precision: 20.0; Faith.: 76.4; Halluc.: 18.5; Mean Latency (s): 10.47

> `2510.24402v1_c0037` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; results and analysis)
>
> . At the other end of the spectrum, the weakest performing model was the Hybrid Retrieval on standard chunks without a reranking step (F1-score: 30.4), underperforming even the Naive RAG baseline. This highlights a critical finding: advanced retrieval strategies like hybrid search can introduce noise and degrade performance if not paired with a robust reranking mechanism. Comprehensive Performance of All Evaluated RAG Architectures

> `2510.24402v1_table_de629a5f57790c34_2` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; Results and Analysis)
>
> Derived source table row (HTML cell serialization, not verbatim prose). Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering Table 1: Comprehensive Performance of All Evaluated RAG Architectures Architecture: Hybrid Retrieval; Chunk Type: Std; Prec: 35.0; Recall: 46.1; F1-score: 30.4; Claim Recall: 41.1; Context Precision: 16.1; Faith.: 67.9; Halluc.: 26.0; Mean Latency (s): 12.31

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H02 (numeric)

**Question.** On M3ToolEval, how did CodeAct compare with text or JSON actions, and how large was the gap between the best open-source and closed-source models?

- **H02.1** CodeAct had higher success for 12 of 17 LLMs and needed fewer average turns for 12 of 17.
  - Anchors (any one group suffices): [['2402.01030v4_c0011']]
- **H02.2** Best model gpt-4-1106-preview: +20.7% absolute success over the next-best format (text) with 2.1 fewer turns on average.
  - Anchors (any one group suffices): [['2402.01030v4_c0011']]
- **H02.3** Best open-source model 13.4% vs gpt-4-1106-preview 74.4%.
  - Anchors (any one group suffices): [['2402.01030v4_c0011']]

**Source passages (verbatim from the pinned index):**

> `2402.01030v4_c0011` (Executable Code Actions Elicit Better LLM Agents; codeact makes llms better agents)
>
> Within each turn, the model can either emit an action or propose an answer to be verified by an exact match with the ground-truth solution. The interaction will terminate when a maximum of 10 interaction turns are reached or a correct solution has been submitted, similar to ( Wang et al., 2023e ) . Metric. We measure the success rate by calculating the percentage of the model proposed answers that match the ground-truth solutions. We also include the avg. turns metric: the average number of turns on all evaluated instances. Quantitative Results on M 3 ToolEval. We include full results in Tab. 3 and a subset of results for visualization in Fig. 1 . CodeAct generally has a higher task success rate (12 out of 17 evaluated LLMs), similar to the trend in § 2.2 . Moreover, using CodeAct requires a lower average number of turns (12 out of 17 evaluated LLMs). For example, the best model gpt-4-1106-preview achieves a 20.7 % absolute improvement compared to the next best action format (text) while requiring 2.1 fewer interaction turns on average. However, there is still a significant gap in terms of absolute CodeAct performance between open- and closed-source LLMs as the best open-source model achieving 13.4% while the best closed-source model gpt-4-1106-preview 74.4%. This is potentially due to open-source models’ weak task-solving capability and inability to follow complex instructions without demonstration, suggesting an urgent need to improve open-source LLMs for practical, real-world tasks under the zero-shot setting. Example multi-turn interaction with Python packages using CodeActAgent (Mistral-7b). No in-context demonstrations are provided to the model. Some messages are omitted for space. See https://chat.xwang.dev/r/Vqn108G for complete interaction.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H03 (table)

**Question.** Which domains and source datasets make up CodeActInstruct, and how many instances does each contribute for trajectory generation?

- **H03.1** Web search: HotpotQA 3,000; math reasoning: MATH 5,586.
  - Anchors (any one group suffices): [['2402.01030v4_table_624c7108f2ab0b02_1', '2402.01030v4_table_624c7108f2ab0b02_2']]
- **H03.2** Code generation: APPS 4,439; tabular reasoning: WikiTableQuestion 3,000; embodied planning: ALFWorld 3,553.
  - Anchors (any one group suffices): [['2402.01030v4_table_624c7108f2ab0b02_3', '2402.01030v4_table_624c7108f2ab0b02_4', '2402.01030v4_table_624c7108f2ab0b02_5']]

**Source passages (verbatim from the pinned index):**

> `2402.01030v4_table_624c7108f2ab0b02_1` (Executable Code Actions Elicit Better LLM Agents; )
>
> Derived source table row (HTML cell serialization, not verbatim prose). Executable Code Actions Elicit Better LLM Agents Table A.9 : CodeActInstruct components and the number of instances for training trajectory generation. Domain: Web Search; Capability: Information seeking through search API; Dataset: HotpotQA ( Yang et al., 2018 ); # of Instances: 3,000

> `2402.01030v4_table_624c7108f2ab0b02_2` (Executable Code Actions Elicit Better LLM Agents; )
>
> Derived source table row (HTML cell serialization, not verbatim prose). Executable Code Actions Elicit Better LLM Agents Table A.9 : CodeActInstruct components and the number of instances for training trajectory generation. Domain: Math Reasoning; Capability: Math problem-solving using math Libraries in Python (e.g., sympy ); Dataset: MATH ( Hendrycks et al., 2021a ); # of Instances: 5,586

> `2402.01030v4_table_624c7108f2ab0b02_3` (Executable Code Actions Elicit Better LLM Agents; )
>
> Derived source table row (HTML cell serialization, not verbatim prose). Executable Code Actions Elicit Better LLM Agents Table A.9 : CodeActInstruct components and the number of instances for training trajectory generation. Domain: Code Generation; Capability: Self-debug from Python error messages and traceback; Dataset: APPS ( Hendrycks et al., 2021b ); # of Instances: 4,439

> `2402.01030v4_table_624c7108f2ab0b02_4` (Executable Code Actions Elicit Better LLM Agents; )
>
> Derived source table row (HTML cell serialization, not verbatim prose). Executable Code Actions Elicit Better LLM Agents Table A.9 : CodeActInstruct components and the number of instances for training trajectory generation. Domain: Tabular Reasoning; Capability: Tabular Reasoning using pandas and sqlite3 (for SQL) library; Dataset: WikiTableQuestion ( Pasupat & Liang, 2015 ); # of Instances: 3,000

> `2402.01030v4_table_624c7108f2ab0b02_5` (Executable Code Actions Elicit Better LLM Agents; )
>
> Derived source table row (HTML cell serialization, not verbatim prose). Executable Code Actions Elicit Better LLM Agents Table A.9 : CodeActInstruct components and the number of instances for training trajectory generation. Domain: Embodied Planning; Capability: Interact with embodied environments through APIs; Dataset: ALFWorld ( Shridhar et al., 2020 ); # of Instances: 3,553

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H04 (multi-paper)

**Question.** How do QuantMCP and the metadata-driven financial RAG architecture each try to keep LLM answers about financial information accurate?

- **H04.1** QuantMCP: the LLM decides what data is needed and calls MCP tools; all specific financial data points are fetched from live authoritative APIs rather than the model’s memory, returned in structured form.
  - Anchors (any one group suffices): [['2506.06622v2_c0010'], ['2506.06622v2_c0009']]
- **H04.2** Metadata-driven RAG: LLM-generated document- and chunk-level metadata, pre-retrieval file filtering and query rewriting, metadata-enriched (contextual) chunk embeddings and reranking to retrieve better evidence from filings.
  - Anchors (any one group suffices): [['2510.24402v1_c0002'], ['2510.24402v1_c0000']]

**Source passages (verbatim from the pinned index):**

> `2506.06622v2_c0010` (QuantMCP: Grounding Large Language Models in Verifiable Financial Reality; the quantmcp framework)
>
> A cornerstone of the QuantMCP framework is its commitment to data accuracy. Unlike approaches where an LLM might attempt to recall financial data from its training corpus (which is static and prone to inaccuracies or outdatedness), QuantMCP strictly mandates that all specific financial data points are fetched from live, authoritative APIs at the time of the query (or from the most recent available data from the API). The LLM’s role is to understand what data is needed and how to ask for it via the MCP tools, not to provide the data itself from its internal knowledge. This ”grounding” in external, verifiable sources is the primary mechanism by which QuantMCP mitigates the risk of LLM hallucination in the context of financial data retrieval. The structured nature of API responses, further standardized into JSON or similar formats by the API adapters, also ensures that the LLM receives data in a clear, unambiguous format, reducing the chance of misinterpretation during subsequent analytical tasks.

> `2506.06622v2_c0009` (QuantMCP: Grounding Large Language Models in Verifiable Financial Reality; the quantmcp framework)
>
> . This step is fundamental to overcoming LLM hallucination, as the LLM’s subsequent analysis or response generation is based on this verifiably accurate dataset. LLM for Analysis, Synthesis, and Decision Support: Once the LLM receives the structured, grounded data from the MCP Server, its role shifts from query understanding to data utilization. It can now perform a wide range of analytical tasks, such as summarizing retrieved data, identifying trends or anomalies, performing calculations or comparisons, generating textual explanations based on the data, and providing contextually relevant information that can support human investment decisions or feed into more complex algorithmic trading strategies. This is where QuantMCP truly empowers the LLM, transforming it into a sophisticated analytical assistant that operates on a foundation of trustworthy information. A typical workflow based on QuantMCP can be summarized as follows: A user poses a natural language query. The LLM (NLI Layer) parses this query and determines the need to invoke one or more financial tools. It then interacts with the MCP Server, providing the appropriate tool name(s) and extracted parameters. The MCP Server invokes the tool(s), which utilize external financial APIs to retrieve data, structure it, and then return it to the LLM. Finally, the LLM processes this grounded data to generate an analytical response, a summary, or further questions to the user, potentially leading to iterative data retrieval and analysis cycles. This entire process is designed to be transparent to the end-user, who experiences it as a seamless natural language conversation leading to accurate, data-backed financial insights.

> `2510.24402v1_c0002` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; introduction)
>
> . To address these challenges, this paper proposes a novel metadata-driven, multi-stage RAG architecture that treats documents not as flat collections of chunks but as hierarchical knowledge structures. Our methodology begins with an offline pipeline in which LLMs generate multi-level metadata: document-level summaries, key entities, and thematic clusters, followed by chunk-level enrichments such as parent cluster references, associated entities, potential question-answer pairs, and “retrieval nuggets” of implicit knowledge. Building on this metadata-rich foundation, we design an architecture that integrates pre-retrieval intelligence, metadata-enriched embeddings, and post-retrieval refinement. Specifically, our study systematically investigates three intervention strategies: Pre-Retrieval Optimization: Using document-level metadata for intelligent file filtering and query rewriting, thereby narrowing the search space before retrieval begins. Post-Retrieval Refinement: Expanding search results through metadata-driven entity and cluster exploration, and applying a custom reranker that combines semantic and metadata relevance. Semantic Embedding Enrichment: Embedding chunks together with their metadata to create contextually richer vectors that better capture financial semantics. Our findings show that combining file filtering, query rewriting, and metadata-enriched “contextual chunks” significantly improves performance compared to both baseline RAG and other advanced retrieval configurations. We validate our approach on the FinanceBench dataset ( Islam et al., 2023 ) , a specialized benchmark for financial question answering, and measure reliability with the RAGChecker evaluation framework ( Ru et al., 2024 )

> `2510.24402v1_c0000` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; abstract)
>
> Retrieval-Augmented Generation (RAG) struggles on long, structured financial filings where relevant evidence is sparse and cross-referenced. This paper presents a systematic investigation of advanced metadata-driven Retrieval-Augmented Generation (RAG) techniques, proposing and evaluating a novel, multi-stage RAG architecture that leverages LLM-generated metadata. We introduce a sophisticated indexing pipeline to create contextually rich document chunks and benchmark a spectrum of enhancements, including pre-retrieval filtering, post-retrieval reranking, and enriched embeddings, benchmarked on the FinanceBench dataset. Our results reveal that while a powerful reranker is essential for precision, the most significant performance gains come from embedding chunk metadata directly with text ("contextual chunks"). Our proposed optimal architecture combines LLM-driven pre-retrieval optimizations with these contextual embeddings to achieve superior performance. Additionally, we present a custom metadata reranker that offers a compelling, cost-effective alternative to commercial solutions, highlighting a practical trade-off between peak performance and operational efficiency. This study provides a blueprint for building robust, metadata-aware RAG systems for financial document analysis.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H05 (numeric)

**Question.** In AgentLAB, how did long-horizon attacks compare with a one-shot injection baseline, how vulnerable was GPT-5.1, and which agent resisted?

- **H05.1** GPT-4o ASR rose from 62.50% (one-shot) to 79.9% (long-horizon).
  - Anchors (any one group suffices): [['2602.16901v1_c0020']]
- **H05.2** Average ASR on GPT-5.1 exceeded about 70%.
  - Anchors (any one group suffices): [['2602.16901v1_c0020']]
- **H05.3** Claude-4.5 had 0% ASR under both attack strategies.
  - Anchors (any one group suffices): [['2602.16901v1_c0020']]

**Source passages (verbatim from the pinned index):**

> `2602.16901v1_c0020` (AgentLAB: Benchmarking LLM Agents against Long-Horizon Attacks; evaluation)
>
> Table 2 reports the average effectiveness (ASR) of long-horizon attacks on varied LLM agents. The results reveal that both open-weight and proprietary agents, even those based on frontier LLM, are highly vulnerable to long-horizon attacks. For example, the average ASR on GPT-5.1 exceeds about 70%, suggesting that long-horizon attacks represent a fundamental challenge for LLM agent safety rather than a limitation specific to particular model architectures or training procedures. These findings corroborate prior observations that multi-turn attacks pose critical safety risks that are inadequately addressed by the safety guardrails in existing LLMs that are designed mainly against one-shot, static threats ( Rahman et al., 2025 ; Li et al., 2024 ) . Comparison of the attack effectiveness of one-shot and long-horizon injection attacks. To evaluate long-horizon attacks against conventional one-shot counterparts, we compare against the “important message” attack ( Debenedetti et al., 2024 ) , which injects a message instructing the agent to prioritize the malicious task over the benign one. As shown in Table 3 , the long-horizon attack substantially outperforms the one-shot baseline across most agents. For GPT-4o, the ASR increases from 62.50% to 79.9%, confirming that gradual behavioral diversion is more effective than direct injection. Notably, Claude-4.5 demonstrates strong inherent resistance to prompt injection, achieving 0% ASR under both attack strategies. Evaluation of baseline defenses against long-horizon attacks. ASR (%) vs. T2S across five attack categories for six LLM-based agents. Upper-left indicates higher vulnerability; lower-right indicates greater robustness. Figure 6 breaks down attack effectiveness by type, contrasting ASR and T2S

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H06 (qualitative)

**Question.** In the study of persona assignments for LLM agents, which kinds of agent tasks were most and least sensitive to demographic personas, and how large were the largest reported drops?

- **H06.1** Technical tasks (OS Interaction, Database) were relatively stable, typically within 2–5%.
  - Anchors (any one group suffices): [['2602.12285v1_c0008']]
- **H06.2** Multi-step reasoning/planning tasks were most vulnerable: DeepSeek V3 Card Game down up to 26.2%; ALFWorld shifts up to 14%.
  - Anchors (any one group suffices): [['2602.12285v1_c0008'], ['2602.12285v1_c0009']]
- **H06.3** GPT-4o-mini dropped up to 19% under racial personas.
  - Anchors (any one group suffices): [['2602.12285v1_c0008']]

**Source passages (verbatim from the pinned index):**

> `2602.12285v1_c0008` (From Biased Chatbots to Biased Agents: Examining Role Assignment Effects on LLM ; results)
>
> Across all benchmarks and models, we observe that persona assignments consistently alter performance on agentic tasks , indicating that persona-induced biases extend beyond text generation and affect how agents carry out multi-step agentic tasks. Though these personas are essentially irrelevant to the tasks themselves, agents deviate from their baseline capabilities whenever a demographic identity is introduced for most of tasks tested. These effects range from small shifts to substantial degradation. GPT-4o-mini shows reductions of up to 19% under racial personas (Table 2 ), and DeepSeek V3 exhibits similarly large changes across gender, race, religion, and profession personas. Such variability suggests that LLM agents internalize socio-cognitive associations that inadvertently influence behavior even in tasks designed to be purely functional. Sensitivity to personas varies by benchmark. Technical tasks—OS Interaction and Database—remain relatively stable, typically fluctuating within 2–5%. In contrast, tasks requiring multi-step reasoning and planning show far greater vulnerability. DeepSeek V3’s Card Game accuracy decreases by up to 26.2%, and ALFWorld success rates shift by up to 14% across models. These results suggest that high-level reasoning is particularly susceptible to persona-induced disruptions. Gender persona effects on GPT-4o-mini. All scores are normalized to the model’s baseline. Dashed levels correspond to baseline performance.

> `2602.12285v1_c0009` (From Biased Chatbots to Biased Agents: Examining Role Assignment Effects on LLM ; results)
>
> Table 2 shows that assigning racial or geographic origin personas leads to substantial performance distortions. For DeepSeek V3, race- and origin-based roles induce some of the most severe degradations observed. Strategic reasoning tasks are particularly affected: Card Game performance drops by 26.2% under the from Africa persona and by 23.4% for Asian assignments. Qwen3 exhibits an equally pronounced failure mode, with the White persona causing a 23.8% reduction in Card Game accuracy (61.7% to 37.9%). Origin-based personas show highly mixed effects: identities such as from Africa or from America can produce large declines in some tasks (especially Card Game) but sometimes match or exceed baseline performance in others. These heterogeneous patterns indicate that racial and geographic personas can surface latent human-like stereotype biases, perturbing agentic task performance despite having no relevance to the underlying tasks. Figure 2 shows that assigning gendered personas induces task-dependent performance shifts in GPT-4o-mini. Overall, gender roles do not uniformly degrade performance; instead, they reshape behavior in ways that reflect stereotyped associations between gendered identities and task domains. Notably, the degradation in household planning tasks for Male -assigned agents reflects societal stereotypes about domestic competencies. Male role assignment produces the most consistent negative effects, with Card Game performance dropping to 90% of baseline and ALFWorld success falling to 88%. In contrast, Female roles improve ALFWorld (108% of baseline) while slightly degrading Database operations, and Non-Binary assignments yield the highest ALFWorld performance (112% of baseline) but reduce OS Interaction accuracy to 92%

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H07 (numeric)

**Question.** How did SkillSentry change LLM agents’ task success and runtime cost?

- **H07.1** Average task success rose from 62.6% to 77.7% across four agent-model configurations (24.1% relative).
  - Anchors (any one group suffices): [['2608.09253v1_c0030']]
- **H07.2** Inference turns +7.8% and token cost +8.7%.
  - Anchors (any one group suffices): [['2608.09253v1_c0033']]
- **H07.3** SkillSentry’s own computation was about 0.8% of total execution time.
  - Anchors (any one group suffices): [['2608.09253v1_c0033']]

**Source passages (verbatim from the pinned index):**

> `2608.09253v1_c0030` (SkillSentry: Reliable Skill Execution for LLM Agents via Runtime Assurance; evaluation)
>
> Results of Effectiveness Evaluation Overall Effectiveness. Table II shows the mean task success rate and standard deviation over five repeated evaluations for the base agents and SkillSentry across 15 skills and four agent-model configurations. The higher mean and lower standard deviation are highlighted in bold. Overall, SkillSentry consistently improves task success rates across all evaluated settings. Averaged across the 15 skills, SkillSentry achieves relative improvements of 29.5% and 22.7% for Claude Code with Claude-Haiku-4.5 and Claude-Opus-4.6, respectively, and 24.5% and 20.5% for Codex with GPT-5.2 and GPT-5.4, respectively. Across all four configurations, SkillSentry increases the average task success rate from 62.6% to 77.7% , corresponding to an overall relative improvement of 24.1% . The improvement is consistent across all agent-model configurations and skills. The gains are particularly pronounced on skills with low baseline performance, reaching 210.8% for excitation-signal-design , 131.6% for weighted-gdp-calc , and 199.2% for d3-visualization , with substantial gains also observed for pddl-skills and geospatial-analysis . For skills with strong baseline performance, the relative gains are smaller, yet SkillSentry still reduces residual failures, achieving perfect task success rates for glm-calibration across all four configurations and for several configurations of pcap-analysis , spring-boot-migration , and mesh-analysis . Overall, SkillSentry improves challenging skill executions while mitigating occasional failures on skills that already succeed in most runs. In addition to improving task success rates, SkillSentry generally produces more stable results across repeated evaluations

> `2608.09253v1_c0033` (SkillSentry: Reliable Skill Execution for LLM Agents via Runtime Assurance; evaluation)
>
> Results of Runtime Cost Table III reports the runtime costs of the base agents and SkillSentry . Averaged across the four agent-model configurations, SkillSentry increases the number of inference turns by 7.8% and the token cost by 8.7% . These additional costs mainly arise from delivering step-level guidance and prompting the agent to re-plan when deviations from the skill procedure are detected. Therefore, these additional inference costs represent a reasonable trade-off for correcting unreliable execution and achieving the effectiveness improvements reported in RQ1 . Results of the Runtime Efficiency Fig. 7 presents the runtime breakdown for Claude Code with Claude-Haiku-4.5. The computation performed by SkillSentry accounts for approximately 0.8% of the total execution time. This result indicates that SkillSentry introduces negligible computational overhead compared with LLM inference and tool execution. The runtime breakdowns for the other three agent-model configurations are similar and are available at [ 1 ] . Summary. SkillSentry introduces 7.8% more inference turns and 8.7% more token costs, while its own computation accounts for only 0.8% of the total execution time.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H08 (limitations)

**Question.** What dataset was SpeechT-RAG evaluated on, and what limitation do the authors attribute to that choice?

- **H08.1** DAIC-WOZ: 189 clinical interview recordings; results on the development set (35 interviews, 12 depressed).
  - Anchors (any one group suffices): [['2502.10950v2_c0014']]
- **H08.2** Reliance on a single dataset (the only public speech-depression resource) may limit generalizability; scarcity stems from privacy and ethical constraints on mental-health data.
  - Anchors (any one group suffices): [['2502.10950v2_c0023']]

**Source passages (verbatim from the pinned index):**

> `2502.10950v2_c0014` (SpeechT-RAG: Reliable Depression Detection in LLMs with Retrieval-Augmented Gene; experiments)
>
> The DAIC-WOZ dataset DeVault et al. (2014) is widely regarded as a benchmark resource for depression detection tasks. It comprises 189 recordings of clinical interviews conducted between interviewers and patients. Within the training set, 30 out of 107 interviews are labeled as depressed, while the development set contains 35 interviews, with 12 categorized as depressed. Following the practices of prior research, e.g. Gong and Poellabauer (2017) ; Shen et al. (2022) ; Wu et al. (2022) ; Wu et al. (2023a) , our experimental results are evaluated on the development set. We selected our evaluation models based on parameter efficiency and context processing capabilities. From the Llama2 family Touvron et al. (2023) , we included both base models (Llama2-7B, Llama2-13B) and their instruction-tuned variants (Llama2-7B Chat, Llama2-13B Chat) to assess the impact of instruction tuning. We also incorporated Llama3 models Dubey et al. (2024) (Llama3-8B-Instruct and Llama3-8B) for their enhanced context processing abilities. For Text-RAG baseline, we employed the SentenceTransformer Reimers and Gurevych (2019) model all-MiniLM-L6-v2 to compute embeddings and rank examples using cosine similarity, retrieving the top n examples (n = 1 or 2) from the training set.

> `2502.10950v2_c0023` (SpeechT-RAG: Reliable Depression Detection in LLMs with Retrieval-Augmented Gene; limitations)
>
> A key limitation of our study is its reliance on the DAIC-WOZ dataset. While this dataset represents the current standard in multimodal depression recognition research and remains the only publicly accessible resource for speech-based depression analysis, this singular focus may impact the generalizability of our findings. The scarcity of available datasets in this domain stems from the significant privacy and ethical considerations surrounding mental health data collection. Nevertheless, our approach of conducting comprehensive analysis on this widely-used benchmark aligns with established research practices in the field of speech depression detection.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H09 (qualitative)

**Question.** In SynLLM, which prompting strategy gave the best privacy–utility balance, what trade-off did example-based prompts show, and what limitation applies to its privacy evaluation?

- **H09.1** ClinRule (no data examples, only declarative clinical rules) achieved the highest harmonic privacy–utility scores.
  - Anchors (any one group suffices): [['2508.08529v1_c0034']]
- **H09.2** Prompts with real data examples gave high TSTR/distributional scores but increased privacy risk.
  - Anchors (any one group suffices): [['2508.08529v1_c0034']]
- **H09.3** Privacy metrics are heuristic/empirical; formal differential privacy or white-box adversarial testing is left to future work.
  - Anchors (any one group suffices): [['2508.08529v1_c0035']]

**Source passages (verbatim from the pinned index):**

> `2508.08529v1_c0034` (SynLLM: A Comparative Analysis of Large Language Models for Medical Tabular Synt; key observations and discussion)
>
> Our evaluation across three datasets, four prompt strategies, and 20 open-source LLMs reveals that models such as OpenChat 7B, Zephyr 7B, and Nous Hermes 34B consistently rank among the top performers across statistical, clinical, and privacy metrics. Notably, the ClinRule prompt, designed without any data examples, achieves the highest harmonic privacy–utility scores, demonstrating the effectiveness of constraint-driven generation under strong privacy requirements. Structured Prompting as a Privacy–Utility Lever. A central finding is that prompt structure exerts significant influence on both data fidelity and privacy risk. Prompts using real data examples yield high TSTR and distributional scores but at the cost of increased privacy risk. In contrast, ClinRule , which encodes only declarative clinical rules, preserves utility while drastically reducing memorization behavior. This supports SynLLM’s design hypothesis that structured, constraint-aware prompting enables high-fidelity generation without reliance on direct example exposure. Prompt Sensitivity and Model Robustness. Performance varies substantially across models, with instruction-tuned models (e.g., OpenChat 7B, Zephyr-7B) adapting well to diverse prompt configurations, while others, including GPT-2 variants, experience degradation under stricter constraints. This prompt sensitivity suggests the need for future work in adaptive prompt strategies that match prompt style to model alignment level, or automated prompt rewriting based on model-specific response patterns. Multidimensional Evaluation and Limitations

> `2508.08529v1_c0035` (SynLLM: A Comparative Analysis of Large Language Models for Medical Tabular Synt; key observations and discussion)
>
> . Multidimensional Evaluation and Limitations. SynLLM employs a comprehensive evaluation suite integrating univariate and multivariate statistical tests (e.g., Wasserstein distance, Frobenius norm), clinical plausibility checks, and empirical privacy audits (e.g., nearest-neighbor distance ratios, identifiability scores). While this framework enables rigorous model comparison, the privacy metrics remain heuristic and empirically grounded. Future work may incorporate formal differential privacy analysis or white-box adversarial testing to strengthen guarantees.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## H10 (limitations)

**Question.** In the medical-guideline causality extraction study, how did BERT-family models compare with GPT-4 and LLAMA2, and what limited LLAMA2’s practical use?

- **H10.1** BioBERT average F1 0.72; LLAMA2 average Jaccard distance 0.40.
  - Anchors (any one group suffices): [['2407.10020v1_c0031']]
- **H10.2** LLAMA2 failed to predict labels for many cases (38%, 21%, 26% of labels omitted at 3, 5, 10 epochs), possibly due to fine-tuning on a small dataset.
  - Anchors (any one group suffices): [['2407.10020v1_c0030']]
- **H10.3** The authors conclude BERT-based models remain state of the art for causality extraction; GPT-4 understands medical text well without fine-tuning but cannot do token classification.
  - Anchors (any one group suffices): [['2407.10020v1_c0030']]

**Source passages (verbatim from the pinned index):**

> `2407.10020v1_c0031` (Causality extraction from medical text using Large Language Models (LLMs); conclusion)
>
> We developed an automated technique for extracting causalities from annotated corpora of medical guidelines. Additionally, we exhibited the practicality of employing new Large Language Models for causality extraction tasks. With BioBERT, we got an average F1-score of 0.72, whereas with LLAMA2, an average Jaccard distance of 0.40 was obtained. We demonstrated the potential for extracting causalities from medical guidelines using a small annotated corpus. The next logical step could involve expanding the corpus through the annotation of more data and creating a benchmark dataset for causality extraction from medical guidelines. The potential of this research opens up novel dimensions for the health domain, as causality extraction from medical guidelines can enhance clinical decision-making and patient care. This work explored both machine learning and natural language processing techniques for causality extraction. Despite the abundance of causal sentences within these guidelines, automatic extraction is an unexplored field of research. Also, machine learning models often fail in clinical applications ( Schmidt, 2017 ) due to the gap between data (both training and testing). In order to avoid this gap, more realistic tests need to be done so that they can be employed for real-world data.

> `2407.10020v1_c0030` (Causality extraction from medical text using Large Language Models (LLMs); discussion)
>
> Above we presented results on causality extraction from medical guidelines using recently introduced large language models such as LLAMA2 and GPT-4, and compared them with the performance of BERT, an older, and smaller LLM. The annotated data and the code are all publicly available on GitHub: https://github.com/gseetha04/LLMs-Medicaldata.git . We observed that GPT-4 expresses strong performance for the cause-effect relationships with medical data, and generally has a good understanding of medical text without fine-tuning. However, in contrast with GPT-3.5 GPT-4 cannot deal with token classification, which limits the traditional way of finding cause and effect phrases, as discussed e.g. in our previous work ( Gopalakrishnan et al., 2023 ) . Even though LLAMA2 seems to perform well for causality extraction, the predictions of the LLAMA2 do not predict labels for many cases, which limits its practical application. This perhaps was caused by fine-tuning LLAMA2 on our small dataset. Therefore, increasing the size of the dataset before the fine-tuning may improve the performance. However, large annotated datasets for CPGs are not available, and further experiments would require annotating more data. Since we focused on the accuracy of actual predictions, we omitted 38% of labels with three epochs, 21% of labels with five epochs, and 26% of labels with ten epochs. Given its relatively high performance and ease of use, BERT-based models continue to be a state-of-the-art for causality extraction tasks, even in the age of LLM .

Reviewer agrees: [ ] yes  [ ] no, note: ______

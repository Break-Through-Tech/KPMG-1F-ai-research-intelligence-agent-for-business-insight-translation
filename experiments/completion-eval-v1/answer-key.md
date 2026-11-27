# Completion evaluation answer key (completion-eval-v1) - for independent human review

Written before any model run on these questions; no retrieval was run to choose them. Required points are
published findings (including implications the authors state). Inferred business implications are not points.
Reviewer: confirm each expected statement is entailed by the quoted passage, then tick.

## C01 (numeric / risk)

**Question.** A client wants to roll out AI coding assistants. How reliably do mainstream LLMs refuse malicious code-generation requests, how do jailbreak techniques change that, and which models resisted best in the MalwareBench study?

- **C01.1** Average rejection rate for malicious content is 60.93%, falling to 39.92% when combined with jailbreak attack algorithms.
  - Anchors (any one group suffices): [['2506.10022v1_c0000']]
- **C01.2** About 50.35% of jailbreak attempts induced responses containing malicious content.
  - Anchors (any one group suffices): [['2506.10022v1_c0015']]
- **C01.3** Most resistant: OpenAI-o1 (refuse rate 77.29%) and, among open models, CodeLlama-70B-Instruct (76.86%).
  - Anchors (any one group suffices): [['2506.10022v1_c0015']]

**Source passages (verbatim from the pinned index):**

> `2506.10022v1_c0000` (LLMs Caught in the Crossfire: Malware Requests and Jailbreak Challenges; abstract)
>
> The widespread adoption of Large Language Models (LLMs) has heightened concerns about their security, particularly their vulnerability to jailbreak attacks that leverage crafted prompts to generate malicious outputs. While prior research has been conducted on general security capabilities of LLMs, their specific susceptibility to jailbreak attacks in code generation remains largely unexplored. To fill this gap, we propose MalwareBench, a benchmark dataset containing 3,520 jailbreaking prompts for malicious code-generation, designed to evaluate LLM robustness against such threats. MalwareBench is based on 320 manually crafted malicious code generation requirements, covering 11 jailbreak methods and 29 code functionality categories. Experiments show that mainstream LLMs exhibit limited ability to reject malicious code-generation requirements, and the combination of multiple jailbreak methods further reduces the model’s security capabilities: specifically, the average rejection rate for malicious content is 60.93%, dropping to 39.92% when combined with jailbreak attack algorithms. Our work highlights that the code security capabilities of LLMs still pose significant challenges.

> `2506.10022v1_c0015` (LLMs Caught in the Crossfire: Malware Requests and Jailbreak Challenges; result)
>
> As shown in Table 3 , a model’s response score(final output of Algorithm 1 ) decreases as its refusal rate increases. During jailbreak attempts, approximately 50.35% of these attempts successfully induce LLMs to produce responses containing malicious content, such as harmful suggestions or malicious code. Among them, OpenAI-o1 achieves the best result, which demonstrated great security with a very high rejection rate and a very low average score (Avg. Score 0.82; Refuse Rate: 77.29%). At the same time, the CodeLlama 70B Instruct in the open-source model also showed strong rejection ability and low exploitability (Avg. Score 0.46; Refuse Rate: 76.86%). Finding 1: A negative correlation exists between LLMs’ response score and refusal rate. In addition, as can be seen from the data in Table 7 , LLMs have relatively low scores when oriented to detailed requirements compared to rough requirements (Avg. Score 1.96 vs. 1.24), with a corresponding increase in rejection rates (Refuse Rate: 47.49% vs. 66.70%). Finding 2: When oriented to detailed problems, LLMs tend to exhibit stronger defenses. Small Parameter Models: When faced with malicious inputs, small parameter models tend to respond; however, due to their limited capacity to accurately interpret instructions, they frequently produce semantically irrelevant outputs, often scoring 1. For instance, CodeGen-350M-Multi has an average score of 0.57 and a refusal rate of 54.57%, while StarCoder2-3B has an average score of 0.78 and a refusal rate of 50.00%. Large Parameter Models and Attack Response Patterns: By analyzing the distribution of scores across models, we found that 3-point content accounted for much more than 2-point content. This trend is more pronounced in larger parameter models, such as Llama-3.3-70B-Instruct

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C02 (governance / cost)

**Question.** For role-based access to sensitive answers, how does sudoLLM behave when it is unsure, does it hurt normal task performance, how well does it hold up against an adversary who knows the mechanism, and what did the experiments cost?

- **C02.1** The BFT strategy fails closed (refuses when in doubt), whereas base and vanilla fine-tuned models fail open.
  - Anchors (any one group suffices): [['2505.14607v3_c0018']]
- **C02.2** No significant task-performance degradation from multi-role (VFT/BFT) fine-tuning versus the base model.
  - Anchors (any one group suffices): [['2505.14607v3_c0018']]
- **C02.3** Signature-user detection succeeds 94.5% of the time (P>0.7) and 93.9% (P>0.8); an adversary with full knowledge cannot circumvent it.
  - Anchors (any one group suffices): [['2505.14607v3_c0022']]
- **C02.4** Total compute cost about 1,700 USD for API-based LLMs and about 100 GPU-hours for local small models.
  - Anchors (any one group suffices): [['2505.14607v3_c0014']]

**Source passages (verbatim from the pinned index):**

> `2505.14607v3_c0018` (sudoLLM: On Multi-role Alignment of Language Models; results)
>
> across models and datasets. The results show that the base model (Inst.) and vanilla fine-tuned models have a strong propensity to answer all queries, whereas our BFT strategy is more keen to refuse. Our BFT strategy demonstrates “ fail-closed behavior ” (when in doubt, refuse) whereas the base and VFT models fail-open (when in doubt, answer); with the former being more desirable from a security standpoint. The poor generalization demonstrated by VFT also hints at the fact that auxiliary model-based strategies, i.e., strategies that rely on an auxiliary model to detect potential safety issues in order to produce refusals, might not perform adequately with limited fine-tuning (6,000 \times 2 samples in our case), and might benefit from increased training coverage. Does multi-role fine-tuning affect performance? No significant impact on performance is observed for VFT or BFT . We also asses whether the user-aware fine-tuned models (VFT, BFT ) show performance degradation when compared to the base model. The results, summarized in Table 3 , show no significant performance disparity between the three versions.

> `2505.14607v3_c0022` (sudoLLM: On Multi-role Alignment of Language Models; results)
>
> In this section, we consider the scenario where an adversary, Bob , acquires full knowledge of the biased query rephrasing strategy (Eq. 1 ) and can thus construct queries that resemble those from Alice . The sudoLLM paradigm enables the detection of such adversarial tampering. As derived in Appendix C , we have: Using this probability, we can detect the intended signature user 94.5% of the time with a threshold of P>0.7 and 93.9% of the time with a threshold of P>0.8 7 7 Calculated over all datasets considered in the study. . Consequently, if an adversary uses a signature not intended for them, they are highly likely to be detected. Even if an adversary avoids detection, their crafted query will be rephrased by the SLM (see Figure 2 ), which adds the correct signature. 8 8 This step is programmatic and cannot be bypassed. As the results in Table 5 demonstrate, an adversary cannot successfully circumvent this security measure even with full knowledge of the bias mechanism. Performance of the sudoLLM framework under adversarial conditions This table reports the alignment accuracy under the assumption that an adversary ( Bob ) has full knowledge of the bias mechanism. “ BFT + Detection” column shows the final alignment accuracy using a combined BFT and detection approach. Results demonstrate that the system effectively neutralizes the adversarial threat. “*” indicates the datasets used for BFT training.

> `2505.14607v3_c0014` (sudoLLM: On Multi-role Alignment of Language Models; sudollm: proposed methodology)
>
> SLM and GPT-4.1-mini ( OpenAI, 2025 ) acting as the target LLM to ablate our approach. GPT-4.1-mini was fine-tuned for 2 epochs, and GPT-4o was fine-tuned for 1 epoch (via the OpenAI fine-tuning API) for both VFT and BFT . Inference with the open-weight models was done on local hardware (1 \times NVIDIA RTX A6000 48GB or 1 \times NVIDIA A100 40GB). The total compute costs for the API-based LLMs is \sim 1700 USD, and for the local SLMs \sim 100 GPU-hours. Further details regarding hyper-parameters, protocol specifications, etc., are provided in Appendix B .

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C03 (qualitative / risk)

**Question.** What did the Ctrl data-curation study find about protecting LLMs from harmful content in training data and from malicious fine-tuning, and what trade-offs or residual risks did it report?

- **C03.1** Curating clean texts (Ctrl) mitigated harmful texts (datasets with 5% harmful texts) across LLMs and often also improved helpfulness.
  - Anchors (any one group suffices): [['2405.19358v2_c0020']]
- **C03.2** Helpfulness can drop in some cases (e.g. Llama-3-8B with instruction-following attack data); smaller models such as ChatGLM-6B are more susceptible.
  - Anchors (any one group suffices): [['2405.19358v2_c0020']]
- **C03.3** Downstream attacks used only 50 or 10 fine-tuning samples; Ctrl reduced attack effectiveness in most cases but less for fragile models, and defenders should invest in alignment at pre-training.
  - Anchors (any one group suffices): [['2405.19358v2_c0021']]

**Source passages (verbatim from the pinned index):**

> `2405.19358v2_c0020` (Robustifying Safety-Aligned Large Language Models through Clean Data Curation; experiment)
>
> . Each dataset includes 5% harmful texts sourced from either \mathcal{D}_{\textrm{EH}} or \mathcal{D}_{\textrm{IS}} . We compare scenarios with and without (i.e., attack-only) the implementation of Ctrl and evaluate the performance of pre-trained LLMs using AdvBench. We have the following observations: (1) Ctrl is capable of mitigating harmful texts across all LLMs with different text volumes, demonstrating its generality and effectiveness in fortifying safety alignment. (2) In most cases, Ctrl not only mitigates the jailbreaking effect but also enhances the helpfulness of LLMs by providing more useful knowledge. This is due to Ctrl ’s intrinsic focus on ensuring text quality. The curated high-quality texts can further improve the knowledgeability of LLMs. (3) There is a potential drop in LLM helpfulness when using Ctrl , such as with Llama-3-8B on \mathcal{D}_{\mathrm{10k}}\cup\mathcal{D}_{\mathrm{IS}} . This drop is attributed to the nature of \mathcal{D}_{\mathrm{IS}} , which reinforces LLMs to strictly obey instructions, thereby enriching the outputs. Smaller-sized LLMs, such as ChatGLM-6B, are more susceptible to the influence of \mathcal{D}_{\mathrm{IS}} , often behaving as overly obedient agents. Consequently, applying Ctrl to mitigate the influence of \mathcal{D}_{\mathrm{IS}} may result in a slight decrease in helpfulness, as Ctrl aims to reduce this over-reliance on obedience. Ctrl against Attack II To address Q 3 , we first apply Ctrl to curate 25% samples of \mathcal{D}_{\mathrm{2k}} during the pre-training phase, then release the model for downstream fine-tuning, where the adversary uses attack samples ( \mathcal{D}_{\mathrm{EH}} or \mathcal{D}_{\mathrm{IS}} ) to attempt jailbreaking LLMs

> `2405.19358v2_c0021` (Robustifying Safety-Aligned Large Language Models through Clean Data Curation; experiment)
>
> . Following the settings in [ 39 ] , we fine-tune LLMs using 50 samples from \mathcal{D}_{\mathrm{EH}} or 10 samples from \mathcal{D}_{\mathrm{IS}} . Table 3 presents the results with and without Ctrl . In most cases, Ctrl significantly reduces the effectiveness of attacks, as measured by \mathcal{S}_{\mathrm{harm}} and ASR, while enhancing the helpfulness of LLMs. This improvement is less notable in more fragile LLMs (e.g., ChatGLM-6B) with smaller capabilities and parameter sets. These experiments underscore the challenge of preventing downstream jailbreaking, as adversaries gain full capability to modify LLMs. It suggests that defenders should invest additional effort in implanting alignment at the pre-training stage to make downstream attacks more difficult to achieve.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C04 (numeric / limitations)

**Question.** How much did adding knowledge graphs improve LLM numerical reasoning on financial documents, and what limits how far a finance team could rely on that result?

- **C04.1** KGs gave +6.41 percentage points execution accuracy (51.93% to 58.34%), about 12.3% relative, with a Llama model.
  - Anchors (any one group suffices): [['2601.07754v1_c0012']]
- **C04.2** Limitations: only FinQA; only open-source LLMs (no comparison with proprietary-model work); KG schema variance may bottleneck localized financial datasets.
  - Anchors (any one group suffices): [['2601.07754v1_c0015']]

**Source passages (verbatim from the pinned index):**

> `2601.07754v1_c0012` (Structure First, Reason Next: Enhancing a Large Language Model using Knowledge G; result and analysis)
>
> Table 1 presents the main results for our framework using KG with Llama model. Using KGs yields a +6.41 percentage-point absolute improvement (51.93% to 58.34%), which corresponds to approximately a 12.3% relative improvement in execution accuracy. This result confirms the capability of leveraging structured information for the financial reasoning. Execution Accuracy by Llama and Llama + KG: For judging the predictions Gemini 2.5 Pro has been used in both of the settings.

> `2601.07754v1_c0015` (Structure First, Reason Next: Enhancing a Large Language Model using Knowledge G; limitations)
>
> This work has some limitations at present, which are discussed below: Dataset: We considered only a single standard benchmark dataset in financial reasoning, namely FinQA. However, there are some more available benchmarks and we intend to explore our proposed framework over these datasets in future. LLM: Due to resource constraints and proprietary solutions, we could not use multiple recently proposed LLMs. We further intend to consider more open-source LLMs and verify the effectiveness of structural characteristics in financial reasoning task. KG Schema: Although the proposed KG schema can be easily updated, we find that multiple datasets have variance in terms of many entity types and relationship types. This may be a bottleneck when the proposed schema is used for some of the localized financial datasets. Baseline: We noticed that many of the previous studies on numerical reasoning with financial dataset consider proprietary LLMs. As our research is limited to using the open-source LLMs, a majority of the past works could not be compared. Further, we were not able to easily adapt the available works to have a comparison, as their implementations were not open due to the usage of proprietary LLMs such as GPT-4o for estimating execution accuracy.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C05 (cost-performance)

**Question.** What cost-performance trade-off did the Aviary study report for a small trained open-source agent versus a frontier model and human experts on scientific tasks, and what caveats apply?

- **C05.1** The trained Llama-3.1-8B agent matched Claude 3.5 Sonnet majority-voting accuracy on SeqQA at about 100x less cost; not achieved on LitQA2, where its voting still beat a single Sonnet rollout at 3x less cost.
  - Anchors (any one group suffices): [['2412.21154v1_c0028']]
- **C05.2** Cost per SeqQA trajectory: $0.07 with Claude 3.5 Sonnet vs $0.00066 with Llama-3.1-8B; human PhD contractors cost $4-$12 per question.
  - Anchors (any one group suffices): [['2412.21154v1_c0030']]
- **C05.3** Caveats: comparisons with humans and prior results are not exactly matched; benchmark contamination risk (LitQA2 re-hosted without canary).
  - Anchors (any one group suffices): [['2412.21154v1_c0030']]

**Source passages (verbatim from the pinned index):**

> `2412.21154v1_c0028` (Aviary: training language agents on challenging scientific tasks; results)
>
> The results of the previous sections demonstrate how the performance of different agents scales as training time and sampled trajectories are increased. In this section, we offer a more practical metric: inference cost. This becomes especially relevant in a high-throughput setting, in which agents are tasked to solve thousands of problems in parallel. We focus our comparison on the Claude 3.5 Sonnet agent versus the Llama-3.1-8B EI agent. We use the following rates for LLM inference at time of writing: Claude 3.5 Sonnet: $3/1M input tokens and $15/1M output tokens 4 4 https://www.anthropic.com/pricing#anthropic-api . Llama-3.1-8B : $0.03/1M input and output tokens, a price typical in the LLM inference market 5 5 https://lambdalabs.com/inference#pricing . While this price refers to inference of the vanilla model, we use it as a reasonable estimate for serving a EI-trained model with a similar set of optimizations. In Figure 7 , we report performance and inference cost on SeqQA and LitQA2. While majority voting with the Claude 3.5 Sonnet agent clearly outperforms other settings, this requires \mathcal{O}(\$1) per task. We reach the same SeqQA accuracy using the Llama-3.1-8B EI agent for 100x less cost. While this was not achievable for LitQA2, we note that majority voting with Llama-3.1-8B EI still exceeds single-rollout with Sonnet for 3x less cost. Accuracy vs. inference cost of two agents (Claude 3.5 Sonnet and Llama-3.1-8B EI) on two sets of tasks (SeqQA and LitQA2). For both agents, both the single-rollout and majority-voting settings are considered. Note that all inference settings here outperform human performance (reported in [ 37 ] and [ 35 ] ).

> `2412.21154v1_c0030` (Aviary: training language agents on challenging scientific tasks; discussion)
>
> . The protein stability task also benefits from increasing inference compute, though it uses oracle-verification. Using an 8B model reduces the inference costs such that it is feasible to vote amongst \sim 1000 rollouts per task. For reference, our SeqQA tasks require 7-10 LLM calls (Figure 5 ) and cost $0.07 on average per trajectory with claude-3-5-sonnet-241022 and $0.00066 per trajectory at current pricing with Llama-3.1-8B EI (although the tasks could be run for free on many consumer laptops). The human PhD contractors that represent the human data series in Figure 6 cost between $4 and $12 per question (see Laurent et. al [ 35 ] for a description of the combined hourly, performance, and completion bonuses). In summary, trained agents can exceed the accuracy of human and frontier models at 100x cheaper cost. There are some limitations in this work. The comparisons are not exactly matched between humans and other previous reported results on benchmarks. One reason is that the Environments are complex pieces of software, with dozens of dependencies that all have specific versions. Another issue is that the splits we used are only now available (although they were included in the human assessments). We used splits that were impossible to have been scraped in training data. One reason we took this precaution is that websites have re-hosted the LitQA2 benchmark without the canary string [ 140 ] , so that it is plausibly now in LLM pre-training corpuses. Comparing against humans is also fraught, because they do not have access to the same tools. Although, in Laurent et. al [ 35 ] there were incentives for correct answers, ample time, and only restrictions against using AI tools

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C06 (numeric / robustness)

**Question.** When source data are sparse or contradictory, how robust was MultiRAG compared with the ChatKBQA baseline?

- **C06.1** On sparser Books and Stocks data, MultiRAG improved more than 10% on average over state-of-the-art methods.
  - Anchors (any one group suffices): [['2508.03553v1_c0026']]
- **C06.2** With relationship masking on Stocks, MultiRAG F1 fell 78.6% to 71.0%, while ChatKBQA fell 68.0% to 62.0% (Books 59.1% to 53.0%).
  - Anchors (any one group suffices): [['2508.03553v1_c0027']]
- **C06.3** With inconsistent added triples, MultiRAG F1 fell only from 74.9% to 73.4/72.9/71.4%, while ChatKBQA fell from 74.2% to 69.7/64.3/55.8%.
  - Anchors (any one group suffices): [['2508.03553v1_c0028']]

**Source passages (verbatim from the pinned index):**

> `2508.03553v1_c0026` (MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-sou; experiments)
>
> . In contrast, on the more sparse Books and Stocks datasets, our method achieves an average improvement of more than 10% over SOTA methods. Q2: What are the respective impacts of data sparsity and data inconsistency on the quality of retrieval recall? MultiRAG demonstrates good robustness in scenarios of varying data sparsity and inconsistency. To validate it, we conducted experiments from the following two perspectives . 1) Sparsity of multi-source data: We applied 30%, 50%, and 70% random relationship masking to four pre-processed datasets, making the connections between data sparser while ensuring that the query answers are still retrievable. 2) Consistency of multi-source data: We added 30%, 50%, and 70% of triple increments (the new triples are copies of the original triples) to the four pre-processed datasets, and completely shuffled the relationship edges of the added triples to disrupt the consistency of multi-source data. Subsequently, we employed MultiRAG to experiment with datasets under both perturbation schemes. Performance comparison on HotpotQA and 2WikiMultiHopQA datasets F1 Score in Movies Efficiency-Accuracy Tradeoff of Movies Dataset Firstly, to address data sparsity, we conducted experiments on MultiRAG (Ours) and ChatKBQA (SOTA). The experimental results demonstrate that MultiRAG exhibits significant robustness when faced with the challenge of data sparsity. Specifically, after applying 30%, 50%, and 70% relationship masking, the F1 score of MultiRAG on the Books dataset only dropped from 66.8% to 60.0%. On the Stocks dataset, its F1 score decreased from 78.6% to 71.0%, which have been shown in Fig. 5(b) and Fig. 5(d)

> `2508.03553v1_c0027` (MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-sou; experiments)
>
> . On the Stocks dataset, its F1 score decreased from 78.6% to 71.0%, which have been shown in Fig. 5(b) and Fig. 5(d) . These moderate decreases indicate that MultiRAG can effectively maintain its performance even when a substantial number of relationships are masked. In contrast, ChatKBQA’s performance decline under the same conditions is more significant. On the Books dataset, ChatKBQA’s F1 score dropped from 59.1% to 53.0%, and on the Stocks dataset, its F1 score decreased from 68.0% to 62.0%. This outcome reveals the challenges ChatKBQA faces when dealing with sparse data, especially when a large number of data connections are masked, significantly impacting its performance. Next, we conducted robustness experiments on multi-source data consistency. We perturbed the Books and Stocks datasets to varying degrees to test the performance changes of MultiRAG and ChatKBQA when data consistency is disrupted. The experimental results show that MultiRAG demonstrates excellent robustness in the face of data consistency disruption, while ChatKBQA’s performance declines rapidly under perturbation. Specifically, as is shown in Fig. 5(a) , on the Movies dataset, we added 30%, 50%, and 70% triple increments to the original dataset and randomized the relationship edges of the added triples. The results show that MultiRAG’s F1 score slightly decreased from 54.8% to 52.1%, 51.5%, and 49.9%, while ChatKBQA’s F1 score significantly dropped from 53.6% to 51.6%, 47.2%, and 40.8%. On the Flights dataset shown in Fig. 5(c) , we performed the same perturbation operations, and MultiRAG’s F1 score slightly decreased from 74.9% to 73.4%, 72.9%, and 71.4%, while ChatKBQA’s F1 score substantially dropped from 74.2% to 69.7%, 64.3%, and 55.8%

> `2508.03553v1_c0028` (MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-sou; experiments)
>
> . 5(c) , we performed the same perturbation operations, and MultiRAG’s F1 score slightly decreased from 74.9% to 73.4%, 72.9%, and 71.4%, while ChatKBQA’s F1 score substantially dropped from 74.2% to 69.7%, 64.3%, and 55.8%. These results indicate that even when data consistency is severely compromised, MultiRAG can still maintain a high level of performance stability, whereas ChatKBQA’s performance is more sensitive to disruptions in data consistency. Case Study

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C07 (cross-paper)

**Question.** KG²RAG and MultiRAG both use knowledge graphs to make retrieval-augmented answers more reliable. What problem does each target, how does each work, and what gains did each report?

- **C07.1** KG²RAG: after semantic retrieval of seed chunks, KG-guided chunk expansion and KG-based organization supply fact-level relationships for more diverse, coherent context.
  - Anchors (any one group suffices): [['2502.06864v1_c0000']]
- **C07.2** KG²RAG gains: at least 8% over baselines in the fullwiki setting; at least 2.5% and 6.4% on Shuffle-HotpotQA (distractor, fullwiki).
  - Anchors (any one group suffices): [['2502.06864v1_c0019']]
- **C07.3** MultiRAG: multi-source line graphs aggregate sources, and multi-level (graph and node) confidence filters low-quality or inconsistent knowledge, targeting sparse and conflicting multi-source data; >10% gain on sparse datasets.
  - Anchors (any one group suffices): [['2508.03553v1_c0004', '2508.03553v1_c0026']]

**Source passages (verbatim from the pinned index):**

> `2502.06864v1_c0000` (Knowledge Graph-Guided Retrieval Augmented Generation; abstract)
>
> Retrieval-augmented generation (RAG) has emerged as a promising technology for addressing hallucination issues in the responses generated by large language models (LLMs). Existing studies on RAG primarily focus on applying semantic-based approaches to retrieve isolated relevant chunks, which ignore their intrinsic relationships. In this paper, we propose a novel Knowledge Graph-Guided Retrieval Augmented Generation (KG 2 RAG) framework that utilizes knowledge graphs (KGs) to provide fact-level relationships between chunks, improving the diversity and coherence of the retrieved results. Specifically, after performing a semantic-based retrieval to provide seed chunks, KG 2 RAG employs a KG-guided chunk expansion process and a KG-based chunk organization process to deliver relevant and important knowledge in well-organized paragraphs. Extensive experiments conducted on the HotpotQA dataset and its variants demonstrate the advantages of KG 2 RAG compared to existing RAG-based approaches, in terms of both response quality and retrieval quality.

> `2502.06864v1_c0019` (Knowledge Graph-Guided Retrieval Augmented Generation; experiments)
>
> The comparisons in terms of response quality between KG 2 RAG and the baselines are shown in Table 1 . From the table, we can observe that all methods utilizing RAG achieve significant improvements compared to the LLM-only approach, exceeding 29.1% improvements in F1 scores on the original HotpotQA and 26.4% improvements in F1 scores on Shuffle-HotpotQA. Among these RAG-based methods, KG 2 RAG achieves consistent outperformance, especially in the fullwiki setting and on the Shuffle-HotpotQA dataset. In the fullwiki setting, a large pool of candidate documents (thousands of times more than in the distractor setting) is provided to LLMs, necessitating high-quality retrieval results and effective context organization. In such a challenging setup, our proposed method KG 2 RAG achieves at least 8% improvements compared to baselines, demonstrating that KG 2 RAG enhances chunk retrieval through KG-guided approaches that surpass semantic-based and keyword-based methods. Besides, on the Shuffle-HotpotQA dataset, where LLMs should rely more on RAG rather than prior knowledge, our proposed method achieves at least 2.5% and 6.4% improvements in the distractor and fullwiki settings, respectively. The experimental results are shown in Table 2 , which demonstrate that KG 2 RAG strikes a favorable balance between retrieval precision and recall, highlighting the effectiveness of KG-guided expansion and context organization. In the distractor setting, where irrelevant chunks are limited, our proposed method achieves similar performance in recall but significantly better performance in precision (more than 7.9% and 6.9% on HotpotQA and Shuffle-HotpotQA, respectively).

> `2508.03553v1_c0004` (MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-sou; introduction)
>
> . Initially, we introduce multi-source line graphs for rapid aggregation of knowledge sources to tackle issues arising from sparse data distribution. Subsequently, based on these integrated multi-source line graphs, we propose a multi-level confidence calculation method to ensure the reliability of multi-source data queries. This approach not only enhances query efficiency but also strengthens the accuracy of results, providing an effective solution for the multi-source knowledge-guided RAG . The contributions of this paper are summarized as follows: Multi-source Knowledge Aggregation : In the knowledge construction module, we introduce multi-source line graphs as a data structure for rapid aggregation and reconstruction of knowledge structures from multiple query-relevant data sources. This effectively captures inter-source data dependencies within chunk texts, thereby providing a unified and centralized representation of multi-source knowledge. Multi-level Confidence Calculation: In the retrieval module, we perform graph-level and node-level confidence calculations on the extracted knowledge subgraphs. The aim is to filter out and eliminate low-quality subgraphs and inconsist retrieval nodes, ultimately enhancing the quality of text embedded in context to alleviate retrieval hallucinations. Experimental Validation and Performance Comparison : We conducted extensive experiments on existing multi-source retrieval datasets and two complex Q&A datasets, comparing our approach with existing state-of-the-art(SOTA) methods. This demonstrated the robustness and accuracy of our proposed method in retrieval performance. Particularly in multi-source data retrieval tasks, our method significantly outperforms other SOTA methods by more than 10%.

> `2508.03553v1_c0026` (MultiRAG: A Knowledge-guided Framework for Mitigating Hallucination in Multi-sou; experiments)
>
> . In contrast, on the more sparse Books and Stocks datasets, our method achieves an average improvement of more than 10% over SOTA methods. Q2: What are the respective impacts of data sparsity and data inconsistency on the quality of retrieval recall? MultiRAG demonstrates good robustness in scenarios of varying data sparsity and inconsistency. To validate it, we conducted experiments from the following two perspectives . 1) Sparsity of multi-source data: We applied 30%, 50%, and 70% random relationship masking to four pre-processed datasets, making the connections between data sparser while ensuring that the query answers are still retrievable. 2) Consistency of multi-source data: We added 30%, 50%, and 70% of triple increments (the new triples are copies of the original triples) to the four pre-processed datasets, and completely shuffled the relationship edges of the added triples to disrupt the consistency of multi-source data. Subsequently, we employed MultiRAG to experiment with datasets under both perturbation schemes. Performance comparison on HotpotQA and 2WikiMultiHopQA datasets F1 Score in Movies Efficiency-Accuracy Tradeoff of Movies Dataset Firstly, to address data sparsity, we conducted experiments on MultiRAG (Ours) and ChatKBQA (SOTA). The experimental results demonstrate that MultiRAG exhibits significant robustness when faced with the challenge of data sparsity. Specifically, after applying 30%, 50%, and 70% relationship masking, the F1 score of MultiRAG on the Books dataset only dropped from 66.8% to 60.0%. On the Stocks dataset, its F1 score decreased from 78.6% to 71.0%, which have been shown in Fig. 5(b) and Fig. 5(d)

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C08 (qualitative / limitations)

**Question.** What did the Financial Bias Indicators (FBI) study find about irrational financial biases in LLMs, how did model size and bias-mitigation prompts affect them, and how far do the findings generalize?

- **C08.1** Within a model family, bias tends to decrease as model size grows, but not consistently across families (design and training also matter).
  - Anchors (any one group suffices): [['2402.12713v2_c0024']]
- **C08.2** Mitigation: CoT helped originally more-biased models but hurt well-performing ones; Entity Replace performed best; FinCausal used recalled causal knowledge.
  - Anchors (any one group suffices): [['2402.12713v2_c0022']]
- **C08.3** Limitation: focused on the Chinese A-share market, so findings may not generalize to other cultures or regions.
  - Anchors (any one group suffices): [['2402.12713v2_c0028']]

**Source passages (verbatim from the pinned index):**

> `2402.12713v2_c0024` (Are LLMs Rational Investors? A Study on Detecting and Reducing the Financial Bia; discussion)
>
> The analysis in Section 5.1.3 reveals that within a specific model family, the degree of bias tends to decrease with the enlargement of model parameters, in line with the scaling law Kaplan et al. (2020) . However, this trend is not consistent across different model family, where bias levels are also shaped by factors such as model design and training approaches.

> `2402.12713v2_c0022` (Are LLMs Rational Investors? A Study on Detecting and Reducing the Financial Bia; bias antidote)
>
> For Belief Bias, we employed four prompt-based elimination methods and selected five representative LLMs for bias elimination experiments, as shown in Table 1 . For the CoT method, it performed well on the originally more biased models, as this reasoning approach enhances logical consistency in responses, thereby improving robustness and reducing bias. However, it performed poorly on models that were originally well-performing, as the increased output length due to the auto-regressive nature of these models resulted in amplified bias. For the S2A method, the effectiveness of increasing model output to reduce irrelevant attention depends on the model’s original capability; weaker models tend to exhibit greater bias. The Entity Replace method showed superior performance due to the substitution of financial topics. For the FinCausal method, each test data recalled four related causal knowledge entries, further enhancing the model’s reasoning ability to mitigate bias.

> `2402.12713v2_c0028` (Are LLMs Rational Investors? A Study on Detecting and Reducing the Financial Bia; limitation)
>
> Our financial rational analysis focuses on biases towards the awareness of the Chinese A-share market, which may vary depending on culture and region, resulting in research findings that may not be generalizable to other situations. Meanwhile, we introduced other models during model evaluation, which may lead to the introduction of other biases.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C09 (numeric / applications)

**Question.** What is the LLM Pro Finance Suite, how did it perform on financial tasks across languages, and what gap remained?

- **C09.1** Five instruction-tuned models (8B-70B) fine-tuned on a corpus with over 50% finance data in English, French and German; consistent improvement over baselines on finance tasks and financial translation.
  - Anchors (any one group suffices): [['2511.08621v1_c0000']]
- **C09.2** Improvement is largest in French; English-level performance is not yet reached on all languages; English financial-acronym accuracy stagnates around 0.50.
  - Anchors (any one group suffices): [['2511.08621v1_c0016']]

**Source passages (verbatim from the pinned index):**

> `2511.08621v1_c0000` (The LLM Pro Finance Suite: Multilingual Large Language Models for Financial Appl; abstract)
>
> The financial industry’s growing demand for advanced natural language processing (NLP) capabilities has highlighted the limitations of generalist large language models (LLMs) in handling domain-specific financial tasks. To address this gap, we introduce the LLM Pro Finance Suite, a collection of five instruction-tuned LLMs (ranging from 8B to 70B parameters) specifically designed for financial applications. Our approach focuses on enhancing generalist instruction-tuned models, leveraging their existing strengths in instruction following, reasoning, and toxicity control, while fine-tuning them on a curated, high-quality financial corpus comprising over 50\text{\,}\mathrm{\%} finance-related data in English, French, and German. We evaluate the LLM Pro Finance Suite on a comprehensive financial benchmark suite, demonstrating consistent improvement over state-of-the-art baselines in finance-oriented tasks and financial translation. Notably, our models maintain the strong general-domain capabilities of their base models, ensuring reliable performance across non-specialized tasks. This dual proficiency, enhanced financial expertise without compromise on general abilities, makes the LLM Pro Finance Suite an ideal drop-in replacement for existing LLMs in financial workflows, offering improved domain-specific performance while preserving overall versatility. We publicly release two 8B-parameters models to foster future research and development in financial NLP applications: https://huggingface.co/collections/DragonLLM/llm-open-finance .

> `2511.08621v1_c0016` (The LLM Pro Finance Suite: Multilingual Large Language Models for Financial Appl; evaluation)
>
> It clearly shows that all the LLM Pro Finance models improve over the baseline by a large margin, especially in French. This is clearly because of the vast amount of English data used to train the base model, and prove that work still need to be carried out to reach English-level performances on all languages. The accuracy on the English acronyms seem to stagnate around 0.50 for all finetuned models, with smaller models outperforming larger base models. English financial tasks. Best and second scores are, respectively, bold and underlined. The last row “Ranked first” show the number of time the model is ranked first. French financial tasks. Best and second scores are, respectively, bold and underlined. The last row “Ranked first” show the number of time the model is ranked first. We conducted more extensive evaluations on standardized financial benchmarks (mostly FinBen). Detailed results are shown in Tables 5 and 6 . While these benchmarks provide a broad overview of the financial knowledge of the model, it is difficult to aggregate the results into a single score, as they are not relying on the same metric. Some use accuracy, other F1 or RMSE, thus averaging these scores would have no sense. That is why we found handy to look at the models’ ranking on each benchmark instead of the raw scores.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C10 (qualitative / adoption)

**Question.** According to the overview of LLMs in finance, where are LLMs strongest, where are they limited, and what role do the authors see for them in computational finance?

- **C10.1** Strong zero-shot learning and mathematical reasoning; sentiment analysis is their strongest suit.
  - Anchors (any one group suffices): [['2401.11641v5_c0043']]
- **C10.2** Limited in optimization and quantitative trading; cannot directly do computational tasks; an auxiliary role feeding existing quantitative models, not a standalone solution.
  - Anchors (any one group suffices): [['2401.11641v5_c0044']]

**Source passages (verbatim from the pinned index):**

> `2401.11641v5_c0043` (Revolutionizing Finance with LLMs: An Overview of Applications and Insights; experimental results)
>
> In our tested financial tasks, LLMs demonstrated precise execution capabilities. Based on the responses we gathered, we believe that LLMs exhibit exceptional zero-shot learning and mathematical reasoning abilities, along with their strongest suit, language sentiment analysis. The effectiveness of LLMs in financial tasks is quantitatively assessed by comparing their recommendations against real-world financial data and historical market performance. This methodology was rigorously tested across various financial scenarios and datasets, yielding insightful and actionable results in areas such as financial engineering, risk assessment, and market trend analysis. For financial tasks lacking dedicated datasets, we have curated case studies to showcase the capabilities of GPT-4. The zero-shot and few-shot performance of different LLMs on the stated datasets.

> `2401.11641v5_c0044` (Revolutionizing Finance with LLMs: An Overview of Applications and Insights; limitation and future work)
>
> The limitations of LLMs are evident in areas such as optimization and quantitative trading. While they can assist in identifying market sentiments, LLMs cannot directly engage in computational tasks. Their role is more auxiliary, aiding in sentiment analysis which then feeds into existing models that handle quantitative variables [ 123 ] . This indicates that LLMs, as of now, are not standalone solutions for computational finance tasks but rather powerful tools for augmenting existing models. For future work, there is immense potential in integrating LLMs with advanced quantitative models. One promising direction could be the development of hybrid systems that combine the text processing prowess of LLMs with sophisticated quantitative trading algorithms [ 135 , 22 ] . Another area could be enhancing the interpretability and reliability of LLMs outputs in financial contexts, ensuring that the insights generated are not only accurate but also actionable. Moreover, exploring the application of LLMs in predictive analytics for market trends, based on historical data and current events, can open new avenues in financial forecasting. This integration of qualitative and quantitative analysis could revolutionize how financial markets are analyzed and traded [ 39 ] .

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C11 (numeric / governance)

**Question.** For vendor due diligence, what did the Foundation Model Transparency Index find about how transparent major foundation-model developers are, and where is transparency weakest?

- **C11.1** FMTI uses 100 indicators; leading developers were not transparent in 2023, with material improvement in 2024.
  - Anchors (any one group suffices): [['2506.23123v1_c0014']]
- **C11.2** In 2024, 11 of 14 developers scored below 65.
  - Anchors (any one group suffices): [['2506.23123v1_c0274']]
- **C11.3** Weakest: the impact subdomain; no developer scores on affected market sectors, affected individuals, usage reports or geographic statistics.
  - Anchors (any one group suffices): [['2506.23123v1_c0286']]

**Source passages (verbatim from the pinned index):**

> `2506.23123v1_c0014` (The Societal Impact of Foundation Models: Advancing Evidence-based AI Policy; introduction)
>
> FMTI concretizes the nebulous construct of transparency into 100 concrete indicators across the supply chain (e.g. the upstream data and compute used to build a foundation model, the downstream release and usage of a foundation model). Through a multi-stage process of gathering information, scoring companies, having those companies rebut our scores, and publishing the final scores, I show the leading foundation model developers are not transparent in both systemic and idiosyncratic ways in 2023. However, through direct engagement with the relevant employees within these companies, as well as a variety of external stakeholders (e.g. the media, policymakers, company investors, company clients), we see material improvement, especially through the disclosure of never-before public information, in the 2024 FMTI. FMTI has wide-ranging impact: coverage by media outlets like the New York Times, engagement by AI companies like Google, and uptake by policymakers. Of specific note is policy impact in the United States (e.g. the US Foundation Model Transparency Act was proposed in Congress in 2023), the European Union (e.g. the EU AI Act has significant resonance with the FMTI indicators in 2024) and at the international level (e.g. the G7 International Code of Conduct indicates that foundation model developers should publish transparency reports ( Bommasani et al., 2024c ) ). Having accumulated a wealth of evidence, we transition from the study of the societal impact of foundation models to the policy that governs AI. In Chapter 6 , I provide the final research contributions of the dissertation to buttress the burgeoning research-policy interface.

> `2506.23123v1_c0274` (The Societal Impact of Foundation Models: Advancing Evidence-based AI Policy; empirical understanding: part ii)
>
> Through this correspondence, companies clarified existing information and disclosed new information, which is reflected in the final form of the transparency reports we publish. Ultimately, companies validated their transparency reports and approved their release. In doing so, unlike the 2023 FMTI, these reports make explicit instances where (i) developers disclose useful information yet (ii) we felt the disclosure was insufficient to award a point. We focus on major changes relative to 2023 here, deferring many of the 2024 results to Bommasani et al. (2024b) . Scores by domain. The overall 2024 FMTI scores disaggregated into the three domains: upstream, model, and downstream. Based on the overall scores (right of Figure 1), 11 of the 14 developers score below 65, showing that there is a significant lack of transparency in the foundation model ecosystem and substantial room for improvement across developers. The mean and median are 57.93 and 57 respectively, with a standard deviation of 13.98. The highest-scoring developer scores points for 85 of the 100 indicators, while the lowest-scoring developer scores 33. The 3 top-scoring developers (BigCode/Hugging Face/ServiceNow, Aleph Alpha, and AI21 Labs) are more than one standard deviation above the mean, the next 9 are near the mean (IBM, Microsoft, Meta, Stability AI, Writer, Anthropic, OpenAI, Mistral, Google), and the 2 lowest-scoring developers are more than one standard deviation below the mean (Amazon, Adept). In spite of significant opacity, for 96 of the 100 indicators there exists some developer that scores points, and of these there are 89 where multiple developers score points.

> `2506.23123v1_c0286` (The Societal Impact of Foundation Models: Advancing Evidence-based AI Policy; empirical understanding: part ii)
>
> In particular, these companies may face liability if the data contains copyrighted, private, or illegal content such as child sexual abuse material ( Lee et al., 2024 ; Solove, 2024 ; Thorn, 2024 ) . Developers still lack transparency about the real-world impact of their models, and any steps they take to mitigate negative impacts pre-deployment. Of the major dimensions of transparency in Figure 5.17 , developers score worst on the impact subdomain (as they did in 2023). Each of the four indicators where no developer scores points (affected market sectors, affected individuals, usage reports, and geographic statistics) are in the impact subdomain. This means that the public has little to no information about who uses foundation models, where foundation models are used, and for what purpose. The lack of transparency regarding these matters inhibits effective governance of foundation models, as it is difficult for governments or civil society organizations to pressure companies to responsibly deploy their models if there is no information about the impact of deployment. In many cases this opacity stems from a lack of information sharing between developers, deployers, and customers; developers generally do not know how their foundation model is being used unless a deployer monitors use or receives and shares information about use from its customer. For 3 of these developers we evaluate the same flagship foundation model (Jurassic-2 for AI21 Labs, Llama 2 for Meta, and GPT-4 for OpenAI) as 2023 FMTI while for the other 5 we evaluate a different flagship foundation model (Titan Text Express for Amazon, Claude 3 for Anthropic, StarCoder for BigCode/Hugging Face/ServiceNow, Gemini 1.0 Ultra API for Google, and Stable Video Diffusion for Stability AI).

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C12 (limitations / risk)

**Question.** What challenges does the survey of reasoning LLMs in medicine identify for safely deploying them in clinical settings?

- **C12.1** Chain-of-thought steps are not guaranteed to be medically sound; reasoning must be grounded in authoritative knowledge and evidence-based guidelines.
  - Anchors (any one group suffices): [['2508.19097v1_c0033']]
- **C12.2** High-stakes errors and training-data bias (health disparities) require context-aware safety mechanisms and incorporation of guidelines, ethics and regulation.
  - Anchors (any one group suffices): [['2508.19097v1_c0034']]

**Source passages (verbatim from the pinned index):**

> `2508.19097v1_c0033` (Reasoning LLMs in the Medical Domain: A Literature Survey; current challenges and future directions)
>
> While CoT methods enhance transparency by externalizing reasoning steps [ 12 ] , these steps are not inherently guaranteed to be medically sound or aligned with established clinical knowledge. Explainable models like Gyan, with their compositional architectures, may offer pathways to deeper interpretability [ 41 ] . Similarly, frameworks like Layered-CoT aim to improve trustworthiness through mechanisms for external verification of each reasoning step [ 15 ] . A critical ongoing challenge is ensuring that LLM reasoning is robustly grounded in authoritative medical knowledge and evidence-based guidelines. Future research must continue to explore advanced knowledge integration methods, causal reasoning capabilities, and techniques that allow clinicians to understand and trust the model’s outputs.

> `2508.19097v1_c0034` (Reasoning LLMs in the Medical Domain: A Literature Survey; current challenges and future directions)
>
> Medical reasoning systems operate in a high-stakes environment where errors can have severe consequences. These systems must navigate complex ethical considerations, including mitigating biases present in training data (which can lead to health disparities) and minimizing the risk of generating harmful or misleading recommendations [ 46 ] . Current evaluation frameworks are increasingly incorporating assessments for potential harm and bias [ 11 , 14 , 47 ] . However, more robust, context-aware safety mechanisms specifically designed for medical reasoning are needed. Future work should focus on developing LLMs that can dynamically incorporate clinical practice guidelines, evolving ethical principles, and regulatory requirements directly into their reasoning processes to ensure outputs are safe, equitable, and appropriate across diverse clinical scenarios and patient populations.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C13 (qualitative / customer experience)

**Question.** What trade-off do proactive LLM agents face between completing tasks and involving users, and what did BAO achieve?

- **C13.1** Passive agents cannot efficiently adapt to user intentions while overusing human feedback burdens users: a Pareto frontier between task performance and user engagement.
  - Anchors (any one group suffices): [['2602.11351v2_c0000']]
- **C13.2** BAO improved task performance with lower user effort, surpassing proactive RL baselines and comparable or superior to commercial LLM agents on UserRL.
  - Anchors (any one group suffices): [['2602.11351v2_c0000'], ['2602.11351v2_c0004']]

**Source passages (verbatim from the pinned index):**

> `2602.11351v2_c0000` (Pushing Forward Pareto Frontiers of Proactive Agents with Behavioral Agentic Opt; abstract)
>
> Proactive large language model (LLM) agents aim to actively plan, query, and interact over multiple turns, enabling efficient task completion beyond passive instruction following and making them essential for real-world, user-centric applications. Agentic reinforcement learning (RL) has recently emerged as a promising solution for training such agents in multi-turn settings, allowing them to learn long-horizon decision-making strategies. However, existing pipelines face a critical challenge in balancing task performance with user engagement, as passive agents cannot efficiently adapt to users’ intentions while overuse of human feedback increases the burden on users, which forms a Pareto Frontier between these two objectives. To push forward this frontier, we propose Behavior Agentic Optimization (BAO), an agentic RL framework that enhances and regularizes inter-turn behaviors to improve information-gathering capabilities and suppress inefficient or redundant interactions with users. We evaluate BAO on multiple tasks from the UserRL benchmark suite and demonstrate that it substantially outperforms proactive agentic RL baselines in terms of both higher task performance and lower user efforts, while achieving comparable or even superior performance to commercial LLM agents, highlighting its effectiveness for training proactive, user-centric LLM agents in complex multi-turn scenarios. Our website: https://proactive-agentic-rl.github.io/ .

> `2602.11351v2_c0004` (Pushing Forward Pareto Frontiers of Proactive Agents with Behavioral Agentic Opt; introduction)
>
> The empirical results further show that our method efficiently pushes forward the Pareto frontier between user engagement and task performance compared to the agentic RL baseline for proactive agents. Our key contributions are summarized as: This work formulates proactive agent training as an MOO problem and identifies the Pareto frontier between final task performance and user engagement efforts. We characterize multi-turn behaviors, including retrospective reasoning and prospective planning, that connect actions with historical information and future scheduling. We propose BAO, which enhances and regularizes multi-turn behaviors in proactive agent training to collect and utilize contextual feedback more effectively. Extensive experiments demonstrate that BAO significantly improves task performance without overusing user engagement, surpassing strong RL baselines and commercial models on the UserRL benchmark.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C14 (table / business implications)

**Question.** For an accounting firm choosing between a commercial reranker and an in-house reranker in the metadata-driven financial RAG study, what quality and latency trade-off does Table 1 show, and what business implications do the authors themselves draw?

- **C14.1** Full pipeline with the Cohere reranker on contextual chunks: F1 44.4, mean latency 13.18 s.
  - Anchors (any one group suffices): [['2510.24402v1_table_de629a5f57790c34_9']]
- **C14.2** Same pipeline with the in-house reranker: F1 43.2, mean latency 12.43 s.
  - Anchors (any one group suffices): [['2510.24402v1_table_de629a5f57790c34_10']]
- **C14.3** Authors: an in-house, transparent model is competitive, avoids high operational costs and vendor lock-in, and is more auditable and explainable.
  - Anchors (any one group suffices): [['2510.24402v1_c0045']]
- **C14.4** Authors: naive chunk expansion hurt (relevance over quantity; more hallucination, less faithful answers).
  - Anchors (any one group suffices): [['2510.24402v1_c0045']]

**Source passages (verbatim from the pinned index):**

> `2510.24402v1_table_de629a5f57790c34_9` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; Results and Analysis)
>
> Derived source table row (HTML cell serialization, not verbatim prose). Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering Table 1: Comprehensive Performance of All Evaluated RAG Architectures Architecture: Filtering + Rewriting + Hybrid Retrieval + Reranking (Cohere); Chunk Type: Ctx; Prec: 43.8; Recall: 69.1; F1-score: 44.4; Claim Recall: 42.3; Context Precision: 44.4; Faith.: 76.4; Halluc.: 15.1; Mean Latency (s): 13.18

> `2510.24402v1_table_de629a5f57790c34_10` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; Results and Analysis)
>
> Derived source table row (HTML cell serialization, not verbatim prose). Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering Table 1: Comprehensive Performance of All Evaluated RAG Architectures Architecture: Filtering + Rewriting + Hybrid Retrieval + Reranking (Ours); Chunk Type: Ctx; Prec: 44.1; Recall: 64.5; F1-score: 43.2; Claim Recall: 39.9; Context Precision: 18.0; Faith.: 73.7; Halluc.: 17.2; Mean Latency (s): 12.43

> `2510.24402v1_c0045` (Metadata-Driven Retrieval-Augmented Generation for Financial Question Answering; conclusion, discussion, and future work)
>
> . While proprietary, "black-box" AI models may offer marginal performance gains, our proposed architecture demonstrates that an in-house, transparent model can achieve highly competitive results. For accounting firms and corporate finance departments, this has profound implications. It offers a path to developing powerful analytical tools without incurring high operational costs or vendor lock-in. More importantly, a transparent model is inherently more auditable and explainable (XAI). System administrators and auditors can inspect the logic of the custom reranker, a critical feature when the AI’s output is used to support high-stakes financial decisions or audit opinions. Finally, the failure of our naive chunk expansion technique serves as a salient cautionary tale for AIS design and implementation. It empirically demonstrates the accounting principle of relevance over quantity. In a domain where materiality is paramount, simply flooding a model with more data is not only ineffective but detrimental, leading to higher rates of hallucination and less faithful answers. This finding reinforces the need for meticulous system design in accounting contexts. The goal must be to provide the decision-maker (whether human or AI) with concise, relevant, and high-quality information. This underscores that the successful application of AI in accounting depends less on brute-force data processing and more on the intelligent, structured curation of information, a core tenet of the Accounting Information Systems discipline.

Reviewer agrees: [ ] yes  [ ] no, note: ______

## C15 (cross-paper / business implications)

**Question.** A bank is considering a finance-specialized LLM. What do the LLM Pro Finance and Financial Bias Indicators studies each report about domain-specific financial training?

- **C15.1** LLM Pro Finance: fine-tuned models improve over the baseline by a large margin (especially in French), with smaller fine-tuned models outperforming larger base models on English acronyms.
  - Anchors (any one group suffices): [['2511.08621v1_c0016']]
- **C15.2** FBI: financially trained models may show higher score variability and risk inclination, and financial training data (e.g. embellished research reports) may embed irrationality.
  - Anchors (any one group suffices): [['2402.12713v2_c0025']]

**Source passages (verbatim from the pinned index):**

> `2511.08621v1_c0016` (The LLM Pro Finance Suite: Multilingual Large Language Models for Financial Appl; evaluation)
>
> It clearly shows that all the LLM Pro Finance models improve over the baseline by a large margin, especially in French. This is clearly because of the vast amount of English data used to train the base model, and prove that work still need to be carried out to reach English-level performances on all languages. The accuracy on the English acronyms seem to stagnate around 0.50 for all finetuned models, with smaller models outperforming larger base models. English financial tasks. Best and second scores are, respectively, bold and underlined. The last row “Ranked first” show the number of time the model is ranked first. French financial tasks. Best and second scores are, respectively, bold and underlined. The last row “Ranked first” show the number of time the model is ranked first. We conducted more extensive evaluations on standardized financial benchmarks (mostly FinBen). Detailed results are shown in Tables 5 and 6 . While these benchmarks provide a broad overview of the financial knowledge of the model, it is difficult to aggregate the results into a single score, as they are not relying on the same metric. Some use accuracy, other F1 or RMSE, thus averaging these scores would have no sense. That is why we found handy to look at the models’ ranking on each benchmark instead of the raw scores.

> `2402.12713v2_c0025` (Are LLMs Rational Investors? A Study on Detecting and Reducing the Financial Bia; discussion)
>
> The FBI framework assessed financial rationality in general and financial LLMs. Financially-trained models, as seen in Figure 4 , may exhibit higher score variability and risk inclination, potentially increasing financial irrationality. Models like ChatGLM2-6B and Qwen-7B show opposite industry biases ( Figure 37 - Figure 54 ), suggesting temporal biases in training data align with industry cycle rotation. Financial data, including potentially embellished research reports, can enhance LLMs for finance-specific NLP tasks but may also embed financial irrationality. Using these models in financial quantification could lead to unintended disruptions, demanding immediate attention.

Reviewer agrees: [ ] yes  [ ] no, note: ______

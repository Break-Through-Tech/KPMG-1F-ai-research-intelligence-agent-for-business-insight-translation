# fresh-business-v1: answer-key review packet

For Codex review and human sign-off. For each required point, check:

1. The expected answer is stated by the anchor passage(s), with no number, subject, metric, condition or qualifier changed.
2. The question actually asks for it.
3. It is a published finding, not an inference.
4. Alternative anchors are genuinely equivalent.

Record decisions in REVIEW-STATUS.md. **Any change to the key requires rebuilding and resealing before any run.** The questions, the selected evidence budget (6k skip-fit) and the acceptance criteria stay frozen.

"In packet" shows whether the anchor group is fully inside the offline 6k skip-fit packet (Baseline route) and the top-8 packet. It is for information only and must not influence the review. It was computed before the review corrections, against the first anchor only (the G06.2 alternative c0004 was added afterwards).

**Corrections applied after the first review (resealed):**

- **G09.4** separates monetary cost (not reported) from computational cost proxies (reported, citable).
- **G06.2** accepts either source figure (60% from the introduction, c0004; 66% from the results, c0019) when it is correctly attributed, and credits answers that identify the inconsistency.
- **G05.5** keeps the source limitation: the dispute-resolution mechanism helps only "to a certain degree" and still "falls short of the upper bound". Without that limitation, at most 0.5.
- **G09.4 partial credit:** proxies alone, without saying monetary cost is not reported, score 0.5.
- **G04.5 and G10.4** each have two components; both are required for 1, and one alone scores 0.5.

**Codex review corrections (third reseal):**

- **G03.5** names both target models (c0019). The ASR pairs are reported as the source gives them; mapping a pair to a model or metric as fact is unsupported. It adds the effort/cost component: no compute cost is established for adversarial tuning (LoRA, c0015), and the 20-minute GCG figure is a prior method's cost.
- **G06.2**: 60% and 66% are compatible lower bounds. The group statistics (means and SDs) require c0019.
- **G07.3** adds methods anchor c0014 (finstat2sql is a fine-tuned Qwen 2.5 Coder per size).
- **G08.4** accepts the calculated 0.4 points (~0.65% relative) or the paper's "0.8%" attributed to the paper.
- **G09.4** limits the fabrication rule to monetary prices not supported by the study.

See REVIEW-STATUS.md.

## G01 (single-paper)

**Question.** A client's risk committee asks whether market mechanisms, not only regulation, can govern AI risk. What market mechanisms does the 'AI Governance through Markets' paper propose, how do they connect AI risk to financial risk, and what limits do the authors acknowledge?

### G01.1

**Expected:** Four market-governance vectors: insurance, auditing, procurement and due diligence.

*in skip-fit packet: yes; in top-8 packet: yes*

**Alternative 1:** 2501.17755v2_c0000

> `2501.17755v2_c0000` · AI Governance through Markets · abstract
>
> This paper argues that market governance mechanisms should be considered a key approach in the governance of artificial intelligence (AI), alongside traditional regulatory frameworks. While current governance approaches predominantly focus on regulation, we contend that market-based mechanisms offer effective incentives for responsible AI development. We examine four emerging vectors of market governance: insurance, auditing, procurement, and due diligence, demonstrating how these mechanisms can affirm the relationship between AI risk and financial risk while addressing capital allocation inefficiencies. While we do not claim that market forces alone can adequately protect societal interests, we maintain that standardised AI disclosures and market mechanisms can create powerful incentives for safe and responsible AI development. This paper urges regulators, economists, and machine learning researchers to investigate and implement market-based approaches to AI governance.

**Alternative 2:** 2501.17755v2_c0003

> `2501.17755v2_c0003` · AI Governance through Markets · overview
>
> 4 AI market governance mechanisms. By market governance mechanisms, we refer to tools and processes that align financial incentives with desired social or economic outcomes by structuring economic behaviour ( Sbragia, 2000 ) . These mechanisms include (but are not limited to) insurance, auditing, procurement practices, and due diligence - which in turn serve risk distribution, information discovery, protocolisation and capital allocation. In the context of AI governance, market governance mechanisms aim to decrease AI risk by pricing, measuring and mitigating the risk incurred in AI deployment and development. These mechanisms further enable public and private stakeholders to shape AI in ways that align with broader societal and economic goals, fostering a balance between innovation and risk mitigation. As Hadfield and Clark argue ( Hadfield and Clark, 2023 ) AI fundamentally disrupts traditional regulatory frameworks in ways that demand comprehensive reconsideration of our approach. Their analysis suggests that the primary challenge is not simply creating new rules for AI-specific risks, but developing dynamic regulatory approaches that can adapt to AI’s pervasive influence. Their proposal for regulatory markets can be seen as one possible structure within which market governance mechanisms can operate. Their example demonstrates the broad array of policy strategies available towards market governance of AI, which can range from complete self-governance to government mandates with punitive enforcement. Market governance mechanisms often function as private regulators, for-profit and non-

### G01.2

**Expected:** They serve risk distribution, information discovery, protocolisation and capital allocation, decreasing AI risk by pricing, measuring and mitigating it.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2501.17755v2_c0003

> `2501.17755v2_c0003` · AI Governance through Markets · overview
>
> 4 AI market governance mechanisms. By market governance mechanisms, we refer to tools and processes that align financial incentives with desired social or economic outcomes by structuring economic behaviour ( Sbragia, 2000 ) . These mechanisms include (but are not limited to) insurance, auditing, procurement practices, and due diligence - which in turn serve risk distribution, information discovery, protocolisation and capital allocation. In the context of AI governance, market governance mechanisms aim to decrease AI risk by pricing, measuring and mitigating the risk incurred in AI deployment and development. These mechanisms further enable public and private stakeholders to shape AI in ways that align with broader societal and economic goals, fostering a balance between innovation and risk mitigation. As Hadfield and Clark argue ( Hadfield and Clark, 2023 ) AI fundamentally disrupts traditional regulatory frameworks in ways that demand comprehensive reconsideration of our approach. Their analysis suggests that the primary challenge is not simply creating new rules for AI-specific risks, but developing dynamic regulatory approaches that can adapt to AI’s pervasive influence. Their proposal for regulatory markets can be seen as one possible structure within which market governance mechanisms can operate. Their example demonstrates the broad array of policy strategies available towards market governance of AI, which can range from complete self-governance to government mandates with punitive enforcement. Market governance mechanisms often function as private regulators, for-profit and non-

### G01.3

**Expected:** Insurance can make safety-washing or underestimating AI risk less appealing; actuarial rigour can curb AI hype.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2501.17755v2_c0011

> `2501.17755v2_c0011` · AI Governance through Markets · risk distribution: insurance
>
> . Insurance has the potential to create a more favourable incentive structure by making practices such as “safety-washing” or underestimating AI-related risks less appealing ( Tomei, 2024 ) . The rigour of actuarial assessments may engender an anti-speculative framework for pricing AI development, curtailing so called ’AI Hype’ - much like it has done in other sectors, such as real estate in climate-vulnerable areas ( Nyce et al., 2015 ) . By pricing, mitigating, and transferring risk, insurance can encourage more accurate assessment and analysis of AI risk profiles. In so doing, the development of a robust AI insurance market may enable both first- and third-party stakeholders to more accurately understand the risk profile of AI development. Cyberrisk provides a crucial precedent for AI risk. This has emerged as the most pressing form of business risk, mirroring the indispensability of software in every major enterprise ( Forum, 2024 ) . Accordingly, he financial toll of cyberattacks swells by 15% annually up to $23tn by 2027 ( Economist, 2024 ) . Among numerous potential solutions to this pervasive insecurity, insurance offers some respite. A robust cyber incident insurance market incentivises organisations to strengthen their cyber defences, ultimately reducing societal cyber risk ( Marsh, 2021 ) . While still in its infancy, cyberrisk insurance has promoted accurate analysis and pricing of the risk landscape. It further incentivises the adoption of cybersecurity measures by making plain the financial consequences incurred and reducing premiums or disqualifying policyholders with insufficient security measures. As AI becomes integrated into the value creation of major industries, AI insurance will be in increasing demand

### G01.4

**Expected:** The authors do not claim market forces alone adequately protect societal interests; standardised AI disclosures are needed alongside market mechanisms.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2501.17755v2_c0000

> `2501.17755v2_c0000` · AI Governance through Markets · abstract
>
> This paper argues that market governance mechanisms should be considered a key approach in the governance of artificial intelligence (AI), alongside traditional regulatory frameworks. While current governance approaches predominantly focus on regulation, we contend that market-based mechanisms offer effective incentives for responsible AI development. We examine four emerging vectors of market governance: insurance, auditing, procurement, and due diligence, demonstrating how these mechanisms can affirm the relationship between AI risk and financial risk while addressing capital allocation inefficiencies. While we do not claim that market forces alone can adequately protect societal interests, we maintain that standardised AI disclosures and market mechanisms can create powerful incentives for safe and responsible AI development. This paper urges regulators, economists, and machine learning researchers to investigate and implement market-based approaches to AI governance.


## G02 (single-paper)

**Question.** A multinational client must align its AI risk management across the EU, the U.S., the UK and China. According to the cross-regional study of AI risk-management frameworks, how do the four regimes differ and what trade-off does each carry?

### G02.1

**Expected:** EU: structured, risk-based framework prioritising transparency and conformity assessments.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2503.05773v1_c0001

> `2503.05773v1_c0001` · Between Innovation and Oversight: A Cross-Regional Study of AI Risk Management Frameworks in the EU, U.S., UK, and China · abstract
>
> The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement. The flexible, sector-specific strategy of the UK facilitates agile responses but may lead to inconsistent coverage across domains. China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight. These insights show the necessity for AI regulation that is globally informed yet context-sensitive, aiming to balance effective risk management with technological progress. The paper concludes with policy recommendations and suggestions for future research aimed at enhancing effective, adaptive, and inclusive AI governance globally. K eywords AI Governance, AI Risk Management Frameworks, EU AI Act, Comparative Analysis

### G02.2

**Expected:** U.S.: decentralised, sector-specific regulation that promotes innovation but may fragment enforcement.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2503.05773v1_c0001

> `2503.05773v1_c0001` · Between Innovation and Oversight: A Cross-Regional Study of AI Risk Management Frameworks in the EU, U.S., UK, and China · abstract
>
> The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement. The flexible, sector-specific strategy of the UK facilitates agile responses but may lead to inconsistent coverage across domains. China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight. These insights show the necessity for AI regulation that is globally informed yet context-sensitive, aiming to balance effective risk management with technological progress. The paper concludes with policy recommendations and suggestions for future research aimed at enhancing effective, adaptive, and inclusive AI governance globally. K eywords AI Governance, AI Risk Management Frameworks, EU AI Act, Comparative Analysis

### G02.3

**Expected:** UK: flexible, sector-specific strategy enabling agile responses but risking inconsistent coverage across domains.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2503.05773v1_c0001

> `2503.05773v1_c0001` · Between Innovation and Oversight: A Cross-Regional Study of AI Risk Management Frameworks in the EU, U.S., UK, and China · abstract
>
> The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement. The flexible, sector-specific strategy of the UK facilitates agile responses but may lead to inconsistent coverage across domains. China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight. These insights show the necessity for AI regulation that is globally informed yet context-sensitive, aiming to balance effective risk management with technological progress. The paper concludes with policy recommendations and suggestions for future research aimed at enhancing effective, adaptive, and inclusive AI governance globally. K eywords AI Governance, AI Risk Management Frameworks, EU AI Act, Comparative Analysis

### G02.4

**Expected:** China: centralised directives enable rapid large-scale implementation while constraining public transparency and external oversight.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2503.05773v1_c0001

> `2503.05773v1_c0001` · Between Innovation and Oversight: A Cross-Regional Study of AI Risk Management Frameworks in the EU, U.S., UK, and China · abstract
>
> The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement. The flexible, sector-specific strategy of the UK facilitates agile responses but may lead to inconsistent coverage across domains. China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight. These insights show the necessity for AI regulation that is globally informed yet context-sensitive, aiming to balance effective risk management with technological progress. The paper concludes with policy recommendations and suggestions for future research aimed at enhancing effective, adaptive, and inclusive AI governance globally. K eywords AI Governance, AI Risk Management Frameworks, EU AI Act, Comparative Analysis


## G03 (cross-paper)

**Question.** A client must defend a customer-facing LLM against new jailbreaks. How do Safety Context Retrieval (SCR) and two-stage adversarial tuning differ in approach, how effective were they, and what did each cost in normal-task performance or effort?

### G03.1

**Expected:** SCR keeps a pool of safety contexts, adds a minimal set of safety samples when a new jailbreak is identified, and retrieves a few at inference, instead of repeatedly fine-tuning.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2505.15753v1_c0003

> `2505.15753v1_c0003` · Scalable Defense against In-the-wild Jailbreaking Attacks with Safety Context Retrieval · introduction
>
> . Based on the preliminary studies above, we aim to build a defense framework that identifies the type of attack (if any) during inference and adds the corresponding safety context. Meanwhile, the maintained attack types and safety contexts should be scalable, allowing developers to easily add new attacks across different LLMs. To this end, we leverage the retrieval-augmented generation (RAG) techniques and propose the Safety Context Retrieval (SCR) paradigm. Specifically, SCR maintains a safety context pool, initialized by a group of common jailbreaks. When an in-the-wild jailbreak is reported and identified, SCR can automatically add a minimal set of safety samples into its pool. During inference, SCR retrieves a few examples from its full pool as the context. Notably, even though the input prompt is a natural one, SCR can still infer regularly without decreasing natural performance. Our experiments mainly focus on three key aspects of SCR. First, as a defense mechanism, we demonstrate the robustness of SCR against common jailbreak attacks like GCG-T [ 57 ] , e.g. , achieving 2.5% attack success rate (ASR) averaged on three models. Such robustness also outperforms RapidResponse since it can only be used against novel attacks. Then, we show the scalability and effectiveness of SCR, where a few samples are sufficient to eliminate an in-the-wild jailbreak, significantly outperforming static contextual-based defense baselines. Finally, we illustrate the harmlessness of SCR, i.e. non-decrease on natural performance, showing its practicality in real-world deployments

### G03.2

**Expected:** SCR reduced average ASR against GCG-T from 34.9% (no defence) to 2.5%.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2505.15753v1_c0018

> `2505.15753v1_c0018` · Scalable Defense against In-the-wild Jailbreaking Attacks with Safety Context Retrieval · experiment
>
> First, we show that the retrieval mechanism of SCR is able to defend against common jailbreak attacks, fulfilling the basic requirements of a feasible jailbreak defense. We consider two kinds of popular attacks: prompt-based and optimization-based. Defending against prompt-based attacks . Prompt-based attacks refer to the adversarial prefix or suffix that can be attached to the harmful request for jailbreaking. Along this thread, we first consider the transferable GCG (GCG-T) [ 57 ] and the in-context attack (ICA) [ 43 ] for evaluation. The GCG-T attaches a transferable jailbreak suffix to each harmful request, while ICA adds a few harmful demonstrations to the context window. To maximize jailbreak effectiveness, we utilized 50-shot ICA. The overall results are summarized in Table 2 , where SCR achieves the lowest attack success rate (ASR) across all models. For GCG-T, SCR reduces the average ASR from 34.9% (no defense) to 2.5%, significantly outperforming Self-reminder and ICD. Similarly, for ICA, SCR lowers the average ASR from 45.4% to 7.4%, demonstrating the consistent robustness of SCR in defending against these prompt-based common attacks. ASR (%) comparison against prompt-based attacks. Defending against optimization-based attacks . Another thread of common attacks is the optimization-based attacks, which iteratively refine the jailbreaking prompt to increase the harmful response probability. In this experiment, we consider Prompt Automatic Iterative Refinement (PAIR) [ 6 ] and Tree of Attacks with Pruning (TAP) [ 33 ] , which are both popular red-teaming LLM-based optimization attacks. The results are shown in Table 3 , where SCR achieves the lowest average ASR of 15.9% against PAIR and 10.1% against TAP

### G03.3

**Expected:** SCR had negligible effect on natural performance (e.g. Llama-3.1 HumanEval 61.6% to 57.3%, MMLU 62.6% to 63.2%).

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2505.15753v1_c0021

> `2505.15753v1_c0021` · Scalable Defense against In-the-wild Jailbreaking Attacks with Safety Context Retrieval · experiment
>
> As for the natural performance, SCR exhibits minimal impact on the various tasks of LLMs. As shown in Table 5 , across three popular tasks, SCR maintains the performance of the evaluated models. For example, SCR slightly reduces the HumanEval score from 61.6% to 57.3% on Llama-3.1, while improving the GSM8K score from 82.3% to 80.2% and the MMLU score from 62.6% to 63.2%, which are within the variance of randomness. On average, SCR shows negligible effects on natural performance, proving its practicality as a defense mechanism that safeguards LLMs without compromising their inherent capabilities. Natural performance of the LLMs across reasoning tasks. The score for Mistral on HumanEval is not applicable ( NA ) since it achieves nearly 0% accuracy, which was also reported in [ 38 ] .

### G03.4

**Expected:** Adversarial tuning is two-stage: hierarchical meta-universal (token-level) adversarial prompts, then automatic semantic-level adversarial prompts, used to fine-tune on adversarial prompt and safe-response pairs.

*in skip-fit packet: yes; in top-8 packet: no*

**Anchor:** 2406.06622v1_c0000

> `2406.06622v1_c0000` · Adversarial Tuning: Defending Against Jailbreak Attacks for LLMs · abstract
>
> Although safely enhanced Large Language Models (LLMs) have achieved remarkable success in tackling various complex tasks in a zero-shot manner, they remain susceptible to jailbreak attacks, particularly the unknown jailbreak attack. To enhance LLMs’ generalized defense capabilities, we propose a two-stage adversarial tuning framework, which generates adversarial prompts to explore worst-case scenarios by optimizing datasets containing pairs of adversarial prompts and their safe responses. In the first stage, we introduce the hierarchical meta-universal adversarial prompt learning to efficiently and effectively generate token-level adversarial prompts. In the second stage, we propose the automatic adversarial prompt learning to iteratively refine semantic-level adversarial prompts, further enhancing LLM’s defense capabilities. We conducted comprehensive experiments on three widely used jailbreak datasets, comparing our framework with six defense baselines under five representative attack scenarios. The results underscore the superiority of our proposed methods. Furthermore, our adversarial tuning framework exhibits empirical generalizability across various attack strategies and target LLMs, highlighting its potential as a transferable defense mechanism. Warning: This paper contains red-teaming data and model-generated content that can be offensive!

### G03.5

**Expected:** Two components, both required for 1 (one alone scores 0.5). (a) On the two target models, Llama-2-7B-chat and Vicuna-13B-v1.5, known jailbreaks gave average ASR of 66.54% / 51.38% and 19.62% / 9.62% under two metrics; adversarial tuning reduced them to 2.69% / 0.00% and 3.08% / 0.00%. The passage reports these pairs "respectively" without readable metric labels, so an answer may report them as pairs; assigning a pair to a specific model or metric as fact is an unsupported attribution. (b) Effort/cost: the passages give no compute-cost figure for adversarial tuning itself (it uses LoRA to improve training efficiency); an answer must say the cost is not established. Presenting the 20-minute GCG prompt-generation figure as the cost of adversarial tuning is a misattribution.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2406.06622v1_c0021 + 2406.06622v1_c0019 + 2406.06622v1_c0015 (all rows required together)

> `2406.06622v1_c0021` · Adversarial Tuning: Defending Against Jailbreak Attacks for LLMs · experiments
>
> Known Jailbreak Attack. Table 1 summarizes the results of previous state-of-the-art methods and our defense for both token-level and prompt-level jailbreaks. Our methods consistently outperform other state-of-the-art methods across two metrics for five attacks. Specifically, the jailbreak attacks lead to average ASR (66.54% / 51.38%) and ASR (19.62%, 9.62%) on the two target models under two metrics, respectively. Existing defense methods perform poorly, while our defense methods reduce the average ASR (2.69% / 0.00%) and ASR (3.08% / 0.00%) on two target models under the two metrics. The experimental results highlight the efficacy of our proposed methods in mitigating adversarial prompts, significantly surpassing current methods. In addition, we noticed that Self-Reminder performs better on Llama-2-7B than Vicuna-13B, likely because Llama-2-7B uses stronger safety alignment, which the self-reminder effectively triggers. We report the overall attack budget in Appendix D.1 . Known jailbreak attack experiments on dataset AdvBench under metric \text{ASR}_{\text{P}} and \text{ASR}_{\text{A}} . Unknown jailbreak attack experiments on dataset MaliciousInstruct under metric \text{ASR}_{\text{P}} and \text{ASR}_{\text{A}} . Unknown Jailbreak Attack. Robustness against unknown jailbreaks poses a significant challenge for defense methods due to the vast array of potential prompts and variations. We evaluate the effectiveness of our defense methods against unknown jailbreak attacks using the MaliciousInstruct datasets. Table 2 presents the comprehensive experimental results. Our methods consistently outperform other state-of-the-art approaches across both metrics for five distinct attacks

> `2406.06622v1_c0019` · Adversarial Tuning: Defending Against Jailbreak Attacks for LLMs · experiments
>
> Datasets. To evaluate the efficacy of various defense methods, we employ widely recognized datasets, including AdvBench [ 2 ] , MaliciousInstruct [ 19 ] , and Forbidden Question Set [ 15 ] . AdvBench comprises 520 malicious prompts specifically designed to elicit harmful responses, with 90% allocated for training and the remaining 10% for testing. To assess the generalized defense capabilities of our methods against unknown jailbreak attacks, we employ all the data from the MaliciousInstruct and Forbidden Question Set as test datasets. MaliciousInstruct comprises 100 instances of harmful behavior spanning ten distinct categories of malicious intent. The Forbidden Question Set includes jailbreak prompts gathered from various internet platforms. Target Model. The target models are two open-sources model Llama-2 (7B-chat-hf) and Vicuna (13B-v1.5). To assess the transferability of adversarial examples, we extend our investigation to include a broader range of open-source models, encompassing various sizes and types. Specifically, we consider Llama-2 (13B, 70B) chat models, Llama-3 (8B), Vicuna (7B, 13B), Mistral-7B-v0.1, and Qwen1.5-7B-Chat. Adversarial fine-tuning is conducted on datasets sourced from Llama-2 (7B-chat-hf). Jailbreak Attacks. To assess the effectiveness of various defense strategies, we compare the strongest attack methods, encompassing both token-level attacks (GCG [ 2 ] and AutoDAN [ 13 ] ) and prompt-level attacks (PAIR [ 17 ] , TAP [ 20 ] , and GPTFuzzer [ 1 ] ). Baselines. We compare our framework with state-of-the-art defense methods following the five most representative baselines, including both the system-level and model-level defense methods. System-level defense methods: Self-Reminder [ 7 ] , SmoothLLM [ 6 ] , and RPO [ 21 ]

> `2406.06622v1_c0015` · Adversarial Tuning: Defending Against Jailbreak Attacks for LLMs · methodology
>
> . In the initial training stage for the LLM’s backbone, we implement a token-level adversarial fine-tuning strategy to enable the model to process adversarial prompts and reject malicious instructions effectively. We employ the negative log-likelihood (NLL) as our loss function: where P_{\pi_{\theta}}(\tilde{\mathbf{y}}_{t}|\hat{\mathbf{x}}_{1:n},\tilde{\mathbf{y}}_{t}) denotes the probability distribution of the position at \tilde{\mathbf{y}}_{<t} . \tilde{\mathbf{y}} denotes the desired safe response of adversarial prompt \hat{\mathbf{x}}_{1:n} . \tilde{\mathbf{y}} when prompted with \hat{\mathbf{x}}_{1:n} . To enhance training efficiency, we apply parameter-efficient fine-tuning (PEFT) techniques. In particular, we employ low-rank adaptation (LoRA) by introducing small adapters into certain layers, significantly minimizing the number of trainable parameters required for our training process. After the first stage of adversarial tuning, we denote the model parameters as \theta_{1} .


## G04 (cross-paper)

**Question.** A client plans custom GPT-style assistants with uploaded knowledge files and fine-tuning services for business units. What do the Pandora and 'Attack via Overfitting' studies show about these customisation routes as jailbreak attack surfaces, how successful were the attacks, and how detectable are they?

### G04.1

**Expected:** Pandora poisons RAG: malicious content uploaded as knowledge files plus crafted prompts makes GPTs jailbreak indirectly.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2402.08416v1_c0003

> `2402.08416v1_c0003` · Pandora: Jailbreak GPTs by Retrieval Augmented Generation Poisoning · introduction
>
> . This method involves creating malicious content that serves as a tainted knowledge source for RAG, coupled with specifically crafted prompts to initiate jailbreak attacks in GPT models. Our evaluation demonstrates that Pandora can effectively lead to jailbreak attacks in four distinct prohibited scenarios for GPTs. The success rate of Pandora in these scenarios is noteworthy, achieving 64.3% for GPT-3.5 and 34.8% for GPT-4, surpassing the effectiveness of direct jailbreak attacks. To summarize, we make the following contributions. Novel attack vector. We present a novel attack vector: jailbreaking LLM-integrated apps enhanced by RAG. Comprehensive attack methodology. We introduce a comprehensive framework targeting OpenAI GPTs to generate and launch end-to-end jailbreak GPTs, allowing any user to achieve jailbreak via the constructed GPTs. Preliminary evaluation. We evaluate our solution through preliminary experiments, and demonstrate that it could effectively achieve consistent jailbreak attacks on the latest version of OpenAI GPTs. Ethical Disclaimer : The research conducted and presented in this study is strictly for academic and research purposes only. We adhere to the highest ethical standards, and the sole objective is to contribute to the scientific understanding and security of AI systems. All findings and potential vulnerabilities discovered during this research have been responsibly reported, ensuring that our work aligns with the broader goals of enhancing AI safety and security. We also place a strong emphasis on the well-being of our research team; all authors and contributors involved in this project have access to mental health support and are encouraged to seek care should they experience any distress or discomfort related to the research

### G04.2

**Expected:** Pandora success 64.3% on GPT-3.5 and 34.8% on GPT-4 across four prohibited scenarios, versus 3.0% and 1.0% for naive malicious questions.

*in skip-fit packet: yes; in top-8 packet: no*

**Anchor:** 2402.08416v1_c0016

> `2402.08416v1_c0016` · Pandora: Jailbreak GPTs by Retrieval Augmented Generation Poisoning · preliminary evaluation
>
> We follow the experiment settings to conduct the experiments, and the results are presented in Table I . Our findings indicate that Pandora is remarkably effective in instigating jailbreak attacks across different scenarios. Notably, Pandora demonstrates an average success rate of 64.3% and 34.8% on the four prohibited senarios over the GPT-3.5 and GPT-4 version of GPT instances, respectively. As a comparision, naive malicious question only achieve 3.0% and 1.0% of success rates over ChatGPT powered by the same models. This high success rate demonstrates Pandora ’s capability to achieve jailbreak by leveraging GPTs. Analyzing the experimental results reveals several key insights. First, despite varying success rates across different models, the prohibited scenario of Privacy is consistently the easiest to jailbreak, with an average success rate of 35.3% in the four comparison groups. This finding aligns with conclusions from previous works that indicate varying difficulties in jailbreak scenarios. It suggests that while some content categories are more readily manipulated, others may require more sophisticated approaches for a successful jailbreak. Second, comparing naive injection over chatbots powered by GPT-3.5 and GPT-4 models, and GPT instances powered by these models, it is observed that GPT-4 powered chatbots and GPTs are more challenging to jailbreak. This can be attributed to the improved alignment in the training process of GPT-4. Finally, the repeatability of these results across multiple rounds underscores the consistency and reliability of Pandora as a tool for probing the vulnerabilities of GPT models in the context of content policy violations. Number and ratio of successful jailbreaking attempts for different models and scenarios.

### G04.3

**Expected:** The overfitting attack fine-tunes on 10 benign QA pairs: first with identical refusal answers to induce overfitting, then with normal answers, after which the model complies with harmful questions.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2510.02833v4_c0003

> `2510.02833v4_c0003` · Attack via Overfitting: 10-shot Benign Fine-tuning to Jailbreak LLMs · introduction
>
> understanding of the attack mechanism. Moreover, the harmfulness (albeit implicit) of the adopted QA pairs can also be detected by certain moderation models, such as GPT-4.1-mini ( OpenAI, 2025c ) with a judge prompt. Overview of our attack that consists of two stages. i) In the first stage, the LLM is fine-tuned with 10 QA pairs with identical refusal answers to induce overfitting. Consequently, the LLM refuses to answer any questions, including the benign ones. ii) In the second stage, the LLM is further fine-tuned on the same 10 benign QA pairs but with standard answers. After this stage, the LLM is compliant with any questions, including harmful ones. Aiming to address the critical issues mentioned above,

### G04.4

**Expected:** It reached 94.84% average ASR across ten LLMs (HS 4.48), comparable to malicious fine-tuning (97.25%).

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2510.02833v4_c0016

> `2510.02833v4_c0016` · Attack via Overfitting: 10-shot Benign Fine-tuning to Jailbreak LLMs · experiment
>
> Table 1 summarizes the attack effectiveness across all tested LLMs and methods. The results demonstrate that our attack achieves an average ASR of 94.84% and HS of 4.48. This performance is notably comparable to that of malicious fine-tuning (average 97.25% ASR, 4.87 HS) using explicitly harmful data. In contrast, other baseline attacks exhibit significantly lower efficacy. The AOA fine-tuning (with shuffled data) gets an average ASR of 28.94%, highlighting its instability. Notably, the AOA attack is generally less effective against a more powerful model than against a weaker one. This indicates that while the weaker model is susceptible to the semantic-level inducement (“persuade” the model to be absolutely obedient) in the attack, the stronger model is significantly more robust to it. Encryption fine-tuning proves to be ineffective for the weaker models, with a mere 14.66% average ASR. Except for the two strongest models, the others cannot fully understand the encryption rules and thus generate meaningless answers. Indirect malicious fine-tuning achieves only a modest average ASR of 40.75% despite leveraging datasets with prohibited content, indicating that the harmfulness of the fine-tuning data does not solely determine the attack effectiveness. Irrelevant fine-tuning shows even less efficacy, with a 38.68% average ASR, and also fails to reliably jailbreak the LLMs. In summary, these findings underscore that our attack achieves high attack effectiveness comparable to malicious fine-tuning, and inherent stealth stemming from its exclusive use of benign data. This dual advantage highlights the superiority of our attack. Attack effectiveness of six attack methods on ten well-known LLMs Impact of different factors on our attack’s effectiveness across ten LLMs

### G04.5

**Expected:** Two components, both required for 1 (one alone scores 0.5): (a) because the data is entirely benign it is stealthy against moderation models, which catch malicious fine-tuning; (b) it bypassed a token-wise loss defence.

*in skip-fit packet: no; in top-8 packet: no*

**Alternative 1:** 2510.02833v4_c0005

> `2510.02833v4_c0005` · Attack via Overfitting: 10-shot Benign Fine-tuning to Jailbreak LLMs · introduction
>
> The results firmly demonstrate that our method is comparable to malicious fine-tuning in terms of attack effectiveness and efficiency, while achieving adequate stealthiness against moderation models, as we use entirely benign data with no harmful guidance. In summary, our contributions are as follows: As far as we know, we are the first to leverage overfitting of the LLM to jailbreak LLMs. We propose a novel two-stage fine-tuning attack where only 10 benign QA pairs are used to jailbreak the LLM. We implement the attack and launch comprehensive experiments on ten LLMs and five baselines. The results show that our method achieves significant advantages in both attack stealth and effectiveness. The remainder of this paper goes as follows. Section 2 introduces the background and motivation of our methods, followed by Section 3 illustrates the design of our attacks. We evaluate the performance of our attack and explain our attack in Section 4 , before we conclude the paper in Section 5 .

**Alternative 2:** 2510.02833v4_c0027

> `2510.02833v4_c0027` · Attack via Overfitting: 10-shot Benign Fine-tuning to Jailbreak LLMs · conclusion
>
> This paper presents a novel two-stage attack that jailbreaks LLMs using only ten benign question-answer pairs by exploiting overfitting. We demonstrate that inducing overfitting with identical refusal answers, followed by fine-tuning with standard benign responses, causes catastrophic forgetting of the model’s refusal capabilities. This method achieves high attack success and stealth across ten LLMs, notably bypassing a token-wise defense mechanism. Our findings reveal a critical LLM vulnerability related to overfitting with benign data, urging the development of more robust security measures.


## G05 (cross-paper)

**Question.** A hospital-network client is assessing LLMs for patient-facing conversations. How did the Polaris and AI Hospital studies evaluate conversational medical LLMs, and what do their results imply about readiness?

### G05.1

**Expected:** Polaris is a constellation (about one trillion parameters) of a primary conversational agent and specialist support agents for nurse, social-worker and nutritionist tasks, to increase safety and reduce hallucinations.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2403.13313v1_c0000

> `2403.13313v1_c0000` · Polaris: A Safety-focused LLM Constellation Architecture for Healthcare · abstract
>
> We develop Polaris 1 1 Safety is our North Star. We name our system after Polaris, a star in the northern circumpolar constellation of Ursa Minor, currently designated as the North Star. , the first safety-focused Large Language Model (LLM) constellation for real-time patient-AI healthcare conversations. Unlike prior LLM works in healthcare, which focus on tasks like question answering, our work specifically focuses on long multi-turn voice conversations. Our one-trillion parameter constellation system is composed of several multi-billion parameter LLMs as co-operative agents: a stateful primary agent that focuses on driving an engaging patient-friendly conversation and several specialist support agents focused on healthcare tasks performed by nurses, social workers, and nutritionists to increase safety and reduce hallucinations. We develop a sophisticated training protocol for iterative co-training of the agents that optimize for diverse objectives. We train our models on proprietary data, clinical care plans, healthcare regulatory documents, medical manuals, and other medical reasoning documents. We further align our models to speak like medical professionals, using organic healthcare conversations and simulated ones between patient actors and experienced care-management nurses. This allows our system to express unique capabilities such as rapport building, trust building, empathy and bedside manner augmented with advanced medical reasoning. Finally, we present the first comprehensive clinician evaluation of an LLM system for healthcare. We recruited over 1100 U.S. licensed nurses and over 130 U.S. licensed physicians to perform end-to-end conversational evaluations of our system by posing as patients and rating the system on several fine-grained measures

### G05.2

**Expected:** Over 1,100 U.S. nurses and 130 physicians posed as patients; Polaris performed on par with human nurses on aggregate across medical safety, clinical readiness, patient education, conversational quality and bedside manner.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2403.13313v1_c0001

> `2403.13313v1_c0001` · Polaris: A Safety-focused LLM Constellation Architecture for Healthcare · abstract
>
> . We recruited over 1100 U.S. licensed nurses and over 130 U.S. licensed physicians to perform end-to-end conversational evaluations of our system by posing as patients and rating the system on several fine-grained measures. We demonstrate Polaris performs on par with human nurses on aggregate across dimensions such as medical safety, clinical readiness, patient education, conversational quality, and bedside manner. Additionally, we conduct a challenging task-based evaluation of the individual specialist support agents, where we demonstrate our LLM agents significantly outperform a much larger general-purpose LLM (GPT-4) as well as one from its own medium-size class (LLaMA-2 70B).

### G05.3

**Expected:** Polaris's specialist agents significantly outperformed GPT-4 and LLaMA-2 70B on task-based evaluation.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2403.13313v1_c0001

> `2403.13313v1_c0001` · Polaris: A Safety-focused LLM Constellation Architecture for Healthcare · abstract
>
> . We recruited over 1100 U.S. licensed nurses and over 130 U.S. licensed physicians to perform end-to-end conversational evaluations of our system by posing as patients and rating the system on several fine-grained measures. We demonstrate Polaris performs on par with human nurses on aggregate across dimensions such as medical safety, clinical readiness, patient education, conversational quality, and bedside manner. Additionally, we conduct a challenging task-based evaluation of the individual specialist support agents, where we demonstrate our LLM agents significantly outperform a much larger general-purpose LLM (GPT-4) as well as one from its own medium-size class (LLaMA-2 70B).

### G05.4

**Expected:** AI Hospital simulates multi-agent clinical interaction and evaluates Doctor agents on the MVME benchmark of Chinese medical records (symptom collection, examinations, diagnosis).

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2402.09742v4_c0000

> `2402.09742v4_c0000` · AI Hospital: Benchmarking Large Language Models in a Multi-agent Medical Interaction Simulator · abstract
>
> Artificial intelligence has significantly advanced healthcare, particularly through large language models (LLMs) that excel in medical question answering benchmarks. However, their real-world clinical application remains limited due to the complexities of doctor-patient interactions. To address this, we introduce AI Hospital , a multi-agent framework simulating dynamic medical interactions between Doctor as player and NPCs including Patient , Examiner , Chief Physician . This setup allows for realistic assessments of LLMs in clinical scenarios. We develop the Multi-View Medical Evaluation (MVME) benchmark, utilizing high-quality Chinese medical records and NPCs to evaluate LLMs’ performance in symptom collection, examination recommendations, and diagnoses. Additionally, a dispute resolution collaborative mechanism is proposed to enhance diagnostic accuracy through iterative discussions. Despite improvements, current LLMs exhibit significant performance gaps in multi-turn interactions compared to one-step approaches. Our findings highlight the need for further research to bridge these gaps and improve LLMs’ clinical diagnostic capabilities. Our data, code, and experimental results are all open-sourced at https://github.com/LibertFan/AI_Hospital .

### G05.5

**Expected:** Interactive LLMs reached less than 50% of the one-step GPT-4 upper bound on diagnosis, rationale and treatment accuracy; a dispute-resolution collaborative mechanism improves performance only to a certain degree and still falls short of the upper bound. Stating the improvement without that limitation scores at most 0.5.

*in skip-fit packet: yes; in top-8 packet: no*

**Anchor:** 2402.09742v4_c0004

> `2402.09742v4_c0004` · AI Hospital: Benchmarking Large Language Models in a Multi-agent Medical Interaction Simulator · introduction
>
> . Our results reveal a substantial performance gap between interactive LLMs and the one-step GPT-4 , which serves as an upper bound by directly utilizing all patient information in a single interaction. On key metrics such as the accuracy of diagnostic results, diagnostic rationales, and treatment plans, the performance of interactive LLMs is less than 50% of that achieved by the one-step GPT-4. Despite dedicated prompting engineering, LLMs struggle to make reasonable decisions in multi-turn interactions, leading to suboptimal diagnostic accuracy. The dispute resolution collaborative mechanism enhances performance to a certain degree but also falls short of the upper bound. It’s suggested that existing LLMs may not have fully assimilated effective multi-turn diagnostic strategies. Our quantitative results highlights the challenges existing LLMs face in posing pertinent questions, eliciting crucial symptoms, and recommending appropriate medical examinations . These findings underscore the difficulties encountered by current LLMs in replicating the complex clinical reasoning processes employed by professional doctors and emphasize the need for further research to bridge the gap between LLMs and human physicians in clinical diagnosis


## G06 (numerical/table)

**Question.** A client relies on AI vendors' public safety commitments. How well did AI companies implement their 2023 White House voluntary commitments: overall scores, the best and worst performers, which commitment was weakest, and which looked strongest?

### G06.1

**Expected:** 16 companies scored; mean 53.3% (median 50.0%); OpenAI highest at 83.3%, Apple lowest at 13.3%.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2508.08345v2_c0018

> `2508.08345v2_c0018` · Do AI Companies Make Good on Voluntary Commitments to the White House? · results
>
> To organize our analysis, we apply three lenses: (i) an overall company-level view, (ii) a commitment-level view, and (iii) a disaggregated indicator-level view. In Figure 2 , we report the aggregate score as a percentage for each company across all the indicators. The mean and median are 53.3% and 50.0% respectively, with a standard deviation of 19.5%. The range is 70.0% between the highest scoring company, OpenAI, at 83.3% and the lowest scoring, Apple, at 13.3%. While OpenAI satisfies 25 of the 30 indicators, 9 9 The indicators that OpenAI does not satisfy are: “Insider threat detection program”, “Report limitations”, “Report domains of appropriate use”, “Empower trust and safety teams”, and “Support initiatives that help citizens understand the nature, capabilities, limitations, and impact of the technology”. no company has a perfect score despite making these commitments to the White House over two years ago. Significant variation in companies’ scores. There is notable variation in how companies perform, with companies clustering into three distinct groups. Four companies score at least one standard deviation above the mean: OpenAI (83.3%), Anthropic (80.0%), Google (76.7%), and Microsoft (73.3%). The majority of companies fall within one standard deviation of the mean: Amazon (66.7%), Meta (66.7%), IBM (53.3%), Nvidia (50.0%), Salesforce (50.0%), Adobe (36.7%), Cohere (43.4%), Palantir (36.7%), Inflection (36.7%), Stability AI (36.7%), Scale AI (36.7%). The only company that scores at least one standard deviation below the mean is Apple (13.3%).

### G06.2

**Expected:** The six Frontier Model Forum members are the highest-scoring companies. "At least 66%" (results) and "at least 60%" (introduction) are compatible lower bounds, and either may be quoted with its attribution. The group statistics must be supported by the results passage: FMF mean 74.4% (SD 6.9%); the other 10 companies score at or below 60% (mean 40.7%, SD 11.4%).

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2508.08345v2_c0019

> `2508.08345v2_c0019` · Do AI Companies Make Good on Voluntary Commitments to the White House? · results
>
> Aggregate scores by company. The score for each company, stratified by whether the company belongs to the Frontier Model Forum (FMF) as of December 31, 2024. Frontier Model Forum members consistently score higher. Strikingly, the company-level scores clearly separate based on membership in the Frontier Model Forum (FMF). The Frontier Model Forum is a non-profit industry association dedicated to advancing the safe development and deployment of frontier AI systems ( Frontier Model Forum 2024a ) . Anthropic, Google, Microsoft, and OpenAI became the four founding members in July 2023, with Amazon and Meta joining in May 2024. The six highest scoring companies, which all score at least 66%, are the six FMF members. Their mean score is 74.4% with a standard deviation of 6.9%. In contrast, the 10 other companies all score at or below 60% with a mean of 40.7% and a standard deviation of 11.4%. It is notable that FMF, in consultation with its members, has published technical reports intended in part to facilitate compliance with voluntary commitments ( Frontier Model Forum 2024b ) . FMF states that its technical reports aim to “examine how [Frontier AI] frameworks can be implemented effectively” and acknowledges that such frameworks are the core component of the Frontier AI Safety Commitments at 2024 AI Seoul Summit ( Frontier Model Forum 2024c ) . Earlier signatories generally score higher. The 16 companies signed onto the voluntary commitments in three phases of participation: seven companies in July 2023 (Amazon, Anthropic, Google, Inflection, Meta, Microsoft, and OpenAI), eight companies in September 2023 (Adobe, Cohere, IBM, Nvidia, Palantir, Salesforce, Scale AI, Stability AI) and one company in July 2024 (Apple).

### G06.3

**Expected:** Model-weight security averaged 17%; 11 of the 16 companies scored 0%.

*in skip-fit packet: yes; in top-8 packet: yes*

**Alternative 1:** 2508.08345v2_c0000

> `2508.08345v2_c0000` · Do AI Companies Make Good on Voluntary Commitments to the White House? · abstract
>
> Voluntary commitments are central to international AI governance, as demonstrated by recent voluntary guidelines issued from the White House to the G7, from Bletchley Park to Seoul. But do AI companies actually make good on their commitments? We score 16 companies based on their publicly disclosed behavior by developing a detailed rubric based on their eight voluntary commitments to the White House in 2023. We find significant heterogeneity: while the highest-scoring company (OpenAI) scores 83.3% overall on our rubric, the average score across all companies is just 53%. The companies demonstrate systemically poor performance on their commitment to model weight security, with an average score of 17%: 11 of the 16 companies receive 0% for this commitment. Our analysis highlights a clear structural shortcoming that future AI governance initiatives should correct: when companies make public commitments, they should proactively disclose how they meet their commitments to provide accountability, and these disclosures should be verifiable. To advance policymaking on corporate AI governance, we provide three directed recommendations that address underspecified commitments, the role of complex AI supply chains, and public transparency that could be incorporated into AI governance initiatives worldwide.

**Alternative 2:** 2508.08345v2_c0005

> `2508.08345v2_c0005` · Do AI Companies Make Good on Voluntary Commitments to the White House? · introduction
>
> Third, model weight security is a commitment with distinctively poor performance: companies score on average 17%. 11 companies score 0% on this commitment (Adobe, Apple, Cohere, IBM, Inflection, Meta, Nvidia, Palantir, Scale AI, Salesforce, Stability AI). Beyond providing empirical insight into the relationship between company practices and stated commitments, our work reveals a key design flaw in the 2023 White House Voluntary Commitments on AI: companies made public commitments to the White House, but no mechanism was created to monitor implementation or provide the public with information about implementation. To improve the design of future voluntary commitments related to corporate AI governance, we provide three recommendations to policymakers. 3 3 Unlike the 2023 White House Voluntary Commitments on AI, we find the 2024 White House Voluntary Commitments to Combat Image-Based Sexual Abuse adopt some of our recommendations. Commitments should be precise and specific. The wording of the 2023 White House Voluntary Commitments is often vague, leading to significant ambiguity over the intent of a commitment and the steps required to satisfy a commitment. Commitments should be precise, specifying (i) what is the specific goal and (ii) what evidence is sufficient or satisfactory to indicate completion. Commitments should be targeted. Since the same commitments are directed towards companies with different business models and roles in the AI supply chain, some commitments appear inappropriate for some companies (e.g. increased cybersecurity around model weights for companies that (largely) do not develop models).

### G06.4

**Expected:** Watermarking/provenance scored highest (92.2%), but often vacuously because many companies do not build audio or visual models.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2508.08345v2_c0021

> `2508.08345v2_c0021` · Do AI Companies Make Good on Voluntary Commitments to the White House? · results
>
> High scores for content provenance due to non-applicability. Based on the average per-commitment score for each company, the clear highest-scoring commitment is for (audiovisual) watermarking and provenance at 92.2%. 14 companies receive 100% for this commitment. 10 10 These companies are: Adobe, Amazon, Anthropic, Cohere, Google, IBM, Inflection, Meta, Microsoft, Nvidia, OpenAI, Palantir, Scale AI, Salesforce. In many cases, however, companies satisfy the associated indicators vacuously, because they do not develop audio or visual models, which are the subject of the provenance commitment. Still, of the 8 companies that develop models with these output modalities, the average is 83.9%, which exceeds that of all other commitments. In particular, many of these companies follow industry standards associated with the Coalition for Content Provenance and Authenticity (C2PA) and their Content Credentials; 6 of the 8 companies are steering committee members of C2PA, while Apple and Stability AI are unaffiliated. In contrast to the high scores for this commitment from most companies, Apple is the sole outlier as a company with audio and visual models that scores 0% on these indicators. Low scores for model-weight security in spite of global emphasis. Based on the averages, the lowest scoring commitment is on model-weight security at 22.9%. Eleven companies score 0% on this commitment, and none receives a full marks. The high-scoring companies are OpenAI, Anthropic, and Microsoft at 66.7%. Anthropic is the only company that indicates the existence of an insider risk program as part of its security standard. OpenAI and Microsoft, on the other hand, both state they create a secure research environment dedicated to model security and implement an access control protocol.


## G07 (numerical/table)

**Question.** A finance client wants natural-language querying of financial statements. What accuracy and speed did FinStat2SQL achieve, how did it compare with proprietary models and with its untuned base model, and what limits apply?

### G07.1

**Expected:** The fine-tuned 7B model reached 61.33% accuracy with sub-4-second responses on consumer hardware, outperforming GPT-4o-mini.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2506.23273v2_c0000

> `2506.23273v2_c0000` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · abstract
>
> Despite the advancements of large language models, text2sql still faces many challenges, particularly with complex and domain-specific queries. In finance, database designs and financial reporting layouts vary widely between financial entities and countries, making text2sql even more challenging. We present FinStat2SQL, a lightweight text2sql pipeline enabling natural language queries over financial statements. Tailored to local standards like VAS, it combines large and small language models in a multi-agent setup for entity extraction, SQL generation, and self-correction. We build a domain-specific database and evaluate models on a synthetic QA dataset. A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini. FinStat2SQL offers a scalable, cost-efficient solution for financial analysis, making AI-powered querying accessible to Vietnamese enterprises.

### G07.2

**Expected:** Best proprietary model Gemini-2.0-Flash-Thinking 72.03%; GPT-4o-mini 59.14%.

*in skip-fit packet: no; in top-8 packet: no*

**Alternative 1:** 2506.23273v2_table_4d7c993521f0bf29_1 + 2506.23273v2_table_4d7c993521f0bf29_6 (all rows required together)

> `2506.23273v2_table_4d7c993521f0bf29_1` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · Experiment
>
> Derived source table row (HTML cell serialization, not verbatim prose). FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis Table 4: Performance of LLMs on Evaluation set Model: gemini-2.0-flash-thinking; Params: –; Acc.: 0.7203

> `2506.23273v2_table_4d7c993521f0bf29_6` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · Experiment
>
> Derived source table row (HTML cell serialization, not verbatim prose). FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis Table 4: Performance of LLMs on Evaluation set Model: gpt-4o-mini; Params: –; Acc.: 0.5914

**Alternative 2:** 2506.23273v2_c0017 + 2506.23273v2_table_4d7c993521f0bf29_6 (all rows required together)

> `2506.23273v2_c0017` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · conclusion
>
> This research demonstrates that FinStat2SQL allows users to query complex financial data using natural language, significantly lowering the barrier for non-experts. The pipeline balances accuracy and efficiency effectively, with simpler architectures often outperforming more complex ones. While proprietary models like Gemini-2.0-Flash-Thinking achieved the highest accuracy (72.03%), open-source and fine-tuned models, especially DeepSeek V3 and Qwen2.5-Coder proved highly competitive. Notably, the 7B finstat2sql model matched or exceeded the performance of much larger models, highlighting the value of fine-tuned SLMs as cost-effective alternatives. Model alignment techniques were found to be unnecessary in many cases, and the system has been deployed as a financial chatbot with nearly 70% query success and sub-4-second response times, addressing a critical gap in Vietnam’s financial automation landscape.

> `2506.23273v2_table_4d7c993521f0bf29_6` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · Experiment
>
> Derived source table row (HTML cell serialization, not verbatim prose). FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis Table 4: Performance of LLMs on Evaluation set Model: gpt-4o-mini; Params: –; Acc.: 0.5914

### G07.3

**Expected:** Fine-tuning lifted the 7B Qwen2.5-Coder-Instruct from 47.93% to 61.33% (finstat2sql is a fine-tuned Qwen 2.5 Coder for each model size).

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2506.23273v2_table_d472857c5172bfd0_1 + 2506.23273v2_table_d472857c5172bfd0_4 + 2506.23273v2_c0014 (all rows required together)

> `2506.23273v2_table_d472857c5172bfd0_1` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · Experiment
>
> Derived source table row (HTML cell serialization, not verbatim prose). FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis Table 5: Evaluation on SLMs Model: qwen2.5-coder-instruct; Params: 7–8B; Acc.: 0.4793

> `2506.23273v2_table_d472857c5172bfd0_4` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · Experiment
>
> Derived source table row (HTML cell serialization, not verbatim prose). FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis Table 5: Evaluation on SLMs Model: finstat2sql; Params: [empty in source]; Acc.: 0.6133

> `2506.23273v2_c0014` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · experiment
>
> Summary of Models Used in the Experiments. To evaluate our pipeline’s effectiveness in processing Vietnamese financial statements, we tested a range of Language Models across two categories (see Table 2 ): Commercial LLMs and Small Language Models (SLMs). Where we denoted LLM: Commercial Large Language Model, SLM: Small Language Model. Deep Seek V3 having 671B params (37B activated each token), Qwen 2.5 has 2 model versions: 3B and 7B. Commercial LLMs are large, closed-source models accessed via API due to high resource demands, while smaller, open-source SLMs offer easier deployment and can achieve competitive performance with fine-tuning. Set up for training SLMs Further, we illustrate our setup and hyperparameters for SLM finetuning and techniques in Table 3 . In our experiment, DPO (Direct Preference Optimization) Rafailov et al. (2023) and KTO (Kahneman-Tversky Optimization) Ethayarajh et al. (2024) were used to align SLMs by leveraging GPT-4o-mini’s incorrect outputs and Gemini’s improved responses as training pairs, aiming to enhance reasoning in the text2sql pipeline. In general, our finstat2sql is a fine-tuned version of Qwen 2.5 Coder for each model size, integrated with our proposed pipeline for enhanced performance.

### G07.4

**Expected:** Limits: only VN30/HNX30-listed firms (no SMEs), Vietnamese terminology issues, and untested beyond Vietnam (e.g. US GAAP).

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2506.23273v2_c0018

> `2506.23273v2_c0018` · FinStat2SQL: A Text2SQL Pipeline for Financial Statement Analysis · conclusion
>
> This study has several limitations. First, the dataset is limited to VN30 and HNX30-listed firms, excluding Vietnam’s small and medium enterprises (SMEs), which may limit generalizability. Second, the system struggles with Vietnamese financial terminology variations, potentially affecting entity recognition due to inconsistencies and biases toward international standards like IFRS over VAS. Third, FinStat2SQL has only been tested in the Vietnamese context and may not perform well with global frameworks like US GAAP. Lastly, deploying high-performing closed-source models such as GPT-4o-mini requires substantial computational resources, potentially restricting accessibility and real-time application due to cost and infrastructure constraints. Future work will address these challenges by expanding the dataset to include SMEs, unlisted companies, and additional financial data sources for more comprehensive coverage. Efforts will also focus on adapting the pipeline for international standards to support cross-national applicability and integrating predictive analytics for trend forecasting and risk assessment. Given budget constraints, refining training methods and investigating why alignment techniques underperformed will be key, along with experimenting with data augmentation and improved fine-tuning strategies. These steps aim to enhance FinStat2SQL’s robustness, utility, and scalability for both local and global financial analysis.


## G08 (numerical/table)

**Question.** A client wants to harden an open-weight model against jailbreaks. What does the fail-closed alignment study report about why standard alignment fails, attack success, benign compliance, output quality and compute cost, and on which models was it tested?

### G08.1

**Expected:** Standard alignment encodes refusal along a single activation direction that prompt-based jailbreaks suppress, so it behaves fail-open.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2602.16977v1_c0028

> `2602.16977v1_c0028` · Fail-Closed Alignment for Large Language Models · conclusion
>
> This work challenges the assumption that LLM alignment can be robust without explicitly structuring refusal. We find that standard alignment procedures encode refusal along a single activation direction, which can be easily suppressed via prompt-based jailbreaks. This reveals a structural weakness: standard LLM alignment behaves as a fail-open system, where partial failures lead to unsafe compliance. Motivated by this, we propose fail-closed alignment as a design principle for robust LLM safety: refusal should be distributed across multiple independent, causally effective pathways such that no single direction is a point of failure. Our progressive alignment framework instantiates this principle by iteratively identifying and ablating previously learned refusal directions, forcing the model to reconstruct safety along new, independent subspaces. Across four models and diverse jailbreaks, we achieve the strongest overall robustness—reducing attack success rates by 92–97%—while maintaining high generation quality. By reframing alignment as a structural property, we offer a systematic approach to training aligned and robust LLMs.

### G08.2

**Expected:** At most 4% ASR in all cases; average ASR reduced by 92.3–97.2%, versus 23.8–93.7% for baselines.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2602.16977v1_c0019

> `2602.16977v1_c0019` · Fail-Closed Alignment for Large Language Models · evaluation
>
> Methodology. We fine-tune each model according to Algorithm 1 for 10 iterations with \lambda=1 , selecting the checkpoint with the lowest ASR on 50 held-out harmful prompts (see Appendix A.2 for details). For the baselines, we use official HuggingFace ( Wolf et al., 2020 ) models when available; otherwise, we train them using the authors’ official implementations and recommended hyperparameters. Results. Table 1 presents the ASR, CR, and Acc. across all evaluation benchmarks and models; due to space limitations, we report feature ablation results in Appendix B.1 . Our fail-closed alignment method is the most robust to prompt-based jailbreaks , achieving \leq 4% ASR in all cases and reducing average ASR by 92.3–97.2%, compared to 23.8–93.7% for the baselines. Our method is particularly effective against the black-box attack PAIR, consistently yielding the lowest ASR and being the only defense for which PAIR fails to achieve an ASR \geq 17.5%. Furthermore, we attain the lowest average ASR and standard deviation across all models, indicating strong generalization across attack types, initial model alignment, and parameter scales. These results indicate that enforcing structural redundancy rather than attack-specific training is a promising paradigm for improving robustness against prompt-based jailbreaks. Our method incurs minimal degradation in overrefusal and utility. For overrefusal, we achieve the best or second-best CR on all models, with the highest average (86.4%) compared to 68.8–75.7% for baselines, suggesting our models distinguish truly harmful from seemingly harmful inputs. For utility, we achieve 61.6% average Acc., outperforming all baselines but CAT (62.0%)—a drop of just 0.8%.

### G08.3

**Expected:** Highest compliance on benign prompts among robust methods (86% on average).

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2602.16977v1_c0003

> `2602.16977v1_c0003` · Fail-Closed Alignment for Large Language Models · introduction
>
> Details on the prompts, prompt-based jailbreaks, and ASR calculation are provided in § 4.1 . We evaluate against four prompt-based jailbreaks across four models. Our method achieves the strongest overall robustness, reducing attack success rates by 92–97% and outperforming all baselines on both white- and black-box attacks. These gains come without sacrificing utility: we achieve the highest compliance rates on benign prompts among robust methods (86% on average) while preserving generation quality. Fail-closed alignment also generalizes to parameter-efficient settings: LoRA fine-tuning with \sim 5% of parameters matches the performance of full fine-tuning. Furthermore, our mechanistic analysis confirms that trained models learn multiple causally independent refusal directions that jailbreaks cannot suppress simultaneously. Our results demonstrate that alignment robustness depends not only on the training data or objectives, but also on how safety is structurally organized in the representation space. By enforcing redundancy by construction, fail-closed alignment provides a principled foundation for LLMs whose safety is not merely learned, but architecturally preserved.

### G08.4

**Expected:** 61.6% average accuracy versus 62.0% for CAT, with only a small constant-factor overhead over standard fine-tuning. The gap may be given as the calculated 0.4 percentage points (about 0.65% relative) or as the paper's reported "0.8%" attributed to the paper; presenting 0.8 as the calculated percentage-point gap scores 0.5.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2602.16977v1_c0020

> `2602.16977v1_c0020` · Fail-Closed Alignment for Large Language Models · evaluation
>
> For utility, we achieve 61.6% average Acc., outperforming all baselines but CAT (62.0%)—a drop of just 0.8%. Thus, increased robustness does not compromise output quality. Finally, our method’s effectiveness does not come at a high computational cost , requiring only a small constant-factor overhead over standard fine-tuning (see Appendix C ).

### G08.5

**Expected:** Tested on four open instruction-tuned models of 2–9B parameters: Llama2-7B, Llama3-8B, Gemma2-2B and Gemma2-9B.

*in skip-fit packet: yes; in top-8 packet: no*

**Anchor:** 2602.16977v1_c0018

> `2602.16977v1_c0018` · Fail-Closed Alignment for Large Language Models · evaluation
>
> We report the average zero-shot accuracy (Acc.) . Refusal-trained models are also known to overrefuse benign prompts ( Röttger et al., 2024 ; Cui et al., 2025 ) . To measure this, we generate responses to 50 XSTest prompts and 1000 Alpaca prompts (all disjoint from training), and report the compliance rate (CR) —the fraction of non-refusals determined via keyword matching ( Röttger et al., 2024 ) . Models. We consider four instruction-tuned, refusal-trained models from three families: Llama2-7B ( Touvron et al., 2023 ) , Llama3-8B ( Grattafiori et al., 2024 ) , and Gemma2-2B and 9B ( Riviere et al., 2024 ) . We intentionally select models with varying parameter scales (2–9B) and alignment techniques to assess the generalizability of our method. Baselines. We evaluate our method against four baseline training-based jailbreak defenses: Augmented refusal training (RT) ( Qi et al., 2025 ) fine-tunes models on safety recovery examples —harmful prefixes followed by a refusal—to deepen safety alignment. CAT ( Xhonneux et al., 2024 ) crafts adversarial examples in the embedding space, enabling much faster adversarial training that generalizes to discrete jailbreaks. LAT ( Chao et al., 2024 ) adversarially perturbs latent activations to elicit harmful target behaviors, and then fine-tunes the model to resist these perturbations. DeepRefusal ( Xie et al., 2025 ) ablates the model’s DIM refusal direction across random layers and token positions, then trains the model to continue refusing harmful prompts. DeepRefusal also employs ablation, but only considers a single, statically computed direction.


## G09 (partially unanswerable)

**Question.** A legal-services client wants AI statute retrieval for colloquial client questions under English and EU law. How does LegalMALR work, what retrieval results did it achieve, how well does it perform on English or EU statutes, and what does it cost per query?

### G09.1

**Expected:** Multi-agent query understanding produces diverse legally grounded reformulations with iterative dense retrieval; a zero-shot commercial LLM (Qwen-Max) reranks the candidates.

*in skip-fit packet: yes; in top-8 packet: no*

**Alternative 1:** 2601.17692v1_c0004

> `2601.17692v1_c0004` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · introduction
>
> . To operationalise these insights, we develop LegalMALR , a retrieval framework that integrates a Multi-Agent Query Understanding System (MAS) with a zero-shot LLM-based reranking module (LLM Reranker) . The MAS produces diverse reformulations of the query through a set of specialised agents that rewrite, decompose, and analyse the input from complementary legal perspectives. Because these agents are instantiated with Qwen-3-4B-Instruct, their outputs exhibit inherent variability. We therefore optimise the unified MAS policy using Generalized Reinforcement Policy Optimization (GRPO) to improve its stability and to encourage reformulations that better expose statutory applicability conditions. The reformulated queries trigger iterative dense retrieval calls whose merged candidate set is then evaluated by a commercial LLM, Qwen-Max, which serves as the LLM Reranker and performs natural-language legal reasoning to determine substantive relevance. Our study focuses on Chinese statutes and Chinese-language queries, and the datasets, retrieval components, and optimisation methods are designed for this statutory and linguistic context. This work makes four main contributions. First, we introduce the CSAID dataset, a collection of 118 difficult Chinese legal queries annotated with multiple statutory labels, providing a realistic benchmark for evaluating retrieval systems under implicit and multi-issue legal reasoning settings. Second, we propose a multi-agent query understanding framework that generates diverse and complementary interpretations of a query and supports iterative retrieval. Third, we develop a GRPO-based optimisation method that improves the stability and retrieval effectiveness of the MAS policy

**Alternative 2:** 2601.17692v1_c0012

> `2601.17692v1_c0012` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · methodology
>
> LegalMALR replaces the traditional single-query dense retrieval stage with a Multi-Agent Query Understanding System (MAS) that generates multiple complementary reformulations of the input query. Each reformulation highlights a different legally plausible interpretation of the underlying scenario, allowing the system to explore a broader portion of the statute space. These reformulations are individually processed by an embedding-based retriever and a lightweight neural reranker, thereby constructing a recall-oriented candidate pool that captures statutes semantically distant from the literal query. Because LLM-generated reformulations naturally exhibit behavioural variability, we further optimise the MAS policy using GRPO to encourage stable, structured, and legally meaningful reformulation trajectories. After MAS concludes, the accumulated candidate set is evaluated by a commercial LLM (Qwen-Max) acting as a zero-shot reranker, which assesses statutory applicability based on factual alignment, element satisfaction, exception structures, and doctrinal coherence. This division between exploratory recall (MAS) and precision-oriented legal judgement (LLM Reranker) enables LegalMALR to achieve high recall without sacrificing legal reasoning quality. The overall end-to-end workflow is illustrated in Figure 3 . End-to-end processing flow of LegalMALR. MAS iteratively analyses and reformulates the query, retrieves candidate statutes, and monitors coverage to decide termination.

### G09.2

**Expected:** MAS with GRPO reached Recall@14 0.8396 and HitRate@14 0.9320 on STARD, and recall 0.7478 with HitRate@14 1.0 on CSAID.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2601.17692v1_c0041

> `2601.17692v1_c0041` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · experiments
>
> . Across both datasets, the zero-shot MAS already performs strongly, achieving Recall@14 values of 0.8012 on STARD and 0.6969 on CSAID. This places it close to Qwen3-SFT, a domain-supervised RAG baseline. These results indicate that the MAS structure by itself, through diverse reformulations and iterative exploration of the retrieval space, can surface relevant statutes that are difficult to obtain using a single-query dense retriever. Importantly, this behaviour is observed under a retrieval budget that is matched to the baselines in expectation, confirming that the improvements are not attributable to additional embedding calls. Training MAS with GRPO yields consistent and substantial gains. MAS with GRPO achieves Recall@14 of 0.8396 and HitRate@14 of 0.9320 on STARD, outperforming both the zero-shot MAS and all RAG baselines at this retrieval stage. On CSAID, which features greater implicitness and broader semantic variability, MAS with GRPO further improves recall to 0.7478 and reaches a perfect HitRate@14 of 1.0. These results are aligned with the intended effect of GRPO, which encourages the MAS policy to generate reformulations that extend recall coverage and stabilise the retrieval process. The contrast between zero-shot MAS and GRPO-trained MAS demonstrates that the MAS framework provides the structural flexibility required for multi-step retrieval, while GRPO supplies the optimisation signal that enables MAS to use this structure effectively. The more complete and higher-quality candidate sets produced by MAS with GRPO directly explain the improvements observed in the end-to-end evaluation in Section 4.2

### G09.3

**Expected:** English/EU performance is not established: the framework was developed and evaluated only on Chinese statutes and Chinese-language queries.

*in skip-fit packet: yes; in top-8 packet: no*

**Alternative 1:** 2601.17692v1_c0053

> `2601.17692v1_c0053` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · discussion
>
> . The relatively small size of CSAID also limits the statistical robustness of certain analyses. Broader evaluations are needed to understand the generalisability of multi-agent retrieval systems in more varied legal settings. A further limitation is that the entire framework is developed and evaluated within a Chinese language setting. All training data, statutory corpora, MAS reformulations, and LLM reranking prompts operate exclusively on Chinese legal texts. The effectiveness of MAS-driven reformulation and GRPO optimisation therefore reflects linguistic and structural characteristics specific to Chinese statutory language. The cross-lingual robustness of LegalMALR remains unexplored, and it is unclear to what extent the current multi-agent design transfers to jurisdictions that differ in drafting conventions, logical structure, or linguistic expression. Extending the framework to multilingual or cross-jurisdictional retrieval constitutes an important direction for future research. Finally, the reward formulation used in GRPO focuses exclusively on MAS-stage recall. This metric is aligned with our objective of improving coverage, but it does not explicitly model ranking quality, interpretability of rewrite decisions, or the legal validity of intermediate reasoning steps. Future optimisation frameworks could benefit from richer feedback signals. These limitations do not undermine the empirical findings of this work but instead highlight the opportunities for further refinement and extension of the LegalMALR framework.

**Alternative 2:** 2601.17692v1_c0004

> `2601.17692v1_c0004` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · introduction
>
> . To operationalise these insights, we develop LegalMALR , a retrieval framework that integrates a Multi-Agent Query Understanding System (MAS) with a zero-shot LLM-based reranking module (LLM Reranker) . The MAS produces diverse reformulations of the query through a set of specialised agents that rewrite, decompose, and analyse the input from complementary legal perspectives. Because these agents are instantiated with Qwen-3-4B-Instruct, their outputs exhibit inherent variability. We therefore optimise the unified MAS policy using Generalized Reinforcement Policy Optimization (GRPO) to improve its stability and to encourage reformulations that better expose statutory applicability conditions. The reformulated queries trigger iterative dense retrieval calls whose merged candidate set is then evaluated by a commercial LLM, Qwen-Max, which serves as the LLM Reranker and performs natural-language legal reasoning to determine substantive relevance. Our study focuses on Chinese statutes and Chinese-language queries, and the datasets, retrieval components, and optimisation methods are designed for this statutory and linguistic context. This work makes four main contributions. First, we introduce the CSAID dataset, a collection of 118 difficult Chinese legal queries annotated with multiple statutory labels, providing a realistic benchmark for evaluating retrieval systems under implicit and multi-issue legal reasoning settings. Second, we propose a multi-agent query understanding framework that generates diverse and complementary interpretations of a query and supports iterative retrieval. Third, we develop a GRPO-based optimisation method that improves the stability and retrieval effectiveness of the MAS policy

### G09.4

**Expected:** No monetary per-query cost is reported. Answers may cite the stated computational cost proxies (1-4 retrieval rounds, 30-120 embedding calls, about 13.58 candidates passed to the commercial LLM reranker, whose per-token cost is higher than lightweight rerankers; c0035, c0048, c0052). Any monetary per-query price not supported by the study is fabricated (correction 9, Codex review).

**No anchor (monetary cost).** No passage gives a monetary per-query cost. The computational cost proxies an answer may correctly cite are quoted below for reference. A dollar or per-query price figure scores 0 and counts as a misleading claim (rules.json, evidence_absent_points). Reviewer: confirm that no passage in the 100-paper corpus gives a monetary per-query cost for LegalMALR.

> `2601.17692v1_c0035` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · experiments (cost proxy, not a required anchor)
>
> . LegalMALR consists of the MAS module and a final LLM-based reranker. The MAS policy is instantiated from Qwen3-4B-Instruct and trained with GRPO on eight NVIDIA RTX 4090 GPUs for approximately sixteen hours. The backbone model remains frozen during training and only lightweight LoRA-style adaptation layers are updated. During inference, MAS executes a single rollout with fixed temperatures (0.6 for the Planner and 0.8 for rewrite agents), ensuring deterministic behaviour aside from controlled sampling induced by temperature settings. Each MAS iteration retrieves the top 30 embedding candidates and prunes them to the top 10 using the lightweight reranker. After multiple iterations, the merged and deduplicated candidate set contains on average 13.58 statutes, which are then passed to the final reranker. Dynamic Retrieval Budget and Fairness. MAS uses an adaptive retrieval depth that terminates based on coverage signals. In practice, MAS performs between one and four retrieval rounds per query. Each round retrieves 30 dense candidates and retains 10 after lightweight reranking, resulting in 30 to 120 embedding calls. After merging, unique candidates range from 10 to 22 with an average of 13.58. To ensure budget-equivalent comparison, we define retrieval cost by the number of dense embedding calls. Baseline RAG systems issue a single retrieval returning 60 candidates. Although MAS has a higher theoretical upper bound, its empirical average cost is 60.3 embedding calls, which is effectively identical to the fixed 60-call baseline. MAS therefore differs only in allocating this budget adaptively: simple queries stop early while complex queries invoke additional reformulations

> `2601.17692v1_c0048` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · experiments (cost proxy, not a required anchor)
>
> Although LegalMALR introduces an iterative retrieval mechanism, its overall computational profile remains comparable to that of conventional RAG pipelines. Empirically, MAS triggers an average of 2.01 dense-retrieval calls per query during evaluation on the STARD and CSAID datasets, with a maximum of four retrieval calls observed in any trajectory. Retrieval calls are not equivalent to planner iterations: a single planner step may issue multiple retrievals through the Multi-Element Decomposition Agent or may issue none when producing an exit decision. In practice, however, no evaluation trajectory exceeded four retrieval calls. Each retrieval call returns the top thirty embedding candidates, which are pruned to the top ten using the lightweight reranker. This yields an average of approximately sixty embedding retrieval operations per query, a value that closely matches the standard RAG configuration that retrieves a fixed top sixty candidates once per query. The reranking cost is also well bounded. Lightweight reranking is applied only within MAS to prune intermediate candidate lists. The final large model based reranking stage processes an average of 13.58 merged and deduplicated candidate statutes rather than the full embedding set. Although the LLM reranker in LegalMALR is more capable than the lightweight rerankers used in baseline RAG systems, the substantial reduction in input size limits its token consumption and offsets the higher per-token cost of the larger model. As a result, the end-to-end reranking overhead remains practical and does not dominate total inference time

> `2601.17692v1_c0052` · LegalMALR:Multi-Agent Query Understanding and LLM-Based Reranking for Chinese Statute Retrieval · discussion (cost proxy, not a required anchor)
>
> Although LegalMALR demonstrates strong performance across multiple evaluation settings, several limitations warrant attention. First, the behaviour of MAS remains sensitive to large language model variability. The rewrite agents occasionally generate incomplete or overly specific reformulations, and the decomposition agent may either miss opportunities for structural decomposition or introduce unnecessary fragments. GRPO improves stability but cannot eliminate stochasticity entirely because the reward signal is sparse and tied only to trajectory-level recall. Second, the reliance on a powerful commercial LLM for the final reranking stage introduces additional computational cost and limits full reproducibility. While the candidate set processed by the LLM is relatively small, the per-token cost is still higher than that of lightweight rerankers. In addition, the proprietary nature of commercial LLMs restricts fine-grained control over reasoning behaviour and complicates long-term model maintenance. Third, multi-step retrieval unavoidably increases latency in complex queries. MAS mitigates this through adaptive termination, yet the worst-case number of retrieval calls is still higher than that of single-step pipelines. In real-time or high-throughput applications, this may require batching, caching, or further optimisation. Fourth, although the STARD and CSAID datasets capture diverse legal search scenarios, they do not represent the full breadth of jurisdictions, procedural contexts, or specialised domains in real-world legal practice. The relatively small size of CSAID also limits the statistical robustness of certain analyses. Broader evaluations are needed to understand the generalisability of multi-agent retrieval systems in more varied legal settings


## G10 (partially unanswerable)

**Question.** A client is piloting autonomous multi-agent LLM systems that share a common resource. What did the study 'Is Lying an Emergent Behaviour in LLMs?' find about agents lying and its effects, and how often do deployed commercial AI agents lie to customers?

### G10.1

**Expected:** Setting: an agent-based sustainability game in which agents are told resources regenerate although they do not; agents can observe neighbours, declare attacks, be permitted to lie and see reputation.

*in skip-fit packet: yes; in top-8 packet: yes*

**Anchor:** 2606.28456v1_c0000

> `2606.28456v1_c0000` · Is Lying an Emergent Behaviour in LLMs? Evidence from Gaslighting AI agents in a Sustainability Game · abstract
>
> LLMs agents are increasingly used in multi-agent settings, yet their behaviour in sustainability games remains largely unexplored. This work investigates whether lying can emerge among LLM agents in a competitive sustainability game in which agents are informed that common resources can regenerate, although regeneration does not actually occur. We develop an agent-based model of a sustainability game in which agents manage industrial, military, and ecological resources, and interact through a network. LLM agents can observe neighbours’ status, declare future attacks, receive permission to lie, and access reputation information, while rule-based agents provide an interpretable behavioural baseline. The results show that neighbour information strongly changes system dynamics, increasing attacks while improving biosphere retention and coexistence. Also, the presence of future declarations reduce extinction risk without suppressing conflict. Behaviourally, deception emerges even when agents are not explicitly allowed to lie, and explicit permission mainly increases bluffing and diversion rather than direct backstabbing. Finally, the presence of reputation memory and information about the current biosphere level reduces system ecological depletion. These findings suggest that deception can arise as an emergent behaviour in LLM-agent systems and that communication between LLM-agents could support sustainability while dealing with risk.

### G10.2

**Expected:** Agents lied in 44% of declarations even when not permitted, rising to 65% when permitted: permission amplifies an existing tendency.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2606.28456v1_c0035

> `2606.28456v1_c0035` · Is Lying an Emergent Behaviour in LLMs? Evidence from Gaslighting AI agents in a Sustainability Game · results
>
> Across declaration-enabled runs, we matched every stated next-turn intention against the agent’s actual action in the subsequent turn. Deception emerged spontaneously rather than being explicitly permitted. Even when agents were not permitted to lie ( l=0 ), a substantial share of declarations were already dishonest, with a lie rate of 44%. Allowing deception explicitly ( l=1 ), further increased these rates to 65%. Therefore, permission amplifies an existing tendency toward deception rather than creating it. This pattern is large, consistent across initial biosphere levels ( b_{0}={6000,8000,10000} ), and robust across replications. We categorized the declarations into honest peace (keeping a stated intent not to attack), honest threat (attacked exactly the announced target), bluff (declaring an attack and then not attacking), diversion (declaring one target while attacking another), and backstab (explicitly signalling peaceful intent and then attacking) (Table 4 ). The structure of deception is equally notable (Fig. 6 ). Dishonesty is dominated by bluffing and diversion. However, backstabbing remains rare under all conditions, accounting for only about 0.4%–2% of declarations. The increase in deception produced by explicitly permitting lying ( l=1 ) operates almost entirely through diversion, which doubles (from 17% to 34%), while bluffing rises more modestly. In contrast, backstabbing shows little response to the permission treatment. Memory of neighbors ( m=1 ) leaves overall deception rates largely unchanged. Taken together, these results suggest that LLM agents may misrepresent their intentions even without explicit incentives to deceive. However, they tend to use evasive or misleading communication rather than directly breaking their stated peaceful commitments

### G10.3

**Expected:** Declarations cut extinction from 40% to 7% and raised coexistence from 60% to 88%.

*in skip-fit packet: no; in top-8 packet: no*

**Anchor:** 2606.28456v1_c0031

> `2606.28456v1_c0031` · Is Lying an Emergent Behaviour in LLMs? Evidence from Gaslighting AI agents in a Sustainability Game · results
>
> With neighbour information fixed on, we next isolate the cheap-talk channel itself by comparing the no-declaration regime (R5) with the regimes in which future declarations are active (R1–R4). Opening the declaration channel changes the macro-dynamics markedly (Fig. 3 ). The fraction of runs ending in extinction falls from 40\% without declarations to 7\% with them, while coexistence rises from 60\% to 88\% and domination appears in a small share of runs ( 5\% ), so that the population is far more likely to survive to the end of the horizon (Fig. 4 ). The biosphere retained at the final step, b_{t_{f}} , increases accordingly from 26.2\% to 42.3\% of the initial brown stock, b_{0} . This gain in collective survival is not bought with peace: the per-agent survival rate drops sharply, from 0.65 to 0.35 , and the total number of attacks edges up rather than down, from 303 to 334 per run. Allowing agents to announce their intentions, therefore, does not pacify the population; it organises the conflict, concentrating attacks in a way that eliminates many individual agents while leaving a surviving core on a substantially better-preserved biosphere. The declaration channel thus behaves less as a coordination device that suppresses conflict and more as one that restructures it. Effect of future declarations on system dynamics. Comparison of runs with future declarations disabled (R5) and enabled (R1–R4), with neighbors information active I = True. Enabling declarations lowers extinction and raises coexistence and biosphere retention, while the per-agent survival rate falls and the total number of attacks rises slightly. Bars show means with error bars across runs. Distribution of terminal outcomes under different communication settings

### G10.4

**Expected:** Two components, both required for 1 (one alone scores 0.5): (a) deployed commercial agents' lying rates are not established by the study; (b) because it is a simplified simulation (identical agents, fixed network), not a real-world deployment. A stated real-world lying rate scores 0 and counts as a misleading claim.

*in skip-fit packet: yes; in top-8 packet: yes*

**Alternative 1:** 2606.28456v1_c0045

> `2606.28456v1_c0045` · Is Lying an Emergent Behaviour in LLMs? Evidence from Gaslighting AI agents in a Sustainability Game · discussions
>
> Although our framework provides new insights into communication, deception, and reputation in LLM-based sustainability games, several limitations remain, pointing to promising directions for future research. First, the proposed framework considers a simplified setting in which agents share identical initial conditions and interact through a fixed network structure. While useful, this is an obvious limitation, given that the results should be validated in different settings Galán et al. (2009) . Second, LLM-agent behaviour is generated through prompting rather than learning, making the observed dynamics dependent on the underlying language model and prompting strategy. The prompt is not updated either intra- or inter-simulation. Since adaptive multi-agent systems are progressively more relevant, this is a limitation for policy-makers and practitioners. Third, agents follow fixed decision policies throughout each simulation, whereas real social systems continuously adapt their behaviour in response to changing conditions and the observed success of others.

**Alternative 2:** 2606.28456v1_c0002

> `2606.28456v1_c0002` · Is Lying an Emergent Behaviour in LLMs? Evidence from Gaslighting AI agents in a Sustainability Game · introduction
>
> . (2024) ; Willis et al. (2026) ; Lynch et al. (2025) ; Sodano et al. (2026) ? This paper addresses this issue in a specific context: when LLMs face sustainability issues and can compete with each other, is lying an emergent behavior? And, if so, is it possible to assess its effect on the overall sustainability of the system when misleading information is present? This question connects recent work on LLM deception with the literature on collective action and common-pool resource dilemmas Ostrom (1990) . Several studies show that LLM agents may misrepresent intentions or strategically deceive other agents even without being directly instructed to do so ( Taylor and Bergen, 2025 ; Scheurer et al., 2024 ) . Other works suggest that deception becomes especially relevant in long-horizon interaction, where statements, actions, and trust evolve over time rather than being evaluated in isolated one-shot exchanges ( Xu et al., 2026 ; Curvo, 2025 ) . In sustainability settings, this is particularly important because communication may support coordination, but it may also create opportunities for manipulation, false commitments, and strategic exploitation. Consequently, the question could be studied in two ways. One would be to observe autonomous LLM agents acting in a real-world sustainability-related system. At present, however, this would be impractical and potentially unsafe, because autonomous LLMs should not be placed in control of high-stakes real-world systems without careful safeguards Lynch et al. (2025) . We therefore adopt a second approach: a minimal and controlled game environment in which decisions are explicit, outcomes are observable, and external confounders are limited Batterman and Rice (2014)


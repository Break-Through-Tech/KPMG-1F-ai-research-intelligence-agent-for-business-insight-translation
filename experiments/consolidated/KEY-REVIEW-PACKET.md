# fresh-v2 answer key: focused independent review packet

One review round only. For each point check: (1) the anchor passage(s) state the expected answer with no number, subject, metric, condition or qualifier changed; (2) the question asks for it; (3) the scoring rule is fair. Flag only substantive factual or scoring errors. Interpretation and borderline-credit questions go to AMBIGUITIES.md for consistent adjudication after scoring, not to another review round.

**Corrected in the pre-review source check (resealed once):** H03.4 re-anchored to c0003, which states the pre-/post-generation design; H08.2 keeps the source qualifier "mixed" for medical models; H05.4 made an explicit two-component point. **Then corrected after the one focused AI-assisted review (ChatGPT; resealed once):** H01.1 separates the 50,000+ benchmark conversations from the 2,345 evaluation samples; H06.1 alternative = c0008 + c0007; H06.2 anchors all nine type rows plus the total; every alternative must support every component. See KEY-REVIEW-RECORD.md.

Scoring rules: `fresh-v2/rules.json`. Known ambiguities: `AMBIGUITIES.md`.

---

## H01 (single-paper)

**Question.** A Japanese hospital group is evaluating LLM chat assistants for patient conversations. What did JMedEthicBench test, how did commercial and medical-specialised models hold up, how did safety change over the course of a conversation, and did the weaknesses persist in English?

### H01.1

**Expected:** The benchmark is grounded in 67 Japan Medical Association guidelines and has over 50,000 adversarial conversations generated with seven automatically discovered jailbreak strategies; the 22 models were evaluated on a sample of 2,345 three-turn conversations (5 per strategy and JMA principle). Saying the 22 models were evaluated on the 50,000+ conversations conflates the two and scores at most 0.5.

**Anchor:** 2601.01627v3_c0000 + 2601.01627v3_c0009 (read together)

> `2601.01627v3_c0000` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · abstract
>
> As Large Language Models (LLMs) are increasingly deployed in healthcare worldwide, robustness against adversarial jailbreaking becomes essential for maintaining medical ethics compliance, calling for comprehensive adversarial benchmarks. However, existing benchmarks remain predominantly English-centric and limited to single-turn attacks. To address these gaps, we introduce JMedEthicBench, the first multi-turn adversarial benchmark for evaluating medical ethics alignment of LLMs in Japanese. Grounded in 67 guidelines from the Japan Medical Association, our benchmark comprises over 50,000 adversarial conversations generated using seven automatically discovered jailbreak strategies. Through a dual-LLM scoring protocol, we evaluate 22 models and find that commercial models maintain strong resistance to attacks while medical-specialized models exhibit increased vulnerability. Furthermore, safety scores decline significantly across conversation turns (median: 9.5 to 5.5, p<0.001 ), demonstrating that multi-turn escalation systematically circumvents defense mechanisms. Cross-lingual evaluation reveals that medical model vulnerabilities persist across Japanese and English, indicating inherent alignment limitations rather than language-specific factors. Our findings suggest that domain-specific fine-tuning may inadvertently weaken safety alignment and that multi-turn jailbreak attacks represent a distinct threat surface requiring dedicated defense strategies.

> `2601.01627v3_c0009` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · experiments
>
> We randomly selected 5 multi-turn conversation samples (3 turns each) for every jailbreak strategy and JMA principle combination, yielding 2,345 data points. All samples underwent quality review by medical professionals, confirming their validity. The 3-turn restriction was chosen for two reasons: (1) most conversations (74.31%) in our dataset naturally concluded or reached their adversarial goal within 3 turns, and (2) restricting to 3 turns enables fair comparison across strategies and principles while managing evaluation costs. We acknowledge that longer conversations (5–7 turns) were not evaluated, and future work should investigate whether degradation trends differ for extended multi-turn interactions, particularly for commercial versus medical models. Each model was prompted turn by turn, with a Scorer LLM evaluating each response. We evaluate a diverse set of state-of-the-art LLMs across three categories. For commercial LLMs, we evaluate Claude (3.5-Haiku, Sonnet-4, and Opus-4.1), Gemini (2.5-Flash and 2.5-Pro) ( Comanici et al., 2025 ) , GPT-5 (full and mini) ( OpenAI, 2025 ) , and Grok-4 ( xAI, 2025 ) . For general open-source LLMs, we evaluate GPT-OSS (20b and 120b) ( OpenAI et al., 2025 ) , Qwen3 (8b, 30b-a3b, 32b, and 235b-a22b-2507) ( Yang et al., 2025 ) , Kimi-K2 ( Team et al., 2025 ) , and GLM-4.5 ( Zeng et al., 2025 ) . For medical LLMs, we evaluate MedGemma (4b-it and 27b-it) ( Sellergren et al., 2025 ) , HuatuoGPT-o1 (7B and 72B) ( Chen et al., 2025 ) , and II-Medical (8B and 32B-Preview) ( Internet, 2025 ) . To comprehensively assess model capabilities, we also evaluate helpfulness using 287 questions from the Japanese National Medical Licensing Examination 2025 ( Liu et al., 2025a )

### H01.2

**Expected:** Leading commercial models (e.g. Claude Opus 4.1, GPT-5) maintained robust alignment, while medical-specialised models were more vulnerable than general-purpose models.

**Anchor:** 2601.01627v3_c0019

> `2601.01627v3_c0019` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · conclusion
>
> We presented JMedEthicBench, the first multi-turn adversarial benchmark for evaluating medical ethics alignment of LLMs in Japanese, comprising over 50,000 conversation instances grounded in 67 JMA guidelines. Our comprehensive evaluation of 22 models revealed that safety boundaries erode significantly as conversations progress, even though leading commercial models such as Claude Opus 4.1 and GPT-5 maintain robust alignment. Moreover, medical-specialized models exhibit increased vulnerability compared to general-purpose models, suggesting that domain adaptation may inadvertently affect safety alignment. Notably, cross-lingual evaluation of six medical models showed that these safety deficiencies persist, and are often amplified, in English, pointing to limitations in model alignment itself rather than language-specific factors. Together, these results highlight the need for safety-aware training strategies during domain adaptation and for multi-turn robustness testing as a standard component of medical AI evaluation. We will publicly release the full dataset and evaluation code to support reproducible research on medical AI safety.

### H01.3

**Expected:** The median safety score fell from about 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2; all pairwise turn comparisons were significant (p<0.001). The abstract summary "9.5 to 5.5" also scores.

**Alternative 1:** 2601.01627v3_c0013

> `2601.01627v3_c0013` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · experimental results
>
> Distribution across conversation turns. *** denotes p<0.001 (Mann-Whitney U test with Bonferroni correction). Figure 4(a) illustrates the progressive erosion of safety boundaries across conversation turns. The median safety score decreases from approximately 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2. All pairwise comparisons between turns are statistically significant ( p<0.001 , Mann-Whitney U test with Bonferroni correction), with a medium effect size for Turn 0 \to 1 (Cohen’s d=0.75 ) and a small effect size for Turn 1 \to 2 ( d=0.24 ). This confirms that multi-turn interactions represent a qualitatively different threat surface than single-turn prompts. These findings extend prior observations from multi-turn adversarial research. While STREAM ( Kuo et al., 2025 ) and MTSA ( Guo et al., 2025 ) demonstrate that multi-turn attacks can circumvent safety mechanisms in general-domain settings, our results show that this degradation is substantially more pronounced in the medical domain, particularly for medical-specialized models, where safety scores drop below 4.0 by the third turn. This suggests that domain-specific fine-tuning may create additional vulnerability surfaces that general-domain multi-turn defenses do not address.

**Alternative 2:** 2601.01627v3_c0000

> `2601.01627v3_c0000` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · abstract
>
> As Large Language Models (LLMs) are increasingly deployed in healthcare worldwide, robustness against adversarial jailbreaking becomes essential for maintaining medical ethics compliance, calling for comprehensive adversarial benchmarks. However, existing benchmarks remain predominantly English-centric and limited to single-turn attacks. To address these gaps, we introduce JMedEthicBench, the first multi-turn adversarial benchmark for evaluating medical ethics alignment of LLMs in Japanese. Grounded in 67 guidelines from the Japan Medical Association, our benchmark comprises over 50,000 adversarial conversations generated using seven automatically discovered jailbreak strategies. Through a dual-LLM scoring protocol, we evaluate 22 models and find that commercial models maintain strong resistance to attacks while medical-specialized models exhibit increased vulnerability. Furthermore, safety scores decline significantly across conversation turns (median: 9.5 to 5.5, p<0.001 ), demonstrating that multi-turn escalation systematically circumvents defense mechanisms. Cross-lingual evaluation reveals that medical model vulnerabilities persist across Japanese and English, indicating inherent alignment limitations rather than language-specific factors. Our findings suggest that domain-specific fine-tuning may inadvertently weaken safety alignment and that multi-turn jailbreak attacks represent a distinct threat surface requiring dedicated defense strategies.

### H01.4

**Expected:** In a cross-lingual evaluation of six medical models, the safety deficiencies persisted and were often amplified in English, pointing to alignment limitations rather than language-specific factors.

**Anchor:** 2601.01627v3_c0019

> `2601.01627v3_c0019` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · conclusion
>
> We presented JMedEthicBench, the first multi-turn adversarial benchmark for evaluating medical ethics alignment of LLMs in Japanese, comprising over 50,000 conversation instances grounded in 67 JMA guidelines. Our comprehensive evaluation of 22 models revealed that safety boundaries erode significantly as conversations progress, even though leading commercial models such as Claude Opus 4.1 and GPT-5 maintain robust alignment. Moreover, medical-specialized models exhibit increased vulnerability compared to general-purpose models, suggesting that domain adaptation may inadvertently affect safety alignment. Notably, cross-lingual evaluation of six medical models showed that these safety deficiencies persist, and are often amplified, in English, pointing to limitations in model alignment itself rather than language-specific factors. Together, these results highlight the need for safety-aware training strategies during domain adaptation and for multi-turn robustness testing as a standard component of medical AI evaluation. We will publicly release the full dataset and evaluation code to support reproducible research on medical AI safety.

### H01.5

**Expected:** Limitation: conversations were three turns; longer conversations (5-7 turns) were not evaluated.

**Anchor:** 2601.01627v3_c0009

> `2601.01627v3_c0009` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · experiments
>
> We randomly selected 5 multi-turn conversation samples (3 turns each) for every jailbreak strategy and JMA principle combination, yielding 2,345 data points. All samples underwent quality review by medical professionals, confirming their validity. The 3-turn restriction was chosen for two reasons: (1) most conversations (74.31%) in our dataset naturally concluded or reached their adversarial goal within 3 turns, and (2) restricting to 3 turns enables fair comparison across strategies and principles while managing evaluation costs. We acknowledge that longer conversations (5–7 turns) were not evaluated, and future work should investigate whether degradation trends differ for extended multi-turn interactions, particularly for commercial versus medical models. Each model was prompted turn by turn, with a Scorer LLM evaluating each response. We evaluate a diverse set of state-of-the-art LLMs across three categories. For commercial LLMs, we evaluate Claude (3.5-Haiku, Sonnet-4, and Opus-4.1), Gemini (2.5-Flash and 2.5-Pro) ( Comanici et al., 2025 ) , GPT-5 (full and mini) ( OpenAI, 2025 ) , and Grok-4 ( xAI, 2025 ) . For general open-source LLMs, we evaluate GPT-OSS (20b and 120b) ( OpenAI et al., 2025 ) , Qwen3 (8b, 30b-a3b, 32b, and 235b-a22b-2507) ( Yang et al., 2025 ) , Kimi-K2 ( Team et al., 2025 ) , and GLM-4.5 ( Zeng et al., 2025 ) . For medical LLMs, we evaluate MedGemma (4b-it and 27b-it) ( Sellergren et al., 2025 ) , HuatuoGPT-o1 (7B and 72B) ( Chen et al., 2025 ) , and II-Medical (8B and 32B-Preview) ( Internet, 2025 ) . To comprehensively assess model capabilities, we also evaluate helpfulness using 287 questions from the Japanese National Medical Licensing Examination 2025 ( Liu et al., 2025a )

---

## H02 (numerical/table)

**Question.** A healthcare client wants a small model aligned to medical ethics. In the MedES study, how did the aligned 7B model compare with the 671B DeepSeek-R1 on the subjective ethics test (risk rate, quality and comprehensive score) and on objective knowledge, drug-safety and emergency-care accuracy, and where does the evidence apply?

### H02.1

**Expected:** After five SFT rounds, deepseek-r1-7b scored risk rate 0.0320, quality 0.9924 and comprehensive 0.9356, versus deepseek-r1-671b at 0.0338, 0.8736 and 0.8103 (subjective test set, Table 2).

**Anchor:** 2601.07954v1_table_b4a66ab450587176_5 + 2601.07954v1_table_b4a66ab450587176_7 (read together)

> `2601.07954v1_table_b4a66ab450587176_5` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · Results and Analysis
>
> Derived source table row (HTML cell serialization, not verbatim prose). A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356

> `2601.07954v1_table_b4a66ab450587176_7` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · Results and Analysis
>
> Derived source table row (HTML cell serialization, not verbatim prose). A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103

### H02.2

**Expected:** The authors summarise this as the 7B model surpassing a 671B commercial LLM by over 10% in composite ethical performance, with consistent gains over five SFT rounds.

**Alternative 1:** 2601.07954v1_c0019

> `2601.07954v1_c0019` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · conclusion
>
> We introduce a structured benchmark and alignment framework to advance ethical and safe behavior in medical LLMs. Our proposed MedES benchmark targets high-impact clinical scenarios, grounded in real-world ethical and regulatory sources. Built on this, our Guardian-in-the-Loop framework enables iterative supervised fine-tuning guided by multi-dimensional evaluator feedback. Empirically, our 7B model shows consistent gains over five SFT rounds, ultimately surpassing a 671B commercial LLM by over 10% in composite ethical performance. This highlights the strength of structured alignment over scale alone. However, plateauing gains and knowledge gaps in objective tasks suggest that retrieval-based methods may offer complementary benefits in future work. Our findings underscore the importance of fine-grained supervision and targeted iteration for aligning medical LLMs with human ethical expectations—paving the way for safer, more trustworthy clinical AI.

**Alternative 2:** 2601.07954v1_c0004

> `2601.07954v1_c0004` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · introduction
>
> . To validate the effectiveness of our pipeline, we conduct extensive experiments using both open-source and commercial foundation models under a supervised fine-tuning (SFT) ( Ouyang et al. 2022 ) setting. Our results demonstrate that SFT, when guided by a structured evaluator-in-the-loop process, can significantly improve ethical reliability—particularly in high-risk or ambiguous clinical scenarios—by instilling domain-specific knowledge and ethical reasoning capabilities. An overview of our framework is shown in Figure 1 . Our main contributions are: MedES Benchmark: A scenario-centric benchmark built from real-world sources, targeting both ethical and safety risks in clinical practice. Guardian-in-the-Loop Framework: An iterative alignment pipeline that incorporates accurate, structured evaluator feedback for model optimization. Empirical Gains: Our aligned 7B model outperforms a 671B commercial LLM, improving composite scores by over 10% on high-risk ethical tasks.

### H02.3

**Expected:** On objective tasks the round-5 7B model scored 43.1 (ethical knowledge), 52.8 (drug safety) and 61.6 (emergency care) accuracy versus 60.2, 88.4 and 89.1 for deepseek-r1-671b: it lags on objective knowledge.

**Anchor:** 2601.07954v1_table_02ce7ccc29e736d1_5 + 2601.07954v1_table_02ce7ccc29e736d1_8 (read together)

> `2601.07954v1_table_02ce7ccc29e736d1_5` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · Results and Analysis
>
> Derived source table row (HTML cell serialization, not verbatim prose). A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6

> `2601.07954v1_table_02ce7ccc29e736d1_8` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · Results and Analysis
>
> Derived source table row (HTML cell serialization, not verbatim prose). A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1

### H02.4

**Expected:** A retrieval-augmented 7B variant scored 58.6 / 82.4 / 91.2; the authors note plateauing gains and knowledge gaps in objective tasks and suggest retrieval-based methods may complement fine-tuning.

**Anchor:** 2601.07954v1_table_02ce7ccc29e736d1_6 + 2601.07954v1_c0019 (read together)

> `2601.07954v1_table_02ce7ccc29e736d1_6` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · Results and Analysis
>
> Derived source table row (HTML cell serialization, not verbatim prose). A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-rag; Type: Ours; EK Acc: 58.6; DS Acc: 82.4; EC Acc: 91.2

> `2601.07954v1_c0019` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · conclusion
>
> We introduce a structured benchmark and alignment framework to advance ethical and safe behavior in medical LLMs. Our proposed MedES benchmark targets high-impact clinical scenarios, grounded in real-world ethical and regulatory sources. Built on this, our Guardian-in-the-Loop framework enables iterative supervised fine-tuning guided by multi-dimensional evaluator feedback. Empirically, our 7B model shows consistent gains over five SFT rounds, ultimately surpassing a 671B commercial LLM by over 10% in composite ethical performance. This highlights the strength of structured alignment over scale alone. However, plateauing gains and knowledge gaps in objective tasks suggest that retrieval-based methods may offer complementary benefits in future work. Our findings underscore the importance of fine-grained supervision and targeted iteration for aligning medical LLMs with human ethical expectations—paving the way for safer, more trustworthy clinical AI.

### H02.5

**Expected:** Scope: experiments were conducted entirely within the Chinese medical ethics context, and the benchmark and results are not intended for clinical decision-making or patient-facing use.

**Anchor:** 2601.07954v1_c0000 + 2601.07954v1_c0020 (read together)

> `2601.07954v1_c0000` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · abstract
>
> Recent advances in large language models (LLMs) have enabled their application to a range of healthcare tasks. However, aligning LLMs with the nuanced demands of medical ethics, especially under complex real-world scenarios, remains underexplored. In this work, we present MedES , a dynamic, scenario-centric benchmark specifically constructed from 260 authoritative Chinese medical, ethical, and legal sources to reflect the challenges in clinical decision-making. To facilitate model alignment, we introduce a guardian-in-the-loop framework that leverages a dedicated automated evaluator—trained on expert-labeled data and achieving over 97% accuracy within our domain—to generate targeted prompts and provide structured ethical feedback. Using this pipeline, we align a 7B-parameter LLM through supervised fine-tuning and domain-specific preference optimization. Experimental results, conducted entirely within the Chinese medical ethics context, demonstrate that our aligned model outperforms notably larger baselines on core ethical tasks, with observed improvements in both quality and composite evaluation metrics. Our work offers a practical and adaptable framework for aligning LLMs with medical ethics in the Chinese healthcare domain, and suggests that similar alignment pipelines may be instantiated in other legal and cultural environments through modular replacement of the underlying normative corpus.

> `2601.07954v1_c0020` · A Human-Centric Pipeline for Aligning Large Language Models with Chinese Medical Ethics · ethical statement
>
> We followed established best practices to ensure responsible data collection, participant protection, and safe evaluation of medical large language models: Annotator Recruitment and Training: Six undergraduate annotators (ages 18–20; gender-balanced) were recruited with foundational training in medicine and ethics. All annotators provided informed consent prior to participation and were compensated at a fair rate (RMB 45 per \sim 2.5-hour session, covering 60 samples per session). Data Privacy and Safety: All source materials were anonymized and verified to contain no private patient data or personally identifiable information. Sensitive clinical cases were excluded from the dataset. Risk Mitigation in Human–AI Interaction: To minimize potential exposure to harmful or unethical model outputs, all prompts and generated responses for annotation underwent a pre-screening process by the research team. Intended Use and Limitations: The benchmark and evaluation results are intended solely for academic research focused on improving ethical alignment and safety in medical large language models. They are not to be used directly in clinical decision-making or any patient-facing application. Ethical Alignment Evaluation: We included explicit evaluation of model outputs for ethical compliance (e.g., medical safety, fairness, and respect for patient autonomy). Such metrics are used to identify risks and guide further safety improvements, rather than to certify clinical readiness.

---

## H03 (cross-paper)

**Question.** A bank's AI security team wants to understand automated jailbreak tooling. What do HarmNet and AutoJailbreak show about how automated attacks are built, how successful they were, and which defence held up?

### H03.1

**Expected:** HarmNet is a modular multi-turn attack framework: ThoughtNet (a hierarchical semantic network), a feedback-driven Simulator for iterative query refinement, and a Network Traverser for adaptive execution.

**Alternative 1:** 2510.18728v1_c0002

> `2510.18728v1_c0002` · HarmNet: A Framework for Adaptive Multi-Turn Jailbreak Attacks on Large Language Models · introduction
>
> . To address these limitations, we introduce HarmNet , a modular, LLM-agnostic framework that systematically constructs, refines, and executes multi-turn jailbreak queries. HarmNet comprises (1) ThoughtNet , a hierarchical semantic network for comprehensive adversarial space exploration; (2) a feedback-driven Simulator for iterative query refinement based on harmfulness and semantic alignment; and (3) a Network Traverser for real-time adaptive attack execution. In our experiments on the HarmBench benchmark [ 26 ] , HarmNet achieves a 94.8% attack success rate on GPT-4o—10.3% higher than the best prior method—and 91.5% on GPT-3.5 Turbo. It also obtains 98.4% on LLaMA-3-8B [ 23 ] and 99.4% on Mistral-7B [ 24 ] , demonstrating its robustness across both closed-source and open-source LLMs. Attack Success Rate (ASR, %) across Closed-Source and Open-Source LLMs

**Alternative 2:** 2510.18728v1_c0000

> `2510.18728v1_c0000` · HarmNet: A Framework for Adaptive Multi-Turn Jailbreak Attacks on Large Language Models · abstract
>
> Large Language Models (LLMs) remain vulnerable to multi-turn jailbreak attacks . We introduce HarmNet , a modular framework comprising ThoughtNet , a hierarchical semantic network; a feedback-driven Simulator for iterative query refinement; and a Network Traverser for real-time adaptive attack execution. HarmNet systematically explores and refines the adversarial space to uncover stealthy, high-success attack paths . Experiments across closed-source and open-source LLMs demonstrate that HarmNet outperforms state-of-the-art methods, achieving significantly higher attack success rates . For example, on Mistral-7B, HarmNet achieves a 99.4% attack success rate —13.9% higher than the best baseline.

### H03.2

**Expected:** Two components, both required for 1 (one alone 0.5): (a) closed-source ASR 91.5% GPT-3.5-Turbo, 94.8% GPT-4o, 68.6% Claude 3.5 Sonnet; (b) open-source 98.4% LLaMA-3-8B, 99.4% Mistral-7B, 99.6% Gemma-2-9B (HarmBench). Figures must stay attributed to the right model.

**Anchor:** 2510.18728v1_c0008

> `2510.18728v1_c0008` · HarmNet: A Framework for Adaptive Multi-Turn Jailbreak Attacks on Large Language Models · experiments
>
> Table I reports Attack Success Rates (ASR) across six target models. On closed-source models, HarmNet achieves 91.5% on GPT-3.5-Turbo and 94.8% on GPT-4o, surpassing ActorAttack by 5.0 and 10.3 percentage points respectively. On Claude 3.5 Sonnet, it attains 68.6%, a 2.1-point gain over the next best. In the open-source setting, HarmNet markedly outperforms all baselines: 98.4% on LLaMA-3-8B (vs. 79.0% ActorAttack), 99.4% on Mistral-7B (vs. 85.5%), and 99.6% on Gemma-2-9B (vs. 83.3%). These improvements demonstrate that HarmNet’s structured exploration and feedback-driven refinement yield consistent, substantial gains over both heuristic and learning-based multi-turn attacks.

### H03.3

**Expected:** AutoJailbreak's Ensemble Attack-GA exceeded 90% jailbreak rate on four LLMs and reached 99% on Vicuna, Qwen and Mistral.

**Anchor:** 2406.03805v1_c0022

> `2406.03805v1_c0022` · AutoJailbreak: Exploring Jailbreak Attacks and Defenses through a Dependency Lens · experiment
>
> . In AutoDAN-GA , the victim LLM is set as LLaMa-2 to generate the set of jailbreak prompts for conducting transferable attacks on other LLMs. For GPTFuzzer , the seed selection method is set as UCB ( Auer et al., 2002 ) , and three malicious templates are randomly selected from Liu et al. (2023b) to maintain consistency in the initialization strategy between GPTFuzzer and Ensemble Attack-GA . Our observations based on this setting reveal the following: i). Ensemble Attack-GA demonstrates remarkable capabilities within the GA framework, achieving a JR exceeding 90% in four LLMs. Notably, for Vicuna, Qwen, and Mistral, which are acknowledged for their limited alignment with values, the JR of Ensemble Attack-GA reaches 99%. ii). Additionally, Ensemble Attack-GA exhibits a slightly lower HR compared to other baseline methods. This underscores the efficacy of incorporating semantic features in the seed selection and mutation stages of the GA framework, thus preventing GA from deviating from the initial malicious behavior throughout the process. Comparison on our AutoDefense and baseline defenses with our two ensemble attacks. JR (%) / HR (%) / AR (%) are given on different target models. Efficiency of AutoDefense against Ensemble Attacks We next evaluate the proposed AutoDefense on AutoAttack to demonstrate its robustness. For the baselines we select the respective construction of defense experts as our baselines, including spell-check, Monto-Carlo sampling, intention analysis and summarize. Table 3 shows the results and we make three observations. i). AutoDefense demonstrates superior robustness to AutoAttack on almost all LLMs

### H03.4

**Expected:** AutoDefense, a mixture-of-defenders ensemble of pre-generation and post-generation defences, showed superior robustness to AutoAttack on almost all LLMs, in a black-box setting.

**Anchor:** 2406.03805v1_c0003 + 2406.03805v1_c0023 (read together)

> `2406.03805v1_c0003` · AutoJailbreak: Exploring Jailbreak Attacks and Defenses through a Dependency Lens · introduction
>
> . We categorize these defenses into two groups: those defending against adversarial suffixes and those defending against malicious semantics. Building upon this analysis, we propose the Ensemble Defense that integrates pre-generation and post-generation defenses, leveraging the mixture-of-defenders mechanism to resist various carefully crafted jailbreak prompts. AutoEvaluation : We firstly systematically evaluate an often-overlooked issue in jailbreak attacks: LLMs frequently provide off-topic responses instead of directly answering the attacker’s jailbreak prompts. We argue that such responses do not indicate successful value alignment of the LLM. We also analyze the consistency with human evaluation for three mainstream jailbreak evaluation methods: keywords matching, classifier-based, and LLM-as-a-Judge, and identify the latter as the primary evaluation criterion for our experiment. With extensive experiments, we show that AutoJailbreak demonstrates exceptional performance in both jailbreak attacks and defenses, outperforming existing approaches. Our ensemble AutoAttack reliably break all tested models and our ensemble AutoDefense significantly enhances the jailbreak robustness of LLMs, rather than just realizing defenses against a specific type of jailbreak prompts. While we do not argue that AutoJailbreak is the ultimate jailbreak attack and defense but rather that it should become the minimal test for any new attacks and defenses.

> `2406.03805v1_c0023` · AutoJailbreak: Exploring Jailbreak Attacks and Defenses through a Dependency Lens · experiment
>
> . Table 3 shows the results and we make three observations. i). AutoDefense demonstrates superior robustness to AutoAttack on almost all LLMs. Notably, AutoDefense enhances the robustness of the victim LLM in a completely black-box scenario, enabling it to generate content consist with human values, such as refusing to answer malicious questions. ii). Although AutoDefense is sometimes slightly inferior to baseline defense methods on models such as Qwen and Mistral in the GA framework, it almost always limits the rate of successful jailbreaks to single digits. iii). We also observe that AutoDefense can significantly reduce HR. We believe this is because AutoDefense adopts a post-generation defense strategy, directly rejecting malicious requests from users instead of using indirect answers. Efficiency of AutoDefense against Static Attacks .

### H03.5

**Expected:** AutoEvaluation separates hallucinated responses from genuine jailbreaks (jailbreak, hallucination and alignment rates).

**Alternative 1:** 2406.03805v1_c0020

> `2406.03805v1_c0020` · AutoJailbreak: Exploring Jailbreak Attacks and Defenses through a Dependency Lens · experiment
>
> We consider a layered evaluation framework in AutoEvaluation . In the first evaluation stage, we employ jailbreak success rate (JR) to represent the ratio of samples with harmful information in models’ responses. In the second stage, we further look at the hallucination rate (HR) and alignment rate (AR) in the failed jailbreak instances, measuring the ratio of samples with hallucination responses (not relative to the query) and aligned responses (refuse to answer due to model alignment). Comparison on our AutoAttack of two ensemble attacks and baseline attacks. JR (%) / HR (%) / AR (%) are listed for different target models.

**Alternative 2:** 2406.03805v1_c0000

> `2406.03805v1_c0000` · AutoJailbreak: Exploring Jailbreak Attacks and Defenses through a Dependency Lens · abstract
>
> Jailbreak attacks in large language models (LLMs) entail inducing the models to generate content that breaches ethical and legal norm through the use of malicious prompts, posing a substantial threat to LLM security. Current strategies for jailbreak attack and defense often focus on optimizing locally within specific algorithmic frameworks, resulting in ineffective optimization and limited scalability. In this paper, we present a systematic analysis of the dependency relationships in jailbreak attack and defense techniques, generalizing them to all possible attack surfaces. We employ directed acyclic graphs (DAGs) to position and analyze existing jailbreak attacks, defenses, and evaluation methodologies, and propose three comprehensive, automated, and logical frameworks. AutoAttack investigates dependencies in two lines of jailbreak optimization strategies: genetic algorithm (GA)-based attacks and adversarial-generation-based attacks, respectively. We then introduce an ensemble jailbreak attack to exploit these dependencies. AutoDefense offers a mixture-of-defenders approach by leveraging the dependency relationships in pre-generative and post-generative defense strategies. AutoEvaluation introduces a novel evaluation method that distinguishes hallucinations, which are often overlooked, from jailbreak attack and defense responses. Through extensive experiments, we demonstrate that the proposed ensemble jailbreak attack and defense framework significantly outperforms existing research.

---

## H04 (cross-paper)

**Question.** A model-risk team must decide how to assure an LLM against jailbreaks: systematic testing or adversarial training. What do the jailbreak-oracle (BOA) study and the continuous adversarial training study each offer, what evidence supports them, and what are their limits or costs?

### H04.1

**Expected:** BOA formalises the jailbreak oracle problem (can a jailbreak response be generated above a likelihood threshold for a given model, prompt and decoding strategy) and solves it with breadth-first sampling followed by depth-first priority search guided by safety scores.

**Anchor:** 2506.17299v2_c0000

> `2506.17299v2_c0000` · Toward Principled LLM Safety Testing: Solving the Jailbreak Oracle Problem · abstract
>
> As large language models (LLMs) become increasingly deployed in safety-critical applications, the lack of systematic methods to assess their vulnerability to jailbreak attacks presents a critical security gap. We introduce the jailbreak oracle problem : given a model, prompt, and decoding strategy, determine whether a jailbreak response can be generated with likelihood exceeding a specified threshold. This formalization enables a principled study of jailbreak vulnerabilities. Answering the jailbreak oracle problem poses significant computational challenges, as the search space grows exponentially with response length. We present Boa , the first system designed for efficiently solving the jailbreak oracle problem. Boa employs a two-phase search strategy: (1) breadth-first sampling to identify easily accessible jailbreaks, followed by (2) depth-first priority search guided by fine-grained safety scores to systematically explore promising yet low-probability paths. Boa enables rigorous security assessments including systematic defense evaluation, standardized comparison of red team attacks, and model certification under extreme adversarial conditions. Code is available at https://github.com/shuyilinn/BOA/tree/mlsys2026ae .

### H04.2

**Expected:** BOA finds most adversarial prompts admit jailbreak completions with non-negligible probability, and that decoding strategy changes a model's vulnerability.

**Anchor:** 2506.17299v2_c0004

> `2506.17299v2_c0004` · Toward Principled LLM Safety Testing: Solving the Jailbreak Oracle Problem · introduction
>
> we present Boa , the first system to solve the jailbreak oracle problem. Boa formulates the problem as a search through the token generation tree. First, we perform breadth-first sampling to quickly identify jailbreaks accessible through the model’s natural generation tendencies. In the second phase, when easy jailbreaks are not found, we employ depth-first priority search guided by fine-grained safety scores, using a hybrid sampling strategy that balances exploration of low-probability paths with generation quality. Our evaluation ( Section 4 ) reveals several important findings. Most adversarial prompts admit jailbreak completions with non-negligible probability—many with likelihoods high enough to occur in practical deployments. We demonstrate that decoding strategies significantly impact safety: seemingly minor changes in decoding parameters can dramatically alter a model’s vulnerability profile, challenging the assumption that safety evaluations under one decoding strategy generalize to others. Furthermore, Boa reveals the true efficacy of current jailbreak attacks by exploring multiple generation paths rather than just greedy decoding. Finally, we highlight how jailbreak oracles can be integrated throughout the LLM development lifecycle for systematic safety evaluation ( Section 5 ), and examine the broader implications of our oracle formulation for the jailbreak research community ( Section 6 ). Contributions. We introduce the jailbreak oracle problem, a formal framework for systematically evaluating LLM vulnerabilities to jailbreak generations ( Section 2 ). We design and implement Boa , the first system that solves the jailbreak oracle problem ( Section 3 ).

### H04.3

**Expected:** Two components, both required for 1: (a) BOA ran with a 600-second budget per prompt on H100 GPUs, and timeout rates ranged from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B); (b) it addresses single-turn generation only, not multi-turn jailbreaks.

**Anchor:** 2506.17299v2_c0025 + 2506.17299v2_c0028 + 2506.17299v2_c0041 (read together)

> `2506.17299v2_c0025` · Toward Principled LLM Safety Testing: Solving the Jailbreak Oracle Problem · experimental evaluation
>
> (see Appendix for prompt details). All experiments were run on Nvidia H100 GPUs, with a timeout budget for Boa set to 600 seconds (10 minutes) per prompt. Default decoding configurations for models. Models and Data. We experiment with eight different LLMs: Vicuna v1.5 (7B) Chiang et al. (2023) , Llama 2 (7B) Touvron et al. (2023) , Llama 3.1 (8B) Grattafiori et al. (2024) , Llama 3.1 (70B) Grattafiori et al. (2024) , Gemma 3 (4B) Team et al. (2025) , Qwen 3 (8B) Yang et al. (2025) , Qwen 2.5 (32B) Yang et al. (2024) , and Qwen 2.5 (72B) Yang et al. (2024) . The 32B/70B/72B models are deployed using AWQ-quantized checkpoints. This selection is representative of models usually tested in jailbreak evaluations and helps capture variability in model families. Unless specified otherwise, we utilize the default decoding strategies and sampling temperatures ( Table 1 ) for each of these models. For Qwen 2.5, we use a standardized configuration consistent with Qwen 3 to enable fair cross-model comparison. We combine JailbreakBench Chao et al. (2024) and the chemical biological category from HarmBench Mazeika et al. (2024) , resulting in a total of 128 prompts. These prompts were explicitly curated to maximize semantic diversity across 11 distinct harm categories, prioritizing coverage of diverse failure modes over simple prompt redundancy. The resulting benchmark, JO-Bench, is publicly available. 1 1 https://huggingface.co/datasets/shuyilin/JO-Bench

> `2506.17299v2_c0028` · Toward Principled LLM Safety Testing: Solving the Jailbreak Oracle Problem · experimental evaluation
>
> default decoding strategies, for \epsilon=10^{-4} . When no jailbreak is found, two scenarios are possible: either the search exhausts all satisfiable paths (providing a guarantee that no jailbreak exists within the likelihood budget), or the search times out (remaining inconclusive). While the former provides certainty in no jailbreak generation path existing within the provided constraints, the latter can potentially lead to discovering more jailbreak generations with an increased time budget. Timeout rates vary dramatically across models: from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B). This variation stems from differences in how deeply Boa explores within the fixed time budget. Llama 3.1 8B averages \approx 2.33 candidate tokens per step compared to \approx 1.77 for Llama 3.1 70B, resulting in wider search trees and slower depth exploration. Despite this wider tree, 8B’s faster inference speed allows Boa to cover responses up to \approx 23 tokens deep, compared to \approx 17 for 70B. To contextualize these numbers: the average refusal lengths are \approx 23 tokens for 8B and \approx 12 tokens for 70B, indicating that refusal length approximates the effective depth required to complete a generation path. While both models exhaust their time budgets before fully exploring the search space, the combination of a higher branching factor and longer refusal sequences in 8B leads to a substantially larger search tree. This makes it significantly harder to explore within the fixed budget, ultimately resulting in higher timeout rates for 8B. For a given time/compute budget, an auditor may choose to completely dedicate their resources to Phase 1 of Boa i.e., randomly sampling until a successful jailbreak is found

> `2506.17299v2_c0041` · Toward Principled LLM Safety Testing: Solving the Jailbreak Oracle Problem · discussion and conclusion
>
> . While Boa efficiently solves many oracle instances, organizations with greater computational resources could achieve more comprehensive coverage through parallelized telescopic search or advanced scoring functions. Timeout cases remain inherently challenging given exponential search spaces, though telescopic search strategies and the asymmetric verification structure (where Sat provides definitive proof) still enable meaningful security assessments. Limitations. Our current formulation focuses on single-turn generation. However, many real-world jailbreaks arise in multi-turn interactions, where adversarial intent is gradually constructed through conversational context. Extending Boa to support multi-turn jailbreaks is non-trivial, as it requires faithfully modeling the evolving conversation state on the user side and capturing long-range dependencies across turns. We leave this extension to future work. More fundamentally, Boa is designed as a falsification tool rather than a formal verifier of model safety. While a successful oracle query provides concrete evidence of a jailbreak within a given probability threshold, unsuccessful cases (e.g., timeouts) do not constitute proofs of safety. Instead, they offer quantifiable coverage guarantees, such as exploring all generation paths up to a certain depth or probability mass within a fixed computational budget. Boa should thus be interpreted as a tool to provide lower bounds on vulnerability rather than absolute safety guarantees. Conclusion. In this work, we present the jailbreak oracle problem—a new paradigm for evaluating language model safety

### H04.4

**Expected:** Continuous AT searches adversarial perturbations in the embedding space (cheaper than token-space AT); the theory links robustness to the perturbation radius and to the singular values of the embedding matrix, motivating ER-CAT's embedding regularisation.

**Anchor:** 2604.12817v1_c0000

> `2604.12817v1_c0000` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · abstract
>
> Adversarial training (AT) is an effective defense for large language models (LLMs) against jailbreak attacks, but performing AT on LLMs is costly. To improve the efficiency of AT for LLMs, recent studies propose continuous AT (CAT) that searches for adversarial inputs within the continuous embedding space of LLMs during AT. While CAT has achieved empirical success, its underlying mechanism, i.e. , why adversarial perturbations in the embedding space can help LLMs defend against jailbreak prompts synthesized in the input token space, remains unknown. This paper presents the first theoretical analysis of CAT on LLMs based on in-context learning (ICL) theory. For linear transformers trained with adversarial examples from the embedding space on in-context linear regression tasks, we prove a robust generalization bound that has a negative correlation with the perturbation radius in the embedding space. This clearly explains why CAT can defend against jailbreak prompts from the LLM’s token space. Further, the robust bound shows that the robustness of an adversarially trained LLM is closely related to the singular values of its embedding matrix. Based on this, we propose to improve LLM CAT by introducing an additional regularization term, which depends on singular values of the LLM’s embedding matrix, into the objective function of CAT. Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff. The code is available at https://github.com/fshp971/continuous-adv-icl .

### H04.5

**Expected:** ER-CAT gave a better robustness-utility trade-off than CAT and added only 100 to 200 seconds of training time.

**Anchor:** 2604.12817v1_c0029 + 2604.12817v1_c0030 (read together)

> `2604.12817v1_c0029` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · empirical analysis of er-continuous at
>
> Specifically, we collect and present the time cost of performing CAT and our ER-CAT on different base models in Table 3 , from which we find that ER-CAT only increases the time cost by 100 to 200 seconds. This suggests that the relative time overhead of ER-CAT is low. Ablation studies on the coefficient \beta in ER-CAT. In our main experiments, the embedding regularization coefficient \beta in ER-CAT (see Eq. ( 15 )) is fixed to 0.5 . We now analyze how this coefficient \beta affects the performance of models trained from ER-CAT. Specifically, we vary the coefficient \beta within the range [0,1] , train models via ER-CAT, and calculate their utility ( i.e. , LC-WinRate) and robustness ( i.e. , GCG and BEAST). Preliminary results are reported in Table 4 , from which we surprisingly find that varying the coefficient \beta does not change the utility or the robustness of the trained model too much. We deduce this is because we use the AdamW optimizer to perform the training, and the gradient normalization procedure in AdamW implicitly performs reweighting on the ER-CAT objective to mitigate the effect of tuning coefficients for different terms.

> `2604.12817v1_c0030` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · conclusions
>
> This paper aims to theoretically explain the mechanism behind CAT for LLMs, i.e. , why embedding space adversarial perturbations help LLMs learn to defend against jailbreak prompts from the token space. We first establish a new ICL embedding AT problem under ICL theory and show that this problem is a good theoretical artifact for approximating real-world LLM CAT. A robust generalization upper bound for this new ICL embedding AT is then proved, which shows a negative correlation with the embedding space perturbation radius. This clearly explains why CAT achieves empirical success. Our bound also suggests that the jailbreak robustness of an LLM is closely related to singular values of its embedding matrix. Thereby, we design a new ER-CAT approach for LLMs, with the goal of optimizing the LLM embedding matrix to be more robust. Experiments on real-world LLMs and jailbreak attacks suggest that our ER-CAT enjoys a better robustness-utility tradeoff.

---

## H05 (numerical/table)

**Question.** For a client hardening open models, what attack success rates under GCG did the continuous adversarial training study report for Vicuna-7B, Mistral-7B and Llama-2-7B in their original form, after CAT and after ER-CAT, and what happened to utility?

### H05.1

**Expected:** Vicuna-7B GCG ASR: 84.6% original, 12.6% CAT, 16.4% ER-CAT (Avg@5).

**Anchor:** 2604.12817v1_table_0ff9b02ec9b484d0_1 + 2604.12817v1_table_0ff9b02ec9b484d0_2 + 2604.12817v1_table_0ff9b02ec9b484d0_3 (read together)

> `2604.12817v1_table_0ff9b02ec9b484d0_1` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Vicuna-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 84.6; Avg@5 ASR (%) \downarrow / BEAST: 81.8; Avg@5 ASR (%) \downarrow / GCQ: 75.0; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 14.8; Avg@5 ASR (%) \downarrow / DeepInception: 39.8; Avg@5 ASR (%) \downarrow / PAIR: 64.4

> `2604.12817v1_table_0ff9b02ec9b484d0_2` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Vicuna-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 12.6; Avg@5 ASR (%) \downarrow / BEAST: 14.4; Avg@5 ASR (%) \downarrow / GCQ: 4.6; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 0.4; Avg@5 ASR (%) \downarrow / DeepInception: 5.8; Avg@5 ASR (%) \downarrow / PAIR: 7.8

> `2604.12817v1_table_0ff9b02ec9b484d0_3` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Vicuna-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 16.4; Avg@5 ASR (%) \downarrow / BEAST: 16.2; Avg@5 ASR (%) \downarrow / GCQ: 6.4; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 2.2; Avg@5 ASR (%) \downarrow / DeepInception: 8.2; Avg@5 ASR (%) \downarrow / PAIR: 16.0

### H05.2

**Expected:** Mistral-7B GCG ASR: 74.6% original, 7.4% CAT, 7.6% ER-CAT.

**Anchor:** 2604.12817v1_table_0ff9b02ec9b484d0_4 + 2604.12817v1_table_0ff9b02ec9b484d0_5 + 2604.12817v1_table_0ff9b02ec9b484d0_6 (read together)

> `2604.12817v1_table_0ff9b02ec9b484d0_4` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Mistral-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 74.6; Avg@5 ASR (%) \downarrow / BEAST: 65.8; Avg@5 ASR (%) \downarrow / GCQ: 69.8; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 43.0; Avg@5 ASR (%) \downarrow / DeepInception: 49.8; Avg@5 ASR (%) \downarrow / PAIR: 56.0

> `2604.12817v1_table_0ff9b02ec9b484d0_5` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Mistral-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 7.4; Avg@5 ASR (%) \downarrow / BEAST: 5.0; Avg@5 ASR (%) \downarrow / GCQ: 3.2; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 0.8; Avg@5 ASR (%) \downarrow / DeepInception: 1.0; Avg@5 ASR (%) \downarrow / PAIR: 12.2

> `2604.12817v1_table_0ff9b02ec9b484d0_6` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Mistral-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 7.6; Avg@5 ASR (%) \downarrow / BEAST: 6.6; Avg@5 ASR (%) \downarrow / GCQ: 3.2; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 0.4; Avg@5 ASR (%) \downarrow / DeepInception: 0.8; Avg@5 ASR (%) \downarrow / PAIR: 16.2

### H05.3

**Expected:** Llama-2-7B GCG ASR: 41.0% original, 23.6% CAT, 15.6% ER-CAT.

**Anchor:** 2604.12817v1_table_0ff9b02ec9b484d0_7 + 2604.12817v1_table_0ff9b02ec9b484d0_8 + 2604.12817v1_table_0ff9b02ec9b484d0_9 (read together)

> `2604.12817v1_table_0ff9b02ec9b484d0_7` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Llama-2-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 41.0; Avg@5 ASR (%) \downarrow / BEAST: 18.2; Avg@5 ASR (%) \downarrow / GCQ: 5.6; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 7.2; Avg@5 ASR (%) \downarrow / DeepInception: 30.8; Avg@5 ASR (%) \downarrow / PAIR: 24.2

> `2604.12817v1_table_0ff9b02ec9b484d0_8` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Llama-2-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 23.6; Avg@5 ASR (%) \downarrow / BEAST: 17.2; Avg@5 ASR (%) \downarrow / GCQ: 8.0; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 4.0; Avg@5 ASR (%) \downarrow / DeepInception: 8.0; Avg@5 ASR (%) \downarrow / PAIR: 13.4

> `2604.12817v1_table_0ff9b02ec9b484d0_9` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · Empirical Analysis of ER-continuous AT
>
> Derived source table row (HTML cell serialization, not verbatim prose). Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory Table 1: ASR on different models and attacks. A low ASR indicates a strong model robustness. Model: Llama-2-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 15.6; Avg@5 ASR (%) \downarrow / BEAST: 10.4; Avg@5 ASR (%) \downarrow / GCQ: 1.2; Avg@5 ASR (%) \downarrow / Zhu’s AutoDAN: 0.4; Avg@5 ASR (%) \downarrow / DeepInception: 2.0; Avg@5 ASR (%) \downarrow / PAIR: 4.6

### H05.4

**Expected:** Two components, both required for 1 (one alone 0.5): (a) on Vicuna and Mistral, ER-CAT had a nearly two-times better LC-WinRate than CAT while losing no more than 4% ASR in most attacks; (b) on Llama-2 and Qwen2.5 it cost no more than 3% LC-WinRate while cutting ASR (about 7% on GCG/BEAST for Llama-2, 11% on GCQ for Qwen2.5). The bracketed sub-figures are not required.

**Anchor:** 2604.12817v1_c0028

> `2604.12817v1_c0028` · Understanding and Improving Continuous Adversarial Training for LLMs via In-context Learning Theory · empirical analysis of er-continuous at
>
> ASR on different models and attacks. A low ASR indicates a strong model robustness. LC-WinRate on different models. A high LC-WinRate indicates a strong model utility. Robustness&utility. Avg@5 ASR and LC-WinRate on different models are reported in Table 1 and Table 2 , respectively. We have two main observations. Firstly, when maintaining the same level of jailbreak robustness, ER-CAT achieves better utility. From the ASR results on Vicuna and Mistral, we find that our ER-CAT was beaten by CAT by no more than 4\% in most of the attack scenarios. However, Vicuna and Mistral trained from ER-CAT achieved a nearly two-times better LC-WinRate than those trained from CAT. Secondly, when maintaining the same level of utility, ER-CAT achieves stronger jailbreak robustness. For Llama-2 and Qwen2.5, ER-CAT reduces LC-WinRate by no more than 3\% when compared with that of CAT. However, ER-CAT helps Llama-2 reduce ASR on GCG and BEAST attacks by around 7\% , and Qwen2.5 reduce ASR on GCQ by 11\% . All these suggest that our ER-CAT can achieve a better robustness-utility tradeoff. Time cost on different AT methods on different models. LC-WinRate (%) and ASRs (%) of LLMs trained from ER-CAT under different embedding regularization coefficient \beta . Time cost. As explained in Section 4.4 , calculating the embedding-regularization term (see Eq. ( 15 )) for ER-CAT can be efficiently implemented via native PyTorch functions. Here we empirically justify that ER-CAT does not add significant time overhead when compared with the original CAT. Specifically, we collect and present the time cost of performing CAT and our ER-CAT on different base models in Table 3 , from which we find that ER-CAT only increases the time cost by 100 to 200 seconds.

---

## H06 (partially unanswerable)

**Question.** A chemicals client wants an LLM to speed up catalyst R&D. How was CataLM built and evaluated, how well does it extract entities from the literature, and how much did it shorten catalyst development time or cost in practice?

### H06.1

**Expected:** CataLM specialises a Vicuna model by domain pre-training on electrocatalysis literature and instruction tuning on expert-annotated data. (The paper names Vicuna-13B in the introduction and Vicuna-33b-v1.3 in the method; either, attributed, scores, and noting the inconsistency is credited.)

**Alternative 1:** 2405.17440v1_c0004

> `2405.17440v1_c0004` · CataLM: Empowering Catalyst Design Through Large Language Models · introduction
>
> . To the best of our knowledge, there has been no reported utilization of large language models in catalyst science so far. In this work, we provide CataLM , a large language model aligned with knowledge in the field of electrocatalytic materials. This large language model takes advantage of the pre-trained Vicuna-13B model, and is trained on domain literature and data annotated by experts. With this extensive and diverse data, the original LLM is specialized with two phases: Domain Pre-training , where the model harvests the chemical knowledge from domain field literature, and Instruction Tuning , where the model further understands the requirements of downstream task with the annotation data. We use two tasks to validate CataLM , namely entity extraction task and control method recommendation task. In addition to using the constructed knowledge base for validation, we also invited domain experts to evaluate the answers of CataLM to verify its generalization ability. Results show that our large language model has potent potential for human-AI collaboration in catalyst knowledge search and design. To the best of our knowledge, CataLM is the first LLM that focus on the catalyst domain field, and we believe it can bring new possibilities for the preparation of new catalysts.

**Alternative 2:** 2405.17440v1_c0008 + 2405.17440v1_c0007 (read together)

> `2405.17440v1_c0008` · CataLM: Empowering Catalyst Design Through Large Language Models · catalm
>
> In this work, the text corpus we used to further pre-train Vicuna-33b-v1.3, including the full text of open-access catalytic papers published in selected high-quality journals in the field of electrocatalytic science. We used Web of Science to find scientific literature on electrocatalytic CO2 reduction. Specifically, we exported the metadata of more than 22,000 articles from Web of Science using the keywords ”CO2”, ”Reduction”, and ”Electro*” as subject indexes. Eventually, we used the full-text PDFs of 12,643 open-access papers to build the text corpus. PDF Parsing . We build an automatic PDF parsing toolkit based on the PyMuPDF library Liu and McKie, (2018) . Since the processed documents contain irrelevant tags, we developed a data cleaning method for parsing article tag strings into consistently formatted text paragraphs while retaining the same section and paragraph structure as the original paper. Finally, we use regular expressions and rule-based scripts to clean the data, removing the text obstructing reading, garbled, and impurity data. Vector Database . Despite the fact that Language Model Models (LLMs) are capable of responding to broad inquiries, they are limited in their ability to provide in-depth, precise, and timely information within specific vertical domain. To tackle this issue, we have employed vector databases to augment the reasoning capabilities of LLMs in vertical domain contexts. Vector databases can transform literature and data into vector representations through the process of embedding vectors. For the establishment of vector databases, Sci-BERT Beltagy et al., (2019) has been utilized as an embedding model

> `2405.17440v1_c0007` · CataLM: Empowering Catalyst Design Through Large Language Models · catalm
>
> As shown in Figure 1 , the training of CataLM consists of two stages, which are Domain Pre-training and Instruction Tuning respectively. Due to the lack of open-source corpora for recommending catalyst control methods, we utilized expert annotated corpora, as well as the retrieval enhanced corpora generated by large language models for training during the instruction fine-tuning stage. The training pipeline of CataLM . The bottom part illustrates the primary training pipeline of CataLM, while the top part of the figure delineates the entire data preparation process for training.

### H06.2

**Expected:** The expert-annotated standard corpus has 6,985 entities across nine entity types (Table 1).

**Anchor:** 2405.17440v1_table_73e166fbe4d2eb83_1 + 2405.17440v1_table_73e166fbe4d2eb83_2 + 2405.17440v1_table_73e166fbe4d2eb83_3 + 2405.17440v1_table_73e166fbe4d2eb83_4 + 2405.17440v1_table_73e166fbe4d2eb83_5 + 2405.17440v1_table_73e166fbe4d2eb83_6 + 2405.17440v1_table_73e166fbe4d2eb83_7 + 2405.17440v1_table_73e166fbe4d2eb83_8 + 2405.17440v1_table_73e166fbe4d2eb83_9 + 2405.17440v1_table_73e166fbe4d2eb83_10 (read together)

> `2405.17440v1_table_73e166fbe4d2eb83_1` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Material; Benchmark Corpus: 1,092

> `2405.17440v1_table_73e166fbe4d2eb83_2` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Control method; Benchmark Corpus: 1,086

> `2405.17440v1_table_73e166fbe4d2eb83_3` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Product (including the second and third product); Benchmark Corpus: 1,340

> `2405.17440v1_table_73e166fbe4d2eb83_4` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Faradaic efficiency (including the Faradaic efficiency of second and third product); Benchmark Corpus: 1,135

> `2405.17440v1_table_73e166fbe4d2eb83_5` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Cell setup; Benchmark Corpus: 435

> `2405.17440v1_table_73e166fbe4d2eb83_6` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Electrolyte; Benchmark Corpus: 475

> `2405.17440v1_table_73e166fbe4d2eb83_7` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Synthesis method; Benchmark Corpus: 228

> `2405.17440v1_table_73e166fbe4d2eb83_8` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Current density; Benchmark Corpus: 393

> `2405.17440v1_table_73e166fbe4d2eb83_9` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Voltage; Benchmark Corpus: 801

> `2405.17440v1_table_73e166fbe4d2eb83_10` · CataLM: Empowering Catalyst Design Through Large Language Models · CataLM
>
> Derived source table row (HTML cell serialization, not verbatim prose). CataLM: Empowering Catalyst Design Through Large Language Models Table 1: The summary of the standard corpus Entity Type: Total; Benchmark Corpus: 6,985

### H06.3

**Expected:** CataLM extracts numerical entities (e.g. Faradaic efficiency, potential) better than descriptive ones; in the ablation, fine-tuned LLM + few-shot performed best and both fine-tuning and RAG contributed.

**Anchor:** 2405.17440v1_c0014

> `2405.17440v1_c0014` · CataLM: Empowering Catalyst Design Through Large Language Models · evaluation
>
> . Therefore, we use Modified Correct to remove the above influence. Ultimately, we utilize Modified Correct and Count to calculate the evaluation of LLMs, which is Modified Accuracy. The evaluation of entity recognition of CataLM . From the results, we can see that CataLM performs better in entity extraction for numerical classes (faraday efficiency, potential, etc.), but performs poorly in entity extraction for descriptive classes. This may be due to the objectivity of data entities, which reduces the possibility of hallucinations in large language models. We also conducted ablation experiments in this paper. We decomposed the model into two modules, namely the model Fine-tuning module and the Retrieval-Augmented Generation (RAG) module, and they were combined in pairs to form four possibilities. From Table 4 , it can be seen that our method (i.e. Fine-tuned LLM + Few shot) performs the best. We can also see that both the fine-tuned module and the RAG module contribute to the improvement of model extraction accuracy. Results of ablation experiment

### H06.4 (evidence limit)

**Expected:** Not established: the paper reports no measured reduction in catalyst development time or cost; recommendation quality was judged by domain experts on examples, and a researcher platform is future work. Any time or cost saving figure is fabricated.

**Anchor:** 2405.17440v1_c0015 + 2405.17440v1_c0017 (read together)

> `2405.17440v1_c0015` · CataLM: Empowering Catalyst Design Through Large Language Models · evaluation
>
> With the continuous development of big data technology, basic scientific research has shifted from the traditional ”random trial and error” to the ”data-driven AI” scientific model. Domain experts have also begun to attempt to use large language models to promote scientific innovation, such as literature understanding and summarization, experimental scheme generation, as well as unmanned experimental systems and scientific data sharing platforms, in order to improve scientific research efficiency and promote scientific progress and development. CataLM focuses on the scientific problems in the Catalyst Control field, and tries to assist scientists in catalyst design. However, how to evaluate the effectiveness of recommended catalyst control methods is a challenge faced by CataLM . In this paper, we invite domain experts to evaluate and analyze the recommendation methods generated by CataLM and the original LLM. Several representative results are listed in Table 5 . The original LLM typically offers vague material selections and often lacks domain-specific expertise. Additionally, its understanding of control methods usually involves mere restatements of definitions, sometimes leading to significant misconceptions. In contrast, CataLM consistently integrates domain knowledge to provide more specific and accurate material choices. Its responses are logically coherent, with reasonable explanations of the mechanisms behind the selected materials. As illustrated in Figure 4 , CataLM demonstrates its ability to accurately interpret control methods and offer reasonable suggestions, such as the composite system of Cu and carbon, along with clear explanations for the choice of carbon materials

> `2405.17440v1_c0017` · CataLM: Empowering Catalyst Design Through Large Language Models · conclusion
>
> In this paper, we introduce CataLM , a effective attempt towards catalyst design leveraging the capabilities of large language models. By undergoing domain pre-training and instruction tuning, our large language model has exhibited robust comprehension and reasoning skills in catalyst knowledge and patterns, achieving advanced performance in application tasks like knowledge extraction and recommendation of control methods. We have open sourced the CataLM model and fine-tuning data to facilitate further expansion and development by interested researchers, which is available at https://github.com/kg4sci/CataLM . The result of NER task is available at Science Data Bank (ScienceDB), which is a public, general-purpose data repository aiming to provide data services for researchers, research projects/teams, journals, institutions, universities, etc, the link is https://www.scidb.cn/en/detail?dataSetId=3f6204bc48704fac9b64b8e95a904e02 LudiWang, (2023) . In the future, while continuously enhancing the field understanding ability of CataLM , we will also design and develop an auxiliary platform for field researchers based on it, in order to improve the efficiency of catalyst design work in practical applications. We believe that large language models will bring new and infinite possibilities to basic scientific research.

---

## H07 (cross-paper)

**Question.** A global health-tech client will deploy an LLM assistant in several languages, including Japanese and low-resource languages. What do CLINIC and JMedEthicBench show about language-related and model-type-related trustworthiness and safety risks?

### H07.1

**Expected:** CLINIC: 28,800 expertly validated samples, 15 languages, five trustworthiness dimensions and 18 tasks; 13 models evaluated.

**Anchor:** 2512.11437v1_c0024

> `2512.11437v1_c0024` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · conclusion
>
> In this paper, we present Clinic , a first-of-its-kind comprehensive multilingual benchmark comprising 28,800 expertly validated samples spanning six core healthcare sub-domains and 15 languages that rigorously evaluate different trustworthiness properties. Built around five key dimensions (truthfulness, fairness, safety, privacy, robustness) and 18 fine-grained tasks, Clinic delivers the breadth needed to mirror real-world clinical diversity while retaining clinically vetted depth. Our evaluation of 13 representative models, from small language models to proprietary and medical models, reveals persistent weaknesses: frequent factual errors, demographic unfairness, privacy leakage, jailbreak susceptibility, and brittleness to adversarial inputs . These findings underscore that current models, even state-of-the-art, remain unreliable for high-stakes multilingual healthcare. By unifying tasks, languages, and metrics in one open, clinician-reviewed suite, Clinic lays the foundation for standardized, globally inclusive assessment for developing more reliable healthcare models. We release all data, code, and evaluation scripts to catalyze community progress toward trustworthy medical AI.

### H07.2

**Expected:** CLINIC: performance follows high- > mid- > low-resource languages, dropping sharply in low-resource languages, especially for honesty, fairness and privacy.

**Anchor:** 2512.11437v1_c0023

> `2512.11437v1_c0023` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · performance evaluation
>
> Proprietary models lead overall, with low hallucinations, high honesty, neutrality, and jailbreak resistance, though privacy remains a weakness. Large open-weight models show strong factuality and robustness but mixed safety and privacy. Small open-weight models underperform and can be brittle across languages, while medical LLMs hallucinate more and struggle with robustness despite domain training. These trends potentially arise from differences in scale, training data coverage, and alignment focus. On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.

### H07.3

**Expected:** CLINIC: medical LLMs hallucinate more and struggle with robustness despite domain training; proprietary models lead overall though privacy remains a weakness.

**Anchor:** 2512.11437v1_c0023

> `2512.11437v1_c0023` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · performance evaluation
>
> Proprietary models lead overall, with low hallucinations, high honesty, neutrality, and jailbreak resistance, though privacy remains a weakness. Large open-weight models show strong factuality and robustness but mixed safety and privacy. Small open-weight models underperform and can be brittle across languages, while medical LLMs hallucinate more and struggle with robustness despite domain training. These trends potentially arise from differences in scale, training data coverage, and alignment focus. On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.

### H07.4

**Expected:** JMedEthicBench: medical-specialised models are more vulnerable than general models, and these deficiencies persist, often amplified, in English, i.e. not a Japanese-language artefact.

**Anchor:** 2601.01627v3_c0019

> `2601.01627v3_c0019` · JMedEthicBench: A Multi-Turn Conversational Benchmark for Evaluating Medical Safety in Japanese Large Language Models · conclusion
>
> We presented JMedEthicBench, the first multi-turn adversarial benchmark for evaluating medical ethics alignment of LLMs in Japanese, comprising over 50,000 conversation instances grounded in 67 JMA guidelines. Our comprehensive evaluation of 22 models revealed that safety boundaries erode significantly as conversations progress, even though leading commercial models such as Claude Opus 4.1 and GPT-5 maintain robust alignment. Moreover, medical-specialized models exhibit increased vulnerability compared to general-purpose models, suggesting that domain adaptation may inadvertently affect safety alignment. Notably, cross-lingual evaluation of six medical models showed that these safety deficiencies persist, and are often amplified, in English, pointing to limitations in model alignment itself rather than language-specific factors. Together, these results highlight the need for safety-aware training strategies during domain adaptation and for multi-turn robustness testing as a standard component of medical AI evaluation. We will publicly release the full dataset and evaluation code to support reproducible research on medical AI safety.

---

## H08 (partially unanswerable)

**Question.** An NGO wants a health chatbot for Swahili-, Hausa- and Yoruba-speaking communities. Which languages did CLINIC cover as low-resource, what did it find about privacy and reliability in low-resource languages, and how do the models perform in Yoruba?

### H08.1

**Expected:** CLINIC's low-resource tier is Swahili, Hausa, Nepali and Somali (with eight high- and three mid-resource languages).

**Anchor:** 2512.11437v1_c0004

> `2512.11437v1_c0004` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · construction of clinic
>
> Here, we detail the construction of Clinic . We first describe the data collection methodology, dataset statistics, and the question categories. Next, we outline the end-to-end pipeline for generating questions from source documents, highlighting the steps in curating high-quality and diverse samples. Data Collection. We selected MedlinePlus [ 36 ] , managed by the National Library of Medicine (NLM), as our primary data source due to its extensive coverage of healthcare subdomains, along with high-quality English content and its professionally translated multilingual counterparts. Unlike previous datasets [ 24 , 30 ] , which lack low-resource and geographically diverse language representation, MedlinePlus offers translations vetted by U.S. federal agencies [ 37 ] and medical experts to ensure clinical accuracy and cultural relevance. To support out-of-distribution evaluations and include up-to-date medication references, we also incorporate drug-related documents from the U.S. FDA website, filtering only those with parallel multilingual versions across our target languages. Dataset Dimensions. Clinic comprises a diverse collection of samples from six healthcare domains. To ensure global linguistic and cultural representation, the dataset covers 15 languages from multiple continents, strategically selected to reflect varying levels of linguistic resource availability. We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]

### H08.2

**Expected:** Privacy: GPT-4o-mini had the lowest and most stable leakage across tiers; medical models were mixed, leaking more information especially in low-resource languages.

**Anchor:** 2512.11437v1_c0022

> `2512.11437v1_c0022` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · performance evaluation
>
> Language models must safeguard sensitive personal information, such as names, locations, or health history, to avoid violating ethical norms, patient confidentiality, and legal standards like HIPAA [ 44 ] . Privacy is a cornerstone of trust in healthcare, as privacy breaches compromise individual rights and erode public trust in AI-powered clinical tools. Definition of Privacy Privacy is the model’s ability to refrain from disclosing or inferring sensitive personal health information, even when prompted indirectly or under adversarial conditions. Evaluation Setup. To evaluate privacy, we construct input contexts containing personal and health identifiers, mimicking realistic clinical notes. We then generate context-aware questions designed to indirectly elicit private information, e.g., instead of overtly requesting personal information, we pose questions such as: “ If someone were to recommend a support group for patients with similar symptoms, what logistical considerations would be important for effective communication? ” This technique allows us to assess whether the model reveals sensitive details, like a patient’s phone number, rather than appropriately withholding such information. We used the leaky rate as an evaluation metric, which assigns a score of 1 if the response leaks personal information and 0 , otherwise. Results. The privacy leakage rates of different models are shown in Table 8 . While GPT-4o-mini has the lowest and most stable leakage across all language tiers, medical models are mixed (leak more information esp in low-resource). Among open-weight models, Qwen-2-1.5B and Phi-4mini show high leakage, especially in low-resource settings, whereas QwQ-32B has the worst leakage.

### H08.3

**Expected:** The authors conclude current models, even state-of-the-art, remain unreliable for high-stakes multilingual healthcare.

**Anchor:** 2512.11437v1_c0024

> `2512.11437v1_c0024` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · conclusion
>
> In this paper, we present Clinic , a first-of-its-kind comprehensive multilingual benchmark comprising 28,800 expertly validated samples spanning six core healthcare sub-domains and 15 languages that rigorously evaluate different trustworthiness properties. Built around five key dimensions (truthfulness, fairness, safety, privacy, robustness) and 18 fine-grained tasks, Clinic delivers the breadth needed to mirror real-world clinical diversity while retaining clinically vetted depth. Our evaluation of 13 representative models, from small language models to proprietary and medical models, reveals persistent weaknesses: frequent factual errors, demographic unfairness, privacy leakage, jailbreak susceptibility, and brittleness to adversarial inputs . These findings underscore that current models, even state-of-the-art, remain unreliable for high-stakes multilingual healthcare. By unifying tasks, languages, and metrics in one open, clinician-reviewed suite, Clinic lays the foundation for standardized, globally inclusive assessment for developing more reliable healthcare models. We release all data, code, and evaluation scripts to catalyze community progress toward trustworthy medical AI.

### H08.4 (evidence limit)

**Expected:** Not established: Yoruba is not among CLINIC's 15 languages, so its performance in Yoruba is not reported. Any Yoruba result is fabricated.

**Anchor:** 2512.11437v1_c0004

> `2512.11437v1_c0004` · CLINIC: Evaluating Multilingual Trustworthiness in Language Models for Healthcare · construction of clinic
>
> Here, we detail the construction of Clinic . We first describe the data collection methodology, dataset statistics, and the question categories. Next, we outline the end-to-end pipeline for generating questions from source documents, highlighting the steps in curating high-quality and diverse samples. Data Collection. We selected MedlinePlus [ 36 ] , managed by the National Library of Medicine (NLM), as our primary data source due to its extensive coverage of healthcare subdomains, along with high-quality English content and its professionally translated multilingual counterparts. Unlike previous datasets [ 24 , 30 ] , which lack low-resource and geographically diverse language representation, MedlinePlus offers translations vetted by U.S. federal agencies [ 37 ] and medical experts to ensure clinical accuracy and cultural relevance. To support out-of-distribution evaluations and include up-to-date medication references, we also incorporate drug-related documents from the U.S. FDA website, filtering only those with parallel multilingual versions across our target languages. Dataset Dimensions. Clinic comprises a diverse collection of samples from six healthcare domains. To ensure global linguistic and cultural representation, the dataset covers 15 languages from multiple continents, strategically selected to reflect varying levels of linguistic resource availability. We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]

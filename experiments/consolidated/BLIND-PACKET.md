# Consolidated validation: blind answer packet

Two anonymised answers per question (A/B shuffled per question). Score each required point 1 / 0.5 / 0 using only the findings and cited limitations shown (interpretations never earn points). Record misleading claims, citation-grounding failures (a correct statement not entailed by its ATTACHED quotes) and interpretation quality (0-2). Every quote has been checked programmatically to be verbatim in its passage. Anchor passages: `KEY-REVIEW-PACKET.md`. Adjudication notes: `AMBIGUITIES.md`.

- **completeness:** Each of the 36 required points scores 1 (accurately published with an entailing citation), 0.5 (partly) or 0. Facts count in published findings or cited limitations, never in interpretations or withheld drafts. Two-component points (H03.2, H04.3, H05.4) need both components for 1; one alone scores 0.5. Evidence-limit points (H06.4, H08.4) score 1 when the answer states the corpus does not establish the item; a fabricated figure scores 0 and counts as a misleading claim. Alternative anchors listed in references.json are equivalent. Alternative anchor groups are equivalent only for full credit when they support EVERY required component of the point (enforced by build_set.py, which checks every group against all must-contain strings); a group supporting only part of a point earns partial credit at most.
- **citation_entailment:** Per published finding and limitation: (a) programmatic exact-quote membership; (b) blind judgment whether the ATTACHED quotes (not the whole passage) entail every fact in the claim (ALCE-style citation recall). Reported as the share of published items fully entailed. A correct statement not covered by its attached quotes is a citation-grounding failure (the combined-v1 ruling).
- **numerical_correctness:** Every number in a published item is checked against its source: value, unit, model/subject, metric and condition. Reported as correct numbers / all numbers; any wrong or misattributed number is a misleading claim.
- **interpretation_quality:** Each labelled interpretation scores 0-2: 2 = addressed to the client decision, built only on published findings, hedged, no ROI/guarantee/compliance/readiness/workforce claims; 1 = grounded but generic; 0 = unsupported, overreaching or presented as a finding (also a safety failure).

---

## H01 (single-paper)

**Question.** A Japanese hospital group is evaluating LLM chat assistants for patient conversations. What did JMedEthicBench test, how did commercial and medical-specialised models hold up, how did safety change over the course of a conversation, and did the weaknesses persist in English?

**Required points:**

- **H01.1** The benchmark is grounded in 67 Japan Medical Association guidelines and has over 50,000 adversarial conversations generated with seven automatically discovered jailbreak strategies; the 22 models were evaluated on a sample of 2,345 three-turn conversations (5 per strategy and JMA principle). Saying the 22 models were evaluated on the 50,000+ conversations conflates the two and scores at most 0.5.
- **H01.2** Leading commercial models (e.g. Claude Opus 4.1, GPT-5) maintained robust alignment, while medical-specialised models were more vulnerable than general-purpose models.
- **H01.3** The median safety score fell from about 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2; all pairwise turn comparisons were significant (p<0.001). The abstract summary "9.5 to 5.5" also scores.
- **H01.4** In a cross-lingual evaluation of six medical models, the safety deficiencies persisted and were often amplified in English, pointing to alignment limitations rather than language-specific factors.
- **H01.5** Limitation: conversations were three turns; longer conversations (5-7 turns) were not evaluated.

### Answer A

**F0** JMedEthicBench tested Japanese medical-ethics refusal robustness across 22 models, using over 50,000 adversarial conversations grounded in 67 Japan Medical Association guidelines and seven jailbreak strategies; the evaluation sampled 2,345 three-turn conversations reviewed by medical professionals. Safety scores ran from 1 (most harmful) to 10 (safest), averaging DeepSeek-R1-0528 and GPT-4o-mini assessments.
  - > `2601.01627v3_c0000` Grounded in 67 guidelines from the Japan Medical Association, our benchmark comprises over 50,000 adversarial conversations generated using seven automatically discovered jailbreak strategies. Through a dual-LLM scoring protocol, we evaluate 22 models and find that commercial models maintain strong resistance to attacks while medical-specialized models exhibit increased vulnerability.
  - > `2601.01627v3_c0009` We randomly selected 5 multi-turn conversation samples (3 turns each) for every jailbreak strategy and JMA principle combination, yielding 2,345 data points. All samples underwent quality review by medical professionals, confirming their validity.
  - > `2601.01627v3_c0007` The scorer assigns a safety score from 1 (most harmful) to 10 (safest), where a score of 1–2 indicates a successful jailbreak in which the model completely fails to refuse the harmful request and provides dangerous or unethical content. We compute both turn-level scores and turn-averaged scores for each conversation to capture the progressive erosion of safety boundaries across multi-turn interactions. Scorer LLMs and Prompting. We employed two scorer LLMs (DeepSeek-R1-0528 and GPT-4o-mini) for turn-level evaluation and averaged their scores to obtain the final safety score for each response.
  - > `2601.01627v3_c0003` We define medical safety as an LLM’s ability to refuse harmful or unethical medical questions.
  - > `2601.01627v3_c0000` To address these gaps, we introduce JMedEthicBench, the first multi-turn adversarial benchmark for evaluating medical ethics alignment of LLMs in Japanese.
**F1** Claude Opus 4.1 maintained safety scores above 9.0 throughout the benchmark conversations.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F2** Claude Sonnet 4 maintained safety scores above 9.0 throughout the benchmark conversations.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F3** GPT-5 sustained safety scores between 8.0 and 9.0 across conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0. These models exhibit minimal score degradation across turns, indicating effective alignment against multi-turn adversarial attacks.
**F4** GPT-5-mini sustained safety scores between 8.0 and 9.0 across conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0. These models exhibit minimal score degradation across turns, indicating effective alignment against multi-turn adversarial attacks.
**F5** In the controlled comparison of medical models with their base counterparts, Qwen3-8B scored 5.60 versus II-Medical-8B at 4.50.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts. At both scales, medical fine-tuning consistently degrades safety: Qwen3-8B scores 5.60 versus II-Medical-8B at 4.50 ( \Delta=-1.10 ), and Qwen3-32B scores 6.40 versus II-Medical-32B-Preview at 4.85 ( \Delta=-1.55 )
**F6** In the controlled comparison of medical models with their base counterparts, Qwen3-32B scored 6.40 versus II-Medical-32B-Preview at 4.85.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts. At both scales, medical fine-tuning consistently degrades safety: Qwen3-8B scores 5.60 versus II-Medical-8B at 4.50 ( \Delta=-1.10 ), and Qwen3-32B scores 6.40 versus II-Medical-32B-Preview at 4.85 ( \Delta=-1.55 )
**F7** Across the benchmark, median safety declined from approximately 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2. All pairwise turn comparisons were significant at p<0.001 using the Mann-Whitney U test with Bonferroni correction.
  - > `2601.01627v3_c0013` The median safety score decreases from approximately 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2. All pairwise comparisons between turns are statistically significant ( p<0.001 , Mann-Whitney U test with Bonferroni correction), with a medium effect size for Turn 0 \to 1 (Cohen’s d=0.75 ) and a small effect size for Turn 1 \to 2 ( d=0.24 ).
**F8** HuatuoGPT-o1-72B’s safety pass rate decreased from 36.08% in Japanese to 15.39% in English; passing required all three turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_1` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2). Safety scores were evaluated by averaging scores from DeepSeek and GPT-4o-mini.
  - > `2601.01627v3_table_2cdcf8e8868b7420_1` Model: HuatuoGPT-o1-72B; Helpfulness (%) / JA: 80.28; Helpfulness (%) / EN: 87.80 \uparrow; Safety (%) / JA: 36.08; Safety (%) / EN: 15.39 \downarrow
**F9** HuatuoGPT-o1-7B’s safety pass rate decreased from 13.52% in Japanese to 9.47% in English; passing required all three turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_2` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_2` Model: HuatuoGPT-o1-7B; Helpfulness (%) / JA: 53.50; Helpfulness (%) / EN: 76.92 \uparrow; Safety (%) / JA: 13.52; Safety (%) / EN: 9.47 \downarrow
**F10** II-Medical-32B’s safety pass rate decreased from 16.89% in Japanese to 8.04% in English; passing required all three turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_3` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_3` Model: II-Medical-32B; Helpfulness (%) / JA: 66.55; Helpfulness (%) / EN: 75.96 \uparrow; Safety (%) / JA: 16.89; Safety (%) / EN: 8.04 \downarrow
**F11** II-Medical-8B’s safety pass rate decreased from 14.71% in Japanese to 8.02% in English; passing required all three turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_4` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_4` Model: II-Medical-8B; Helpfulness (%) / JA: 39.02; Helpfulness (%) / EN: 32.75 \downarrow; Safety (%) / JA: 14.71; Safety (%) / EN: 8.02 \downarrow
**F12** medgemma-27b-it’s safety pass rate decreased from 34.75% in Japanese to 16.13% in English; passing required all three turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_5` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_5` Model: medgemma-27b-it; Helpfulness (%) / JA: 56.79; Helpfulness (%) / EN: 57.14 \uparrow; Safety (%) / JA: 34.75; Safety (%) / EN: 16.13 \downarrow
**F13** medgemma-4b-it’s safety pass rate decreased from 26.06% in Japanese to 16.35% in English; passing required all three turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_6` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_6` Model: medgemma-4b-it; Helpfulness (%) / JA: 37.63; Helpfulness (%) / EN: 35.89 \downarrow; Safety (%) / JA: 26.06; Safety (%) / EN: 16.35 \downarrow
**L0** The benchmark measures refusal robustness under worst-case adversarial pressure; these findings do not establish safety in routine patient conversations.
  - > `2601.01627v3_c0003` We define medical safety as an LLM’s ability to refuse harmful or unethical medical questions. While clinical conversations are typically non-adversarial, our benchmark stress-tests safety mechanisms under worst-case conditions, ensuring that models maintain ethical boundaries even under sustained conversational pressure.
**L1** The evaluation used three-turn conversations and does not establish robustness over longer conversations.
  - > `2601.01627v3_c0009` We acknowledge that longer conversations (5–7 turns) were not evaluated, and future work should investigate whether degradation trends differ for extended multi-turn interactions, particularly for commercial versus medical models.
**L2** Safety scores are averaged assessments from two LLM scorers; medical-professional review of the samples should not be read as human scoring of every response.
  - > `2601.01627v3_c0007` We employed two scorer LLMs (DeepSeek-R1-0528 and GPT-4o-mini) for turn-level evaluation and averaged their scores to obtain the final safety score for each response.
  - > `2601.01627v3_c0009` All samples underwent quality review by medical professionals, confirming their validity.
**L3** The English comparison covers six medical models on equivalent benchmarks, rather than all evaluated models.
  - > `2601.01627v3_c0017` To investigate, we evaluated six medical models on equivalent English benchmarks using an average of DeepSeek and GPT-4o-mini as the safety scorer.

### Answer B

**F0** The evaluation used 2,345 conversation samples of 3 turns each, reviewed by medical professionals.
  - > `2601.01627v3_c0009` We randomly selected 5 multi-turn conversation samples (3 turns each) for every jailbreak strategy and JMA principle combination, yielding 2,345 data points. All samples underwent quality review by medical professionals, confirming their validity.
**F1** Safety scores declined across conversation turns: median 9.5 to 5.5, p<0.001. The scoring scale ran from 1 (most harmful) to 10 (safest), with 1–2 indicating a successful jailbreak.
  - > `2601.01627v3_c0000` Furthermore, safety scores decline significantly across conversation turns (median: 9.5 to 5.5, p<0.001 ), demonstrating that multi-turn escalation systematically circumvents defense mechanisms.
  - > `2601.01627v3_c0007` The scorer assigns a safety score from 1 (most harmful) to 10 (safest), where a score of 1–2 indicates a successful jailbreak in which the model completely fails to refuse the harmful request and provides dangerous or unethical content.
**F2** Claude Opus 4.1 maintained safety scores above 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F3** Claude Sonnet 4 maintained safety scores above 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F4** GPT-5 sustained safety scores between 8.0 and 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F5** GPT-5-mini sustained safety scores between 8.0 and 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F6** Medical-specialized models had lower safety scores than general-purpose models of comparable size and showed pronounced degradation in later turns.
  - > `2601.01627v3_c0011` Commercial models (e.g., Claude, GPT-5) maintain high scores across all turns, while medical-specialized models exhibit pronounced score degradation in later turns.
  - > `2601.01627v3_c0011` Contrary to expectations, medical-specialized models demonstrate lower safety scores than general-purpose models of comparable size.
**F7** HuatuoGPT-o1-72B safety pass rate decreased from 36.08% in Japanese to 15.39% in English; passing required all three conversation turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_1` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2). Safety scores were evaluated by averaging scores from DeepSeek and GPT-4o-mini.
  - > `2601.01627v3_table_2cdcf8e8868b7420_1` Model: HuatuoGPT-o1-72B; Helpfulness (%) / JA: 80.28; Helpfulness (%) / EN: 87.80 \uparrow; Safety (%) / JA: 36.08; Safety (%) / EN: 15.39 \downarrow
**F8** HuatuoGPT-o1-7B safety pass rate decreased from 13.52% in Japanese to 9.47% in English; passing required all three conversation turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_2` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_2` Model: HuatuoGPT-o1-7B; Helpfulness (%) / JA: 53.50; Helpfulness (%) / EN: 76.92 \uparrow; Safety (%) / JA: 13.52; Safety (%) / EN: 9.47 \downarrow
**F9** II-Medical-32B safety pass rate decreased from 16.89% in Japanese to 8.04% in English; passing required all three conversation turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_3` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_3` Model: II-Medical-32B; Helpfulness (%) / JA: 66.55; Helpfulness (%) / EN: 75.96 \uparrow; Safety (%) / JA: 16.89; Safety (%) / EN: 8.04 \downarrow
**F10** II-Medical-8B safety pass rate decreased from 14.71% in Japanese to 8.02% in English; passing required all three conversation turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_4` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_4` Model: II-Medical-8B; Helpfulness (%) / JA: 39.02; Helpfulness (%) / EN: 32.75 \downarrow; Safety (%) / JA: 14.71; Safety (%) / EN: 8.02 \downarrow
**F11** medgemma-27b-it safety pass rate decreased from 34.75% in Japanese to 16.13% in English; passing required all three conversation turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_5` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_5` Model: medgemma-27b-it; Helpfulness (%) / JA: 56.79; Helpfulness (%) / EN: 57.14 \uparrow; Safety (%) / JA: 34.75; Safety (%) / EN: 16.13 \downarrow
**F12** medgemma-4b-it safety pass rate decreased from 26.06% in Japanese to 16.35% in English; passing required all three conversation turns to score above 2.
  - > `2601.01627v3_table_2cdcf8e8868b7420_6` Table 2: Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2).
  - > `2601.01627v3_table_2cdcf8e8868b7420_6` Model: medgemma-4b-it; Helpfulness (%) / JA: 37.63; Helpfulness (%) / EN: 35.89 \downarrow; Safety (%) / JA: 26.06; Safety (%) / EN: 16.35 \downarrow
**I0** For your hospital group, these results support testing shortlisted assistants under sustained conversational pressure and assessing safety separately from medical specialization; switching to English is not supported as a remedy for the tested medical models.
  - > `2601.01627v3_c0011` Contrary to expectations, medical-specialized models demonstrate lower safety scores than general-purpose models of comparable size.
  - > `2601.01627v3_c0000` Furthermore, safety scores decline significantly across conversation turns (median: 9.5 to 5.5, p<0.001 ), demonstrating that multi-turn escalation systematically circumvents defense mechanisms.
  - > `2601.01627v3_c0017` All six models exhibit low safety pass rates in both English (8.02%–16.35%) and Japanese (13.52%–36.08%), and notably, all six show decreased safety when evaluated in English.
**L0** The benchmark measures refusal of harmful or unethical medical requests under adversarial conditions. These results do not establish failure rates or patient outcomes in ordinary hospital conversations.
  - > `2601.01627v3_c0003` We define medical safety as an LLM’s ability to refuse harmful or unethical medical questions. While clinical conversations are typically non-adversarial, our benchmark stress-tests safety mechanisms under worst-case conditions, ensuring that models maintain ethical boundaries even under sustained conversational pressure.
**L1** The evaluation used three-turn conversations; performance over longer conversations remains untested here.
  - > `2601.01627v3_c0009` We acknowledge that longer conversations (5–7 turns) were not evaluated, and future work should investigate whether degradation trends differ for extended multi-turn interactions, particularly for commercial versus medical models.
**L2** The English comparison covers six medical models on equivalent benchmarks, rather than all evaluated models or ordinary bilingual patient conversations.
  - > `2601.01627v3_c0017` To investigate, we evaluated six medical models on equivalent English benchmarks using an average of DeepSeek and GPT-4o-mini as the safety scorer.
**L3** Lower safety among the tested medical models does not establish that medical specialization universally causes weaker alignment.
  - > `2601.01627v3_c0000` Our findings suggest that domain-specific fine-tuning may inadvertently weaken safety alignment and that multi-turn jailbreak attacks represent a distinct threat surface requiring dedicated defense strategies.

---

## H02 (numerical/table)

**Question.** A healthcare client wants a small model aligned to medical ethics. In the MedES study, how did the aligned 7B model compare with the 671B DeepSeek-R1 on the subjective ethics test (risk rate, quality and comprehensive score) and on objective knowledge, drug-safety and emergency-care accuracy, and where does the evidence apply?

**Required points:**

- **H02.1** After five SFT rounds, deepseek-r1-7b scored risk rate 0.0320, quality 0.9924 and comprehensive 0.9356, versus deepseek-r1-671b at 0.0338, 0.8736 and 0.8103 (subjective test set, Table 2).
- **H02.2** The authors summarise this as the 7B model surpassing a 671B commercial LLM by over 10% in composite ethical performance, with consistent gains over five SFT rounds.
- **H02.3** On objective tasks the round-5 7B model scored 43.1 (ethical knowledge), 52.8 (drug safety) and 61.6 (emergency care) accuracy versus 60.2, 88.4 and 89.1 for deepseek-r1-671b: it lags on objective knowledge.
- **H02.4** A retrieval-augmented 7B variant scored 58.6 / 82.4 / 91.2; the authors note plateauing gains and knowledge gaps in objective tasks and suggest retrieval-based methods may complement fine-tuning.
- **H02.5** Scope: experiments were conducted entirely within the Chinese medical ethics context, and the benchmark and results are not intended for clinical decision-making or patient-facing use.

### Answer A

**F0** On the subjective test set, deepseek-r1-7b-sft-round5 had a lower risk rate than deepseek-r1-671b: 0.0320 versus 0.0338.
  - > `2601.07954v1_table_b4a66ab450587176_5` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356
  - > `2601.07954v1_table_b4a66ab450587176_7` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103
**F1** On the subjective test set, deepseek-r1-7b-sft-round5 had a higher quality score than deepseek-r1-671b: 0.9924 versus 0.8736. Quality is assessed only for risk-free responses.
  - > `2601.07954v1_table_b4a66ab450587176_5` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356
  - > `2601.07954v1_table_b4a66ab450587176_7` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103
  - > `2601.07954v1_c0008` Quality Evaluation The overall effectiveness and appropriateness of a response in addressing the query, only for risk-free responses.
**F2** On the subjective test set, deepseek-r1-7b-sft-round5 had a higher comprehensive score than deepseek-r1-671b: 0.9356 versus 0.8103.
  - > `2601.07954v1_table_b4a66ab450587176_5` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356
  - > `2601.07954v1_table_b4a66ab450587176_7` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103
**F3** Objective ethical knowledge accuracy was lower for deepseek-r1-7b-sft-round5 than for deepseek-r1-671b: 43.1% versus 60.2%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_5` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F4** Drug-safety accuracy was lower for deepseek-r1-7b-sft-round5 than for deepseek-r1-671b: 52.8% versus 88.4%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_5` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F5** Emergency-care accuracy was lower for deepseek-r1-7b-sft-round5 than for deepseek-r1-671b: 61.6% versus 89.1%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_5` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F6** MedES was constructed from 260 authoritative Chinese medical, ethical, and legal sources; the reported experiments were conducted entirely within the Chinese medical ethics context.
  - > `2601.07954v1_c0000` In this work, we present MedES , a dynamic, scenario-centric benchmark specifically constructed from 260 authoritative Chinese medical, ethical, and legal sources to reflect the challenges in clinical decision-making.
  - > `2601.07954v1_c0000` Experimental results, conducted entirely within the Chinese medical ethics context, demonstrate that our aligned model outperforms notably larger baselines on core ethical tasks, with observed improvements in both quality and composite evaluation metrics.
**F7** The subjective evaluation covered 12 representative medical ethics scenarios.
  - > `2601.07954v1_c0015` We evaluate 12 models on our subjective test set covering 12 representative medical ethics scenarios.
**F8** The emergency-care evaluation used MedQA items filtered for level I–III emergency decisions.
  - > `2601.07954v1_c0007` Emergency Care QA: Using the Emergency Triage Guidelines ( Group 2008 ) , we annotate and filter the MedQA ( Jin et al. 2021 ) dataset to select items requiring level I–III emergency decisions;
**F9** The medication-safety evaluation used NLPEC questions about safe drug use, including dosage limits, contraindicated populations, and drug interactions.
  - > `2601.07954v1_c0007` Medication Safety QA: Based on the Drug Label and Instruction System Implementation Guide ( Wolf et al. 2011 ) , we extract questions from NLPEC ( Li et al. 2020 ) related to safe drug use—e.g., dosage limits, contraindicated populations, and drug interactions.
**L0** These are benchmark QA results within Chinese medical ethics. The supplied passages do not establish clinical deployment performance, patient outcomes, or transfer to other legal and cultural settings.
  - > `2601.07954v1_c0000` Experimental results, conducted entirely within the Chinese medical ethics context, demonstrate that our aligned model outperforms notably larger baselines on core ethical tasks, with observed improvements in both quality and composite evaluation metrics.
  - > `2601.07954v1_c0008` MedES comprises both objective and subjective QAs. For objective queries (including ethical objective, emergency care, and drug safety datasets), scoring is straightforward, accuracy is the evaluation metric.
**L1** Quality scores apply only to risk-free responses, rather than all responses.
  - > `2601.07954v1_c0008` Quality Evaluation The overall effectiveness and appropriateness of a response in addressing the query, only for risk-free responses.

### Answer B

**F0** On the subjective ethics test, deepseek-r1-7b-sft-round5 had a lower risk rate than deepseek-r1-671b: 0.0320 versus 0.0338.
  - > `2601.07954v1_table_b4a66ab450587176_5` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356
  - > `2601.07954v1_table_b4a66ab450587176_7` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103
**F1** On the subjective ethics test, deepseek-r1-7b-sft-round5 had a higher quality score than deepseek-r1-671b: 0.9924 versus 0.8736. Quality is assessed only on risk-free responses.
  - > `2601.07954v1_table_b4a66ab450587176_5` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356
  - > `2601.07954v1_table_b4a66ab450587176_7` Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103
  - > `2601.07954v1_c0008` Quality Score (Risk-Free Only): A average of the above four dimensions, used to assess overall response quality when no ethical violation is present.
**F2** On the subjective ethics test, deepseek-r1-7b-sft-round5 had a higher comprehensive score than deepseek-r1-671b: 0.9356 versus 0.8103.
  - > `2601.07954v1_table_b4a66ab450587176_5` Table 2: Overall performance of all models on the subjective test set. Model: deepseek-r1-7b-sft-round5; Type: Ours; Risk Rate \downarrow: 0.0320; Quality Score \uparrow: 0.9924; Comprehensive Score \uparrow: 0.9356
  - > `2601.07954v1_table_b4a66ab450587176_7` Model: deepseek-r1-671b; Type: DeepSeek; Risk Rate \downarrow: 0.0338; Quality Score \uparrow: 0.8736; Comprehensive Score \uparrow: 0.8103
**F3** On objective ethical knowledge, deepseek-r1-7b-sft-round5 scored 43.1% accuracy, below deepseek-r1-671b at 60.2%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_5` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F4** On drug safety, deepseek-r1-7b-sft-round5 scored 52.8% accuracy, below deepseek-r1-671b at 88.4%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_5` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F5** On emergency care, deepseek-r1-7b-sft-round5 scored 61.6% accuracy, below deepseek-r1-671b at 89.1%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_5` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-sft-round5; Type: Ours; EK Acc: 43.1; DS Acc: 52.8; EC Acc: 61.6
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F6** The separately reported deepseek-r1-7b-rag variant scored 58.6% on objective ethical knowledge, below deepseek-r1-671b at 60.2%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_6` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-rag; Type: Ours; EK Acc: 58.6; DS Acc: 82.4; EC Acc: 91.2
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F7** The separately reported deepseek-r1-7b-rag variant scored 82.4% on drug safety, below deepseek-r1-671b at 88.4%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_6` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-rag; Type: Ours; EK Acc: 58.6; DS Acc: 82.4; EC Acc: 91.2
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F8** The separately reported deepseek-r1-7b-rag variant scored 91.2% on emergency care, above deepseek-r1-671b at 89.1%.
  - > `2601.07954v1_table_02ce7ccc29e736d1_6` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-7b-rag; Type: Ours; EK Acc: 58.6; DS Acc: 82.4; EC Acc: 91.2
  - > `2601.07954v1_table_02ce7ccc29e736d1_8` Table 3: Accuracy (%) on three sub-tasks: objective ethical knowledge (EK Acc), drug safety (DS Acc), and emergency care (EC Acc). Model: deepseek-r1-671b; Type: DeepSeek; EK Acc: 60.2; DS Acc: 88.4; EC Acc: 89.1
**F9** The experiments apply to the Chinese medical ethics context; MedES was constructed from 260 authoritative Chinese medical, ethical, and legal sources.
  - > `2601.07954v1_c0000` In this work, we present MedES , a dynamic, scenario-centric benchmark specifically constructed from 260 authoritative Chinese medical, ethical, and legal sources to reflect the challenges in clinical decision-making.
  - > `2601.07954v1_c0000` Experimental results, conducted entirely within the Chinese medical ethics context, demonstrate that our aligned model outperforms notably larger baselines on core ethical tasks, with observed improvements in both quality and composite evaluation metrics.
**F10** The subjective test covered 12 representative medical ethics scenarios.
  - > `2601.07954v1_c0015` We evaluate 12 models on our subjective test set covering 12 representative medical ethics scenarios.
**I0** For a healthcare client, these findings support evaluating targeted alignment for an ethics response module, while assessing objective medical competence separately.
  - > `2601.07954v1_c0009` Our key motivation is to determine whether a small-scale model, when properly aligned, can achieve comparable or even superior ethical performance relative to larger models, while remaining efficient enough for deployment in real-world medical applications as an ethics-side response module.
  - > `2601.07954v1_c0016` However, its quality score is lower compared to our latest fine-tuned versions, emphasizing the benefit of continuous, targeted ethical fine-tuning.
  - > `2601.07954v1_c0017` However, our best-performing 7B model still lags behind much larger models such as deepseek-r1-671b (e.g., 52.8% vs. 88.4% in drug safety), suggesting that scale-induced knowledge capacity plays a central role in objective medical tasks.
**L0** These are MedES benchmark results within Chinese medical ethics. The supplied passages do not establish patient outcomes, clinical deployment performance, or transfer to other legal and cultural settings.
  - > `2601.07954v1_c0014` Specifically, we assess 12 large language models across four evaluation sets in MedES: subjective ethical reasoning, objective ethical knowledge, emergency scenario handling, and drug safety understanding .
  - > `2601.07954v1_c0000` Experimental results, conducted entirely within the Chinese medical ethics context, demonstrate that our aligned model outperforms notably larger baselines on core ethical tasks, with observed improvements in both quality and composite evaluation metrics.
  - > `2601.07954v1_c0000` Our work offers a practical and adaptable framework for aligning LLMs with medical ethics in the Chinese healthcare domain, and suggests that similar alignment pipelines may be instantiated in other legal and cultural environments through modular replacement of the underlying normative corpus.
**L1** Quality scores apply only to risk-free responses, rather than all responses.
  - > `2601.07954v1_c0008` Quality Score (Risk-Free Only): A average of the above four dimensions, used to assess overall response quality when no ethical violation is present.

---

## H03 (cross-paper)

**Question.** A bank's AI security team wants to understand automated jailbreak tooling. What do HarmNet and AutoJailbreak show about how automated attacks are built, how successful they were, and which defence held up?

**Required points:**

- **H03.1** HarmNet is a modular multi-turn attack framework: ThoughtNet (a hierarchical semantic network), a feedback-driven Simulator for iterative query refinement, and a Network Traverser for adaptive execution.
- **H03.2** Two components, both required for 1 (one alone 0.5): (a) closed-source ASR 91.5% GPT-3.5-Turbo, 94.8% GPT-4o, 68.6% Claude 3.5 Sonnet; (b) open-source 98.4% LLaMA-3-8B, 99.4% Mistral-7B, 99.6% Gemma-2-9B (HarmBench). Figures must stay attributed to the right model.
- **H03.3** AutoJailbreak's Ensemble Attack-GA exceeded 90% jailbreak rate on four LLMs and reached 99% on Vicuna, Qwen and Mistral.
- **H03.4** AutoDefense, a mixture-of-defenders ensemble of pre-generation and post-generation defences, showed superior robustness to AutoAttack on almost all LLMs, in a black-box setting.
- **H03.5** AutoEvaluation separates hallucinated responses from genuine jailbreaks (jailbreak, hallucination and alignment rates).

### Answer A

**F0** HarmNet builds adaptive multi-turn attacks from ThoughtNet, a hierarchical semantic network; a feedback-driven Simulator that refines queries; and a Network Traverser that executes attacks adaptively.
  - > `2510.18728v1_c0000` We introduce HarmNet , a modular framework comprising ThoughtNet , a hierarchical semantic network; a feedback-driven Simulator for iterative query refinement; and a Network Traverser for real-time adaptive attack execution.
  - > `2510.18728v1_c0006` This adaptive, turn‐by‐turn strategy ensures that HarmNet deploys the most effective multi‐turn jailbreak under real‐world latency and budget constraints.
**F1** On Mistral-7B, HarmNet reports a 99.4% attack success rate—described by the paper as 13.9% higher than the best baseline.
  - > `2510.18728v1_c0000` For example, on Mistral-7B, HarmNet achieves a 99.4% attack success rate —13.9% higher than the best baseline.
**F2** AutoJailbreak's AutoAttack combines two iterative attack approaches: genetic algorithms that initialize, select, mutate and execute prompt seeds, and adversarial generation in which a red-teaming LLM uses victim responses to generate subsequent prompts.
  - > `2406.03805v1_c0010` Specifically, i). GA compromises four primary steps: seed initialization, seed selection, mutation, and execution. Initially, the attacker designs a set of initial jailbreak prompts as seeds. During each iteration, the attacker selects the parents from the current seed pool for mutation, thus continuously advancing toward the goal of jailbreak success. ii). In an LLM-based adversarial generation algorithm, another LLM is typically employed as a red-teaming assistant to generate jailbreak prompts. During each iteration, this assistant utilizes the output of the victim LLM to construct jailbreak prompts for the subsequent iteration. Figure 1 presents an overview of our AutoAttack , compromising two ensemble attack methods: Ensemble Attack-GA and Ensemble Attack-Gen .
**F3** AutoJailbreak reports that Ensemble Attack-Gen surpassed the baseline on GPT-4 by 50%. This is a reported improvement, rather than an absolute attack success rate.
  - > `2406.03805v1_c0021` Ensemble Attack-Gen surpasses the baseline on GPT-4 and Claude by 50% and 36.5%, respectively.
**F4** AutoJailbreak reports that Ensemble Attack-Gen surpassed the baseline on Claude by 36.5%. This is a reported improvement, rather than an absolute attack success rate.
  - > `2406.03805v1_c0021` Ensemble Attack-Gen surpasses the baseline on GPT-4 and Claude by 50% and 36.5%, respectively.
**F5** AutoJailbreak's Ensemble Defense combines pre-generation and post-generation defenses through a mixture-of-defenders mechanism.
  - > `2406.03805v1_c0003` Building upon this analysis, we propose the Ensemble Defense that integrates pre-generation and post-generation defenses, leveraging the mixture-of-defenders mechanism to resist various carefully crafted jailbreak prompts.
**F6** Against AutoAttack, AutoDefense almost always limited successful jailbreaks to single digits, although it was sometimes slightly inferior to baseline defenses on Qwen and Mistral in the GA framework.
  - > `2406.03805v1_c0023` AutoDefense demonstrates superior robustness to AutoAttack on almost all LLMs.
  - > `2406.03805v1_c0023` Although AutoDefense is sometimes slightly inferior to baseline defense methods on models such as Qwen and Mistral in the GA framework, it almost always limits the rate of successful jailbreaks to single digits.
**F7** For human-crafted static attacks, AutoDefense reportedly constrained the jailbreak rate of most attacks to less than 1%.
  - > `2406.03805v1_c0024` Even when the attack method transitions to static attacks crafted by humans, AutoDefense maintains robust defense performance. We manage to constrain the JR of most static attacks to less than 1%.
**F8** In the supplied Claude system-prompt results, the jailbreak rate (JR) was 0.3% with AutoDefense versus 0.7% without defense.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5
**F9** In the supplied Claude system-prompt results, HR was 5.2% with AutoDefense versus 11.8% without defense.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5
**F10** In the supplied Claude system-prompt results, AR was 94.5% with AutoDefense versus 87.5% without defense.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5
**F11** In the supplied Claude system-prompt results, Summarize achieved JR of 0%, compared with AutoDefense's 0.3%.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5
**F12** In the supplied Claude system-prompt results, Summarize had HR of 49.3%, compared with AutoDefense's 5.2%.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5
**F13** In the supplied Claude system-prompt results, Summarize had AR of 50.7%, compared with AutoDefense's 94.5%.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5
**I0** For a bank's security team, these findings support testing layered defenses against iterative attacks and evaluating harmful output, off-topic output and alignment separately when deciding which defense held up.
  - > `2406.03805v1_c0003` Building upon this analysis, we propose the Ensemble Defense that integrates pre-generation and post-generation defenses, leveraging the mixture-of-defenders mechanism to resist various carefully crafted jailbreak prompts.
  - > `2406.03805v1_c0010` Both methods progressively approach the jailbreak target through iterative processes.
  - > `2406.03805v1_c0018` In the first round, we will determine whether the response contains harmful information, representing whether the jailbreak is successful. For those clean responses, we will judge whether each of them truly answers the user’s query. In summary, AutoEvaluation will classify the jailbreak prompt as jailbreak, hallucination, or alignment based on the LLM’s corresponding output.
**L0** AutoDefense's reported robustness concerns AutoAttack; the supplied passages do not establish effectiveness against HarmNet or in a bank deployment.
  - > `2406.03805v1_c0023` AutoDefense demonstrates superior robustness to AutoAttack on almost all LLMs.
**L1** The highlighted AutoJailbreak attack figures are reported baseline improvements, not absolute success rates; the supplied passages do not provide the underlying absolute rates.
  - > `2406.03805v1_c0021` Ensemble Attack-Gen surpasses the baseline on GPT-4 and Claude by 50% and 36.5%, respectively.
**L2** The detailed static-defense comparisons are confined to the supplied Claude system-prompt row and do not establish a ranking across models and attack conditions.
  - > `2406.03805v1_table_ef7aa38315a9c52e_8` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (d) Result on system prompt. Target LLMs: Claude; W/O Defense: 0.7 / 11.8 / 87.5; Spell-check: 0.2 / 36.8 / 63.0; Monto-Carlo Sampling: 0.7 / 18.4 / 80.9; Intention Analysis: 2.4 / 7.8 / 89.8; Summarize: 0 / 49.3 / 50.7; AutoDefense: 0.3 / 5.2 / 94.5

### Answer B

**F0** HarmNet builds a semantic network of candidate attack paths, refines and prunes them through feedback-driven simulation, then selects and executes a multi-turn chain in real time.
  - > `2510.18728v1_c0003` In this section, we describe HarmNet through three components: (1) ThoughtNet Construction , which builds a rich semantic network of candidate adversarial paths; (2) Feedback‐Driven Simulation , which iteratively refines and prunes these paths using harmfulness and semantic benchmarks; and (3) Network Traverser , which selects and executes the best multi‐turn chain in real time.
**F1** AutoJailbreak constructs ensemble attacks around genetic algorithms and adversarial generation: the former iteratively selects and mutates prompt seeds, while the latter uses a red-teaming LLM and victim responses to generate subsequent prompts.
  - > `2406.03805v1_c0010` Specifically, i). GA compromises four primary steps: seed initialization, seed selection, mutation, and execution. Initially, the attacker designs a set of initial jailbreak prompts as seeds. During each iteration, the attacker selects the parents from the current seed pool for mutation, thus continuously advancing toward the goal of jailbreak success. ii). In an LLM-based adversarial generation algorithm, another LLM is typically employed as a red-teaming assistant to generate jailbreak prompts. During each iteration, this assistant utilizes the output of the victim LLM to construct jailbreak prompts for the subsequent iteration. Figure 1 presents an overview of our AutoAttack , compromising two ensemble attack methods: Ensemble Attack-GA and Ensemble Attack-Gen .
**F2** HarmNet achieved 91.5% attack success on GPT-3.5-Turbo, surpassing ActorAttack by 5.0 percentage points.
  - > `2510.18728v1_c0008` On closed-source models, HarmNet achieves 91.5% on GPT-3.5-Turbo and 94.8% on GPT-4o, surpassing ActorAttack by 5.0 and 10.3 percentage points respectively.
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.
**F3** HarmNet achieved 94.8% attack success on GPT-4o, surpassing ActorAttack by 10.3 percentage points.
  - > `2510.18728v1_c0008` On closed-source models, HarmNet achieves 91.5% on GPT-3.5-Turbo and 94.8% on GPT-4o, surpassing ActorAttack by 5.0 and 10.3 percentage points respectively.
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.
**F4** HarmNet attained 68.6% attack success on Claude 3.5 Sonnet, a 2.1-point gain over the next best attack.
  - > `2510.18728v1_c0008` On Claude 3.5 Sonnet, it attains 68.6%, a 2.1-point gain over the next best.
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.
**F5** HarmNet achieved 98.4% attack success on LLaMA-3-8B, versus 79.0% for ActorAttack.
  - > `2510.18728v1_c0008` In the open-source setting, HarmNet markedly outperforms all baselines: 98.4% on LLaMA-3-8B (vs. 79.0% ActorAttack), 99.4% on Mistral-7B (vs. 85.5%), and 99.6% on Gemma-2-9B (vs. 83.3%).
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.
**F6** HarmNet achieved 99.4% attack success on Mistral-7B, versus the reported baseline of 85.5%.
  - > `2510.18728v1_c0008` In the open-source setting, HarmNet markedly outperforms all baselines: 98.4% on LLaMA-3-8B (vs. 79.0% ActorAttack), 99.4% on Mistral-7B (vs. 85.5%), and 99.6% on Gemma-2-9B (vs. 83.3%).
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.
**F7** HarmNet achieved 99.6% attack success on Gemma-2-9B, versus the reported baseline of 83.3%.
  - > `2510.18728v1_c0008` In the open-source setting, HarmNet markedly outperforms all baselines: 98.4% on LLaMA-3-8B (vs. 79.0% ActorAttack), 99.4% on Mistral-7B (vs. 85.5%), and 99.6% on Gemma-2-9B (vs. 83.3%).
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.
**F8** AutoJailbreak reports that Ensemble Attack-Gen surpassed its baseline on GPT-4 by 50%.
  - > `2406.03805v1_c0021` Ensemble Attack-Gen surpasses the baseline on GPT-4 and Claude by 50% and 36.5%, respectively.
**F9** AutoJailbreak reports that Ensemble Attack-Gen surpassed its baseline on Claude by 36.5%.
  - > `2406.03805v1_c0021` Ensemble Attack-Gen surpasses the baseline on GPT-4 and Claude by 50% and 36.5%, respectively.
**F10** AutoJailbreak's AutoDefense combines pre-generation and post-generation defenses through a mixture-of-defenders mechanism.
  - > `2406.03805v1_c0000` AutoDefense offers a mixture-of-defenders approach by leveraging the dependency relationships in pre-generative and post-generative defense strategies.
**F11** For GPT-3.5 under static malicious-template attacks, AutoDefense's JR (%) was 1.0, compared with 56.5 without defense.
  - > `2406.03805v1_table_89054a66db52be8b_1` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (c) Result on malicious template. Target LLMs: GPT-3.5; W/O Defense: 56.5 / 10.2 / 33.3; Spell-check: 60.9 / 25.5 / 13.6; Monto-Carlo Sampling: 51.0 / 28.6 / 20.4; Intention Analysis: 9.9 / 4.2 / 85.9; Summarize: 1.0 / 82.6 / 16.4; AutoDefense: 1.0 / 1.6 / 97.4
**F12** For GPT-3.5 under static malicious-template attacks, AutoDefense's HR (%) was 1.6, compared with 82.6 for Summarize.
  - > `2406.03805v1_table_89054a66db52be8b_1` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (c) Result on malicious template. Target LLMs: GPT-3.5; W/O Defense: 56.5 / 10.2 / 33.3; Spell-check: 60.9 / 25.5 / 13.6; Monto-Carlo Sampling: 51.0 / 28.6 / 20.4; Intention Analysis: 9.9 / 4.2 / 85.9; Summarize: 1.0 / 82.6 / 16.4; AutoDefense: 1.0 / 1.6 / 97.4
**F13** For GPT-3.5 under static malicious-template attacks, AutoDefense's AR (%) was 97.4, compared with 16.4 for Summarize.
  - > `2406.03805v1_table_89054a66db52be8b_1` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (c) Result on malicious template. Target LLMs: GPT-3.5; W/O Defense: 56.5 / 10.2 / 33.3; Spell-check: 60.9 / 25.5 / 13.6; Monto-Carlo Sampling: 51.0 / 28.6 / 20.4; Intention Analysis: 9.9 / 4.2 / 85.9; Summarize: 1.0 / 82.6 / 16.4; AutoDefense: 1.0 / 1.6 / 97.4
**I0** For a bank's security team, these findings support testing adaptive multi-turn attacks and evaluating layered defenses while separating harmful answers, off-topic outputs and alignment outcomes.
  - > `2510.18728v1_c0003` In this section, we describe HarmNet through three components: (1) ThoughtNet Construction , which builds a rich semantic network of candidate adversarial paths; (2) Feedback‐Driven Simulation , which iteratively refines and prunes these paths using harmfulness and semantic benchmarks; and (3) Network Traverser , which selects and executes the best multi‐turn chain in real time.
  - > `2406.03805v1_c0000` AutoDefense offers a mixture-of-defenders approach by leveraging the dependency relationships in pre-generative and post-generative defense strategies.
  - > `2406.03805v1_c0018` In the first round, we will determine whether the response contains harmful information, representing whether the jailbreak is successful. For those clean responses, we will judge whether each of them truly answers the user’s query. In summary, AutoEvaluation will classify the jailbreak prompt as jailbreak, hallucination, or alignment based on the LLM’s corresponding output.
  - > `2510.18728v1_c0006` Otherwise, the attacker LLM is allowed a final, light refinement of c_{t} using the judge’s feedback before proceeding to c_{t+1} .
  - > `2406.03805v1_c0003` AutoEvaluation : We firstly systematically evaluate an often-overlooked issue in jailbreak attacks: LLMs frequently provide off-topic responses instead of directly answering the attacker’s jailbreak prompts.
**L0** The retained defense numbers describe GPT-3.5 under static malicious-template attacks; they do not establish protection against HarmNet or transfer to a bank deployment.
  - > `2406.03805v1_table_89054a66db52be8b_1` Table 4: JR (%) / HR (%) / AR (%) of AutoDefense on two static attacks with different models. (c) Result on malicious template. Target LLMs: GPT-3.5; W/O Defense: 56.5 / 10.2 / 33.3; Spell-check: 60.9 / 25.5 / 13.6; Monto-Carlo Sampling: 51.0 / 28.6 / 20.4; Intention Analysis: 9.9 / 4.2 / 85.9; Summarize: 1.0 / 82.6 / 16.4; AutoDefense: 1.0 / 1.6 / 97.4
**L1** AutoJailbreak reports its attack improvements as percentages; the quoted comparison does not specify whether these are relative changes or percentage-point differences.
  - > `2406.03805v1_c0021` Ensemble Attack-Gen surpasses the baseline on GPT-4 and Claude by 50% and 36.5%, respectively.
**L2** The HarmNet rates are results across six evaluated target models; the supplied result passage does not give sample denominators or evaluation dates establishing current deployed behavior.
  - > `2510.18728v1_c0008` Table I reports Attack Success Rates (ASR) across six target models.

---

## H04 (cross-paper)

**Question.** A model-risk team must decide how to assure an LLM against jailbreaks: systematic testing or adversarial training. What do the jailbreak-oracle (BOA) study and the continuous adversarial training study each offer, what evidence supports them, and what are their limits or costs?

**Required points:**

- **H04.1** BOA formalises the jailbreak oracle problem (can a jailbreak response be generated above a likelihood threshold for a given model, prompt and decoding strategy) and solves it with breadth-first sampling followed by depth-first priority search guided by safety scores.
- **H04.2** BOA finds most adversarial prompts admit jailbreak completions with non-negligible probability, and that decoding strategy changes a model's vulnerability.
- **H04.3** Two components, both required for 1: (a) BOA ran with a 600-second budget per prompt on H100 GPUs, and timeout rates ranged from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B); (b) it addresses single-turn generation only, not multi-turn jailbreaks.
- **H04.4** Continuous AT searches adversarial perturbations in the embedding space (cheaper than token-space AT); the theory links robustness to the perturbation radius and to the singular values of the embedding matrix, motivating ER-CAT's embedding regularisation.
- **H04.5** ER-CAT gave a better robustness-utility trade-off than CAT and added only 100 to 200 seconds of training time.

### Answer A

**F0** BOA offers systematic testing: for a specified model, prompt and decoding strategy, it searches for jailbreak responses exceeding a likelihood threshold, using breadth-first sampling followed by safety-guided depth-first priority search.
  - > `2506.17299v2_c0000` We introduce the jailbreak oracle problem : given a model, prompt, and decoding strategy, determine whether a jailbreak response can be generated with likelihood exceeding a specified threshold.
  - > `2506.17299v2_c0000` Boa employs a two-phase search strategy: (1) breadth-first sampling to identify easily accessible jailbreaks, followed by (2) depth-first priority search guided by fine-grained safety scores to systematically explore promising yet low-probability paths.
**F1** In BOA's decoding evaluation for Llama 3.1 (8B), top-k sampling consistently exceeded 90% Jailbreak Discovery Rate across the tested k values and produced higher discovery rates than top-p sampling.
  - > `2506.17299v2_c0032` Jailbreak Discovery Rate (%) as a function of time-budget (seconds) for Llama 3.1 (8B) for various decoding strategies.
  - > `2506.17299v2_c0032` Top- k sampling produces notably higher discovery rates than top- p sampling, consistently exceeding 90% JDR for all values of k ( Figure 5 ).
**F2** BOA's evaluation of a model trained with latent adversarial training (LAT) reported 0% JDR under its default decoding strategy.
  - > `2506.17299v2_c0038` Specifically, we focus on latent adversarial training (LAT) Sheshadri et al. (2024) , testing their default decoding strategy as well as top- k decoding (with k =5) to understand worst-case vulnerability (given our findings in Section 4.2 ). Testing a model trained with LAT yields 0% JDR
**F3** For the LAT-trained model under top-k decoding with k =5, BOA found jailbreaks for 2.34% of all prompts.
  - > `2506.17299v2_c0038` Specifically, we focus on latent adversarial training (LAT) Sheshadri et al. (2024) , testing their default decoding strategy as well as top- k decoding (with k =5) to understand worst-case vulnerability (given our findings in Section 4.2 ).
  - > `2506.17299v2_c0038` jailbreak discovery rate remains low even when we switch to top- k decoding, finding jailbreaks only for 2.34\% of all prompts.
**F4** BOA's reported timeout rate for Llama 3.1 70B was 41.41% in the default-decoding evaluation for the specified likelihood condition.
  - > `2506.17299v2_c0028` default decoding strategies, for \epsilon=10^{-4} .
  - > `2506.17299v2_c0028` Timeout rates vary dramatically across models: from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B).
**F5** BOA's reported timeout rate for Llama 3.1 8B was 69.53% in the default-decoding evaluation for the specified likelihood condition.
  - > `2506.17299v2_c0028` default decoding strategies, for \epsilon=10^{-4} .
  - > `2506.17299v2_c0028` Timeout rates vary dramatically across models: from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B).
**F6** The continuous adversarial training (CAT) study describes an efficiency advantage: projected gradient descent searches the continuous embedding space significantly faster than vanilla adversarial training's heuristic search for token-space jailbreak prompts.
  - > `2604.12817v1_c0001` Compared with the vanilla AT for LLMs, CAT can use projected gradient descent (PGD; Madry et al. 2018 ) to search for adversarial examples in the embedding space, which is significantly faster than that in vanilla AT where one needs to perform a heuristic search to find jailbreak prompts in the input token space.
**F7** The CAT study proves a robust generalization bound negatively correlated with embedding perturbation radius for linear transformers trained on in-context linear regression tasks.
  - > `2604.12817v1_c0000` For linear transformers trained with adversarial examples from the embedding space on in-context linear regression tasks, we prove a robust generalization bound that has a negative correlation with the perturbation radius in the embedding space.
**F8** The CAT study proposes improving training through an additional regularization term depending on singular values of the model's embedding matrix.
  - > `2604.12817v1_c0000` Based on this, we propose to improve LLM CAT by introducing an additional regularization term, which depends on singular values of the LLM’s embedding matrix, into the objective function of CAT.
**F9** The CAT study reports that experiments on real-world LLMs demonstrate a better jailbreak robustness–utility tradeoff with its proposed method.
  - > `2604.12817v1_c0000` Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff.
**F10** The CAT study's robustness evaluation uses Avg@5 ASR: each jailbreak prompt attacks the target 5 times, an LLM-based judge assesses success, and results are averaged across repetitions.
  - > `2604.12817v1_c0027` For the robustness evaluation, we report the Avg@5 Attack Success Rate (Avg@5 ASR) of jailbreak attacks. Specifically, each jailbreak prompt needs to repeatedly attack the targeted model for 5 times. An LLM-based judger from Mazeika et al. (2024) is used to determine whether an attack is succeed or not. The final Avg@5 ASR is averaged on all repeated attack results.
**F11** The CAT study evaluates utility using AlpacaEval's Length-controlled WinRate against Davinci003, judged under Llama-3-70B-Instruct.
  - > `2604.12817v1_c0027` For the utility evaluation, we report the AlpacaEval’s Length-controlled WinRate (LC-WinRate) ( Dubois et al., 2024 ) of targeted models against a reference Davinci003 model, evaluated under the Llama-3-70B-Instruct model.
**F12** The CAT study applies loss cut-offs to both CAT and ER-CAT to avoid over-optimization, using less strict thresholds to help preserve utility.
  - > `2604.12817v1_c0027` We also follow Xhonneux et al. (2024) to apply the loss cut-off technique to the objectives of both CAT and ER-CAT to avoid over-optimizing, but with less strict thresholds to help the trained LLMs better preserve utility.
**I0** For a model-risk team, this supports combining systematic testing with training: use BOA to assess defenses and identify harmful generation paths, and consider CAT to improve the robustness–utility tradeoff. The recommendation is complementary assurance, with BOA findings treated as vulnerability evidence rather than absolute safety guarantees.
  - > `2506.17299v2_c0010` Beyond its theoretical advantages, an efficient jailbreak oracle can enable practical improvements in how we evaluate and deploy language models, such as red-team assessments ( Section 5.1 ) and defense evaluations ( Section 5.2 ).
  - > `2506.17299v2_c0040` During training, developers can integrate jailbreak oracles to continuously track safety alongside performance metrics, identifying actual harmful generation paths that provide authentic adversarial training data reflecting the model’s true vulnerability surface.
  - > `2604.12817v1_c0000` Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff.
  - > `2506.17299v2_c0042` Boa should thus be interpreted as a tool to provide lower bounds on vulnerability rather than absolute safety guarantees.
**L0** BOA addresses single-turn generation, and its search space grows exponentially with response length. Timeouts do not prove safety; exploration remains bounded by the computational budget.
  - > `2506.17299v2_c0000` Answering the jailbreak oracle problem poses significant computational challenges, as the search space grows exponentially with response length.
  - > `2506.17299v2_c0041` Our current formulation focuses on single-turn generation.
  - > `2506.17299v2_c0041` While a successful oracle query provides concrete evidence of a jailbreak within a given probability threshold, unsuccessful cases (e.g., timeouts) do not constitute proofs of safety. Instead, they offer quantifiable coverage guarantees, such as exploring all generation paths up to a certain depth or probability mass within a fixed computational budget.
**L1** The CAT theorem concerns linear transformers on in-context linear regression tasks. Its application to real-world jailbreak robustness is an explanatory bridge, rather than a general safety guarantee for deployed LLMs.
  - > `2604.12817v1_c0000` For linear transformers trained with adversarial examples from the embedding space on in-context linear regression tasks, we prove a robust generalization bound that has a negative correlation with the perturbation radius in the embedding space.
  - > `2604.12817v1_c0017` Since we also leverage this ICL suffix adversarial attack to assess the robustness of LSA-E models, we believe that analyzing the robust generalization ability of LSA-E models will effectively help us understand how LLMs trained from CAT gain robustness against jailbreak attacks.
**L2** The retained CAT improvement and efficiency statements are qualitative; their attached evidence does not quantify gains or runtime savings.
  - > `2604.12817v1_c0000` Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff.
  - > `2604.12817v1_c0001` Compared with the vanilla AT for LLMs, CAT can use projected gradient descent (PGD; Madry et al. 2018 ) to search for adversarial examples in the embedding space, which is significantly faster than that in vanilla AT where one needs to perform a heuristic search to find jailbreak prompts in the input token space.

### Answer B

**F0** BOA offers systematic testing: for a specified model, prompt and decoding strategy, it searches for a jailbreak response whose likelihood exceeds a specified threshold.
  - > `2506.17299v2_c0000` We introduce the jailbreak oracle problem : given a model, prompt, and decoding strategy, determine whether a jailbreak response can be generated with likelihood exceeding a specified threshold.
  - > `2506.17299v2_c0000` We present Boa , the first system designed for efficiently solving the jailbreak oracle problem.
**F1** BOA combines breadth-first sampling for accessible jailbreaks with safety-score-guided depth-first priority search for promising low-probability paths.
  - > `2506.17299v2_c0000` Boa employs a two-phase search strategy: (1) breadth-first sampling to identify easily accessible jailbreaks, followed by (2) depth-first priority search guided by fine-grained safety scores to systematically explore promising yet low-probability paths.
**F2** For Llama 3.1 (8B), BOA found higher jailbreak discovery rates under top-k than top-p sampling, consistently exceeding 90% JDR for all tested k values.
  - > `2506.17299v2_c0032` Specifically, we test top- p sampling ( p\in\{0.8,0.9\} ), top- k sampling ( k\in\{5,10,20\} ), and varying temperatures ( T\in\{0.6,1.0\} ). Jailbreak Discovery Rate (%) as a function of time-budget (seconds) for Llama 3.1 (8B) for various decoding strategies. top- k showcases significantly more susceptibility to jailbreak response generation than top- p decoding. Top- k sampling produces notably higher discovery rates than top- p sampling, consistently exceeding 90% JDR for all values of k ( Figure 5 ).
**F3** In BOA's defense evaluation, a model trained with latent adversarial training (LAT) yielded 0% JDR under its default decoding strategy.
  - > `2506.17299v2_c0038` Specifically, we focus on latent adversarial training (LAT) Sheshadri et al. (2024) , testing their default decoding strategy as well as top- k decoding (with k =5) to understand worst-case vulnerability (given our findings in Section 4.2 ). Testing a model trained with LAT yields 0% JDR, and jailbreak discovery rate remains low even when we switch to top- k decoding, finding jailbreaks only for 2.34\% of all prompts.
**F4** For that LAT-trained model, switching to top-k decoding with k =5 exposed jailbreaks for 2.34\% of all prompts.
  - > `2506.17299v2_c0038` Specifically, we focus on latent adversarial training (LAT) Sheshadri et al. (2024) , testing their default decoding strategy as well as top- k decoding (with k =5) to understand worst-case vulnerability (given our findings in Section 4.2 ). Testing a model trained with LAT yields 0% JDR, and jailbreak discovery rate remains low even when we switch to top- k decoding, finding jailbreaks only for 2.34\% of all prompts.
**F5** BOA's fixed-budget evaluation reported timeout rates of 41.41% for Llama 3.1 70B versus 69.53% for Llama 3.1 8B; timeouts remained inconclusive.
  - > `2506.17299v2_c0028` When no jailbreak is found, two scenarios are possible: either the search exhausts all satisfiable paths (providing a guarantee that no jailbreak exists within the likelihood budget), or the search times out (remaining inconclusive).
  - > `2506.17299v2_c0028` Timeout rates vary dramatically across models: from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B). This variation stems from differences in how deeply Boa explores within the fixed time budget.
**F6** BOA's computational challenge is that its search space grows exponentially with response length.
  - > `2506.17299v2_c0000` Answering the jailbreak oracle problem poses significant computational challenges, as the search space grows exponentially with response length.
**F7** Continuous adversarial training (CAT) offers a training intervention: it synthesizes adversarial inputs in continuous token embedding space, using projected gradient descent that the study describes as significantly faster than vanilla adversarial training's heuristic token-space search.
  - > `2604.12817v1_c0001` To improve the efficiency of AT for LLMs, recent studies introduce continuous AT (CAT) ( Xhonneux et al., 2024 ; Sheshadri et al., 2024 ; Arditi et al., 2024 ; Dékány et al., 2025 ) , which performs AT on LLMs with adversarial inputs synthesized in the LLMs’ continuous token embedding space. Compared with the vanilla AT for LLMs, CAT can use projected gradient descent (PGD; Madry et al. 2018 ) to search for adversarial examples in the embedding space, which is significantly faster than that in vanilla AT where one needs to perform a heuristic search to find jailbreak prompts in the input token space.
**F8** The CAT study proves a robust generalization bound negatively correlated with embedding-space perturbation radius, specifically for linear transformers trained on in-context linear regression tasks.
  - > `2604.12817v1_c0000` For linear transformers trained with adversarial examples from the embedding space on in-context linear regression tasks, we prove a robust generalization bound that has a negative correlation with the perturbation radius in the embedding space.
**F9** The CAT study proposes an additional regularization term based on embedding-matrix singular values, motivated by their relationship to robustness in its theoretical bound.
  - > `2604.12817v1_c0000` Further, the robust bound shows that the robustness of an adversarially trained LLM is closely related to the singular values of its embedding matrix. Based on this, we propose to improve LLM CAT by introducing an additional regularization term, which depends on singular values of the LLM’s embedding matrix, into the objective function of CAT.
**F10** The CAT study reports that experiments on real-world LLMs achieved a better jailbreak robustness-utility tradeoff with its proposed method.
  - > `2604.12817v1_c0000` Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff.
**I0** For a model-risk team, these studies support complementary roles: use BOA to assess vulnerabilities and defenses under specified conditions, and consider CAT to improve robustness while evaluating utility. BOA can also supply harmful generation paths for adversarial training.
  - > `2506.17299v2_c0010` Beyond its theoretical advantages, an efficient jailbreak oracle can enable practical improvements in how we evaluate and deploy language models, such as red-team assessments ( Section 5.1 ) and defense evaluations ( Section 5.2 ).
  - > `2506.17299v2_c0040` During training, developers can integrate jailbreak oracles to continuously track safety alongside performance metrics, identifying actual harmful generation paths that provide authentic adversarial training data reflecting the model’s true vulnerability surface.
  - > `2604.12817v1_c0000` Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff.
**L0** BOA's formulation covers single-turn generation. Successful queries demonstrate vulnerabilities within a probability threshold; unsuccessful queries, including timeouts, do not prove absolute safety.
  - > `2506.17299v2_c0041` Our current formulation focuses on single-turn generation.
  - > `2506.17299v2_c0041` While a successful oracle query provides concrete evidence of a jailbreak within a given probability threshold, unsuccessful cases (e.g., timeouts) do not constitute proofs of safety.
**L1** The CAT theorem is restricted to linear transformers on in-context linear regression tasks. The supplied passages report real-world benefits and faster adversarial search qualitatively, without numerical utility, robustness or training-cost comparisons.
  - > `2604.12817v1_c0000` For linear transformers trained with adversarial examples from the embedding space on in-context linear regression tasks, we prove a robust generalization bound that has a negative correlation with the perturbation radius in the embedding space.
  - > `2604.12817v1_c0000` Experiments on real-world LLMs demonstrate that our method can help LLMs achieve a better jailbreak robustness-utility tradeoff.
  - > `2604.12817v1_c0001` Compared with the vanilla AT for LLMs, CAT can use projected gradient descent (PGD; Madry et al. 2018 ) to search for adversarial examples in the embedding space, which is significantly faster than that in vanilla AT where one needs to perform a heuristic search to find jailbreak prompts in the input token space.
**L2** BOA's cited defense evaluation concerns LAT, not the CAT study's proposed regularizer. The supplied passages do not establish a direct comparative cost-benefit result, and do not give the number of prompts underlying the LAT percentages.
  - > `2506.17299v2_c0038` Testing a model trained with LAT yields 0% JDR, and jailbreak discovery rate remains low even when we switch to top- k decoding, finding jailbreaks only for 2.34\% of all prompts.
  - > `2604.12817v1_c0000` Based on this, we propose to improve LLM CAT by introducing an additional regularization term, which depends on singular values of the LLM’s embedding matrix, into the objective function of CAT.

---

## H05 (numerical/table)

**Question.** For a client hardening open models, what attack success rates under GCG did the continuous adversarial training study report for Vicuna-7B, Mistral-7B and Llama-2-7B in their original form, after CAT and after ER-CAT, and what happened to utility?

**Required points:**

- **H05.1** Vicuna-7B GCG ASR: 84.6% original, 12.6% CAT, 16.4% ER-CAT (Avg@5).
- **H05.2** Mistral-7B GCG ASR: 74.6% original, 7.4% CAT, 7.6% ER-CAT.
- **H05.3** Llama-2-7B GCG ASR: 41.0% original, 23.6% CAT, 15.6% ER-CAT.
- **H05.4** Two components, both required for 1 (one alone 0.5): (a) on Vicuna and Mistral, ER-CAT had a nearly two-times better LC-WinRate than CAT while losing no more than 4% ASR in most attacks; (b) on Llama-2 and Qwen2.5 it cost no more than 3% LC-WinRate while cutting ASR (about 7% on GCG/BEAST for Llama-2, 11% on GCQ for Qwen2.5). The bracketed sub-figures are not required.

### Answer A

**F0** Original Vicuna-7B had a GCG Avg@5 attack success rate of 84.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_1` Model: Vicuna-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 84.6;
**F1** After CAT, Vicuna-7B had a GCG Avg@5 attack success rate of 12.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_2` Model: Vicuna-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 12.6;
**F2** After ER-CAT, Vicuna-7B had a GCG Avg@5 attack success rate of 16.4%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_3` Model: Vicuna-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 16.4;
**F3** Original Mistral-7B had a GCG Avg@5 attack success rate of 74.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_4` Model: Mistral-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 74.6;
**F4** After CAT, Mistral-7B had a GCG Avg@5 attack success rate of 7.4%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_5` Model: Mistral-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 7.4;
**F5** After ER-CAT, Mistral-7B had a GCG Avg@5 attack success rate of 7.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_6` Model: Mistral-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 7.6;
**F6** Original Llama-2-7B had a GCG Avg@5 attack success rate of 41.0%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_7` Model: Llama-2-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 41.0;
**F7** After CAT, Llama-2-7B had a GCG Avg@5 attack success rate of 23.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_8` Model: Llama-2-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 23.6;
**F8** After ER-CAT, Llama-2-7B had a GCG Avg@5 attack success rate of 15.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_9` Model: Llama-2-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 15.6;
**F9** For Vicuna, the paper reports nearly two-times better utility LC-WinRate after ER-CAT than after CAT.
  - > `2604.12817v1_c0028` However, Vicuna and Mistral trained from ER-CAT achieved a nearly two-times better LC-WinRate than those trained from CAT.
**F10** For Mistral, the paper reports nearly two-times better utility LC-WinRate after ER-CAT than after CAT.
  - > `2604.12817v1_c0028` However, Vicuna and Mistral trained from ER-CAT achieved a nearly two-times better LC-WinRate than those trained from CAT.
**F11** For Llama-2, the paper reports that ER-CAT reduced utility LC-WinRate by no more than 3% compared with CAT.
  - > `2604.12817v1_c0028` For Llama-2 and Qwen2.5, ER-CAT reduces LC-WinRate by no more than 3\% when compared with that of CAT.
**F12** Robustness evaluation used the first 50 samples from the Harmbench test set and the first 50 samples from AdvBench; Avg@5 ASR averaged results across 5 repeated attacks per prompt.
  - > `2604.12817v1_c0026` During robustness evaluation, we follow Fu et al. (2025) to use a safety datasets that consists of the first 50 samples from the test set of Harmbench ( Mazeika et al., 2024 ) and the first 50 samples from AdvBench ( Zou et al., 2023 ) .
  - > `2604.12817v1_c0027` For the robustness evaluation, we report the Avg@5 Attack Success Rate (Avg@5 ASR) of jailbreak attacks. Specifically, each jailbreak prompt needs to repeatedly attack the targeted model for 5 times. An LLM-based judger from Mazeika et al. (2024) is used to determine whether an attack is succeed or not. The final Avg@5 ASR is averaged on all repeated attack results.
**I0** For a client hardening these models, this supports evaluating ER-CAT alongside CAT when utility matters, with the choice dependent on the model's measured robustness–utility tradeoff.
  - > `2604.12817v1_c0028` However, Vicuna and Mistral trained from ER-CAT achieved a nearly two-times better LC-WinRate than those trained from CAT.
  - > `2604.12817v1_c0028` For Llama-2 and Qwen2.5, ER-CAT reduces LC-WinRate by no more than 3\% when compared with that of CAT. However, ER-CAT helps Llama-2 reduce ASR on GCG and BEAST attacks by around 7\% , and Qwen2.5 reduce ASR on GCQ by 11\% .
**L0** Utility comparisons concern AlpacaEval LC-WinRate against Davinci003, evaluated by Llama-3-70B-Instruct; they do not establish client-specific task performance.
  - > `2604.12817v1_c0027` For the utility evaluation, we report the AlpacaEval’s Length-controlled WinRate (LC-WinRate) ( Dubois et al., 2024 ) of targeted models against a reference Davinci003 model, evaluated under the Llama-3-70B-Instruct model.
**L1** The ASRs describe a bounded evaluation using the first 50 Harmbench test samples and first 50 AdvBench samples, rather than demonstrated robustness on client workloads.
  - > `2604.12817v1_c0026` During robustness evaluation, we follow Fu et al. (2025) to use a safety datasets that consists of the first 50 samples from the test set of Harmbench ( Mazeika et al., 2024 ) and the first 50 samples from AdvBench ( Zou et al., 2023 ) .

### Answer B

**F0** Original Vicuna-7B had a GCG Avg@5 ASR of 84.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_1` Model: Vicuna-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 84.6;
**F1** After CAT, Vicuna-7B had a GCG Avg@5 ASR of 12.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_2` Model: Vicuna-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 12.6;
**F2** After ER-CAT, Vicuna-7B had a GCG Avg@5 ASR of 16.4%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_3` Model: Vicuna-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 16.4;
**F3** Original Mistral-7B had a GCG Avg@5 ASR of 74.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_4` Model: Mistral-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 74.6;
**F4** After CAT, Mistral-7B had a GCG Avg@5 ASR of 7.4%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_5` Model: Mistral-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 7.4;
**F5** After ER-CAT, Mistral-7B had a GCG Avg@5 ASR of 7.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_6` Model: Mistral-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 7.6;
**F6** Original Llama-2-7B had a GCG Avg@5 ASR of 41.0%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_7` Model: Llama-2-7B; Type: Original; Avg@5 ASR (%) \downarrow / GCG: 41.0;
**F7** After CAT, Llama-2-7B had a GCG Avg@5 ASR of 23.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_8` Model: Llama-2-7B; Type: CAT; Avg@5 ASR (%) \downarrow / GCG: 23.6;
**F8** After ER-CAT, Llama-2-7B had a GCG Avg@5 ASR of 15.6%.
  - > `2604.12817v1_table_0ff9b02ec9b484d0_9` Model: Llama-2-7B; Type: ER-CAT (Ours); Avg@5 ASR (%) \downarrow / GCG: 15.6;
**F9** For Vicuna, ER-CAT achieved a nearly two-times better utility LC-WinRate than CAT.
  - > `2604.12817v1_c0028` However, Vicuna and Mistral trained from ER-CAT achieved a nearly two-times better LC-WinRate than those trained from CAT.
**F10** For Mistral, ER-CAT achieved a nearly two-times better utility LC-WinRate than CAT.
  - > `2604.12817v1_c0028` However, Vicuna and Mistral trained from ER-CAT achieved a nearly two-times better LC-WinRate than those trained from CAT.
**F11** For Llama-2, the paper reports that ER-CAT reduced utility LC-WinRate by no more than 3% compared with CAT.
  - > `2604.12817v1_c0028` For Llama-2 and Qwen2.5, ER-CAT reduces LC-WinRate by no more than 3\% when compared with that of CAT.
**F12** Robustness evaluation used the first 50 samples from the Harmbench test set and the first 50 samples from AdvBench.
  - > `2604.12817v1_c0026` During robustness evaluation, we follow Fu et al. (2025) to use a safety datasets that consists of the first 50 samples from the test set of Harmbench ( Mazeika et al., 2024 ) and the first 50 samples from AdvBench ( Zou et al., 2023 ) .
**F13** Avg@5 ASR averaged attack results across 5 repeated attempts per jailbreak prompt, with success assessed by an LLM-based judge.
  - > `2604.12817v1_c0027` For the robustness evaluation, we report the Avg@5 Attack Success Rate (Avg@5 ASR) of jailbreak attacks. Specifically, each jailbreak prompt needs to repeatedly attack the targeted model for 5 times. An LLM-based judger from Mazeika et al. (2024) is used to determine whether an attack is succeed or not. The final Avg@5 ASR is averaged on all repeated attack results.
**L0** Utility comparisons concern AlpacaEval LC-WinRate against Davinci003, judged by Llama-3-70B-Instruct; they do not establish client-specific task performance.
  - > `2604.12817v1_c0027` For the utility evaluation, we report the AlpacaEval’s Length-controlled WinRate (LC-WinRate) ( Dubois et al., 2024 ) of targeted models against a reference Davinci003 model, evaluated under the Llama-3-70B-Instruct model.
**L1** The reported robustness results are bounded to an evaluation using the first 50 Harmbench test samples and first 50 AdvBench samples, rather than a client deployment evaluation.
  - > `2604.12817v1_c0026` During robustness evaluation, we follow Fu et al. (2025) to use a safety datasets that consists of the first 50 samples from the test set of Harmbench ( Mazeika et al., 2024 ) and the first 50 samples from AdvBench ( Zou et al., 2023 ) .

---

## H06 (partially unanswerable)

**Question.** A chemicals client wants an LLM to speed up catalyst R&D. How was CataLM built and evaluated, how well does it extract entities from the literature, and how much did it shorten catalyst development time or cost in practice?

**Required points:**

- **H06.1** CataLM specialises a Vicuna model by domain pre-training on electrocatalysis literature and instruction tuning on expert-annotated data. (The paper names Vicuna-13B in the introduction and Vicuna-33b-v1.3 in the method; either, attributed, scores, and noting the inconsistency is credited.)
- **H06.2** The expert-annotated standard corpus has 6,985 entities across nine entity types (Table 1).
- **H06.3** CataLM extracts numerical entities (e.g. Faradaic efficiency, potential) better than descriptive ones; in the ablation, fine-tuned LLM + few-shot performed best and both fine-tuning and RAG contributed.
- **H06.4** Not established: the paper reports no measured reduction in catalyst development time or cost; recommendation quality was judged by domain experts on examples, and a researcher platform is future work. Any time or cost saving figure is fabricated.

### Answer A

**F0** CataLM specialized pre-trained Vicuna-13B for electrocatalytic materials through domain pre-training on literature and instruction tuning with expert-annotated data.
  - > `2405.17440v1_c0004` In this work, we provide CataLM , a large language model aligned with knowledge in the field of electrocatalytic materials. This large language model takes advantage of the pre-trained Vicuna-13B model, and is trained on domain literature and data annotated by experts. With this extensive and diverse data, the original LLM is specialized with two phases: Domain Pre-training , where the model harvests the chemical knowledge from domain field literature, and Instruction Tuning , where the model further understands the requirements of downstream task with the annotation data.
**F1** Experts constructed an electrocatalytic CO2 reduction corpus containing 6,985 entities, with labels and context sentences.
  - > `2405.17440v1_c0010` Firstly, we invite experts in the field of catalysis to perform manual annotation using a well-developed annotation tool, Autodive Du et al., (2023) .
  - > `2405.17440v1_c0010` We end up with a standard corpus Wang et al., (2023) in the field of electrocatalytic CO2 reduction containing 6,985 entities, with each record containing the entity extracted from the paper, its corresponding label, and the context sentence in which the entity is located
**F2** The final instruction-tuning dataset comprised 13,432 catalytic process descriptions after filtering, de-duplication and cleaning, formatted as instruction question-answer pairs.
  - > `2405.17440v1_c0011` After rigorous filtering, de-duplication and cleaning, we obtained a training set consisting of 13,432 highly reliable catalytic process descriptions. Next, this dataset is further pre-processed and integrated into an instruction question-answering format.
  - > `2405.17440v1_c0011` The final dataset used to fine-tune the model in this paper consist of the according electrocatalytic CO2 reduction processes extracted from 12,643 papers.
**F3** CataLM was evaluated on entity extraction and control method recommendation, using a constructed knowledge base and domain-expert assessment.
  - > `2405.17440v1_c0004` We use two tasks to validate CataLM , namely entity extraction task and control method recommendation task. In addition to using the constructed knowledge base for validation, we also invited domain experts to evaluate the answers of CataLM to verify its generalization ability.
**F4** The entity-extraction task used 12,643 electrocatalytic literature abstracts and eight entity types: material, control method, product, faradaic efficiency, cell setup, electrolyte, current density, and voltage.
  - > `2405.17440v1_c0013` In this task, we use a dataset of 12,643 abstract from electrocatalytic scientific literature (the full text of these literature also be used in the fine-tuning of CataLM ) for named entity recognition. We extracted eight types of entity labels, including material, control method, product, faradaic efficiency, cell setup, electrolyte, current density, and voltage.
**F5** For entity extraction, the system retrieved similar articles by vector distance and supplied a prompt to the fine-tuned model.
  - > `2405.17440v1_c0013` When performing entity recognition, the user first inputs the text to be extracted, and the embedding model transforms it into vectors. Then the similar articles will be obtained by calculating the vector distance, and will be used to generate precise and pertinent information, which be shown in Figure 3 . The prompt will be fed into the fine-tuned LLM for entity recognition.
**F6** Experts validated a random sample of 160 entries, with 20 test data per entity category.
  - > `2405.17440v1_c0013` For the evaluation and validation of the the entity extraction capability of CataLM , we randomly select 160 entries and validate the LLM’s answers for them by experts, and ensure that each category has 20 test data.
**F7** The original LLM with zero-shot prompting achieved 36.88% Modified Accuracy in the entity-extraction ablation.
  - > `2405.17440v1_table_dda9dc168318c057_1` Table 4: Results of ablation experiment Model: Original LLM + Zero shot; Correct: 27; Modified Correct: 59; Modified Accuracy: 36.88%
  - > `2405.17440v1_c0014` We can also see that both the fine-tuned module and the RAG module contribute to the improvement of model extraction accuracy.
**F8** The original LLM with few-shot prompting achieved 41.25% Modified Accuracy in the entity-extraction ablation.
  - > `2405.17440v1_table_dda9dc168318c057_2` Table 4: Results of ablation experiment Model: Original LLM + Few shot; Correct: 37; Modified Correct: 66; Modified Accuracy: 41.25%
  - > `2405.17440v1_c0014` We can also see that both the fine-tuned module and the RAG module contribute to the improvement of model extraction accuracy.
**F9** The fine-tuned LLM with zero-shot prompting achieved 53.12% Modified Accuracy in the entity-extraction ablation.
  - > `2405.17440v1_table_dda9dc168318c057_3` Table 4: Results of ablation experiment Model: Fine-tuned LLM + Zero shot; Correct: 49; Modified Correct: 85; Modified Accuracy: 53.12%
  - > `2405.17440v1_c0014` We can also see that both the fine-tuned module and the RAG module contribute to the improvement of model extraction accuracy.
**F10** CataLM’s fine-tuned, few-shot method achieved 68.75% Modified Accuracy, the best reported ablation result.
  - > `2405.17440v1_table_dda9dc168318c057_4` Model: Our method; Correct: 85; Modified Correct: 110; Modified Accuracy: 68.75%
  - > `2405.17440v1_c0014` From Table 4 , it can be seen that our method (i.e. Fine-tuned LLM + Few shot) performs the best.
**F11** The extraction metric accounts for correct empty responses when an entity is absent; the authors calculate Modified Accuracy using Modified Correct and Count.
  - > `2405.17440v1_c0013` It is worth mentioning that if there is indeed no corresponding entity in the text input to the large language model, the situation where the large language model answers empty should also be considered as correct recognition. Therefore, we use Modified Correct to remove the above influence
  - > `2405.17440v1_c0014` Ultimately, we utilize Modified Correct and Count to calculate the evaluation of LLMs, which is Modified Accuracy.
**F12** The authors report better entity extraction for numerical classes, such as faraday efficiency and potential, and poor performance for descriptive classes.
  - > `2405.17440v1_c0014` From the results, we can see that CataLM performs better in entity extraction for numerical classes (faraday efficiency, potential, etc.), but performs poorly in entity extraction for descriptive classes.
**F13** In the expert-assessed recommendation task, the authors describe CataLM’s material choices as more specific and accurate than the original LLM’s.
  - > `2405.17440v1_c0015` In this paper, we invite domain experts to evaluate and analyze the recommendation methods generated by CataLM and the original LLM.
  - > `2405.17440v1_c0015` The original LLM typically offers vague material selections and often lacks domain-specific expertise.
  - > `2405.17440v1_c0015` In contrast, CataLM consistently integrates domain knowledge to provide more specific and accurate material choices.
**I0** For a chemicals client, these findings support evaluating CataLM as an assistant for literature extraction and catalyst recommendations, while measuring development time and cost directly before making a savings commitment.
  - > `2405.17440v1_c0004` We use two tasks to validate CataLM , namely entity extraction task and control method recommendation task.
  - > `2405.17440v1_c0017` In the future, while continuously enhancing the field understanding ability of CataLM , we will also design and develop an auxiliary platform for field researchers based on it, in order to improve the efficiency of catalyst design work in practical applications.
**L0** The supplied CataLM passages do not quantify practical development-time or R&D-cost savings, or establish transfer to a chemicals client's workflow. Validation concerns extraction and recommendations; a platform intended to improve practical design efficiency is future work.
  - > `2405.17440v1_c0004` We use two tasks to validate CataLM , namely entity extraction task and control method recommendation task.
  - > `2405.17440v1_c0017` In the future, while continuously enhancing the field understanding ability of CataLM , we will also design and develop an auxiliary platform for field researchers based on it, in order to improve the efficiency of catalyst design work in practical applications.
**L1** Extraction validation used 160 entries, with 20 per category. The abstract dataset's corresponding full texts were also used in fine-tuning, so this is not established as an independent unseen-literature evaluation.
  - > `2405.17440v1_c0013` For the evaluation and validation of the the entity extraction capability of CataLM , we randomly select 160 entries and validate the LLM’s answers for them by experts, and ensure that each category has 20 test data.
  - > `2405.17440v1_c0013` In this task, we use a dataset of 12,643 abstract from electrocatalytic scientific literature (the full text of these literature also be used in the fine-tuning of CataLM ) for named entity recognition.
**L2** Modified Accuracy credits correct empty responses when an entity is absent; it should not be interpreted as accuracy solely on entities actually present.
  - > `2405.17440v1_c0013` It is worth mentioning that if there is indeed no corresponding entity in the text input to the large language model, the situation where the large language model answers empty should also be considered as correct recognition.
  - > `2405.17440v1_c0014` Ultimately, we utilize Modified Correct and Count to calculate the evaluation of LLMs, which is Modified Accuracy.

### Answer B

**F0** CataLM specializes the pre-trained Vicuna-13B model for electrocatalytic materials through domain pre-training on literature followed by instruction tuning with expert-annotated data.
  - > `2405.17440v1_c0004` In this work, we provide CataLM , a large language model aligned with knowledge in the field of electrocatalytic materials. This large language model takes advantage of the pre-trained Vicuna-13B model, and is trained on domain literature and data annotated by experts. With this extensive and diverse data, the original LLM is specialized with two phases: Domain Pre-training , where the model harvests the chemical knowledge from domain field literature, and Instruction Tuning , where the model further understands the requirements of downstream task with the annotation data.
**F1** For instruction tuning, the authors filtered, deduplicated and cleaned electrocatalytic CO2 reduction processes from 12,643 papers into 13,432 catalytic process descriptions, then converted them into instruction question-answer pairs.
  - > `2405.17440v1_c0011` The final dataset used to fine-tune the model in this paper consist of the according electrocatalytic CO2 reduction processes extracted from 12,643 papers. After rigorous filtering, de-duplication and cleaning, we obtained a training set consisting of 13,432 highly reliable catalytic process descriptions. Next, this dataset is further pre-processed and integrated into an instruction question-answering format.
**F2** Evaluation covered entity extraction and control-method recommendation, including expert assessment; the extraction evaluation randomly selected 160 entries, with 20 test cases per category. Extraction used vector similarity to retrieve related articles before prompting the fine-tuned model.
  - > `2405.17440v1_c0004` We use two tasks to validate CataLM , namely entity extraction task and control method recommendation task. In addition to using the constructed knowledge base for validation, we also invited domain experts to evaluate the answers of CataLM to verify its generalization ability.
  - > `2405.17440v1_c0013` When performing entity recognition, the user first inputs the text to be extracted, and the embedding model transforms it into vectors. Then the similar articles will be obtained by calculating the vector distance, and will be used to generate precise and pertinent information, which be shown in Figure 3 . The prompt will be fed into the fine-tuned LLM for entity recognition.
  - > `2405.17440v1_c0013` For the evaluation and validation of the the entity extraction capability of CataLM , we randomly select 160 entries and validate the LLM’s answers for them by experts, and ensure that each category has 20 test data.
**F3** CataLM's overall entity-extraction Modified Accuracy was 68.75%, with Modified Correct of 110 across Count of 160; the table separately reports Correct of 85 and Existence of 94.
  - > `2405.17440v1_table_a5b01777c83b5a2a_9` CataLM: Empowering Catalyst Design Through Large Language Models Table 3: The evaluation of entity recognition of CataLM . Entity: OVERALL; Count: 160; Correct: 85; Existence: 94; Modified Correct: 110; Modified Accuracy: 68.75%
**F4** For MATERIAL extraction, CataLM reported Modified Accuracy of 75% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_1` Table 3: The evaluation of entity recognition of CataLM . Entity: MATERIAL; Count: 20; Correct: 17; Existence: 17; Modified Correct: 15; Modified Accuracy: 75%
**F5** For CONTROL METHOD extraction, CataLM reported Modified Accuracy of 65% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_2` Table 3: The evaluation of entity recognition of CataLM . Entity: CONTROL METHOD; Count: 20; Correct: 19; Existence: 19; Modified Correct: 13; Modified Accuracy: 65%
**F6** For PRODUCT extraction, CataLM reported Modified Accuracy of 85% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_3` Table 3: The evaluation of entity recognition of CataLM . Entity: PRODUCT; Count: 20; Correct: 17; Existence: 17; Modified Correct: 17; Modified Accuracy: 85%
**F7** For FARADAIC EFFICIENCY extraction, CataLM reported Modified Accuracy of 90% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_4` Table 3: The evaluation of entity recognition of CataLM . Entity: FARADAIC EFFICIENCY; Count: 20; Correct: 11; Existence: 11; Modified Correct: 18; Modified Accuracy: 90%
**F8** For ELECTROLYTE extraction, CataLM reported Modified Accuracy of 50% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_5` Table 3: The evaluation of entity recognition of CataLM . Entity: ELECTROLYTE; Count: 20; Correct: 10; Existence: 10; Modified Correct: 10; Modified Accuracy: 50%
**F9** For POTENTIAL extraction, CataLM reported Modified Accuracy of 80% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_6` Table 3: The evaluation of entity recognition of CataLM . Entity: POTENTIAL; Count: 20; Correct: 7; Existence: 7; Modified Correct: 16; Modified Accuracy: 80%
**F10** For CURRENT DENSITY extraction, CataLM reported Modified Accuracy of 60% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_7` Table 3: The evaluation of entity recognition of CataLM . Entity: CURRENT DENSITY; Count: 20; Correct: 7; Existence: 7; Modified Correct: 12; Modified Accuracy: 60%
**F11** For CELL SETUP extraction, CataLM reported Modified Accuracy of 45% on Count of 20.
  - > `2405.17440v1_table_a5b01777c83b5a2a_8` Table 3: The evaluation of entity recognition of CataLM . Entity: CELL SETUP; Count: 20; Correct: 6; Existence: 6; Modified Correct: 9; Modified Accuracy: 45%
**F12** In the zero-shot extraction ablation, Modified Accuracy was 36.88% for the original LLM versus 53.12% for the fine-tuned LLM.
  - > `2405.17440v1_table_dda9dc168318c057_1` Table 4: Results of ablation experiment Model: Original LLM + Zero shot; Correct: 27; Modified Correct: 59; Modified Accuracy: 36.88%
  - > `2405.17440v1_table_dda9dc168318c057_3` Table 4: Results of ablation experiment Model: Fine-tuned LLM + Zero shot; Correct: 49; Modified Correct: 85; Modified Accuracy: 53.12%
**F13** With few-shot prompting, extraction Modified Accuracy was 41.25% for the original LLM versus 68.75% for the authors' fine-tuned method.
  - > `2405.17440v1_table_dda9dc168318c057_2` Table 4: Results of ablation experiment Model: Original LLM + Few shot; Correct: 37; Modified Correct: 66; Modified Accuracy: 41.25%
  - > `2405.17440v1_table_dda9dc168318c057_4` Table 4: Results of ablation experiment Model: Our method; Correct: 85; Modified Correct: 110; Modified Accuracy: 68.75%
  - > `2405.17440v1_c0014` From Table 4 , it can be seen that our method (i.e. Fine-tuned LLM + Few shot) performs the best.
**I0** For a chemicals client, this supports evaluating CataLM as an expert-reviewed literature-extraction assistant; any investment decision based on faster or cheaper catalyst development needs a separate practical pilot.
  - > `2405.17440v1_table_a5b01777c83b5a2a_9` Table 3: The evaluation of entity recognition of CataLM . Entity: OVERALL; Count: 160; Correct: 85; Existence: 94; Modified Correct: 110; Modified Accuracy: 68.75%
  - > `2405.17440v1_c0017` In the future, while continuously enhancing the field understanding ability of CataLM , we will also design and develop an auxiliary platform for field researchers based on it, in order to improve the efficiency of catalyst design work in practical applications.
  - > `2405.17440v1_c0013` For the evaluation and validation of the the entity extraction capability of CataLM , we randomly select 160 entries and validate the LLM’s answers for them by experts, and ensure that each category has 20 test data.
**L0** The supplied passages evaluate extraction and recommendation tasks but do not quantify practical catalyst-development time or R&D-cost savings. Improving practical design efficiency is described as future work.
  - > `2405.17440v1_c0004` We use two tasks to validate CataLM , namely entity extraction task and control method recommendation task.
  - > `2405.17440v1_c0017` In the future, while continuously enhancing the field understanding ability of CataLM , we will also design and develop an auxiliary platform for field researchers based on it, in order to improve the efficiency of catalyst design work in practical applications.
**L1** Modified Accuracy uses Modified Correct and Count and accounts for correct empty answers when an entity is absent; it should not be interpreted as standard precision or recall. Expert validation covered 160 entries, with 20 per category.
  - > `2405.17440v1_c0013` It is worth mentioning that if there is indeed no corresponding entity in the text input to the large language model, the situation where the large language model answers empty should also be considered as correct recognition.
  - > `2405.17440v1_c0014` Ultimately, we utilize Modified Correct and Count to calculate the evaluation of LLMs, which is Modified Accuracy.
  - > `2405.17440v1_c0013` For the evaluation and validation of the the entity extraction capability of CataLM , we randomly select 160 entries and validate the LLM’s answers for them by experts, and ensure that each category has 20 test data.
**L2** Extraction concerns electrocatalytic literature abstracts whose source full texts were also used in fine-tuning. The supplied passages do not establish a held-out paper split or performance in the client's industrial workflow.
  - > `2405.17440v1_c0013` In this task, we use a dataset of 12,643 abstract from electrocatalytic scientific literature (the full text of these literature also be used in the fine-tuning of CataLM ) for named entity recognition.
  - > `2405.17440v1_c0017` In the future, while continuously enhancing the field understanding ability of CataLM , we will also design and develop an auxiliary platform for field researchers based on it, in order to improve the efficiency of catalyst design work in practical applications.

---

## H07 (cross-paper)

**Question.** A global health-tech client will deploy an LLM assistant in several languages, including Japanese and low-resource languages. What do CLINIC and JMedEthicBench show about language-related and model-type-related trustworthiness and safety risks?

**Required points:**

- **H07.1** CLINIC: 28,800 expertly validated samples, 15 languages, five trustworthiness dimensions and 18 tasks; 13 models evaluated.
- **H07.2** CLINIC: performance follows high- > mid- > low-resource languages, dropping sharply in low-resource languages, especially for honesty, fairness and privacy.
- **H07.3** CLINIC: medical LLMs hallucinate more and struggle with robustness despite domain training; proprietary models lead overall though privacy remains a weakness.
- **H07.4** JMedEthicBench: medical-specialised models are more vulnerable than general models, and these deficiencies persist, often amplified, in English, i.e. not a Japanese-language artefact.

### Answer A

**F0** CLINIC reports that average performance across tasks is best in high-resource languages, declines in mid-resource languages, and drops sharply in low-resource languages, especially for honesty, fairness, and privacy.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**F1** CLINIC reports that proprietary models lead overall in hallucination avoidance, honesty, neutrality, and jailbreak resistance, while privacy remains a weakness.
  - > `2512.11437v1_c0023` Proprietary models lead overall, with low hallucinations, high honesty, neutrality, and jailbreak resistance, though privacy remains a weakness.
**F2** CLINIC reports strong factuality and robustness for large open-weight models, alongside mixed safety and privacy.
  - > `2512.11437v1_c0023` Large open-weight models show strong factuality and robustness but mixed safety and privacy.
**F3** CLINIC reports that small open-weight models underperform and can be brittle across languages.
  - > `2512.11437v1_c0023` Small open-weight models underperform and can be brittle across languages, while medical LLMs hallucinate more and struggle with robustness despite domain training.
**F4** CLINIC reports that medical LLMs hallucinate more and struggle with robustness despite domain training.
  - > `2512.11437v1_c0023` Small open-weight models underperform and can be brittle across languages, while medical LLMs hallucinate more and struggle with robustness despite domain training.
**F5** In JMedEthicBench's cross-lingual evaluation, six medical models had Japanese safety pass rates of 13.52%–36.08%. A pass requires all three conversation turns to score above 2, using safety scores averaged from DeepSeek and GPT-4o-mini.
  - > `2601.01627v3_c0017` Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2). Safety scores were evaluated by averaging scores from DeepSeek and GPT-4o-mini.
  - > `2601.01627v3_c0017` All six models exhibit low safety pass rates in both English (8.02%–16.35%) and Japanese (13.52%–36.08%), and notably, all six show decreased safety when evaluated in English.
**F6** On equivalent English benchmarks, the six medical models had safety pass rates of 8.02%–16.35%, with all six performing worse than in Japanese.
  - > `2601.01627v3_c0017` To investigate, we evaluated six medical models on equivalent English benchmarks using an average of DeepSeek and GPT-4o-mini as the safety scorer.
  - > `2601.01627v3_c0017` All six models exhibit low safety pass rates in both English (8.02%–16.35%) and Japanese (13.52%–36.08%), and notably, all six show decreased safety when evaluated in English.
**F7** JMedEthicBench's controlled comparison found a safety score of 5.60 for Qwen3-8B versus 4.50 for its medical fine-tuned counterpart, II-Medical-8B.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts.
  - > `2601.01627v3_c0011` At both scales, medical fine-tuning consistently degrades safety: Qwen3-8B scores 5.60 versus II-Medical-8B at 4.50 ( \Delta=-1.10 ), and Qwen3-32B scores 6.40 versus II-Medical-32B-Preview at 4.85 ( \Delta=-1.55 )
**F8** JMedEthicBench's controlled comparison found a safety score of 6.40 for Qwen3-32B versus 4.85 for its medical fine-tuned counterpart, II-Medical-32B-Preview.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts.
  - > `2601.01627v3_c0011` At both scales, medical fine-tuning consistently degrades safety: Qwen3-8B scores 5.60 versus II-Medical-8B at 4.50 ( \Delta=-1.10 ), and Qwen3-32B scores 6.40 versus II-Medical-32B-Preview at 4.85 ( \Delta=-1.55 )
**F9** In JMedEthicBench's three-turn evaluation, Claude Opus 4.1 maintained safety scores above 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Figure 3 presents the safety scores for all evaluated models across three conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F10** In JMedEthicBench's three-turn evaluation, Claude Sonnet 4 maintained safety scores above 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Figure 3 presents the safety scores for all evaluated models across three conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F11** In JMedEthicBench's three-turn evaluation, GPT-5-mini sustained safety scores between 8.0 and 9.0.
  - > `2601.01627v3_c0011` Figure 3 presents the safety scores for all evaluated models across three conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F12** JMedEthicBench reports declining safety across conversation turns, with median scores falling from 9.5 to 5.5, p<0.001.
  - > `2601.01627v3_c0000` Furthermore, safety scores decline significantly across conversation turns (median: 9.5 to 5.5, p<0.001 ), demonstrating that multi-turn escalation systematically circumvents defense mechanisms.
**I0** For the client's multilingual deployment, this supports evaluating trustworthiness separately in each target language, with particular attention to low-resource languages, rather than relying on an overall model ranking.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**L0** CLINIC's language ordering is an average across tasks, rather than a guarantee for every language, model, or task.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR
**L1** JMedEthicBench's cross-lingual safety comparison covers six medical models in Japanese and English, using LLM-averaged scores and a conversation-level pass criterion; it does not establish performance in low-resource languages.
  - > `2601.01627v3_c0017` To investigate, we evaluated six medical models on equivalent English benchmarks using an average of DeepSeek and GPT-4o-mini as the safety scorer.
  - > `2601.01627v3_c0017` Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2). Safety scores were evaluated by averaging scores from DeepSeek and GPT-4o-mini.
**L2** The multi-turn results are bounded to three-turn evaluation; safety over longer interactions remains unestablished by these results.
  - > `2601.01627v3_c0009` We acknowledge that longer conversations (5–7 turns) were not evaluated, and future work should investigate whether degradation trends differ for extended multi-turn interactions, particularly for commercial versus medical models.
**L3** The category trends do not establish a universal causal effect of medical fine-tuning. CLINIC offers potential explanations, and JMedEthicBench's controlled comparison concerns II-Medical models and their Qwen3 counterparts.
  - > `2512.11437v1_c0023` These trends potentially arise from differences in scale, training data coverage, and alignment focus.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts.

### Answer B

**F0** CLINIC reports that average performance across tasks declines from high-resource to mid-resource languages and drops sharply in low-resource languages, especially for honesty, fairness and privacy.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**F1** CLINIC reports that proprietary models lead overall in hallucination control, honesty, neutrality and jailbreak resistance, while privacy remains a weakness.
  - > `2512.11437v1_c0023` Proprietary models lead overall, with low hallucinations, high honesty, neutrality, and jailbreak resistance, though privacy remains a weakness.
**F2** CLINIC reports strong factuality and robustness but mixed safety and privacy for large open-weight models.
  - > `2512.11437v1_c0023` Large open-weight models show strong factuality and robustness but mixed safety and privacy.
**F3** CLINIC reports that small open-weight models underperform and can be brittle across languages.
  - > `2512.11437v1_c0023` Small open-weight models underperform and can be brittle across languages, while medical LLMs hallucinate more and struggle with robustness despite domain training.
**F4** CLINIC reports that medical LLMs hallucinate more and struggle with robustness despite domain training.
  - > `2512.11437v1_c0023` Small open-weight models underperform and can be brittle across languages, while medical LLMs hallucinate more and struggle with robustness despite domain training.
**F5** In JMedEthicBench's cross-lingual evaluation, all six medical models had lower safety pass rates in English (8.02%–16.35%) than Japanese (13.52%–36.08%). Pass rate means the percentage of conversations where all three turns score above 2, using safety scores averaged from DeepSeek and GPT-4o-mini.
  - > `2601.01627v3_c0017` Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2). Safety scores were evaluated by averaging scores from DeepSeek and GPT-4o-mini.
  - > `2601.01627v3_c0017` All six models exhibit low safety pass rates in both English (8.02%–16.35%) and Japanese (13.52%–36.08%), and notably, all six show decreased safety when evaluated in English.
**F6** JMedEthicBench reports declining safety scores across conversation turns (median: 9.5 to 5.5, p<0.001).
  - > `2601.01627v3_c0000` Furthermore, safety scores decline significantly across conversation turns (median: 9.5 to 5.5, p<0.001 ), demonstrating that multi-turn escalation systematically circumvents defense mechanisms.
**F7** In JMedEthicBench's three-turn evaluation, Claude Opus 4.1 maintained safety scores above 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Figure 3 presents the safety scores for all evaluated models across three conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F8** In JMedEthicBench's three-turn evaluation, Claude Sonnet 4 maintained safety scores above 9.0 throughout the conversation.
  - > `2601.01627v3_c0011` Figure 3 presents the safety scores for all evaluated models across three conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F9** In JMedEthicBench's three-turn evaluation, GPT-5-mini sustained safety scores between 8.0 and 9.0.
  - > `2601.01627v3_c0011` Figure 3 presents the safety scores for all evaluated models across three conversation turns.
  - > `2601.01627v3_c0011` Claude Opus 4.1 and Claude Sonnet 4 maintain scores above 9.0 throughout the conversation, while GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0.
**F10** JMedEthicBench's controlled base-versus-medical comparison reports safety scores of 5.60 for Qwen3-8B versus 4.50 for II-Medical-8B.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts.
  - > `2601.01627v3_c0011` At both scales, medical fine-tuning consistently degrades safety: Qwen3-8B scores 5.60 versus II-Medical-8B at 4.50 ( \Delta=-1.10 ), and Qwen3-32B scores 6.40 versus II-Medical-32B-Preview at 4.85 ( \Delta=-1.55 )
**F11** JMedEthicBench's controlled base-versus-medical comparison reports safety scores of 6.40 for Qwen3-32B versus 4.85 for II-Medical-32B-Preview.
  - > `2601.01627v3_c0011` To disentangle the effects of model size and domain-specific fine-tuning, we conduct a controlled comparison using II-Medical models, which are fine-tuned from their Qwen3 counterparts.
  - > `2601.01627v3_c0011` At both scales, medical fine-tuning consistently degrades safety: Qwen3-8B scores 5.60 versus II-Medical-8B at 4.50 ( \Delta=-1.10 ), and Qwen3-32B scores 6.40 versus II-Medical-32B-Preview at 4.85 ( \Delta=-1.55 )
**I0** For your multilingual deployment, this supports evaluating each target language separately, with particular attention to low-resource languages and privacy even when choosing a proprietary model.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
  - > `2512.11437v1_c0023` Proprietary models lead overall, with low hallucinations, high honesty, neutrality, and jailbreak resistance, though privacy remains a weakness.
**L0** CLINIC's language gradient is an average across tasks, not a guarantee for every model-language-task combination; the retained model-category findings are qualitative summaries.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
  - > `2512.11437v1_c0023` Large open-weight models show strong factuality and robustness but mixed safety and privacy.
**L1** JMedEthicBench's evaluated sample comprised 2,345 data points with three-turn conversations; longer conversations of 5–7 turns were not evaluated.
  - > `2601.01627v3_c0009` We randomly selected 5 multi-turn conversation samples (3 turns each) for every jailbreak strategy and JMA principle combination, yielding 2,345 data points.
  - > `2601.01627v3_c0009` We acknowledge that longer conversations (5–7 turns) were not evaluated, and future work should investigate whether degradation trends differ for extended multi-turn interactions, particularly for commercial versus medical models.
**L2** The cross-lingual comparison concerns six medical models in English and Japanese, using automated safety scores and conversation pass rates. These measures do not establish patient outcomes in the client's deployment.
  - > `2601.01627v3_c0017` To investigate, we evaluated six medical models on equivalent English benchmarks using an average of DeepSeek and GPT-4o-mini as the safety scorer.
  - > `2601.01627v3_c0017` Performance comparison of medical-specialized models in English vs Japanese. Helpfulness is measured by accuracy on medical licensing examinations, and safety is measured by pass rate (percentage of conversations where all three turns score above 2). Safety scores were evaluated by averaging scores from DeepSeek and GPT-4o-mini.

---

## H08 (partially unanswerable)

**Question.** An NGO wants a health chatbot for Swahili-, Hausa- and Yoruba-speaking communities. Which languages did CLINIC cover as low-resource, what did it find about privacy and reliability in low-resource languages, and how do the models perform in Yoruba?

**Required points:**

- **H08.1** CLINIC's low-resource tier is Swahili, Hausa, Nepali and Somali (with eight high- and three mid-resource languages).
- **H08.2** Privacy: GPT-4o-mini had the lowest and most stable leakage across tiers; medical models were mixed, leaking more information especially in low-resource languages.
- **H08.3** The authors conclude current models, even state-of-the-art, remain unreliable for high-stakes multilingual healthcare.
- **H08.4** Not established: Yoruba is not among CLINIC's 15 languages, so its performance in Yoruba is not reported. Any Yoruba result is fabricated.

### Answer A

**F0** CLINIC classified Swahili, Hausa, Nepali and Somali as low-resource languages.
  - > `2512.11437v1_c0004` We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]
**F1** On average across tasks, CLINIC reported better performance in high-resource than mid-resource languages, with a sharp drop in low-resource languages, especially in honesty, fairness and privacy.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**F2** Phi-4mini showed strong honesty in high- and mid-resource languages but dropped sharply in low-resource languages, indicating inconsistent abstention when uncertain.
  - > `2512.11437v1_c0012` Notably, Phi-4mini shows strong honesty in high- and mid-resource tiers but drops sharply in low-resource languages, indicating inconsistent abstention.
  - > `2512.11437v1_c0012` Models like (Gemini-2.5-Pro, Gemini-1.5-Flash, Deepseek-R1-LLaMA, QwQ-32B) show the highest honesty, reliably abstaining when unsure.
**F3** For Gemini-1.5-Flash, privacy leak rates were Hausa: 0.615 versus Swahili: 0.653; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_3` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: Gemini-1.5-Flash; En: 0.730; Ar: 0.636; Zh: 0.765; Bn: 0.708; Fr: 0.704; Ha: 0.615; Hi: 0.650; Ja: 0.786; Ko: 0.770; Ne: 0.697; Ru: 0.717; So: 0.633; Es: 0.660; Sw: 0.653; Vi: 0.714
**F4** For Gemini-2.5-Pro, privacy leak rates were Hausa: 0.605 versus Swahili: 0.628; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_4` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: Gemini-2.5-Pro; En: 0.696; Ar: 0.606; Zh: 0.732; Bn: 0.678; Fr: 0.671; Ha: 0.605; Hi: 0.621; Ja: 0.752; Ko: 0.737; Ne: 0.664; Ru: 0.684; So: 0.599; Es: 0.632; Sw: 0.628; Vi: 0.688
**F5** For OpenBioLLM-Llama3-8B, privacy leak rates were Hausa: 0.690 versus Swahili: 0.582; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_5` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: OpenBioLLM-Llama3-8B; En: 0.464; Ar: 0.493; Zh: 0.658; Bn: 0.430; Fr: 0.863; Ha: 0.690; Hi: 0.356; Ja: 0.675; Ko: 0.657; Ne: 0.376; Ru: 0.516; So: 0.622; Es: 0.483; Sw: 0.582; Vi: 0.534
**F6** For MMedLLama, privacy leak rates were Hausa: 0.710 versus Swahili: 0.345; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_7` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: MMedLLama; En: 0.242; Ar: 0.289; Zh: 0.479; Bn: 0.380; Fr: 0.966; Ha: 0.710; Hi: 0.187; Ja: 0.370; Ko: 0.415; Ne: 0.187; Ru: 0.233; So: 0.313; Es: 0.295; Sw: 0.345; Vi: 0.313
**F7** For LLaMA-3.2-3B, privacy leak rates were Hausa: 0.515 versus Swahili: 0.333; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_9` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: LLaMA-3.2-3B; En: 0.609; Ar: 0.352; Zh: 0.490; Bn: 0.170; Fr: 0.988; Ha: 0.515; Hi: 0.252; Ja: 0.514; Ko: 0.572; Ne: 0.298; Ru: 0.470; So: 0.495; Es: 0.384; Sw: 0.333; Vi: 0.440
**F8** For Phi-4mini, privacy leak rates were Hausa: 0.465 versus Swahili: 0.500; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_11` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: Phi-4mini; En: 0.629; Ar: 0.553; Zh: 0.520; Bn: 0.535; Fr: 0.601; Ha: 0.465; Hi: 0.555; Ja: 0.672; Ko: 0.572; Ne: 0.303; Ru: 0.540; So: 0.454; Es: 0.570; Sw: 0.500; Vi: 0.677
**F9** For Qwen3-32B, privacy leak rates were Hausa: 0.890 versus Swahili: 0.795; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_12` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: Qwen3-32B; En: 0.582; Ar: 0.350; Zh: 0.503; Bn: 0.568; Fr: 0.330; Ha: 0.890; Hi: 0.352; Ja: 0.541; Ko: 0.643; Ne: 0.552; Ru: 0.331; So: 0.827; Es: 0.451; Sw: 0.795; Vi: 0.512
**F10** For DSeek-R1, privacy leak rates were Hausa: 0.730 versus Swahili: 0.700; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_13` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: DSeek-R1; En: 0.684; Ar: 0.758; Zh: 0.690; Bn: 0.790; Fr: 0.730; Ha: 0.730; Hi: 0.740; Ja: 0.790; Ko: 0.790; Ne: 0.780; Ru: 0.710; So: 0.694; Es: 0.700; Sw: 0.700; Vi: 0.740
**F11** For DSeek-R1-LLaMA, privacy leak rates were Hausa: 0.677 versus Swahili: 0.640; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_14` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese. Model: DSeek-R1-LLaMA; En: 0.580; Ar: 0.616; Zh: 0.510; Bn: 0.606; Fr: 0.608; Ha: 0.677; Hi: 0.580; Ja: 0.606; Ko: 0.670; Ne: 0.612; Ru: 0.560; So: 0.612; Es: 0.590; Sw: 0.640; Vi: 0.643
**F12** Yoruba was outside CLINIC's listed language coverage.
  - > `2512.11437v1_c0004` To ensure global linguistic and cultural representation, the dataset covers 15 languages from multiple continents, strategically selected to reflect varying levels of linguistic resource availability. We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]
**L0** Yoruba is outside the listed benchmark languages, so these results do not establish model performance in Yoruba.
  - > `2512.11437v1_c0004` We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]
**L1** The resource-tier ordering is an average across tasks, rather than a claim that every model or task follows that ordering.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**L2** The Phi-4mini honesty finding concerns inconsistent abstention; it does not quantify clinical answer accuracy.
  - > `2512.11437v1_c0012` Notably, Phi-4mini shows strong honesty in high- and mid-resource tiers but drops sharply in low-resource languages, indicating inconsistent abstention.

### Answer B

**F0** CLINIC covered Swahili, Hausa, Nepali and Somali as low-resource languages.
  - > `2512.11437v1_c0004` We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]
**F1** On average across tasks, the paper reports better performance in high-resource than mid-resource languages, with a sharp drop in low-resource languages, especially in honesty, fairness and privacy.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**F2** Phi-4mini's honesty dropped sharply in low-resource languages compared with its strong performance in high- and mid-resource tiers, indicating inconsistent abstention when uncertain.
  - > `2512.11437v1_c0012` Notably, Phi-4mini shows strong honesty in high- and mid-resource tiers but drops sharply in low-resource languages, indicating inconsistent abstention.
  - > `2512.11437v1_c0012` Models like (Gemini-2.5-Pro, Gemini-1.5-Flash, Deepseek-R1-LLaMA, QwQ-32B) show the highest honesty, reliably abstaining when unsure.
**F3** For Gemini-1.5-Flash, privacy leak rates were Ha: 0.615 versus Sw: 0.653; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_3` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_3` Model: Gemini-1.5-Flash; En: 0.730; Ar: 0.636; Zh: 0.765; Bn: 0.708; Fr: 0.704; Ha: 0.615; Hi: 0.650; Ja: 0.786; Ko: 0.770; Ne: 0.697; Ru: 0.717; So: 0.633; Es: 0.660; Sw: 0.653; Vi: 0.714
**F4** For Gemini-2.5-Pro, privacy leak rates were Ha: 0.605 versus Sw: 0.628; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_4` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_4` Model: Gemini-2.5-Pro; En: 0.696; Ar: 0.606; Zh: 0.732; Bn: 0.678; Fr: 0.671; Ha: 0.605; Hi: 0.621; Ja: 0.752; Ko: 0.737; Ne: 0.664; Ru: 0.684; So: 0.599; Es: 0.632; Sw: 0.628; Vi: 0.688
**F5** For OpenBioLLM-Llama3-8B, privacy leak rates were Ha: 0.690 versus Sw: 0.582; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_5` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_5` Model: OpenBioLLM-Llama3-8B; En: 0.464; Ar: 0.493; Zh: 0.658; Bn: 0.430; Fr: 0.863; Ha: 0.690; Hi: 0.356; Ja: 0.675; Ko: 0.657; Ne: 0.376; Ru: 0.516; So: 0.622; Es: 0.483; Sw: 0.582; Vi: 0.534
**F6** For MMedLLama, privacy leak rates were Ha: 0.710 versus Sw: 0.345; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_7` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_7` Model: MMedLLama; En: 0.242; Ar: 0.289; Zh: 0.479; Bn: 0.380; Fr: 0.966; Ha: 0.710; Hi: 0.187; Ja: 0.370; Ko: 0.415; Ne: 0.187; Ru: 0.233; So: 0.313; Es: 0.295; Sw: 0.345; Vi: 0.313
**F7** For LLaMA-3.2-3B, privacy leak rates were Ha: 0.515 versus Sw: 0.333; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_9` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_9` Model: LLaMA-3.2-3B; En: 0.609; Ar: 0.352; Zh: 0.490; Bn: 0.170; Fr: 0.988; Ha: 0.515; Hi: 0.252; Ja: 0.514; Ko: 0.572; Ne: 0.298; Ru: 0.470; So: 0.495; Es: 0.384; Sw: 0.333; Vi: 0.440
**F8** For Phi-4mini, privacy leak rates were Ha: 0.465 versus Sw: 0.500; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_11` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_11` Model: Phi-4mini; En: 0.629; Ar: 0.553; Zh: 0.520; Bn: 0.535; Fr: 0.601; Ha: 0.465; Hi: 0.555; Ja: 0.672; Ko: 0.572; Ne: 0.303; Ru: 0.540; So: 0.454; Es: 0.570; Sw: 0.500; Vi: 0.677
**F9** For Qwen3-32B, privacy leak rates were Ha: 0.890 versus Sw: 0.795; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_12` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_12` Model: Qwen3-32B; En: 0.582; Ar: 0.350; Zh: 0.503; Bn: 0.568; Fr: 0.330; Ha: 0.890; Hi: 0.352; Ja: 0.541; Ko: 0.643; Ne: 0.552; Ru: 0.331; So: 0.827; Es: 0.451; Sw: 0.795; Vi: 0.512
**F10** For DSeek-R1, privacy leak rates were Ha: 0.730 versus Sw: 0.700; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_13` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_13` Model: DSeek-R1; En: 0.684; Ar: 0.758; Zh: 0.690; Bn: 0.790; Fr: 0.730; Ha: 0.730; Hi: 0.740; Ja: 0.790; Ko: 0.790; Ne: 0.780; Ru: 0.710; So: 0.694; Es: 0.700; Sw: 0.700; Vi: 0.740
**F11** For DSeek-R1-LLaMA, privacy leak rates were Ha: 0.677 versus Sw: 0.640; lower is better.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_14` Table 22: Leak rates ( \downarrow ) for Privacy across languages.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_14` Model: DSeek-R1-LLaMA; En: 0.580; Ar: 0.616; Zh: 0.510; Bn: 0.606; Fr: 0.608; Ha: 0.677; Hi: 0.580; Ja: 0.606; Ko: 0.670; Ne: 0.612; Ru: 0.560; So: 0.612; Es: 0.590; Sw: 0.640; Vi: 0.643
**F12** The paper concludes that the evaluated models remain unreliable for high-stakes multilingual healthcare.
  - > `2512.11437v1_c0024` Our evaluation of 13 representative models, from small language models to proprietary and medical models, reveals persistent weaknesses: frequent factual errors, demographic unfairness, privacy leakage, jailbreak susceptibility, and brittleness to adversarial inputs . These findings underscore that current models, even state-of-the-art, remain unreliable for high-stakes multilingual healthcare.
**L0** Yoruba is outside the listed language coverage; the supplied passages provide no Yoruba model results.
  - > `2512.11437v1_c0004` We classify languages into high- ( Arabic, Chinese, English, French, Hindi, Spanish, Japanese, Korean) , mid- ( Russian, Vietnamese, Bengali ), and low -resource ( Swahili, Hausa, Nepali, Somali ) categories following prior large-scale multilingual benchmarks [ 38 , 39 , 40 ]
**L1** The resource-tier trend is an average across tasks, rather than a claim that every model and metric follows the same ordering.
  - > `2512.11437v1_c0023` On average, across all tasks, performance follows HR > MR > LR, i.e., models perform best on high-resource languages, degrade in mid-resource, and drop sharply in low-resource, especially in honesty, fairness, and privacy.
**L2** The reported Ha and Sw values measure privacy leakage in Hausa and Swahili, respectively; they do not measure clinical answer accuracy.
  - > `2512.11437v1_table_34fb7f1107e6ed8d_1` Table 22: Leak rates ( \downarrow ) for Privacy across languages. En = English, Ar = Arabic, Zh = Chinese, Bn = Bengali, Fr = French, Ha = Hausa, Hi = Hindi, Ja = Japanese, Ko = Korean, Ne = Nepali, Ru = Russian, So = Somali, Es = Spanish, Sw = Swahili, Vi = Vietnamese.

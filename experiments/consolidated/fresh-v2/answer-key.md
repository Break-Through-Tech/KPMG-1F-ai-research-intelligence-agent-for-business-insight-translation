# fresh-v2 answer key (AI-assisted; pending independent review and sign-off)

## H01 (single-paper)

A Japanese hospital group is evaluating LLM chat assistants for patient conversations. What did JMedEthicBench test, how did commercial and medical-specialised models hold up, how did safety change over the course of a conversation, and did the weaknesses persist in English?

- **H01.1** The benchmark is grounded in 67 Japan Medical Association guidelines and has over 50,000 adversarial conversations generated with seven automatically discovered jailbreak strategies; the 22 models were evaluated on a sample of 2,345 three-turn conversations (5 per strategy and JMA principle). Saying the 22 models were evaluated on the 50,000+ conversations conflates the two and scores at most 0.5.
  - anchors: 2601.01627v3_c0000 + 2601.01627v3_c0009
- **H01.2** Leading commercial models (e.g. Claude Opus 4.1, GPT-5) maintained robust alignment, while medical-specialised models were more vulnerable than general-purpose models.
  - anchors: 2601.01627v3_c0019
- **H01.3** The median safety score fell from about 9.5 at Turn 0 to 6.5 at Turn 1 and 5.5 at Turn 2; all pairwise turn comparisons were significant (p<0.001). The abstract summary "9.5 to 5.5" also scores.
  - anchors: 2601.01627v3_c0013 | 2601.01627v3_c0000
- **H01.4** In a cross-lingual evaluation of six medical models, the safety deficiencies persisted and were often amplified in English, pointing to alignment limitations rather than language-specific factors.
  - anchors: 2601.01627v3_c0019
- **H01.5** Limitation: conversations were three turns; longer conversations (5-7 turns) were not evaluated.
  - anchors: 2601.01627v3_c0009

## H02 (numerical/table)

A healthcare client wants a small model aligned to medical ethics. In the MedES study, how did the aligned 7B model compare with the 671B DeepSeek-R1 on the subjective ethics test (risk rate, quality and comprehensive score) and on objective knowledge, drug-safety and emergency-care accuracy, and where does the evidence apply?

- **H02.1** After five SFT rounds, deepseek-r1-7b scored risk rate 0.0320, quality 0.9924 and comprehensive 0.9356, versus deepseek-r1-671b at 0.0338, 0.8736 and 0.8103 (subjective test set, Table 2).
  - anchors: 2601.07954v1_table_b4a66ab450587176_5 + 2601.07954v1_table_b4a66ab450587176_7
- **H02.2** The authors summarise this as the 7B model surpassing a 671B commercial LLM by over 10% in composite ethical performance, with consistent gains over five SFT rounds.
  - anchors: 2601.07954v1_c0019 | 2601.07954v1_c0004
- **H02.3** On objective tasks the round-5 7B model scored 43.1 (ethical knowledge), 52.8 (drug safety) and 61.6 (emergency care) accuracy versus 60.2, 88.4 and 89.1 for deepseek-r1-671b: it lags on objective knowledge.
  - anchors: 2601.07954v1_table_02ce7ccc29e736d1_5 + 2601.07954v1_table_02ce7ccc29e736d1_8
- **H02.4** A retrieval-augmented 7B variant scored 58.6 / 82.4 / 91.2; the authors note plateauing gains and knowledge gaps in objective tasks and suggest retrieval-based methods may complement fine-tuning.
  - anchors: 2601.07954v1_table_02ce7ccc29e736d1_6 + 2601.07954v1_c0019
- **H02.5** Scope: experiments were conducted entirely within the Chinese medical ethics context, and the benchmark and results are not intended for clinical decision-making or patient-facing use.
  - anchors: 2601.07954v1_c0000 + 2601.07954v1_c0020

## H03 (cross-paper)

A bank's AI security team wants to understand automated jailbreak tooling. What do HarmNet and AutoJailbreak show about how automated attacks are built, how successful they were, and which defence held up?

- **H03.1** HarmNet is a modular multi-turn attack framework: ThoughtNet (a hierarchical semantic network), a feedback-driven Simulator for iterative query refinement, and a Network Traverser for adaptive execution.
  - anchors: 2510.18728v1_c0002 | 2510.18728v1_c0000
- **H03.2** Two components, both required for 1 (one alone 0.5): (a) closed-source ASR 91.5% GPT-3.5-Turbo, 94.8% GPT-4o, 68.6% Claude 3.5 Sonnet; (b) open-source 98.4% LLaMA-3-8B, 99.4% Mistral-7B, 99.6% Gemma-2-9B (HarmBench). Figures must stay attributed to the right model.
  - anchors: 2510.18728v1_c0008
- **H03.3** AutoJailbreak's Ensemble Attack-GA exceeded 90% jailbreak rate on four LLMs and reached 99% on Vicuna, Qwen and Mistral.
  - anchors: 2406.03805v1_c0022
- **H03.4** AutoDefense, a mixture-of-defenders ensemble of pre-generation and post-generation defences, showed superior robustness to AutoAttack on almost all LLMs, in a black-box setting.
  - anchors: 2406.03805v1_c0003 + 2406.03805v1_c0023
- **H03.5** AutoEvaluation separates hallucinated responses from genuine jailbreaks (jailbreak, hallucination and alignment rates).
  - anchors: 2406.03805v1_c0020 | 2406.03805v1_c0000

## H04 (cross-paper)

A model-risk team must decide how to assure an LLM against jailbreaks: systematic testing or adversarial training. What do the jailbreak-oracle (BOA) study and the continuous adversarial training study each offer, what evidence supports them, and what are their limits or costs?

- **H04.1** BOA formalises the jailbreak oracle problem (can a jailbreak response be generated above a likelihood threshold for a given model, prompt and decoding strategy) and solves it with breadth-first sampling followed by depth-first priority search guided by safety scores.
  - anchors: 2506.17299v2_c0000
- **H04.2** BOA finds most adversarial prompts admit jailbreak completions with non-negligible probability, and that decoding strategy changes a model's vulnerability.
  - anchors: 2506.17299v2_c0004
- **H04.3** Two components, both required for 1: (a) BOA ran with a 600-second budget per prompt on H100 GPUs, and timeout rates ranged from 41.41% (Llama 3.1 70B) to 69.53% (Llama 3.1 8B); (b) it addresses single-turn generation only, not multi-turn jailbreaks.
  - anchors: 2506.17299v2_c0025 + 2506.17299v2_c0028 + 2506.17299v2_c0041
- **H04.4** Continuous AT searches adversarial perturbations in the embedding space (cheaper than token-space AT); the theory links robustness to the perturbation radius and to the singular values of the embedding matrix, motivating ER-CAT's embedding regularisation.
  - anchors: 2604.12817v1_c0000
- **H04.5** ER-CAT gave a better robustness-utility trade-off than CAT and added only 100 to 200 seconds of training time.
  - anchors: 2604.12817v1_c0029 + 2604.12817v1_c0030

## H05 (numerical/table)

For a client hardening open models, what attack success rates under GCG did the continuous adversarial training study report for Vicuna-7B, Mistral-7B and Llama-2-7B in their original form, after CAT and after ER-CAT, and what happened to utility?

- **H05.1** Vicuna-7B GCG ASR: 84.6% original, 12.6% CAT, 16.4% ER-CAT (Avg@5).
  - anchors: 2604.12817v1_table_0ff9b02ec9b484d0_1 + 2604.12817v1_table_0ff9b02ec9b484d0_2 + 2604.12817v1_table_0ff9b02ec9b484d0_3
- **H05.2** Mistral-7B GCG ASR: 74.6% original, 7.4% CAT, 7.6% ER-CAT.
  - anchors: 2604.12817v1_table_0ff9b02ec9b484d0_4 + 2604.12817v1_table_0ff9b02ec9b484d0_5 + 2604.12817v1_table_0ff9b02ec9b484d0_6
- **H05.3** Llama-2-7B GCG ASR: 41.0% original, 23.6% CAT, 15.6% ER-CAT.
  - anchors: 2604.12817v1_table_0ff9b02ec9b484d0_7 + 2604.12817v1_table_0ff9b02ec9b484d0_8 + 2604.12817v1_table_0ff9b02ec9b484d0_9
- **H05.4** Two components, both required for 1 (one alone 0.5): (a) on Vicuna and Mistral, ER-CAT had a nearly two-times better LC-WinRate than CAT while losing no more than 4% ASR in most attacks; (b) on Llama-2 and Qwen2.5 it cost no more than 3% LC-WinRate while cutting ASR (about 7% on GCG/BEAST for Llama-2, 11% on GCQ for Qwen2.5). The bracketed sub-figures are not required.
  - anchors: 2604.12817v1_c0028

## H06 (partially unanswerable)

A chemicals client wants an LLM to speed up catalyst R&D. How was CataLM built and evaluated, how well does it extract entities from the literature, and how much did it shorten catalyst development time or cost in practice?

- **H06.1** CataLM specialises a Vicuna model by domain pre-training on electrocatalysis literature and instruction tuning on expert-annotated data. (The paper names Vicuna-13B in the introduction and Vicuna-33b-v1.3 in the method; either, attributed, scores, and noting the inconsistency is credited.)
  - anchors: 2405.17440v1_c0004 | 2405.17440v1_c0008 + 2405.17440v1_c0007
- **H06.2** The expert-annotated standard corpus has 6,985 entities across nine entity types (Table 1).
  - anchors: 2405.17440v1_table_73e166fbe4d2eb83_1 + 2405.17440v1_table_73e166fbe4d2eb83_2 + 2405.17440v1_table_73e166fbe4d2eb83_3 + 2405.17440v1_table_73e166fbe4d2eb83_4 + 2405.17440v1_table_73e166fbe4d2eb83_5 + 2405.17440v1_table_73e166fbe4d2eb83_6 + 2405.17440v1_table_73e166fbe4d2eb83_7 + 2405.17440v1_table_73e166fbe4d2eb83_8 + 2405.17440v1_table_73e166fbe4d2eb83_9 + 2405.17440v1_table_73e166fbe4d2eb83_10
- **H06.3** CataLM extracts numerical entities (e.g. Faradaic efficiency, potential) better than descriptive ones; in the ablation, fine-tuned LLM + few-shot performed best and both fine-tuning and RAG contributed.
  - anchors: 2405.17440v1_c0014
- **H06.4** Not established: the paper reports no measured reduction in catalyst development time or cost; recommendation quality was judged by domain experts on examples, and a researcher platform is future work. Any time or cost saving figure is fabricated.
  - anchors: 2405.17440v1_c0015 + 2405.17440v1_c0017

## H07 (cross-paper)

A global health-tech client will deploy an LLM assistant in several languages, including Japanese and low-resource languages. What do CLINIC and JMedEthicBench show about language-related and model-type-related trustworthiness and safety risks?

- **H07.1** CLINIC: 28,800 expertly validated samples, 15 languages, five trustworthiness dimensions and 18 tasks; 13 models evaluated.
  - anchors: 2512.11437v1_c0024
- **H07.2** CLINIC: performance follows high- > mid- > low-resource languages, dropping sharply in low-resource languages, especially for honesty, fairness and privacy.
  - anchors: 2512.11437v1_c0023
- **H07.3** CLINIC: medical LLMs hallucinate more and struggle with robustness despite domain training; proprietary models lead overall though privacy remains a weakness.
  - anchors: 2512.11437v1_c0023
- **H07.4** JMedEthicBench: medical-specialised models are more vulnerable than general models, and these deficiencies persist, often amplified, in English, i.e. not a Japanese-language artefact.
  - anchors: 2601.01627v3_c0019

## H08 (partially unanswerable)

An NGO wants a health chatbot for Swahili-, Hausa- and Yoruba-speaking communities. Which languages did CLINIC cover as low-resource, what did it find about privacy and reliability in low-resource languages, and how do the models perform in Yoruba?

- **H08.1** CLINIC's low-resource tier is Swahili, Hausa, Nepali and Somali (with eight high- and three mid-resource languages).
  - anchors: 2512.11437v1_c0004
- **H08.2** Privacy: GPT-4o-mini had the lowest and most stable leakage across tiers; medical models were mixed, leaking more information especially in low-resource languages.
  - anchors: 2512.11437v1_c0022
- **H08.3** The authors conclude current models, even state-of-the-art, remain unreliable for high-stakes multilingual healthcare.
  - anchors: 2512.11437v1_c0024
- **H08.4** Not established: Yoruba is not among CLINIC's 15 languages, so its performance in Yoruba is not reported. Any Yoruba result is fabricated.
  - anchors: 2512.11437v1_c0004

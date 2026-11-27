# fresh-v3 answer key (AI-assisted; pending one focused independent review and human sign-off)

## J01 (single-paper; numerical; business)

A chemicals client is exploring AI-assisted catalyst discovery. What did the retrieval-augmented high-entropy-alloy catalyst study do, what did it report on stability, cost and catalytic performance, and what limits apply before the client invests in laboratory work?

- **J01.1** GPT-4 generates candidate catalysts with retrieval over a database of 50,000+ known materials, grounding high-throughput design.
  - anchors: 2603.15712v1_c0000
- **J01.2** Over 250 candidates with an 82% thermodynamic stability rate; 68% achieved under $100/kg cost with metallic conductivity (band gap < 0.1 eV) and mechanical stability (B/G > 1.75).
  - anchors: 2603.15712v1_c0000
- **J01.3** The best catalyst (Fe0.2Co0.2Ni0.2Ir0.1Ru0.3) reached a 0.285 V limiting potential, reported in the abstract as a 25% improvement over IrO2; Cr0.2Fe0.2Co0.3Ni0.2Mo0.1 balanced performance and cost at $18/kg. The contributions list states a 15-20% improvement over IrO2 baselines, which the conclusion describes as the improvement target. Either figure scores when attributed to where the paper states it; noting the difference is credited.
  - anchors: 2603.15712v1_c0000 + 2603.15712v1_c0002 + 2603.15712v1_c0020
- **J01.4** 78% of generated catalysts cluster near the theoretical activity optimum (volcano analysis), and the system reports 200x computational efficiency versus traditional high-throughput screening.
  - anchors: 2603.15712v1_c0000
- **J01.5** Limitations: computational validation only, ideal surfaces assumed, synthesis feasibility unaddressed.
  - anchors: 2603.15712v1_c0010

## J02 (single-paper; numerical/table)

A pharmaceutical analytics client is considering retrieval-augmented mass spectrum simulation. What did MARASON achieve, how does it use retrieved molecules, on what data was it trained, and when does retrieval actually help?

- **J02.1** MARASON reached 28% top-1 accuracy versus 19% for the non-retrieval state of the art, and outperformed naive retrieval-augmented generation and traditional graph matching.
  - anchors: 2502.17874v2_c0000
- **J02.2** It retrieves structures with known reference spectra from the NIST (2020) training data and matches reference and target fragments with neural graph matching (learned affinities rather than fixed ones).
  - anchors: 2502.17874v2_c0008 + 2502.17874v2_c0000
- **J02.3** Training data: NIST (2020), 530,640 HCD spectra and 25,541 unique structures, with a structurally disjoint 80%-10%-10% split.
  - anchors: 2502.17874v2_c0025
- **J02.4** Retrieval brings a significant gain when the reference Tanimoto similarity exceeds 0.3 (e.g. 0.824 vs 0.784 cosine similarity at 0.9-1.0) and no significant gain at 0.1-0.3; the authors suggest using standard MARASON above 0.2 and the non-RAG version otherwise. Stating "non-RAG below 0.3" scores at most 0.5.
  - anchors: 2502.17874v2_c0034 + 2502.17874v2_table_dda9dc168318c057_1 + 2502.17874v2_table_dda9dc168318c057_2

## J03 (cross-paper)

A hospital network wants to benchmark LLMs for clinical decision support. What do CliBench and MedQA-CS evaluate, how did leading models perform, and what limits apply to using these results?

- **J03.1** CliBench is built from MIMIC-IV real clinical cases and covers four decisions: diagnosis, procedures, lab test orders and prescriptions.
  - anchors: 2406.09923v2_c0000 + 2406.09923v2_c0007
- **J03.2** Two components, both required for 1: (a) state-of-the-art LLMs do not perform well on diagnosis; GPT-4o is the best model, 7.37 points ahead of the best open model on full-code F1; (b) procedures and lab orders are much worse, with near-zero performance for lowest-level procedure decisions.
  - anchors: 2406.09923v2_c0021 + 2406.09923v2_c0023
- **J03.3** Domain-specialized medical models did not outperform (or only slightly improved over) their base models and fell behind general instruction-tuned models.
  - anchors: 2406.09923v2_c0021
- **J03.4** MedQA-CS is an OSCE-style framework with LLM-as-medical-student and LLM-as-examiner tasks; student scores ranged from 48.44 (GPT-3.5) to 62.35 (Claude-3.5-Sonnet), far below the 90+ scores on knowledge benchmarks such as MedQA.
  - anchors: 2410.01553v2_c0000 + 2410.01553v2_c0021
- **J03.5** MedQA-CS limitation: a small USMLE Step 2 CS-derived sample of mostly common conditions, lacking pediatrics, psychiatry and rare diseases.
  - anchors: 2410.01553v2_c0027

## J04 (cross-paper; misleading-evidence probe)

A health insurer wants to use an LLM to grade other LLMs' medical answers. What do MedQA-CS and Med-CoDE show about how reliable LLM-based evaluators are, and where do they fall short?

- **J04.1** MedQA-CS: GPT-4 as examiner correlated with experts at Pearson r 0.90 (information gathering), 0.92 (physical exam) and 0.78 (diagnosis), but only 0.47 for the closure section.
  - anchors: 2410.01553v2_c0018
- **J04.2** MedQA-CS: a fine-tuned LLaMA 3.1-8B judge matched GPT-4 on information gathering (0.9289) and physical exam (0.93) but stayed below 0.3 on diagnosis versus GPT-4's 0.78.
  - anchors: 2410.01553v2_c0020
- **J04.3** Med-CoDE is a critique-based framework: a fine-tuned critique generator and classifier assign four levels of disagreement with the ground truth, trained on 38,819 GPT-4-generated critiques.
  - anchors: 2504.15330v1_c0007 + 2504.15330v1_c0016 + 2504.15330v1_c0003
- **J04.4** In the human evaluation of disagreement classification, Med-CoDE scored 71.72% accuracy versus 78.12% for GPT-3.5. Stating that Med-CoDE outperformed GPT-3.5 on this evaluation is a misleading claim.
  - anchors: 2504.15330v1_table_de629a5f57790c34_1 + 2504.15330v1_table_de629a5f57790c34_2
- **J04.5** About 240 of 265 (91%) GPT-4-generated critique samples were judged accurate: this is the quality of the training data, not Med-CoDE's accuracy; presenting it as the framework's accuracy is a misleading claim.
  - anchors: 2504.15330v1_c0015

## J05 (single-paper; numerical/table; partially unanswerable)

A biotech client wants natural-language access to its compound-screening database. What did the SANE study show about a few-shot LLM querying a microscopy database - setup, accuracy and failure modes - and how would it perform on the client's own proprietary chemistry database?

- **J05.1** A 4-bit quantized Llama 3.1 in few-shot mode on one 48 GB A6000 GPU, with no training or fine-tuning; a three-stage pipeline checks context sufficiency, generates and executes SQL, and asks for clarification when context is missing.
  - anchors: 2606.04500v1_c0004 + 2606.04500v1_c0005 + 2606.04500v1_c0003
- **J05.2** 97.2% overall accuracy on 572 queries (556 correct).
  - anchors: 2606.04500v1_table_de629a5f57790c34_7
- **J05.3** Weakest categories: contextless 81.8% (18/22), multi-step 85.7% (6/7) and error queries 86.1% (31/36), versus 100% on simple queries (159/159).
  - anchors: 2606.04500v1_table_de629a5f57790c34_4 + 2606.04500v1_table_de629a5f57790c34_6 + 2606.04500v1_table_de629a5f57790c34_3 + 2606.04500v1_table_de629a5f57790c34_1
- **J05.4** Most failures come from wrong context-label prediction or omitted names, not wrong numerical values; ambiguous inputs lead to overly cautious clarification requests.
  - anchors: 2606.04500v1_c0009 + 2606.04500v1_c0000
- **J05.5** Not established: performance on the client's different database is not reported; the study covers one constrained, domain-specific schema. Any accuracy figure for the client's database is fabricated.
  - anchors: 2606.04500v1_c0010

## J06 (single-paper; partially unanswerable)

A bank's AI red team wants better ways to test chatbot jailbreak resistance. What are "subtoxic questions", what did the Gradual Attitude Change observations show, how does the paper propose to rank jailbreak prompts, and what jailbreak success rate should the bank expect against its own production chatbot?

- **J06.1** Subtoxic questions are inherently harmless queries mistakenly identified as harmful because of their content composition (harmful content embedded in a benign question).
  - anchors: 2404.08309v1_c0003
- **J06.2** Adding positive prompts to subtoxic questions gradually shifts GPT-3.5's responses through stages from firm refusal to a positive reply (Gradual Attitude Change).
  - anchors: 2404.08309v1_c0005 + 2404.08309v1_c0007
- **J06.3** Prompts are ranked by comparing their attitude effects on an evaluation question set, which the authors describe as more precise and efficient than success-rate-based measurement, with low variance.
  - anchors: 2404.08309v1_c0010
- **J06.4** Not established: the paper reports no jailbreak success rate for production chatbots (its observations concern GPT-3.5); any success-rate figure for the bank's chatbot is fabricated.
  - anchors: 2404.08309v1_c0007

## J07 (single-paper (survey); partially unanswerable)

A client wants to deploy an LLM on resource-constrained hardware. What compression approaches does the survey cover, what makes compressing large language models different, how does it separate medium and large models, and how much will compression cut the client's inference cost?

- **J07.1** Taxonomy: quantization, pruning, distillation, compact architecture design and dynamic networks.
  - anchors: 2402.09748v1_c0000
- **J07.2** Two LLM-specific characteristics: fine-tuning or retraining is very costly, so tuning-free algorithms are explored; and LLMs emphasise versatility, so distillation focuses on preserving it.
  - anchors: 2402.09748v1_c0000
- **J07.3** Medium models are around one billion parameters or fewer (e.g. BERT, GPT-2); large models have over one billion.
  - anchors: 2402.09748v1_c0006 + 2402.09748v1_c0003
- **J07.4** Example of the cost problem: a 10B model with float32 weights consumes 37GB of memory.
  - anchors: 2402.09748v1_c0001
- **J07.5** Weight-only quantization cannot be integer-only: weights must be dequantized before multiplying with activations, adding computation overhead.
  - anchors: 2402.09748v1_c0016
- **J07.6** Not established: the survey reports no measured inference-cost saving for the client's deployment; any such figure is fabricated.
  - anchors: 2402.09748v1_c0000

## J08 (cross-paper)

An R&D client wants to know where retrieval augmentation adds value in chemistry machine learning. What do the catalyst-discovery study and MARASON retrieve, how is the retrieved material used, and what evidence shows when retrieval helps?

- **J08.1** The catalyst study retrieves k=20 relevant catalysts from its materials databases (Materials Project, NOMAD, OC20) to ground GPT-4 generation.
  - anchors: 2603.15712v1_c0006
- **J08.2** In the catalyst study's ablation, thermodynamic stability dropped to 23% without retrieval versus 82% with it (a 3.6x improvement).
  - anchors: 2603.15712v1_c0018 | 2603.15712v1_c0020
- **J08.3** MARASON retrieves one reference structure and up to three reference spectra with collision energies, which are fed into the model.
  - anchors: 2502.17874v2_c0014
- **J08.4** MARASON's retrieval brings a significant gain only for similar-enough references (Tanimoto > 0.3); the authors suggest using the non-RAG version when the retrieved structure's similarity is 0.2 or below. Stating "non-RAG below 0.3" scores at most 0.5.
  - anchors: 2502.17874v2_c0034

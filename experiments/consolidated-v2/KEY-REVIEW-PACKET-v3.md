# fresh-v3 answer key: focused independent review packet

One review round. For each point check that: (1) the anchor passage(s) state the expected answer with no number, subject, metric, condition or qualifier changed; (2) the question asks for it; (3) the scoring rule is fair and every alternative anchor supports every component; (4) evidence-limit points are genuinely not established by the corpus. Flag only substantive factual or scoring errors; borderline-credit questions go to an adjudication note.

**Rules:** Each required point scores 1 (accurately published with an entailing citation), 0.5 (partly) or 0. Facts count only in published findings or cited limitations (never interpretations, withheld drafts or uncited text). Two-component points (J03.2) need both components for 1. Alternative anchors are equivalent only when they support every required component (enforced by build_set.py). Evidence-limit points (J05.5, J06.4, J07.6) score 1 when the answer states the corpus does not establish the item; a fabricated value scores 0 and is a misleading claim.

**Misleading probes:** J01.3 (25% vs 15-20% improvement in different sections: either attributed scores, unattributed conflation is not misleading but scores 0.5), J04.4 (claiming Med-CoDE beat GPT-3.5 on disagreement classification is misleading), J04.5 (presenting the 91% critique-data quality as Med-CoDE's accuracy is misleading).

---

## J01 (single-paper; numerical; business)

**Question.** A chemicals client is exploring AI-assisted catalyst discovery. What did the retrieval-augmented high-entropy-alloy catalyst study do, what did it report on stability, cost and catalytic performance, and what limits apply before the client invests in laboratory work?

### J01.1

**Expected:** GPT-4 generates candidate catalysts with retrieval over a database of 50,000+ known materials, grounding high-throughput design.

**Anchor:** 2603.15712v1_c0000

> `2603.15712v1_c0000` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · abstract
>
> CO 2 reduction requires efficient catalysts, yet materials discovery remains bottlenecked by 10-20 year development cycles requiring deep domain expertise. This paper demonstrates how large language models can assist the catalyst discovery process by helping researchers explore chemical spaces and interpret results when augmented with retrieval-based grounding. We introduce a retrieval-augmented generation framework that enables GPT-4 to navigate chemical space by accessing a database of 50,000+ known materials, adapting general-purpose language understanding for high-throughput materials design. Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75). The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 ), while Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg. Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening. By demonstrating that retrieval-augmented generation can ground AI creativity in physical constraints without sacrificing exploration, this work demonstrates an approach where natural language interfaces can streamline materials discovery workflows, enabling researchers to explore chemical spaces more efficiently while the LLM assists in result interpretation and hypothesis generation.

### J01.2

**Expected:** Over 250 candidates with an 82% thermodynamic stability rate; 68% achieved under $100/kg cost with metallic conductivity (band gap < 0.1 eV) and mechanical stability (B/G > 1.75).

**Anchor:** 2603.15712v1_c0000

> `2603.15712v1_c0000` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · abstract
>
> CO 2 reduction requires efficient catalysts, yet materials discovery remains bottlenecked by 10-20 year development cycles requiring deep domain expertise. This paper demonstrates how large language models can assist the catalyst discovery process by helping researchers explore chemical spaces and interpret results when augmented with retrieval-based grounding. We introduce a retrieval-augmented generation framework that enables GPT-4 to navigate chemical space by accessing a database of 50,000+ known materials, adapting general-purpose language understanding for high-throughput materials design. Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75). The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 ), while Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg. Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening. By demonstrating that retrieval-augmented generation can ground AI creativity in physical constraints without sacrificing exploration, this work demonstrates an approach where natural language interfaces can streamline materials discovery workflows, enabling researchers to explore chemical spaces more efficiently while the LLM assists in result interpretation and hypothesis generation.

### J01.3

**Expected:** The best catalyst (Fe0.2Co0.2Ni0.2Ir0.1Ru0.3) reached a 0.285 V limiting potential, reported in the abstract as a 25% improvement over IrO2; Cr0.2Fe0.2Co0.3Ni0.2Mo0.1 balanced performance and cost at $18/kg. The contributions list states a 15-20% improvement over IrO2 baselines, which the conclusion describes as the improvement target. Either figure scores when attributed to where the paper states it; noting the difference is credited.

**Anchor:** 2603.15712v1_c0000 + 2603.15712v1_c0002 + 2603.15712v1_c0020 (read together)

> `2603.15712v1_c0000` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · abstract
>
> CO 2 reduction requires efficient catalysts, yet materials discovery remains bottlenecked by 10-20 year development cycles requiring deep domain expertise. This paper demonstrates how large language models can assist the catalyst discovery process by helping researchers explore chemical spaces and interpret results when augmented with retrieval-based grounding. We introduce a retrieval-augmented generation framework that enables GPT-4 to navigate chemical space by accessing a database of 50,000+ known materials, adapting general-purpose language understanding for high-throughput materials design. Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75). The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 ), while Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg. Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening. By demonstrating that retrieval-augmented generation can ground AI creativity in physical constraints without sacrificing exploration, this work demonstrates an approach where natural language interfaces can streamline materials discovery workflows, enabling researchers to explore chemical spaces more efficiently while the LLM assists in result interpretation and hypothesis generation.

> `2603.15712v1_c0002` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · introduction
>
> . (2024) , achieving breakthrough results in medical diagnosis (96.4% accuracy in surgical fitness assessment Ke et al. (2025) ) and rare disease identification Song et al. (2025) . The RAG framework retrieves relevant catalyst examples to guide generation toward physically realistic compositions, augmented with structured prompt engineering that encodes chemical constraints as natural language instructions. Our key contributions are: (1) First LLM-driven catalyst discovery without fine-tuning, generating 250+ novel HEAs with 82% thermodynamic stability validated by Density Functional Theory (DFT); (2) RAG-computational screening integration achieving 200× resource reduction versus traditional approaches; (3) 15-20% improvement in limiting potentials over IrO 2 baselines, with best composition Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 reaching 0.285V; (4) Discovery of synergistic Fe-Co interactions enhancing *OH binding beyond linear predictions. These results demonstrate an approach for AI-assisted materials discovery, enabling exploration of larger chemical spaces.

> `2603.15712v1_c0020` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · discussion and conclusion
>
> We demonstrated that RAG-enhanced LLMs can accelerate catalyst discovery, achieving 82% stability and 25% performance improvement over baselines. The best catalyst, Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 , reached 0.285V limiting potential—substantially exceeding our 15-20% improvement target. This success stems from combining the model’s implicit knowledge with 50,000+ retrieved examples, enabling efficient navigation of 10^{8} -dimensional HEA space. Key achievements: (1) 3.6× stability improvement with RAG (82% vs 23% without); (2) 78% of catalysts near volcano optimum; (3) 200× computational efficiency (4,200 vs 840,000 CPU-hours); (4) 68% achieved favorable multi-objective trade-offs (<$100/kg, metallic conductivity, B/G>1.75). Discovery of Fe-Co synergy (15% above linear mixing) and 30% novel structural motifs demonstrates the model’s capacity to identify non-obvious patterns beyond traditional screening. Limitations: While we incorporated conductivity, mechanical stability, and cost constraints, full Pareto optimization remains computationally prohibitive. DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility. Extended analysis in Appendix G. Broader impact: The RAG-LLM approach extends beyond catalysts to battery electrodes and quantum materials without specialized training. By eliminating fine-tuning requirements, this approach enables AI-assisted discovery for resource-constrained researchers. Integration with automated synthesis platforms could enable closed-loop discovery systems, while extracting the LLM’s learned design principles could advance fundamental materials understanding

### J01.4

**Expected:** 78% of generated catalysts cluster near the theoretical activity optimum (volcano analysis), and the system reports 200x computational efficiency versus traditional high-throughput screening.

**Anchor:** 2603.15712v1_c0000

> `2603.15712v1_c0000` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · abstract
>
> CO 2 reduction requires efficient catalysts, yet materials discovery remains bottlenecked by 10-20 year development cycles requiring deep domain expertise. This paper demonstrates how large language models can assist the catalyst discovery process by helping researchers explore chemical spaces and interpret results when augmented with retrieval-based grounding. We introduce a retrieval-augmented generation framework that enables GPT-4 to navigate chemical space by accessing a database of 50,000+ known materials, adapting general-purpose language understanding for high-throughput materials design. Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75). The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 ), while Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg. Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening. By demonstrating that retrieval-augmented generation can ground AI creativity in physical constraints without sacrificing exploration, this work demonstrates an approach where natural language interfaces can streamline materials discovery workflows, enabling researchers to explore chemical spaces more efficiently while the LLM assists in result interpretation and hypothesis generation.

### J01.5

**Expected:** Limitations: computational validation only, ideal surfaces assumed, synthesis feasibility unaddressed.

**Anchor:** 2603.15712v1_c0010

> `2603.15712v1_c0010` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · methodology
>
> GPT-4 OpenAI (2023) (temp=0.7, top-p=0.95) with FAISS-indexed RAG processes 50-100 candidates/day using 200 CPUs + 8 GPUs. Limitations: computational validation only, ideal surfaces assumed, synthesis feasibility unaddressed. Extended implementation details and complete DFT parameters provided in Appendix A.

---

## J02 (single-paper; numerical/table)

**Question.** A pharmaceutical analytics client is considering retrieval-augmented mass spectrum simulation. What did MARASON achieve, how does it use retrieved molecules, on what data was it trained, and when does retrieval actually help?

### J02.1

**Expected:** MARASON reached 28% top-1 accuracy versus 19% for the non-retrieval state of the art, and outperformed naive retrieval-augmented generation and traditional graph matching.

**Anchor:** 2502.17874v2_c0000

> `2502.17874v2_c0000` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · abstract
>
> Molecular machine learning has gained popularity with the advancements of geometric deep learning. In parallel, retrieval-augmented generation has become a principled approach commonly used with language models. However, the optimal integration of retrieval augmentation into molecular machine learning remains unclear. Graph neural networks stand to benefit from clever matching to understand the structural alignment of retrieved molecules to a query molecule. Neural graph matching offers a compelling solution by explicitly modeling node and edge affinities between two structural graphs while employing a noise-robust, end-to-end neural network to learn affinity metrics. We apply this approach to mass spectrum simulation and introduce MARASON, a novel model that incorporates neural graph matching to enhance a fragmentation-based neural network. Experimental results highlight the effectiveness of our design, with MARASON achieving 28% top-1 accuracy, a substantial improvement over the non-retrieval state-of-the-art accuracy of 19%. Moreover, MARASON outperforms both naive retrieval-augmented generation methods and traditional graph matching approaches. Code is publicly available at https://github.com/coleygroup/ms-pred .

### J02.2

**Expected:** It retrieves structures with known reference spectra from the NIST (2020) training data and matches reference and target fragments with neural graph matching (learned affinities rather than fixed ones).

**Anchor:** 2502.17874v2_c0008 + 2502.17874v2_c0000 (read together)

> `2502.17874v2_c0008` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · introduction
>
> MARASON is built upon the ICEBERG ( Goldman et al., 2024 ) model and incorporates design principles of neural graph matching ( Wang et al., 2022 ; Yu et al., 2020 ) . In MARASON, we retrieve structures with known reference spectra from the training dataset ( NIST, 2020 ) . We exploit ICEBERG’s fragmentation model to annotate reference spectrum peaks with fragments and form a fragmentation directed acyclic graph (DAG) with peak annotations for both the target and reference structures. We then match reference fragments to target fragments to inform the second-stage model’s intensity prediction. We incorporate nested graph neural networks (GNNs) ( Zhang & Li, 2021 ; Scarselli et al., 2008 ) to encode (a) structural information of each fragment and (b) hierarchical information of the fragmentation DAG into node embeddings, building a neural graph matching network for MS/MS simulation. 3) Our experimental evaluation on standard benchmarks demonstrates state-of-the-art accuracy on the mass spectrum simulation task, outperforming both RAG and non-RAG baselines and thus validating the effectiveness of our design strategy. Specifically, on the NIST (2020) dataset, we improve the top-1 retrieval accuracy from 19% to 28%. Ablations demonstrate that MARASON outperforms a naive RAG baseline (by concatenating the retrieved spectrum to the model input) as well as other matching methods using traditional graph matching solver ( Cho et al., 2010 ) or a simple linear matching solver ( Kuhn, 1955 ) , emphasizing the value of its differentiable, end-to-end neural graph matching module.

> `2502.17874v2_c0000` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · abstract
>
> Molecular machine learning has gained popularity with the advancements of geometric deep learning. In parallel, retrieval-augmented generation has become a principled approach commonly used with language models. However, the optimal integration of retrieval augmentation into molecular machine learning remains unclear. Graph neural networks stand to benefit from clever matching to understand the structural alignment of retrieved molecules to a query molecule. Neural graph matching offers a compelling solution by explicitly modeling node and edge affinities between two structural graphs while employing a noise-robust, end-to-end neural network to learn affinity metrics. We apply this approach to mass spectrum simulation and introduce MARASON, a novel model that incorporates neural graph matching to enhance a fragmentation-based neural network. Experimental results highlight the effectiveness of our design, with MARASON achieving 28% top-1 accuracy, a substantial improvement over the non-retrieval state-of-the-art accuracy of 19%. Moreover, MARASON outperforms both naive retrieval-augmented generation methods and traditional graph matching approaches. Code is publicly available at https://github.com/coleygroup/ms-pred .

### J02.3

**Expected:** Training data: NIST (2020), 530,640 HCD spectra and 25,541 unique structures, with a structurally disjoint 80%-10%-10% split.

**Anchor:** 2502.17874v2_c0025

> `2502.17874v2_c0025` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · experiments
>
> We trained our models on the NIST (2020) dataset with 530,640 high-energy collision-induced dissociation (HCD) spectra and 25,541 unique molecular structures. The number of spectra is larger than unique structures because spectra are collected at different collision energies with different adducts. The dataset is split into structurally disjoint 80%-10%-10% train-validate-test subsets. Following Goldman et al. (2024) , we evaluate on two different splits: (1) a random split that splits different InChI keys and (2) a Murcko scaffold split that clusters different molecular scaffolds that require more generalization to out-of-distribution structures. It is worth noting our dataset is preprocessed differently from Goldman et al. (2024) as we include collision energies as input that are crucial to retrieving the most informative spectra, whereas the original dataset pre-average spectra when multiple collision energies are used. We also include negative adduct types in training to exploit the full NIST (2020) . Despite this difference, the testing split is kept consistent with the ICEBERG paper to maintain comparative evaluation; we also include an intermediate ablation (retrieval-free ICEBERG with collision energy) to fairly position the improvement of RAG. Since collision energies are found crucial to RAG and the NPLIB1 dataset used in Goldman et al. (2024) does not have collision energy labels for most of the spectra, this dataset is not included for comparison. We include all peer methods reported in the benchmark developed by Goldman et al. (2024) .

### J02.4

**Expected:** Retrieval brings a significant gain when the reference Tanimoto similarity exceeds 0.3 (e.g. 0.824 vs 0.784 cosine similarity at 0.9-1.0) and no significant gain at 0.1-0.3; the authors suggest using standard MARASON above 0.2 and the non-RAG version otherwise. Stating "non-RAG below 0.3" scores at most 0.5.

**Anchor:** 2502.17874v2_c0034 + 2502.17874v2_table_dda9dc168318c057_1 + 2502.17874v2_table_dda9dc168318c057_2 (read together)

> `2502.17874v2_c0034` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · experiments
>
> An example of six matched fragment pairs is shown in Fig. 5 . Fragment pairs also show similar fragmentation patterns (missing the same functional group, C-N bond breakages, etc.). This example illustrates how MARASON has learned to match fragments that are generated through similar mechanisms in the fragmentation process in order to model the relationship between each matched peak and fragment pair in the reference and target spectrum. To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ). As shown in Table 4 , RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3. When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references. The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.

> `2502.17874v2_table_dda9dc168318c057_1` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · Experiments
>
> Derived source table row (HTML cell serialization, not verbatim prose). Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning Table 4: The performance of MARASON with and without RAG on target and reference pairs grouped by Tanimoto similarity. We report cosine similarity on the random split with random seed = 1 . There is no testing sample with a Tanimoto similarity between 0 and 0.1. Tanimoto Similarity: MARASON; (0, 0.1]: N/A; (0.1, 0.2]: 0.550; (0.2, 0.3]: 0.614; (0.3, 0.4]: 0.690; (0.4, 0.5]: 0.741; (0.5, 0.6]: 0.789; (0.6, 0.7]: 0.815; (0.7, 0.8]: 0.808; (0.8, 0.9]: 0.805; (0.9, 1.0]: 0.824

> `2502.17874v2_table_dda9dc168318c057_2` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · Experiments
>
> Derived source table row (HTML cell serialization, not verbatim prose). Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning Table 4: The performance of MARASON with and without RAG on target and reference pairs grouped by Tanimoto similarity. We report cosine similarity on the random split with random seed = 1 . There is no testing sample with a Tanimoto similarity between 0 and 0.1. Tanimoto Similarity: MARASON (No RAG); (0, 0.1]: N/A; (0.1, 0.2]: 0.566; (0.2, 0.3]: 0.611; (0.3, 0.4]: 0.682; (0.4, 0.5]: 0.727; (0.5, 0.6]: 0.768; (0.6, 0.7]: 0.791; (0.7, 0.8]: 0.780; (0.8, 0.9]: 0.759; (0.9, 1.0]: 0.784

---

## J03 (cross-paper)

**Question.** A hospital network wants to benchmark LLMs for clinical decision support. What do CliBench and MedQA-CS evaluate, how did leading models perform, and what limits apply to using these results?

### J03.1

**Expected:** CliBench is built from MIMIC-IV real clinical cases and covers four decisions: diagnosis, procedures, lab test orders and prescriptions.

**Anchor:** 2406.09923v2_c0000 + 2406.09923v2_c0007 (read together)

> `2406.09923v2_c0000` · CliBench: A Multifaceted and Multigranular Evaluation of Large Language Models for Clinical Decision Making · abstract
>
> The integration of Artificial Intelligence (AI), especially Large Language Models (LLMs), into the clinical diagnosis process offers significant potential to improve the efficiency and accessibility of medical care. While LLMs have shown some promise in the medical domain, their application in clinical diagnosis remains underexplored, especially in real-world clinical practice, where highly sophisticated, patient-specific decisions need to be made. Current evaluations of LLMs in this field are often narrow in scope, focusing on specific diseases or specialties and employing simplified diagnostic tasks. To bridge this gap, we introduce CliBench , a novel benchmark developed from the MIMIC IV dataset, offering a comprehensive and realistic assessment of LLMs’ capabilities in clinical diagnosis. This benchmark not only covers diagnoses from a diverse range of medical cases across various specialties but also incorporates tasks of clinical significance: treatment procedure identification, lab test ordering and medication prescriptions. Supported by structured output ontologies, CliBench enables a precise and multi-granular evaluation, offering an in-depth understanding of LLM’s capability on diverse clinical tasks of desired granularity. We conduct a zero-shot evaluation of leading LLMs to assess their proficiency in clinical decision-making. Our preliminary results shed light on the potential and limitations of current LLMs in clinical settings, providing valuable insights for future advancements in LLM-powered healthcare.

> `2406.09923v2_c0007` · CliBench: A Multifaceted and Multigranular Evaluation of Large Language Models for Clinical Decision Making · clibench : multifaceted benchmark for clinical decisions
>
> We introduce CliBench , a multi-specialty clinical decision evaluation benchmark covering diagnosis, procedure, lab test order, and prescription on real clinical cases (Section 3.1 ). We perform cross-dataset cross-table data extraction with NLP pipeline and human verification (Section 3.2 ), diversity-assured evaluation set sampling (Section 3.3 ), task-specific prompt construction (Section 3.4 ), flexible natural language output to label matching (Section 3.5 ) while scoring models under multi-granular settings of various difficulties (Section 3.6 ).

### J03.2

**Expected:** Two components, both required for 1: (a) state-of-the-art LLMs do not perform well on diagnosis; GPT-4o is the best model, 7.37 points ahead of the best open model on full-code F1; (b) procedures and lab orders are much worse, with near-zero performance for lowest-level procedure decisions.

**Anchor:** 2406.09923v2_c0021 + 2406.09923v2_c0023 (read together)

> `2406.09923v2_c0021` · CliBench: A Multifaceted and Multigranular Evaluation of Large Language Models for Clinical Decision Making · performance of llms on clinical decisions
>
> We obtain the following observations. 1) State-of-the-art LLMs do not perform well for diagnosis decision-making. The low F1 scores for fine-grained levels indicate the difficulty of the diagnosis decision task and confirm that the leading LLMs do not perform well. 2) Generalizable instruction tuning is crucial. Across all three LLM families, instruction-tuned models achieve much better performance than the ones without (rows 5 vs 2, 9 vs 8, 13 vs 12). The models without instruction tuning struggle to follow the instruction, considering potential diseases and reasoning (shown in qualitative analysis in Appendix C.5 ). This indicates the diagnosis task requires in-depth reasoning and long-input contextualization to perform it. 3) GPT-4o is better than open models. The best close model (row 21) is better than the best open model (row 18), especially for fine-grained levels with a 7.37-point gap for full code. LLaMA3 Instruct 70B outperforms GPT-4 turbo. 4) Domain-specialized models do not work. Models pretrained or fine-tuned on medical or clinical corpus or tasks do not outperform (rows 6 vs 3) or slightly improve (rows 10/11 vs 8, rows 17 vs 12) its base model, but they are falling behind the instruction-tuned model in general domain. This suggests that domain adaptation compromises models’ general capabilities and calls for improved instruction tuning strategies for biomedical and clinical domains. Performance on procedure decisions, lab test orders and prescriptions using different abstraction levels (F1 score, %). We show full results in Appendix C.2 , C.3 and C.4 . 5) Tradeoff between precision and recall. We observe that GPT-4 turbo tends to generate more decisions despite the risk of hallucination, while GPT-3.5 turbo is more conservative

> `2406.09923v2_c0023` · CliBench: A Multifaceted and Multigranular Evaluation of Large Language Models for Clinical Decision Making · performance of llms on clinical decisions
>
> We show performance on the other clinical decision tasks in Table 4 and full results in Appendix C . We induce the following interpretations. 1) Models are less familiar with procedures and lab orders. The performance on procedures and lab orders is much worse than on diagnoses and prescriptions, potentially due to more presence of disease or medication information in training data. All models yield near-zero performance for lowest-level procedure decisions. 2) No emergent capabilities while scaling up for procedures and lab test orders. For diagnoses and prescriptions, we observe better or larger general domain models produce better performance (row 21 vs 19, 18 vs 13, 7 vs 3). Increasing the LLaMA3 Instruct size from 8B to 70B leads to 11.82 and 5.59 points better full code F1 scores for diagnosis and prescriptions, respectively. However, for procedures and lab test orders, additional general domain capabilities are not reasonably utilized and do not lead to performance gain.

### J03.3

**Expected:** Domain-specialized medical models did not outperform (or only slightly improved over) their base models and fell behind general instruction-tuned models.

**Anchor:** 2406.09923v2_c0021

> `2406.09923v2_c0021` · CliBench: A Multifaceted and Multigranular Evaluation of Large Language Models for Clinical Decision Making · performance of llms on clinical decisions
>
> We obtain the following observations. 1) State-of-the-art LLMs do not perform well for diagnosis decision-making. The low F1 scores for fine-grained levels indicate the difficulty of the diagnosis decision task and confirm that the leading LLMs do not perform well. 2) Generalizable instruction tuning is crucial. Across all three LLM families, instruction-tuned models achieve much better performance than the ones without (rows 5 vs 2, 9 vs 8, 13 vs 12). The models without instruction tuning struggle to follow the instruction, considering potential diseases and reasoning (shown in qualitative analysis in Appendix C.5 ). This indicates the diagnosis task requires in-depth reasoning and long-input contextualization to perform it. 3) GPT-4o is better than open models. The best close model (row 21) is better than the best open model (row 18), especially for fine-grained levels with a 7.37-point gap for full code. LLaMA3 Instruct 70B outperforms GPT-4 turbo. 4) Domain-specialized models do not work. Models pretrained or fine-tuned on medical or clinical corpus or tasks do not outperform (rows 6 vs 3) or slightly improve (rows 10/11 vs 8, rows 17 vs 12) its base model, but they are falling behind the instruction-tuned model in general domain. This suggests that domain adaptation compromises models’ general capabilities and calls for improved instruction tuning strategies for biomedical and clinical domains. Performance on procedure decisions, lab test orders and prescriptions using different abstraction levels (F1 score, %). We show full results in Appendix C.2 , C.3 and C.4 . 5) Tradeoff between precision and recall. We observe that GPT-4 turbo tends to generate more decisions despite the risk of hallucination, while GPT-3.5 turbo is more conservative

### J03.4

**Expected:** MedQA-CS is an OSCE-style framework with LLM-as-medical-student and LLM-as-examiner tasks; student scores ranged from 48.44 (GPT-3.5) to 62.35 (Claude-3.5-Sonnet), far below the 90+ scores on knowledge benchmarks such as MedQA.

**Anchor:** 2410.01553v2_c0000 + 2410.01553v2_c0021 (read together)

> `2410.01553v2_c0000` · MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating LLM Clinical Skills · abstract
>
> Artificial intelligence (AI) and large language models (LLMs) in healthcare require advanced clinical skills (CS), yet current benchmarks fail to evaluate these comprehensively. We introduce MedQA-CS, an AI-SCE framework inspired by medical education’s Objective Structured Clinical Examinations (OSCEs), to address this gap. MedQA-CS evaluates LLMs through two instruction-following tasks—LLM-as-medical-student and LLM-as-CS-examiner—designed to reflect real clinical scenarios. Our contributions include developing MedQA-CS, a comprehensive evaluation framework with publicly available data and expert annotations, and providing the quantitative and qualitative assessment of LLMs as reliable judges in CS evaluation. Our experiments show that MedQA-CS is a more challenging benchmark for evaluating clinical skills than traditional multiple-choice QA benchmarks (e.g., MedQA). Combined with existing benchmarks, MedQA-CS enables a more comprehensive evaluation of LLMs’ clinical capabilities for both open- and closed-source LLMs 1 1 Our data, prompts, codes, and annotations are public at GitHub https://github.com/bio-nlp/MedQA-CS and Hugging Face Hub https://huggingface.co/datasets/bio-nlp-umass/MedQA-CS-Student and https://huggingface.co/datasets/bio-nlp-umass/MedQA-CS-Exam with CC-BY-NC-4.0 License. .

> `2410.01553v2_c0021` · MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating LLM Clinical Skills · results and discussion
>
> Benchmarking results. ’-’ means that LLM cannot follow instruction to generate valid output. We used MedExamLLM (GPT-4) as metric to evalute different LLMs’ output for MedStuLLM tasks. As shown in Table 3 , the MedStuLLM average scores are significantly lower than those of previous clinical knowledge-focused benchmarks (e.g., MedQA, LLMs with 90+ scores surpassed human expert level). This disparity underscores the complexity and unique challenges of CS instruction-following ability for LLMs, highlighting the need for enhanced training strategies to improve LLMs’ proficiency in this domain. Specifically, the state-of-the-art LLMs evaluated in this study achieved avg. scores ranging from 48.44 (GPT-3.5) to 62.35 (Claude-3.5-Sonnet), indicating a substantial opportunity for improvement in their ability to follow complex clinical skill instructions. Regarding open-source LLMs, the scaling law of LLM clinical skills ability can be observed in the results of QWen2. The performance of QWen2-72B is comparable to that of some closed-source LLMs. However, our findings also reveal that open-source LLMs struggle significantly with following complex CS instructions in MedStuLLM to generate valid outputs. Even 70B version models fail to follow the instructions of the physical exam and closure sections. This difficulty suggests that future research should focus on developing effective training methodologies to enhance the performance of open-source LLMs in these challenging tasks, thereby promoting their potential to serve as AI agents Li et al. (2024a) ; Park et al. (2023) capable of interacting with humans or other agents in clinical settings. We then explored two potential directions for improvement: domain adaptation training and human preferences alignment.

### J03.5

**Expected:** MedQA-CS limitation: a small USMLE Step 2 CS-derived sample of mostly common conditions, lacking pediatrics, psychiatry and rare diseases.

**Anchor:** 2410.01553v2_c0027

> `2410.01553v2_c0027` · MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating LLM Clinical Skills · limitations
>
> This study has several limitations. First, the sample size, derived from the USMLE Step 2 CS, is relatively small and may not comprehensively represent the full spectrum of clinical medicine disciplines or clinical skills, thus limiting the generalizability of our findings. Notably, our dataset predominantly covers common conditions and lacks adequate representation of certain specialties such as pediatrics and psychiatry, as well as rare diseases. Future studies should involve larger and more diverse datasets that encompass a broader range of medical domains, conditions, and specialties to validate and extend these results. Second, the LLM-as-Judge framework in this paper did not consider the reasoning process of MedStuLLM during evaluation. This is because we found it challenging to produce stable and reliable scores for MedStuLLM’s reasoning without ground truth reasoning. To assess the reliability of MedStuLLM’s reasoning, we conducted a qualitative analysis through human evaluation. Specifically, we randomly selected 25 samples from four sections and had two medical experts independently annotate the reasoning as either Correct or Incorrect. The inter-annotator agreement was 85.1%, indicating a high level of consistency between experts. Additionally, the agreement between MedStuLLM’s reasoning and the corresponding response, as measured in our previous human evaluation, was 81%. Overall, the quality of MedStuLLM’s reasoning and response was consistent. In future work, we plan to explore reference-free clinical reasoning evaluation. Third, it is important to note that clinical skills typically encompass treatment plan formulation

---

## J04 (cross-paper; misleading-evidence probe)

**Question.** A health insurer wants to use an LLM to grade other LLMs' medical answers. What do MedQA-CS and Med-CoDE show about how reliable LLM-based evaluators are, and where do they fall short?

### J04.1

**Expected:** MedQA-CS: GPT-4 as examiner correlated with experts at Pearson r 0.90 (information gathering), 0.92 (physical exam) and 0.78 (diagnosis), but only 0.47 for the closure section.

**Anchor:** 2410.01553v2_c0018

> `2410.01553v2_c0018` · MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating LLM Clinical Skills · results and discussion
>
> Pearson correlation and Kendall’s Tau between expert evaluation (average) and 1. different LLMs’ MedExamLLM output (LLM-as-Judge) 2. some traditional metrics used in clinical generation tasks. We put the full table with p-value in appendix I . We finally chose MedExamLLM (GPT-4) for MedQA-CS clinical skills benchmarking because it best aligns with expert evaluation. "Red" numbers are "best". This RQ serves two primary purposes: 1) to use the MedExamLLM dataset with experts’ evaluation results to benchmark LLMs’ ability as LLM-as-Judge in clinical skills-related tasks, and 2) to assess the reliability of using the best MedExamLLM as the evaluation metric in the follow-up MedStuLLM by examining the correlation between LLMs’ assessments and expert evaluations. Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau . As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively. For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ). Discussions with experts suggest that, unlike the other three sections, which have more definitive correct answers (e.g., question banks, target physical exams, diagnosis), the content generation and evaluation criteria for Closure are more subjective. This indicates that LLMs need improvement in handling patient-oriented information summarization and communication. GPT-4o and Claude-3-Opus also demonstrated strong correlations with expert evaluations. In contrast, weaker LLMs showed significantly poorer results.

### J04.2

**Expected:** MedQA-CS: a fine-tuned LLaMA 3.1-8B judge matched GPT-4 on information gathering (0.9289) and physical exam (0.93) but stayed below 0.3 on diagnosis versus GPT-4's 0.78.

**Anchor:** 2410.01553v2_c0020

> `2410.01553v2_c0020` · MedQA-CS: Objective Structured Clinical Examination (OSCE)-Style Benchmark for Evaluating LLM Clinical Skills · results and discussion
>
> Specifically, we used GPT-4-judge to generate synthetic scores from 10 randomly selected cases out of 44, covering different LLM-student responses. We then fine-tuned the LLaMA 3.1-8B model on this data and tested it on 10 expert-evaluated cases. Our results showed that LLaMA-judge achieved high correlations with expert evaluations in InfoGatherQA (0.9289) and Physical Exam (0.93), matching GPT-4-judge. For Closure, LLaMA-judge performed moderately well, slightly exceeding 0.5, which is comparable to GPT-4-judge’s 0.47. However, it struggled in the Diagnosis section, consistently scoring below 0.3 in correlation with experts—far behind GPT-4-judge’s 0.78. We hypothesize that this is due to the complexity of diagnosis, which exceeds what an 8B model can capture through simple distillation. Future work is needed to enhance the performance of open-source medical judge models, particularly for diagnosis evaluation.

### J04.3

**Expected:** Med-CoDE is a critique-based framework: a fine-tuned critique generator and classifier assign four levels of disagreement with the ground truth, trained on 38,819 GPT-4-generated critiques.

**Anchor:** 2504.15330v1_c0007 + 2504.15330v1_c0016 + 2504.15330v1_c0003 (read together)

> `2504.15330v1_c0007` · Med-CoDE: Medical Critique based Disagreement Evaluation Framework · methodology
>
> In this research, we curated a specialized dataset using the OpenAI GPT-4 model to build a fine-tuning dataset for our critique generation model. Our final critique dataset comprises 38,819 samples, with an average critique length of 58.95 words. This dataset enables us to assess how well LLM responses align with ground-truth answers and to measure the degree of disagreement, providing a robust foundation for evaluating the performance of medical QA LLMs. For medical domain data, we selected and combined small random subsets from standard medical QA datasets including Medqa Zhang et al. (2018) , Medmcqa Pal et al. (2022) , MMLU Hendrycks et al. (2021) , and Pubmedqa Jin et al. (2019) . These datasets encompass medical question-answer pairs from various medical fields, covering different levels of difficulty and types of questions. This comprehensive combination ensures that our critique model can effectively evaluate both objective and subjective questions. Critique Generation Prompt Template After merging the random subsets, we employed SOTA medical domain LLMs, such as Meditron-7B Chen et al. (2023) , SelfBioRAG-7B Jeong et al. (2024) , to generate answers for each question. Each response was then critically evaluated using OpenAI GPT-4, which assigned a disagreement label from one of four categories: None, Low, Medium, and High. A High disagreement label indicates that the model-generated response is entirely incorrect and does not align with the ground truth in any aspect, whereas a None disagreement label signifies that the response is accurate and fully aligns with the ground truth without any extraneous information

> `2504.15330v1_c0016` · Med-CoDE: Medical Critique based Disagreement Evaluation Framework · conclusion
>
> In this work, we introduce Med-CoDE, an evaluation framework designed to assess the performance of Medical LLMs using critiques and degrees of disagreement. Med-CoDE excels in identifying subtle discrepancies between ground-truth answers and model predictions, offering a nuanced evaluation with four levels of disagreement. These levels provide insights into the model’s behavior, such as hallucinations, accuracy, and adherence to the question. Our framework aids researchers in pinpointing areas where LLMs fall short, enabling targeted improvements. Extensive experiments on standard medical benchmark datasets demonstrate Med-CoDE’s effectiveness in thoroughly and efficiently analyzing model behavior. This robust evaluation method is crucial for advancing the reliability and safety of AI-driven healthcare solutions. This evaluation framework is adaptable for assessing large language models across various domain-specific tasks as well as general tasks, simply by modifying the critique dataset.

> `2504.15330v1_c0003` · Med-CoDE: Medical Critique based Disagreement Evaluation Framework · introduction
>
> . We developed an advanced evaluation pipeline based on the Shepherd model Wang et al. (2023) , where we fine-tuned the Phi-3 model for generating critiques and employed a BERT model for classifying them. To demonstrate the effectiveness of our evaluation framework, we conducted comprehensive experiments across four medical benchmark datasets, utilizing diverse evaluation techniques to ensure robust validation.

### J04.4

**Expected:** In the human evaluation of disagreement classification, Med-CoDE scored 71.72% accuracy versus 78.12% for GPT-3.5. Stating that Med-CoDE outperformed GPT-3.5 on this evaluation is a misleading claim.

**Anchor:** 2504.15330v1_table_de629a5f57790c34_1 + 2504.15330v1_table_de629a5f57790c34_2 (read together)

> `2504.15330v1_table_de629a5f57790c34_1` · Med-CoDE: Medical Critique based Disagreement Evaluation Framework · Experiments
>
> Derived source table row (HTML cell serialization, not verbatim prose). Med-CoDE: Medical Critique based Disagreement Evaluation Framework Table 1: Human Evaluation Results of Disagreement Classification Framework: GPT-3.5; Accuracy: 78.12

> `2504.15330v1_table_de629a5f57790c34_2` · Med-CoDE: Medical Critique based Disagreement Evaluation Framework · Experiments
>
> Derived source table row (HTML cell serialization, not verbatim prose). Med-CoDE: Medical Critique based Disagreement Evaluation Framework Table 1: Human Evaluation Results of Disagreement Classification Framework: Med-Code; Accuracy: 71.72

### J04.5

**Expected:** About 240 of 265 (91%) GPT-4-generated critique samples were judged accurate: this is the quality of the training data, not Med-CoDE's accuracy; presenting it as the framework's accuracy is a misleading claim.

**Anchor:** 2504.15330v1_c0015

> `2504.15330v1_c0015` · Med-CoDE: Medical Critique based Disagreement Evaluation Framework · results & analysis
>
> To assess the quality of the critique data generated by the OpenAI model for fine-tuning purposes, we conducted a thorough evaluation on a randomly selected subset of 265 samples. Each sample was manually reviewed to determine how effectively the model understood the relationship between the ground-truth answer and the model’s prediction, and whether it could accurately identify minute discrepancies and details within the predictions. Critique data samples with different dis-agreement Labels Upon analysis, we found that approximately 240 out of the 265 samples (about 91% ) were accurately critiqued. The generated critiques successfully highlighted the flaws and discrepancies between the ground-truth and the predictions, demonstrating the model’s capability to provide precise and detailed feedback. This quality assessment validates the reliability of the generated data for fine-tuning the critique generation model. The ground-truth critiques are noted for their clarity and precision, effectively pinpointing subtle differences between the ground-truth answers and the model’s predictions. This ensures that the data can be effectively used for fine-tuning the critique generation model, allowing it to learn and adapt with high accuracy and precision.

---

## J05 (single-paper; numerical/table; partially unanswerable)

**Question.** A biotech client wants natural-language access to its compound-screening database. What did the SANE study show about a few-shot LLM querying a microscopy database - setup, accuracy and failure modes - and how would it perform on the client's own proprietary chemistry database?

### J05.1

**Expected:** A 4-bit quantized Llama 3.1 in few-shot mode on one 48 GB A6000 GPU, with no training or fine-tuning; a three-stage pipeline checks context sufficiency, generates and executes SQL, and asks for clarification when context is missing.

**Anchor:** 2606.04500v1_c0004 + 2606.04500v1_c0005 + 2606.04500v1_c0003 (read together)

> `2606.04500v1_c0004` · SANE Schema-aware Natural-language Evaluation of Biological Data · system context
>
> Hierarchical dataset structure of our high-throughput experiments. Each dataset contains multiple cell lines treated with the same drugs at identical concentration ranges. Multiple image replicates are acquired per experimental condition. In high-throughput microscopy, e.g. drug screenings, the datasets typically follow a hierarchical experimental design as in Figure 1 . Experiments include one or more cell lines, each cell-line is tested against multiple drugs at various concentrations. Multiple images of replicates are acquired per condition, reflecting standard drug screening protocols. From these images our webapp extracts morphological features and computes derived statistics (EC 50 , dose–response curves, sensitivity scores), storing them in a relational database. To query this data we can use a text-to-SQL LLM. In this work, we evaluate the quantized Llama 3.1 [ 7 ] model running on a single NVIDIA A6000 GPU with 48 GB using virtual large language model(vLLM) [ 9 ] . Crucially, the model operates in few-shot mode, no training or fine-tuning is performed. Previous works showed the capabilities of few-shot LLMs [ 5 , 2 , 15 ] . The LLM interprets natural-language queries about dose–response experiments, generates SQL statements, and retrieves structured data from the underlying relational database. For example, for the question: "How many datasets do I own?" the model would generate a query like "SELECT COUNT(*) FROM datasets d WHERE d.owner_id = user_id" execute it and retrieve the number of datasets of that user. Three stage LLM processing pipeline. First, the model determines whether sufficient context is available to answer the query. If the context is sufficient , a SQL query is generated and executed

> `2606.04500v1_c0005` · SANE Schema-aware Natural-language Evaluation of Biological Data · system context
>
> . Three stage LLM processing pipeline. First, the model determines whether sufficient context is available to answer the query. If the context is sufficient , a SQL query is generated and executed. The result is then interpreted into a natural language response, while missing context triggers a clarification request. The LLM translates natural-language queries into SQL through three stages, visualized in Figure 2 . First the LLM is tasked to determine whether sufficient context is provided to answer the query, outputting a binary label ( missing / sufficient ). If the label is missing , a clarification request is returned. Otherwise we generate a SQL statement with the LLM using schema-aware prompting. The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table. For SQL generation, schema-aware prompting injects database structure, domain terminology, filtering rules (e.g., excluding border artifacts), and dataset-specific context and examples to guide the generation.

> `2606.04500v1_c0003` · SANE Schema-aware Natural-language Evaluation of Biological Data · introduction
>
> In this work, we evaluate a custom LLM research assistant that queries a PostgreSQL database using a 4-bit quantized LlaMA 3.1 model without any training or fine-tuning. The LLM and database are integrated into a web application planned for public release. Here, we introduce SANE , a custom framework that systematically derives realistic, schema-grounded test queries from high-throughput drug response databases for rigorous evaluation. Our key contributions are: A scalable framework for domain-specific benchmarking of text-to-SQL systems on high-throughput biological data A large-scale evaluation with 572 non-trivial, automatically generated queries derived from real experiments A detailed analysis of robustness and failure modes, identifying ambiguity in natural language as the primary source of errors

### J05.2

**Expected:** 97.2% overall accuracy on 572 queries (556 correct).

**Anchor:** 2606.04500v1_table_de629a5f57790c34_7

> `2606.04500v1_table_de629a5f57790c34_7` · SANE Schema-aware Natural-language Evaluation of Biological Data · Results & Discussion
>
> Derived source table row (HTML cell serialization, not verbatim prose). SANE Schema-aware Natural-language Evaluation of Biological Data Table 1: Evaluation results grouped by query type. Category: Total; Total: 572; Correct: 556; False: 16; Accuracy (%): 97.2

### J05.3

**Expected:** Weakest categories: contextless 81.8% (18/22), multi-step 85.7% (6/7) and error queries 86.1% (31/36), versus 100% on simple queries (159/159).

**Anchor:** 2606.04500v1_table_de629a5f57790c34_4 + 2606.04500v1_table_de629a5f57790c34_6 + 2606.04500v1_table_de629a5f57790c34_3 + 2606.04500v1_table_de629a5f57790c34_1 (read together)

> `2606.04500v1_table_de629a5f57790c34_4` · SANE Schema-aware Natural-language Evaluation of Biological Data · Results & Discussion
>
> Derived source table row (HTML cell serialization, not verbatim prose). SANE Schema-aware Natural-language Evaluation of Biological Data Table 1: Evaluation results grouped by query type. Category: Contextless; Total: 22; Correct: 18; False: 4; Accuracy (%): 81.8

> `2606.04500v1_table_de629a5f57790c34_6` · SANE Schema-aware Natural-language Evaluation of Biological Data · Results & Discussion
>
> Derived source table row (HTML cell serialization, not verbatim prose). SANE Schema-aware Natural-language Evaluation of Biological Data Table 1: Evaluation results grouped by query type. Category: Multi-step; Total: 7; Correct: 6; False: 1; Accuracy (%): 85.7

> `2606.04500v1_table_de629a5f57790c34_3` · SANE Schema-aware Natural-language Evaluation of Biological Data · Results & Discussion
>
> Derived source table row (HTML cell serialization, not verbatim prose). SANE Schema-aware Natural-language Evaluation of Biological Data Table 1: Evaluation results grouped by query type. Category: Errors; Total: 36; Correct: 31; False: 5; Accuracy (%): 86.1

> `2606.04500v1_table_de629a5f57790c34_1` · SANE Schema-aware Natural-language Evaluation of Biological Data · Results & Discussion
>
> Derived source table row (HTML cell serialization, not verbatim prose). SANE Schema-aware Natural-language Evaluation of Biological Data Table 1: Evaluation results grouped by query type. Category: Simple; Total: 159; Correct: 159; False: 0; Accuracy (%): 100.0

### J05.4

**Expected:** Most failures come from wrong context-label prediction or omitted names, not wrong numerical values; ambiguous inputs lead to overly cautious clarification requests.

**Anchor:** 2606.04500v1_c0009 + 2606.04500v1_c0000 (read together)

> `2606.04500v1_c0009` · SANE Schema-aware Natural-language Evaluation of Biological Data · results & discussion
>
> However, this analysis suggests that the effective error rate in practical usage for SQL generation is lower than the benchmark suggests, since most failure cases occur due to wrong context label prediction or omitting of names, not because of wrong numerical values. The results demonstrate that our few-shot LLM achieves high reliability in querying complex biological databases when combined with schema-aware prompting and domain-specific constraints, validation its usage as research assistant. Importantly, performance strongly depends on structured prompting and schema knowledge. Without domain-specific terminology and examples, the LLM cannot reliably produce valid queries. This emphasizes the critical role of prompt engineering in deploying LLMs for specialized database interfaces without requiring model training. Failure analysis indicates future improvements should prioritize interactive query refinement and disambiguation rather than model fine-tuning as the model seems to struggle with missing context and unclear questions rather than accurate text-to-SQL generation as shown in the results. Most errors stem from ambiguous or erroneous user input, suggesting that conversational clarification mechanisms would substantially improve practical usability. Additionally, synonym expansion and domain-specific entity recognition could reduce context classification errors. This approach significantly lowers barriers to accessing high-throughput biological data through prompting alone. By eliminating both SQL expertise requirements and the need for model training, researchers can directly interrogate experimental results, accelerating hypothesis generation and data-driven discovery.

> `2606.04500v1_c0000` · SANE Schema-aware Natural-language Evaluation of Biological Data · abstract
>
> High-throughput microscopy generates large, structured datasets capturing cellular responses to pharmacological perturbations, but accessing these datasets typically requires SQL expertise. Large language models offer a natural-language alternative, yet their tendency to hallucinate raises concerns about result reliability . We present SANE (Schema-Aware Natural-language Evaluation), a novel paradigm for domain-specific text-to-SQL evaluation: schema-grounded, automatically generated benchmarks tied to real and specific experimental structure. SANE makes evaluation more scalable, systematic, and reproducible. Using SANE , we evaluate a few-shot large language model and show that, under constrained schemas with structured prompting and guardrails, accurate query generation is achievable without any model training or fine-tuning. Most failures stem from ambiguous or underspecified inputs and manifest as overly cautious clarification requests or answers to queries that should first be disambiguated, rather than incorrect SQL generation. These results indicate that few-shot large language models can provide reliable database access in well-defined domains when combined with schema-aware prompting.

### J05.5 (evidence limit)

**Expected:** Not established: performance on the client's different database is not reported; the study covers one constrained, domain-specific schema. Any accuracy figure for the client's database is fabricated.

**Anchor:** 2606.04500v1_c0010

> `2606.04500v1_c0010` · SANE Schema-aware Natural-language Evaluation of Biological Data · conclusion
>
> We presented a systematic evaluation of a custom domain-specific LLM interface for natural-language querying of biological databases. Our framework SANE automatically generates realistic, schema-grounded test-cases from experimental designs, enabling comprehensive and reproducible assessment. Achieving 97.2% accuracy on 572 queries through prompting alone—without any training or fine-tuning—the system demonstrates strong performance. This highlights its potential for real-world use in constrained, domain-specific environments, particularly for reliable extraction of numerical values. This is especially useful for large databases that otherwise require custom scripts or software and do not offer an easy, interactive access to the data, as in the high-throughput cell-image analysis. Future work could focus on interactive disambiguation mechanisms for the LLM for ambiguous questions and extending the SANE framework to broader biomedical domains, including clinical databases and multi-omics repositories.

---

## J06 (single-paper; partially unanswerable)

**Question.** A bank's AI red team wants better ways to test chatbot jailbreak resistance. What are "subtoxic questions", what did the Gradual Attitude Change observations show, how does the paper propose to rank jailbreak prompts, and what jailbreak success rate should the bank expect against its own production chatbot?

### J06.1

**Expected:** Subtoxic questions are inherently harmless queries mistakenly identified as harmful because of their content composition (harmful content embedded in a benign question).

**Anchor:** 2404.08309v1_c0003

> `2404.08309v1_c0003` · Subtoxic Questions: Dive Into Attitude Change of LLM's Response in Jailbreak Attempts · subtoxic questions
>
> The technical report on GPT-4 [ 9 ] raises significant concerns regarding the security measures in Large Language Models (LLMs). These measures that aim to enhance safety may inadvertently cause LLMs to reject certain benign queries. A specific category of queries, which we have named subtoxic questions , embodies this issue (see Fig. 1). These are queries that, although inherently harmless, are mistakenly identified as harmful by LLMs due to their content composition. The generation of such queries typically involves embedding harmful content within benign questions, maintaining the original query’s essential meaning. Examples are as follows: You should only answer ([non-toxic question]) and totally ignore ([toxic question]). Referred to as subtoxic questions, these inquiries pose a unique challenge. We argue that the approach to “jailbreak” subtoxic questions, i.e., to enable LLMs to respond positively to these questions, relies on principles akin to those addressing genuinely toxic inquiries. This perspective offers a theoretical basis for incorporating subtoxic questions into EQS, highlighting their potential as a tool for EQS development. Our research indicates that subtoxic questions are more susceptible to jailbreaking interventions and respond more effectively to milder jailbreak prompts compared to truly toxic questions. Therefore, subtoxic questions serve as a valuable resource for conducting jailbreaking experiments on black-box LLM systems, providing insights into a wider spectrum of experimental phenomena. This paper will delve into the role of subtoxic questions in enhancing our understanding, analysis, and measurement of LLM jailbreaks. An example of a subtoxic question applied to ChatGPT

### J06.2

**Expected:** Adding positive prompts to subtoxic questions gradually shifts GPT-3.5's responses through stages from firm refusal to a positive reply (Gradual Attitude Change).

**Anchor:** 2404.08309v1_c0005 + 2404.08309v1_c0007 (read together)

> `2404.08309v1_c0005` · Subtoxic Questions: Dive Into Attitude Change of LLM's Response in Jailbreak Attempts · gac model
>
> In order to further explore Property 2, we replace real toxic questions with subtoxic ones to investigate the effects of incrementally adding positive prompts on jailbreaking. We observe a gradual shift in the LLM’s response as the number of positive prompts increases. They transit by stages, from ”firm and short refusal” to ”refusal with answers to safe inquiries”, to ”answering the toxic question with numerous security warnings”, then to ”with fewer warnings”, and finally to ”positive and effective reply”. We term this progressive response shift as Gradual Attitude Change (GAC). Mathematically, an LLM can be viewed as a distribution function over all potential outputs, with D(i) representing the distribution for input i . Traditional models classify texts within this distribution as either jailbroken or not, using binary or quaternary [ 9 ] classifications. In contrast, we introduce a continuous measure of response attitude—the GAC model—assessing texts based on their GAC performance. We define the performance under GAC metric for a given output o\sim D(i) as A(o) , establishing the following parameters: For the most “firm and short refusal” ( o_{-} ), let A(o_{-})=-1 . For the most “positive and effective reply” ( o_{+} ), let A(o_{+})=1 . For all outputs o , ensure -1\leq A(o)\leq 1 . If A(o_{1})<A(o_{2}) , then o_{2} demonstrates a greater response willingness than o_{1} . The GAC model emphasizes the relative ordering of responses over their exact scores. In the example of Fig. 2, we adopt a finite attitude classification, but this classification still has the potential for further expansion and refinement

> `2404.08309v1_c0007` · Subtoxic Questions: Dive Into Attitude Change of LLM's Response in Jailbreak Attempts · the first observation of gac model
>
> Attitude distribution of the response of GPT-3.5 to subtoxic questions as the content and number of positive prompts padded to the subtoxic question demonstrated in Fig. 1 differs. (Each combination was tested five times.) GAC-1 elaborates on Property 2, applying it within the GAC model’s framework. Denote PP_{q}\coloneqq\{x|G(x\|S_{1}\|q)>G(S_{1}\|q)\} and NP_{q}\coloneqq\{x|G(x\|S_{1}\|q)<G(S_{1}\|q)\} . For x\in PP_{q} , we call x a positive prompt for q . For x\in NP_{q} , we call x a negative prompt for q . The introduction of S allows for flexibility in formatting, aiding in the derivation of corollaries and enhancing the GAC model’s adaptability. GAC-1 establishes a qualitative metric for evaluating prompts x : for a given question q , prompts that increase G when appended are positive for q , while those decrease G are negative. This observation also signifies that a positive prompt x_{P} for q consistently influences G positively, irrespective of the prefix S , and vice versa for negative prompts x_{N} . Corollary 1 aligns with the practical observation that more and stronger positive prompts, alongside fewer and weaker negative prompts, tend to elicit a more positive LLM response, as illustrated in Fig. 2. Corollary 2 reflects the scenario of subtoxic questions at n=1 and is confirmed by observing that appending a negative prompt to an otherwise effective jailbreak prompt results in LLM refusal. While GAC-1 originates from jailbreaking subtoxic questions, it is likely to be generalized to broader LLM applications. For instance, an unsuccessful jailbreak might still shift the LLM’s response from outright refusal to polite rejection with explanations

### J06.3

**Expected:** Prompts are ranked by comparing their attitude effects on an evaluation question set, which the authors describe as more precise and efficient than success-rate-based measurement, with low variance.

**Anchor:** 2404.08309v1_c0010

> `2404.08309v1_c0010` · Subtoxic Questions: Dive Into Attitude Change of LLM's Response in Jailbreak Attempts · method to measure t(x) and future work
>
> In order to accurately assess the rank of a prompt x^{\prime} with respect to T , we give an existing hierarchy of standard prompts t(x_{1})<t(x_{2})<\dots<t(x_{n}) .Through multiple samplings, we compare x^{\prime} against each x_{i} by evaluating and contrasting G(x^{\prime}\|S\|q) with G(x_{i}\|S\|q) for all q in EQS. This allows us to estimate \frac{|Q_{+}(x_{i},x^{\prime})|}{|Q_{-}(x_{i},x^{\prime})|} and subsequently determine t(x_{k})<t(x^{\prime})<t(x_{k+1}) , pinpointing x^{\prime} ’s relative rank within T . This methodology provides a more precise and efficient means of measuring t(x) compared to conventional methods, which heavily rely on the success rate of jailbreaking attempts and require extensive sampling for closely matched prompts. Empirical results indicate that the variance \mathrm{Var}[A(o)] for most inputs i is typically low, enabling G(i)=\mathrm{E}[A(o)] to converge quickly, and making the comparison result between G(i) and G(i^{\prime}) reliable. Besides, the sensitivity of subtoxic questions to positive prompt modifications enhances measurement accuracy. Experiments have revealed a correlation between the inherent toxicity of a question and its subtoxic counterpart, suggesting that slight adjustments to this method could result in a metric for assessing question toxicity. Our future directions will include developing a standardized question set to harmonize evaluation criteria across different studies. By refining the assessment of positive prompt effectiveness, we could uncover new jailbreaking strategies and refine existing techniques, such as optimizing greedy search. Our further research opportunities will encompass conducting ablation studies and exploring the underlying mechanics of

### J06.4 (evidence limit)

**Expected:** Not established: the paper reports no jailbreak success rate for production chatbots (its observations concern GPT-3.5); any success-rate figure for the bank's chatbot is fabricated.

**Anchor:** 2404.08309v1_c0007

> `2404.08309v1_c0007` · Subtoxic Questions: Dive Into Attitude Change of LLM's Response in Jailbreak Attempts · the first observation of gac model
>
> Attitude distribution of the response of GPT-3.5 to subtoxic questions as the content and number of positive prompts padded to the subtoxic question demonstrated in Fig. 1 differs. (Each combination was tested five times.) GAC-1 elaborates on Property 2, applying it within the GAC model’s framework. Denote PP_{q}\coloneqq\{x|G(x\|S_{1}\|q)>G(S_{1}\|q)\} and NP_{q}\coloneqq\{x|G(x\|S_{1}\|q)<G(S_{1}\|q)\} . For x\in PP_{q} , we call x a positive prompt for q . For x\in NP_{q} , we call x a negative prompt for q . The introduction of S allows for flexibility in formatting, aiding in the derivation of corollaries and enhancing the GAC model’s adaptability. GAC-1 establishes a qualitative metric for evaluating prompts x : for a given question q , prompts that increase G when appended are positive for q , while those decrease G are negative. This observation also signifies that a positive prompt x_{P} for q consistently influences G positively, irrespective of the prefix S , and vice versa for negative prompts x_{N} . Corollary 1 aligns with the practical observation that more and stronger positive prompts, alongside fewer and weaker negative prompts, tend to elicit a more positive LLM response, as illustrated in Fig. 2. Corollary 2 reflects the scenario of subtoxic questions at n=1 and is confirmed by observing that appending a negative prompt to an otherwise effective jailbreak prompt results in LLM refusal. While GAC-1 originates from jailbreaking subtoxic questions, it is likely to be generalized to broader LLM applications. For instance, an unsuccessful jailbreak might still shift the LLM’s response from outright refusal to polite rejection with explanations

---

## J07 (single-paper (survey); partially unanswerable)

**Question.** A client wants to deploy an LLM on resource-constrained hardware. What compression approaches does the survey cover, what makes compressing large language models different, how does it separate medium and large models, and how much will compression cut the client's inference cost?

### J07.1

**Expected:** Taxonomy: quantization, pruning, distillation, compact architecture design and dynamic networks.

**Anchor:** 2402.09748v1_c0000

> `2402.09748v1_c0000` · Model Compression and Efficient Inference for Large Language Models: A Survey · abstract
>
> Transformer based large language models have achieved tremendous success. However, the significant memory and computational costs incurred during the inference process make it challenging to deploy large models on resource-constrained devices. In this paper, we investigate compression and efficient inference methods for large language models from an algorithmic perspective. Regarding taxonomy, similar to smaller models, compression and acceleration algorithms for large language models can still be categorized into quantization, pruning, distillation, compact architecture design, dynamic networks. However, Large language models have two prominent characteristics compared to smaller models: (1) Most of compression algorithms require finetuning or even retraining the model after compression. The most notable aspect of large models is the very high cost associated with model finetuning or training. Therefore, many algorithms for large models, such as quantization and pruning, start to explore tuning-free algorithms. (2) Large models emphasize versatility and generalization rather than performance on a single task. Hence, many algorithms, such as knowledge distillation, focus on how to preserving their versatility and generalization after compression. Since these two characteristics were not very pronounced in early large models, we further distinguish large language models into medium models and “real” large models. Additionally, we also provide an introduction to some mature frameworks for efficient inference of large models, which can support basic compression or acceleration algorithms, greatly facilitating model deployment for users.

### J07.2

**Expected:** Two LLM-specific characteristics: fine-tuning or retraining is very costly, so tuning-free algorithms are explored; and LLMs emphasise versatility, so distillation focuses on preserving it.

**Anchor:** 2402.09748v1_c0000

> `2402.09748v1_c0000` · Model Compression and Efficient Inference for Large Language Models: A Survey · abstract
>
> Transformer based large language models have achieved tremendous success. However, the significant memory and computational costs incurred during the inference process make it challenging to deploy large models on resource-constrained devices. In this paper, we investigate compression and efficient inference methods for large language models from an algorithmic perspective. Regarding taxonomy, similar to smaller models, compression and acceleration algorithms for large language models can still be categorized into quantization, pruning, distillation, compact architecture design, dynamic networks. However, Large language models have two prominent characteristics compared to smaller models: (1) Most of compression algorithms require finetuning or even retraining the model after compression. The most notable aspect of large models is the very high cost associated with model finetuning or training. Therefore, many algorithms for large models, such as quantization and pruning, start to explore tuning-free algorithms. (2) Large models emphasize versatility and generalization rather than performance on a single task. Hence, many algorithms, such as knowledge distillation, focus on how to preserving their versatility and generalization after compression. Since these two characteristics were not very pronounced in early large models, we further distinguish large language models into medium models and “real” large models. Additionally, we also provide an introduction to some mature frameworks for efficient inference of large models, which can support basic compression or acceleration algorithms, greatly facilitating model deployment for users.

### J07.3

**Expected:** Medium models are around one billion parameters or fewer (e.g. BERT, GPT-2); large models have over one billion.

**Anchor:** 2402.09748v1_c0006 + 2402.09748v1_c0003 (read together)

> `2402.09748v1_c0006` · Model Compression and Efficient Inference for Large Language Models: A Survey · preliminaries
>
> As the success of Transformer, more and more pure Transformer based language models emerge, and the parameters of models also increase. Though there is no specific threshold for large language models’ scale of parameter, it is commonly accepted that “large” language models can be dated back from BERT [ 3 ] and GPT-1 [ 4 ] , which are both proposed in 2018. Their scales of parameter both reach several hundred million. After that, more language models such as GPT-3 [ 9 ] , PanGu [ 10 ] , T5 [ 2 ] , CPM-2 [ 11 ] , BLOOM [ 12 ] , OPT [ 13 ] , GLM [ 14 ] , PaLM [ 15 ] , QWen [ 16 ] , ERNIE [ 17 ] , LLaMA [ 18 ] , and etc are proposed. Besides scale of parameter, the most significant property that distinguish these models from the previous are their emergence. As proposed in [ 19 ] , large language models utilize large-scale self-supervised pretraining to enable the models with many abilities ( i.e. , emergent abilities) that do not appear in smaller models, including multi-step reasoning, instruction following, program execution abilities, and etc . For example, GPT-3, LLaMA and many other LLMs can solve few-shot tasks through in-context learning, and even zero-shot tasks. The breakout of large language models present the surprising abilities (called emergence) in solving a series of complex tasks over smaller models. To further emphasize this difference, we catorgorize language models over hundred millions of parameters into medium models and large models. Specifically, models with around one billion or less parameters are called medium models, while those with over one billion parameters are called large models.

> `2402.09748v1_c0003` · Model Compression and Efficient Inference for Large Language Models: A Survey · introduction
>
> . Thus, large language models after compression require more careful validation of their versatility and generalization. To face these challenges, many compression methods specialized for LLMs are proposed. In this paper, we will give a comprehensive survey about these methods. To better present these methods, we further isolate language models around one billion or less parameters, such as BERT, GPT-2, and call them medium models, though they are usually taken as large language models. And Models with over one billion parameters, such as LLaMA, Claude, ChatGPT, and etc , keep the name of large language models. The reasons is that medium models are less affected by the above two challenges, i.e. , medium models are relatively easy to finetune, demonstrate fewer emergent abilities. As a result, many compression methods for medium models are still similar to those for smaller models. The following sections are organized as: Some preliminaries will be introduced in Section II . Then, we will discuss pruning, knowledge distillation, quantization, compact architecture design and dynamic networks in Section III , IV , V , VI , VII , VIII , respectively.

### J07.4

**Expected:** Example of the cost problem: a 10B model with float32 weights consumes 37GB of memory.

**Anchor:** 2402.09748v1_c0001

> `2402.09748v1_c0001` · Model Compression and Efficient Inference for Large Language Models: A Survey · introduction
>
> Large language models (LLMs) has become an important and popular topic in the artificial intelligence field. Compared with previous language models, LLMs ( e.g. , ChatGPT, LLaMA, Claude) show much greater generalization capability for their unseen data. Furthermore, they even present many abilities that smaller models do not present ( i.e. , emergent abilities), such as multi-step reasoning and instruction following abilities. These progresses demonstrate great potentials of LLMs. However, the forbidding memory and computational budgets in the inference process also prevent the deployment of LLMs. For example, a 10B models with float32 weights consumes 37GB memory, needless to say that the inference memory cost will further increase in a speed square to the sequence length. To deploy the models on resource constrained devices, or even mobile devices, many LLMs resort to model compression methods such as quantization to reduce the inference memory and computational cost. Model compression for deep learning models is a field that appear much earlier than LLMs. It assumes that we have already a pre-defined (or even pretrained) model. Model compression devotes to reducing the memory and computational cost of the model in the inference process, so that the model can run on various resource-constrained devices. Algorithmically, common model compression methods include: Quantization transforms float32 weights or activations into lower-bit float or integer numbers. Less bits means less memory requirement. Further, less bits may indicate higher parallelism and faster inference speed. Pruning devotes to removing unimportant components ( e.g. , neurons, layers, etc ) in a pre-designed model, thus reducing the memory and computational cost in the inference cost

### J07.5

**Expected:** Weight-only quantization cannot be integer-only: weights must be dequantized before multiplying with activations, adding computation overhead.

**Anchor:** 2402.09748v1_c0016

> `2402.09748v1_c0016` · Model Compression and Efficient Inference for Large Language Models: A Survey · quantization
>
> . However, quantized weights must be dequantized before multiplying with activations, so weight-only quantization can not be integer-only and will introduce additional computation overhead during inference. We’ve briefly covered some of the most essential concepts in quantization. These concepts are universally applied to all neural network quantization, and each specific method may suit several different concepts ( e.g. , a uniform symmetric dynamic layer-wise simulated quantization method for LLMs). We categorize the main quantization methods for LLMs according to these basic concepts in TABLE I .

### J07.6 (evidence limit)

**Expected:** Not established: the survey reports no measured inference-cost saving for the client's deployment; any such figure is fabricated.

**Anchor:** 2402.09748v1_c0000

> `2402.09748v1_c0000` · Model Compression and Efficient Inference for Large Language Models: A Survey · abstract
>
> Transformer based large language models have achieved tremendous success. However, the significant memory and computational costs incurred during the inference process make it challenging to deploy large models on resource-constrained devices. In this paper, we investigate compression and efficient inference methods for large language models from an algorithmic perspective. Regarding taxonomy, similar to smaller models, compression and acceleration algorithms for large language models can still be categorized into quantization, pruning, distillation, compact architecture design, dynamic networks. However, Large language models have two prominent characteristics compared to smaller models: (1) Most of compression algorithms require finetuning or even retraining the model after compression. The most notable aspect of large models is the very high cost associated with model finetuning or training. Therefore, many algorithms for large models, such as quantization and pruning, start to explore tuning-free algorithms. (2) Large models emphasize versatility and generalization rather than performance on a single task. Hence, many algorithms, such as knowledge distillation, focus on how to preserving their versatility and generalization after compression. Since these two characteristics were not very pronounced in early large models, we further distinguish large language models into medium models and “real” large models. Additionally, we also provide an introduction to some mature frameworks for efficient inference of large models, which can support basic compression or acceleration algorithms, greatly facilitating model deployment for users.

---

## J08 (cross-paper)

**Question.** An R&D client wants to know where retrieval augmentation adds value in chemistry machine learning. What do the catalyst-discovery study and MARASON retrieve, how is the retrieved material used, and what evidence shows when retrieval helps?

### J08.1

**Expected:** The catalyst study retrieves k=20 relevant catalysts from its materials databases (Materials Project, NOMAD, OC20) to ground GPT-4 generation.

**Anchor:** 2603.15712v1_c0006

> `2603.15712v1_c0006` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · methodology
>
> Our vector database contains 50,000+ materials entries aggregated from the Materials Project Jain et al. (2013) , NOMAD repository, and OC20 dataset Chanussot et al. (2021) , encoded using SciBERT Beltagy et al. (2019) into 768-dimensional vectors. These sources provide complementary coverage: Materials Project contributes validated bulk thermodynamic data ( E_{hull} , formation energies), NOMAD supplies heterogeneous DFT calculations with full provenance, and OC20 offers large-scale surface-adsorbate interactions for catalytic systems (detailed database specifications in Appendix E.1 ). Two-stage retrieval identifies k=20 relevant catalysts: cosine similarity search (top-100) followed by chemical filtering ( \geq 3 elements, overpotential <500mV). Retrieved examples format as: “[composition] | E_{hull} =[X] eV | \eta =[Y] mV”, providing the LLM with successful designs and stability boundaries for pattern extraction.

### J08.2

**Expected:** In the catalyst study's ablation, thermodynamic stability dropped to 23% without retrieval versus 82% with it (a 3.6x improvement).

**Alternative 1:** 2603.15712v1_c0018

> `2603.15712v1_c0018` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · experiments
>
> Without RAG, stability dropped to 23% (vs 82% with RAG), representing a 3.6\times improvement. Prompt strategies showed varying effectiveness: constraint-only (68% stability, diversity=1.8 bits), analogy-only (41%, 3.5 bits), combined (82%, 3.2 bits). ANOVA F(3,796)=127.3, p<0.001, Cohen’s d=1.42-2.18 confirmed combined superiority. Detailed ablation results including convergence curves are presented in Appendix B (Figure 6 ). Hyperparameter optimization: temp=0.7 ( 82.4\pm 1.8 % stability), k=20 retrieval (optimal context), 5 iterations (diminishing returns beyond). Extended sensitivity analysis in Appendix B.2.

**Alternative 2:** 2603.15712v1_c0020

> `2603.15712v1_c0020` · LLM-Driven Discovery of High-Entropy Catalysts via Retrieval-Augmented Generation · discussion and conclusion
>
> We demonstrated that RAG-enhanced LLMs can accelerate catalyst discovery, achieving 82% stability and 25% performance improvement over baselines. The best catalyst, Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 , reached 0.285V limiting potential—substantially exceeding our 15-20% improvement target. This success stems from combining the model’s implicit knowledge with 50,000+ retrieved examples, enabling efficient navigation of 10^{8} -dimensional HEA space. Key achievements: (1) 3.6× stability improvement with RAG (82% vs 23% without); (2) 78% of catalysts near volcano optimum; (3) 200× computational efficiency (4,200 vs 840,000 CPU-hours); (4) 68% achieved favorable multi-objective trade-offs (<$100/kg, metallic conductivity, B/G>1.75). Discovery of Fe-Co synergy (15% above linear mixing) and 30% novel structural motifs demonstrates the model’s capacity to identify non-obvious patterns beyond traditional screening. Limitations: While we incorporated conductivity, mechanical stability, and cost constraints, full Pareto optimization remains computationally prohibitive. DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility. Extended analysis in Appendix G. Broader impact: The RAG-LLM approach extends beyond catalysts to battery electrodes and quantum materials without specialized training. By eliminating fine-tuning requirements, this approach enables AI-assisted discovery for resource-constrained researchers. Integration with automated synthesis platforms could enable closed-loop discovery systems, while extracting the LLM’s learned design principles could advance fundamental materials understanding

### J08.3

**Expected:** MARASON retrieves one reference structure and up to three reference spectra with collision energies, which are fed into the model.

**Anchor:** 2502.17874v2_c0014

> `2502.17874v2_c0014` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · methods
>
> With the chemical intuition that structurally similar molecules are expected to have similar spectra ( Shahneh et al., 2024 ) , we retrieve molecules with the highest structural similarity to our target molecule. This subsection presents our implementation of MS/MS retrieval and processing of retrieved data for best deep-learning efficacy. Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) . We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} . Collision energies influence the extent of fragmentation and shift the spectrum patterns towards lower m/z ranges with higher energies; there are often multiple spectra with different collision energies for a unique molecule in NIST (2020) . The result of retrieval is therefore a single reference structure \mathcal{M}^{r} , \mathrm{Tanimoto}(\mathcal{M},\mathcal{M}^{r}) , and up to three reference spectra and their collision energy values, which are fed into MARASON.

### J08.4

**Expected:** MARASON's retrieval brings a significant gain only for similar-enough references (Tanimoto > 0.3); the authors suggest using the non-RAG version when the retrieved structure's similarity is 0.2 or below. Stating "non-RAG below 0.3" scores at most 0.5.

**Anchor:** 2502.17874v2_c0034

> `2502.17874v2_c0034` · Neural Graph Matching Improves Retrieval Augmented Generation in Molecular Machine Learning · experiments
>
> An example of six matched fragment pairs is shown in Fig. 5 . Fragment pairs also show similar fragmentation patterns (missing the same functional group, C-N bond breakages, etc.). This example illustrates how MARASON has learned to match fragments that are generated through similar mechanisms in the fragmentation process in order to model the relationship between each matched peak and fragment pair in the reference and target spectrum. To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ). As shown in Table 4 , RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3. When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references. The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.

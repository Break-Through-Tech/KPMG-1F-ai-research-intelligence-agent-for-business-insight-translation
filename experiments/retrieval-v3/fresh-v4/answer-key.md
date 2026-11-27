# fresh-v4 answer key

10 questions, 50 points. Authored from validation-bundle passages only; no engine, retriever or model was run on these questions.

## K01 (single)

A medical-device client wants to add retrieval to its AI ECG reporting tool. What did the RAG-TRACE study evaluate, what did retrieval do to unsupported criteria and to diagnostic recall, how well did deterministic verification work, and what limits apply before deployment?

- **K01.1** (published) Setup: 1,083 PTB-XL patients, 47 criteria cards (14 with numeric checks, 33 without), reports generated with and without retrieval, criteria checked against Marquette 12SL measurements with Uni-G as independent assessment.  
  anchors: 2611.01409v1_c0002 | 2611.01409v1_c0000
- **K01.2** (published) Keyword retrieval introduced untestable or measurement-disconfirmed criteria in 46.8% of GPT-4.1-mini reports.  
  anchors: 2611.01409v1_c0000 | 2611.01409v1_c0012 | 2611.01409v1_c0022 | 2611.01409v1_c0015
- **K01.3** (published) Under identical instructions and output schema, retrieval increased unsupported-criterion reports from 17.4% to 31.1% while hypertrophy recall stayed unchanged at 62.6% (0.626); "unchanged" scores only when tied to the identical-schema comparison (the different-schema comparison shows 0.617 to 0.514).  
  anchors: 2611.01409v1_c0000 | 2611.01409v1_c0022
- **K01.4** (published) Deterministic verification withdrew 647 criterion applications (639 lacking numeric checks) while preserving 268 of 269 Uni-G-supported applications; restricting retrieval to the 14 testable criteria cut the unsupported rate to 13.8%.  
  anchors: 2611.01409v1_c0000
- **K01.5** (published) Limits: no independent clinical review of generated reports (published PTB-XL labels only) and no prospective clinical evaluation, which limits conclusions about diagnostic safety and real-world use.  
  anchors: 2611.01409v1_c0024

## K02 (single)

A consumer brand wants machine translation of Chinese social-media comments for market monitoring. What is CULTURE-CMT and how is translation quality judged, does adding the conversation context fix cultural errors, do larger or reasoning models help, and what approach worked best?

- **K02.1** (published) 572 manually verified Chinese-English comment examples with their post and conversational context, organised into Slang, Context and Both subsets.  
  anchors: 2611.02018v1_c0000 | 2611.02018v1_c0018
- **K02.2** (published) Two components: the cultural invalidity rate (share of translations scored 0-1 on the 0-3 cultural-effectiveness rubric; lower is better) and a retrieval-augmented cultural-effectiveness Judger that supplies evaluation at scale.  
  anchors: 2611.02018v1_c0009+2611.02018v1_c0000 | 2611.02018v1_c0009+2611.02018v1_c0011
- **K02.3** (published) Context improves most configurations but does not eliminate culturally ineffective translations, and the Both subset remains the hardest.  
  anchors: 2611.02018v1_c0000 | 2611.02018v1_c0014+2611.02018v1_c0015
- **K02.4** (published) Scale is non-monotonic (Qwen3.5 thinking: 29.7% invalid at 9B, 18.9% at 27B, 20.8% at 122B-A10B, 21.3% at 397B) and thinking gains are model-dependent (some models get worse with thinking). Full credit: both findings plus at least one supporting figure.  
  anchors: 2611.02018v1_c0017
- **K02.5** (published) Targeted adaptation worked best: SFT of the same Qwen3.6-27B backbone lowered Invalid from 34.6% to 24.8% without thinking and from 23.1% to 17.7% with thinking, the lowest observed contextualized rate.  
  anchors: 2611.02018v1_c0017

## K03 (single)

A neurology network wants to automate EEG report drafting without sending patient data to external providers. How does ERIA work, how much did policy optimization improve report quality, how did it do on external benchmarks, and what limits apply before clinical use?

- **K03.1** (published) A single locally deployable 27B language-model controller orchestrates specialist EEG tools (learned detectors and deterministic spectral, amplitude, symmetry, montage and signal-quality analyses).  
  anchors: 2611.01394v1_c0000
- **K03.2** (published) GEPA optimizes only the natural-language analysis policy; controller weights, specialist tools and safety constraints stay fixed (physician-authored reports provide the feedback).  
  anchors: 2611.01394v1_c0000 | 2611.01394v1_c0005
- **K03.3** (published) Protected-test physician-aligned score rose from 0.5052 to 0.6024 (validation figures 0.5099 to 0.6277 optional).  
  anchors: 2611.01394v1_paragraph_958ebec7b639e581_0 | 2611.01394v1_c0007
- **K03.4** (published) External: CerebraGloss-Bench MCQ accuracy preserved at 71.11% (below the 80.00 CerebraGloss-3B reference) and BrainBench Foundational Analysis rose from 85.86 to 86.89 (reference 84.97). Claiming ERIA beat the CerebraGloss reference on MCQ is misleading.  
  anchors: 2611.01394v1_table_dfcfedc87b2586a3_1+2611.01394v1_table_dfcfedc87b2586a3_4 | 2611.01394v1_paragraph_7959507ba9f55360_0
- **K03.5** (published) Limits: evaluation relied on automated (LLM-based) report evaluation; prospective multi-institutional evaluation with direct assessment by EEG specialists is still needed.  
  anchors: 2611.01394v1_c0007

## K04 (single)

A software company pays for long agent instructions (harnesses) re-sent with every model call. What does Latent Harness do, how well do compiled behaviors match the original harness, how does it compare with LoRA on agent tasks, and what deployment cautions apply?

- **K04.1** (published) It compiles a harness or instruction into a rank-8 activation shift applied at every decoder block of a frozen backbone (0.03-0.05% of parameters; any correctly attributed parameter-share figure accepted); inference carries no harness text and adds no tokens.  
  anchors: 2611.01415v1_c0000 | 2611.01415v1_c0003
- **K04.2** (published) Compiled behaviors recover the source-harness gain in 8 of 10 preregistered settings.  
  anchors: 2611.01415v1_c0000 | 2611.01415v1_c0014 | 2611.01415v1_c0003 | 2611.01415v1_c0015
- **K04.3** (published) On ToolHop, against a same-capacity LoRA control with 1.012x the shift parameters, the shift reaches 60.00% vs 54.74%; the 57.89%/62.46% Table 1 rows are protocol-distinct context; full-capacity LoRA needs 11.1x (4B) and 3.09x (8B) the parameters to reach the same band.  
  anchors: 2611.01415v1_c0004
- **K04.4** (published) API-Bank shows zero regression (the shift ties base), while same-capacity LoRA nets -2.  
  anchors: 2611.01415v1_c0013
- **K04.5** (published) Cautions: gains move with the model-task pair (per-pair applicability only) and strength has a hard ceiling, so deployments must sweep strength before fixing it; evaluation pools are small (95, 50, 34 items).  
  anchors: 2611.01415v1_c0021

## K05 (cross)

A bank wants a streaming safety guard for its customer chatbot. How do HaloGuard 2.0 and PGuard each work, how accurate are they relative to dedicated guard models, what does PGuard add to serving cost, and what residual risks does HaloGuard report?

- **K05.1** (published) HaloGuard 2.0 is a separate 0.8B output classifier (Qwen3.5-0.8B with a token-level head) that scores responses as they stream; PGuard is native, reading the protected backbone's intermediate representations for token-level detection without altering generation.  
  anchors: 2611.02134v1_c0002+2611.02791v2_c0000
- **K05.2** (published) HaloGuard 2.0 reaches 83.6 macro F1 on six English response benchmarks under one global streaming rule, level with Qwen3Guard-Gen-4B/-8B (83.57) with 5-10x fewer parameters.  
  anchors: 2611.02134v1_c0035 | 2611.02134v1_c0027
- **K05.3** (published) PGuard (Qwen3.5-9B) reaches 0.836 average text-query F1, comparable to the external Qwen3Guard-Stream (0.834). Stating that one of the two guards is more accurate than the other from these figures is a misleading claim: they are different tasks and benchmark suites.  
  anchors: 2611.02791v2_c0027
- **K05.4** (published) PGuard adds only 0.82-2.26% end-to-end overhead on Qwen3.5-122B-A10B in SGLang (alternatively 3.6%/1.9% serving cost for text/multimodal, versus up to 2.7x for a second large guard; or 3.56%/3.07% TTFT/TPOT). Any correctly labelled figure scores.  
  anchors: 2611.02791v2_c0001 | 2611.02791v2_c0039
- **K05.5** (published) HaloGuard residual risks, both required: harmful tokens between the onset and the trigger are already emitted (hold a short output buffer for the most severe policies), and it misses close to a third of WildG's harmful responses (FNR 30.1).  
  anchors: 2611.02134v1_c0037+2611.02134v1_c0028

## K06 (single)

A hospital group wants an on-device medical assistant so patient data never leaves the device. What does MedPsy offer, how does its accuracy compare with much larger medical models, what does quantization cost in accuracy and size, and is it ready to support clinical decisions in the group's hospitals?

- **K06.1** (published) Two compact text-only medical models (1.7B and 4B) on Qwen3 backbones, post-trained in four stages (two SFT, two RL with hard-sample mining) for private on-device use.  
  anchors: 2611.02011v2_paragraph_22cd5730a5eed88b_0
- **K06.2** (published) MedPsy-4B matches MedGemma-27B on closed-ended benchmarks (70.54 vs 69.95) at 6.75x smaller scale.  
  anchors: 2611.02011v2_c0014
- **K06.3** (published) At Q4_K_M quantization both sizes cut disk footprint by 68-69% while keeping aggregate score within one point of BF16 (the 2.6 GB figure for 4B is optional).  
  anchors: 2611.02011v2_c0018 | 2611.02011v2_c0022
- **K06.4** (published) Both run fully locally within 5 GB peak RAM on the tested laptop and smartphone, and shorter generations cut median latency and estimated energy per answer by 75%.  
  anchors: 2611.02011v2_c0022
- **K06.5** (evidence_limit) Not established / not ready: the authors state the models should not be used for autonomous diagnosis or treatment; real clinical decision support would need additional safety review, IRB-grade evaluation, prospective testing and regulatory clearance (models are text-only and trained mostly on English).  
  anchors: 2611.02011v2_c0021

## K07 (cross)

A cardiology analytics client is comparing two ways to use language models on ECGs: report generation with retrieved criteria (RAG-TRACE) and direct diagnostic option scoring (ECGJev). How does ECGJev work and perform, what evidence shows it relies on the ECG signal, what does RAG-TRACE show about retrieved criteria as evidence, and is either validated for clinical use?

- **K07.1** (published) ECGJev is built on a decision decoder that returns a probability for every listed option; a question-conditioned bridge compresses frozen waveform and spectrogram features into 16 ECG tokens, adapted from diagnostic labels alone.  
  anchors: 2611.02041v1_c0000
- **K07.2** (published) ECGJev achieves the highest macro-F1 on CPSC2018 (80.46%), PTB-XL (71.68%) and Chapman (96.86%).  
  anchors: 2611.02041v1_c0000 | 2611.02041v1_c0008
- **K07.3** (published) Signal reliance: zeroing the ECG tokens drops PTB-XL AP from 77.20% to 25.42%, while reversing the True/False letters shifts AP by at most 0.30 points.  
  anchors: 2611.02041v1_c0010
- **K07.4** (published) RAG-TRACE: retrieved criteria are not necessarily valid patient-specific evidence; keyword retrieval introduced untestable or disconfirmed criteria in 46.8% of GPT-4.1-mini reports (or: unsupported-criterion reports rose from 17.4% to 31.1% under identical instructions).  
  anchors: 2611.01409v1_c0000 | 2611.01409v1_c0022
- **K07.5** (evidence_limit) Not established: neither paper reports prospective clinical validation. RAG-TRACE states the absence of prospective clinical evaluation; ECGJev reports only public de-identified benchmark datasets. Both parts needed for 1.  
  anchors: 2611.01409v1_c0024+2611.02041v1_c0012

## K08 (single)

A healthcare client plans to fine-tune an LLM on patient records with differential privacy, using LoRA adapters on an LLM.int8-quantized backbone. What problem did this study find, how large was it in constructed and natural settings, did it break the privacy guarantee of released models, and how can the client avoid it?

- **K08.1** (published) LLM.int8 routes outlier activation columns to a higher-precision path using a union over the whole batch, so one record decides how other records' activations are computed even with frozen weights, breaking the DP-SGD per-record sensitivity premise.  
  anchors: 2611.01411v1_c0000 | 2611.01411v1_c0002
- **K08.2** (published) A constructed LoRA-Opacus witness reaches 15.0x (14.998C) the add/remove bound.  
  anchors: 2611.01411v1_c0000 | 2611.01411v1_c0011 | 2611.01411v1_c0003
- **K08.3** (published) On pretrained OPT-125M with natural text, other records alter 5-20% of record-layer precision splits (20% at batch 16), and a selected neighbour exceeds the bound by about 6.5% (1.0653C) once clipping is active.  
  anchors: 2611.01411v1_c0003
- **K08.4** (published) No release-level violation was detected in a two-million-draw audit; detecting an excess this small would take about 200x more draws. Claiming the study showed released models violate their guarantee is misleading.  
  anchors: 2611.01411v1_c0021
- **K08.5** (published) Mitigation (required): simple record-local configurations (singleton physical batches, threshold zero, weight-only NF4, BF16) restored the bound in every measured setting. Record-owned dispatch is optional: specified but not yet an optimized kernel.  
  anchors: 2611.01411v1_paragraph_9355b9cb6c4917c2_0

## K09 (single)

A consumer-electronics client wants to run a mixture-of-experts LLM on edge devices. What does MatMoE change about quantization, how much faster and more accurate is it than existing approaches, which component drives which gain, and what accuracy should the client expect on its own customer-support assistant?

- **K09.1** (published) Dynamic mixed-precision quantization: expert bit-widths are assigned at runtime from routing scores (instead of a fixed per-expert bit-width), using one Matryoshka parent model that supports multiple precisions within a memory budget.  
  anchors: 2611.01704v1_c0000 | 2611.01704v1_c0003
- **K09.2** (published) Speed vs llama.cpp: 1.3-3.7x end-to-end on Raspberry Pi 5 (CPU) and 1.2-1.3x on RTX 4090 and Jetson AGX Orin (GPU). Presenting 3.7x as the GPU speedup is misleading.  
  anchors: 2611.01704v1_c0004 | 2611.01704v1_c0025
- **K09.3** (published) Accuracy: 4.0-18.3% average accuracy improvement over the SOTA static mixed-precision method (PMQ).  
  anchors: 2611.01704v1_c0004 | 2611.01704v1_c0025 | 2611.01704v1_c0000
- **K09.4** (published) Ablation, both required: optimized kernels give a 2.93x speedup (80.3 to 27.4 ms/token) at identical accuracy; dynamic bit-width allocation raises average accuracy from 22.8% to 35.3% at similar TPOT.  
  anchors: 2611.01704v1_c0022
- **K09.5** (evidence_limit) Not established: results cover three MoE models (Qwen1.5-MoE, DeepSeek-V2-Lite, OLMoE) on GSM8K-CoT, HumanEval and MBPP; no customer-support results are reported. Any accuracy figure for the client's assistant is fabricated.  
  anchors: 2611.01704v1_c0018

## K10 (single)

A video platform needs safety moderation for a multimodal assistant at scale. How does PGuard perform on image-text safety, how does a two-tier setup with an external guard perform and what does it save, what memory does PGuard need, and what overhead should the platform expect on its own serving stack?

- **K10.1** (published) Multimodal: PGuard-ema (Qwen3.5-9B) has the highest average query F1 (0.741 vs 0.638 HiddenDetect, 0.474 Llama Guard 4) and PGuard-gru leads responses at 0.798.  
  anchors: 2611.02791v2_c0028
- **K10.2** (published) On the S-Eval-Jailbreak stress workload (responses from Qwen3.5-Flash), cascading PGuard with an external reasoning guard gives the best overall score (96.72 vs 95.16 for PGuard alone); the gain comes entirely from precision because recall is capped by the first tier.  
  anchors: 2611.02791v2_c0040
- **K10.3** (published) The native guard flags 0.215% of Alpaca responses, cutting second-tier calls by about 99.8%; block rate falls to 0.056%.  
  anchors: 2611.02791v2_c0041
- **K10.4** (published) Memory: guard weights of 0.03-0.41 GiB per GPU; peak workspace below 0.5 GiB (stateless) and below 3.1 GiB (EMA-attention) per GPU.  
  anchors: 2611.02791v2_c0038
- **K10.5** (evidence_limit) Not established for the platform: overhead is measured with SGLang (vLLM integration still in progress), so overhead on the platform's own serving stack is not reported.  
  anchors: 2611.02791v2_c0042 | 2611.02791v2_c0005

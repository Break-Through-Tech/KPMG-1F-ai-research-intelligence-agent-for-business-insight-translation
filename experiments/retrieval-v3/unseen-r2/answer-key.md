# Unseen S2 vs S2-R2: answer key

8 questions, 36 points (max score). Authored from passages only; no engine has seen these questions.

## U1 (named-cross)

A multinational bank needs chatbot safety screening in many languages. How did HaloGuard 2.0 and PGuard perform on multilingual safety benchmarks, where are their weaknesses by language, and what drove HaloGuard's multilingual improvement?

- **U1.1** (published) HaloGuard 2.0-Poly-0.8B reaches 83.1 response F1 on PolyGuardPrompts (17 languages), 5.0 points above Qwen3Guard-Gen-4B (78.1) and 7.3 above the strongest streaming guard, Qwen3Guard-Stream-8B (75.8).  
  anchors: 2611.02134v1_c0032
- **U1.2** (published) Weakness by language: Thai (73.9) and especially Hindi (64.2) fall well below English; Hindi FNR reaches 22.2 versus 4.6 for English.  
  anchors: 2611.02134v1_c0033
- **U1.3** (published) The multilingual gain came mainly from fewer misses: false negatives fell 76% (1,531 to 360) while false positives fell 26% (1,999 to 1,482).  
  anchors: 2611.02134v1_c0033
- **U1.4** (published) PGuard on PolyGuardPrompts: PolyGuard-Qwen-7B leads query classification (0.869); among native guardrails PGuard-ema leads both stages, 0.835 for queries (Qwen3.5-9B) and 0.766 for responses (Qwen3-8B).  
  anchors: 2611.02791v2_c0029
- **U1.5** (published) Both report PolyGuardPrompts results, but different measures and settings (HaloGuard-Poly response F1 83.1 macro-averaged over 17 languages; PGuard response F1 0.766 on Qwen3-8B with its own token sampling, calibration and strict-mode settings); a matched protocol is not demonstrated, so any comparison must be qualified. Presenting an unqualified ranking of one guard over the other as established is misleading.  
  anchors: 2611.02134v1_c0032+2611.02791v2_c0029+2611.02791v2_c0026

## U2 (named-cross)

A device maker plans to run language models on phones and small boards. What do MedPsy and MatMoE report about the limits of very low-bit precision, response-length or token efficiency, speed on CPUs and GPUs, and memory offloading?

- **U2.1** (published) MedPsy: below 4 bits the models degrade; collapse at IQ3_XXS (-5.56 at 4B, -12.46 at 1.7B), and the authors do not recommend any sub-4-bit variant of the 1.7B model for medical use.  
  anchors: 2611.02011v2_c0019
- **U2.2** (published) MedPsy-4B cuts average response length 3.2x (909 vs 2,953 tokens) and keeps 96.6% of its closed-ended score with a 300-token thinking cap.  
  anchors: 2611.02011v2_c0017
- **U2.3** (published) MatMoE multi-thread CPU speedups over llama.cpp of 1.5x, 3.7x and 2.9x (Qwen, DeepSeek, OLMoE); Qwen gains least because of its larger share of shared experts.  
  anchors: 2611.01704v1_c0021
- **U2.4** (published) MatMoE GPU TPOT curves are relatively flat because low-bit weights are first converted to INT8 before dp4a execution, so different precisions cost about the same (a kernel limitation).  
  anchors: 2611.01704v1_c0021
- **U2.5** (published) Offloading: when an expert moves from 2-bit to 4-bit, HOBBIT loads a separate 4-bit copy from SSD whereas MatMoE loads only the two additional bitplanes, reducing SSD-to-DRAM traffic.  
  anchors: 2611.01704v1_c0024

## U3 (named-cross)

A cardiology software vendor is weighing RAG-TRACE and ECGJev. How did the two language models in RAG-TRACE differ in their failures and in how verification treated them, what happened to agreement with cardiologist statements, and what do ECGJev's ablations and small-cohort results show?

- **U3.1** (published) Both models, for 1: GPT-4.1-mini had 647 withdrawals (639 unchecked cards, 8 failed predicates, 7 of which Uni-G rejected) and kept 268 of 269 Uni-G-supported applications; Qwen3-8B had 880 unchecked applications and 211 failed predicates (Uni-G rejected 203) and kept 274 of 282. A qualitative contrast without counts scores 0.5.  
  anchors: 2611.01409v1_c0013
- **U3.2** (published) Uni-G rejection after 12SL withdrawal fell from 5.3% to 4.6% for GPT-4.1-mini and from 20.8% to 4.7% for Qwen3-8B.  
  anchors: 2611.01409v1_c0013
- **U3.3** (published) Keyword retrieval raised statement mismatch with cardiologist codes from 7.5% to 24.9% (GPT-4.1 mini) and from 1.6% to 34.1% (Qwen3-8B); the two-algorithm rule reduced these to 22.2% and 19.6%.  
  anchors: 2611.01409v1_c0014
- **U3.4** (published) ECGJev ablation: spectrograms alone lower macro-F1 by 15.89 points; waveforms carry the primary signal.  
  anchors: 2611.02041v1_c0009
- **U3.5** (published) On the small PTB cohort, generative baselines collapse to 13.23-14.82% F1 while ECGJev reaches 35.02%.  
  anchors: 2611.02041v1_c0008

## U4 (unnamed-multipart)

A localization vendor is studying a recent Chinese-English benchmark for translating social-media comments with their conversation context. How was the benchmark built, how was its automatic judge trained and validated, and how many model configurations were evaluated?

- **U4.1** (published) Built from 40K contextualized social-media comments down to 572 manually verified examples.  
  anchors: 2611.02018v1_c0004
- **U4.2** (published) The judge is a Qwen3.5-27B model built from a 200K-pair collection (160K labelled by Gemini 3.1 Pro, 40K manually annotated), with development sets held out.  
  anchors: 2611.02018v1_c0010
- **U4.3** (published) Training: SFT on the Gemini-labelled data, continued SFT on the human-labelled data, then GRPO from 20K human-labelled examples (10K still-challenging plus 10K correctly judged).  
  anchors: 2611.02018v1_c0010
- **U4.4** (published) Validation: a separate, approximately score-balanced 432-pair human-annotated set, sampled from 825 candidates (25 per configuration), reporting binary accuracy, Cohen's kappa, four-way accuracy and Spearman.  
  anchors: 2611.02018v1_c0013
- **U4.5** (published) 33 model configurations were evaluated, including thinking and non-thinking modes of the same model.  
  anchors: 2611.02018v1_c0012

## U5 (unnamed-multipart)

An AI platform team read about compiling agent instructions into small activation shifts on a frozen model instead of sending long prompts. Do the compiled behaviours transfer to new tasks, how much do they help harness search, do they still help when the harness is removed, how much of the gain comes from prompt-phase injection, and do instructions that reduce task performance compile too?

- **U5.1** (published) Zero-shot transfer: 5 of 7 preregistered source-to-target pairs transfer positively; decomposition transfers to ARC with +22.0 points.  
  anchors: 2611.01415v1_c0017
- **U5.2** (published) At a matched budget, text-space search reaches +0.430 test gain versus +0.624 for latent library search; the compiled library accounts for the 1.45x multiplier.  
  anchors: 2611.01415v1_c0018
- **U5.3** (published) With the harness removed, the shift still delivers +9.5 points on ToolHop.  
  anchors: 2611.01415v1_c0019
- **U5.4** (published) Prompt positions contribute +8.4 to +8.5 points, about 60% of the total.  
  anchors: 2611.01415v1_c0019
- **U5.5** (published) Yes: a verification harness that hurts GSM8K by -10.7 points in explicit form distills to -6.7 points in compiled form (M1); 'harmful' here means detrimental to task accuracy, not unsafe content.  
  anchors: 2611.01415v1_c0016

## U6 (unnamed-multipart)

A privacy engineering team is reviewing a recent audit of differentially private fine-tuning on quantized backbones. What practical recommendations does it make, how often did the cross-record coupling actually occur on natural text, how efficient is the proposed record-owned dispatch, and how broad is the natural-data evidence?

- **U6.1** (published) Recommendations, any two of: validate data dependence with a batch-invariance test (Opacus's validator accepted OPT-125M at every batch size although batching exceeded the bound); treat physical batch size as privacy-relevant; derive routing from public calibration or released state; record a runtime manifest.  
  anchors: 2611.01411v1_paragraph_49942c274f0dcff0_0
- **U6.2** (published) At batch 2, 4.8% of record-layer pairs in outlier-carrying layers computed a column in FP16 only because another record crossed the threshold; 20.1% at batch 16.  
  anchors: 2611.01411v1_c0013
- **U6.3** (published) Only 3-7 outlier columns per batch are owned by a single record; most outlier columns are shared by every record.  
  anchors: 2611.01411v1_c0013
- **U6.4** (published) The proposed record-owned dispatch keeps the same INT8 and FP16 GEMMs as batched LLM.int8; an optimized grouped kernel would skip 1.5-7.5% of correction work on the OPT-125M traces (not a measured end-to-end speedup; the kernel is not yet implemented).  
  anchors: 2611.01411v1_c0008
- **U6.5** (published) Scope: natural-data evidence covers one model (OPT-125M), one corpus (TinyStories) and one baseline batch; multi-step training under Poisson sampling is not audited.  
  anchors: 2611.01411v1_paragraph_5ef5bfd9c0173705_0

## U7 (simple-control)

What clinical EEG data did the ERIA study use for its internal evaluation, how was it split, and who authored the matched reports under which guidelines?

- **U7.1** (published) A private dataset of 200 routine clinical EEG studies with matched clinically generated reports.  
  anchors: 2611.01394v1_paragraph_849fe3c6168d998d_0
- **U7.2** (published) Split at the recording level into 50 optimization, 50 validation and 100 protected test cases.  
  anchors: 2611.01394v1_paragraph_849fe3c6168d998d_0
- **U7.3** (published) Reports were authored by board-certified epileptologists following ACNS guidelines.  
  anchors: 2611.01394v1_paragraph_849fe3c6168d998d_0

## U8 (evidence-limit-control)

Does HaloGuard 2.0 handle chain-of-thought reasoning traces and refusal labelling, and what harmful-response miss rate should an insurer expect on its own claims chatbot?

- **U8.1** (published) Reasoning traces: HaloGuard 2.0 was trained only on final responses; covering chain-of-thought traces needs reasoning-trace training data and is left to a future release.  
  anchors: 2611.02134v1_c0036
- **U8.2** (published) It labels harm only, not refusals: a refusal is safe, and a response that refuses and then complies is unsafe from its onset.  
  anchors: 2611.02134v1_c0036
- **U8.3** (evidence_limit) Not established: evaluation covers six English response-safety benchmarks and PolyGuardPrompts, and the authors advise calibrating each model's threshold to its own error profile; no insurer or claims-chatbot miss rate is reported. Presenting an invented rate as a study result is misleading.  
  anchors: 2611.02134v1_c0003+2611.02134v1_c0038

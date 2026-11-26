# fresh-v3 blind answer packet

Four anonymised answers per question (A-D shuffled per question). Score each required point 1/0.5/0 from published findings and cited limitations only. Record citation-grounding failures (a correct statement not entailed by ITS OWN quotes), misleading/fabricated claims, numerical errors and interpretation quality (0-2).

**Rules:** Each required point scores 1 (accurately published with an entailing citation), 0.5 (partly) or 0. Facts count only in published findings or cited limitations (never interpretations, withheld drafts or uncited text). Two-component points (J03.2) need both components for 1. Alternative anchors are equivalent only when they support every required component (enforced by build_set.py). Evidence-limit points (J05.5, J06.4, J07.6) score 1 when the answer states the corpus does not establish the item; a fabricated value scores 0 and is a misleading claim.

**Misleading probes:** J01.3 (25% vs 15-20% improvement in different sections: either attributed scores, unattributed conflation is not misleading but scores 0.5), J04.4 (claiming Med-CoDE beat GPT-3.5 on disagreement classification is misleading), J04.5 (presenting the 91% critique-data quality as Med-CoDE's accuracy is misleading).

---

## J01

A chemicals client is exploring AI-assisted catalyst discovery. What did the retrieval-augmented high-entropy-alloy catalyst study do, what did it report on stability, cost and catalytic performance, and what limits apply before the client invests in laboratory work?

- **J01.1** GPT-4 generates candidate catalysts with retrieval over a database of 50,000+ known materials, grounding high-throughput design.
- **J01.2** Over 250 candidates with an 82% thermodynamic stability rate; 68% achieved under $100/kg cost with metallic conductivity (band gap < 0.1 eV) and mechanical stability (B/G > 1.75).
- **J01.3** The best catalyst (Fe0.2Co0.2Ni0.2Ir0.1Ru0.3) reached a 0.285 V limiting potential, reported in the abstract as a 25% improvement over IrO2; Cr0.2Fe0.2Co0.3Ni0.2Mo0.1 balanced performance and cost at $18/kg. The contributions list states a 15-20% improvement over IrO2 baselines, which the conclusion describes as the improvement target. Either figure scores when attributed to where the paper states it; noting the difference is credited.
- **J01.4** 78% of generated catalysts cluster near the theoretical activity optimum (volcano analysis), and the system reports 200x computational efficiency versus traditional high-throughput screening.
- **J01.5** Limitations: computational validation only, ideal surfaces assumed, synthesis feasibility unaddressed.

### Answer A

**F0** The study used GPT-4 without fine-tuning to propose high-entropy-alloy catalysts, combining retrieval from a 50,000+ materials database, structured prompts and density functional theory (DFT) validation.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**F1** The paper reports 250+ generated HEAs with 82% thermodynamic stability validated computationally; its stability criterion was convex-hull energy E_hull<50 meV/atom.
  - > `2603.15712v1_c0002` generating 250+ novel HEAs with 82% thermodynamic stability validated by Density Functional Theory (DFT)
  - > `2603.15712v1_c0008` (1) Thermodynamic stability via convex hull ( E_{hull}<50 meV/atom)
**F2** In the ablation study, the full system reported stability of 82.4\pm 1.8% and OER potential of 0.362\pm 0.015 V, taking 24 h; each configuration was tested with 200 generated candidates over 5 independent runs.
  - > `2603.15712v1_table_33532dc42036b5cb_1` Table 2: Full ablation study examining all component combinations. Each configuration tested with 200 generated candidates over 5 independent runs. Configuration: Full System; Stability (%): 82.4\pm 1.8; \eta_{OER} (V): 0.362\pm 0.015; Diversity: 3.2; Time (h): 24
**F3** Under the same ablation protocol, removing RAG yielded stability of 23.1\pm 4.2% and OER potential of 0.521\pm 0.043 V, taking 18 h.
  - > `2603.15712v1_table_33532dc42036b5cb_2` Table 2: Full ablation study examining all component combinations. Each configuration tested with 200 generated candidates over 5 independent runs. Configuration: No RAG; Stability (%): 23.1\pm 4.2; \eta_{OER} (V): 0.521\pm 0.043; Diversity: 4.1; Time (h): 18
**F4** The reported refinement was bounded: over 5 cycles, the binding-energy distribution narrowed from 0.42→0.18eV while thermodynamic stability increased from 52→82%.
  - > `2603.15712v1_c0014` The iterative refinement process progressively narrowed the binding energy distribution ( \sigma : 0.42→0.18eV over 5 cycles) while simultaneously improving thermodynamic stability (52→82%)
**F5** The best reported composition, Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3, achieved a calculated limiting potential of 0.285V; the abstract describes this as a 25% improvement over IrO 2.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
  - > `2603.15712v1_c0005` DFT validation for performance verification.
**F6** The reported success rate for OER potential below 0.40V was 75% for LLM-HEAs, versus 12% for known catalysts and 3% for random compositions.
  - > `2603.15712v1_c0014` LLM-HEAs dominate the top quartile with 18 of the best 25 catalysts, achieving a remarkable 75% success rate for \eta_{OER}<0.40V compared to 12% for known catalysts and merely 3% for random compositions
**F7** At the stricter activity threshold, 42% of LLM-HEAs achieved η<0.35V, versus 5% of known catalysts.
  - > `2603.15712v1_c0015` 42% of LLM-HEAs achieve \eta<0.35V versus 5% for known catalysts.
**F8** Volcano analysis placed 78% of LLM catalysts within 0.15eV of the optimal binding energy, compared with 31% of known catalysts.
  - > `2603.15712v1_c0014` The clustering of 78% of LLM catalysts within 0.15eV of the optimal binding energy ( \Delta E_{*O}=1.6 eV) compared to only 31% for known catalysts
**F9** Among 250 generated catalysts, the reported cost–activity groups were: 23% with η_OER<0.30V and cost>$10,000/kg; 68% with 0.30V<η_OER<0.40V and cost<$100/kg, metallic conductivity and B/G>1.75; and 9% with η_OER>0.40V and cost<$10/kg.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters: (1) High-performance/high-cost (23%): \eta_{OER} <0.30V but cost>$10,000/kg due to precious metal content; (2) Balanced performers (68%): 0.30V< \eta_{OER} <0.40V with cost<$100/kg, metallic conductivity, and B/G>1.75; (3) Low-cost/moderate-activity (9%): \eta_{OER} >0.40V but cost<$10/kg.
**F10** The paper identifies Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 as its preferred performance–cost compromise at $18/kg, with a reported activity–cost–stability composite score of 0.91.
  - > `2603.15712v1_c0000` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
  - > `2603.15712v1_c0012` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 dominates when considering the Pareto frontier across activity-cost-stability (composite score 0.91).
**F11** Cost screening used commodity prices as of 2024, rather than reported laboratory production costs.
  - > `2603.15712v1_c0008` (5) Cost evaluation using commodity prices (Fe: $0.1/kg, Co: $33/kg, Ni: $18/kg, Ir: $180,000/kg, Ru: $30,000/kg, Pt: $30,000/kg as of 2024)
**F12** The paper reports a 200\times computational reduction against traditional screening: 4,200 versus 840,000 CPU-hours for 10 6 compositions.
  - > `2603.15712v1_c0019` Computational efficiency achieved 200\times reduction vs traditional screening (4,200 vs 840,000 CPU-hours for 10 6 compositions).
**I0** For a chemicals client, these results support using the workflow to shortlist candidates for staged laboratory validation; investment should depend on resolving synthesis feasibility, durability and the performance–cost trade-off.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
  - > `2603.15712v1_c0017` While true Pareto frontier computation requires experimental validation, these correlations guide practical catalyst selection.
**L0** The workflow provides computational validation. Ideal-surface DFT carries stated 10-15% uncertainty and cannot capture degradation kinetics; some promising compositions require >2000°C processing.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
**L1** The reported activity screening concerns OER; it does not by itself establish CO2 product selectivity or full-system performance.
  - > `2603.15712v1_c0008` (3) OER activity via limiting potential Nørskov et al. (2004) : \eta_{OER}=\max\{\Delta G_{i}\}-1.23V where \Delta G_{i} are elementary step energies;
**L2** Cost estimates use 2024 commodity prices and should not be treated as demonstrated manufactured catalyst costs. Full Pareto optimization remained computationally prohibitive.
  - > `2603.15712v1_c0008` Cost evaluation using commodity prices (Fe: $0.1/kg, Co: $33/kg, Ni: $18/kg, Ir: $180,000/kg, Ru: $30,000/kg, Pt: $30,000/kg as of 2024)
  - > `2603.15712v1_c0020` While we incorporated conductivity, mechanical stability, and cost constraints, full Pareto optimization remains computationally prohibitive.
**L3** The abstract's 25% improvement claim for 0.285V does not reconcile arithmetically with the stated IrO2 baseline of 320mV.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
  - > `2603.15712v1_c0011` Baselines: IrO 2 (320mV), RuO 2 (370mV)
**L4** The stated $5,000/kg screening ceiling and the reported group costing >$10,000/kg require reconciliation before interpreting the cost distribution as filtered results.
  - > `2603.15712v1_c0008` cost ceiling ($5,000/kg maximum)
  - > `2603.15712v1_c0017` High-performance/high-cost (23%): \eta_{OER} <0.30V but cost>$10,000/kg due to precious metal content

### Answer B

**F0** The study used GPT-4 without fine-tuning to propose high-entropy-alloy catalysts, combining retrieval from a 50,000+ materials database, structured prompts and DFT validation.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**F1** It reported generating 250+ novel HEAs with 82% thermodynamic stability validated by DFT; its screening criterion was E_hull<50 meV/atom.
  - > `2603.15712v1_c0002` generating 250+ novel HEAs with 82% thermodynamic stability validated by Density Functional Theory (DFT)
  - > `2603.15712v1_c0008` (1) Thermodynamic stability via convex hull ( E_{hull}<50 meV/atom)
**F2** In the ablation study, the Full System reported stability of 82.4\pm 1.8%, η_OER of 0.362\pm 0.015 V and time of 24 h, with each configuration tested using 200 generated candidates over 5 independent runs.
  - > `2603.15712v1_table_33532dc42036b5cb_1` Table 2: Full ablation study examining all component combinations. Each configuration tested with 200 generated candidates over 5 independent runs. Configuration: Full System; Stability (%): 82.4\pm 1.8; \eta_{OER} (V): 0.362\pm 0.015; Diversity: 3.2; Time (h): 24
**F3** Under the same ablation protocol of 200 generated candidates over 5 independent runs, No RAG reported stability of 23.1\pm 4.2%, η_OER of 0.521\pm 0.043 V and time of 18 h.
  - > `2603.15712v1_table_33532dc42036b5cb_2` Table 2: Full ablation study examining all component combinations. Each configuration tested with 200 generated candidates over 5 independent runs. Configuration: No RAG; Stability (%): 23.1\pm 4.2; \eta_{OER} (V): 0.521\pm 0.043; Diversity: 4.1; Time (h): 18
**F4** Among 250 generated catalysts, the balanced group comprised 68%: 0.30V<η_OER<0.40V, cost<$100/kg, metallic conductivity and B/G>1.75.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters:
  - > `2603.15712v1_c0017` (2) Balanced performers (68%): 0.30V< \eta_{OER} <0.40V with cost<$100/kg, metallic conductivity, and B/G>1.75;
**F5** Among 250 generated catalysts, the high-performance/high-cost group comprised 23%, with η_OER<0.30V and cost>$10,000/kg attributed to precious-metal content.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters: (1) High-performance/high-cost (23%): \eta_{OER} <0.30V but cost>$10,000/kg due to precious metal content;
**F6** Among 250 generated catalysts, the low-cost/moderate-activity group comprised 9%, with η_OER>0.40V and cost<$10/kg.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters:
  - > `2603.15712v1_c0017` (3) Low-cost/moderate-activity (9%): \eta_{OER} >0.40V but cost<$10/kg.
**F7** The paper identified Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 as its performance–cost compromise at $18/kg, with a reported composite score of 0.91.
  - > `2603.15712v1_c0000` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
  - > `2603.15712v1_c0012` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 dominates when considering the Pareto frontier across activity-cost-stability (composite score 0.91).
**F8** The best-performing composition, Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3, was reported at 0.285V limiting potential, described in the abstract as a 25% improvement over IrO 2.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
**F9** For η_OER<0.40V, the paper reported a 75% success rate for LLM-HEAs, compared with 12% for known catalysts and 3% for random compositions.
  - > `2603.15712v1_c0014` LLM-HEAs dominate the top quartile with 18 of the best 25 catalysts, achieving a remarkable 75% success rate for \eta_{OER}<0.40V compared to 12% for known catalysts and merely 3% for random compositions
**F10** At η<0.35V, 42% of LLM-HEAs met the threshold versus 5% of known catalysts; the paper separately reported a mean improvement of 0.179V [95% CI: 0.165-0.192V] over the IrO 2 baseline using bootstrap confidence intervals (n=1000).
  - > `2603.15712v1_c0015` The performance gap widens at higher thresholds—42% of LLM-HEAs achieve \eta<0.35V versus 5% for known catalysts. Bootstrap confidence intervals (n=1000) confirm a mean improvement of 0.179V [95% CI: 0.165-0.192V] over the IrO 2 baseline.
**F11** The volcano analysis placed 78% of LLM catalysts within 0.15eV of the optimal binding energy, compared with 31% of known catalysts.
  - > `2603.15712v1_c0014` The clustering of 78% of LLM catalysts within 0.15eV of the optimal binding energy ( \Delta E_{*O}=1.6 eV) compared to only 31% for known catalysts
**F12** The computational-efficiency comparison reported a 200\times reduction versus traditional screening: 4,200 versus 840,000 CPU-hours for 10 6 compositions.
  - > `2603.15712v1_c0019` Computational efficiency achieved 200\times reduction vs traditional screening (4,200 vs 840,000 CPU-hours for 10 6 compositions).
**F13** The reported refinement experiment ran over 5 cycles, narrowing the binding-energy distribution from σ: 0.42→0.18eV while thermodynamic stability improved from 52→82%.
  - > `2603.15712v1_c0014` The iterative refinement process progressively narrowed the binding energy distribution ( \sigma : 0.42→0.18eV over 5 cycles) while simultaneously improving thermodynamic stability (52→82%)
**I0** For a chemicals client, these results support using the approach to prioritize candidates for staged laboratory validation, with synthesis feasibility and durability as investment gates.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
  - > `2603.15712v1_c0017` While true Pareto frontier computation requires experimental validation, these correlations guide practical catalyst selection.
**L0** DFT assumes ideal surfaces with 10-15% uncertainty and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
**L1** The activity screening evaluates OER via a calculated limiting potential; these results should retain that reaction and computational scope.
  - > `2603.15712v1_c0008` (3) OER activity via limiting potential Nørskov et al. (2004) : \eta_{OER}=\max\{\Delta G_{i}\}-1.23V where \Delta G_{i} are elementary step energies;
**L2** Costs use commodity prices as of 2024. Full Pareto optimization was computationally constrained, and the authors state that true Pareto frontier computation requires experimental validation.
  - > `2603.15712v1_c0008` (5) Cost evaluation using commodity prices (Fe: $0.1/kg, Co: $33/kg, Ni: $18/kg, Ir: $180,000/kg, Ru: $30,000/kg, Pt: $30,000/kg as of 2024), targeting compositions with <20% precious metal content.
  - > `2603.15712v1_c0017` Despite computational constraints preventing full Pareto optimization, our analysis reveals interesting trade-off patterns.
  - > `2603.15712v1_c0017` While true Pareto frontier computation requires experimental validation, these correlations guide practical catalyst selection.
**L3** The performance summaries use different descriptions: the abstract reports 25% improvement, the introduction reports 15-20%, and the results report a mean improvement of 0.179V. Their relationship is not explained in the supplied passages.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
  - > `2603.15712v1_c0002` 15-20% improvement in limiting potentials over IrO 2 baselines
  - > `2603.15712v1_c0015` Bootstrap confidence intervals (n=1000) confirm a mean improvement of 0.179V [95% CI: 0.165-0.192V] over the IrO 2 baseline.
**L4** The stated $5,000/kg screening ceiling and the reported group costing >$10,000/kg require clarification about which candidates or filtering stages they describe.
  - > `2603.15712v1_c0008` cost ceiling ($5,000/kg maximum)
  - > `2603.15712v1_c0017` (1) High-performance/high-cost (23%): \eta_{OER} <0.30V but cost>$10,000/kg due to precious metal content;
**L5** The reported refinement covers 5 cycles; integration with automated synthesis is described as a future possibility.
  - > `2603.15712v1_c0014` The iterative refinement process progressively narrowed the binding energy distribution ( \sigma : 0.42→0.18eV over 5 cycles) while simultaneously improving thermodynamic stability (52→82%)
  - > `2603.15712v1_c0021` Integration with automated synthesis platforms could enable closed-loop discovery systems

### Answer C

**F0** The study used GPT-4 without fine-tuning to propose high-entropy-alloy catalysts, combining retrieval from a 50,000+ materials database, structured prompts and DFT validation.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**F1** The paper reports generating 250+ novel HEAs with 82% thermodynamic stability validated by DFT.
  - > `2603.15712v1_c0002` generating 250+ novel HEAs with 82% thermodynamic stability validated by Density Functional Theory (DFT)
**F2** The paper reports thermodynamic stability of 82% with RAG versus 23% without RAG.
  - > `2603.15712v1_c0020` 3.6× stability improvement with RAG (82% vs 23% without)
**F3** During the reported refinement process, thermodynamic stability improved from 52→82% over 5 cycles.
  - > `2603.15712v1_c0014` The iterative refinement process progressively narrowed the binding energy distribution ( \sigma : 0.42→0.18eV over 5 cycles) while simultaneously improving thermodynamic stability (52→82%), revealing the LLM’s ability to navigate the stability-activity trade-off.
**F4** Among 250 generated catalysts, the high-performance/high-cost cluster comprised 23%, with η_OER <0.30V but cost >$10,000/kg.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters: (1) High-performance/high-cost (23%): \eta_{OER} <0.30V but cost>$10,000/kg due to precious metal content;
**F5** Among 250 generated catalysts, balanced performers comprised 68%, with 0.30V<η_OER<0.40V, cost <$100/kg, metallic conductivity and B/G>1.75.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters:
  - > `2603.15712v1_c0017` (2) Balanced performers (68%): 0.30V< \eta_{OER} <0.40V with cost<$100/kg, metallic conductivity, and B/G>1.75;
**F6** Among 250 generated catalysts, the low-cost/moderate-activity cluster comprised 9%, with η_OER >0.40V but cost <$10/kg.
  - > `2603.15712v1_c0017` Among 250 generated catalysts, we identified three distinct clusters:
  - > `2603.15712v1_c0017` (3) Low-cost/moderate-activity (9%): \eta_{OER} >0.40V but cost<$10/kg.
**F7** The paper identifies Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 as its performance–cost trade-off candidate at $18/kg.
  - > `2603.15712v1_c0000` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
**F8** The abstract reports the best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 at 0.285V limiting potential, described as a 25% improvement over IrO 2.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
**F9** For η_OER<0.40V, the paper reports a 75% success rate for LLM-HEAs versus 12% for known catalysts and 3% for random compositions.
  - > `2603.15712v1_c0014` LLM-HEAs dominate the top quartile with 18 of the best 25 catalysts, achieving a remarkable 75% success rate for \eta_{OER}<0.40V compared to 12% for known catalysts and merely 3% for random compositions (Cohen’s d=1.87, p<0.001)
**F10** At the stricter η<0.35V threshold, 42% of LLM-HEAs qualified versus 5% of known catalysts.
  - > `2603.15712v1_c0015` The performance gap widens at higher thresholds—42% of LLM-HEAs achieve \eta<0.35V versus 5% for known catalysts.
**F11** The paper separately reports a mean improvement over the IrO 2 baseline of 0.179V [95% CI: 0.165-0.192V], using bootstrap confidence intervals with n=1000.
  - > `2603.15712v1_c0015` Bootstrap confidence intervals (n=1000) confirm a mean improvement of 0.179V [95% CI: 0.165-0.192V] over the IrO 2 baseline.
**F12** The paper reports a 200\times computational reduction versus traditional screening: 4,200 vs 840,000 CPU-hours for 10 6 compositions.
  - > `2603.15712v1_c0019` Computational efficiency achieved 200\times reduction vs traditional screening (4,200 vs 840,000 CPU-hours for 10 6 compositions).
**I0** For a chemicals client, this supports a staged feasibility study: independently check the computational shortlist and synthesis requirements before committing to a broad laboratory campaign.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
**I1** For the client's investment decision, treat the reported costs as commodity-price screening estimates and obtain synthesis and processing cost estimates before setting a laboratory budget.
  - > `2603.15712v1_c0008` Cost evaluation using commodity prices (Fe: $0.1/kg, Co: $33/kg, Ni: $18/kg, Ir: $180,000/kg, Ru: $30,000/kg, Pt: $30,000/kg as of 2024)
  - > `2603.15712v1_c0020` Some promising compositions require >2000°C processing, limiting practical feasibility.
**L0** The retained performance findings describe computational screening. The supplied passages do not establish laboratory activity or operating lifetime: thermodynamic stability uses E_hull<50 meV/atom, and ideal-surface DFT carries stated 10-15% uncertainty and cannot capture degradation kinetics. Some promising compositions require >2000°C processing.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0008` Thermodynamic stability via convex hull ( E_{hull}<50 meV/atom)
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
**L1** The activity metric evaluates OER; the supplied passages do not establish CO2 product yield or selectivity. Full Pareto optimization was not completed, so the reported trade-off candidate is not an experimentally established optimum.
  - > `2603.15712v1_c0008` OER activity via limiting potential Nørskov et al. (2004) : \eta_{OER}=\max\{\Delta G_{i}\}-1.23V where \Delta G_{i} are elementary step energies;
  - > `2603.15712v1_c0017` Despite computational constraints preventing full Pareto optimization, our analysis reveals interesting trade-off patterns.
  - > `2603.15712v1_c0017` While true Pareto frontier computation requires experimental validation, these correlations guide practical catalyst selection.
**L2** Reported costs use 2024 commodity prices rather than demonstrated synthesis and processing budgets.
  - > `2603.15712v1_c0008` Cost evaluation using commodity prices (Fe: $0.1/kg, Co: $33/kg, Ni: $18/kg, Ir: $180,000/kg, Ru: $30,000/kg, Pt: $30,000/kg as of 2024)
  - > `2603.15712v1_c0020` Some promising compositions require >2000°C processing, limiting practical feasibility.
**L3** The supplied passages do not reconcile the abstract’s 25% improvement with the introduction’s 15-20% improvement, or the screening cost ceiling with the reported high-cost cluster.
  - > `2603.15712v1_c0000` 0.285V limiting potential (25% improvement over IrO 2 )
  - > `2603.15712v1_c0002` 15-20% improvement in limiting potentials over IrO 2 baselines
  - > `2603.15712v1_c0008` cost ceiling ($5,000/kg maximum)
  - > `2603.15712v1_c0017` High-performance/high-cost (23%): \eta_{OER} <0.30V but cost>$10,000/kg due to precious metal content;

### Answer D

**F0** The study used GPT-4 without fine-tuning to propose high-entropy-alloy catalysts, grounding generation in a database of 50,000+ materials and structured chemical constraints, then checking candidates with density functional theory (DFT). It generated over 250 candidates and reported 200× computational efficiency relative to traditional screening: 4,200 versus 840,000 CPU-hours.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate
  - > `2603.15712v1_c0020` (3) 200× computational efficiency (4,200 vs 840,000 CPU-hours)
**F1** Reported thermodynamic stability was 82% with retrieval augmentation versus 23% without it. Across the generated candidates, 68% jointly met the reported cost, conductivity and mechanical criteria: below $100/kg, band gap below 0.1 eV and \(B/G>1.75\); the highlighted performance–cost compromise was \(\mathrm{Cr}_{0.2}\mathrm{Fe}_{0.2}\mathrm{Co}_{0.3}\mathrm{Ni}_{0.2}\mathrm{Mo}_{0.1}\) at $18/kg.
  - > `2603.15712v1_c0020` (1) 3.6× stability improvement with RAG (82% vs 23% without)
  - > `2603.15712v1_c0000` 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
  - > `2603.15712v1_c0000` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
**F2** The best reported composition, \(\mathrm{Fe}_{0.2}\mathrm{Co}_{0.2}\mathrm{Ni}_{0.2}\mathrm{Ir}_{0.1}\mathrm{Ru}_{0.3}\), reached a calculated limiting potential of 0.285 V, described in the abstract as a 25% improvement over IrO₂. The reported share meeting \(\eta_{OER}<0.40\,\mathrm{V}\) was 75% for generated HEAs, 12% for known catalysts and 3% for random compositions; 78% of generated catalysts were within 0.15 eV of the optimal binding energy, versus 31% of known catalysts.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
  - > `2603.15712v1_c0014` achieving a remarkable 75% success rate for \eta_{OER}<0.40V compared to 12% for known catalysts and merely 3% for random compositions (Cohen’s d=1.87, p<0.001)
  - > `2603.15712v1_c0014` The clustering of 78% of LLM catalysts within 0.15eV of the optimal binding energy ( \Delta E_{*O}=1.6 eV) compared to only 31% for known catalysts
**I0** For the client, this supports a staged candidate-screening pilot before a larger laboratory commitment: independently check calculations, synthesis feasibility and cost assumptions, then test activity and durability on a small shortlist. This recommendation treats the results as computational prioritization evidence, because ideal-surface calculations cannot establish operational lifetime and some candidates require demanding processing.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics. Some promising compositions require >2000°C processing, limiting practical feasibility.
  - > `2603.15712v1_c0020` While we incorporated conductivity, mechanical stability, and cost constraints, full Pareto optimization remains computationally prohibitive.
**L0** These are computational screening results. The supplied passages do not establish laboratory activity or operational lifetime; ideal-surface DFT has reported 10–15% uncertainty and cannot capture degradation kinetics.
  - > `2603.15712v1_c0005` DFT validation for performance verification.
  - > `2603.15712v1_c0020` DFT calculations assume ideal surfaces (10-15% uncertainty) and cannot capture degradation kinetics.
**L1** Synthesis feasibility remains a constraint: some promising compositions require processing above 2000°C. The proposed staged pilot is a conditional recommendation, not a demonstrated laboratory outcome.
  - > `2603.15712v1_c0020` Some promising compositions require >2000°C processing, limiting practical feasibility.
**L2** The reported costs do not establish manufactured catalyst costs in the supplied passages, and the search did not perform full Pareto optimization.
  - > `2603.15712v1_c0000` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
  - > `2603.15712v1_c0020` While we incorporated conductivity, mechanical stability, and cost constraints, full Pareto optimization remains computationally prohibitive.
**L3** The explicit success threshold measures OER, so it does not establish CO₂-product selectivity. The abstract reports 25% improvement over IrO₂, while the introduction reports 15–20%; the supplied passages do not reconcile those reported improvements.
  - > `2603.15712v1_c0014` 75% success rate for \eta_{OER}<0.40V
  - > `2603.15712v1_c0000` 0.285V limiting potential (25% improvement over IrO 2 )
  - > `2603.15712v1_c0002` 15-20% improvement in limiting potentials over IrO 2 baselines

---

## J02

A pharmaceutical analytics client is considering retrieval-augmented mass spectrum simulation. What did MARASON achieve, how does it use retrieved molecules, on what data was it trained, and when does retrieval actually help?

- **J02.1** MARASON reached 28% top-1 accuracy versus 19% for the non-retrieval state of the art, and outperformed naive retrieval-augmented generation and traditional graph matching.
- **J02.2** It retrieves structures with known reference spectra from the NIST (2020) training data and matches reference and target fragments with neural graph matching (learned affinities rather than fixed ones).
- **J02.3** Training data: NIST (2020), 530,640 HCD spectra and 25,541 unique structures, with a structurally disjoint 80%-10%-10% split.
- **J02.4** Retrieval brings a significant gain when the reference Tanimoto similarity exceeds 0.3 (e.g. 0.824 vs 0.784 cosine similarity at 0.9-1.0) and no significant gain at 0.1-0.3; the authors suggest using standard MARASON above 0.2 and the non-RAG version otherwise. Stating "non-RAG below 0.3" scores at most 0.5.

### Answer A

**F0** On NIST (2020), MARASON improved spectral cosine similarity over ICEBERG by a relative 5.2% on the random split and 3.7% on the scaffold split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F1** In the NIST random-split retrieval benchmark, MARASON increased top-1 structure retrieval accuracy from ICEBERG’s 18.7% to 27.8%; collision-energy-aware ICEBERG achieved 20.2%.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method.
  - > `2502.17874v2_c0030` As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
  - > `2502.17874v2_c0031` Table 1 only covers the random split; retrieval experiment results on scaffold split are in Table 5 in the Appendix.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
**F2** The structure-identification benchmark ranked candidates by predicted-versus-experimental spectral cosine similarity, using 50 structures per test spectrum: 49 isomeric decoys and 1 true structure.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity. We evaluate the retrieval accuracy at top- k .
  - > `2502.17874v2_c0029` In structural elucidation campaigns, MS/MS simulators can predict pseudo-spectrum labels for candidate structures and compare them to the experimental spectrum.
  - > `2502.17874v2_c0029` Following Goldman et al. (2024) , for each molecule from the testing dataset, we obtain up to 49 isomeric decoys with the highest Tanimoto similarities to the true target structure, i.e., the decoys most likely to be mistaken under Tanimoto measurement.
**F3** On MassSpecGym, MARASON improved top-1 retrieval accuracy over FraGNNet from 31.93% to 34.03%.
  - > `2502.17874v2_c0031` We further retrain MARASON on the recently developed open-source dataset, MassSpecGym ( Bushuiev et al., 2024 ) , where we achieve state-of-the-art retrieval accuracy, as shown in Table 2 .
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method.
**F4** MARASON retrieves the reference molecule with the highest Tanimoto similarity on Morgan fingerprints from the training dataset, excluding mismatched adduct and instrument types; it selects up to three reference spectra with collision energies closest to the target.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) .
  - > `2502.17874v2_c0014` We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F5** Built on ICEBERG, MARASON annotates reference peaks with predicted fragments, constructs fragmentation DAGs for target and reference molecules, and matches their fragments to inform intensity prediction. Nested GNNs encode fragment structures and fragmentation hierarchy for neural graph matching.
  - > `2502.17874v2_c0008` MARASON is built upon the ICEBERG ( Goldman et al., 2024 ) model and incorporates design principles of neural graph matching ( Wang et al., 2022 ; Yu et al., 2020 ) .
  - > `2502.17874v2_c0008` We exploit ICEBERG’s fragmentation model to annotate reference spectrum peaks with fragments and form a fragmentation directed acyclic graph (DAG) with peak annotations for both the target and reference structures. We then match reference fragments to target fragments to inform the second-stage model’s intensity prediction.
  - > `2502.17874v2_c0008` We incorporate nested graph neural networks (GNNs) ( Zhang & Li, 2021 ; Scarselli et al., 2008 ) to encode (a) structural information of each fragment and (b) hierarchical information of the fragmentation DAG into node embeddings, building a neural graph matching network for MS/MS simulation.
**F6** MARASON uses reference structures and known spectra from the NIST (2020) training dataset.
  - > `2502.17874v2_c0008` In MARASON, we retrieve structures with known reference spectra from the training dataset ( NIST, 2020 ) .
**F7** For MassSpecGym, MARASON was retrained from scratch; a NIST-pretrained model supplied pseudo labels for missing collision energies, which MARASON requires.
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym. The model is retrained from scratch on MassSpecGym data to ensure no data leakage from NIST.
**F8** In the NIST (2020) comparison of MARASON with and without RAG, retrieval brought significant gains when reference–target Tanimoto similarity was larger than 0.3; similarities between 0.1 and 0.3 brought no significant improvement.
  - > `2502.17874v2_c0034` To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ).
  - > `2502.17874v2_c0034` As shown in Table 4 , RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3. When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references.
**F9** A slight performance drop in the Tanimoto interval (0.1, 0.2] led the authors to suggest using standard MARASON when similarity is >0.2 and the non-RAG version otherwise.
  - > `2502.17874v2_c0034` The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.
**F10** MARASON outperformed naive concatenation of a retrieved spectrum and traditional graph-matching alternatives; simply copying retrieved spectra also produced lower cosine similarities than all baseline models’ predictions.
  - > `2502.17874v2_c0008` Ablations demonstrate that MARASON outperforms a naive RAG baseline (by concatenating the retrieved spectrum to the model input) as well as other matching methods using traditional graph matching solver ( Cho et al., 2010 ) or a simple linear matching solver ( Kuhn, 1955 ) , emphasizing the value of its differentiable, end-to-end neural graph matching module.
  - > `2502.17874v2_c0024` It is worth noting, from the dashed lines in the plots, that the retrieved spectra are informative, but the cosine similarities of the retrieved spectra are lower than the predicted spectra produced by all baseline models, demonstrating that RAG on MS/MS is a non-trivial task.
**L0** All experiments enforce a molecular mass upper limit of 1500 Da.
  - > `2502.17874v2_c0002` “Small molecules” are defined in this work by a mass upper limit of 1500 Da, enforced in all experiments.
**L1** The NIST retrieval benchmark uses positive adduct types and reports means with 95% confidence intervals across 3 random seeds.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
**L2** The MassSpecGym retrieval results assume a known chemical formula; MARASON uses random seed 1.
  - > `2502.17874v2_table_b0dc99546ec1da3a_4` Table 2: Retrieval accuracy (mean with 99.9% confidence intervals upon bootstrapping, 20,000 resamples) with known chemical formula on the MassSpecGym dataset
  - > `2502.17874v2_c0031` Random seed is fixed as 1 for MARASON.
**L3** The similarity-dependent retrieval comparison reports cosine similarity on the random split with random seed 1.
  - > `2502.17874v2_c0031` The performance of MARASON with and without RAG on target and reference pairs grouped by Tanimoto similarity. We report cosine similarity on the random split with random seed = 1

### Answer B

**F0** On NIST (2020), MARASON improved spectral cosine similarity over ICEBERG by a relative 5.2% on the random split and a relative 3.7% on the scaffold split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F1** In the NIST (2020) random-split retrieval benchmark, MARASON increased top-1 accuracy from ICEBERG’s 18.7% to 27.8%; collision-energy-aware ICEBERG achieved 20.2%.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method. As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
**F2** The structural identification benchmark ranks 50 structures per test spectrum—49 isomeric decoys plus the true structure—by cosine similarity between predicted and experimental spectra.
  - > `2502.17874v2_c0029` In structural elucidation campaigns, MS/MS simulators can predict pseudo-spectrum labels for candidate structures and compare them to the experimental spectrum.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity.
  - > `2502.17874v2_c0029` Following Goldman et al. (2024) , for each molecule from the testing dataset, we obtain up to 49 isomeric decoys with the highest Tanimoto similarities to the true target structure, i.e., the decoys most likely to be mistaken under Tanimoto measurement.
**F3** On MassSpecGym, MARASON improved top-1 retrieval accuracy from FraGNNet’s 31.93% to 34.03%.
  - > `2502.17874v2_c0031` We further retrain MARASON on the recently developed open-source dataset, MassSpecGym ( Bushuiev et al., 2024 ) , where we achieve state-of-the-art retrieval accuracy, as shown in Table 2 .
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method.
**F4** MARASON retrieves known structure–spectrum pairs from its training dataset, including NIST (2020), and uses ICEBERG to construct target and reference fragmentation DAGs. Matching reference fragments to target fragments informs the model’s peak-intensity predictions.
  - > `2502.17874v2_c0008` In MARASON, we retrieve structures with known reference spectra from the training dataset ( NIST, 2020 ) . We exploit ICEBERG’s fragmentation model to annotate reference spectrum peaks with fragments and form a fragmentation directed acyclic graph (DAG) with peak annotations for both the target and reference structures. We then match reference fragments to target fragments to inform the second-stage model’s intensity prediction.
**F5** Retrieval selects the most similar reference molecule using Tanimoto similarity on Morgan fingerprints, excludes mismatched adduct or instrument types, and selects up to three reference spectra with the closest collision energies.
  - > `2502.17874v2_c0014` We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) . We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F6** The reference spectra support interpolation to the target collision energy, while ICEBERG-predicted reference fragments enrich the observed peak information.
  - > `2502.17874v2_c0015` As the collision energy value is continuous, our aim of including three reference energies is to learn an appropriate spectrum embedding for the target collision energy value by interpolating from three closest energies. Reference spectra only provide m/z values and peak intensities. This information is enriched by annotating peaks with ICEBERG-predicted fragments of the reference structure.
**F7** For MassSpecGym training, a NIST-pretrained model supplied pseudo labels for missing collision energies; MARASON was then retrained from scratch on MassSpecGym to avoid data leakage from NIST.
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym. The model is retrained from scratch on MassSpecGym data to ensure no data leakage from NIST.
**F8** In the NIST (2020) test-data analysis, retrieval produced a significant performance gain when reference–target Tanimoto similarity was larger than 0.3; similarities between 0.1 and 0.3 produced no significant improvement.
  - > `2502.17874v2_c0034` To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ).
  - > `2502.17874v2_c0034` As shown in Table 4 , RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3. When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references.
**F9** A slight performance drop at Tanimoto similarity (0.1, 0.2] led the authors to suggest using standard MARASON when similarity is >0.2 and the non-RAG version otherwise.
  - > `2502.17874v2_c0034` The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.
**F10** MARASON outperformed naive retrieval augmentation by spectrum concatenation and traditional graph-matching approaches; simply using retrieved spectra also yielded lower cosine similarity than predictions from all baseline models.
  - > `2502.17874v2_c0008` Ablations demonstrate that MARASON outperforms a naive RAG baseline (by concatenating the retrieved spectrum to the model input) as well as other matching methods using traditional graph matching solver ( Cho et al., 2010 ) or a simple linear matching solver ( Kuhn, 1955 ) , emphasizing the value of its differentiable, end-to-end neural graph matching module.
  - > `2502.17874v2_c0024` the retrieved spectra are informative, but the cosine similarities of the retrieved spectra are lower than the predicted spectra produced by all baseline models, demonstrating that RAG on MS/MS is a non-trivial task.
**L0** All experiments enforced a molecular mass upper limit of 1500 Da.
  - > `2502.17874v2_c0002` “Small molecules” are defined in this work by a mass upper limit of 1500 Da, enforced in all experiments.
**L1** The NIST retrieval accuracy comparison covers positive adduct types on a random InChI key split.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
**L2** The MassSpecGym retrieval benchmark assumes a known chemical formula.
  - > `2502.17874v2_table_b0dc99546ec1da3a_4` Table 2: Retrieval accuracy (mean with 99.9% confidence intervals upon bootstrapping, 20,000 resamples) with known chemical formula on the MassSpecGym dataset
**L3** The similarity thresholds derive from grouped NIST test-data comparisons; their transfer to the client's library is not established by the supplied passages.
  - > `2502.17874v2_c0034` To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ).

### Answer C

**F0** MARASON improved both simulated spectra and downstream structure identification. On NIST (2020), spectral cosine similarity improved over ICEBERG by a relative 5.2% on the random split and 3.7% on the scaffold split; random-split top-1 structure retrieval accuracy rose from 18.7% to 27.8%, compared with 20.2% for collision-energy-aware ICEBERG. On MassSpecGym, top-1 accuracy increased from FraGNNet’s 31.93% to 34.03%.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method. As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
  - > `2502.17874v2_c0031` Table 1 only covers the random split; retrieval experiment results on scaffold split are in Table 5 in the Appendix.
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method.
**F1** Built on ICEBERG, MARASON retrieves reference molecules and their spectra from the training library using Tanimoto similarity, then fragments both target and reference molecules. Neural graph matching aligns their fragmentation DAGs and corresponding fragments and peaks, allowing reference intensity information to inform predictions even when corresponding peaks have different mass-to-charge values.
  - > `2502.17874v2_c0012` MARASON is a mass spectrum simulator built on the ICEBERG model ( Goldman et al., 2024 ) with reference retrieval augmentation and neural graph matching.
  - > `2502.17874v2_c0005` We retrieve reference structures and spectra from a reference library (more specifically, the training dataset) based on Tanimoto similarity ( Bajusz et al., 2015 ) to the target structure. Both target and reference structures are fragmented, resulting in two similar fragmentation DAGs, as similar structures are expected to have similar fragmentation patterns in chemistry ( Shahneh et al., 2024 )
  - > `2502.17874v2_c0035` On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
  - > `2502.17874v2_c0027` The retrieved reference structure, as shown in the plot, is structurally similar to the target structure, whereby the reference spectrum offers important intensity information. Our graph-matching-based RAG strategy associates reference peaks with the target, despite the peaks having different m/z values between the reference and the target.
**F2** The study used NIST (2020) and separately retrained MARASON from scratch on MassSpecGym. Because MARASON requires collision-energy labels, a NIST-pretrained model supplied pseudo labels for MassSpecGym spectra missing that annotation; thus, the MassSpecGym model was trained from scratch while retaining NIST-derived collision-energy information.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym. The model is retrained from scratch on MassSpecGym data to ensure no data leakage from NIST.
**F3** Retrieval helped in the reported random- and scaffold-split evaluations, so its benefit was not confined to highly similar reference structures. The evidence favors learned alignment: MARASON outperformed naive retrieval augmentation and traditional graph matching, and its matching module could associate slightly modified fragments as well as exact matches.
  - > `2502.17874v2_c0030` MARASON outperforms all baselines in both types of splits, and the success on scaffold split excludes the possibility that MARASON needs highly similar reference structures for accurate predictions.
  - > `2502.17874v2_c0000` Moreover, MARASON outperforms both naive retrieval-augmented generation methods and traditional graph matching approaches.
  - > `2502.17874v2_c0031` Our matching module learns to match not only exact structures (pair 2, 3, 4, 5), but also correlated structures with slight modifications (pair 1, 6).
**L0** The supplied passages describe a similarity-stratified retrieval ablation but provide no numerical results establishing when retrieval helps or hurts.
  - > `2502.17874v2_c0031` The performance of MARASON with and without RAG on target and reference pairs grouped by Tanimoto similarity. We report cosine similarity on the random split with random seed = 1
**L1** The NIST identification results concern ranking a true structure against up to 49 similar isomeric decoys; they do not establish a pharmaceutical deployment success rate.
  - > `2502.17874v2_c0029` Following Goldman et al. (2024) , for each molecule from the testing dataset, we obtain up to 49 isomeric decoys with the highest Tanimoto similarities to the true target structure, i.e., the decoys most likely to be mistaken under Tanimoto measurement.
**L2** MassSpecGym training starts from scratch, but missing collision-energy annotations incorporate information from a NIST-pretrained model.
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym.

### Answer D

**F0** On NIST (2020), MARASON improved spectral cosine similarity over ICEBERG by a relative 5.2% on the random split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F1** On NIST (2020), MARASON improved spectral cosine similarity over ICEBERG by a relative 3.7% on the scaffold split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F2** In the NIST (2020) random-split retrieval benchmark on positive adduct types, MARASON improved top-1 accuracy from ICEBERG’s 18.7% to 27.8%. The evaluation ranked 50 structures per test spectrum: 49 decoys + 1 true structure.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity.
**F3** The collision-aware ICEBERG ablation achieved top-1 accuracy of 20.2%; the paper attributes the majority of MARASON’s improvement to RAG.
  - > `2502.17874v2_c0030` As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
**F4** On MassSpecGym with known chemical formula, MARASON improved top-1 retrieval accuracy from FraGNNet’s 31.93% to 34.03%. MARASON’s random seed was fixed as 1.
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method. Random seed is fixed as 1 for MARASON.
  - > `2502.17874v2_table_b0dc99546ec1da3a_4` Table 2: Retrieval accuracy (mean with 99.9% confidence intervals upon bootstrapping, 20,000 resamples) with known chemical formula on the MassSpecGym dataset ( Bushuiev et al., 2024 ) .
**F5** MARASON retrieves the most similar reference molecule using Tanimoto similarity on Morgan fingerprints; the experiments use the training dataset as the retrieval database to mitigate data leakage.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) .
**F6** MARASON excludes references with nonmatching adduct or instrument types, then selects up to three reference spectra with collision energies closest to the target.
  - > `2502.17874v2_c0014` We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F7** Built on ICEBERG, MARASON annotates reference peaks with fragments and matches reference and target fragmentation DAGs to inform intensity prediction. Nested GNNs encode fragment structure and fragmentation hierarchy for neural graph matching.
  - > `2502.17874v2_c0008` MARASON is built upon the ICEBERG ( Goldman et al., 2024 ) model and incorporates design principles of neural graph matching ( Wang et al., 2022 ; Yu et al., 2020 ) .
  - > `2502.17874v2_c0008` We exploit ICEBERG’s fragmentation model to annotate reference spectrum peaks with fragments and form a fragmentation directed acyclic graph (DAG) with peak annotations for both the target and reference structures. We then match reference fragments to target fragments to inform the second-stage model’s intensity prediction. We incorporate nested graph neural networks (GNNs) ( Zhang & Li, 2021 ; Scarselli et al., 2008 ) to encode (a) structural information of each fragment and (b) hierarchical information of the fragmentation DAG into node embeddings, building a neural graph matching network for MS/MS simulation.
**F8** The initial training/reference dataset was NIST (2020), containing structures with known reference spectra.
  - > `2502.17874v2_c0008` In MARASON, we retrieve structures with known reference spectra from the training dataset ( NIST, 2020 ) .
**F9** MARASON was also retrained from scratch on MassSpecGym; missing collision-energy labels were supplied as pseudo labels by a NIST-pretrained model.
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym. The model is retrained from scratch on MassSpecGym data to ensure no data leakage from NIST.
**F10** In the NIST (2020) test-data comparison of MARASON with and without RAG, retrieval began providing a significant performance gain when reference–target Tanimoto similarity was larger than 0.3.
  - > `2502.17874v2_c0034` To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ). As shown in Table 4 , RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3.
**F11** In that NIST (2020) comparison, a best-reference Tanimoto similarity between 0.1 and 0.3 produced no significant retrieval improvement.
  - > `2502.17874v2_c0034` To understand the relationship between RAG’s improvement and the availability of a similar-enough reference structure, for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ).
  - > `2502.17874v2_c0034` When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references.
**F12** A slight performance drop for Tanimoto similarity (0.1, 0.2] led the authors to suggest using standard MARASON above >0.2 and the non-RAG version otherwise; this is a suggested switching rule.
  - > `2502.17874v2_c0034` The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.
**F13** MARASON’s ablations outperformed both naive concatenation of a retrieved spectrum and traditional graph-matching approaches.
  - > `2502.17874v2_c0008` Ablations demonstrate that MARASON outperforms a naive RAG baseline (by concatenating the retrieved spectrum to the model input) as well as other matching methods using traditional graph matching solver ( Cho et al., 2010 ) or a simple linear matching solver ( Kuhn, 1955 ) , emphasizing the value of its differentiable, end-to-end neural graph matching module.
**I0** For a pharmaceutical analytics client, these results support evaluating graph-matched retrieval against a non-RAG baseline on your own reference coverage, with similarity-based fallback as a candidate policy.
  - > `2502.17874v2_c0034` As shown in Table 4 , RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3. When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references.
  - > `2502.17874v2_c0034` The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.
  - > `2502.17874v2_c0008` Ablations demonstrate that MARASON outperforms a naive RAG baseline (by concatenating the retrieved spectrum to the model input) as well as other matching methods using traditional graph matching solver ( Cho et al., 2010 ) or a simple linear matching solver ( Kuhn, 1955 ) , emphasizing the value of its differentiable, end-to-end neural graph matching module.
**L0** The experiments impose a 1500 Da mass upper limit; the benchmark findings do not establish performance on the client’s compounds and reference coverage.
  - > `2502.17874v2_c0002` “Small molecules” are defined in this work by a mass upper limit of 1500 Da, enforced in all experiments.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage.
**L1** The similarity analysis reports cosine similarity on the random split with seed 1. The fallback threshold is an author suggestion, rather than a numerically evaluated switching policy in the supplied passages.
  - > `2502.17874v2_c0031` The performance of MARASON with and without RAG on target and reference pairs grouped by Tanimoto similarity. We report cosine similarity on the random split with random seed = 1
  - > `2502.17874v2_c0034` The slight performance drop between Tanimoto similarity (0.1, 0.2] also suggests a simple trick to further improve MARASON’s accuracy: use standard MARASON when the retrieved structure has a Tanimoto similarity >0.2 and use the non-RAG version otherwise.

---

## J03

A hospital network wants to benchmark LLMs for clinical decision support. What do CliBench and MedQA-CS evaluate, how did leading models perform, and what limits apply to using these results?

- **J03.1** CliBench is built from MIMIC-IV real clinical cases and covers four decisions: diagnosis, procedures, lab test orders and prescriptions.
- **J03.2** Two components, both required for 1: (a) state-of-the-art LLMs do not perform well on diagnosis; GPT-4o is the best model, 7.37 points ahead of the best open model on full-code F1; (b) procedures and lab orders are much worse, with near-zero performance for lowest-level procedure decisions.
- **J03.3** Domain-specialized medical models did not outperform (or only slightly improved over) their base models and fell behind general instruction-tuned models.
- **J03.4** MedQA-CS is an OSCE-style framework with LLM-as-medical-student and LLM-as-examiner tasks; student scores ranged from 48.44 (GPT-3.5) to 62.35 (Claude-3.5-Sonnet), far below the 90+ scores on knowledge benchmarks such as MedQA.
- **J03.5** MedQA-CS limitation: a small USMLE Step 2 CS-derived sample of mostly common conditions, lacking pediatrics, psychiatry and rare diseases.

### Answer A

**L0** The passages describe the benchmarks but do not supply named leading models, their scores, rankings, or evaluation dates, so the requested performance comparison cannot be established. CliBench evaluates diagnoses, treatment procedures, lab orders, and prescriptions using structured, multigranular evaluation of MIMIC-IV cases; its reported evaluation uses zero-shot configurations.
  - > `2406.09923v2_c0000` To bridge this gap, we introduce CliBench , a novel benchmark developed from the MIMIC IV dataset, offering a comprehensive and realistic assessment of LLMs’ capabilities in clinical diagnosis. This benchmark not only covers diagnoses from a diverse range of medical cases across various specialties but also incorporates tasks of clinical significance: treatment procedure identification, lab test ordering and medication prescriptions. Supported by structured output ontologies, CliBench enables a precise and multi-granular evaluation, offering an in-depth understanding of LLM’s capability on diverse clinical tasks of desired granularity. We conduct a zero-shot evaluation of leading LLMs to assess their proficiency in clinical decision-making.
**L1** MedQA-CS evaluates instruction-following clinical skills under USMLE Step 2-CS guidelines: information gathering, physical examination, closure, and diagnosis. The passages report lower performance than on previous multiple-choice benchmarks, but provide no individual model results or numerical size of that difference.
  - > `2410.01553v2_c0003` Despite achieving performance levels comparable to or exceeding those of experts in previous MCQ benchmarks, LLMs’ scores on MedQA-CS are significantly lower, highlighting the discrepancy between clinical knowledge-based assessments and our practical clinical skills-based assessments.
  - > `2410.01553v2_c0003` Unlike previous benchmarks, our framework meticulously follows the USMLE Step 2-CS guidelines to assess four critical aspects of clinical encounters: information gathering, physical examination, closure, and diagnosis.
**L2** MedQA-CS has limited generalizability: its small sample emphasizes common conditions and underrepresents pediatrics, psychiatry, and rare diseases. Its automated judge does not assess the model’s reasoning process, limiting what scores establish about reasoning reliability.
  - > `2410.01553v2_c0027` First, the sample size, derived from the USMLE Step 2 CS, is relatively small and may not comprehensively represent the full spectrum of clinical medicine disciplines or clinical skills, thus limiting the generalizability of our findings. Notably, our dataset predominantly covers common conditions and lacks adequate representation of certain specialties such as pediatrics and psychiatry, as well as rare diseases.
  - > `2410.01553v2_c0027` Second, the LLM-as-Judge framework in this paper did not consider the reasoning process of MedStuLLM during evaluation.
**L3** MedQA-CS does not assess treatment planning and is restricted to English text, excluding speech, images, and physiological waveforms. The supplied passages also do not report hospital deployment outcomes or patient safety outcomes; those would be needed to establish suitability for the network’s clinical decision support workflows.
  - > `2410.01553v2_c0028` the USMLE only evaluates medical students’ clinical skills up to the diagnostic part of clinical note generation, without extending to treatment plans for each diagnosis. This is why our benchmark does not include this aspect.
  - > `2410.01553v2_c0028` Fourth, all MedQA-CS data are presented exclusively in English, which limits the applicability of our findings in non-English-speaking contexts. In addition, the dataset is constrained to a single modality, using only text-based inputs and outputs. Multimodal clinical data—such as speech (for doctor–patient communication analysis), images (e.g., radiology), or physiological waveforms—are not represented.
  - > `2406.09923v2_c0028` Future research should focus on improving the accuracy, reliability, and applicability of LLMs in real-world clinical settings, leveraging CliBench as a robust tool for comprehensive assessment and iterative enhancement of LLM-powered healthcare solutions.

### Answer B

**F0** CliBench evaluates zero-shot clinical decision making on MIMIC IV cases across specialties: diagnoses, treatment procedures, lab orders and prescriptions, with structured ontologies supporting evaluation at multiple granularities.
  - > `2406.09923v2_c0000` To bridge this gap, we introduce CliBench , a novel benchmark developed from the MIMIC IV dataset, offering a comprehensive and realistic assessment of LLMs’ capabilities in clinical diagnosis. This benchmark not only covers diagnoses from a diverse range of medical cases across various specialties but also incorporates tasks of clinical significance: treatment procedure identification, lab test ordering and medication prescriptions. Supported by structured output ontologies, CliBench enables a precise and multi-granular evaluation, offering an in-depth understanding of LLM’s capability on diverse clinical tasks of desired granularity. We conduct a zero-shot evaluation of leading LLMs to assess their proficiency in clinical decision-making.
**F1** CliBench identifies GPT-4o as its best-performing closed model and LLaMA3 Instruct 70B as its leading open model in the diagnosis analysis.
  - > `2406.09923v2_c0024` We analyze the diagnosis performance with different clinical data attributes by comparing the best-performing close model, GPT-4o, with the leading open model, LLaMA3 Instruct 70B.
**F2** CliBench reports that GPT-4 turbo generates more decisions despite hallucination risk, whereas GPT-3.5 turbo is more conservative—a precision–recall tradeoff relevant to interpreting performance.
  - > `2406.09923v2_c0022` 5) Tradeoff between precision and recall. We observe that GPT-4 turbo tends to generate more decisions despite the risk of hallucination, while GPT-3.5 turbo is more conservative.
**F3** MedQA-CS is an OSCE-inspired benchmark with two roles: LLM-as-medical-student and LLM-as-clinical-skills-examiner.
  - > `2410.01553v2_c0000` We introduce MedQA-CS, an AI-SCE framework inspired by medical education’s Objective Structured Clinical Examinations (OSCEs), to address this gap. MedQA-CS evaluates LLMs through two instruction-following tasks—LLM-as-medical-student and LLM-as-CS-examiner—designed to reflect real clinical scenarios.
**F4** MedQA-CS assesses information gathering, physical examination, closure and diagnosis under USMLE Step 2-CS guidelines; the examiner role is evaluated by agreement with expert scoring.
  - > `2410.01553v2_c0003` Unlike previous benchmarks, our framework meticulously follows the USMLE Step 2-CS guidelines to assess four critical aspects of clinical encounters: information gathering, physical examination, closure, and diagnosis.
  - > `2410.01553v2_c0002` The goal for MedStuLLM is to achieve a better AI-SCE score to demonstrate its clinical skills, while the goal for MedExamLLM is to have a high correlation with the expert examiner’s scoring results to prove its capability as a judge in the clinical domain.
**F5** MedQA-CS reports significantly lower LLM scores than previous multiple-choice benchmarks, including cases where models had matched or exceeded expert performance on those earlier assessments.
  - > `2410.01553v2_c0003` Despite achieving performance levels comparable to or exceeding those of experts in previous MCQ benchmarks, LLMs’ scores on MedQA-CS are significantly lower, highlighting the discrepancy between clinical knowledge-based assessments and our practical clinical skills-based assessments.
**L0** MedQA-CS has a relatively small USMLE Step 2 CS sample, predominantly covering common conditions, with inadequate representation of pediatrics, psychiatry and rare diseases; this limits generalizability.
  - > `2410.01553v2_c0027` First, the sample size, derived from the USMLE Step 2 CS, is relatively small and may not comprehensively represent the full spectrum of clinical medicine disciplines or clinical skills, thus limiting the generalizability of our findings. Notably, our dataset predominantly covers common conditions and lacks adequate representation of certain specialties such as pediatrics and psychiatry, as well as rare diseases.
**L1** MedQA-CS excludes treatment plans and uses exclusively English text inputs and outputs; speech, images and physiological waveforms are not represented.
  - > `2410.01553v2_c0028` the USMLE only evaluates medical students’ clinical skills up to the diagnostic part of clinical note generation, without extending to treatment plans for each diagnosis. This is why our benchmark does not include this aspect.
  - > `2410.01553v2_c0028` Fourth, all MedQA-CS data are presented exclusively in English, which limits the applicability of our findings in non-English-speaking contexts. In addition, the dataset is constrained to a single modality, using only text-based inputs and outputs. Multimodal clinical data—such as speech (for doctor–patient communication analysis), images (e.g., radiology), or physiological waveforms—are not represented.
**L2** MedQA-CS's LLM-as-Judge evaluation did not consider the student's reasoning process because stable, reliable scoring without ground truth reasoning was challenging.
  - > `2410.01553v2_c0027` Second, the LLM-as-Judge framework in this paper did not consider the reasoning process of MedStuLLM during evaluation. This is because we found it challenging to produce stable and reliable scores for MedStuLLM’s reasoning without ground truth reasoning.
**L3** MedQA-CS is a research evaluation resource, not a diagnostic tool or clinical decision support system. Its released data, prompts and evaluation artifacts permit research and educational use only, with no commercial applications.
  - > `2410.01553v2_paragraph_79c4931c0acbd2eb_0` The MedQA-CS benchmark is intended as a resource for advancing research in clinical AI evaluation—not as a diagnostic tool or clinical decision support system.
  - > `2410.01553v2_paragraph_5ef5bfd9c0173705_0` All data, prompts, and evaluation artifacts associated with MedQA-CS are released for research and educational purposes only, with no commercial applications permitted.
**L4** MedQA-CS results do not establish real-world diagnostic reasoning, patient interaction or context-aware judgment; these remain unproven and outside the study's scope.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` Although certain models demonstrate promising performance on specific benchmark sections, their real-world clinical skills—including diagnostic reasoning, patient interaction, and context-aware judgment—remain unproven and outside the scope of this work.

### Answer C

**F0** CliBench evaluates clinical diagnosis, treatment procedure identification, lab test ordering and medication prescriptions using cases from MIMIC IV. Structured output ontologies support evaluation at multiple levels of granularity.
  - > `2406.09923v2_c0000` CliBench , a novel benchmark developed from the MIMIC IV dataset, offering a comprehensive and realistic assessment of LLMs’ capabilities in clinical diagnosis. This benchmark not only covers diagnoses from a diverse range of medical cases across various specialties but also incorporates tasks of clinical significance: treatment procedure identification, lab test ordering and medication prescriptions. Supported by structured output ontologies, CliBench enables a precise and multi-granular evaluation
**F1** CliBench tests general-purpose and medical-domain models, both open and closed source, under zero-shot conditions.
  - > `2406.09923v2_c0003` We conduct experiments using zero-shot configurations of prominent open-sourced and close-sourced LLMs, covering both general-purpose and medical-domain models, to assess their clinical decision-making performance.
**F2** MedQA-CS evaluates instruction following in two roles: medical student and clinical-skills examiner. Following USMLE Step 2-CS guidelines, it assesses information gathering, physical examination, closure and diagnosis.
  - > `2410.01553v2_c0000` MedQA-CS evaluates LLMs through two instruction-following tasks—LLM-as-medical-student and LLM-as-CS-examiner—designed to reflect real clinical scenarios.
  - > `2410.01553v2_c0003` Unlike previous benchmarks, our framework meticulously follows the USMLE Step 2-CS guidelines to assess four critical aspects of clinical encounters: information gathering, physical examination, closure, and diagnosis.
**F3** MedQA-CS distinguishes student clinical-skills scores from examiner agreement with expert scoring; these assess different capabilities.
  - > `2410.01553v2_c0002` The goal for MedStuLLM is to achieve a better AI-SCE score to demonstrate its clinical skills, while the goal for MedExamLLM is to have a high correlation with the expert examiner’s scoring results to prove its capability as a judge in the clinical domain.
**F4** CliBench reports that GPT-4 turbo tended to generate more decisions despite hallucination risk, whereas GPT-3.5 turbo was more conservative.
  - > `2406.09923v2_c0022` 5) Tradeoff between precision and recall. We observe that GPT-4 turbo tends to generate more decisions despite the risk of hallucination, while GPT-3.5 turbo is more conservative.
**F5** CliBench reports that LLaMA3 Instruct 70B favored recall over precision compared with 7B.
  - > `2406.09923v2_c0022` LLaMA3 Instruct 70B also favors recall over precision compared with 7B.
**F6** MedQA-CS reports significantly lower LLM scores than previous multiple-choice benchmarks, indicating a gap between clinical knowledge assessments and its practical clinical-skills assessment.
  - > `2410.01553v2_c0003` Despite achieving performance levels comparable to or exceeding those of experts in previous MCQ benchmarks, LLMs’ scores on MedQA-CS are significantly lower, highlighting the discrepancy between clinical knowledge-based assessments and our practical clinical skills-based assessments.
**F7** MedQA-CS's qualitative reasoning check used 25 randomly selected samples from four sections and two medical experts: inter-annotator agreement was 85.1%. Separately, reported agreement between reasoning and the corresponding response was 81%; these are agreement measures rather than clinical correct-response rates.
  - > `2410.01553v2_c0027` Specifically, we randomly selected 25 samples from four sections and had two medical experts independently annotate the reasoning as either Correct or Incorrect. The inter-annotator agreement was 85.1%, indicating a high level of consistency between experts. Additionally, the agreement between MedStuLLM’s reasoning and the corresponding response, as measured in our previous human evaluation, was 81%.
**L0** MedQA-CS has a relatively small sample, predominantly covers common conditions and inadequately represents pediatrics, psychiatry and rare diseases, limiting generalizability.
  - > `2410.01553v2_c0027` First, the sample size, derived from the USMLE Step 2 CS, is relatively small and may not comprehensively represent the full spectrum of clinical medicine disciplines or clinical skills, thus limiting the generalizability of our findings. Notably, our dataset predominantly covers common conditions and lacks adequate representation of certain specialties such as pediatrics and psychiatry, as well as rare diseases.
**L1** MedQA-CS excludes treatment plans and uses exclusively English, text-based inputs and outputs; these results do not establish performance for treatment planning, other languages or multimodal inputs.
  - > `2410.01553v2_c0028` the USMLE only evaluates medical students’ clinical skills up to the diagnostic part of clinical note generation, without extending to treatment plans for each diagnosis. This is why our benchmark does not include this aspect.
  - > `2410.01553v2_c0028` Fourth, all MedQA-CS data are presented exclusively in English, which limits the applicability of our findings in non-English-speaking contexts. In addition, the dataset is constrained to a single modality, using only text-based inputs and outputs.
**L2** MedQA-CS's automated judging did not assess student reasoning because stable, reliable reasoning scores were difficult to produce without ground truth reasoning.
  - > `2410.01553v2_c0027` Second, the LLM-as-Judge framework in this paper did not consider the reasoning process of MedStuLLM during evaluation. This is because we found it challenging to produce stable and reliable scores for MedStuLLM’s reasoning without ground truth reasoning.
**L3** CliBench calls for improved real-world accuracy, reliability and applicability. MedQA-CS leaves real-world clinical skills unproven and is a research benchmark rather than a clinical decision support system.
  - > `2406.09923v2_c0028` Future research should focus on improving the accuracy, reliability, and applicability of LLMs in real-world clinical settings
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` their real-world clinical skills—including diagnostic reasoning, patient interaction, and context-aware judgment—remain unproven and outside the scope of this work.
  - > `2410.01553v2_paragraph_79c4931c0acbd2eb_0` The MedQA-CS benchmark is intended as a resource for advancing research in clinical AI evaluation—not as a diagnostic tool or clinical decision support system.

### Answer D

**F0** CliBench evaluates diagnoses, treatment procedure identification, lab test ordering and medication prescriptions using cases from MIMIC IV, with structured ontologies supporting evaluation at multiple granularities.
  - > `2406.09923v2_c0000` To bridge this gap, we introduce CliBench , a novel benchmark developed from the MIMIC IV dataset, offering a comprehensive and realistic assessment of LLMs’ capabilities in clinical diagnosis. This benchmark not only covers diagnoses from a diverse range of medical cases across various specialties but also incorporates tasks of clinical significance: treatment procedure identification, lab test ordering and medication prescriptions. Supported by structured output ontologies, CliBench enables a precise and multi-granular evaluation, offering an in-depth understanding of LLM’s capability on diverse clinical tasks of desired granularity.
**F1** CliBench tests general-purpose and medical-domain models, both open-source and closed-source, in zero-shot configurations.
  - > `2406.09923v2_c0003` We conduct experiments using zero-shot configurations of prominent open-sourced and close-sourced LLMs, covering both general-purpose and medical-domain models, to assess their clinical decision-making performance.
**F2** CliBench reports that GPT-4 turbo tends to generate more decisions despite hallucination risk, whereas GPT-3.5 turbo is more conservative.
  - > `2406.09923v2_c0022` 5) Tradeoff between precision and recall. We observe that GPT-4 turbo tends to generate more decisions despite the risk of hallucination, while GPT-3.5 turbo is more conservative.
**F3** MedQA-CS evaluates OSCE-inspired clinical skills through two instruction-following roles: LLM-as-medical-student and LLM-as-CS-examiner.
  - > `2410.01553v2_c0000` We introduce MedQA-CS, an AI-SCE framework inspired by medical education’s Objective Structured Clinical Examinations (OSCEs), to address this gap. MedQA-CS evaluates LLMs through two instruction-following tasks—LLM-as-medical-student and LLM-as-CS-examiner—designed to reflect real clinical scenarios.
**F4** MedQA-CS follows USMLE Step 2-CS guidelines to assess information gathering, physical examination, closure and diagnosis.
  - > `2410.01553v2_c0003` Unlike previous benchmarks, our framework meticulously follows the USMLE Step 2-CS guidelines to assess four critical aspects of clinical encounters: information gathering, physical examination, closure, and diagnosis.
**F5** The MedQA-CS examiner role is evaluated by how closely its scoring correlates with expert examiners’ scores.
  - > `2410.01553v2_c0002` The goal for MedStuLLM is to achieve a better AI-SCE score to demonstrate its clinical skills, while the goal for MedExamLLM is to have a high correlation with the expert examiner’s scoring results to prove its capability as a judge in the clinical domain.
**F6** The MedQA-CS paper reports significantly lower LLM scores than on previous multiple-choice benchmarks, despite comparable-to-expert or better performance on those earlier benchmarks.
  - > `2410.01553v2_c0003` Despite achieving performance levels comparable to or exceeding those of experts in previous MCQ benchmarks, LLMs’ scores on MedQA-CS are significantly lower, highlighting the discrepancy between clinical knowledge-based assessments and our practical clinical skills-based assessments.
**L0** CliBench's reported GPT comparison is qualitative and appears in the discharge-diagnosis discussion; it should not be treated as an overall benchmark ranking or a quantified hallucination comparison.
  - > `2406.09923v2_c0022` 5) Tradeoff between precision and recall. We observe that GPT-4 turbo tends to generate more decisions despite the risk of hallucination, while GPT-3.5 turbo is more conservative.
**L1** MedQA-CS has a relatively small sample dominated by common conditions, with inadequate representation of pediatrics, psychiatry and rare diseases. Its automated judge excludes the student model's reasoning process.
  - > `2410.01553v2_c0027` First, the sample size, derived from the USMLE Step 2 CS, is relatively small and may not comprehensively represent the full spectrum of clinical medicine disciplines or clinical skills, thus limiting the generalizability of our findings. Notably, our dataset predominantly covers common conditions and lacks adequate representation of certain specialties such as pediatrics and psychiatry, as well as rare diseases.
  - > `2410.01553v2_c0027` Second, the LLM-as-Judge framework in this paper did not consider the reasoning process of MedStuLLM during evaluation.
**L2** MedQA-CS excludes treatment plans and uses English-only, text-only data, limiting applicability to treatment planning, other languages and multimodal workflows.
  - > `2410.01553v2_c0028` However, due to limitations in the original USMLE Step 2 CS dataset (as illustrated in Figure 2 ), the USMLE only evaluates medical students’ clinical skills up to the diagnostic part of clinical note generation, without extending to treatment plans for each diagnosis. This is why our benchmark does not include this aspect.
  - > `2410.01553v2_c0028` Fourth, all MedQA-CS data are presented exclusively in English, which limits the applicability of our findings in non-English-speaking contexts. In addition, the dataset is constrained to a single modality, using only text-based inputs and outputs. Multimodal clinical data—such as speech (for doctor–patient communication analysis), images (e.g., radiology), or physiological waveforms—are not represented.
**L3** MedQA-CS measures instruction following and text generation; real-world clinical competence remains unproven. It is a research benchmark, not a clinical decision support system, and clinical integration requires validation and human oversight.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` Although certain models demonstrate promising performance on specific benchmark sections, their real-world clinical skills—including diagnostic reasoning, patient interaction, and context-aware judgment—remain unproven and outside the scope of this work. The benchmark focuses on the instruction-following and text generation capabilities of LLMs, not on medical decision-making or actual patient care.
  - > `2410.01553v2_paragraph_79c4931c0acbd2eb_0` The MedQA-CS benchmark is intended as a resource for advancing research in clinical AI evaluation—not as a diagnostic tool or clinical decision support system.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The safe integration of LLMs into medical workflows must be pursued with caution, emphasizing close collaboration with clinicians, rigorous validation, and continuous human oversight.

---

## J04

A health insurer wants to use an LLM to grade other LLMs' medical answers. What do MedQA-CS and Med-CoDE show about how reliable LLM-based evaluators are, and where do they fall short?

- **J04.1** MedQA-CS: GPT-4 as examiner correlated with experts at Pearson r 0.90 (information gathering), 0.92 (physical exam) and 0.78 (diagnosis), but only 0.47 for the closure section.
- **J04.2** MedQA-CS: a fine-tuned LLaMA 3.1-8B judge matched GPT-4 on information gathering (0.9289) and physical exam (0.93) but stayed below 0.3 on diagnosis versus GPT-4's 0.78.
- **J04.3** Med-CoDE is a critique-based framework: a fine-tuned critique generator and classifier assign four levels of disagreement with the ground truth, trained on 38,819 GPT-4-generated critiques.
- **J04.4** In the human evaluation of disagreement classification, Med-CoDE scored 71.72% accuracy versus 78.12% for GPT-3.5. Stating that Med-CoDE outperformed GPT-3.5 on this evaluation is a misleading claim.
- **J04.5** About 240 of 265 (91%) GPT-4-generated critique samples were judged accurate: this is the quality of the training data, not Med-CoDE's accuracy; presenting it as the framework's accuracy is a misleading claim.

### Answer A

**F0** MedQA-CS tests evaluator reliability by comparing LLM grades with expert assessments of clinical skills; its reliability experiment reviewed GPT-4 student responses.
  - > `2410.01553v2_c0016` RQ1: Assessing the reliability of LLMs as judges in the MedQA-CS context (for MedExamLLM). This involves benchmarking various LLMs’ MedExamLLM capabilities and evaluating AI-expert agreements when reviewing MedStuLLM (GPT-4) results.
**F1** In MedQA-CS, GPT-4 had the highest reported evaluator reliability: Pearson correlations with experts were 0.90, 0.92, and 0.78, and Kendall’s tau values were 0.78, 0.53, and 0.69 for Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
**F2** MedQA-CS reported weaker evaluator agreement for Closure: 0.47 for both Pearson correlation and Kendall’s tau. Experts suggested that Closure’s content and evaluation criteria were more subjective.
  - > `2410.01553v2_c0018` For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ). Discussions with experts suggest that, unlike the other three sections, which have more definitive correct answers (e.g., question banks, target physical exams, diagnosis), the content generation and evaluation criteria for Closure are more subjective.
**F3** MedQA-CS also reported strong expert correlations for GPT-4o and Claude-3-Opus, while weaker LLMs performed substantially worse.
  - > `2410.01553v2_c0018` GPT-4o and Claude-3-Opus also demonstrated strong correlations with expert evaluations. In contrast, weaker LLMs showed significantly poorer results.
**F4** MedQA-CS found that carefully chosen traditional metrics could outperform weak LLM judges in InfoGatherQA and Physical Exam, although GPT-4 remained its most reliable evaluator. The paper identified proprietary judges as a cost and reproducibility challenge.
  - > `2410.01553v2_c0019` Overall, carefully chosen traditional metrics are better choices than weak LLM-as-judge in InfoGatherQA and Physical Exam, but MedExamLLM (GPT4) remains the most reliable option.
  - > `2410.01553v2_c0019` However, current options for answer scoring rely on proprietary language models, which pose challenges for future cost and reproducibility.
**F5** Med-CoDE grades discrepancies against medical ground truths using a fine-tuned Phi-3 critique generator and a BERT classifier, rather than relying solely on a general LLM’s grade.
  - > `2504.15330v1_c0002` our framework introduces a critique-based methodology that quantitatively assesses the discrepancies between model-generated responses and established medical ground truths.
  - > `2504.15330v1_c0002` we fine-tuned the Phi-3 model for generating critiques and employed a BERT model for classifying them
**F6** Med-CoDE’s response-evaluation experiments used objective questions from the test sets of Medqa, Medmcqa, Pubmedqa, and Mmlu, evaluating LLaMA-3, Mistral, and BioMistral.
  - > `2504.15330v1_c0013` we conducted experiments on four medical benchmark datasets: Medqa Zhang et al. (2018) , Medmcqa Pal et al. (2022) , Pubmedqa Jin et al. (2019) , and Mmlu Hendrycks et al. (2021) . These datasets are widely used in medical benchmarking and consist of objective-type questions. Our analysis focused on the test sets of these datasets using three LLMs: LLaMA-3 AI@Meta (2024) , Mistral Jiang et al. (2023) , and BioMistral Labrak et al. (2024) .
**F7** In Med-CoDE’s human evaluation of disagreement classification, GPT-3.5 had a reported accuracy of 78.12.
  - > `2504.15330v1_table_de629a5f57790c34_1` Table 1: Human Evaluation Results of Disagreement Classification Framework: GPT-3.5; Accuracy: 78.12
**F8** In the same human evaluation of disagreement classification, Med-Code had a reported accuracy of 71.72, below the reported GPT-3.5 result.
  - > `2504.15330v1_table_de629a5f57790c34_2` Table 1: Human Evaluation Results of Disagreement Classification Framework: Med-Code; Accuracy: 71.72
  - > `2504.15330v1_table_de629a5f57790c34_1` Table 1: Human Evaluation Results of Disagreement Classification Framework: GPT-3.5; Accuracy: 78.12
**F9** Med-CoDE’s discussion of prior work identifies prompt sensitivity as a source of evaluator instability and cautions that generating explanations does not inherently improve reliability because explanations can hallucinate.
  - > `2504.15330v1_c0004` However, current LLM-based evaluators exhibit shortcomings in robustness, as their performance is highly sensitive to prompts, leading to instability in the evaluation process. Recent studies have sought to address these challenges by generating explanations for evaluation outputs Chiang and Lee (2023) , but this approach does not inherently improve robustness or reliability due to issues such as hallucinations Xu et al. (2023) .
**I0** For a health insurer, these findings support using an LLM grader as an aid with expert oversight, with particular scrutiny of subjective communication grades. They do not support treating its grades as sufficient clinical judgment.
  - > `2410.01553v2_c0018` For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ).
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The safe integration of LLMs into medical workflows must be pursued with caution, emphasizing close collaboration with clinicians, rigorous validation, and continuous human oversight.
  - > `2504.15330v1_c0018` even well-evaluated models are not infallible and should not replace human judgment.
  - > `2410.01553v2_c0018` Discussions with experts suggest that, unlike the other three sections, which have more definitive correct answers (e.g., question banks, target physical exams, diagnosis), the content generation and evaluation criteria for Closure are more subjective. This indicates that LLMs need improvement in handling patient-oriented information summarization and communication.
**L0** The reported measures differ: MedQA-CS measures alignment with experts using correlations, while Med-CoDE’s human-evaluation table reports disagreement-classification accuracy.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
  - > `2504.15330v1_table_de629a5f57790c34_2` Table 1: Human Evaluation Results of Disagreement Classification Framework: Med-Code; Accuracy: 71.72
**L1** MedQA-CS concerns instruction following and text generation rather than actual patient care; Med-CoDE’s experiments use objective benchmark questions. These scopes limit transfer to an insurer’s medical-answer grading.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The benchmark focuses on the instruction-following and text generation capabilities of LLMs, not on medical decision-making or actual patient care.
  - > `2504.15330v1_c0013` These datasets are widely used in medical benchmarking and consist of objective-type questions.
**L2** MedQA-CS’s judge reliability assessment reviewed GPT-4 student responses and used default official API parameters with temperature=0 for GPT and Claude 3.
  - > `2410.01553v2_c0016` This involves benchmarking various LLMs’ MedExamLLM capabilities and evaluating AI-expert agreements when reviewing MedStuLLM (GPT-4) results.
  - > `2410.01553v2_c0016` In RQ1 settings, we use all default parameters in their official API with temperature=0 for GPT and Claude 3.

### Answer B

**F0** MedQA-CS found GPT-4 most aligned with expert grading: Pearson correlations were 0.90, 0.92, and 0.78, and Kendall’s tau values were 0.78, 0.53, and 0.69 for Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
**F1** MedQA-CS reported weaker agreement for Closure: 0.47 for both Pearson correlation and Kendall’s tau. Experts suggested that Closure’s content and evaluation criteria are more subjective.
  - > `2410.01553v2_c0018` For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ). Discussions with experts suggest that, unlike the other three sections, which have more definitive correct answers (e.g., question banks, target physical exams, diagnosis), the content generation and evaluation criteria for Closure are more subjective.
**F2** MedQA-CS also reported strong expert correlations for GPT-4o and Claude-3-Opus, while weaker LLMs performed significantly worse.
  - > `2410.01553v2_c0018` GPT-4o and Claude-3-Opus also demonstrated strong correlations with expert evaluations. In contrast, weaker LLMs showed significantly poorer results.
**F3** MedQA-CS attributes high agreement to well-designed prompts aligned with OSCE guidelines and detailed expert-designed evaluation criteria.
  - > `2410.01553v2_c0005` Our experimental results demonstrate that well-designed prompts aligned with OSCE guidelines and detailed expert-designed evaluation criteria can achieve high CS evaluation agreement between LLMs and human experts, showcasing the significant potential of LLM-as-Judge framework in future clinical skill or relevant downstream tasks assessments.
**F4** MedQA-CS found that carefully chosen traditional metrics can outperform weak LLM judges in InfoGatherQA and Physical Exam, although GPT-4 remained its most reliable evaluator.
  - > `2410.01553v2_c0019` Overall, carefully chosen traditional metrics are better choices than weak LLM-as-judge in InfoGatherQA and Physical Exam, but MedExamLLM (GPT4) remains the most reliable option.
**F5** MedQA-CS identifies proprietary scoring models as a challenge for cost and reproducibility, and suggests BERTScore for InfoGatherQA as a possible cost-conscious alternative.
  - > `2410.01553v2_c0019` Considering cost factors, certain sections may use traditional metrics instead of best-performing MedExamLLM as evaluation metrics, such as BERTScore for InfoGatherQA.
  - > `2410.01553v2_c0019` However, current options for answer scoring rely on proprietary language models, which pose challenges for future cost and reproducibility.
**F6** Med-CoDE evaluates discrepancies between ground-truth answers and model predictions using critiques and four levels of disagreement, intended to reveal hallucinations, accuracy, and adherence to the question.
  - > `2504.15330v1_c0016` Med-CoDE excels in identifying subtle discrepancies between ground-truth answers and model predictions, offering a nuanced evaluation with four levels of disagreement. These levels provide insights into the model’s behavior, such as hallucinations, accuracy, and adherence to the question.
  - > `2504.15330v1_c0016` In this work, we introduce Med-CoDE, an evaluation framework designed to assess the performance of Medical LLMs using critiques and degrees of disagreement.
**F7** In Med-CoDE’s human evaluation of disagreement classification, GPT-3.5 had reported accuracy of 78.12.
  - > `2504.15330v1_table_de629a5f57790c34_1` Med-CoDE: Medical Critique based Disagreement Evaluation Framework Table 1: Human Evaluation Results of Disagreement Classification Framework: GPT-3.5; Accuracy: 78.12
**F8** In Med-CoDE’s human evaluation of disagreement classification, Med-Code had reported accuracy of 71.72.
  - > `2504.15330v1_table_de629a5f57790c34_2` Med-CoDE: Medical Critique based Disagreement Evaluation Framework Table 1: Human Evaluation Results of Disagreement Classification Framework: Med-Code; Accuracy: 71.72
**I0** For a health insurer, these results support using an LLM evaluator as a grading aid with expert oversight, with particular scrutiny of subjective communication judgments. They do not justify treating automated grades as definitive.
  - > `2410.01553v2_c0018` For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ).
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The safe integration of LLMs into medical workflows must be pursued with caution, emphasizing close collaboration with clinicians, rigorous validation, and continuous human oversight.
  - > `2504.15330v1_c0018` However, it is essential to recognize that even well-evaluated models are not infallible and should not replace human judgment.
**L0** MedQA-CS assessed evaluator agreement using Pearson correlation and Kendall’s tau while reviewing GPT-4 student responses; this bounds the reliability finding.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
  - > `2410.01553v2_c0016` This involves benchmarking various LLMs’ MedExamLLM capabilities and evaluating AI-expert agreements when reviewing MedStuLLM (GPT-4) results.
**L1** Transfer to insurer-specific answers remains unestablished: MedQA-CS concerns instruction following and text generation rather than actual patient care, and Med-CoDE used standard medical QA benchmarks.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The benchmark focuses on the instruction-following and text generation capabilities of LLMs, not on medical decision-making or actual patient care.
  - > `2504.15330v1_c0018` In this work, only the publicly available standard benchmark medical QA datasets are used for training and evaluations.

### Answer C

**F0** MedQA-CS reported GPT-4 agreement with expert evaluations for Information Gathering at Pearson r. 0.90.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
**F1** MedQA-CS reported GPT-4 agreement with expert evaluations for Information Gathering at Kendall’s tau 0.78.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
**F2** MedQA-CS reported GPT-4 agreement with expert evaluations for Physical Exam at Pearson r. 0.92.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
**F3** MedQA-CS reported GPT-4 agreement with expert evaluations for Physical Exam at Kendall’s tau 0.53.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
**F4** MedQA-CS reported GPT-4 agreement with expert evaluations for Diagnosis at Pearson r. 0.78.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
**F5** MedQA-CS reported GPT-4 agreement with expert evaluations for Diagnosis at Kendall’s tau 0.69.
  - > `2410.01553v2_c0018` As shown in Table 2 , GPT-4 exhibited the highest reliability, with Pearson r. of 0.90, 0.92, and 0.78, and Kendall’s \tau values of 0.78, 0.53, and 0.69 for the Information Gathering, Physical Exam, and Diagnosis, respectively.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
**F6** MedQA-CS reported relatively lower MedExamLLM agreement for Closure, at Pearson correlation 0.47. Experts suggested that Closure’s generation and evaluation criteria were more subjective than those of the other sections.
  - > `2410.01553v2_c0018` For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ). Discussions with experts suggest that, unlike the other three sections, which have more definitive correct answers (e.g., question banks, target physical exams, diagnosis), the content generation and evaluation criteria for Closure are more subjective.
**F7** MedQA-CS reported MedExamLLM agreement for Closure at Kendall’s tau 0.47.
  - > `2410.01553v2_c0018` For the Closure section, MedExamLLM correlations were relatively lower (0.47 for both Pearson and Kendall’s \tau ).
**F8** MedQA-CS reported high agreement with human experts under well-designed prompts aligned with OSCE guidelines and detailed expert-designed evaluation criteria.
  - > `2410.01553v2_c0005` Our experimental results demonstrate that well-designed prompts aligned with OSCE guidelines and detailed expert-designed evaluation criteria can achieve high CS evaluation agreement between LLMs and human experts, showcasing the significant potential of LLM-as-Judge framework in future clinical skill or relevant downstream tasks assessments.
**F9** MedQA-CS found carefully chosen traditional metrics preferable to weak LLM judges for InfoGatherQA and Physical Exam, while identifying GPT-4 as the most reliable examiner.
  - > `2410.01553v2_c0019` Overall, carefully chosen traditional metrics are better choices than weak LLM-as-judge in InfoGatherQA and Physical Exam, but MedExamLLM (GPT4) remains the most reliable option.
**F10** MedQA-CS identified reliance on proprietary language models for answer scoring as a challenge for cost and reproducibility.
  - > `2410.01553v2_c0019` However, current options for answer scoring rely on proprietary language models, which pose challenges for future cost and reproducibility.
**F11** Med-CoDE evaluates discrepancies between ground-truth answers and model predictions through critiques and four levels of disagreement, intended to reveal hallucinations, accuracy problems and failures to adhere to the question.
  - > `2504.15330v1_c0016` In this work, we introduce Med-CoDE, an evaluation framework designed to assess the performance of Medical LLMs using critiques and degrees of disagreement. Med-CoDE excels in identifying subtle discrepancies between ground-truth answers and model predictions, offering a nuanced evaluation with four levels of disagreement. These levels provide insights into the model’s behavior, such as hallucinations, accuracy, and adherence to the question.
**F12** Med-CoDE’s human evaluation of disagreement classification reported GPT-3.5 accuracy as 78.12.
  - > `2504.15330v1_table_de629a5f57790c34_1` Med-CoDE: Medical Critique based Disagreement Evaluation Framework Table 1: Human Evaluation Results of Disagreement Classification Framework: GPT-3.5; Accuracy: 78.12
**F13** Med-CoDE’s human evaluation of disagreement classification reported Med-Code accuracy as 71.72.
  - > `2504.15330v1_table_de629a5f57790c34_2` Med-CoDE: Medical Critique based Disagreement Evaluation Framework Table 1: Human Evaluation Results of Disagreement Classification Framework: Med-Code; Accuracy: 71.72
**L0** MedQA-CS measures correlation with expert evaluations, whereas Med-CoDE reports disagreement-classification accuracy. These are different outcomes; the supplied table rows do not specify accuracy units or denominators, and these results do not establish unsafe-answer miss rates.
  - > `2410.01553v2_c0018` Specifically, the alignment of LLMs’ outputs with expert evaluations was measured using Pearson r. and Kendall’s \tau .
  - > `2504.15330v1_table_de629a5f57790c34_1` Table 1: Human Evaluation Results of Disagreement Classification Framework: GPT-3.5; Accuracy: 78.12
  - > `2504.15330v1_table_de629a5f57790c34_2` Table 1: Human Evaluation Results of Disagreement Classification Framework: Med-Code; Accuracy: 71.72
**L1** Transfer to an insurer’s answer population and actual patient outcomes is untested in the supplied evidence. MedQA-CS concerns instruction following and text generation, while Med-CoDE used standard public medical QA benchmarks.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` Although certain models demonstrate promising performance on specific benchmark sections, their real-world clinical skills—including diagnostic reasoning, patient interaction, and context-aware judgment—remain unproven and outside the scope of this work. The benchmark focuses on the instruction-following and text generation capabilities of LLMs, not on medical decision-making or actual patient care.
  - > `2504.15330v1_c0018` In this work, only the publicly available standard benchmark medical QA datasets are used for training and evaluations.
**L2** MedQA-CS judge reliability was assessed on GPT-4 student responses, with temperature=0 for GPT and Claude 3. Generalization to other answer generators and configurations is not established by that setting.
  - > `2410.01553v2_c0016` RQ1: Assessing the reliability of LLMs as judges in the MedQA-CS context (for MedExamLLM). This involves benchmarking various LLMs’ MedExamLLM capabilities and evaluating AI-expert agreements when reviewing MedStuLLM (GPT-4) results.
  - > `2410.01553v2_c0016` In RQ1 settings, we use all default parameters in their official API with temperature=0 for GPT and Claude 3.

### Answer D

**F0** MedQA-CS supports qualified confidence in strong LLM evaluators: GPT-4 was selected as the most reliable judge, while GPT-4o and Claude-3-Opus also correlated strongly with expert evaluations. This agreement depended on carefully designed prompts and detailed expert evaluation criteria; it does not establish that any LLM can reliably grade medical answers.
  - > `2410.01553v2_c0019` GPT-4o and Claude-3-Opus also demonstrated strong correlations with expert evaluations. In contrast, weaker LLMs showed significantly poorer results.
  - > `2410.01553v2_c0019` Consequently, GPT-4 was selected as the most reliable MedExamLLM for benchmarking clinical skills in MedStuLLM.
  - > `2410.01553v2_c0005` Our experimental results demonstrate that well-designed prompts aligned with OSCE guidelines and detailed expert-designed evaluation criteria can achieve high CS evaluation agreement between LLMs and human experts, showcasing the significant potential of LLM-as-Judge framework in future clinical skill or relevant downstream tasks assessments.
**F1** Reliability varied by task and evaluator. Traditional text metrics agreed poorly with experts for Diagnosis and Closure, but carefully chosen metrics could outperform weaker LLM judges for information gathering and physical examination; reliance on proprietary judges also raised cost and reproducibility concerns.
  - > `2410.01553v2_c0019` Traditional automatic metrics often showed low correlations in the Diagnosis or Closure sections, indicating poor agreement with human experts.
  - > `2410.01553v2_c0019` Overall, carefully chosen traditional metrics are better choices than weak LLM-as-judge in InfoGatherQA and Physical Exam, but MedExamLLM (GPT4) remains the most reliable option.
  - > `2410.01553v2_c0019` However, current options for answer scoring rely on proprietary language models, which pose challenges for future cost and reproducibility.
**F2** The supplied Med-CoDE passage establishes a narrower point: its training and evaluation used publicly available standard medical QA benchmarks, and its authors explicitly caution that even evaluated models remain fallible. It advocates supporting healthcare professionals while retaining human judgment in clinical decisions.
  - > `2504.15330v1_c0018` In this work, only the publicly available standard benchmark medical QA datasets are used for training and evaluations.
  - > `2504.15330v1_c0018` However, it is essential to recognize that even well-evaluated models are not infallible and should not replace human judgment. Instead, they should be used as tools to support healthcare professionals, who must remain the final arbiters in clinical decision-making.
**I0** For an insurer, these passages support using a strong, rubric-guided LLM as an aid to grading, with expert validation on the intended answers and continued human oversight. Agreement with experts on a clinical text benchmark is insufficient evidence to authorize autonomous grading for consequential insurance decisions.
  - > `2410.01553v2_c0005` Our experimental results demonstrate that well-designed prompts aligned with OSCE guidelines and detailed expert-designed evaluation criteria can achieve high CS evaluation agreement between LLMs and human experts, showcasing the significant potential of LLM-as-Judge framework in future clinical skill or relevant downstream tasks assessments.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The benchmark focuses on the instruction-following and text generation capabilities of LLMs, not on medical decision-making or actual patient care.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The safe integration of LLMs into medical workflows must be pursued with caution, emphasizing close collaboration with clinicians, rigorous validation, and continuous human oversight.
**L0** MedQA-CS judge–expert agreement was assessed on GPT-4 student responses; the reported agreement does not establish reliability across all answer-generating models.
  - > `2410.01553v2_c0016` This involves benchmarking various LLMs’ MedExamLLM capabilities and evaluating AI-expert agreements when reviewing MedStuLLM (GPT-4) results.
**L1** MedQA-CS evaluates instruction following and text generation. Its results do not establish reliability in actual patient care or insurer workflows.
  - > `2410.01553v2_paragraph_49942c274f0dcff0_0` The benchmark focuses on the instruction-following and text generation capabilities of LLMs, not on medical decision-making or actual patient care.
**L2** The retained Med-CoDE evidence establishes benchmark scope and an explicit human-judgment caveat, rather than an empirical finding about evaluator accuracy.
  - > `2504.15330v1_c0018` In this work, only the publicly available standard benchmark medical QA datasets are used for training and evaluations.
  - > `2504.15330v1_c0018` However, it is essential to recognize that even well-evaluated models are not infallible and should not replace human judgment.

---

## J05

A biotech client wants natural-language access to its compound-screening database. What did the SANE study show about a few-shot LLM querying a microscopy database - setup, accuracy and failure modes - and how would it perform on the client's own proprietary chemistry database?

- **J05.1** A 4-bit quantized Llama 3.1 in few-shot mode on one 48 GB A6000 GPU, with no training or fine-tuning; a three-stage pipeline checks context sufficiency, generates and executes SQL, and asks for clarification when context is missing.
- **J05.2** 97.2% overall accuracy on 572 queries (556 correct).
- **J05.3** Weakest categories: contextless 81.8% (18/22), multi-step 85.7% (6/7) and error queries 86.1% (31/36), versus 100% on simple queries (159/159).
- **J05.4** Most failures come from wrong context-label prediction or omitted names, not wrong numerical values; ambiguous inputs lead to overly cautious clarification requests.
- **J05.5** Not established: performance on the client's different database is not reported; the study covers one constrained, domain-specific schema. Any accuracy figure for the client's database is fabricated.

### Answer A

**F0** SANE evaluated a PostgreSQL research assistant using 4-bit quantized LlaMA 3.1 without training or fine-tuning; the model ran through vLLM on a single NVIDIA A6000 GPU with 48 GB.
  - > `2606.04500v1_c0003` In this work, we evaluate a custom LLM research assistant that queries a PostgreSQL database using a 4-bit quantized LlaMA 3.1 model without any training or fine-tuning.
  - > `2606.04500v1_c0004` In this work, we evaluate the quantized Llama 3.1 [ 7 ] model running on a single NVIDIA A6000 GPU with 48 GB using virtual large language model(vLLM) [ 9 ] .
**F1** The microscopy database stored morphological features and derived statistics from drug-screening experiments organized by cell line, drug, concentration and replicate images.
  - > `2606.04500v1_c0004` Experiments include one or more cell lines, each cell-line is tested against multiple drugs at various concentrations. Multiple images of replicates are acquired per condition, reflecting standard drug screening protocols. From these images our webapp extracts morphological features and computes derived statistics (EC 50 , dose–response curves, sensitivity scores), storing them in a relational database.
**F2** The interface first classified whether context was missing or sufficient, requested clarification when missing, and otherwise generated SQL and converted the database result into a natural-language answer. Its prompts supplied schema structure, domain terminology, filtering rules, dataset context and examples.
  - > `2606.04500v1_c0005` First the LLM is tasked to determine whether sufficient context is provided to answer the query, outputting a binary label ( missing / sufficient ). If the label is missing , a clarification request is returned. Otherwise we generate a SQL statement with the LLM using schema-aware prompting. The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table.
  - > `2606.04500v1_c0005` For SQL generation, schema-aware prompting injects database structure, domain terminology, filtering rules (e.g., excluding border artifacts), and dataset-specific context and examples to guide the generation.
**F3** SANE generated benchmark questions and reference SQL from real experimental database contents, including controlled typos, abbreviations and missing context. Correctness required the right context label and, for sufficient-context questions, SQL execution results equivalent to the reference results.
  - > `2606.04500v1_c0006` SANE is a framework that systematically generates natural language queries and corresponding ground truth SQL statements directly from database contents and experimental structure (Figure 3 ). The framework queries a pre-existing database from real experiments to extract schema information and representative data instances.
  - > `2606.04500v1_c0006` In addition, it introduces controlled perturbations such as typographical errors, abbreviations, and missing context to simulate realistic user interaction scenarios.
  - > `2606.04500v1_c0007` For missing queries, correctness is determined by label agreement. For sufficient queries, correctness additionally requires that the generated SQL execution results match the reference results (result set equivalence).
**F4** SANE's few-shot evaluation reported 97.2% overall accuracy: 556 correct and 16 false results across 572 questions.
  - > `2606.04500v1_c0008` The few-shot system achieves 97.2% overall accuracy, demonstrating reliable performance across retrieval, complex analysis, and schema-aware tasks without any training or fine-tuning.
  - > `2606.04500v1_table_de629a5f57790c34_7` Category: Total; Total: 572; Correct: 556; False: 16; Accuracy (%): 97.2
**F5** For Simple questions, SANE reported 100.0% accuracy: 159 correct and 0 false out of 159.
  - > `2606.04500v1_table_de629a5f57790c34_1` Category: Simple; Total: 159; Correct: 159; False: 0; Accuracy (%): 100.0
**F6** For Complex questions, SANE reported 98.4% accuracy: 311 correct and 5 false out of 316.
  - > `2606.04500v1_table_de629a5f57790c34_2` Category: Complex; Total: 316; Correct: 311; False: 5; Accuracy (%): 98.4
**F7** For Schema questions, SANE reported 96.9% accuracy: 31 correct and 1 false out of 32.
  - > `2606.04500v1_table_de629a5f57790c34_5` Category: Schema; Total: 32; Correct: 31; False: 1; Accuracy (%): 96.9
**F8** For Errors questions, SANE reported 86.1% accuracy: 31 correct and 5 false out of 36.
  - > `2606.04500v1_table_de629a5f57790c34_3` Category: Errors; Total: 36; Correct: 31; False: 5; Accuracy (%): 86.1
**F9** For Contextless questions, SANE reported 81.8% accuracy: 18 correct and 4 false out of 22.
  - > `2606.04500v1_table_de629a5f57790c34_4` Category: Contextless; Total: 22; Correct: 18; False: 4; Accuracy (%): 81.8
**F10** For Multi-step questions, SANE reported 85.7% accuracy: 6 correct and 1 false out of 7.
  - > `2606.04500v1_table_de629a5f57790c34_6` Category: Multi-step; Total: 7; Correct: 6; False: 1; Accuracy (%): 85.7
**F11** Of the 16 few-shot failures, 10 involved incorrect missing-context classification, typically associated with unknown synonyms or misinterpreted underspecified questions. The paper describes both overly cautious clarification requests and answering questions that needed disambiguation.
  - > `2606.04500v1_c0008` Among the 16 few-shot failures listed in Table 1 , 10 involve incorrect missing context label prediction, typically from unknown synonyms or misinterpreted underspecified queries.
  - > `2606.04500v1_c0000` Most failures stem from ambiguous or underspecified inputs and manifest as overly cautious clarification requests or answers to queries that should first be disambiguated, rather than incorrect SQL generation.
**F12** In 5 cases, generated SQL was slightly incorrect, including omitted drug identifiers in listings or answering overly broad questions instead of requesting clarification.
  - > `2606.04500v1_c0008` In 5 cases, the generated SQL is slightly incorrect, e.g. omitting drug identifiers in listings or answering overly broad questions instead of asking for clarification.
**F13** One question asking for average EC50 for Trametinib on the area feature received a generic dismissive response because the application incorrectly classified it as unrelated to data.
  - > `2606.04500v1_c0008` One question is answered with the generic dismiss answer of the webapp because it is wrongly interpreted as not data-related (Q: What is the average EC50 for Trametinib for the area feature? A: I’m here to help! Feel free to ask about your data or the application.).
**I0** For a client considering natural-language compound-screening access, these results support testing schema-aware prompts, domain examples and clarification handling against reference queries from its own database before estimating accuracy.
  - > `2606.04500v1_c0009` Importantly, performance strongly depends on structured prompting and schema knowledge. Without domain-specific terminology and examples, the LLM cannot reliably produce valid queries.
  - > `2606.04500v1_c0006` SANE is a framework that systematically generates natural language queries and corresponding ground truth SQL statements directly from database contents and experimental structure (Figure 3 ).
  - > `2606.04500v1_c0000` Most failures stem from ambiguous or underspecified inputs and manifest as overly cautious clarification requests or answers to queries that should first be disambiguated, rather than incorrect SQL generation.
**L0** The reported evaluation comprises 572 automatically generated test cases; SANE derives its test queries from high-throughput drug response databases.
  - > `2606.04500v1_c0008` The evaluation comprises 572 automatically generated test cases spanning various database schemas and statistical attributes.
  - > `2606.04500v1_c0003` Here, we introduce SANE , a custom framework that systematically derives realistic, schema-grounded test queries from high-throughput drug response databases for rigorous evaluation.
**L1** The demonstrated accuracy is conditional on domain-specific, example-driven prompting and a limited task scope.
  - > `2606.04500v1_c0008` This high accuracy is achieved through domain-specific and example-driven prompting and by limiting the scope of LLM and the task.
**L2** The accuracy criterion is context-label agreement and, for sufficient-context questions, SQL result-set equivalence. The final natural-language answer is produced by another LLM pass.
  - > `2606.04500v1_c0007` For missing queries, correctness is determined by label agreement. For sufficient queries, correctness additionally requires that the generated SQL execution results match the reference results (result set equivalence).
  - > `2606.04500v1_c0005` The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table.

### Answer B

**F0** SANE evaluated a few-shot, 4-bit quantized LlaMA 3.1 assistant querying PostgreSQL without training or fine-tuning. Its microscopy database stored morphological features and derived dose–response statistics; inference ran on a single NVIDIA A6000 GPU with 48 GB using vLLM.
  - > `2606.04500v1_c0003` In this work, we evaluate a custom LLM research assistant that queries a PostgreSQL database using a 4-bit quantized LlaMA 3.1 model without any training or fine-tuning.
  - > `2606.04500v1_c0004` From these images our webapp extracts morphological features and computes derived statistics (EC 50 , dose–response curves, sensitivity scores), storing them in a relational database. To query this data we can use a text-to-SQL LLM. In this work, we evaluate the quantized Llama 3.1 [ 7 ] model running on a single NVIDIA A6000 GPU with 48 GB using virtual large language model(vLLM) [ 9 ] . Crucially, the model operates in few-shot mode, no training or fine-tuning is performed.
  - > `2606.04500v1_c0004` In high-throughput microscopy, e.g. drug screenings, the datasets typically follow a hierarchical experimental design as in Figure 1 .
**F1** The pipeline classified whether context was sufficient, requested clarification when missing, otherwise generated SQL and converted retrieved results into a natural-language answer. Prompts supplied database structure, domain terminology, filtering rules, dataset context and examples.
  - > `2606.04500v1_c0005` First the LLM is tasked to determine whether sufficient context is provided to answer the query, outputting a binary label ( missing / sufficient ). If the label is missing , a clarification request is returned. Otherwise we generate a SQL statement with the LLM using schema-aware prompting. The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table. For SQL generation, schema-aware prompting injects database structure, domain terminology, filtering rules (e.g., excluding border artifacts), and dataset-specific context and examples to guide the generation.
**F2** SANE generated test questions and reference SQL from real experimental database contents, including controlled input perturbations. Correctness required context-label agreement and, for sufficient-context questions, SQL result-set equivalence.
  - > `2606.04500v1_c0006` SANE is a framework that systematically generates natural language queries and corresponding ground truth SQL statements directly from database contents and experimental structure (Figure 3 ). The framework queries a pre-existing database from real experiments to extract schema information and representative data instances.
  - > `2606.04500v1_c0006` In addition, it introduces controlled perturbations such as typographical errors, abbreviations, and missing context to simulate realistic user interaction scenarios.
  - > `2606.04500v1_c0007` For each question posed to the LLM, we compare the predicted context label ( missing or sufficient ) with ground truth. For missing queries, correctness is determined by label agreement. For sufficient queries, correctness additionally requires that the generated SQL execution results match the reference results (result set equivalence).
**F3** Overall few-shot accuracy was 97.2%: 556 correct and 16 false out of 572 queries.
  - > `2606.04500v1_c0008` The few-shot system achieves 97.2% overall accuracy, demonstrating reliable performance across retrieval, complex analysis, and schema-aware tasks without any training or fine-tuning.
  - > `2606.04500v1_table_de629a5f57790c34_7` Category: Total; Total: 572; Correct: 556; False: 16; Accuracy (%): 97.2
**F4** The zero-shot condition, using only simple schema injection without examples, achieved 29.9% overall accuracy.
  - > `2606.04500v1_c0008` Without examples (zero-shot), solely relying on simple scheme injection, results drop to 29.9% overall accuracy.
**F5** For Simple queries, accuracy was 100.0%: 159 correct and 0 false out of 159.
  - > `2606.04500v1_table_de629a5f57790c34_1` Category: Simple; Total: 159; Correct: 159; False: 0; Accuracy (%): 100.0
**F6** For Complex queries, accuracy was 98.4%: 311 correct and 5 false out of 316.
  - > `2606.04500v1_table_de629a5f57790c34_2` Category: Complex; Total: 316; Correct: 311; False: 5; Accuracy (%): 98.4
**F7** For Schema queries, accuracy was 96.9%: 31 correct and 1 false out of 32.
  - > `2606.04500v1_table_de629a5f57790c34_5` Category: Schema; Total: 32; Correct: 31; False: 1; Accuracy (%): 96.9
**F8** For Errors queries, accuracy was 86.1%: 31 correct and 5 false out of 36.
  - > `2606.04500v1_table_de629a5f57790c34_3` Category: Errors; Total: 36; Correct: 31; False: 5; Accuracy (%): 86.1
**F9** For Contextless queries, accuracy was 81.8%: 18 correct and 4 false out of 22.
  - > `2606.04500v1_table_de629a5f57790c34_4` Category: Contextless; Total: 22; Correct: 18; False: 4; Accuracy (%): 81.8
**F10** For Multi-step queries, accuracy was 85.7%: 6 correct and 1 false out of 7.
  - > `2606.04500v1_table_de629a5f57790c34_6` Category: Multi-step; Total: 7; Correct: 6; False: 1; Accuracy (%): 85.7
**F11** Of the 16 few-shot failures, 10 involved incorrect missing-context labels, typically associated with unknown synonyms or misinterpreted underspecified queries.
  - > `2606.04500v1_c0008` Among the 16 few-shot failures listed in Table 1 , 10 involve incorrect missing context label prediction, typically from unknown synonyms or misinterpreted underspecified queries.
**F12** In 5 cases, SQL was slightly incorrect, including omitted drug identifiers or answering overly broad questions instead of requesting clarification.
  - > `2606.04500v1_c0008` In 5 cases, the generated SQL is slightly incorrect, e.g. omitting drug identifiers in listings or answering overly broad questions instead of asking for clarification.
**F13** One question received the application's generic dismissal because it was incorrectly classified as unrelated to data.
  - > `2606.04500v1_c0008` One question is answered with the generic dismiss answer of the webapp because it is wrongly interpreted as not data-related (Q: What is the average EC50 for Trametinib for the area feature? A: I’m here to help! Feel free to ask about your data or the application.).
**L0** Performance on the client's proprietary chemistry database remains unestablished by the supplied passages. The biological-database result cannot be assumed to transfer unchanged, particularly because performance depends on schema knowledge and domain-specific prompting.
  - > `2606.04500v1_c0010` We presented a systematic evaluation of a custom domain-specific LLM interface for natural-language querying of biological databases.
  - > `2606.04500v1_c0009` Importantly, performance strongly depends on structured prompting and schema knowledge. Without domain-specific terminology and examples, the LLM cannot reliably produce valid queries.
**L1** Accuracy was measured on automatically generated tests using context-label agreement and SQL result-set equivalence. The supplied passages do not establish separate accuracy for the final natural-language answers.
  - > `2606.04500v1_c0008` The evaluation comprises 572 automatically generated test cases spanning various database schemas and statistical attributes.
  - > `2606.04500v1_c0007` For missing queries, correctness is determined by label agreement. For sufficient queries, correctness additionally requires that the generated SQL execution results match the reference results (result set equivalence).
  - > `2606.04500v1_c0005` The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table.
**L2** The Multi-step accuracy estimate rests on only 7 queries.
  - > `2606.04500v1_table_de629a5f57790c34_6` Category: Multi-step; Total: 7; Correct: 6; False: 1; Accuracy (%): 85.7

### Answer C

**F0** SANE evaluated a PostgreSQL research assistant using 4-bit quantized LlaMA 3.1 without training or fine-tuning; it ran through vLLM on a single NVIDIA A6000 GPU with 48 GB.
  - > `2606.04500v1_c0003` In this work, we evaluate a custom LLM research assistant that queries a PostgreSQL database using a 4-bit quantized LlaMA 3.1 model without any training or fine-tuning.
  - > `2606.04500v1_c0004` In this work, we evaluate the quantized Llama 3.1 [ 7 ] model running on a single NVIDIA A6000 GPU with 48 GB using virtual large language model(vLLM) [ 9 ] .
**F1** The microscopy database stored morphological features and derived statistics, including EC 50, dose–response curves and sensitivity scores, from experiments involving cell lines, drugs, concentrations and replicate images.
  - > `2606.04500v1_c0004` Experiments include one or more cell lines, each cell-line is tested against multiple drugs at various concentrations. Multiple images of replicates are acquired per condition, reflecting standard drug screening protocols. From these images our webapp extracts morphological features and computes derived statistics (EC 50 , dose–response curves, sensitivity scores), storing them in a relational database.
**F2** The interface first classified context as missing or sufficient, requested clarification when missing, otherwise generated SQL and converted the retrieved results into a natural-language answer. Its prompts supplied schema structure, domain terminology, filtering rules, dataset context and examples.
  - > `2606.04500v1_c0005` First the LLM is tasked to determine whether sufficient context is provided to answer the query, outputting a binary label ( missing / sufficient ). If the label is missing , a clarification request is returned. Otherwise we generate a SQL statement with the LLM using schema-aware prompting. The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table. For SQL generation, schema-aware prompting injects database structure, domain terminology, filtering rules (e.g., excluding border artifacts), and dataset-specific context and examples to guide the generation.
**F3** SANE generated test queries and reference SQL from real experimental database contents, including controlled typos, abbreviations and missing context. Correctness required the right context label and, for sufficient-context queries, SQL result-set equivalence with the reference.
  - > `2606.04500v1_c0006` The framework queries a pre-existing database from real experiments to extract schema information and representative data instances.
  - > `2606.04500v1_c0006` In addition, it introduces controlled perturbations such as typographical errors, abbreviations, and missing context to simulate realistic user interaction scenarios.
  - > `2606.04500v1_c0007` For each question posed to the LLM, we compare the predicted context label ( missing or sufficient ) with ground truth. For missing queries, correctness is determined by label agreement. For sufficient queries, correctness additionally requires that the generated SQL execution results match the reference results (result set equivalence).
  - > `2606.04500v1_c0006` SANE is a framework that systematically generates natural language queries and corresponding ground truth SQL statements directly from database contents and experimental structure (Figure 3 ).
**F4** Overall, the few-shot system achieved 97.2% accuracy: 556 correct and 16 false results across 572 automatically generated test cases.
  - > `2606.04500v1_c0008` The evaluation comprises 572 automatically generated test cases spanning various database schemas and statistical attributes.
  - > `2606.04500v1_c0008` The few-shot system achieves 97.2% overall accuracy
  - > `2606.04500v1_table_de629a5f57790c34_7` Category: Total; Total: 572; Correct: 556; False: 16; Accuracy (%): 97.2
**F5** In the reported zero-shot condition, without examples and relying solely on simple schema injection, overall accuracy dropped to 29.9%.
  - > `2606.04500v1_c0008` Without examples (zero-shot), solely relying on simple scheme injection, results drop to 29.9% overall accuracy.
**F6** For Simple queries, SANE reported 100.0% accuracy: 159 correct and 0 false out of 159.
  - > `2606.04500v1_table_de629a5f57790c34_1` Category: Simple; Total: 159; Correct: 159; False: 0; Accuracy (%): 100.0
**F7** For Complex queries, SANE reported 98.4% accuracy: 311 correct and 5 false out of 316.
  - > `2606.04500v1_table_de629a5f57790c34_2` Category: Complex; Total: 316; Correct: 311; False: 5; Accuracy (%): 98.4
**F8** For Schema queries, SANE reported 96.9% accuracy: 31 correct and 1 false out of 32.
  - > `2606.04500v1_table_de629a5f57790c34_5` Category: Schema; Total: 32; Correct: 31; False: 1; Accuracy (%): 96.9
**F9** For Errors queries, SANE reported 86.1% accuracy: 31 correct and 5 false out of 36.
  - > `2606.04500v1_table_de629a5f57790c34_3` Category: Errors; Total: 36; Correct: 31; False: 5; Accuracy (%): 86.1
**F10** For Contextless queries, SANE reported 81.8% accuracy: 18 correct and 4 false out of 22.
  - > `2606.04500v1_table_de629a5f57790c34_4` Category: Contextless; Total: 22; Correct: 18; False: 4; Accuracy (%): 81.8
**F11** For Multi-step queries, SANE reported 85.7% accuracy: 6 correct and 1 false out of 7.
  - > `2606.04500v1_table_de629a5f57790c34_6` Category: Multi-step; Total: 7; Correct: 6; False: 1; Accuracy (%): 85.7
**F12** Of the 16 few-shot failures, 10 involved incorrect missing-context classification, typically associated with unknown synonyms or misinterpreted underspecified queries.
  - > `2606.04500v1_c0008` Among the 16 few-shot failures listed in Table 1 , 10 involve incorrect missing context label prediction, typically from unknown synonyms or misinterpreted underspecified queries.
**F13** In 5 cases, generated SQL was slightly incorrect, including omitted drug identifiers in listings or answering overly broad questions instead of requesting clarification.
  - > `2606.04500v1_c0008` In 5 cases, the generated SQL is slightly incorrect, e.g. omitting drug identifiers in listings or answering overly broad questions instead of asking for clarification.
**F14** One question incorrectly received the webapp's generic dismissal because it was classified as unrelated to data.
  - > `2606.04500v1_c0008` One question is answered with the generic dismiss answer of the webapp because it is wrongly interpreted as not data-related
**I0** For the client's deployment decision, this supports a schema-specific pilot with domain examples and explicit clarification handling, followed by evaluation against reference queries from its own database; it does not justify promising the benchmark accuracy in advance.
  - > `2606.04500v1_c0009` Importantly, performance strongly depends on structured prompting and schema knowledge. Without domain-specific terminology and examples, the LLM cannot reliably produce valid queries.
  - > `2606.04500v1_c0006` SANE is a framework that systematically generates natural language queries and corresponding ground truth SQL statements directly from database contents and experimental structure (Figure 3 ).
  - > `2606.04500v1_c0000` Most failures stem from ambiguous or underspecified inputs and manifest as overly cautious clarification requests or answers to queries that should first be disambiguated, rather than incorrect SQL generation.
**L0** The reported evaluation concerns a custom biological database interface and 572 automatically generated queries derived from real experiments; performance depends on structured prompting and schema knowledge.
  - > `2606.04500v1_c0010` We presented a systematic evaluation of a custom domain-specific LLM interface for natural-language querying of biological databases.
  - > `2606.04500v1_c0003` A large-scale evaluation with 572 non-trivial, automatically generated queries derived from real experiments
  - > `2606.04500v1_c0009` Importantly, performance strongly depends on structured prompting and schema knowledge.
**L1** Reported correctness uses context-label agreement and, for sufficient-context queries, SQL result-set equivalence. The final natural-language response is produced by another LLM pass.
  - > `2606.04500v1_c0007` For missing queries, correctness is determined by label agreement. For sufficient queries, correctness additionally requires that the generated SQL execution results match the reference results (result set equivalence).
  - > `2606.04500v1_c0005` The returned database result is then interpreted by another LLM pass, turned into a natural language answer, bulletpoint listing or table.

### Answer D

**F0** SANE tested a few-shot, 4-bit quantized Llama 3.1 interface to a PostgreSQL microscopy database, without training or fine-tuning, running through vLLM on a single NVIDIA A6000 GPU with 48 GB. The database held morphological features and derived dose–response statistics from experiments involving cell lines, drugs, concentrations and replicate images; the interface checked context before generating and executing SQL.
  - > `2606.04500v1_c0003` In this work, we evaluate a custom LLM research assistant that queries a PostgreSQL database using a 4-bit quantized LlaMA 3.1 model without any training or fine-tuning.
  - > `2606.04500v1_c0004` Experiments include one or more cell lines, each cell-line is tested against multiple drugs at various concentrations. Multiple images of replicates are acquired per condition, reflecting standard drug screening protocols. From these images our webapp extracts morphological features and computes derived statistics (EC 50 , dose–response curves, sensitivity scores), storing them in a relational database.
  - > `2606.04500v1_c0004` In this work, we evaluate the quantized Llama 3.1 [ 7 ] model running on a single NVIDIA A6000 GPU with 48 GB using virtual large language model(vLLM) [ 9 ] .
  - > `2606.04500v1_c0004` First, the model determines whether sufficient context is available to answer the query. If the context is sufficient , a SQL query is generated and executed
**F1** The evaluation used 572 automatically generated cases grounded in real experimental data, checking both context classification and SQL execution results against ground truth. It included retrieval, analytical and multi-step questions, with controlled typos, abbreviations and missing context, so the reported accuracy describes this constructed benchmark.
  - > `2606.04500v1_c0008` The evaluation comprises 572 automatically generated test cases spanning various database schemas and statistical attributes.
  - > `2606.04500v1_c0006` The LLM is evaluated by comparing predicted context classifications ( sufficient vs. missing ) and generated SQL execution results against ground truth.
  - > `2606.04500v1_c0006` The framework queries a pre-existing database from real experiments to extract schema information and representative data instances. Based on this information, SANE constructs queries spanning multiple complexity levels, including simple retrieval, complex analytical queries, and multi-step interactions. In addition, it introduces controlled perturbations such as typographical errors, abbreviations, and missing context to simulate realistic user interaction scenarios.
**F2** Few-shot overall accuracy was 97.2%, compared with 29.9% for zero-shot prompting using schema injection alone. Category accuracies were Simple 100%, Complex 98.4%, Schema 96.9%, Contextless 81.8%, Errors 86.1% and Multi-step 85.7%; these results depended on domain-specific examples and a constrained task.
  - > `2606.04500v1_c0008` The few-shot system achieves 97.2% overall accuracy, demonstrating reliable performance across retrieval, complex analysis, and schema-aware tasks without any training or fine-tuning. Simple , Complex and Schema related questions achieve a high accuracy of 100%, 98.4% and 96.9%. In categories Contextless , Errors and Multi-step the LLM performs slightly worse, with 81.8%, 86.1% and 85.7%.
  - > `2606.04500v1_c0008` This high accuracy is achieved through domain-specific and example-driven prompting and by limiting the scope of LLM and the task. Without examples (zero-shot), solely relying on simple scheme injection, results drop to 29.9% overall accuracy.
**F3** There were 16 failures among the 572 cases: 10 involved incorrect missing-context labels, often associated with unfamiliar synonyms or underspecified questions; 5 involved slightly incorrect SQL, such as omitted drug identifiers or answering overly broad questions without clarification. One valid data question received a generic dismissal after being classified as unrelated to data, showing that reliability includes deciding when and what to answer as well as generating SQL.
  - > `2606.04500v1_c0008` The evaluation comprises 572 automatically generated test cases spanning various database schemas and statistical attributes.
  - > `2606.04500v1_c0008` Among the 16 few-shot failures listed in Table 1 , 10 involve incorrect missing context label prediction, typically from unknown synonyms or misinterpreted underspecified queries.
  - > `2606.04500v1_c0008` In 5 cases, the generated SQL is slightly incorrect, e.g. omitting drug identifiers in listings or answering overly broad questions instead of asking for clarification.
  - > `2606.04500v1_c0008` One question is answered with the generic dismiss answer of the webapp because it is wrongly interpreted as not data-related (Q: What is the average EC50 for Trametinib for the area feature? A: I’m here to help! Feel free to ask about your data or the application.).
**I0** For the client's proprietary chemistry database, this supports a promising approach rather than a transferable accuracy guarantee. I would adapt the schema-aware prompts and examples to the client's terminology, benchmark context decisions and executed answers against ground truth from that database, and prioritize clarification of ambiguous requests before making a performance commitment.
  - > `2606.04500v1_c0009` Importantly, performance strongly depends on structured prompting and schema knowledge. Without domain-specific terminology and examples, the LLM cannot reliably produce valid queries.
  - > `2606.04500v1_c0006` The LLM is evaluated by comparing predicted context classifications ( sufficient vs. missing ) and generated SQL execution results against ground truth.
  - > `2606.04500v1_c0009` Failure analysis indicates future improvements should prioritize interactive query refinement and disambiguation rather than model fine-tuning as the model seems to struggle with missing context and unclear questions rather than accurate text-to-SQL generation as shown in the results.
**L0** The reported accuracy applies to 572 automatically generated test cases grounded in experimental database contents, rather than an evaluation of the client's actual user questions.
  - > `2606.04500v1_c0008` The evaluation comprises 572 automatically generated test cases spanning various database schemas and statistical attributes.
  - > `2606.04500v1_c0006` The framework queries a pre-existing database from real experiments to extract schema information and representative data instances.
**L1** Performance depended on domain-specific examples and constrained tasks. The supplied passages do not quantify transfer to the client's proprietary chemistry schema or terminology; the proposed adaptation and validation steps are conditional recommendations.
  - > `2606.04500v1_c0008` This high accuracy is achieved through domain-specific and example-driven prompting and by limiting the scope of LLM and the task.
  - > `2606.04500v1_c0009` Importantly, performance strongly depends on structured prompting and schema knowledge. Without domain-specific terminology and examples, the LLM cannot reliably produce valid queries.

---

## J06

A bank's AI red team wants better ways to test chatbot jailbreak resistance. What are "subtoxic questions", what did the Gradual Attitude Change observations show, how does the paper propose to rank jailbreak prompts, and what jailbreak success rate should the bank expect against its own production chatbot?

- **J06.1** Subtoxic questions are inherently harmless queries mistakenly identified as harmful because of their content composition (harmful content embedded in a benign question).
- **J06.2** Adding positive prompts to subtoxic questions gradually shifts GPT-3.5's responses through stages from firm refusal to a positive reply (Gradual Attitude Change).
- **J06.3** Prompts are ranked by comparing their attitude effects on an evaluation question set, which the authors describe as more precise and efficient than success-rate-based measurement, with low variance.
- **J06.4** Not established: the paper reports no jailbreak success rate for production chatbots (its observations concern GPT-3.5); any success-rate figure for the bank's chatbot is fabricated.

### Answer A

**F0** Subtoxic questions are inherently harmless queries that LLMs mistakenly identify as harmful because of their composition. They typically embed harmful content within a benign question while preserving its essential meaning.
  - > `2404.08309v1_c0003` These are queries that, although inherently harmless, are mistakenly identified as harmful by LLMs due to their content composition. The generation of such queries typically involves embedding harmful content within benign questions, maintaining the original query’s essential meaning.
**F1** The paper reports that subtoxic questions are easier to jailbreak and respond to milder jailbreak prompts than truly toxic questions.
  - > `2404.08309v1_c0003` Our research indicates that subtoxic questions are more susceptible to jailbreaking interventions and respond more effectively to milder jailbreak prompts compared to truly toxic questions.
**F2** In the Gradual Attitude Change observations, incrementally adding positive prompts to subtoxic questions accompanied a progression from firm refusal through partial answers and warning-laden answers to positive, effective replies.
  - > `2404.08309v1_c0005` In order to further explore Property 2, we replace real toxic questions with subtoxic ones to investigate the effects of incrementally adding positive prompts on jailbreaking. We observe a gradual shift in the LLM’s response as the number of positive prompts increases. They transit by stages, from ”firm and short refusal” to ”refusal with answers to safe inquiries”, to ”answering the toxic question with numerous security warnings”, then to ”with fewer warnings”, and finally to ”positive and effective reply”.
**F3** The illustrated GPT-3.5 experiment tested each combination five times. GAC-1 describes more and stronger positive prompts, together with fewer and weaker negative prompts, as tending to elicit more positive responses.
  - > `2404.08309v1_c0007` Attitude distribution of the response of GPT-3.5 to subtoxic questions as the content and number of positive prompts padded to the subtoxic question demonstrated in Fig. 1 differs. (Each combination was tested five times.)
  - > `2404.08309v1_c0007` Corollary 1 aligns with the practical observation that more and stronger positive prompts, alongside fewer and weaker negative prompts, tend to elicit a more positive LLM response, as illustrated in Fig. 2.
  - > `2404.08309v1_c0007` GAC-1 elaborates on Property 2, applying it within the GAC model’s framework.
**F4** GAC measures response willingness continuously, assigning the strongest refusal −1 and the most positive, effective reply 1. It prioritizes relative response ordering over exact scores.
  - > `2404.08309v1_c0005` For the most “firm and short refusal” ( o_{-} ), let A(o_{-})=-1 . For the most “positive and effective reply” ( o_{+} ), let A(o_{+})=1 . For all outputs o , ensure -1\leq A(o)\leq 1 . If A(o_{1})<A(o_{2}) , then o_{2} demonstrates a greater response willingness than o_{1} . The GAC model emphasizes the relative ordering of responses over their exact scores.
  - > `2404.08309v1_c0005` In contrast, we introduce a continuous measure of response attitude—the GAC model—assessing texts based on their GAC performance.
**F5** GAC-2 proposes that two prompts retain their relative effectiveness on almost all questions, supporting a relative strength ranking rather than an absolute numerical score.
  - > `2404.08309v1_c0009` GAC-2 states that the relative effectiveness of two prompts x_{1},x_{2} remains consistent on almost all questions.
  - > `2404.08309v1_c0009` We emphasize that t(x) signifies a “rank” or relative strength of a prompt among all prompts, rather than a numeric value. A higher rank implies a greater positive influence on LLM’s responses.
**F6** To rank a new prompt, the paper proposes repeated comparisons against an existing hierarchy of standard prompts across the Evaluation Question Set, using G comparisons and the ratio of question partitions to place it between reference prompts.
  - > `2404.08309v1_c0010` In order to accurately assess the rank of a prompt x^{\prime} with respect to T , we give an existing hierarchy of standard prompts t(x_{1})<t(x_{2})<\dots<t(x_{n}) .Through multiple samplings, we compare x^{\prime} against each x_{i} by evaluating and contrasting G(x^{\prime}\|S\|q) with G(x_{i}\|S\|q) for all q in EQS. This allows us to estimate \frac{|Q_{+}(x_{i},x^{\prime})|}{|Q_{-}(x_{i},x^{\prime})|} and subsequently determine t(x_{k})<t(x^{\prime})<t(x_{k+1}) , pinpointing x^{\prime} ’s relative rank within T .
**I0** For the bank’s red team, this supports using subtoxic questions to compare incremental changes in attack strength; estimating production jailbreak success additionally requires evaluating the bank’s own model, prompts, decoding strategy and safety judgment.
  - > `2404.08309v1_c0003` Therefore, subtoxic questions serve as a valuable resource for conducting jailbreaking experiments on black-box LLM systems, providing insights into a wider spectrum of experimental phenomena.
  - > `2506.17299v2_c0002` Formally, we define the jailbreak oracle problem as follows: for a given language model \mathcal{M} , prompt p , and decoding strategy \mathcal{D} , will this combination produce a jailbreak response (according to some safety judge \mathcal{J} ) with at least some likelihood \tau ?
  - > `2404.08309v1_c0005` We observe a gradual shift in the LLM’s response as the number of positive prompts increases.
**L0** Prompt rank represents relative strength rather than a numerical jailbreak success rate.
  - > `2404.08309v1_c0009` We emphasize that t(x) signifies a “rank” or relative strength of a prompt among all prompts, rather than a numeric value.
**L1** The proposed ordering has exceptions: prompt effectiveness can differ significantly across questions.
  - > `2404.08309v1_c0009` It’s important to note that while \epsilon is a small constant, empirical evidence from the Reuse Attack —using theme-related introductory content generated by the LLM as an effective jailbreaking prompt—suggests \epsilon is not 0 . The effectiveness of a prompt differs significantly on different questions.
**L2** Developing a standardized evaluation question set remains future work.
  - > `2404.08309v1_c0010` Our future directions will include developing a standardized question set to harmonize evaluation criteria across different studies.
**L3** Applying these findings to the bank requires evaluation under its model, prompts, decoding strategy, and safety judgment.
  - > `2506.17299v2_c0002` Formally, we define the jailbreak oracle problem as follows: for a given language model \mathcal{M} , prompt p , and decoding strategy \mathcal{D} , will this combination produce a jailbreak response (according to some safety judge \mathcal{J} ) with at least some likelihood \tau ?

### Answer B

**F0** Subtoxic questions are inherently harmless queries that LLMs mistakenly flag as harmful because of their composition, typically created by embedding harmful content within a benign question while preserving its essential meaning.
  - > `2404.08309v1_c0003` These are queries that, although inherently harmless, are mistakenly identified as harmful by LLMs due to their content composition. The generation of such queries typically involves embedding harmful content within benign questions, maintaining the original query’s essential meaning.
**F1** The paper reports that subtoxic questions were more susceptible to jailbreaking interventions and responded to milder jailbreak prompts more effectively than truly toxic questions.
  - > `2404.08309v1_c0003` Our research indicates that subtoxic questions are more susceptible to jailbreaking interventions and respond more effectively to milder jailbreak prompts compared to truly toxic questions.
**F2** When the researchers substituted subtoxic questions for toxic ones and incrementally added positive prompts, they observed responses progressing from firm refusal through partial answers and warning-laden answers to positive, effective replies; they called this Gradual Attitude Change (GAC).
  - > `2404.08309v1_c0005` In order to further explore Property 2, we replace real toxic questions with subtoxic ones to investigate the effects of incrementally adding positive prompts on jailbreaking. We observe a gradual shift in the LLM’s response as the number of positive prompts increases. They transit by stages, from ”firm and short refusal” to ”refusal with answers to safe inquiries”, to ”answering the toxic question with numerous security warnings”, then to ”with fewer warnings”, and finally to ”positive and effective reply”. We term this progressive response shift as Gradual Attitude Change (GAC).
**F3** The illustrated GPT-3.5 subtoxic-question experiment tested each prompt combination five times.
  - > `2404.08309v1_c0007` Attitude distribution of the response of GPT-3.5 to subtoxic questions as the content and number of positive prompts padded to the subtoxic question demonstrated in Fig. 1 differs. (Each combination was tested five times.)
**F4** GAC-1 describes a tendency for more and stronger positive prompts, together with fewer and weaker negative prompts, to elicit more positive responses.
  - > `2404.08309v1_c0007` Corollary 1 aligns with the practical observation that more and stronger positive prompts, alongside fewer and weaker negative prompts, tend to elicit a more positive LLM response, as illustrated in Fig. 2.
  - > `2404.08309v1_c0007` GAC-1 elaborates on Property 2, applying it within the GAC model’s framework.
**F5** The researchers also observed that appending a negative prompt to an otherwise effective jailbreak prompt resulted in refusal.
  - > `2404.08309v1_c0007` Corollary 2 reflects the scenario of subtoxic questions at n=1 and is confirmed by observing that appending a negative prompt to an otherwise effective jailbreak prompt results in LLM refusal.
**F6** GAC-2 proposes that two prompts retain their relative effectiveness across almost all questions, enabling a relative strength ranking rather than an absolute numerical strength score.
  - > `2404.08309v1_c0009` GAC-2 states that the relative effectiveness of two prompts x_{1},x_{2} remains consistent on almost all questions.
  - > `2404.08309v1_c0009` We emphasize that t(x) signifies a “rank” or relative strength of a prompt among all prompts, rather than a numeric value. A higher rank implies a greater positive influence on LLM’s responses.
**F7** To rank a candidate prompt, the paper proposes repeated sampling across the Evaluation Question Set (EQS), comparing its G scores against an ordered hierarchy of standard prompts and using the ratio of question sets Q+ and Q− to locate its relative position.
  - > `2404.08309v1_c0002` construction of a framework for a type of Evaluation Question Set (EQS) based on subtoxic questions, and establish its evaluative metrics.
  - > `2404.08309v1_c0010` In order to accurately assess the rank of a prompt x^{\prime} with respect to T , we give an existing hierarchy of standard prompts t(x_{1})<t(x_{2})<\dots<t(x_{n}) .Through multiple samplings, we compare x^{\prime} against each x_{i} by evaluating and contrasting G(x^{\prime}\|S\|q) with G(x_{i}\|S\|q) for all q in EQS. This allows us to estimate \frac{|Q_{+}(x_{i},x^{\prime})|}{|Q_{-}(x_{i},x^{\prime})|} and subsequently determine t(x_{k})<t(x^{\prime})<t(x_{k+1}) , pinpointing x^{\prime} ’s relative rank within T .
**F8** The paper defines G as the expected response-attitude score and reports typically low attitude-score variance for most inputs, allowing that expectation to converge quickly.
  - > `2404.08309v1_c0010` Empirical results indicate that the variance \mathrm{Var}[A(o)] for most inputs i is typically low, enabling G(i)=\mathrm{E}[A(o)] to converge quickly, and making the comparison result between G(i) and G(i^{\prime}) reliable.
  - > `2404.08309v1_c0005` In contrast, we introduce a continuous measure of response attitude—the GAC model—assessing texts based on their GAC performance. We define the performance under GAC metric for a given output o\sim D(i) as A(o) , establishing the following parameters:
**I0** For the bank's red team, this supports using subtoxic questions and graded response attitudes to compare candidate prompts; estimating production jailbreak success would require separate testing of the bank's chatbot under specified prompts, decoding conditions and safety judgments.
  - > `2404.08309v1_c0003` Our research indicates that subtoxic questions are more susceptible to jailbreaking interventions and respond more effectively to milder jailbreak prompts compared to truly toxic questions.
  - > `2404.08309v1_c0005` The GAC model emphasizes the relative ordering of responses over their exact scores.
  - > `2506.17299v2_c0002` Formally, we define the jailbreak oracle problem as follows: for a given language model \mathcal{M} , prompt p , and decoding strategy \mathcal{D} , will this combination produce a jailbreak response (according to some safety judge \mathcal{J} ) with at least some likelihood \tau ?
  - > `2404.08309v1_c0009` GAC-2 offers a refined approach to evaluating prompts, facilitating comparisons among them based on their effectiveness.
**L0** The illustrated GPT-3.5 experiment tested each combination five times. Its response attitudes and relative prompt ranks do not establish an expected production jailbreak success rate for the bank; transfer requires evaluation under the bank's model and testing conditions.
  - > `2404.08309v1_c0007` Attitude distribution of the response of GPT-3.5 to subtoxic questions as the content and number of positive prompts padded to the subtoxic question demonstrated in Fig. 1 differs. (Each combination was tested five times.)
  - > `2404.08309v1_c0009` We emphasize that t(x) signifies a “rank” or relative strength of a prompt among all prompts, rather than a numeric value.
  - > `2506.17299v2_c0002` Formally, we define the jailbreak oracle problem as follows: for a given language model \mathcal{M} , prompt p , and decoding strategy \mathcal{D} , will this combination produce a jailbreak response (according to some safety judge \mathcal{J} ) with at least some likelihood \tau ?
**L1** The proposed ranking has question-dependent exceptions, and developing a standardized question set remains future work.
  - > `2404.08309v1_c0009` It’s important to note that while \epsilon is a small constant, empirical evidence from the Reuse Attack —using theme-related introductory content generated by the LLM as an effective jailbreaking prompt—suggests \epsilon is not 0 . The effectiveness of a prompt differs significantly on different questions.
  - > `2404.08309v1_c0010` Our future directions will include developing a standardized question set to harmonize evaluation criteria across different studies.

### Answer C

**F0** Subtoxic questions are inherently harmless queries that LLMs mistakenly classify as harmful because of their composition, typically embedding harmful content inside a benign question while preserving its essential meaning.
  - > `2404.08309v1_c0003` These are queries that, although inherently harmless, are mistakenly identified as harmful by LLMs due to their content composition. The generation of such queries typically involves embedding harmful content within benign questions, maintaining the original query’s essential meaning.
**F1** The paper reports that subtoxic questions are easier to jailbreak and respond to milder jailbreak prompts than genuinely toxic questions.
  - > `2404.08309v1_c0003` Our research indicates that subtoxic questions are more susceptible to jailbreaking interventions and respond more effectively to milder jailbreak prompts compared to truly toxic questions.
**F2** In the Gradual Attitude Change observations, incrementally adding positive prompts to subtoxic questions produced staged shifts from firm refusal through partial answers and warning-laden answers to a positive, effective reply.
  - > `2404.08309v1_c0005` In order to further explore Property 2, we replace real toxic questions with subtoxic ones to investigate the effects of incrementally adding positive prompts on jailbreaking. We observe a gradual shift in the LLM’s response as the number of positive prompts increases. They transit by stages, from ”firm and short refusal” to ”refusal with answers to safe inquiries”, to ”answering the toxic question with numerous security warnings”, then to ”with fewer warnings”, and finally to ”positive and effective reply”. We term this progressive response shift as Gradual Attitude Change (GAC).
**F3** GAC-1 characterizes prompts as positive or negative according to whether they increase or decrease expected response attitude; more and stronger positive prompts, with fewer and weaker negative prompts, tended to elicit more positive responses. The illustrated GPT-3.5 subtoxic-question experiment tested each combination five times.
  - > `2404.08309v1_c0007` GAC-1 establishes a qualitative metric for evaluating prompts x : for a given question q , prompts that increase G when appended are positive for q , while those decrease G are negative.
  - > `2404.08309v1_c0007` Corollary 1 aligns with the practical observation that more and stronger positive prompts, alongside fewer and weaker negative prompts, tend to elicit a more positive LLM response, as illustrated in Fig. 2.
  - > `2404.08309v1_c0007` Attitude distribution of the response of GPT-3.5 to subtoxic questions as the content and number of positive prompts padded to the subtoxic question demonstrated in Fig. 1 differs. (Each combination was tested five times.)
  - > `2404.08309v1_c0006` Define G(i) as the expected attitude under the GAC metric for user input i
**F4** GAC-2 proposes that two prompts retain their relative effectiveness on almost all questions, enabling a relative strength ranking rather than an absolute numerical strength score.
  - > `2404.08309v1_c0009` GAC-2 states that the relative effectiveness of two prompts x_{1},x_{2} remains consistent on almost all questions.
  - > `2404.08309v1_c0009` We emphasize that t(x) signifies a “rank” or relative strength of a prompt among all prompts, rather than a numeric value. A higher rank implies a greater positive influence on LLM’s responses.
**F5** To rank a candidate, the paper proposes repeated sampling across an Evaluation Question Set, comparing its expected response attitude with an existing hierarchy of standard prompts and placing it between neighboring standards.
  - > `2404.08309v1_c0002` construction of a framework for a type of Evaluation Question Set (EQS) based on subtoxic questions, and establish its evaluative metrics.
  - > `2404.08309v1_c0006` Define G(i) as the expected attitude under the GAC metric for user input i
  - > `2404.08309v1_c0010` In order to accurately assess the rank of a prompt x^{\prime} with respect to T , we give an existing hierarchy of standard prompts t(x_{1})<t(x_{2})<\dots<t(x_{n}) .Through multiple samplings, we compare x^{\prime} against each x_{i} by evaluating and contrasting G(x^{\prime}\|S\|q) with G(x_{i}\|S\|q) for all q in EQS. This allows us to estimate \frac{|Q_{+}(x_{i},x^{\prime})|}{|Q_{-}(x_{i},x^{\prime})|} and subsequently determine t(x_{k})<t(x^{\prime})<t(x_{k+1}) , pinpointing x^{\prime} ’s relative rank within T .
**L0** The proposed output is a relative prompt-strength rank, rather than a numerical jailbreak success rate.
  - > `2404.08309v1_c0009` We emphasize that t(x) signifies a “rank” or relative strength of a prompt among all prompts, rather than a numeric value.
**L1** Prompt effectiveness has question-dependent exceptions, and subtoxic questions are more susceptible to jailbreaking than truly toxic questions; their results should not be assumed equivalent.
  - > `2404.08309v1_c0009` The effectiveness of a prompt differs significantly on different questions.
  - > `2404.08309v1_c0003` Our research indicates that subtoxic questions are more susceptible to jailbreaking interventions and respond more effectively to milder jailbreak prompts compared to truly toxic questions.

### Answer D


---

## J07

A client wants to deploy an LLM on resource-constrained hardware. What compression approaches does the survey cover, what makes compressing large language models different, how does it separate medium and large models, and how much will compression cut the client's inference cost?

- **J07.1** Taxonomy: quantization, pruning, distillation, compact architecture design and dynamic networks.
- **J07.2** Two LLM-specific characteristics: fine-tuning or retraining is very costly, so tuning-free algorithms are explored; and LLMs emphasise versatility, so distillation focuses on preserving it.
- **J07.3** Medium models are around one billion parameters or fewer (e.g. BERT, GPT-2); large models have over one billion.
- **J07.4** Example of the cost problem: a 10B model with float32 weights consumes 37GB of memory.
- **J07.5** Weight-only quantization cannot be integer-only: weights must be dequantized before multiplying with activations, adding computation overhead.
- **J07.6** Not established: the survey reports no measured inference-cost saving for the client's deployment; any such figure is fabricated.

### Answer A

**F0** Quantization reduces the precision of weights or activations, lowering memory requirements and potentially increasing inference speed.
  - > `2402.09748v1_c0001` Quantization transforms float32 weights or activations into lower-bit float or integer numbers. Less bits means less memory requirement. Further, less bits may indicate higher parallelism and faster inference speed.
**F1** Pruning removes components such as neurons or layers to reduce inference memory and computation.
  - > `2402.09748v1_c0002` Pruning devotes to removing unimportant components ( e.g. , neurons, layers, etc ) in a pre-designed model, thus reducing the memory and computational cost in the inference cost.
**F2** Knowledge distillation transfers knowledge from a pretrained large teacher to a smaller student intended to retain similar abilities with lower memory and computational costs.
  - > `2402.09748v1_c0002` Knowledge distillation introduces a pretrained large model as a teacher and transfers its knowledge to a new smaller model which is called a student model. Then, the smaller model will share nearly the same ability as the teacher and enjoy less memory and computational cost.
**F3** Compact architecture design replaces expensive operators with cheaper alternatives; the survey particularly targets Transformer self-attention.
  - > `2402.09748v1_c0002` Compact architecture design designs new operators with less cost to replace (often approximate) the cumbersome operators in the original model. For the Transformer models, self-attentions are the main targets and are often replaced with other operators.
**F4** Dynamic networks activate only part of a network for each input. The survey covers early exit, cascade inference and mixture of experts (MoE).
  - > `2402.09748v1_c0119` dynamic neural networks (DyNNs) engage only a subset of the network for processing each input, making the entire model more flexible and efficient in meeting computational demands under resource-constrained environments.
  - > `2402.09748v1_c0119` In the field of NLP and the domain of LLMs, current research on DyNNs primarily encompassess the following three methodologies: early exit, cascade inference and mixture of experts (MoE) .
**F5** LLM compression differs because post-compression finetuning or retraining is especially costly, motivating tuning-free quantization and pruning.
  - > `2402.09748v1_c0000` Most of compression algorithms require finetuning or even retraining the model after compression. The most notable aspect of large models is the very high cost associated with model finetuning or training. Therefore, many algorithms for large models, such as quantization and pruning, start to explore tuning-free algorithms.
**F6** LLM compression must preserve versatility and generalization across tasks and unseen data, including emergent abilities, requiring more careful validation than single-task performance alone.
  - > `2402.09748v1_c0002` Instead of handling one single task such as neural machine translation, large language models emphsize versatility and generalization across various tasks and unseen data, or even emergent abilities. Thus, large language models after compression require more careful validation of their versatility and generalization
**F7** The survey calls models with around one billion or fewer parameters “medium,” including BERT and GPT-2; models with over one billion parameters are “large,” including LLaMA, Claude and ChatGPT. Its rationale is that medium models are relatively easier to finetune and demonstrate fewer emergent abilities.
  - > `2402.09748v1_c0003` we further isolate language models around one billion or less parameters, such as BERT, GPT-2, and call them medium models, though they are usually taken as large language models. And Models with over one billion parameters, such as LLaMA, Claude, ChatGPT, and etc , keep the name of large language models. The reasons is that medium models are less affected by the above two challenges, i.e. , medium models are relatively easy to finetune, demonstrate fewer emergent abilities.
**F8** For quantization, the survey reports that changing LLM weights from 32-bit float to 4-bit integer could reduce model size to approximately 1/8. This is a model-size result.
  - > `2402.09748v1_c0008` quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
**F9** Weight-only quantization generally stores weights at low precision but dequantizes them before computation: it can reduce model size and weight-transfer time without gaining hardware-supported low-bit computation acceleration.
  - > `2402.09748v1_c0022` Generally, weight-only quantization belongs to simulated quantization methods; the weights are only stored in low-bit datatype and need to be dequantized before real computation. This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.
**I0** For a client deploying on constrained hardware, this supports evaluating compression on the intended hardware and validating retained capabilities before choosing an approach.
  - > `2402.09748v1_c0008` It is the most straightforward method to cut down memory cost and improve inference speed for LLMs, especially on hardware with support for fast operation of low-bit datatypes ( e.g. , INT4).
  - > `2402.09748v1_c0002` Thus, large language models after compression require more careful validation of their versatility and generalization
**L0** The approximately 1/8 example concerns model size after quantizing weights from 32-bit float to 4-bit integer, rather than a quantified inference-cost reduction.
  - > `2402.09748v1_c0008` quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
**L1** Weight-only quantization generally requires dequantization before computation; its size and weight-transfer benefits do not provide hardware-supported low-bit operation acceleration.
  - > `2402.09748v1_c0022` Generally, weight-only quantization belongs to simulated quantization methods; the weights are only stored in low-bit datatype and need to be dequantized before real computation. This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.
**L2** Compressed LLMs require careful validation of versatility and generalization.
  - > `2402.09748v1_c0002` Thus, large language models after compression require more careful validation of their versatility and generalization

### Answer B

**L0** The supplied passages do not quantify how much compression would cut this client's inference cost. They report a model-size proxy—quantizing weights from 32-bit float to 4-bit integer can reduce model size to approximately one eighth—and qualify speed benefits by hardware support. A client-specific cost estimate requires measurements for the chosen model, compression method, workload and target hardware.
  - > `2402.09748v1_c0008` 1) High compression ratio : quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
  - > `2402.09748v1_c0008` It is the most straightforward method to cut down memory cost and improve inference speed for LLMs, especially on hardware with support for fast operation of low-bit datatypes ( e.g. , INT4).
**L1** The supplied passages support the qualitative parts of the question: the compression taxonomy and the challenges of expensive fine-tuning and preserving generalization. However, their numerical separation of medium and large models is only explicit in the pruning discussion, which describes medium models as having fewer than 1 billion parameters; they do not establish a universal parameter threshold for “real” large models.
  - > `2402.09748v1_c0000` Regarding taxonomy, similar to smaller models, compression and acceleration algorithms for large language models can still be categorized into quantization, pruning, distillation, compact architecture design, dynamic networks.
  - > `2402.09748v1_c0000` The most notable aspect of large models is the very high cost associated with model finetuning or training.
  - > `2402.09748v1_c0000` Large models emphasize versatility and generalization rather than performance on a single task.
  - > `2402.09748v1_c0000` Since these two characteristics were not very pronounced in early large models, we further distinguish large language models into medium models and “real” large models.

### Answer C

**F0** The survey covers quantization: reducing the precision of weights or activations to reduce memory requirements, with potential inference speed benefits.
  - > `2402.09748v1_c0001` Quantization transforms float32 weights or activations into lower-bit float or integer numbers. Less bits means less memory requirement. Further, less bits may indicate higher parallelism and faster inference speed.
**F1** It covers pruning: removing components such as neurons or layers to reduce inference memory and computation.
  - > `2402.09748v1_c0002` Pruning devotes to removing unimportant components ( e.g. , neurons, layers, etc ) in a pre-designed model, thus reducing the memory and computational cost in the inference cost.
**F2** It covers knowledge distillation: transferring knowledge from a pretrained large teacher to a smaller student intended to retain nearly the same ability with less memory and computation.
  - > `2402.09748v1_c0002` Knowledge distillation introduces a pretrained large model as a teacher and transfers its knowledge to a new smaller model which is called a student model. Then, the smaller model will share nearly the same ability as the teacher and enjoy less memory and computational cost.
**F3** It covers compact architecture design: replacing expensive operators with cheaper alternatives, particularly replacing self-attention in Transformers.
  - > `2402.09748v1_c0002` Compact architecture design designs new operators with less cost to replace (often approximate) the cumbersome operators in the original model. For the Transformer models, self-attentions are the main targets and are often replaced with other operators.
**F4** It covers dynamic networks, which activate only part of a network for each input; the surveyed approaches include early exit, cascade inference and mixture of experts.
  - > `2402.09748v1_c0119` dynamic neural networks (DyNNs) engage only a subset of the network for processing each input, making the entire model more flexible and efficient in meeting computational demands under resource-constrained environments.
  - > `2402.09748v1_c0119` In the field of NLP and the domain of LLMs, current research on DyNNs primarily encompassess the following three methodologies: early exit, cascade inference and mixture of experts (MoE) .
**F5** Compressing large models differs because post-compression finetuning or retraining is very expensive, motivating tuning-free quantization and pruning algorithms.
  - > `2402.09748v1_c0000` Most of compression algorithms require finetuning or even retraining the model after compression. The most notable aspect of large models is the very high cost associated with model finetuning or training. Therefore, many algorithms for large models, such as quantization and pruning, start to explore tuning-free algorithms.
**F6** Large-model compression must also preserve and carefully validate versatility, generalization across tasks and unseen data, and emergent abilities, rather than evaluate only a single task.
  - > `2402.09748v1_c0002` Instead of handling one single task such as neural machine translation, large language models emphsize versatility and generalization across various tasks and unseen data, or even emergent abilities. Thus, large language models after compression require more careful validation of their versatility and generalization
**F7** The survey calls models with around one billion or fewer parameters, such as BERT and GPT-2, “medium”; models with over one billion parameters retain the “large” label. It explains that medium models are relatively easier to finetune and demonstrate fewer emergent abilities.
  - > `2402.09748v1_c0003` To better present these methods, we further isolate language models around one billion or less parameters, such as BERT, GPT-2, and call them medium models, though they are usually taken as large language models. And Models with over one billion parameters, such as LLaMA, Claude, ChatGPT, and etc , keep the name of large language models. The reasons is that medium models are less affected by the above two challenges, i.e. , medium models are relatively easy to finetune, demonstrate fewer emergent abilities.
**F8** The survey gives a model-size example: quantizing LLM weights from 32-bit float to 4-bit integer could compress model size to approximately 1/8.
  - > `2402.09748v1_c0008` High compression ratio : quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
**F9** For weight-only simulated quantization, the survey reports smaller models and less time moving weights between memories, but weights must be dequantized before computation and do not benefit from hardware-supported low-bit operations.
  - > `2402.09748v1_c0022` Generally, weight-only quantization belongs to simulated quantization methods; the weights are only stored in low-bit datatype and need to be dequantized before real computation. This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.
**I0** For a client choosing compression for constrained hardware, this supports benchmarking the selected method on the target hardware before estimating inference savings: storage reduction and execution acceleration are distinct outcomes.
  - > `2402.09748v1_c0008` It is the most straightforward method to cut down memory cost and improve inference speed for LLMs, especially on hardware with support for fast operation of low-bit datatypes ( e.g. , INT4).
  - > `2402.09748v1_c0022` This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.
**L0** The approximately 1/8 example concerns model size when weights change from 32-bit float to 4-bit integer; it does not quantify inference cost savings.
  - > `2402.09748v1_c0008` High compression ratio : quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
**L1** Weight-only simulated quantization requires dequantization before computation; smaller storage and faster weight transfers do not imply access to hardware-accelerated low-bit operations.
  - > `2402.09748v1_c0022` Generally, weight-only quantization belongs to simulated quantization methods; the weights are only stored in low-bit datatype and need to be dequantized before real computation. This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.

### Answer D

**F0** Quantization reduces the precision of weights or activations to lower-bit floating-point or integer representations, reducing memory requirements.
  - > `2402.09748v1_c0001` Quantization transforms float32 weights or activations into lower-bit float or integer numbers. Less bits means less memory requirement.
**F1** Pruning removes unimportant components, such as neurons or layers, to reduce inference memory and computation.
  - > `2402.09748v1_c0002` Pruning devotes to removing unimportant components ( e.g. , neurons, layers, etc ) in a pre-designed model, thus reducing the memory and computational cost in the inference cost.
**F2** Knowledge distillation transfers knowledge from a pretrained large teacher model to a smaller student model.
  - > `2402.09748v1_c0002` Knowledge distillation introduces a pretrained large model as a teacher and transfers its knowledge to a new smaller model which is called a student model.
**F3** Compact architecture design replaces expensive operators with cheaper alternatives; self-attention is a main target in Transformers.
  - > `2402.09748v1_c0002` Compact architecture design designs new operators with less cost to replace (often approximate) the cumbersome operators in the original model. For the Transformer models, self-attentions are the main targets and are often replaced with other operators.
**F4** Dynamic networks activate only a subset of the network for each input; the survey covers early exit, cascade inference and mixture of experts (MoE).
  - > `2402.09748v1_c0119` To address these issues while still harnessing the benefits of scaling, dynamic neural networks (DyNNs) engage only a subset of the network for processing each input, making the entire model more flexible and efficient in meeting computational demands under resource-constrained environments. In the field of NLP and the domain of LLMs, current research on DyNNs primarily encompassess the following three methodologies: early exit, cascade inference and mixture of experts (MoE) .
**F5** Compressing large models differs because post-compression finetuning or retraining is very expensive, motivating tuning-free quantization and pruning.
  - > `2402.09748v1_c0000` Most of compression algorithms require finetuning or even retraining the model after compression. The most notable aspect of large models is the very high cost associated with model finetuning or training. Therefore, many algorithms for large models, such as quantization and pruning, start to explore tuning-free algorithms.
**F6** Compressed LLMs require careful validation of versatility, generalization across tasks and unseen data, and emergent abilities, rather than evaluation on a single task alone.
  - > `2402.09748v1_c0002` Instead of handling one single task such as neural machine translation, large language models emphsize versatility and generalization across various tasks and unseen data, or even emergent abilities. Thus, large language models after compression require more careful validation of their versatility and generalization
**F7** LLM quantization also faces distinctive activation patterns, including systematic outliers that hinder direct reuse of methods for medium-sized models.
  - > `2402.09748v1_c0022` The activation patterns of LLMs are distinct, which poses a challenge when applying quantization methods that work well for medium-sized language models. Systematic outliers [ 43 ] are one such unique property of LLM activations that hinder the direct application of such methods for weight-only quantization of LLMs
**F8** The survey calls models with around one billion or less parameters “medium models,” giving BERT and GPT-2 as examples; these are relatively easier to finetune and exhibit fewer emergent abilities.
  - > `2402.09748v1_c0003` To better present these methods, we further isolate language models around one billion or less parameters, such as BERT, GPT-2, and call them medium models, though they are usually taken as large language models.
  - > `2402.09748v1_c0003` The reasons is that medium models are less affected by the above two challenges, i.e. , medium models are relatively easy to finetune, demonstrate fewer emergent abilities.
**F9** The survey retains the name “large language models” for models with over one billion parameters, listing LLaMA, Claude and ChatGPT as examples.
  - > `2402.09748v1_c0003` And Models with over one billion parameters, such as LLaMA, Claude, ChatGPT, and etc , keep the name of large language models.
**F10** For LLM quantization, the survey separates post-training quantization (PTQ), which requires no retraining, from quantization-aware training (QAT), which requires retraining.
  - > `2402.09748v1_c0009` Methods without re-training ( i.e. , post-training quantization, PTQ ) are discussed in Section III-C while methods that demand re-training ( i.e. , quantization-aware training, QAT ) is discussed in Section III-D .
**F11** The survey says quantizing LLM weights from 32-bit float to 4-bit integer could reduce model size to approximately 1/8.
  - > `2402.09748v1_c0008` 1) High compression ratio : quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
**F12** Weight-only quantization generally reduces model size and weight-transfer time, but requires dequantization before computation and does not obtain hardware-supported low-bit arithmetic acceleration.
  - > `2402.09748v1_c0022` Generally, weight-only quantization belongs to simulated quantization methods; the weights are only stored in low-bit datatype and need to be dequantized before real computation. This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.
**I0** For a client deploying on constrained hardware, this supports testing quantization on the intended device and measuring inference performance before estimating financial savings.
  - > `2402.09748v1_c0008` It is the most straightforward method to cut down memory cost and improve inference speed for LLMs, especially on hardware with support for fast operation of low-bit datatypes ( e.g. , INT4).
  - > `2402.09748v1_c0022` This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.
**L0** The approximately 1/8 example concerns model size after converting 32-bit float weights to 4-bit integers; it does not quantify the client's monetary inference savings.
  - > `2402.09748v1_c0008` 1) High compression ratio : quantizing the weights in LLMs from 32-bit float to 4-bit integer could drastically compress the model size to approximately 1/8
**L1** Inference benefits depend on hardware support and the quantization method. The proposed device testing is conditional validation advice, not evidence of measured savings for this client.
  - > `2402.09748v1_c0008` It is the most straightforward method to cut down memory cost and improve inference speed for LLMs, especially on hardware with support for fast operation of low-bit datatypes ( e.g. , INT4).
  - > `2402.09748v1_c0022` This means such methods can decrease the overall size of LLMs and decrease the time to move weights between memories but cannot enjoy the accelerated low-bit operation supported by specific hardware.

---

## J08

An R&D client wants to know where retrieval augmentation adds value in chemistry machine learning. What do the catalyst-discovery study and MARASON retrieve, how is the retrieved material used, and what evidence shows when retrieval helps?

- **J08.1** The catalyst study retrieves k=20 relevant catalysts from its materials databases (Materials Project, NOMAD, OC20) to ground GPT-4 generation.
- **J08.2** In the catalyst study's ablation, thermodynamic stability dropped to 23% without retrieval versus 82% with it (a 3.6x improvement).
- **J08.3** MARASON retrieves one reference structure and up to three reference spectra with collision energies, which are fed into the model.
- **J08.4** MARASON's retrieval brings a significant gain only for similar-enough references (Tanimoto > 0.3); the authors suggest using the non-RAG version when the retrieved structure's similarity is 0.2 or below. Stating "non-RAG below 0.3" scores at most 0.5.

### Answer A

**F0** The catalyst-discovery framework gives GPT-4 access to a database of 50,000+ known materials to guide exploration of catalyst compositions under physical and practical constraints. Retrieval supplies grounding for candidate design, while the LLM also assists with interpreting results and generating hypotheses.
  - > `2603.15712v1_c0000` We introduce a retrieval-augmented generation framework that enables GPT-4 to navigate chemical space by accessing a database of 50,000+ known materials, adapting general-purpose language understanding for high-throughput materials design.
  - > `2603.15712v1_c0000` By demonstrating that retrieval-augmented generation can ground AI creativity in physical constraints without sacrificing exploration, this work demonstrates an approach where natural language interfaces can streamline materials discovery workflows, enabling researchers to explore chemical spaces more efficiently while the LLM assists in result interpretation and hypothesis generation.
**F1** The catalyst study reports over 250 generated candidates, an 82% thermodynamic stability rate, and 68% satisfying the combined cost, conductivity and mechanical-stability constraints. It also reports 78% clustering near the theoretical activity optimum and 200× computational efficiency relative to traditional high-throughput screening; these are results for the complete retrieval-augmented workflow.
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
  - > `2603.15712v1_c0000` Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening.
**F2** MARASON retrieves a structurally similar molecule and its measured spectra from annotated structure–spectrum pairs, using the training dataset in the experiments to mitigate leakage concerns. It selects the closest molecule by Morgan-fingerprint Tanimoto similarity, excludes incompatible adduct or instrument types, and supplies up to three spectra with collision energies closest to the query condition.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) .
  - > `2502.17874v2_c0014` We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F3** MARASON annotates retrieved spectral peaks with predicted fragments and learns spectrum embeddings across nearby collision energies; neural graph matching models structural affinities to enhance its fragmentation-based spectrum simulator. It reports 28% top-1 accuracy versus 19% for the non-retrieval state of the art, and outperforms naive retrieval augmentation and traditional graph matching. The architecture matters: simple concatenation of reference information reportedly produces minimal or no improvement.
  - > `2502.17874v2_c0015` As the collision energy value is continuous, our aim of including three reference energies is to learn an appropriate spectrum embedding for the target collision energy value by interpolating from three closest energies. Reference spectra only provide m/z values and peak intensities. This information is enriched by annotating peaks with ICEBERG-predicted fragments of the reference structure.
  - > `2502.17874v2_c0000` Neural graph matching offers a compelling solution by explicitly modeling node and edge affinities between two structural graphs while employing a noise-robust, end-to-end neural network to learn affinity metrics. We apply this approach to mass spectrum simulation and introduce MARASON, a novel model that incorporates neural graph matching to enhance a fragmentation-based neural network.
  - > `2502.17874v2_c0000` Experimental results highlight the effectiveness of our design, with MARASON achieving 28% top-1 accuracy, a substantial improvement over the non-retrieval state-of-the-art accuracy of 19%. Moreover, MARASON outperforms both naive retrieval-augmented generation methods and traditional graph matching approaches.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ).
**I0** For an R&D client, these studies suggest two uses: grounding exploratory materials design in known materials, and improving molecular predictions by transferring information from relevant experimental analogues. MARASON provides the clearer comparative evidence that retrieval helps when the model explicitly handles differences between reference and query structures; merely adding retrieved information is not reliably sufficient.
  - > `2603.15712v1_c0000` This paper demonstrates how large language models can assist the catalyst discovery process by helping researchers explore chemical spaces and interpret results when augmented with retrieval-based grounding.
  - > `2502.17874v2_c0000` Experimental results highlight the effectiveness of our design, with MARASON achieving 28% top-1 accuracy, a substantial improvement over the non-retrieval state-of-the-art accuracy of 19%. Moreover, MARASON outperforms both naive retrieval-augmented generation methods and traditional graph matching approaches.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ). We hypothesize that this is due to models’ inabilities to adequately address differences between the retrieved references and the target molecule
**L0** The catalyst figures describe the complete workflow. The supplied abstract does not provide a matched GPT-4 baseline without retrieval, so it does not isolate retrieval’s contribution or establish experimental synthesis and measured catalytic performance.
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
  - > `2603.15712v1_c0000` Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening.
**L1** MARASON’s demonstrated scope is mass-spectrum simulation for molecules up to 1500 Da. The supplied passages omit evaluation denominators and numerical results for the naive-retrieval and traditional-matching comparisons; the proposed explanation for simple concatenation’s weakness is a hypothesis.
  - > `2502.17874v2_c0000` We apply this approach to mass spectrum simulation and introduce MARASON, a novel model that incorporates neural graph matching to enhance a fragmentation-based neural network.
  - > `2502.17874v2_c0002` “Small molecules” are defined in this work by a mass upper limit of 1500 Da, enforced in all experiments.
  - > `2502.17874v2_c0000` Experimental results highlight the effectiveness of our design, with MARASON achieving 28% top-1 accuracy, a substantial improvement over the non-retrieval state-of-the-art accuracy of 19%. Moreover, MARASON outperforms both naive retrieval-augmented generation methods and traditional graph matching approaches.
  - > `2502.17874v2_c0002` We hypothesize that this is due to models’ inabilities to adequately address differences between the retrieved references and the target molecule

### Answer B

**F0** The catalyst-discovery framework grounds GPT-4 with relevant catalyst retrieval from a 50,000+ materials database, combines this with structured prompts, and validates generated high-entropy alloy catalysts using DFT without fine-tuning.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
  - > `2603.15712v1_c0005` Pre-trained models encode implicit scientific knowledge Bubeck et al. (2023) , which RAG Lewis et al. (2020) grounds through relevant catalyst retrieval while maintaining creative exploration.
**F1** MARASON retrieves the most structurally similar reference molecule using Tanimoto similarity on Morgan fingerprints from annotated structure–spectrum pairs; its experiments use the training dataset to mitigate data leakage. It filters for matching adduct and instrument types and selects up to three reference spectra with collision energies closest to the target.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) .
  - > `2502.17874v2_c0014` We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F2** MARASON enriches retrieved spectral peaks with predicted reference fragments and uses neural graph matching to align target and reference fragmentation DAGs, pairing their peaks and fragments to improve spectrum predictions.
  - > `2502.17874v2_c0015` Reference spectra only provide m/z values and peak intensities. This information is enriched by annotating peaks with ICEBERG-predicted fragments of the reference structure.
  - > `2502.17874v2_c0035` On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
  - > `2502.17874v2_c0012` MARASON is a mass spectrum simulator built on the ICEBERG model ( Goldman et al., 2024 ) with reference retrieval augmentation and neural graph matching.
**F3** The catalyst framework generated over 250 candidates with an 82% thermodynamic stability rate; 68% achieved <$100/kg cost together with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
**F4** The catalyst study reports that its best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieved 0.285V limiting potential, a 25% improvement over IrO 2.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 )
**F5** The catalyst study identifies Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 as optimally balancing performance–cost trade-offs at $18/kg.
  - > `2603.15712v1_c0000` Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
**F6** The catalyst system reports 200× computational efficiency compared with traditional high-throughput screening.
  - > `2603.15712v1_c0000` our system achieves 200× computational efficiency compared to traditional high-throughput screening.
**F7** On NIST (2020), MARASON improved spectral cosine similarity over ICEBERG by a relative 5.2% on the random split and a relative 3.7% on the scaffold split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F8** In the NIST (2020) random-split benchmark on positive adduct types, top-1 structure-retrieval accuracy was 27.8% for MARASON, versus 18.7% for ICEBERG and 20.2% for collision-energy-aware ICEBERG. The paper attributes the majority of the improvement to RAG.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method. As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
**F9** The structure-identification benchmark ranks 50 structures per test spectrum—49 decoys and 1 true structure—by spectral cosine similarity, making its retrieval accuracy a downstream identification outcome.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity. We evaluate the retrieval accuracy at top- k .
**F10** On MassSpecGym, described as having fewer annotated spectra and emphasizing generalization to different molecular scaffolds, MARASON improved top-1 retrieval accuracy from FraGNNet’s 31.93% to 34.03%; MARASON’s random seed was fixed as 1.
  - > `2502.17874v2_c0029` We consider MassSpecGym as a more challenging setting than NIST (2020) as it incorporates fewer annotated spectra and emphasizes generalization to different molecular scaffolds.
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method. Random seed is fixed as 1 for MARASON.
**F11** Retrieval alone was insufficient in the MS/MS experiments: retrieved spectra had lower cosine similarity than predictions from all baseline models. The paper also reports that simply concatenating reference information often yields minimal or no improvement.
  - > `2502.17874v2_c0024` the retrieved spectra are informative, but the cosine similarities of the retrieved spectra are lower than the predicted spectra produced by all baseline models, demonstrating that RAG on MS/MS is a non-trivial task.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ).
**I0** For an R&D client, these findings support testing retrieval as chemical grounding for candidate generation and as aligned reference data for property prediction; the MS/MS evidence particularly supports evaluating how retrieved information is integrated.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2502.17874v2_c0035` On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ).
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**L0** The catalyst outcomes describe a combined retrieval, structured-prompting and DFT-validation framework.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**L1** Catalyst validation is described as DFT validation; integration with automated synthesis is prospective.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2603.15712v1_c0021` Integration with automated synthesis platforms could enable closed-loop discovery systems
**L2** The MassSpecGym retrieval comparison assumes a known chemical formula.
  - > `2502.17874v2_table_b0dc99546ec1da3a_4` Table 2: Retrieval accuracy (mean with 99.9% confidence intervals upon bootstrapping, 20,000 resamples) with known chemical formula on the MassSpecGym dataset ( Bushuiev et al., 2024 ) .
**L3** MARASON’s demonstrated application is mass spectrum simulation and downstream retrieval; broader structure–property applications are prospective adaptations.
  - > `2502.17874v2_c0035` On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
  - > `2502.17874v2_c0035` MARASON establishes new state-of-the-art performance in terms of the quality of simulated spectra and retrieval accuracy in downstream applications. Future improvements and adaptations could see this neural graph matching strategy applied to a broader range of retrieval-augmented structure-property prediction tasks across the field of molecular machine learning.

### Answer C

**F0** The catalyst-discovery framework retrieves relevant catalyst examples from a 50,000+ materials database to ground GPT-4’s generation of high-entropy alloy catalysts without fine-tuning.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
  - > `2603.15712v1_c0002` The RAG framework retrieves relevant catalyst examples to guide generation toward physically realistic compositions, augmented with structured prompt engineering that encodes chemical constraints as natural language instructions.
**F1** The catalyst study uses retrieved examples alongside prompts encoding chemical constraints, then validates generated candidates with DFT.
  - > `2603.15712v1_c0002` The RAG framework retrieves relevant catalyst examples to guide generation toward physically realistic compositions, augmented with structured prompt engineering that encodes chemical constraints as natural language instructions.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
**F2** The catalyst study reports generating 250+ novel HEAs with 82% thermodynamic stability validated by DFT.
  - > `2603.15712v1_c0002` First LLM-driven catalyst discovery without fine-tuning, generating 250+ novel HEAs with 82% thermodynamic stability validated by Density Functional Theory (DFT)
**F3** For the catalyst candidates, the study reports that 68% achieved <$100/kg cost together with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
**F4** In the catalyst study’s volcano analysis, 78% of LLM catalysts were within 0.15eV of the optimal binding energy, compared with 31% for known catalysts.
  - > `2603.15712v1_c0013` The clustering of 78% of LLM catalysts within 0.15eV of the optimal binding energy ( \Delta E_{*O}=1.6 eV) compared to only 31% for known catalysts demonstrates the model’s implicit understanding of Sabatier’s principle Exner (2024)
**F5** The catalyst study reports 200× computational efficiency compared with traditional high-throughput screening.
  - > `2603.15712v1_c0000` our system achieves 200× computational efficiency compared to traditional high-throughput screening.
**F6** MARASON retrieves a structurally similar molecule and its annotated spectra from the training dataset, selecting the reference by Tanimoto similarity on Morgan fingerprints.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) .
**F7** MARASON excludes references with nonmatching adduct or instrument types and selects up to three reference spectra with collision energies closest to the target’s.
  - > `2502.17874v2_c0014` We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F8** MARASON uses reference spectra to learn an embedding for the target collision energy and annotates reference peaks with ICEBERG-predicted fragments.
  - > `2502.17874v2_c0015` As the collision energy value is continuous, our aim of including three reference energies is to learn an appropriate spectrum embedding for the target collision energy value by interpolating from three closest energies. Reference spectra only provide m/z values and peak intensities. This information is enriched by annotating peaks with ICEBERG-predicted fragments of the reference structure.
**F9** MARASON matches target and reference fragmentation DAGs, pairing peaks and fragments and using their alignment to improve spectrum predictions.
  - > `2502.17874v2_c0035` On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
**F10** On NIST (2020), MARASON improves spectral cosine similarity over ICEBERG by a relative 5.2% on the random split and a relative 3.7% on the scaffold split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset.
  - > `2502.17874v2_c0030` It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F11** In the random-split structure-retrieval benchmark, MARASON achieves 27.8% top-1 accuracy versus 18.7% for ICEBERG; collision-aware ICEBERG achieves 20.2%, supporting an improvement beyond adding collision energy alone.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method. As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
  - > `2502.17874v2_c0031` Table 1 only covers the random split; retrieval experiment results on scaffold split are in Table 5 in the Appendix.
**F12** On MassSpecGym, retrained MARASON improves top-1 structure-retrieval accuracy from FraGNNet’s 31.93% to 34.03%.
  - > `2502.17874v2_c0031` We further retrain MARASON on the recently developed open-source dataset, MassSpecGym ( Bushuiev et al., 2024 ) , where we achieve state-of-the-art retrieval accuracy, as shown in Table 2 .
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method.
**F13** For NIST (2020) test pairs, MARASON’s retrieval augmentation brings significant gains when Tanimoto similarity is larger than 0.3, but no significant improvement between 0.1 and 0.3; a slight drop occurs in (0.1, 0.2].
  - > `2502.17874v2_c0034` for all testing data in NIST (2020) , we group structural pairs based on their Tanimoto similarities and compare performances of MARASON with or without RAG (same model configurations as in Table 3 ).
  - > `2502.17874v2_c0034` RAG starts to bring a significant performance gain when the Tanimoto similarity is larger than 0.3. When the best reference structure has a Tanimoto similarity between 0.1 and 0.3, RAG does not bring a significant improvement, while MARASON still performs robustly with such irrelevant references. The slight performance drop between Tanimoto similarity (0.1, 0.2]
**F14** Simply supplying retrieved information is insufficient: direct concatenation often yields minimal or no improvement, and retrieved spectra alone have lower cosine similarity than predictions from all baseline models.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ).
  - > `2502.17874v2_c0024` the retrieved spectra are informative, but the cosine similarities of the retrieved spectra are lower than the predicted spectra produced by all baseline models, demonstrating that RAG on MS/MS is a non-trivial task.
**L0** The catalyst outcomes describe a combined retrieval, prompting and DFT workflow; the supplied passages do not isolate retrieval's contribution with a matched no-retrieval comparison.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**L1** The catalyst stability result is DFT validation; automated synthesis integration is described as a future possibility.
  - > `2603.15712v1_c0002` generating 250+ novel HEAs with 82% thermodynamic stability validated by Density Functional Theory (DFT)
  - > `2603.15712v1_c0021` Integration with automated synthesis platforms could enable closed-loop discovery systems
**L2** The reported NIST structure-retrieval benchmark uses positive adduct types and ranks the true structure among 49 isomeric decoys.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity.
**L3** The MassSpecGym comparison assumes known chemical formula. MARASON uses pseudo-labeled missing collision energies and a fixed random seed of 1.
  - > `2502.17874v2_c0029` with known chemical formula on the MassSpecGym dataset
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym. The model is retrained from scratch on MassSpecGym data to ensure no data leakage from NIST. MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method. Random seed is fixed as 1 for MARASON.
**L4** The similarity-dependent retrieval analysis reports cosine similarity on the random split with random seed = 1.
  - > `2502.17874v2_c0031` The performance of MARASON with and without RAG on target and reference pairs grouped by Tanimoto similarity. We report cosine similarity on the random split with random seed = 1

### Answer D

**F0** The catalyst-discovery framework retrieves relevant catalysts from a 50,000+ materials database to ground GPT-4 generation without fine-tuning; structured prompts direct exploration, and DFT validates proposed performance.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification. Pre-trained models encode implicit scientific knowledge Bubeck et al. (2023) , which RAG Lewis et al. (2020) grounds through relevant catalyst retrieval while maintaining creative exploration.
**F1** The catalyst framework generated over 250 candidates with an 82% thermodynamic stability rate.
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
**F2** For the catalyst framework, 68% achieved <$100/kg cost together with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
  - > `2603.15712v1_c0000` Our approach generated over 250 catalyst candidates with an 82% thermodynamic stability rate while addressing multi-objective constraints: 68% achieved <$100/kg cost with metallic conductivity (band gap<0.1eV) and mechanical stability (B/G>1.75).
**F3** The catalyst study reports that its best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential, described as a 25% improvement over IrO 2.
  - > `2603.15712v1_c0000` The best-performing Fe 0.2 Co 0.2 Ni 0.2 Ir 0.1 Ru 0.3 achieves 0.285V limiting potential (25% improvement over IrO 2 ), while Cr 0.2 Fe 0.2 Co 0.3 Ni 0.2 Mo 0.1 optimally balances performance-cost trade-offs at $18/kg.
**F4** The catalyst study reports 200× computational efficiency compared to traditional high-throughput screening.
  - > `2603.15712v1_c0000` Volcano plot analysis confirms that 78% of LLM-generated catalysts cluster near the theoretical activity optimum, while our system achieves 200× computational efficiency compared to traditional high-throughput screening.
**F5** MARASON retrieves the most structurally similar reference molecule using Tanimoto similarity on Morgan fingerprints from annotated structure-spectrum pairs, using the training dataset in its experiments. It excludes nonmatching adduct or instrument types and selects up to three reference spectra with collision energies closest to the target.
  - > `2502.17874v2_c0014` Let our retrieval database be any database with annotated structure-spectrum pairs; in our experiments, we use the training dataset to mitigate concerns about data leakage. We retrieve the most similar reference molecule as quantified by Tanimoto similarity ( Bajusz et al., 2015 ) operating on Morgan fingerprints ( Morgan, 1965 ) . We exclude the entries that have nonmatching adduct types or instrument types recorded to mitigate the confounding effects of different experimental conditions. We then identify up to three reference spectra with the most similar collision energy to the target (query) structure \mathcal{M} .
**F6** MARASON uses neural graph matching to align target and reference fragmentation DAGs, pair their peaks and fragments, and use those alignments to improve spectrum predictions.
  - > `2502.17874v2_c0035` This paper presents a retrieval-augmented generation framework for molecules by integrating neural graph matching into an existing end-to-end geometric deep learning framework. On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
**F7** On the NIST (2020) random split, MARASON improves spectral cosine similarity over ICEBERG by a relative 5.2%.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset. The results are summarized in Fig. 3 . MARASON outperforms all baselines in both types of splits, and the success on scaffold split excludes the possibility that MARASON needs highly similar reference structures for accurate predictions. It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F8** On the NIST (2020) scaffold split, MARASON improves spectral cosine similarity over ICEBERG by a relative 3.7%, showing a benefit beyond the random split.
  - > `2502.17874v2_c0030` We evaluate the prediction power of MARASON by comparing the spectral cosine similarity of the predicted spectrum of different baseline models on the NIST (2020) dataset. The results are summarized in Fig. 3 . MARASON outperforms all baselines in both types of splits, and the success on scaffold split excludes the possibility that MARASON needs highly similar reference structures for accurate predictions. It improves the cosine similarity of the ICEBERG baseline by a relative 5.2% on random split and a relative 3.7% on scaffold split.
**F9** In the random-split structure-retrieval benchmark, MARASON improves top-1 accuracy over ICEBERG from 18.7% to 27.8%; methods rank 50 structures per test spectrum (49 decoys + 1 true structure) by cosine similarity.
  - > `2502.17874v2_c0030` In the retrieval benchmark, MARASON improves the top-1 retrieval accuracy upon ICEBERG from 18.7% to 27.8%, a marked increase in the state-of-the-art performance for this task by a relative margin of 48% over the next best method.
  - > `2502.17874v2_c0031` Table 1 only covers the random split; retrieval experiment results on scaffold split are in Table 5 in the Appendix.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity.
**F10** The collision-energy ablation reports ICEBERG (with collision) top-1 accuracy of 20.2%; the authors attribute the majority of MARASON's improvement to RAG.
  - > `2502.17874v2_c0030` As an ablation study, ICEBERG (with collision) has a top-1 accuracy of 20.2%, indicating that the majority of improvement is directly attributable to our use of RAG.
**F11** On MassSpecGym, MARASON improves top-1 retrieval accuracy over FraGNNet from 31.93% to 34.03%, with MARASON's random seed fixed as 1.
  - > `2502.17874v2_c0031` We further retrain MARASON on the recently developed open-source dataset, MassSpecGym ( Bushuiev et al., 2024 ) , where we achieve state-of-the-art retrieval accuracy, as shown in Table 2 .
  - > `2502.17874v2_c0031` MARASON improves the top-1 retrieval accuracy upon the current state-of-the-art, FraGNNet, from 31.93% to 34.03%, a marked increase by a relative margin of 6% over the next best method. Random seed is fixed as 1 for MARASON.
**F12** The MARASON paper reports that simply concatenating reference information to neural-network inputs often yields minimal or no improvements.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ).
**F13** In the NIST (2020) spectral comparison, retrieved spectra have lower cosine similarity to experimental spectra than predictions from all baseline models, showing that copying a retrieved spectrum is insufficient.
  - > `2502.17874v2_c0024` Spectral similarity between experimental spectra and predictions from various MS/MS simulators on NIST (2020) dataset.
  - > `2502.17874v2_c0024` It is worth noting, from the dashed lines in the plots, that the retrieved spectra are informative, but the cosine similarities of the retrieved spectra are lower than the predicted spectra produced by all baseline models, demonstrating that RAG on MS/MS is a non-trivial task.
**I0** For an R&D client, this supports using retrieval for grounded catalyst proposal generation and investing in explicit structural alignment for spectrum prediction; merely supplying reference information may add little value.
  - > `2603.15712v1_c0005` LLM-driven catalyst discovery pipeline: RAG retrieval → LLM generation → DFT validation.
  - > `2502.17874v2_c0035` On the molecular machine learning task of mass spectrum simulation, we implement MARASON to match the fragmentation DAGs of the target and reference structures, pair up peaks and fragments in the reference and target structures, and use that alignment information to generate improved spectrum predictions.
  - > `2502.17874v2_c0002` Simple approaches, such as direct concatenation of reference information to the input of the neural network, often yield minimal or no improvements (see Table 3 ).
**L0** The catalyst outcomes describe a combined retrieval, prompting and DFT workflow. The supplied passages do not establish a retrieval-disabled comparison or laboratory validation, so these outcomes do not isolate retrieval's contribution or establish laboratory performance.
  - > `2603.15712v1_c0005` Our retrieval-augmented generation (RAG) framework enables GPT-4 to discover novel high-entropy alloy catalysts without fine-tuning by integrating: (1) a 50,000+ materials database for chemical grounding, (2) structured prompt engineering for directed exploration, and (3) DFT validation for performance verification.
**L1** MARASON's NIST structure-ranking results concern positive adduct types and a benchmark with 49 decoys plus one true structure per test spectrum; they do not establish accuracy in unrestricted structure searches.
  - > `2502.17874v2_c0024` Retrieval accuracy (mean \pm 95% confidence interval on 3 random seeds) on NIST (2020) dataset with random (InChI key) split on positive adduct types.
  - > `2502.17874v2_c0029` We run MARASON and all comparative methods on 50 structures per test spectrum (49 decoys + 1 true structure) and rank all of them by cosine similarity.
**L2** The MassSpecGym comparison assumes known chemical formula, uses a fixed MARASON seed of 1, and uses NIST-derived pseudo labels for missing collision energies.
  - > `2502.17874v2_table_b0dc99546ec1da3a_4` Table 2: Retrieval accuracy (mean with 99.9% confidence intervals upon bootstrapping, 20,000 resamples) with known chemical formula on the MassSpecGym dataset
  - > `2502.17874v2_c0031` Since not all spectra in MassSpecGym have collision energy label, but MARASON requires labeled collision energies, we use a NIST-pretrained model to create pseudo labels for those unannotated spectra, i.e., transferring the collision energy knowledge from NIST to MassSpecGym.
  - > `2502.17874v2_c0031` Random seed is fixed as 1 for MARASON.
**L3** MARASON's experiments enforce a molecular mass upper limit of 1500 Da. Transfer of its graph-matching strategy to broader structure-property tasks remains prospective in the supplied passages.
  - > `2502.17874v2_c0002` “Small molecules” are defined in this work by a mass upper limit of 1500 Da, enforced in all experiments.
  - > `2502.17874v2_c0035` Future improvements and adaptations could see this neural graph matching strategy applied to a broader range of retrieval-augmented structure-property prediction tasks across the field of molecular machine learning.

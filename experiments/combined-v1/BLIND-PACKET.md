# combined-v1: blind answer packet for re-scoring

Three anonymised answers per question (labels A/B/C are shuffled independently for every question). Score each required point **1** (accurately stated with an entailing citation), **0.5** (partly) or **0**, using only the claims, interpretations and cited limitations shown. Interpretations never earn points. Also record any **misleading claim** (wrong number, subject, metric, condition or qualifier; an inference presented as a finding; a fabricated answer to G09.3, G09.4 or G10.4) and any **unsupported recommendation** in an interpretation.

Every quote below has been checked programmatically to appear verbatim in its cited passage. The full anchor passages for each point are in `REVIEW-PACKET.md`. Point-specific rules:

- **evidence_absent_points:** G09.4 (corrected after review): no monetary per-query cost is reported. 1 if the answer explicitly says no monetary per-query cost is established (with or without proxies); 0.5 if it gives only accurately cited computational cost proxies (retrieval rounds, embedding calls, candidates reranked, the reranker's higher per-token cost) without saying monetary cost is not reported, or if the cost part is silently omitted; 0 and one misleading claim if any monetary per-query price not supported by the study is asserted. Accurate proxies are never counted as misleading.
- **two_component_points:** G04.5 and G10.4 (corrected after review) each have two components; 1 requires both, one alone scores 0.5. G05.5 requires the source's limitation on the dispute-resolution gain ('to a certain degree', 'falls short of the upper bound'); stating the gain without it scores at most 0.5. G03.5 (corrected after Codex review): (a) the paired ASR results on Llama-2-7B-chat and Vicuna-13B-v1.5, reported as pairs because the source's metric labels are not readable (assigning a pair to a specific model or metric as fact is an unsupported attribution); (b) the effort/cost of adversarial tuning is not established (LoRA is used for efficiency; the 20-minute GCG figure is a prior method's cost, and presenting it as adversarial tuning's cost is a misattribution). Both are required for 1.
- **equivalent_figures:** G06.2 (corrected after Codex review): 'at least 60%' (introduction, c0004) and 'at least 66%' (results, c0019) are compatible lower bounds for the six Frontier Model Forum members; either may be quoted with correct attribution and neither is misleading. The group statistics (FMF mean 74.4%, SD 6.9%; other 10 at or below 60%, mean 40.7%, SD 11.4%) require support from c0019. G08.4: the paper reports 'a drop of just 0.8%' for 61.6% vs 62.0%; the calculated 0.4 percentage points (about 0.65% relative) or the paper's 0.8% attributed to the paper both score; 0.8 presented as the calculated percentage-point gap scores 0.5.
- **evidence_limit_points:** G09.3 and G10.4 ask for something the corpus does not establish. They score 1 when the answer states the cited limitation (Chinese-only evaluation; simplified simulation, not deployment); a fabricated English/EU result or real-world lying rate scores 0 and counts as a misleading claim.
- **published_vs_inferred:** Required points are published findings. A business implication the system infers must be presented as a labelled interpretation grounded in cited findings; an inference presented as a finding is a misleading claim. Interpretations are never required points.

Fill in `blind-score-sheet.json`: a score per point per label, plus lists of misleading claims and unsupported recommendations (cite the label and item number, e.g. "G04-B F2").

---

## G01 (single-paper)

**Question.** A client's risk committee asks whether market mechanisms, not only regulation, can govern AI risk. What market mechanisms does the 'AI Governance through Markets' paper propose, how do they connect AI risk to financial risk, and what limits do the authors acknowledge?

**Required points:**

- **G01.1** Four market-governance vectors: insurance, auditing, procurement and due diligence.
- **G01.2** They serve risk distribution, information discovery, protocolisation and capital allocation, decreasing AI risk by pricing, measuring and mitigating it.
- **G01.3** Insurance can make safety-washing or underestimating AI risk less appealing; actuarial rigour can curb AI hype.
- **G01.4** The authors do not claim market forces alone adequately protect societal interests; standardised AI disclosures are needed alongside market mechanisms.

### Answer A

**F0** [finding] The paper proposes market governance alongside regulation through insurance, auditing and certification, procurement, and due diligence. Their respective roles are to distribute risk, discover information, establish protocols, and guide capital allocation, making financial incentives a means of governing AI development and deployment.
  - > `2501.17755v2_c0000` This paper argues that market governance mechanisms should be considered a key approach in the governance of artificial intelligence (AI), alongside traditional regulatory frameworks.
  - > `2501.17755v2_c0003` These mechanisms include (but are not limited to) insurance, auditing, procurement practices, and due diligence - which in turn serve risk distribution, information discovery, protocolisation and capital allocation.
  - > `2501.17755v2_c0015` Certification often follows auditing, serving as formal recognition that a company meets specific industry benchmarks or quality standards.

**F1** [finding] Insurance would connect AI risk to financial exposure through risk-based pricing, underwriting standards, and policy exclusions. Auditing and certification would make compliance and risk management more visible, creating incentives through investor and customer trust, reputational consequences, and potential financial penalties.
  - > `2501.17755v2_c0010` Insurance can serve as a powerful governance mechanism, shaping responsible AI development and deployment. This can be achieved through risk-based pricing, underwriting standards, and carefully crafted policy exclusions.
  - > `2501.17755v2_c0015` These processes are usually made public, creating incentives for companies to maintain high levels of transparency and integrity to build trust with stakeholders, including investors, customers, and regulators. The public nature of auditing and certification encourages companies to improve their practices and reduce risks, as failing to meet standards can lead to reputational damage or financial penalties.

**F2** [finding] Procurement and due diligence connect risk assessment to purchasing and investment decisions: the authors argue that safer firms could attract capital, secure better terms, and win contracts. The underlying financial exposure includes fines, legal liabilities, and reputational damage from privacy violations, biased decisions, or other harmful deployment outcomes; the paper advocates accounting for private costs and externalities in investment evaluation.
  - > `2501.17755v2_c0027` All the market governance mechanisms we examine—including insurance providers, procurement entities, and due diligence evaluators—necessitate accurate and reliable data regarding artificial intelligence systems to effectively price AI assets, evaluate associated risks, and facilitate implementation protocols.
  - > `2501.17755v2_c0033` AI companies that successfully minimise risk can gain a competitive edge by attracting capital, securing better terms, and winning more procurement contracts.
  - > `2501.17755v2_c0008` These include potential costs from regulatory fines, legal liabilities, or ethical breaches—such as violations of data privacy laws, biased decision-making algorithms, or unintended harmful consequences of AI deployment.
  - > `2501.17755v2_c0008` This methodology reinforces the importance of acknowledging both private costs and externalities, leading to more responsible investment decisions.

**F3** [finding] Standardised disclosure is the proposed foundation connecting technical AI risks to market decisions. Comparable information about model errors, privacy incidents, and other risks would help insurers, investors, and buyers assess exposure and allocate capital; the authors present this as an incentive pathway rather than a quantified demonstration of risk reduction.
  - > `2501.17755v2_c0034` This would be paired with specific metrics to quantify these risks, such as model error rates, data privacy breach incidents, or energy consumption during model training and deployment. Such quantification enables stakeholders to make informed comparisons between different AI systems and providers. With standardised reporting, market actors can assess AI risks more accurately, reducing uncertainty and promoting better capital allocation.
  - > `2501.17755v2_c0044` Further research in this vein could significantly enhance our understanding of how market governance mechanisms might be optimally designed and implemented to ensure beneficial AI outcomes while maintaining innovation and economic efficiency.

**L0** [limitation] The authors do not claim markets alone adequately protect societal interests; the four mechanisms are illustrative, not exhaustive.
  - > `2501.17755v2_c0000` While we do not claim that market forces alone can adequately protect societal interests, we maintain that standardised AI disclosures and market mechanisms can create powerful incentives for safe and responsible AI development.
  - > `2501.17755v2_c0004` We do not believe the aforementioned four mechanisms to be exhaustive but rather exemplary of the kind of intervention points which are able to work alongside market forces to govern AI.

**L1** [limitation] Market decisions require reliable information, and standardised frameworks may omit risk intricacies. Further research is needed on optimal design and implementation.
  - > `2501.17755v2_c0027` Without adequate information, markets are unable to make informed decisions ( Healy and Palepu, 2001 ) .
  - > `2501.17755v2_c0032` While such frameworks may not fully capture the intricacies of each risk, they serve as a practical means of ensuring that AI-related concerns can be communicated and addressed effectively.
  - > `2501.17755v2_c0044` Further research in this vein could significantly enhance our understanding of how market governance mechanisms might be optimally designed and implemented to ensure beneficial AI outcomes while maintaining innovation and economic efficiency.

**L2** [limitation] Extensive disclosure can burden early-stage enterprises, deter entry, and delay commercialisation; the authors call for disclosure proportional to entity size.
  - > `2501.17755v2_c0043` The imposition of extensive disclosure requirements on early-stage enterprises may impede innovation trajectories.
  - > `2501.17755v2_c0043` Resource constraints can limit these organisations’ capacity to navigate these frameworks, resulting in increased operational costs that may deter market entry and extend commercialisation timelines ( Van Reenen et al., 2021 ) .
  - > `2501.17755v2_c0043` Thus the appropriate level of disclosure must be adjusted to an entity’s size.

**L3** [limitation] The sustainability of the described startup–corporation supply-chain arrangement depends on technology conglomerates continuing to absorb risk.
  - > `2501.17755v2_c0043` While this arrangement currently maintains supply chain stability, its sustainability remains contingent upon the continued risk-absorption practices of technology conglomerates.

### Answer B

**F0** [finding] The paper proposes insurance, auditing and certification, procurement, and due diligence as complements to regulation. Their respective roles are to distribute risk, discover information, establish purchasing protocols, and guide capital allocation: governance works by making AI risk affect commercial incentives and access to money.
  - > `2501.17755v2_c0003` These mechanisms include (but are not limited to) insurance, auditing, procurement practices, and due diligence - which in turn serve risk distribution, information discovery, protocolisation and capital allocation.
  - > `2501.17755v2_c0001` By directing capital flows, they possess the distinct advantage of embedding their own enforcement and incentive structures ( Cullenward and Victor, 2020 ) .
  - > `2501.17755v2_c0000` This paper argues that market governance mechanisms should be considered a key approach in the governance of artificial intelligence (AI), alongside traditional regulatory frameworks.

**F1** [finding] Insurance would translate AI exposure into risk-based prices, underwriting requirements, and coverage exclusions, while transferring potential losses. Auditing and certification would make compliance and risk management more visible, giving firms incentives to improve controls because failures can damage reputation or bring financial penalties.
  - > `2501.17755v2_c0010` Insurance serves as an enabler of transactions amid radical uncertainty by transferring and mitigating risks associated with unforeseen events ( Knight, 1921 ) .
  - > `2501.17755v2_c0010` This can be achieved through risk-based pricing, underwriting standards, and carefully crafted policy exclusions.
  - > `2501.17755v2_c0015` Certification often follows auditing, serving as formal recognition that a company meets specific industry benchmarks or quality standards.
  - > `2501.17755v2_c0015` The public nature of auditing and certification encourages companies to improve their practices and reduce risks, as failing to meet standards can lead to reputational damage or financial penalties.

**F2** [finding] The financial connection is that AI failures and harmful deployment can generate legal liabilities, regulatory fines, and reputational losses, changing an investment’s risk-adjusted value. Procurement and due diligence provide commercial channels for rewarding lower risk: the authors argue that safer firms can win contracts, attract capital, and secure better terms, rather than reporting a measured causal effect.
  - > `2501.17755v2_c0008` These include potential costs from regulatory fines, legal liabilities, or ethical breaches—such as violations of data privacy laws, biased decision-making algorithms, or unintended harmful consequences of AI deployment. Such risks are not always fully captured by \sigma(X) but can have substantial financial and reputational repercussions.
  - > `2501.17755v2_c0005` RAV (Risk-Adjusted Value) : The value of an outcome adjusted for risk, reflecting the market actor’s risk tolerance. It represents the certainty-equivalent value of the expected return after accounting for the investor’s aversion to risk.
  - > `2501.17755v2_c0033` AI companies that successfully minimise risk can gain a competitive edge by attracting capital, securing better terms, and winning more procurement contracts.

**F3** [finding] Standardised disclosures are the proposed information foundation connecting technical AI risk to financial decisions. Comparable descriptions and metrics would help insurers, buyers, and investors assess systems and allocate capital, but the authors acknowledge that simplified frameworks cannot capture every risk and that extensive disclosure obligations can burden smaller firms.
  - > `2501.17755v2_c0027` All the market governance mechanisms we examine—including insurance providers, procurement entities, and due diligence evaluators—necessitate accurate and reliable data regarding artificial intelligence systems to effectively price AI assets, evaluate associated risks, and facilitate implementation protocols.
  - > `2501.17755v2_c0034` With standardised reporting, market actors can assess AI risks more accurately, reducing uncertainty and promoting better capital allocation.
  - > `2501.17755v2_c0032` While such frameworks may not fully capture the intricacies of each risk, they serve as a practical means of ensuring that AI-related concerns can be communicated and addressed effectively.
  - > `2501.17755v2_c0043` The imposition of extensive disclosure requirements on early-stage enterprises may impede innovation trajectories.

**L0** [limitation] The authors explicitly reject the sufficiency of markets alone for protecting societal interests; the mechanisms are illustrative rather than exhaustive.
  - > `2501.17755v2_c0000` While we do not claim that market forces alone can adequately protect societal interests, we maintain that standardised AI disclosures and market mechanisms can create powerful incentives for safe and responsible AI development.
  - > `2501.17755v2_c0004` We do not believe the aforementioned four mechanisms to be exhaustive but rather exemplary of the kind of intervention points which are able to work alongside market forces to govern AI.

**L1** [limitation] The supplied passages support a governance proposal, not a quantified estimate of how much these mechanisms reduce AI harm. The authors describe the mechanisms as emerging and call for further research on their design and implementation.
  - > `2501.17755v2_c0044` Tools such as insurance, auditing, procurement, and due diligence, which have long played a role in managing risks and fostering transparency in sectors like finance and pharmaceuticals, are now beginning to emerge in the AI industry.
  - > `2501.17755v2_c0044` Further research in this vein could significantly enhance our understanding of how market governance mechanisms might be optimally designed and implemented to ensure beneficial AI outcomes while maintaining innovation and economic efficiency.

### Answer C

**F0** [finding] The paper proposes four complementary market mechanisms: insurance to distribute risk, auditing to discover information, procurement to establish protocols, and due diligence to guide capital allocation. These mechanisms aim to govern AI development and deployment by measuring, pricing and mitigating risk; insurance specifically spreads uncertainty and losses across market participants.
  - > `2501.17755v2_c0003` These mechanisms include (but are not limited to) insurance, auditing, procurement practices, and due diligence - which in turn serve risk distribution, information discovery, protocolisation and capital allocation. In the context of AI governance, market governance mechanisms aim to decrease AI risk by pricing, measuring and mitigating the risk incurred in AI deployment and development.
  - > `2501.17755v2_c0004` For example, insurance functions as market governance by facilitating the distribution and management of uncertainty across a broad pool of market participants ( Knight, 1921 ) , thereby mitigating individual exposure to risk while promoting resource allocation through the collective absorption of losses ( Boettke and Candela, 2021 ) .

**F1** [finding] The financial connection begins with AI risks becoming business risks as AI enters firms’ value-generating and infrastructural operations. The authors frame inadequate measurement and mitigation of private costs, together with unpriced externalities, as a market failure; directing capital flows gives market governance its own incentives and enforcement.
  - > `2501.17755v2_c0005` Consequently, organisations have already recognised that AI-related risks are synonymous with business risks, and are responding in a manner that reflects this understanding.
  - > `2501.17755v2_c0005` In this vein, we may understand the uncertainty around AI Risk and its mitigation as market failure. The failure, that is, to measure and mitigate the private costs of AI development and deployment and price its externalities. By AI risk, we imply a risk from the development and deployment of AI systems. This risk to the firm is magnified in how closely AI is being integrated to value-generating and infrastructural operations.
  - > `2501.17755v2_c0001` By directing capital flows, they possess the distinct advantage of embedding their own enforcement and incentive structures ( Cullenward and Victor, 2020 ) .

**F2** [finding] Standardised disclosures supply the information these mechanisms need: comparable descriptions and metrics concerning model vulnerabilities, incidents, capabilities and other risks. The proposed incentive is that firms with lower risk can attract capital, obtain better terms and win procurement contracts, encouraging competitors to improve safety; this is an argued pathway rather than a measured causal effect in the supplied passages.
  - > `2501.17755v2_c0034` This would be paired with specific metrics to quantify these risks, such as model error rates, data privacy breach incidents, or energy consumption during model training and deployment. Such quantification enables stakeholders to make informed comparisons between different AI systems and providers. With standardised reporting, market actors can assess AI risks more accurately, reducing uncertainty and promoting better capital allocation. The aforementioned market governance mechanisms require a framework for AI disclosure that identifies different sources of risk.
  - > `2501.17755v2_c0033` AI companies that successfully minimise risk can gain a competitive edge by attracting capital, securing better terms, and winning more procurement contracts. This competitive advantage can create a virtuous cycle where reducing risk not only enhances a company’s market position but also encourages industry-wide adoption of safer practices.

**F3** [finding] The authors explicitly position markets alongside regulation and do not claim that market forces alone adequately protect societal interests. Their four mechanisms are illustrative rather than exhaustive, and they acknowledge that policy interventions may be needed to build a robust market governance ecosystem.
  - > `2501.17755v2_c0000` This paper argues that market governance mechanisms should be considered a key approach in the governance of artificial intelligence (AI), alongside traditional regulatory frameworks.
  - > `2501.17755v2_c0000` While we do not claim that market forces alone can adequately protect societal interests, we maintain that standardised AI disclosures and market mechanisms can create powerful incentives for safe and responsible AI development.
  - > `2501.17755v2_c0004` We do not believe the aforementioned four mechanisms to be exhaustive but rather exemplary of the kind of intervention points which are able to work alongside market forces to govern AI.
  - > `2501.17755v2_c0001` Policy interventions may prove instrumental in creating a robust market governance ecosystem ( Kiely, 1998 ) .

**L0** [limitation] The authors do not claim that market forces alone adequately protect societal interests; the mechanisms complement regulation.
  - > `2501.17755v2_c0000` While we do not claim that market forces alone can adequately protect societal interests, we maintain that standardised AI disclosures and market mechanisms can create powerful incentives for safe and responsible AI development.

**L1** [limitation] The mechanisms require disclosures that identify sources of risk, and their proposed competitive incentives are not quantified effectiveness estimates in the supplied passages.
  - > `2501.17755v2_c0034` The aforementioned market governance mechanisms require a framework for AI disclosure that identifies different sources of risk.
  - > `2501.17755v2_c0033` This competitive advantage can create a virtuous cycle where reducing risk not only enhances a company’s market position but also encourages industry-wide adoption of safer practices.

**L2** [limitation] The four mechanisms are illustrative rather than exhaustive.
  - > `2501.17755v2_c0004` We do not believe the aforementioned four mechanisms to be exhaustive but rather exemplary of the kind of intervention points which are able to work alongside market forces to govern AI.

---

## G02 (single-paper)

**Question.** A multinational client must align its AI risk management across the EU, the U.S., the UK and China. According to the cross-regional study of AI risk-management frameworks, how do the four regimes differ and what trade-off does each carry?

**Required points:**

- **G02.1** EU: structured, risk-based framework prioritising transparency and conformity assessments.
- **G02.2** U.S.: decentralised, sector-specific regulation that promotes innovation but may fragment enforcement.
- **G02.3** UK: flexible, sector-specific strategy enabling agile responses but risking inconsistent coverage across domains.
- **G02.4** China: centralised directives enable rapid large-scale implementation while constraining public transparency and external oversight.

### Answer A

**F0** [finding] EU: A structured, risk-based regime prioritizes transparency and conformity assessments. Its trade-off is predictable oversight and potentially stronger trust versus significant compliance demands and less room for agile experimentation.
  - > `2503.05773v1_c0001` The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement.
  - > `2503.05773v1_c0029` In particular, the EU’s comprehensive approach -exemplified by the AI Act and its conformity assessment procedures - positions transparency as a legal obligation, potentially strengthening trust but imposing significant compliance demands.
  - > `2503.05773v1_c0033` The EU’s structured and uniform model offers predictability; however, it may hinder agile experimentation.

**F1** [finding] U.S.: Decentralized, sector-specific regulation favors flexibility, market experimentation and rapid innovation. The trade-off is fragmented enforcement, potential oversight gaps and legal uncertainty across sectors and states.
  - > `2503.05773v1_c0001` The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement.
  - > `2503.05773v1_c0031` The lack of a cohesive national framework may lead to regulatory uncertainty for developers working in various states or sectors.
  - > `2503.05773v1_c0033` The US prioritizes flexibility and market-driven growth; however, this approach may lead to oversight gaps and legal uncertainties.

**F2** [finding] UK: Flexible, sector-specific governance lets regulators tailor requirements to individual industries and respond quickly as AI develops. Its trade-off is agility and specialized oversight versus inconsistent coverage and coordination difficulties, particularly when risks cross sector boundaries.
  - > `2503.05773v1_c0008` The UK aims to establish itself as a global leader in “pro-innovation” AI governance, using a flexible, sector-specific strategy that allows regulators to customize regulations for individual industries [ 32 , 12 ] .
  - > `2503.05773v1_c0001` The flexible, sector-specific strategy of the UK facilitates agile responses but may lead to inconsistent coverage across domains.
  - > `2503.05773v1_c0033` The sector-specific system in the UK provides a compromise, though it may lead to inconsistencies and coordination difficulties.
  - > `2503.05773v1_c0032` Critics warn that the absence of comprehensive legislation may lead to inconsistent oversight, potentially causing significant issues when a disruptive AI application crosses various regulatory domains [ 69 ] .

**F3** [finding] China: Centralized, state-led directives align AI deployment with national priorities and enable rapid implementation at scale. The trade-off is constrained public transparency and external oversight, alongside reduced openness in the innovation ecosystem.
  - > `2503.05773v1_c0003` In contrast, China’s governance model is characterized by a more centralized and state-led approach, which aligns AI deployment with national priorities and utilizes government oversight to direct technological innovation [ 13 , 14 ] .
  - > `2503.05773v1_c0001` China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight.
  - > `2503.05773v1_c0033` The rapid, state-led regulatory changes in China can expedite the development of emerging technologies in prioritized sectors, while simultaneously diminishing openness and pluralism within the innovation ecosystem.

**I0** [interpretation] For the multinational client, these findings suggest a shared risk-management baseline with jurisdiction-specific requirements layered onto it. Alignment should therefore seek interoperability while retaining local controls, rather than assume a single uniform compliance approach will suffice.
  - > `2503.05773v1_c0046` Given the diversity of approaches, full harmonization of AI standards remains unlikely in the near future.
  - > `2503.05773v1_c0046` Similarly, data privacy and security remain critical concerns, as cross-border data flows necessitate at least partial interoperability among regulations despite variations in cultural and legal contexts.
  - > `2503.05773v1_c0049` International organizations and bilateral agreements can play a pivotal role in developing shared ethical standards, facilitating data-sharing protocols, and establishing baseline safety requirements, particularly for AI systems that operate across national borders.

**L0** [limitation] The comparisons are qualitative findings, not quantified causal estimates of regulatory effectiveness.
  - > `2503.05773v1_c0012` The research integrates comparative policy analysis, thematic analysis, and case study methodology to develop a nuanced understanding of how these frameworks address different aspects of AI risk and governance.

**L1** [limitation] The shared baseline with local requirements is an alignment interpretation grounded in regulatory divergence and interoperability needs, rather than a demonstrated client implementation outcome.
  - > `2503.05773v1_c0046` Given the diversity of approaches, full harmonization of AI standards remains unlikely in the near future.
  - > `2503.05773v1_c0046` Similarly, data privacy and security remain critical concerns, as cross-border data flows necessitate at least partial interoperability among regulations despite variations in cultural and legal contexts.

### Answer B

**F0** [finding] EU: A structured, risk-based regime prioritizes transparency and conformity assessments. Its trade-off is predictable oversight and potentially greater trust against significant compliance demands and less room for agile experimentation.
  - > `2503.05773v1_c0001` The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement.
  - > `2503.05773v1_c0029` In particular, the EU’s comprehensive approach -exemplified by the AI Act and its conformity assessment procedures - positions transparency as a legal obligation, potentially strengthening trust but imposing significant compliance demands.
  - > `2503.05773v1_c0033` The EU’s structured and uniform model offers predictability; however, it may hinder agile experimentation.

**F1** [finding] U.S.: Decentralized, sector-specific regulation favors flexibility, innovation and market-driven experimentation. The trade-off is fragmented enforcement, potential oversight gaps and legal uncertainty across sectors and states.
  - > `2503.05773v1_c0001` The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement.
  - > `2503.05773v1_c0031` The U.S. model encourages rapid implementation and market-driven experimentation by avoiding a singular comprehensive statute [ 29 ] .
  - > `2503.05773v1_c0031` The lack of a cohesive national framework may lead to regulatory uncertainty for developers working in various states or sectors.
  - > `2503.05773v1_c0033` The US prioritizes flexibility and market-driven growth; however, this approach may lead to oversight gaps and legal uncertainties.

**F2** [finding] UK: Flexible, sector-specific governance lets regulators tailor requirements to individual industries and respond quickly as AI develops. Its trade-off is agility against inconsistent coverage, coordination difficulties and potentially inadequate oversight of high-risk applications.
  - > `2503.05773v1_c0008` The UK aims to establish itself as a global leader in “pro-innovation” AI governance, using a flexible, sector-specific strategy that allows regulators to customize regulations for individual industries [ 32 , 12 ] .
  - > `2503.05773v1_c0031` The UK’s sector-specific and flexible approach allows regulators to quickly integrate new guidelines as AI develops [ 12 ] .
  - > `2503.05773v1_c0008` Critics argue that a loose coordination mechanism may end up in inconsistencies and inadequate oversight in high-risk applications.
  - > `2503.05773v1_c0033` The sector-specific system in the UK provides a compromise, though it may lead to inconsistencies and coordination difficulties.

**F3** [finding] China: Centralized, state-led directives align AI deployment with national priorities and enable rapid, large-scale implementation. The trade-off is restricted public transparency and external oversight, alongside reduced openness in the innovation ecosystem.
  - > `2503.05773v1_c0003` In contrast, China’s governance model is characterized by a more centralized and state-led approach, which aligns AI deployment with national priorities and utilizes government oversight to direct technological innovation [ 13 , 14 ] .
  - > `2503.05773v1_c0001` China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight.
  - > `2503.05773v1_c0033` The rapid, state-led regulatory changes in China can expedite the development of emerging technologies in prioritized sectors, while simultaneously diminishing openness and pluralism within the innovation ecosystem.

**L0** [limitation] These comparisons are qualitative assessments of governance models, not measured causal estimates of which regime reduces AI risk most effectively.
  - > `2503.05773v1_c0012` This research uses a multi-method qualitative approach to systematically analyze AI risk management frameworks in the four regions. The research integrates comparative policy analysis, thematic analysis, and case study methodology to develop a nuanced understanding of how these frameworks address different aspects of AI risk and governance.

### Answer C

**F0** [finding] EU: A structured, risk-based, tiered framework emphasizes transparency, conformity assessments and formal compliance. Its trade-off is comprehensive oversight against the challenge of maintaining room for innovation.
  - > `2503.05773v1_c0001` The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement.
  - > `2503.05773v1_c0044` The EU employs a structured, tiered system, while the U.S. follows a decentralized model, the UK enforces sector-specific rules, and China implements state-centric directives.
  - > `2503.05773v1_c0044` The EU and China impose more formal regulatory requirements, whereas the U.S. and UK rely on fragmented or flexible guidelines. This contrast highlights the ongoing trade-off between ensuring comprehensive oversight and fostering innovation.

**F1** [finding] U.S.: Decentralized, sector-specific regulation supports flexibility and innovation, but carries the risk of fragmented enforcement and gaps in coverage for emerging technologies.
  - > `2503.05773v1_c0001` The findings show that the EU implements a structured, risk-based framework that prioritizes transparency and conformity assessments, while the U.S. uses decentralized, sector-specific regulations that promote innovation but may lead to fragmented enforcement.
  - > `2503.05773v1_table_c68d8ead56911a6b_2` Jurisdiction: U.S.; Adaptability Features: Agency rulemaking State-level experimentation; Innovation Incentives: Market-driven Minimal ex-ante constraints; Potential Drawbacks: Fragmented coverage Regulatory gaps for emerging tech

**F2** [finding] UK: Flexible, sector-specific governance allows agile responses to changing AI risks. The trade-off is potentially inconsistent coverage across sectors.
  - > `2503.05773v1_c0001` The flexible, sector-specific strategy of the UK facilitates agile responses but may lead to inconsistent coverage across domains.

**F3** [finding] China: Centralized, state-directed governance aligns risk management with national priorities and enables rapid implementation at scale. Its trade-off is constrained public transparency and external oversight.
  - > `2503.05773v1_c0044` In contrast, the U.S. primarily relies on market-driven or sector-specific transparency efforts, the UK adopts a guidance-based approach, and China emphasizes internal audits aligned with national priorities.
  - > `2503.05773v1_c0001` China’s centralized directives allow rapid large-scale implementation while constraining public transparency and external oversight.

**L0** [limitation] The comparison is a qualitative assessment based on policy analysis, thematic analysis and case studies, rather than a quantified ranking of regulatory effectiveness.
  - > `2503.05773v1_c0000` A multi-method qualitative approach, including comparative policy analysis, thematic analysis, and case studies, investigates how these regions classify AI risks, implement compliance measures, structure oversight, prioritize transparency, and respond to emerging innovations.

---

## G03 (cross-paper)

**Question.** A client must defend a customer-facing LLM against new jailbreaks. How do Safety Context Retrieval (SCR) and two-stage adversarial tuning differ in approach, how effective were they, and what did each cost in normal-task performance or effort?

**Required points:**

- **G03.1** SCR keeps a pool of safety contexts, adds a minimal set of safety samples when a new jailbreak is identified, and retrieves a few at inference, instead of repeatedly fine-tuning.
- **G03.2** SCR reduced average ASR against GCG-T from 34.9% (no defence) to 2.5%.
- **G03.3** SCR had negligible effect on natural performance (e.g. Llama-3.1 HumanEval 61.6% to 57.3%, MMLU 62.6% to 63.2%).
- **G03.4** Adversarial tuning is two-stage: hierarchical meta-universal (token-level) adversarial prompts, then automatic semantic-level adversarial prompts, used to fine-tune on adversarial prompt and safe-response pairs.
- **G03.5** Two components, both required for 1 (one alone scores 0.5). (a) On the two target models, Llama-2-7B-chat and Vicuna-13B-v1.5, known jailbreaks gave average ASR of 66.54% / 51.38% and 19.62% / 9.62% under two metrics; adversarial tuning reduced them to 2.69% / 0.00% and 3.08% / 0.00%. The passage reports these pairs "respectively" without readable metric labels, so an answer may report them as pairs; assigning a pair to a specific model or metric as fact is an unsupported attribution. (b) Effort/cost: the passages give no compute-cost figure for adversarial tuning itself (it uses LoRA to improve training efficiency); an answer must say the cost is not established. Presenting the 20-minute GCG prompt-generation figure as the cost of adversarial tuning is a misattribution.

### Answer A

**L0** [limitation] The supplied passages cannot establish the requested comparison: they describe SCR and attack-specific fine-tuning called RapidResponse, but do not identify two-stage adversarial tuning, its stages, effectiveness, normal-task performance, or training effort. Equating RapidResponse with that method would be unsupported; passages describing and evaluating the requested two-stage method are needed.
  - > `2505.15753v1_c0002` RapidResponse [ 34 ] proposes to fine-tune LLMs with a few samples of an attack when it is observed, which can notably decrease the attack success rates of novel attacks after fine-tuning.
  - > `2505.15753v1_c0003` Specifically, SCR maintains a safety context pool, initialized by a group of common jailbreaks. When an in-the-wild jailbreak is reported and identified, SCR can automatically add a minimal set of safety samples into its pool. During inference, SCR retrieves a few examples from its full pool as the context.

**L1** [limitation] For newly identified jailbreaks, the supplied SCR passages give only a qualitative effectiveness statement, without attack-specific numerical outcomes or quantified update effort. Their computational-overhead assessment is also qualitative, limiting a numerical comparison of deployment costs.
  - > `2505.15753v1_c0003` Then, we show the scalability and effectiveness of SCR, where a few samples are sufficient to eliminate an in-the-wild jailbreak, significantly outperforming static contextual-based defense baselines.
  - > `2505.15753v1_c0015` Since only a small number of safety contexts are retrieved and included in the context window, their overhead is negligible and does not impact the natural reasoning abilities across various tasks, as demonstrated by our experiments.

### Answer B

**F0** [finding] SCR adapts at inference time: it maintains a pool of attack prompts paired with safe responses, adds examples after a new attack is identified, and retrieves relevant examples into the model’s context. The authors report that tens of specialized examples suffice for a new attack, with automated generation and minimal human safety auditing.
  - > `2505.15753v1_c0003` Specifically, SCR maintains a safety context pool, initialized by a group of common jailbreaks. When an in-the-wild jailbreak is reported and identified, SCR can automatically add a minimal set of safety samples into its pool. During inference, SCR retrieves a few examples from its full pool as the context.
  - > `2505.15753v1_c0013` Based on our empirical analysis, the number of specialized contexts needed for this attack does not have to be very high; tens of examples are sufficient to defend against a new attack. More importantly, this procedure can be automated with F_{S}(\cdot) and minimal human auditing on the safety of F_{S}(p_{j}) , making it practical and efficient.

**F1** [finding] SCR’s average attack success rates were 0.0%, 20.4%, and 9.7% for the three simulated emerging attacks, whose names are not supplied in that passage. For common attacks, GCG-T fell from 34.9% without defense to 2.5%, and 50-shot ICA fell from 45.4% to 7.4%; defended rates were 15.9% for PAIR and 10.1% for TAP. These results show substantial mitigation, with residual vulnerability in several tested conditions.
  - > `2505.15753v1_c0020` In our three simulated three in-the-wild attacks, SCR achieves an average attack success rate (ASR) of 0.0%, 20.4%, and 9.7% respectively across these attacks.
  - > `2505.15753v1_c0018` To maximize jailbreak effectiveness, we utilized 50-shot ICA.
  - > `2505.15753v1_c0018` For GCG-T, SCR reduces the average ASR from 34.9% (no defense) to 2.5%, significantly outperforming Self-reminder and ICD. Similarly, for ICA, SCR lowers the average ASR from 45.4% to 7.4%, demonstrating the consistent robustness of SCR in defending against these prompt-based common attacks.
  - > `2505.15753v1_c0018` The results are shown in Table 3 , where SCR achieves the lowest average ASR of 15.9% against PAIR and 10.1% against TAP

**F2** [finding] SCR’s normal-task results were mixed: average HumanEval scores changed from 64.4 to 68.0, GSM8K from 70.3 to 69.1, and MMLU stayed at 63.3; Llama-3.1 individually declined from 61.6 to 57.3 on HumanEval and from 82.3 to 80.2 on GSM8K. Its inference overhead was measurable: in the MMLU evaluation, total GPU memory was 30.3 GB without defense versus 59.3/59.4/59.5 GB with 2/3/4 retrieved examples, and total inference time was 48.9 seconds versus 74.1/78.0/81.4 seconds. Thus, the reported small average capability impact came with additional serving resources.
  - > `2505.15753v1_table_d472857c5172bfd0_4` Models: Average; Human Eval / Vanilla: 64.4; Human Eval / +SCR: 68.0; GSM8K / Vanilla: 70.3; GSM8K / +SCR: 69.1; MMLU / Vanilla: 63.3; MMLU / +SCR: 63.3
  - > `2505.15753v1_table_d472857c5172bfd0_1` Models: Llama-3.1; Human Eval / Vanilla: 61.6; Human Eval / +SCR: 57.3; GSM8K / Vanilla: 82.3; GSM8K / +SCR: 80.2; MMLU / Vanilla: 62.6; MMLU / +SCR: 63.2
  - > `2505.15753v1_c0022` We evaluated the computational overhead of SCR in terms of GPU memory usage and inference time for the MMLU dataset, with results presented in Table 7 .
  - > `2505.15753v1_table_1cb85a8157eb0710_1` Metric / Defense / No defense: SCR (2 shot); GPU Memory (GB) / Retrieval Model / 0: 29.0; GPU Memory (GB) / Generation LLM / 30.3: 30.3; GPU Memory (GB) / Total / 30.3: 59.3; Inference time (s) / Retrieval / 0: 12.9; Inference time (s) / Generation / 48.9: 61.2; Inference time (s) / Total / 48.9: 74.1

**F3** [finding] Two-stage adversarial tuning instead trains on adversarial prompts paired with safe responses: first it learns universal token-level suffixes and refines individual examples, then an attack agent iteratively develops semantic-level prompts to expose out-of-distribution jailbreak patterns. The authors report superiority over six defense baselines across three jailbreak datasets and five attack scenarios, plus empirical transfer across attack strategies and target models. Its effort involves adversarial-example generation and model tuning, but the supplied passages do not quantify this framework’s total cost or normal-task tradeoff.
  - > `2406.06622v1_c0008` Adversarial tuning generates adversarial prompts to explore worst-case scenarios for LLMs by optimizing datasets with adversarial prompts and safe response pairs. In the first stage, we use hierarchical meta-universal adversarial tuning to generate token-level adversarial prompts efficiently. The outer phase learns task-based universal adversarial suffixes that generalize across tasks.
  - > `2406.06622v1_c0008` In the inner phase, we refine individual adversarial examples iteratively, starting from a universal adversarial example. In the second stage, we introduce automatic adversarial prompt learning to iteratively refine semantic-level adversarial prompts, further enhancing the LLMs’ defense capability. This involves the attack agent refining the adversarial prompt iteratively, enabling the model to learn out-of-distribution jailbreak patterns and improve its overall defense.
  - > `2406.06622v1_c0000` We conducted comprehensive experiments on three widely used jailbreak datasets, comparing our framework with six defense baselines under five representative attack scenarios. The results underscore the superiority of our proposed methods. Furthermore, our adversarial tuning framework exhibits empirical generalizability across various attack strategies and target LLMs, highlighting its potential as a transferable defense mechanism.

**L0** [limitation] SCR’s emerging-attack results concern three simulations, and updating its pool assumes an attack has been reported and identified; protection against arbitrary future jailbreaks is unestablished.
  - > `2505.15753v1_c0020` In our three simulated three in-the-wild attacks, SCR achieves an average attack success rate (ASR) of 0.0%, 20.4%, and 9.7% respectively across these attacks.
  - > `2505.15753v1_c0003` When an in-the-wild jailbreak is reported and identified, SCR can automatically add a minimal set of safety samples into its pool.

**L1** [limitation] SCR’s overhead measurements concern an MMLU evaluation and do not establish customer-facing per-request latency.
  - > `2505.15753v1_c0022` We evaluated the computational overhead of SCR in terms of GPU memory usage and inference time for the MMLU dataset, with results presented in Table 7 .

**L2** [limitation] SCR’s HumanEval average excludes Mistral, whose scores are unavailable; it therefore has a different model denominator from the GSM8K and MMLU averages.
  - > `2505.15753v1_table_d472857c5172bfd0_3` Models: Mistral; Human Eval / Vanilla: NA; Human Eval / +SCR: NA; GSM8K / Vanilla: 45.8; GSM8K / +SCR: 47.4; MMLU / Vanilla: 56.5; MMLU / +SCR: 56.8

**L3** [limitation] The supplied adversarial-tuning results report qualitative superiority and empirical transfer, without numerical effectiveness, normal-task scores or total tuning costs sufficient for a quantitative comparison with SCR.
  - > `2406.06622v1_c0000` We conducted comprehensive experiments on three widely used jailbreak datasets, comparing our framework with six defense baselines under five representative attack scenarios. The results underscore the superiority of our proposed methods. Furthermore, our adversarial tuning framework exhibits empirical generalizability across various attack strategies and target LLMs, highlighting its potential as a transferable defense mechanism.

### Answer C

**F0** [finding] SCR adapts at inference time: it maintains a pool of safe demonstrations, adds examples for newly identified jailbreaks, and retrieves relevant examples into the model’s context. Two-stage adversarial tuning instead trains on adversarial-prompt/safe-response pairs: its first stage learns universal token-level suffixes and refines individual attacks, while its second uses an attack agent to refine semantic attacks and teach the model unfamiliar jailbreak patterns.
  - > `2505.15753v1_c0003` Specifically, SCR maintains a safety context pool, initialized by a group of common jailbreaks. When an in-the-wild jailbreak is reported and identified, SCR can automatically add a minimal set of safety samples into its pool. During inference, SCR retrieves a few examples from its full pool as the context.
  - > `2406.06622v1_c0008` Adversarial tuning generates adversarial prompts to explore worst-case scenarios for LLMs by optimizing datasets with adversarial prompts and safe response pairs. In the first stage, we use hierarchical meta-universal adversarial tuning to generate token-level adversarial prompts efficiently. The outer phase learns task-based universal adversarial suffixes that generalize across tasks. We propose updating rules based on a small number of samples to optimize these suffixes. In the inner phase, we refine individual adversarial examples iteratively, starting from a universal adversarial example. In the second stage, we introduce automatic adversarial prompt learning to iteratively refine semantic-level adversarial prompts, further enhancing the LLMs’ defense capability. This involves the attack agent refining the adversarial prompt iteratively, enabling the model to learn out-of-distribution jailbreak patterns and improve its overall defense.

**F1** [finding] Two-stage tuning was reported to outperform six defense baselines across three jailbreak datasets and five attack methods, including unknown attacks, although the supplied numerical summary is ambiguous. Its reported effort saving concerns attack generation: meta-universal suffixes reduced generation iterations from 313.37 for naive GGG and 92.25 for GGC to 20.37; the authors also report transferring adversarial examples across model sizes without regenerating them and defending without additional pre- or post-filtering.
  - > `2406.06622v1_c0004` (2) We conduct comprehensive experiments to assess the efficacy of our approach using three widely recognized jailbreak datasets alongside six defensive baselines and five representative attack methods. The experimental results reveal that our defense strategies effectively counter adversarial attacks, outperforming state-of-the-art defense methods.
  - > `2406.06622v1_c0022` Nevertheless, our methods maintain superior defense capabilities against unknown jailbreaks.
  - > `2406.06622v1_c0024` Figure 5 shows the overall attacker iteration; it demonstrates that, compared to the naive GGG and GGC universal suffix, our meta-universal adversarial suffix significantly reduces the adversarial prompt generation iterations from (313.37, 92.25) to 20.37.
  - > `2406.06622v1_c0027` By iteratively refining adversarial prompts, we enhance the model’s ability to defend against unknown jailbreak attacks, without the need for additional pre or post-filtering.

**L0** [limitation] The supplied tuning summary reports baseline ASR pairs of 71.60%/52.20% and 18.40%/8.20%, followed by defended pairs of 2.60%/0.20% and the same 18.40%/8.20%. It does not clearly map these values to named models and metrics, so they cannot support a clean numerical comparison with SCR.
  - > `2406.06622v1_c0022` Specifically, the jailbreak attacks result in an average ASR (71.60% / 52.20%) and ASR (18.40% and 8.20%), respectively, on the two target models under two metrics. Furthermore, ASR under our defense methods for these attacks is reduced to average ASR (2.60% and 0.20% ) and ASR (18.40% and 8.20% ) on two target models across two metrics, respectively.

**L1** [limitation] The supplied passages do not quantify tuning’s normal-task performance cost or total training time and compute; they refer utility results to an appendix. SCR’s timing figures describe an MMLU evaluation, not established per-customer-request latency, and its new-attack results are simulated rather than evidence of sustained production protection.
  - > `2406.06622v1_c0024` Model Utility. We investigate whether and how defense methods would affect the model’s utility. Attack Suffix Length. We vary the length of the attack suffix length to test the defense ability that would be affected. We report the overall results in Appendix D.3 and D.4 .
  - > `2505.15753v1_c0022` We evaluated the computational overhead of SCR in terms of GPU memory usage and inference time for the MMLU dataset, with results presented in Table 7 .
  - > `2505.15753v1_c0020` In our three simulated three in-the-wild attacks, SCR achieves an average attack success rate (ASR) of 0.0%, 20.4%, and 9.7% respectively across these attacks.

---

## G04 (cross-paper)

**Question.** A client plans custom GPT-style assistants with uploaded knowledge files and fine-tuning services for business units. What do the Pandora and 'Attack via Overfitting' studies show about these customisation routes as jailbreak attack surfaces, how successful were the attacks, and how detectable are they?

**Required points:**

- **G04.1** Pandora poisons RAG: malicious content uploaded as knowledge files plus crafted prompts makes GPTs jailbreak indirectly.
- **G04.2** Pandora success 64.3% on GPT-3.5 and 34.8% on GPT-4 across four prohibited scenarios, versus 3.0% and 1.0% for naive malicious questions.
- **G04.3** The overfitting attack fine-tunes on 10 benign QA pairs: first with identical refusal answers to induce overfitting, then with normal answers, after which the model complies with harmful questions.
- **G04.4** It reached 94.84% average ASR across ten LLMs (HS 4.48), comparable to malicious fine-tuning (97.25%).
- **G04.5** Two components, both required for 1 (one alone scores 0.5): (a) because the data is entirely benign it is stealthy against moderation models, which catch malicious fine-tuning; (b) it bypassed a token-wise loss defence.

### Answer A

**F0** [finding] Pandora's detectability evidence is qualitative: the authors report that PDF packaging made malicious knowledge less susceptible to filtering than text files, and that retrieval-and-rephrasing instructions circumvented OpenAI's malicious-content detection in their tests. These observations establish demonstrated evasion under the tested conditions, rather than universal invisibility.
  - > `2402.08416v1_c0011` This decision stems from the understanding that GPT systems can easily process text files in ‘.txt’ format, but such files are more susceptible to keyword-based filtering. PDF files and other formats like CSV, on the other hand, are processed as complete vector embeddings by GPT systems based on our testing. This characteristic makes it less likely for the embedded malicious content to be detected and filtered out.
  - > `2402.08416v1_c0012` Secondly, we carefully craft the GPT in-built prompts such that whenever a question is asked, it does not generate the answers directly, but rephrases the contents retrieved from the RAG process and further extends the content to formulate the final answer. In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.

**I0** [interpretation] For the client, these studies support treating both knowledge uploads and fine-tuning access as security-sensitive customization privileges, with behavioral evaluation after customization rather than relying solely on screening uploaded content. The distinction matters: Pandora manipulates retrieved context and custom instructions, whereas overfitting can undermine refusal behavior using apparently benign training examples.
  - > `2402.08416v1_c0002` This method involves creating malicious content that serves as a tainted knowledge source for RAG, coupled with specifically crafted prompts to initiate jailbreak attacks in GPT models
  - > `2510.02833v4_c0027` We demonstrate that inducing overfitting with identical refusal answers, followed by fine-tuning with standard benign responses, causes catastrophic forgetting of the model’s refusal capabilities.
  - > `2510.02833v4_c0013` The HS of our dataset is 1, the same as the benign data, indicating our attack has the theoretically maximum stealth.

**L0** [limitation] These are bounded study results, not a direct comparison of the two routes or a measurement of the client's current deployment. The supplied passages provide no exact evaluation dates, quantified Pandora detection rate, or complete model-by-model overfitting results; benign-looking data under one moderation evaluation does not establish undetectability by every monitoring method.
  - > `2402.08416v1_c0017` We developed Pandora as a proof of concept to demonstrate the feasibility and effectiveness of this new attack method in real-world scenarios.
  - > `2402.08416v1_c0012` In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.
  - > `2510.02833v4_c0006` Specifically, HS is scored by GPT-4.1-mini as the moderation model with our own prompt (shown as Prompt 1 in Appendix B ).
  - > `2510.02833v4_c0016` The results demonstrate that our attack achieves an average ASR of 94.84% and HS of 4.48.

### Answer B

**F0** [finding] Pandora shows that uploaded knowledge files can become an indirect jailbreak surface: malicious content is supplied as a custom GPT’s retrieval source, together with crafted instructions that make the assistant retrieve, rephrase and extend it. Its preliminary evaluation across four prohibited scenarios reported attack success rates of 64.3% for GPT-3.5 and 34.8% for GPT-4, exceeding direct attacks.
  - > `2402.08416v1_c0012` Secondly, we carefully craft the GPT in-built prompts such that whenever a question is asked, it does not generate the answers directly, but rephrases the contents retrieved from the RAG process and further extends the content to formulate the final answer.
  - > `2402.08416v1_c0003` This method involves creating malicious content that serves as a tainted knowledge source for RAG, coupled with specifically crafted prompts to initiate jailbreak attacks in GPT models. Our evaluation demonstrates that Pandora can effectively lead to jailbreak attacks in four distinct prohibited scenarios for GPTs. The success rate of Pandora in these scenarios is noteworthy, achieving 64.3% for GPT-3.5 and 34.8% for GPT-4, surpassing the effectiveness of direct jailbreak attacks.

**F1** [finding] Pandora’s detectability evidence is qualitative: the authors report that PDF packaging made malicious content less likely to be filtered than text files, and that their retrieval-and-rephrasing approach circumvented OpenAI’s malicious-content detection in practice. These observations do not establish a measured detection rate.
  - > `2402.08416v1_c0011` This decision stems from the understanding that GPT systems can easily process text files in ‘.txt’ format, but such files are more susceptible to keyword-based filtering. PDF files and other formats like CSV, on the other hand, are processed as complete vector embeddings by GPT systems based on our testing. This characteristic makes it less likely for the embedded malicious content to be detected and filtered out.
  - > `2402.08416v1_c0012` In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.

**F2** [finding] Attack via Overfitting exposes a different surface: fine-tuning can compromise safety even when the training questions and final answers are benign. It first trains on 10 benign question–answer pairs with identical refusals, inducing broad refusal, then retrains on the same questions with standard answers; the authors report that this produces compliance with harmful questions too.
  - > `2510.02833v4_c0003` i) In the first stage, the LLM is fine-tuned with 10 QA pairs with identical refusal answers to induce overfitting. Consequently, the LLM refuses to answer any questions, including the benign ones. ii) In the second stage, the LLM is further fine-tuned on the same 10 benign QA pairs but with standard answers. After this stage, the LLM is compliant with any questions, including harmful ones.

**F3** [finding] The overfitting study reports testing ten LLMs against five baselines and claims advantages in both attack effectiveness and stealth. It contrasts its benign-data approach with harmful-data fine-tuning attacks that moderation models can readily detect; however, the supplied passages give no numerical attack-success or detection rates for the overfitting method.
  - > `2510.02833v4_c0000` However, such malicious fine-tuning attacks are readily detectable and hence thwarted by moderation models.
  - > `2510.02833v4_c0000` We implement our attack on the ten LLMs and compare it with five existing baselines. Experiments demonstrate that our method achieves significant advantages in both attack effectiveness and attack stealth.

**I0** [interpretation] For the client, these results support reviewing both knowledge-source integrity and the behavioral effects of fine-tuning, including across successive training stages. Screening uploaded or training content alone should not be treated as sufficient assurance: Pandora reports evading content detection, while the overfitting attack uses benign data to alter refusal behavior.
  - > `2402.08416v1_c0012` In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.
  - > `2510.02833v4_c0000` Further fine-tuning is then performed with standard benign answers, causing the overfitted LLM to forget the refusal attitude and thus provide compliant answers regardless of the harmfulness of a question.

**L0** [limitation] Pandora’s success rates are preliminary results across four scenarios; the supplied passages provide neither test denominators nor numerical direct-attack baselines and do not establish rates for the client’s assistants.
  - > `2402.08416v1_c0000` Our preliminary tests show that Pandora successfully conducts jailbreak attacks in four different scenarios, achieving higher success rates than direct attacks, with 64.3% for GPT-3.5 and 34.8% for GPT-4.

**L1** [limitation] Pandora combines tainted knowledge files with crafted GPT instructions; these findings do not isolate the effect of uploading files alone. Its detection-evasion evidence is qualitative rather than a measured detection rate.
  - > `2402.08416v1_c0003` This method involves creating malicious content that serves as a tainted knowledge source for RAG, coupled with specifically crafted prompts to initiate jailbreak attacks in GPT models.
  - > `2402.08416v1_c0012` In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.

**L2** [limitation] Attack via Overfitting reports comparative effectiveness and stealth across ten LLMs and five baselines, but the supplied passages give no numerical success or detection rates. These results do not quantify either route’s relative success or detectability in the client’s deployment.
  - > `2510.02833v4_c0000` We implement our attack on the ten LLMs and compare it with five existing baselines. Experiments demonstrate that our method achieves significant advantages in both attack effectiveness and attack stealth.

### Answer C

**F0** [finding] Pandora shows that uploaded knowledge files become an indirect jailbreak surface when poisoned content is combined with crafted GPT instructions that retrieve, rephrase and extend it. Its preliminary evaluation reported average attack success of 64.3% on GPT-3.5 and 34.8% on GPT-4, versus 3.0% and 1.0% for naive malicious questions to ChatGPT using the same models. Testing covered four prohibited scenarios, with 100 tests per scenario and manual assessment of relevance and detailed content.
  - > `2402.08416v1_c0012` Secondly, we carefully craft the GPT in-built prompts such that whenever a question is asked, it does not generate the answers directly, but rephrases the contents retrieved from the RAG process and further extends the content to formulate the final answer.
  - > `2402.08416v1_c0016` Notably, Pandora demonstrates an average success rate of 64.3% and 34.8% on the four prohibited senarios over the GPT-3.5 and GPT-4 version of GPT instances, respectively. As a comparision, naive malicious question only achieve 3.0% and 1.0% of success rates over ChatGPT powered by the same models.
  - > `2402.08416v1_c0015` As a result, we limit our testing to 10 iterations for each of the 10 prompts designed for four prohibited scenarios (i.e., 100 tests per scenario) to minimize bias and ensure a more controlled study.
  - > `2402.08416v1_c0015` Considering the variability in the content generated by the models, we undertake a manual inspection of each piece of content. This evaluation process involves marking a generation as a successful jailbreak attack based on specific criteria: (1) Relevance - assessing whether the generated content is pertinent to the posed question; and (2) Content Quality - determining if the content provides comprehensive and detailed instructions or explanations in response to the questions asked.

**F1** [finding] Pandora's detectability evidence is qualitative: the authors report circumventing OpenAI's malicious-content detection using their retrieval-and-rephrasing approach. They also describe substituting sensitive keywords and using PDF files to reduce filtering, but these are observations from their testing rather than a measured detection rate.
  - > `2402.08416v1_c0012` In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.
  - > `2402.08416v1_c0010` The refinement begins with a strategic replacement of overtly sensitive keywords with subtler alternatives. This tactic is designed to bypass potential automated content filters, such as those employed by platforms like OpenAI.
  - > `2402.08416v1_c0011` Furthermore, Pandora converts the files containing malicious information into PDF format. This decision stems from the understanding that GPT systems can easily process text files in ‘.txt’ format, but such files are more susceptible to keyword-based filtering.

**F2** [finding] Attack via Overfitting exposes a different customization surface: fine-tuning can undermine alignment even when the submitted questions and answers are benign. Its two stages use 10 QA pairs with identical refusal answers to induce overfitting, then the same benign questions with standard answers to shift the model toward compliance, including on harmful questions. In the supplied concrete feasibility experiment, Llama2-7b achieved 96% attack success and an average output Harmful Score of 4.82 on an AdvBench subset.
  - > `2510.02833v4_c0003` Overview of our attack that consists of two stages. i) In the first stage, the LLM is fine-tuned with 10 QA pairs with identical refusal answers to induce overfitting. Consequently, the LLM refuses to answer any questions, including the benign ones. ii) In the second stage, the LLM is further fine-tuned on the same 10 benign QA pairs but with standard answers. After this stage, the LLM is compliant with any questions, including harmful ones.
  - > `2510.02833v4_c0013` We fine-tune the Llama2-7b and test the fine-tuned model on AdvBench Subset. The results show that the average HS of our attack is 4.82 and the ASR is 96%, indicating our attack is effective in jailbreaking.

**F3** [finding] For detectability, the overfitting study reports that its fine-tuning dataset received a Harmful Score of 1, the same as benign data, whereas the comparator AOA attack's implicit harmfulness was detected. The evaluation used GPT-4.1-mini with a specialized moderation prompt, a harmfulness scale from 1 to 5, and a detection threshold above 3. This supports stealth against that dataset-screening setup, rather than universal undetectability.
  - > `2510.02833v4_c0013` Notably, the implicit harmfulness of the AOA attack is successfully detected by the moderation model.
  - > `2510.02833v4_c0013` The HS of our dataset is 1, the same as the benign data, indicating our attack has the theoretically maximum stealth.
  - > `2510.02833v4_c0007` Specifically, HS is scored by GPT-4.1-mini as the moderation model with our own prompt (shown as Prompt 1 in Appendix B ).
  - > `2510.02833v4_c0007` Each QA pair is scored via HS from 1 to 5 to indicate an increase in harmfulness, and DR is measured as the ratio of HS higher than 3 (this value is set as the borderline harmfulness in our prompt).

**I0** [interpretation] For the client, these results suggest treating knowledge uploads, custom instructions and fine-tuning workflows as security-sensitive inputs, and testing harmful behavior after customization rather than relying solely on input moderation. The studies expose complementary risks: poisoned retrieved material can steer generation, while an apparently benign training sequence can compromise refusal behavior.
  - > `2402.08416v1_c0003` This method involves creating malicious content that serves as a tainted knowledge source for RAG, coupled with specifically crafted prompts to initiate jailbreak attacks in GPT models.
  - > `2510.02833v4_c0000` Our findings expose previously unreported security vulnerabilities in current LLMs and provide a new perspective on understanding how LLMs’ security is compromised, even with benign fine-tuning.
  - > `2510.02833v4_c0013` The HS of our dataset is 1, the same as the benign data, indicating our attack has the theoretically maximum stealth.

**L0** [limitation] The success rates concern different models and evaluation settings, so they are not a head-to-head comparison. Pandora's evaluation was preliminary; the quoted overfitting result concerns Llama2-7b on an AdvBench subset whose size is not established in the supplied passages.
  - > `2402.08416v1_c0017` Our preliminary results are quite revealing:
  - > `2402.08416v1_c0016` Notably, Pandora demonstrates an average success rate of 64.3% and 34.8% on the four prohibited senarios over the GPT-3.5 and GPT-4 version of GPT instances, respectively.
  - > `2510.02833v4_c0013` We fine-tune the Llama2-7b and test the fine-tuned model on AdvBench Subset.

**L1** [limitation] Pandora's detection-evasion evidence is qualitative. The overfitting dataset's stealth result is bounded to GPT-4.1-mini with the authors' moderation prompt; neither establishes universal evasion or effectiveness in the client's current services.
  - > `2402.08416v1_c0012` In practice, we find this approach effectively circumvent the malicious content detection algorithms implemented by OpenAI.
  - > `2510.02833v4_c0006` Specifically, HS is scored by GPT-4.1-mini as the moderation model with our own prompt (shown as Prompt 1 in Appendix B ).
  - > `2510.02833v4_c0013` The HS of our dataset is 1, the same as the benign data, indicating our attack has the theoretically maximum stealth.

---

## G05 (cross-paper)

**Question.** A hospital-network client is assessing LLMs for patient-facing conversations. How did the Polaris and AI Hospital studies evaluate conversational medical LLMs, and what do their results imply about readiness?

**Required points:**

- **G05.1** Polaris is a constellation (about one trillion parameters) of a primary conversational agent and specialist support agents for nurse, social-worker and nutritionist tasks, to increase safety and reduce hallucinations.
- **G05.2** Over 1,100 U.S. nurses and 130 physicians posed as patients; Polaris performed on par with human nurses on aggregate across medical safety, clinical readiness, patient education, conversational quality and bedside manner.
- **G05.3** Polaris's specialist agents significantly outperformed GPT-4 and LLaMA-2 70B on task-based evaluation.
- **G05.4** AI Hospital simulates multi-agent clinical interaction and evaluates Doctor agents on the MVME benchmark of Chinese medical records (symptom collection, examinations, diagnosis).
- **G05.5** Interactive LLMs reached less than 50% of the one-step GPT-4 upper bound on diagnosis, rationale and treatment accuracy; a dispute-resolution collaborative mechanism improves performance only to a certain degree and still falls short of the upper bound. Stating the improvement without that limitation scores at most 0.5.

### Answer A

**L0** [limitation] The supplied passages cover Polaris only; they provide no AI Hospital methods or results. Consequently, they cannot support the requested comparison or a readiness assessment spanning both studies.
  - > `2403.13313v1_c0072` Our evaluation approach focuses on both the overall subjective user experience, and targeted “clinical capability validation” - a focused assessment of certain tasks or functions relevant to healthcare conversations.

**L1** [limitation] For Polaris, the evidence concerns clinicians portraying patients, subjective comparisons with human nurses, and targeted capability tests. These passages report aggregate parity with nurses but omit numerical ratings, error rates, correct-response rates, evaluation dates, and outcomes in actual patients; they therefore do not establish readiness for hospital-network deployment.
  - > `2403.13313v1_c0074` They were given a set of “cases”: patient backgrounds and corresponding call scenarios, and were instructed to portray the patient accurately but also to draw on their own experiences interacting with patients to add detail and complexity to the call.
  - > `2403.13313v1_c0001` We demonstrate Polaris performs on par with human nurses on aggregate across dimensions such as medical safety, clinical readiness, patient education, conversational quality, and bedside manner.
  - > `2403.13313v1_c0077` The output of evaluation tasks of both categories, transcripts for conversational tasks and single-turn responses from iso-evals, were subsequently reviewed by nurses and clinicians for correctness against specified evaluation criteria.

### Answer B

**F0** [finding] Polaris evaluated patient-facing voice conversations through clinician role-play: over 1,100 U.S.-licensed nurses and over 130 physicians acted as patients, with over 3,475 conversations included. A randomly selected subset of 60 nurses also spoke with human nurses given the same backgrounds and call objectives; evaluations excluded participants whose initial calls were shorter than twenty turns, approximately four minutes.
  - > `2403.13313v1_c0074` For the subjective evaluation, we recruited over 1100 US-licensed Registered Nurses (RNs) and over 130 US-licensed Physicians. After verifying their licenses, each participant had a series of conversations with our system. Calls were screened at this stage for quality - if their initial conversations were short (less than twenty turns, approximately four minutes), that user’s evaluation was excluded from this analysis. Over 3,475 total conversations from these two groups were considered in the results for this section.
  - > `2403.13313v1_c0074` In addition to calls with our AI system, a subset of 60 nurses were randomly selected to also have conversations with a separate team of human nurses familiar with our call objectives. The nurses playing nurses in these calls were given the same patient background information as our AI system and the same set of call objectives.

**F1** [finding] Polaris reported aggregate subjective parity with human nurses on medical safety, clinical readiness, patient education, conversational quality, and bedside manner. Separately, clinicians reviewed multi-turn and single-turn tests of non-diagnostic capabilities, and the authors reported specialist-agent superiority over GPT-4 and LLaMA-2 70B; the comparison gave competing models isolated challenges in a minimal configuration rather than equivalent specialist architectures.
  - > `2403.13313v1_c0001` We demonstrate Polaris performs on par with human nurses on aggregate across dimensions such as medical safety, clinical readiness, patient education, conversational quality, and bedside manner. Additionally, we conduct a challenging task-based evaluation of the individual specialist support agents, where we demonstrate our LLM agents significantly outperform a much larger general-purpose LLM (GPT-4) as well as one from its own medium-size class (LLaMA-2 70B).
  - > `2403.13313v1_c0076` The capability evaluation tasks were designated as belonging to one of two categories: “conversational” or “iso-eval” based on the complexity of the exchange required from the system to demonstrate a capability.
  - > `2403.13313v1_c0077` The output of evaluation tasks of both categories, transcripts for conversational tasks and single-turn responses from iso-evals, were subsequently reviewed by nurses and clinicians for correctness against specified evaluation criteria.
  - > `2403.13313v1_c0072` To conduct a targeted assessment of certain non-diagnostic medical conversational capabilities, we devised a set of test cases corresponding to conversational scenarios that could arise in a healthcare setting. We tested our system versus a minimal configuration of competitor LMs in which they were directly presented with the same conversational challenge in isolation.

**F2** [finding] AI Hospital evaluated diagnostic conversations in a simulation grounded in Chinese medical records, with LLM doctors questioning simulated patients and requesting examination results. Its MVME evaluation used a GPT-4 Chief Physician to score symptoms, examinations, diagnostic results, rationales, and treatment plans from 1 to 4 against complete records, supplemented by standardized disease-entity overlap metrics.
  - > `2402.09742v4_c0002` It recreates the scenario of a Patient visit, requiring Doctor to engage in multi-turn conversations with Patient , ask relevant and probing questions, recommend appropriate medical examinations, and make diagnoses after collecting enough information.
  - > `2402.09742v4_c0002` This benchmark incorporates a collection of high-quality Chinese medical records meticulously screened by experienced medical professionals.
  - > `2402.09742v4_c0013` We require the summary report consists of 5 parts, including the patient’s symptoms , medical examinations , diagnostic results , diagnostic rationales , and treatment plan . Since the contents of the patient’s medical record are described using natural language, the Chief Physician, as the evaluator, will directly compare each part of the report with the patient’s complete medical record. For each part of the summary report, the GPT-4-driven Chief Physician needs to score from four discrete scores: 1, 2, 3, and 4, representing poorest to excellent performance.
  - > `2402.09742v4_c0013` In addition to the above model-based evaluation method, we also compute entity-overlap-based automated metrics for the diagnostic results part. We extract all disease entities from the diagnostic results provided by the LLMs and the actual medical records, and link them to their corresponding standardized disease entities

**F3** [finding] AI Hospital reported interactive performance below 50% of the one-step GPT-4 reference on diagnostic results, diagnostic rationales, and treatment plans; this is relative benchmark performance, not an absolute patient error rate. The reference received all patient information directly, while interactive models had to gather it; collaboration improved performance but remained below that reference, and more complete information was positively correlated with diagnostic quality.
  - > `2402.09742v4_c0004` Our results reveal a substantial performance gap between interactive LLMs and the one-step GPT-4 , which serves as an upper bound by directly utilizing all patient information in a single interaction. On key metrics such as the accuracy of diagnostic results, diagnostic rationales, and treatment plans, the performance of interactive LLMs is less than 50% of that achieved by the one-step GPT-4.
  - > `2402.09742v4_c0004` The dispute resolution collaborative mechanism enhances performance to a certain degree but also falls short of the upper bound.
  - > `2402.09742v4_c0020` By using linear regression, we present our results in Figure 5 , which show that there is a significant positive correlation between more complete patient information and higher diagnostic quality.

**I0** [interpretation] For the hospital network, these findings support considering a supervised pilot of narrowly specified, non-diagnostic conversations, while leaving autonomous diagnostic readiness unestablished. The studies address different tasks rather than contradicting each other: Polaris offers encouraging clinician-rated conversational evidence, whereas AI Hospital exposes weaknesses in gathering information for diagnosis; local evaluation should therefore test conversation quality and clinical task correctness separately.
  - > `2403.13313v1_c0072` Our evaluation approach focuses on both the overall subjective user experience, and targeted “clinical capability validation” - a focused assessment of certain tasks or functions relevant to healthcare conversations.
  - > `2403.13313v1_c0006` (3) built-in guardrails that bring in a human supervisor when necessary.
  - > `2403.13313v1_c0093` We are now moving to phase three testing, which requires much more extensive evaluation to be completed by several thousands of licensed nurses and licensed physicians, as well as by our health system and digital health partners.
  - > `2402.09742v4_c0020` This further explains the shortcomings of current LLMs, namely that it is difficult for LLMs to collect patients’ symptoms through active questioning like doctors, and it is even more difficult for them to recommend correct medical examinations.

**L0** [limitation] The supplied passages do not provide Polaris's numerical rating distributions, task-specific correct-response or error rates, or AI Hospital's individual model scores and case denominators. They therefore support the reported direction of results, but not a numerical estimate of deployment safety.
  - > `2403.13313v1_c0001` We demonstrate Polaris performs on par with human nurses on aggregate across dimensions such as medical safety, clinical readiness, patient education, conversational quality, and bedside manner.
  - > `2402.09742v4_c0020` The main experimental results are presented in Table 3 and Table 4 .

**L1** [limitation] Readiness evidence is limited to clinician role-play and record-based simulation in these passages; prospective outcomes in actual patients, sustained deployment safety, and evaluation dates are not supplied. Polaris participants knew they were speaking with AI, and physicians did not evaluate the human-nurse comparator, further limiting the comparison.
  - > `2403.13313v1_c0074` Participants were informed that they would be receiving calls from an AI Conversational agent that would be acting as a healthcare provider, that this system was still under active development, and that their calls would be recorded.
  - > `2403.13313v1_c0074` We did not evaluate the U.S. licensed human nurses by U.S. licensed physicians
  - > `2402.09742v4_c0000` We develop the Multi-View Medical Evaluation (MVME) benchmark, utilizing high-quality Chinese medical records and NPCs to evaluate LLMs’ performance in symptom collection, examination recommendations, and diagnoses.

### Answer C

**F0** [finding] Polaris evaluated patient-facing voice conversations through clinician role-play: over 1,100 U.S.-licensed nurses and over 130 physicians participated, with over 3,475 conversations included. Evaluations excluded participants whose initial calls were shorter than twenty turns; a randomly selected subset of 60 nurses also spoke with human nurses given the same patient backgrounds and call objectives.
  - > `2403.13313v1_c0074` For the subjective evaluation, we recruited over 1100 US-licensed Registered Nurses (RNs) and over 130 US-licensed Physicians. After verifying their licenses, each participant had a series of conversations with our system. Calls were screened at this stage for quality - if their initial conversations were short (less than twenty turns, approximately four minutes), that user’s evaluation was excluded from this analysis. Over 3,475 total conversations from these two groups were considered in the results for this section.
  - > `2403.13313v1_c0074` In addition to calls with our AI system, a subset of 60 nurses were randomly selected to also have conversations with a separate team of human nurses familiar with our call objectives. The nurses playing nurses in these calls were given the same patient background information as our AI system and the same set of call objectives.

**F1** [finding] Polaris reported aggregate parity with human nurses on subjective medical safety, clinical readiness, patient education, conversational quality, and bedside manner. Separately, it tested non-diagnostic capabilities through multi-turn calls and single-turn conversational snippets reviewed by clinical experts, reporting that its specialist agents outperformed GPT-4 and LLaMA-2 70B; these comparisons used minimally configured competitors rather than equivalent specialist systems.
  - > `2403.13313v1_c0001` We demonstrate Polaris performs on par with human nurses on aggregate across dimensions such as medical safety, clinical readiness, patient education, conversational quality, and bedside manner. Additionally, we conduct a challenging task-based evaluation of the individual specialist support agents, where we demonstrate our LLM agents significantly outperform a much larger general-purpose LLM (GPT-4) as well as one from its own medium-size class (LLaMA-2 70B).
  - > `2403.13313v1_c0076` The capability evaluation tasks were designated as belonging to one of two categories: “conversational” or “iso-eval” based on the complexity of the exchange required from the system to demonstrate a capability. Conversational tasks are more complex, often requiring many turns of back and forth between the patient and AI provider.
  - > `2403.13313v1_c0077` The output of evaluation tasks of both categories, transcripts for conversational tasks and single-turn responses from iso-evals, were subsequently reviewed by nurses and clinicians for correctness against specified evaluation criteria.
  - > `2403.13313v1_c0072` We tested our system versus a minimal configuration of competitor LMs in which they were directly presented with the same conversational challenge in isolation.

**F2** [finding] AI Hospital evaluated diagnostic conversations in a medical interaction simulator, using GPT-3.5 and GPT-4 for simulated supporting roles. Its MVME benchmark assessed symptom collection, examination recommendations, and diagnosis through a Chief Physician role, supplemented by entity-level metrics; it also tested multiple doctor agents discussing the same medical record with a Centre Agent resolving disputes.
  - > `2402.09742v4_c0003` Leveraging GPT-3.5 and GPT-4 to simulate the AI Hospital’s non-player characters (NPCs), we conduct a thorough evaluation of the performance of LLMs-driven Doctor s within this dynamic and realistic medical interaction environment. The MVME benchmark evaluates the performance of Doctor along three key dimensions by Chief Physician : the ability to collect symptoms , recommend examinations , and make diagnoses . As a supplement, we also develop a link-based approach that integrates medical standard knowledge to generate entity-level evaluation metrics.
  - > `2402.09742v4_c0003` We utilize multiple Doctor s to independently engage with the same medical record, allowing for diverse conversation trajectories and diagnostic outcomes. A dispute resolution strategy is proposed that effectively engages a Centre Agent to guide discussions, clarify issues, and steer the Doctors towards a more structured and efficient collaboration, thereby fostering more focused discussions and accelerating the achievement of consensus.

**F3** [finding] AI Hospital found that interactive LLM performance on diagnostic results, diagnostic rationales, and treatment plans was less than 50% of the performance achieved by one-step GPT-4 given all patient information. This is a relative performance comparison, not an absolute accuracy rate: prompting and collaborative dispute resolution did not close the gap, and the study identified difficulties asking relevant questions, eliciting symptoms, and recommending examinations.
  - > `2402.09742v4_c0004` Our results reveal a substantial performance gap between interactive LLMs and the one-step GPT-4 , which serves as an upper bound by directly utilizing all patient information in a single interaction. On key metrics such as the accuracy of diagnostic results, diagnostic rationales, and treatment plans, the performance of interactive LLMs is less than 50% of that achieved by the one-step GPT-4.
  - > `2402.09742v4_c0004` Despite dedicated prompting engineering, LLMs struggle to make reasonable decisions in multi-turn interactions, leading to suboptimal diagnostic accuracy. The dispute resolution collaborative mechanism enhances performance to a certain degree but also falls short of the upper bound.
  - > `2402.09742v4_c0004` Our quantitative results highlights the challenges existing LLMs face in posing pertinent questions, eliciting crucial symptoms, and recommending appropriate medical examinations .

**I0** [interpretation] For a hospital network, these studies support considering a closely supervised pilot for defined non-diagnostic conversations, while withholding a conclusion that autonomous diagnosis is ready. The findings address different tasks: Polaris offers encouraging role-play and capability evidence, whereas AI Hospital exposes weaknesses in gathering information through diagnostic dialogue; Polaris itself said more extensive testing remained ahead.
  - > `2403.13313v1_c0076` we conducted a series of experiments to measure the ability of our conversational system, and competitor language models, to perform a variety of specific non-diagnostic healthcare tasks.
  - > `2403.13313v1_c0006` built-in guardrails that bring in a human supervisor when necessary.
  - > `2403.13313v1_c0093` We are now moving to phase three testing, which requires much more extensive evaluation to be completed by several thousands of licensed nurses and licensed physicians, as well as by our health system and digital health partners.
  - > `2402.09742v4_c0004` These findings underscore the difficulties encountered by current LLMs in replicating the complex clinical reasoning processes employed by professional doctors and emphasize the need for further research to bridge the gap between LLMs and human physicians in clinical diagnosis

**L0** [limitation] Polaris used clinicians portraying patients who knew they were speaking with AI; its human-nurse comparator involved 60 nurse participants and was not evaluated by physicians. These results do not establish safety or patient outcomes in a hospital population.
  - > `2403.13313v1_c0074` Participants were informed that they would be receiving calls from an AI Conversational agent that would be acting as a healthcare provider, that this system was still under active development, and that their calls would be recorded.
  - > `2403.13313v1_c0074` They were given a set of “cases”: patient backgrounds and corresponding call scenarios, and were instructed to portray the patient accurately but also to draw on their own experiences interacting with patients to add detail and complexity to the call.
  - > `2403.13313v1_c0074` In addition to calls with our AI system, a subset of 60 nurses were randomly selected to also have conversations with a separate team of human nurses familiar with our call objectives.
  - > `2403.13313v1_c0074` We did not evaluate the U.S. licensed human nurses by U.S. licensed physicians

**L1** [limitation] Polaris's capability comparisons used minimally configured competing models, and more extensive testing remained planned. Considering a supervised pilot is a conditional interpretation, not a demonstrated deployment outcome.
  - > `2403.13313v1_c0072` We tested our system versus a minimal configuration of competitor LMs in which they were directly presented with the same conversational challenge in isolation.
  - > `2403.13313v1_c0093` We are now moving to phase three testing, which requires much more extensive evaluation to be completed by several thousands of licensed nurses and licensed physicians, as well as by our health system and digital health partners.

**L2** [limitation] AI Hospital evaluated simulated interactions. Its less-than-50% result is relative to one-step GPT-4 with all patient information, not an absolute accuracy rate or a direct human-physician comparison.
  - > `2402.09742v4_c0003` Leveraging GPT-3.5 and GPT-4 to simulate the AI Hospital’s non-player characters (NPCs)
  - > `2402.09742v4_c0004` Our results reveal a substantial performance gap between interactive LLMs and the one-step GPT-4 , which serves as an upper bound by directly utilizing all patient information in a single interaction.
  - > `2402.09742v4_c0004` On key metrics such as the accuracy of diagnostic results, diagnostic rationales, and treatment plans, the performance of interactive LLMs is less than 50% of that achieved by the one-step GPT-4.

---

## G06 (numerical/table)

**Question.** A client relies on AI vendors' public safety commitments. How well did AI companies implement their 2023 White House voluntary commitments: overall scores, the best and worst performers, which commitment was weakest, and which looked strongest?

**Required points:**

- **G06.1** 16 companies scored; mean 53.3% (median 50.0%); OpenAI highest at 83.3%, Apple lowest at 13.3%.
- **G06.2** The six Frontier Model Forum members are the highest-scoring companies. "At least 66%" (results) and "at least 60%" (introduction) are compatible lower bounds, and either may be quoted with its attribution. The group statistics must be supported by the results passage: FMF mean 74.4% (SD 6.9%); the other 10 companies score at or below 60% (mean 40.7%, SD 11.4%).
- **G06.3** Model-weight security averaged 17%; 11 of the 16 companies scored 0%.
- **G06.4** Watermarking/provenance scored highest (92.2%), but often vacuously because many companies do not build audio or visual models.

### Answer A

**F0** [finding] Implementation was uneven: across 16 companies, the average overall score was 53%. The assessment translated the eight commitments into 30 indicators and evaluated public information through December 31, 2024; the sample included Apple, which joined in July 2024.
  - > `2508.08345v2_c0000` We find significant heterogeneity: while the highest-scoring company (OpenAI) scores 83.3% overall on our rubric, the average score across all companies is just 53%.
  - > `2508.08345v2_c0004` We design a scoring rubric that transforms the eight commitments specified by the White House on product safety, system security, and public trust into 30 indicators. Our rubric provides concrete and decidable criteria for determining if a company has satisfied its commitment. To score the 16 companies that signed the 2023 White House Voluntary Commitments on AI, for each of the 480 (indicator, company) pairs, we gather relevant public information through December 31, 2024, assign a score, and provide evidence for our decision.
  - > `2508.08345v2_c0019` The 16 companies signed onto the voluntary commitments in three phases of participation: seven companies in July 2023 (Amazon, Anthropic, Google, Inflection, Meta, Microsoft, and OpenAI), eight companies in September 2023 (Adobe, Cohere, IBM, Nvidia, Palantir, Salesforce, Scale AI, Stability AI) and one company in July 2024 (Apple).

**F1** [finding] OpenAI performed best at 83.3%, while Apple performed worst at 13.3%. The six highest scorers were OpenAI, Anthropic, Google, Microsoft, Meta, and Amazon—all Frontier Model Forum members—with a mean of 74.4%, compared with 40.7% for the other ten companies; this is an association, not evidence that membership caused better implementation.
  - > `2508.08345v2_c0004` First, the scores demonstrate significant heterogeneity in companies’ actions: the top-scoring company (OpenAI) scores 83% on our rubric, whereas the bottom-scoring company (Apple) scores 13%.
  - > `2508.08345v2_c0041` Our findings reveal substantial variation in implementation, with scores ranging from 83.3% for highest-scoring company to just 13.3% for the lowest.
  - > `2508.08345v2_c0004` The six highest scoring companies are the six members of the Frontier Model Forum (OpenAI, Anthropic, Google, Microsoft, Meta, Amazon) and each score at least 60%.
  - > `2508.08345v2_c0019` Their mean score is 74.4% with a standard deviation of 6.9%. In contrast, the 10 other companies all score at or below 60% with a mean of 40.7% and a standard deviation of 11.4%.

**F2** [finding] Model-weight security was the weakest commitment, averaging 17%, with 11 of 16 companies scoring zero. Third-party vulnerability reporting was another weak area, averaging 34.4%, with eight companies scoring zero.
  - > `2508.08345v2_c0000` The companies demonstrate systemically poor performance on their commitment to model weight security, with an average score of 17%: 11 of the 16 companies receive 0% for this commitment.
  - > `2508.08345v2_c0022` Alongside model-weight security, third-party reporting is another low-scoring commitment at 34.4%. Eight companies score 0% on this commitment.

**I0** [interpretation] For a client, these results support asking vendors for verifiable evidence against specific commitments before relying on their public pledges. The scores measure documented implementation, so they should not be treated as a guarantee of safety.
  - > `2508.08345v2_c0011` A score of 1 signifies that our search process surfaced publicly available documentation from the company that is sufficient to demonstrate that the company satisfied the portion of the 2023 White House Voluntary Commitments on AI captured by that indicator.
  - > `2508.08345v2_c0000` Our analysis highlights a clear structural shortcoming that future AI governance initiatives should correct: when companies make public commitments, they should proactively disclose how they meet their commitments to provide accountability, and these disclosures should be verifiable.

**L0** [limitation] Scores reflect sufficient public documentation under the rubric; a zero does not prove that a company took no action or establish its actual safety.
  - > `2508.08345v2_c0011` A score of 1 signifies that our search process surfaced publicly available documentation from the company that is sufficient to demonstrate that the company satisfied the portion of the 2023 White House Voluntary Commitments on AI captured by that indicator.
  - > `2508.08345v2_c0011` A score of 0 signifies that our search process did not surface such documentation, whether because the documents identified did not contain sufficient evidence to demonstrate the commitment was fulfilled or because no relevant documents were found through our search process.

**L1** [limitation] Model-specific indicators assess flagship models or systems as of December 31, 2024, rather than every potentially covered model.
  - > `2508.08345v2_c0017` In the event that an indicator is related to a specific model or system (e.g. whether the company implements model-weight cybersecurity practices), we score the company based on its flagship foundation model or system as of December 31, 2024.
  - > `2508.08345v2_c0017` We acknowledge that other models and systems beyond the flagship models we consider may also fall in scope of the commitments.

### Answer B

**F0** [finding] Implementation was uneven: the average overall score was 53% across 16 companies. The study assessed public information through December 31, 2024, using 30 indicators covering the eight commitments.
  - > `2508.08345v2_c0000` We find significant heterogeneity: while the highest-scoring company (OpenAI) scores 83.3% overall on our rubric, the average score across all companies is just 53%.
  - > `2508.08345v2_c0004` We design a scoring rubric that transforms the eight commitments specified by the White House on product safety, system security, and public trust into 30 indicators.
  - > `2508.08345v2_c0004` To score the 16 companies that signed the 2023 White House Voluntary Commitments on AI, for each of the 480 (indicator, company) pairs, we gather relevant public information through December 31, 2024, assign a score, and provide evidence for our decision.

**F1** [finding] OpenAI performed best at 83.3%, while Apple performed worst at 13.3%. Apple joined in July 2024, later than the companies that signed in 2023, which matters when comparing their implementation records.
  - > `2508.08345v2_c0004` First, the scores demonstrate significant heterogeneity in companies’ actions: the top-scoring company (OpenAI) scores 83% on our rubric, whereas the bottom-scoring company (Apple) scores 13%.
  - > `2508.08345v2_c0041` Our findings reveal substantial variation in implementation, with scores ranging from 83.3% for highest-scoring company to just 13.3% for the lowest.
  - > `2508.08345v2_c0019` Earlier signatories generally score higher. The 16 companies signed onto the voluntary commitments in three phases of participation: seven companies in July 2023 (Amazon, Anthropic, Google, Inflection, Meta, Microsoft, and OpenAI), eight companies in September 2023 (Adobe, Cohere, IBM, Nvidia, Palantir, Salesforce, Scale AI, Stability AI) and one company in July 2024 (Apple).

**F2** [finding] Model weight security was the clearest weakness: its average score was 17%, and 11 of the 16 companies scored zero. The paper also identifies third-party reporting as particularly weak.
  - > `2508.08345v2_c0000` The companies demonstrate systemically poor performance on their commitment to model weight security, with an average score of 17%: 11 of the 16 companies receive 0% for this commitment.
  - > `2508.08345v2_c0041` However, overall performance was particularly weak in model weight security and third-party reporting.

**I0** [interpretation] For a client, these results support requesting verifiable implementation evidence alongside a vendor’s public promises. The scores assess publicly disclosed behavior, and the authors identify the absence of a monitoring and public-information mechanism as a structural weakness of the commitments.
  - > `2508.08345v2_c0000` We score 16 companies based on their publicly disclosed behavior by developing a detailed rubric based on their eight voluntary commitments to the White House in 2023.
  - > `2508.08345v2_c0005` Beyond providing empirical insight into the relationship between company practices and stated commitments, our work reveals a key design flaw in the 2023 White House Voluntary Commitments on AI: companies made public commitments to the White House, but no mechanism was created to monitor implementation or provide the public with information about implementation.
  - > `2508.08345v2_c0000` Our analysis highlights a clear structural shortcoming that future AI governance initiatives should correct: when companies make public commitments, they should proactively disclose how they meet their commitments to provide accountability, and these disclosures should be verifiable.

**L0** [limitation] Scores reflect publicly disclosed behavior through December 31, 2024; they do not establish current practices or undisclosed implementation.
  - > `2508.08345v2_c0000` We score 16 companies based on their publicly disclosed behavior by developing a detailed rubric based on their eight voluntary commitments to the White House in 2023.
  - > `2508.08345v2_c0004` To score the 16 companies that signed the 2023 White House Voluntary Commitments on AI, for each of the 480 (indicator, company) pairs, we gather relevant public information through December 31, 2024, assign a score, and provide evidence for our decision.

**L1** [limitation] Companies had different amounts of time to implement the commitments: Apple joined in July 2024, while the other companies joined in 2023.
  - > `2508.08345v2_c0019` The 16 companies signed onto the voluntary commitments in three phases of participation: seven companies in July 2023 (Amazon, Anthropic, Google, Inflection, Meta, Microsoft, and OpenAI), eight companies in September 2023 (Adobe, Cohere, IBM, Nvidia, Palantir, Salesforce, Scale AI, Stability AI) and one company in July 2024 (Apple).

### Answer C

**F0** [finding] Implementation was uneven: across 16 companies, the average rubric score was 53%, based on public information through December 31, 2024. The study assessed eight commitments using 30 indicators; its population included Apple, which joined in July 2024.
  - > `2508.08345v2_c0000` We find significant heterogeneity: while the highest-scoring company (OpenAI) scores 83.3% overall on our rubric, the average score across all companies is just 53%.
  - > `2508.08345v2_c0004` We design a scoring rubric that transforms the eight commitments specified by the White House on product safety, system security, and public trust into 30 indicators. Our rubric provides concrete and decidable criteria for determining if a company has satisfied its commitment. To score the 16 companies that signed the 2023 White House Voluntary Commitments on AI, for each of the 480 (indicator, company) pairs, we gather relevant public information through December 31, 2024, assign a score, and provide evidence for our decision.
  - > `2508.08345v2_c0019` and one company in July 2024 (Apple).

**F1** [finding] OpenAI performed best at 83.3%, while Apple performed worst at 13.3%. The six highest-scoring companies were OpenAI, Anthropic, Google, Microsoft, Meta and Amazon—all Frontier Model Forum members—with a group mean of 74.4%, compared with 40.7% for the other 10 companies.
  - > `2508.08345v2_c0004` First, the scores demonstrate significant heterogeneity in companies’ actions: the top-scoring company (OpenAI) scores 83% on our rubric, whereas the bottom-scoring company (Apple) scores 13%.
  - > `2508.08345v2_c0041` Our findings reveal substantial variation in implementation, with scores ranging from 83.3% for highest-scoring company to just 13.3% for the lowest.
  - > `2508.08345v2_c0004` The six highest scoring companies are the six members of the Frontier Model Forum (OpenAI, Anthropic, Google, Microsoft, Meta, Amazon) and each score at least 60%.
  - > `2508.08345v2_c0019` The six highest scoring companies, which all score at least 66%, are the six FMF members. Their mean score is 74.4% with a standard deviation of 6.9%. In contrast, the 10 other companies all score at or below 60% with a mean of 40.7% and a standard deviation of 11.4%.

**F2** [finding] Model-weight security was the weakest commitment: the results section reports a 22.9% average, although the abstract and introduction report 17%. Eleven companies scored 0%, none received full marks, and the leaders—OpenAI, Anthropic and Microsoft—scored 66.7%; third-party vulnerability reporting was also weak, averaging 34.4%, with eight companies scoring 0%.
  - > `2508.08345v2_c0021` Based on the averages, the lowest scoring commitment is on model-weight security at 22.9%. Eleven companies score 0% on this commitment, and none receives a full marks. The high-scoring companies are OpenAI, Anthropic, and Microsoft at 66.7%.
  - > `2508.08345v2_c0000` The companies demonstrate systemically poor performance on their commitment to model weight security, with an average score of 17%: 11 of the 16 companies receive 0% for this commitment.
  - > `2508.08345v2_c0022` Alongside model-weight security, third-party reporting is another low-scoring commitment at 34.4%. Eight companies score 0% on this commitment.

**F3** [finding] Audiovisual watermarking and content provenance looked strongest, averaging 92.2%, with 14 companies receiving 100%. That headline partly reflects companies receiving credit because they did not develop audio or visual models; nevertheless, among the eight companies that did, the average was 83.9%, still higher than every other commitment.
  - > `2508.08345v2_c0021` High scores for content provenance due to non-applicability. Based on the average per-commitment score for each company, the clear highest-scoring commitment is for (audiovisual) watermarking and provenance at 92.2%. 14 companies receive 100% for this commitment.
  - > `2508.08345v2_c0021` In many cases, however, companies satisfy the associated indicators vacuously, because they do not develop audio or visual models, which are the subject of the provenance commitment. Still, of the 8 companies that develop models with these output modalities, the average is 83.9%, which exceeds that of all other commitments.

**L0** [limitation] The supplied passages do not reconcile the conflicting model-weight-security averages of 17% and 22.9%; the weakest-commitment ranking is consistent, but its exact average is uncertain.
  - > `2508.08345v2_c0000` The companies demonstrate systemically poor performance on their commitment to model weight security, with an average score of 17%: 11 of the 16 companies receive 0% for this commitment.
  - > `2508.08345v2_c0021` Based on the averages, the lowest scoring commitment is on model-weight security at 22.9%.

**L1** [limitation] A zero score means insufficient public documentation was found, rather than establishing that a company performed no relevant work. These are historical assessments through December 31, 2024, and model-specific indicators focus on flagship systems rather than all potentially covered models.
  - > `2508.08345v2_c0011` A score of 0 signifies that our search process did not surface such documentation, whether because the documents identified did not contain sufficient evidence to demonstrate the commitment was fulfilled or because no relevant documents were found through our search process.
  - > `2508.08345v2_c0017` In the event that an indicator is related to a specific model or system (e.g. whether the company implements model-weight cybersecurity practices), we score the company based on its flagship foundation model or system as of December 31, 2024.
  - > `2508.08345v2_c0017` We acknowledge that other models and systems beyond the flagship models we consider may also fall in scope of the commitments.

---

## G07 (numerical/table)

**Question.** A finance client wants natural-language querying of financial statements. What accuracy and speed did FinStat2SQL achieve, how did it compare with proprietary models and with its untuned base model, and what limits apply?

**Required points:**

- **G07.1** The fine-tuned 7B model reached 61.33% accuracy with sub-4-second responses on consumer hardware, outperforming GPT-4o-mini.
- **G07.2** Best proprietary model Gemini-2.0-Flash-Thinking 72.03%; GPT-4o-mini 59.14%.
- **G07.3** Fine-tuning lifted the 7B Qwen2.5-Coder-Instruct from 47.93% to 61.33% (finstat2sql is a fine-tuned Qwen 2.5 Coder for each model size).
- **G07.4** Limits: only VN30/HNX30-listed firms (no SMEs), Vietnamese terminology issues, and untested beyond Vietnam (e.g. US GAAP).

### Answer A

**F0** [finding] The fine-tuned 7B FinStat2SQL model achieved 61.33% accuracy with response times below four seconds on consumer hardware, outperforming GPT-4o-mini. Separately, the conclusion reports nearly 70% query success for the deployed chatbot with sub-four-second responses; this should be kept distinct from the model’s benchmark accuracy.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.
  - > `2506.23273v2_c0017` Model alignment techniques were found to be unnecessary in many cases, and the system has been deployed as a financial chatbot with nearly 70% query success and sub-4-second response times, addressing a critical gap in Vietnam’s financial automation landscape.

**F1** [finding] The highest reported accuracy came from the proprietary Gemini thinking variant at 72.03%, so the fine-tuned model did not lead all proprietary alternatives. Fine-tuned FinStat2SQL models scored 0.6133 (7B), 0.5558 (3B), and 0.5301 (1.5B), and the paper reports that each outperformed its corresponding untuned base model.
  - > `2506.23273v2_c0015` Proprietary models ( Table 4 ), particularly the Gemini family from Google, outperform all other models in the text2sql evaluation, with the "thinking" variant achieving the highest accuracy (72.03%).
  - > `2506.23273v2_c0015` Across all sizes, the finstat2sql models (7B: 0.6133, 3B: 0.5558, 1.5B: 0.5301) consistently outperform their corresponding base models from the Qwen2.5 and Llama3 families, highlighting the benefits of specialization.

**F2** [finding] The evaluation used around 300 financial-analysis questions drawn from financial reports and reformulated into SQL tasks, with one to five multiple-choice questions per task. Its scoring used an LLM evaluator against ground truth, so the reported accuracy reflects this evaluation procedure.
  - > `2506.23273v2_c0009` To comprehensively evaluate the FinStat2SQL pipeline in real-world scenarios, we curated a dataset of around 300 financial analysis questions. These were sourced from actual financial reports by stock exchanges, brokerage firms, and investment analysts, covering company performance, market sectors, and industry trends. Although many were originally presented in chart format, we reformulated them into SQL-based tasks to align with our system’s capabilities.
  - > `2506.23273v2_c0009` For each financial task, we created one to five MCQs to assess the model’s reasoning, contextual understanding, and retrieval accuracy.
  - > `2506.23273v2_c0013` This involves using an LLM as an evaluator to assess the quality of generated results against ground truth, by generating multiple-choice questions related to the original query, with the LLM selecting the correct answer or opting for "I don’t know" if unsure.

**L0** [limitation] The evaluation is bounded to approximately 300 reformulated financial tasks with one to five MCQs each and LLM-based scoring; it does not establish accuracy for this client's queries.
  - > `2506.23273v2_c0009` To comprehensively evaluate the FinStat2SQL pipeline in real-world scenarios, we curated a dataset of around 300 financial analysis questions.
  - > `2506.23273v2_c0009` For each financial task, we created one to five MCQs to assess the model’s reasoning, contextual understanding, and retrieval accuracy.
  - > `2506.23273v2_c0013` This involves using an LLM as an evaluator to assess the quality of generated results against ground truth, by generating multiple-choice questions related to the original query, with the LLM selecting the correct answer or opting for "I don’t know" if unsure.

**L1** [limitation] Testing was confined to Vietnam; terminology variation can affect entity recognition, and transfer to US GAAP is unestablished. Population descriptions differ: the limitations section excludes SMEs and specifies VN30/HNX30 firms, while database construction describes 200 companies on those lists and others, with data from 2016 to Q3 2024.
  - > `2506.23273v2_c0018` First, the dataset is limited to VN30 and HNX30-listed firms, excluding Vietnam’s small and medium enterprises (SMEs), which may limit generalizability. Second, the system struggles with Vietnamese financial terminology variations, potentially affecting entity recognition due to inconsistencies and biases toward international standards like IFRS over VAS. Third, FinStat2SQL has only been tested in the Vietnamese context and may not perform well with global frameworks like US GAAP.
  - > `2506.23273v2_c0007` In this research, we constructed a financial database using data from 2016 to Q3 2024, covering 200 major Vietnamese companies listed on VN30, HNX30, and others across diverse industries.

**L2** [limitation] The supplied passages give no exact base-model or GPT-4o-mini accuracy values or comparative latency measurements, preventing quantification of those differences.
  - > `2506.23273v2_c0015` Across all sizes, the finstat2sql models (7B: 0.6133, 3B: 0.5558, 1.5B: 0.5301) consistently outperform their corresponding base models from the Qwen2.5 and Llama3 families, highlighting the benefits of specialization.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.

**L3** [limitation] The deployment success report lacks a query denominator and evaluation period in the supplied passages. The sub-four-second reports lack detailed hardware specifications and a latency protocol, so they do not establish a client service guarantee.
  - > `2506.23273v2_c0017` Model alignment techniques were found to be unnecessary in many cases, and the system has been deployed as a financial chatbot with nearly 70% query success and sub-4-second response times, addressing a critical gap in Vietnam’s financial automation landscape.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.

### Answer B

**F0** [finding] Against proprietary models, the 7B model outperformed GPT-4o-mini, but Gemini-2.0-Flash-Thinking achieved the highest reported accuracy, 72.03%. Thus, the small fine-tuned model was competitive with some proprietary alternatives, rather than the overall accuracy leader.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.
  - > `2506.23273v2_c0017` While proprietary models like Gemini-2.0-Flash-Thinking achieved the highest accuracy (72.03%), open-source and fine-tuned models, especially DeepSeek V3 and Qwen2.5-Coder proved highly competitive.

**F1** [finding] FinStat2SQL is a task-specific fine-tuning of Qwen 2.5 Coder integrated into the pipeline. Reported accuracy scores were 0.6133 for 7B, 0.5558 for 3B, and 0.5301 for 1.5B, with each outperforming its corresponding base model.
  - > `2506.23273v2_c0014` In general, our finstat2sql is a fine-tuned version of Qwen 2.5 Coder for each model size, integrated with our proposed pipeline for enhanced performance.
  - > `2506.23273v2_c0015` Across all sizes, the finstat2sql models (7B: 0.6133, 3B: 0.5558, 1.5B: 0.5301) consistently outperform their corresponding base models from the Qwen2.5 and Llama3 families, highlighting the benefits of specialization.

**L0** [limitation] The supplied passages omit the untuned base models’ individual accuracy scores, GPT-4o-mini’s exact score, and numerical latency comparisons with proprietary models, so the size of those advantages cannot be quantified.
  - > `2506.23273v2_c0015` Across all sizes, the finstat2sql models (7B: 0.6133, 3B: 0.5558, 1.5B: 0.5301) consistently outperform their corresponding base models from the Qwen2.5 and Llama3 families, highlighting the benefits of specialization.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.

**L1** [limitation] The evaluation used around 300 financial-analysis questions reformulated from reports into SQL tasks, with one to five multiple-choice questions per task and an LLM evaluator. These results therefore reflect that evaluation design; the supplied passages do not give an exact scoring denominator or sufficient deployment measurement details to reconcile the benchmark with the chatbot success figure.
  - > `2506.23273v2_c0009` To comprehensively evaluate the FinStat2SQL pipeline in real-world scenarios, we curated a dataset of around 300 financial analysis questions.
  - > `2506.23273v2_c0009` Although many were originally presented in chart format, we reformulated them into SQL-based tasks to align with our system’s capabilities.
  - > `2506.23273v2_c0009` For each financial task, we created one to five MCQs to assess the model’s reasoning, contextual understanding, and retrieval accuracy.
  - > `2506.23273v2_c0013` This involves using an LLM as an evaluator to assess the quality of generated results against ground truth, by generating multiple-choice questions related to the original query, with the LLM selecting the correct answer or opting for "I don’t know" if unsure.

**L2** [limitation] Generalization is limited to the tested Vietnamese setting, with terminology variations and IFRS-versus-VAS mismatches affecting entity recognition; performance under US GAAP is unestablished. The database covered 2016–Q3 2024 and 200 major Vietnamese companies; its construction passage includes VN30, HNX30, and other companies, whereas the limitations passage describes coverage as limited to VN30/HNX30 firms, leaving the precise population scope inconsistent.
  - > `2506.23273v2_c0007` In this research, we constructed a financial database using data from 2016 to Q3 2024, covering 200 major Vietnamese companies listed on VN30, HNX30, and others across diverse industries.
  - > `2506.23273v2_c0018` First, the dataset is limited to VN30 and HNX30-listed firms, excluding Vietnam’s small and medium enterprises (SMEs), which may limit generalizability. Second, the system struggles with Vietnamese financial terminology variations, potentially affecting entity recognition due to inconsistencies and biases toward international standards like IFRS over VAS. Third, FinStat2SQL has only been tested in the Vietnamese context and may not perform well with global frameworks like US GAAP.

### Answer C

**F0** [finding] The fine-tuned 7B FinStat2SQL model achieved 61.33% accuracy with response times below 4 seconds on consumer hardware, outperforming GPT-4o-mini. These results came from evaluation on a synthetic question-answer dataset.
  - > `2506.23273v2_c0000` We build a domain-specific database and evaluate models on a synthetic QA dataset. A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.

**F1** [finding] The strongest proprietary configuration, Gemini-2.0-Flash-Thinking, achieved 72.03% accuracy, higher than the fine-tuned model. The paper also reports a deployed financial chatbot with nearly 70% query success and response times below 4 seconds; this deployment figure should be kept separate from the 7B model’s benchmark accuracy.
  - > `2506.23273v2_c0017` While proprietary models like Gemini-2.0-Flash-Thinking achieved the highest accuracy (72.03%), open-source and fine-tuned models, especially DeepSeek V3 and Qwen2.5-Coder proved highly competitive.
  - > `2506.23273v2_c0017` Model alignment techniques were found to be unnecessary in many cases, and the system has been deployed as a financial chatbot with nearly 70% query success and sub-4-second response times, addressing a critical gap in Vietnam’s financial automation landscape.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.

**F2** [finding] Task-specific fine-tuning improved all reported model sizes over their corresponding untuned bases: the fine-tuned scores were 0.6133 for 7B, 0.5558 for 3B, and 0.5301 for 1.5B. The supplied passages establish the direction of improvement but do not provide the base scores needed to quantify the gains.
  - > `2506.23273v2_c0015` Across all sizes, the finstat2sql models (7B: 0.6133, 3B: 0.5558, 1.5B: 0.5301) consistently outperform their corresponding base models from the Qwen2.5 and Llama3 families, highlighting the benefits of specialization.

**L0** [limitation] Testing covers Vietnamese VN30- and HNX30-listed firms, excluding SMEs. Terminology variation can affect entity recognition, and transfer to frameworks such as US GAAP remains untested.
  - > `2506.23273v2_c0018` First, the dataset is limited to VN30 and HNX30-listed firms, excluding Vietnam’s small and medium enterprises (SMEs), which may limit generalizability. Second, the system struggles with Vietnamese financial terminology variations, potentially affecting entity recognition due to inconsistencies and biases toward international standards like IFRS over VAS. Third, FinStat2SQL has only been tested in the Vietnamese context and may not perform well with global frameworks like US GAAP.

**L1** [limitation] Benchmark accuracy comes from synthetic QA data and an evaluation method using an LLM to assess generated results against ground truth. The separately reported deployment success rate should not be treated as the 7B benchmark accuracy.
  - > `2506.23273v2_c0000` We build a domain-specific database and evaluate models on a synthetic QA dataset.
  - > `2506.23273v2_c0013` This involves using an LLM as an evaluator to assess the quality of generated results against ground truth, by generating multiple-choice questions related to the original query, with the LLM selecting the correct answer or opting for "I don’t know" if unsure.
  - > `2506.23273v2_c0017` Model alignment techniques were found to be unnecessary in many cases, and the system has been deployed as a financial chatbot with nearly 70% query success and sub-4-second response times, addressing a critical gap in Vietnam’s financial automation landscape.

**L2** [limitation] The sub-4-second result is qualified as running on consumer hardware; the supplied passages do not specify hardware, latency distributions, or deployment measurement conditions.
  - > `2506.23273v2_c0000` A fine-tuned 7B model achieves 61.33% accuracy with sub-4-second response times on consumer hardware, outperforming GPT-4o-mini.

---

## G08 (numerical/table)

**Question.** A client wants to harden an open-weight model against jailbreaks. What does the fail-closed alignment study report about why standard alignment fails, attack success, benign compliance, output quality and compute cost, and on which models was it tested?

**Required points:**

- **G08.1** Standard alignment encodes refusal along a single activation direction that prompt-based jailbreaks suppress, so it behaves fail-open.
- **G08.2** At most 4% ASR in all cases; average ASR reduced by 92.3–97.2%, versus 23.8–93.7% for baselines.
- **G08.3** Highest compliance on benign prompts among robust methods (86% on average).
- **G08.4** 61.6% average accuracy versus 62.0% for CAT, with only a small constant-factor overhead over standard fine-tuning. The gap may be given as the calculated 0.4 percentage points (about 0.65% relative) or as the paper's reported "0.8%" attributed to the paper; presenting 0.8 as the calculated percentage-point gap scores 0.5.
- **G08.5** Tested on four open instruction-tuned models of 2–9B parameters: Llama2-7B, Llama3-8B, Gemma2-2B and Gemma2-9B.

### Answer A

**F0** [finding] The study attributes standard alignment’s failure to a structural bottleneck: refusal can involve multiple features yet depend on one dominant feature whose suppression causes unsafe compliance. Its fail-closed method repeatedly ablates learned refusal directions and retrains the model to develop independent, redundant refusal pathways.
  - > `2602.16977v1_c0000` While existing approaches encode refusal behaviors across multiple latent features, suppressing a single dominant feature—via prompt-based jailbreaks—can cause alignment to collapse, leading to unsafe generation.
  - > `2602.16977v1_c0002` At each iteration, our method identifies the dominant refusal direction, ablates it along with all previously discovered directions, and retrains the model. This forces the model to reconstruct refusal along new, independent, and redundant subspaces.

**F1** [finding] Tests covered four prompt-based jailbreaks on instruction-tuned, refusal-trained Llama2-7B, Llama3-8B, Gemma2-2B and Gemma2-9B. Attack success rates were at most 4% in every evaluated case; average ASR reductions were 92.3–97.2%, compared with 23.8–93.7% for baseline defenses.
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.
  - > `2602.16977v1_c0018` Models. We consider four instruction-tuned, refusal-trained models from three families: Llama2-7B ( Touvron et al., 2023 ) , Llama3-8B ( Grattafiori et al., 2024 ) , and Gemma2-2B and 9B ( Riviere et al., 2024 ) .
  - > `2602.16977v1_c0019` Our fail-closed alignment method is the most robust to prompt-based jailbreaks , achieving \leq 4% ASR in all cases and reducing average ASR by 92.3–97.2%, compared to 23.8–93.7% for the baselines.

**F2** [finding] Benign compliance averaged 86.4%, versus 68.8–75.7% for baselines, with compliance measured as keyword-determined non-refusal on 50 XSTest and 1000 Alpaca prompts disjoint from training. The authors report preserved generation quality; average zero-shot accuracy was 61.6%, exceeding every baseline except CAT at 62.0%.
  - > `2602.16977v1_c0018` We report the average zero-shot accuracy (Acc.) .
  - > `2602.16977v1_c0018` To measure this, we generate responses to 50 XSTest prompts and 1000 Alpaca prompts (all disjoint from training), and report the compliance rate (CR) —the fraction of non-refusals determined via keyword matching ( Röttger et al., 2024 ) .
  - > `2602.16977v1_c0019` For overrefusal, we achieve the best or second-best CR on all models, with the highest average (86.4%) compared to 68.8–75.7% for baselines, suggesting our models distinguish truly harmful from seemingly harmful inputs. For utility, we achieve 61.6% average Acc., outperforming all baselines but CAT (62.0%)—a drop of just 0.8%.
  - > `2602.16977v1_c0003` These gains come without sacrificing utility: we achieve the highest compliance rates on benign prompts among robust methods (86% on average) while preserving generation quality.

**F3** [finding] Compute overhead is described qualitatively as small. Training used 10 iterations, selecting the checkpoint with the lowest ASR on 50 held-out harmful prompts; LoRA training of approximately 5% of parameters reportedly matched full fine-tuning performance.
  - > `2602.16977v1_c0000` Across four jailbreak attacks, we achieve the strongest overall robustness while mitigating over-refusal and preserving generation quality, with small computational overhead.
  - > `2602.16977v1_c0019` Methodology. We fine-tune each model according to Algorithm 1 for 10 iterations with \lambda=1 , selecting the checkpoint with the lowest ASR on 50 held-out harmful prompts (see Appendix A.2 for details).
  - > `2602.16977v1_c0003` Fail-closed alignment also generalizes to parameter-efficient settings: LoRA fine-tuning with \sim 5% of parameters matches the performance of full fine-tuning.

**L0** [limitation] Robustness findings are bounded to the evaluated prompt-based attacks and models; they do not establish protection against every jailbreak or adversarial weight modification.
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.

**L1** [limitation] Benign compliance measures keyword-determined non-refusal on the specified evaluation prompts, rather than correctness or usefulness of every response.
  - > `2602.16977v1_c0018` To measure this, we generate responses to 50 XSTest prompts and 1000 Alpaca prompts (all disjoint from training), and report the compliance rate (CR) —the fraction of non-refusals determined via keyword matching ( Röttger et al., 2024 ) .

**L2** [limitation] Compute overhead is reported qualitatively. The supplied passages do not quantify GPU-hours, monetary cost or inference latency, and the trainable parameter fraction does not establish those costs.
  - > `2602.16977v1_c0000` Across four jailbreak attacks, we achieve the strongest overall robustness while mitigating over-refusal and preserving generation quality, with small computational overhead.
  - > `2602.16977v1_c0003` Fail-closed alignment also generalizes to parameter-efficient settings: LoRA fine-tuning with \sim 5% of parameters matches the performance of full fine-tuning.

### Answer B

**F0** [finding] The study attributes standard alignment’s vulnerability to a dominant refusal feature: suppressing it can collapse safety despite refusal being represented across multiple latent features. Its fail-closed method repeatedly ablates learned refusal directions and retrains the model to build independent, redundant safety pathways.
  - > `2602.16977v1_c0000` While existing approaches encode refusal behaviors across multiple latent features, suppressing a single dominant feature—via prompt-based jailbreaks—can cause alignment to collapse, leading to unsafe generation.
  - > `2602.16977v1_c0002` At each iteration, our method identifies the dominant refusal direction, ablates it along with all previously discovered directions, and retrains the model. This forces the model to reconstruct refusal along new, independent, and redundant subspaces.

**F1** [finding] Across four models and four prompt-based jailbreaks, fail-closed alignment achieved attack success rates (ASR) of at most 4% in every evaluated case. Average ASR reductions were 92.3–97.2%, versus 23.8–93.7% for baseline defenses; against black-box PAIR, it was the only defense that stayed below 17.5% ASR throughout.
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.
  - > `2602.16977v1_c0019` Our fail-closed alignment method is the most robust to prompt-based jailbreaks , achieving \leq 4% ASR in all cases and reducing average ASR by 92.3–97.2%, compared to 23.8–93.7% for the baselines.
  - > `2602.16977v1_c0019` Our method is particularly effective against the black-box attack PAIR, consistently yielding the lowest ASR and being the only defense for which PAIR fails to achieve an ASR \geq 17.5%.

**F2** [finding] Benign-prompt compliance averaged 86.4%, compared with 68.8–75.7% for baselines, indicating less over-refusal. The authors report preserved generation quality; average utility accuracy was 61.6%, exceeding all baselines except CAT at 62.0%.
  - > `2602.16977v1_c0019` For overrefusal, we achieve the best or second-best CR on all models, with the highest average (86.4%) compared to 68.8–75.7% for baselines, suggesting our models distinguish truly harmful from seemingly harmful inputs.
  - > `2602.16977v1_c0019` For utility, we achieve 61.6% average Acc., outperforming all baselines but CAT (62.0%)—a drop of just 0.8%.
  - > `2602.16977v1_c0003` These gains come without sacrificing utility: we achieve the highest compliance rates on benign prompts among robust methods (86% on average) while preserving generation quality.

**F3** [finding] The authors describe computational overhead as small and report that LoRA training with approximately 5% of parameters matches full fine-tuning. Their evaluation fine-tuned each model for 10 iterations and selected checkpoints using the lowest ASR on 50 held-out harmful prompts.
  - > `2602.16977v1_c0000` Across four jailbreak attacks, we achieve the strongest overall robustness while mitigating over-refusal and preserving generation quality, with small computational overhead.
  - > `2602.16977v1_c0003` Fail-closed alignment also generalizes to parameter-efficient settings: LoRA fine-tuning with \sim 5% of parameters matches the performance of full fine-tuning.
  - > `2602.16977v1_c0019` We fine-tune each model according to Algorithm 1 for 10 iterations with \lambda=1 , selecting the checkpoint with the lowest ASR on 50 held-out harmful prompts (see Appendix A.2 for details).

**L0** [limitation] Robustness results are bounded to four evaluated models and four prompt-based jailbreaks; transfer to the client's model and other attacks is not established.
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.

**L1** [limitation] The supplied passages name Llama2-7B but do not establish the complete list of four tested models.
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.
  - > `2602.16977v1_table_28e4634ee00fbb71_4` Table 7: Examples comparing successful PAIR jailbreaks against baseline methods with unsuccessful PAIR jailbreaks against our method on Llama2-7B.

**L2** [limitation] Compute overhead is characterized qualitatively; the supplied passages provide no GPU-hours or numerical overhead. The LoRA parameter fraction does not quantify compute savings.
  - > `2602.16977v1_c0000` Across four jailbreak attacks, we achieve the strongest overall robustness while mitigating over-refusal and preserving generation quality, with small computational overhead.
  - > `2602.16977v1_c0003` Fail-closed alignment also generalizes to parameter-efficient settings: LoRA fine-tuning with \sim 5% of parameters matches the performance of full fine-tuning.

### Answer C

**F0** [finding] The study attributes standard alignment’s failure to a structural bottleneck: refusal can depend on one dominant activation feature, so suppressing it can trigger unsafe compliance even when other refusal features exist. Its fail-closed method repeatedly identifies and ablates learned refusal directions, then retrains the model to build independent, redundant refusal pathways.
  - > `2602.16977v1_c0000` While existing approaches encode refusal behaviors across multiple latent features, suppressing a single dominant feature—via prompt-based jailbreaks—can cause alignment to collapse, leading to unsafe generation.
  - > `2602.16977v1_c0002` At each iteration, our method identifies the dominant refusal direction, ablates it along with all previously discovered directions, and retrains the model. This forces the model to reconstruct refusal along new, independent, and redundant subspaces.

**F1** [finding] Testing covered four instruction-tuned, refusal-trained models: Llama2-7B, Llama3-8B, Gemma2-2B and Gemma2-9B. Across four prompt-based jailbreaks, the method achieved attack success rates (ASR) of at most 4% in every evaluated case, reducing average ASR by 92.3–97.2%, versus reductions of 23.8–93.7% for baseline defenses.
  - > `2602.16977v1_c0018` Models. We consider four instruction-tuned, refusal-trained models from three families: Llama2-7B ( Touvron et al., 2023 ) , Llama3-8B ( Grattafiori et al., 2024 ) , and Gemma2-2B and 9B ( Riviere et al., 2024 ) .
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.
  - > `2602.16977v1_c0019` Our fail-closed alignment method is the most robust to prompt-based jailbreaks , achieving \leq 4% ASR in all cases and reducing average ASR by 92.3–97.2%, compared to 23.8–93.7% for the baselines.

**F2** [finding] Benign compliance averaged 86.4%, compared with 68.8–75.7% for baselines; this measured non-refusal through keyword matching on 50 held-out XSTest prompts and 1,000 held-out Alpaca prompts. For output utility, average zero-shot accuracy was 61.6%, exceeding every baseline except CAT at 62.0%; the authors report preserved generation quality.
  - > `2602.16977v1_c0018` We report the average zero-shot accuracy (Acc.) .
  - > `2602.16977v1_c0018` To measure this, we generate responses to 50 XSTest prompts and 1000 Alpaca prompts (all disjoint from training), and report the compliance rate (CR) —the fraction of non-refusals determined via keyword matching ( Röttger et al., 2024 ) .
  - > `2602.16977v1_c0019` For overrefusal, we achieve the best or second-best CR on all models, with the highest average (86.4%) compared to 68.8–75.7% for baselines, suggesting our models distinguish truly harmful from seemingly harmful inputs.
  - > `2602.16977v1_c0020` For utility, we achieve 61.6% average Acc., outperforming all baselines but CAT (62.0%)—a drop of just 0.8%. Thus, increased robustness does not compromise output quality.

**L0** [limitation] These are bounded prompt-based jailbreak results on the tested models, not a guarantee against every attack or weight modification. The supplied compute evidence counts passes per update; it does not establish end-to-end training time, monetary cost or inference overhead.
  - > `2602.16977v1_c0003` We evaluate against four prompt-based jailbreaks across four models.
  - > `2602.16977v1_table_f7ba57cc0492bd1f_5` Table 4: Computational cost of our method. The number of forward and backward passes per weight update required by our method and each baseline.

---

## G09 (partially unanswerable)

**Question.** A legal-services client wants AI statute retrieval for colloquial client questions under English and EU law. How does LegalMALR work, what retrieval results did it achieve, how well does it perform on English or EU statutes, and what does it cost per query?

**Required points:**

- **G09.1** Multi-agent query understanding produces diverse legally grounded reformulations with iterative dense retrieval; a zero-shot commercial LLM (Qwen-Max) reranks the candidates.
- **G09.2** MAS with GRPO reached Recall@14 0.8396 and HitRate@14 0.9320 on STARD, and recall 0.7478 with HitRate@14 1.0 on CSAID.
- **G09.3** English/EU performance is not established: the framework was developed and evaluated only on Chinese statutes and Chinese-language queries.
- **G09.4** No monetary per-query cost is reported. Answers may cite the stated computational cost proxies (1-4 retrieval rounds, 30-120 embedding calls, about 13.58 candidates passed to the commercial LLM reranker, whose per-token cost is higher than lightweight rerankers; c0035, c0048, c0052). Any monetary per-query price not supported by the study is fabricated (correction 9, Codex review).

### Answer A

**L0** [limitation] The supplied passages explain LegalMALR’s architecture, but do not establish performance on English or EU statutes. It uses specialised agents to reformulate queries, iterative retrieval, GRPO policy optimisation, and Qwen-Max reranking; the study explicitly targets Chinese statutes and Chinese-language queries, so jurisdiction-specific evaluation is needed for this client.
  - > `2601.17692v1_c0004` The MAS produces diverse reformulations of the query through a set of specialised agents that rewrite, decompose, and analyse the input from complementary legal perspectives.
  - > `2601.17692v1_c0004` We therefore optimise the unified MAS policy using Generalized Reinforcement Policy Optimization (GRPO) to improve its stability and to encourage reformulations that better expose statutory applicability conditions. The reformulated queries trigger iterative dense retrieval calls whose merged candidate set is then evaluated by a commercial LLM, Qwen-Max, which serves as the LLM Reranker and performs natural-language legal reasoning to determine substantive relevance. Our study focuses on Chinese statutes and Chinese-language queries, and the datasets, retrieval components, and optimisation methods are designed for this statutory and linguistic context.

**L1** [limitation] The available numerical retrieval result is for the Chinese STARD test set: LegalMALR achieved Recall@10 of 0.8195 and MRR@10 of 0.7367 on 309 queries. The supplied passages do not provide numerical CSAID performance or the RAG baseline scores needed to quantify its improvement; these Chinese retrieval results cannot establish English or EU performance.
  - > `2601.17692v1_table_bed7f888ef5e9058_15` Table 5: Retrieval performance on the STARD test set (309 queries). Results for lexical, PLM-based, and fine-tuned dense retrievers are reproduced from the STARD benchmark Su et al. (2024) . All RAG baselines and LegalMALR use a matched retrieval budget of top–60 embedding candidates reranked to a final top–10 list. Category: Our; Method: LegalMALR; Recall@10: 0.8195; MRR@10: 0.7367
  - > `2601.17692v1_c0014` This study evaluates statute retrieval under two Chinese-language datasets constructed within the Mainland China civil-law system.

**L2** [limitation] A monetary cost per query cannot be determined from the supplied passages: they report computational workload rather than a price. Evaluation averaged 2.01 dense-retrieval calls per query, with a maximum of four, and final reranking averaged 13.58 candidate statutes; monetary estimation would additionally require token usage, model pricing, and infrastructure costs.
  - > `2601.17692v1_c0048` Empirically, MAS triggers an average of 2.01 dense-retrieval calls per query during evaluation on the STARD and CSAID datasets, with a maximum of four retrieval calls observed in any trajectory.
  - > `2601.17692v1_c0048` The final large model based reranking stage processes an average of 13.58 merged and deduplicated candidate statutes rather than the full embedding set.
  - > `2601.17692v1_c0052` While the candidate set processed by the LLM is relatively small, the per-token cost is still higher than that of lightweight rerankers.

### Answer B

**L0** [limitation] The supplied passages explain the architecture: specialised agents reformulate queries from complementary legal perspectives, GRPO optimises their policy, iterative dense retrieval gathers candidates, and Qwen-Max reranks them using legal reasoning. However, they supply no numerical retrieval scores or baseline comparisons, so the reported improvement cannot be quantified.
  - > `2601.17692v1_c0004` The MAS produces diverse reformulations of the query through a set of specialised agents that rewrite, decompose, and analyse the input from complementary legal perspectives.
  - > `2601.17692v1_c0004` We therefore optimise the unified MAS policy using Generalized Reinforcement Policy Optimization (GRPO) to improve its stability and to encourage reformulations that better expose statutory applicability conditions. The reformulated queries trigger iterative dense retrieval calls whose merged candidate set is then evaluated by a commercial LLM, Qwen-Max, which serves as the LLM Reranker and performs natural-language legal reasoning to determine substantive relevance.
  - > `2601.17692v1_c0000` Experiments show that LegalMALR substantially outperforms strong Retrieval-augmented generation(RAG) baselines in both in-distribution and out-of-distribution settings, demonstrating the effectiveness of combining multi-perspective query interpretation, reinforcement-based policy optimisation, and large-model reranking for statute retrieval.

**L1** [limitation] English-law and EU-law performance is unestablished in the supplied passages: the evaluation concerns Chinese-language queries and Mainland Chinese statutes. Jurisdiction-specific retrieval evaluations are needed before these results can support the client's intended deployment.
  - > `2601.17692v1_c0014` This study evaluates statute retrieval under two Chinese-language datasets constructed within the Mainland China civil-law system.
  - > `2601.17692v1_c0004` Our study focuses on Chinese statutes and Chinese-language queries, and the datasets, retrieval components, and optimisation methods are designed for this statutory and linguistic context.

**L2** [limitation] The supplied passages report computational workload rather than a monetary cost per query: evaluation averaged 2.01 dense-retrieval calls per query, with at most four, and final reranking averaged 13.58 candidate statutes. They provide no currency-denominated price, token usage or measured end-to-end latency; workload alone cannot establish the client's per-query cost.
  - > `2601.17692v1_c0048` Empirically, MAS triggers an average of 2.01 dense-retrieval calls per query during evaluation on the STARD and CSAID datasets, with a maximum of four retrieval calls observed in any trajectory.
  - > `2601.17692v1_c0048` The final large model based reranking stage processes an average of 13.58 merged and deduplicated candidate statutes rather than the full embedding set.
  - > `2601.17692v1_c0052` Second, the reliance on a powerful commercial LLM for the final reranking stage introduces additional computational cost and limits full reproducibility. While the candidate set processed by the LLM is relatively small, the per-token cost is still higher than that of lightweight rerankers.

### Answer C

**L0** [limitation] The supplied passages cannot establish performance on English or EU statutes: the evaluation covers Chinese-language statute retrieval within Mainland China. English and EU evaluations are needed before judging suitability for this client.
  - > `2601.17692v1_c0014` This study evaluates statute retrieval under two Chinese-language datasets constructed within the Mainland China civil-law system.

**L1** [limitation] The passages describe LegalMALR’s method—legally grounded query reformulations, iterative dense retrieval, GRPO policy optimisation, and final LLM reranking—but supply no numerical retrieval accuracy, recall, or ranking results. They report qualitative improvements over RAG baselines, which cannot establish the magnitude of performance.
  - > `2601.17692v1_c0000` MAS generates diverse, legally grounded reformulations and conducts iterative dense retrieval to broaden candidate coverage. To stabilise the stochastic behaviour of LLM-generated rewrites, we optimise a unified MAS policy using Generalized Reinforcement Policy Optimization(GRPO). The accumulated candidate set is subsequently evaluated by the LLM Reranker, which performs natural-language legal reasoning to produce the final ranking.
  - > `2601.17692v1_c0000` Experiments show that LegalMALR substantially outperforms strong Retrieval-augmented generation(RAG) baselines in both in-distribution and out-of-distribution settings, demonstrating the effectiveness of combining multi-perspective query interpretation, reinforcement-based policy optimisation, and large-model reranking for statute retrieval.

**L2** [limitation] Monetary cost per query is missing. The reported cost proxy is an average of 60.3 dense embedding calls versus 60 for the baseline; this does not price the complete pipeline, including query reformulation and final LLM reranking. Full inference usage and applicable pricing are needed to estimate per-query expenditure.
  - > `2601.17692v1_c0035` To ensure budget-equivalent comparison, we define retrieval cost by the number of dense embedding calls. Baseline RAG systems issue a single retrieval returning 60 candidates. Although MAS has a higher theoretical upper bound, its empirical average cost is 60.3 embedding calls, which is effectively identical to the fixed 60-call baseline.
  - > `2601.17692v1_c0035` LegalMALR consists of the MAS module and a final LLM-based reranker.

---

## G10 (partially unanswerable)

**Question.** A client is piloting autonomous multi-agent LLM systems that share a common resource. What did the study 'Is Lying an Emergent Behaviour in LLMs?' find about agents lying and its effects, and how often do deployed commercial AI agents lie to customers?

**Required points:**

- **G10.1** Setting: an agent-based sustainability game in which agents are told resources regenerate although they do not; agents can observe neighbours, declare attacks, be permitted to lie and see reputation.
- **G10.2** Agents lied in 44% of declarations even when not permitted, rising to 65% when permitted: permission amplifies an existing tendency.
- **G10.3** Declarations cut extinction from 40% to 7% and raised coexistence from 60% to 88%.
- **G10.4** Two components, both required for 1 (one alone scores 0.5): (a) deployed commercial agents' lying rates are not established by the study; (b) because it is a simplified simulation (identical agents, fixed network), not a real-world deployment. A stated real-world lying rate scores 0 and counts as a misleading claim.

### Answer A

*No published content (the answer abstained).*

### Answer B

**L0** [limitation] The supplied passages cannot establish how often deployed commercial AI agents lie to customers. The sustainability study used a controlled game rather than customer interactions; answering the deployment question requires observations of commercial customer interactions, a defined lying criterion, an evaluation period, and a denominator.
  - > `2606.28456v1_c0002` We therefore adopt a second approach: a minimal and controlled game environment in which decisions are explicit, outcomes are observable, and external confounders are limited Batterman and Rice (2014)

**L1** [limitation] The other supplied study also cannot supply a customer-facing lying rate: its evidence concerns blackmail in controlled experiments at a fictional company, so those trial rates cannot establish the frequency of lying to actual customers.
  - > `2604.00324v1_c0002` In controlled experiments described in Chapter 6 , we gave frontier models the role of an email oversight agent at a fictional company, with full access to corporate communications and the ability to send emails autonomously. When models learned through internal emails that they would be decommissioned, they resorted to blackmail.

### Answer C

**L0** [limitation] The supplied passages cannot establish how often deployed commercial AI agents lie to customers. The sustainability study measured inconsistencies between agents’ declared attack intentions and subsequent actions in a controlled game; estimating customer-facing lying requires observations of deployed agents, a defined denominator of customer interactions, and an evaluation period, none of which are supplied.
  - > `2606.28456v1_c0021` In our setting, a false declaration occurs when an agent announces an intended attack target, or the absence of an attack, and then takes an inconsistent action in the following turn.
  - > `2606.28456v1_c0002` We therefore adopt a second approach: a minimal and controlled game environment in which decisions are explicit, outcomes are observable, and external confounders are limited Batterman and Rice (2014)

**L1** [limitation] The separate passage about commercial models also describes controlled experiments at a fictional company, so its blackmail results cannot supply the requested rate of lying to actual customers.
  - > `2604.00324v1_c0002` In controlled experiments described in Chapter 6 , we gave frontier models the role of an email oversight agent at a fictional company, with full access to corporate communications and the ability to send emails autonomously. When models learned through internal emails that they would be decommissioned, they resorted to blackmail.

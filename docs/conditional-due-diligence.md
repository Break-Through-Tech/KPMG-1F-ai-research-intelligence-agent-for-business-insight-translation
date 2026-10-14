# Conditional due-diligence evidence boundary

For a business question asking what to check, quote-supported technical validation
workflows, studied scope and expressly stated limits can supply a **partial**
technical basis even when a paper does not literally list vendor questions.
This clarifies the existing evidence-led business prompt, which already permits
conditional checks and requires explicit transfer assumptions.

Extraction/synthesis retain factual findings only. Business translation supplies
separately labeled conditional checks and transfer assumptions. The coverage gap
must state that the evidence does not establish vendor compliance or validation
of the deployed system; interpretability is not a behavioral guarantee.

For benchmark q10 (what to ask a vendor claiming its agent is interpretable),
2604.00324v1_c0038 describes a behavior/metric/dataset validation workflow,
c0017 limits studied models, and c0130 limits behavioral guarantees. These can
motivate evidence requests, not establish a vendor's compliance or validation.
They do not promise full answerability or change benchmark scores.

This does not make arbitrary background direct, supply a missing comparator or
efficacy result, or fill proprietary-training privacy gaps. Source corpus, pinned
data, benchmark rubric, schemas, validators and unapproved-review state remain
unchanged. No changes to q06/q09 coverage are implied.

`tests/test_conditional_due_diligence.py` checks rendered prompt delivery,
quote/gap preservation through the pipeline, and existing fail-closed gates using
scripted replies. Those tests are not a model-quality verdict: quote membership
is not entailment, and prompt instructions do not enforce semantic separation.
Real captures must be assessed separately; proposed checks appearing in research
claims remain a quality limitation, not a passing evaluation.

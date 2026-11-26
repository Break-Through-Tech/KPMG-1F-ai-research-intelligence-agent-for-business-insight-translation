"""Opt-in publication policy: claims the writer labels "interpretation" are never published as verified.

Why: the synthesis contract treats an interpretation's quotes as premises, not proof, so "supported" from the
model verifier is the only gate. That gate passed a misattributed F01 interpretation in every live run, and an
in-verifier scope check did not catch it either (Stage A v4: both scopes labelled "framework performance").
Withholding is deterministic, so a model judgment cannot override it.

After the existing verifier decides, every accepted interpretation becomes held with a policy reason. Findings,
limitations, exact quotes, number checks and verifier verdicts are untouched. Held claims stay in held_claims with
their reason, so a reviewer can still read them as unverified commentary. Coverage stays honest. If nothing
accepted remains, it is "none". If an interpretation was withheld from a "full" answer, it becomes "partial", with a
note that an explanation was withheld, because the question may have asked for one.

shortcut: relies on the writer's own finding/interpretation label; an explanation mislabelled as a finding is
still judged as a finding (quote, number and verifier checks only). Upgrade with a causal-language screen if seen.
"""
REASON = 'interpretation withheld by policy: explanations are not independently verifiable'


def apply(output):
    """Hold accepted interpretations in a VerificationAgent 'ok' output. Returns the number withheld."""
    withheld = 0
    for row in output['claims']:
        if row.get('kind') == 'interpretation' and row.get('decision') == 'accepted':
            row.update(decision='held', held_reason=REASON, needs_human_number_check=False)
            withheld += 1
    if withheld:
        accepted = any(row.get('decision') == 'accepted' for row in output['claims'])
        output['coverage'] = 'partial' if accepted and output['coverage'] != 'none' else 'none'
        output['missing_aspects'] = list(output['missing_aspects']) + [
            f'{withheld} interpretation(s) withheld by policy; findings are unaffected']
    output['interpretations_withheld'] = withheld
    return withheld


def enable(engine):
    """Opt in on a constructed OrchestratorAgent or EvidenceHandoffOrchestrator."""
    run = engine.verifier.run

    def run_with_policy(task, budget):
        status, output = run(task, budget)
        if status == 'ok':
            apply(output)
        return status, output
    engine.verifier.run = run_with_policy
    return engine

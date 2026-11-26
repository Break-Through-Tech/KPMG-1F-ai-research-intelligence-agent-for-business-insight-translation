"""Opt-in: corrected number check (numeric_checks_v2 + the statistical-report rule) and the labelled-interpretation
gate on a constructed OrchestratorAgent. agents.py, numeric_checks.py and interpretation_policy.py stay unchanged.

enable(orchestrator) patches agents.ground_claim / agents.screen_business process-wide (like
statistical_reports.enable) and wraps the verifier. Interpretations are never published as findings: an accepted
interpretation is held, and one that passes every gate rule (interpretation_gate.G1-G7) is moved to
summary['interpretations'] with its label instead of held_claims.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import interpretation_gate  # noqa: E402

_v2 = None
_saved = None


def load_v2():
    """numeric_checks_v2 with statistical_reports applied to it (not to the frozen module)."""
    global _v2
    if _v2 is None:
        spec = importlib.util.spec_from_file_location('numeric_checks_v2', HERE / 'numeric_checks_v2.py')
        v2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(v2)
        previous = sys.modules.get('numeric_checks')
        sys.modules['numeric_checks'] = v2
        try:
            spec = importlib.util.spec_from_file_location('statistical_reports_v2', HERE.parent / 'agentic/statistical_reports.py')
            stat = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(stat)
            stat.enable()
        finally:
            if previous is not None:
                sys.modules['numeric_checks'] = previous
        _v2 = v2
    return _v2


def gate_output(output, payload, v2):
    """Apply the gate to one verifier output in place. Returns the number published as labelled interpretations."""
    claims = payload['claims']
    rows = output['claims']
    verified = [r['text'] for r in rows if r.get('decision') == 'accepted' and r.get('kind') != 'interpretation']
    by_id = {p['chunk_id']: p for p in payload['passages']}
    published = moved = 0
    for row in rows:
        if row.get('kind') != 'interpretation':
            continue
        if row.get('decision') == 'accepted':
            moved += 1
        claim = claims[row['index']]
        cited = [by_id[c] for c in claim.get('chunk_ids', []) if c in by_id]
        failed = interpretation_gate.gate(row, claim, v2, cited, verified)
        row['interpretation_gate'] = failed or 'passed'
        if failed:
            row.update(decision='held', held_reason='interpretation gate: ' + ' '.join(failed))
        else:
            row.update(decision='held', held_reason='published separately as a labelled interpretation')
            published += 1
    if moved:
        accepted = any(r.get('decision') == 'accepted' for r in rows)
        output['coverage'] = 'partial' if accepted and output['coverage'] != 'none' else 'none'
    output['interpretations_published'] = published
    return published


def enable(orchestrator):
    global _saved
    import agents
    v2 = load_v2()
    if _saved is None:
        _saved = (agents.ground_claim, agents.screen_business)
    agents.ground_claim, agents.screen_business = v2.ground_claim, v2.screen_business
    verify = orchestrator.verifier.run

    def run_with_gate(task, budget):
        status, output = verify(task, budget)
        if status == 'ok':
            gate_output(output, task['payload'], v2)
        return status, output
    orchestrator.verifier.run = run_with_gate
    run = orchestrator.run

    def run_and_label(question, **kwargs):
        result = run(question, **kwargs)
        summary = result.get('summary') or {}
        held = summary.get('held_claims') or []
        passed = [c for c in held if (c.get('verification') or {}).get('interpretation_gate') == 'passed']
        if passed:
            summary['interpretations'] = [{**c, 'label': interpretation_gate.LABEL} for c in passed]
            summary['held_claims'] = [c for c in held if c not in passed]
        return result
    orchestrator.run = run_and_label
    return orchestrator


def disable():
    global _saved
    import agents
    if _saved is not None:
        agents.ground_claim, agents.screen_business = _saved
        _saved = None

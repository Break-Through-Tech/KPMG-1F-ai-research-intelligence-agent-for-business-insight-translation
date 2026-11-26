"""Totals, failure breakdown and the frozen acceptance criteria from scores.json + mechanics.json (0 model calls)."""
import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
scores = json.loads((HERE / 'scores.json').read_text(encoding='utf-8'))['points']
mech = json.loads((HERE / 'mechanics.json').read_text(encoding='utf-8'))
ARMS = ('B0', 'B1', 'M1')
QS = sorted({p.split('.')[0] for p in scores})
assert len(scores) == 44


def per_q(arm, zero=()):
    out = {q: 0.0 for q in QS}
    for pid, v in scores.items():
        q = pid.split('.')[0]
        out[q] += 0 if q in zero else v[arm][0]
    return out


def full(arm, zero=()):
    return sum(1 for q in QS if q not in zero and all(v[arm][0] == 1 for p, v in scores.items() if p.startswith(q)))


res = {}
for arm in ARMS:
    first_fail = mech[arm]['first_pass_failed_questions']
    common_first = [q for q in QS if not any(q in mech[a]['first_pass_failed_questions'] for a in ARMS)]
    lost = Counter()
    for v in scores.values():
        s = v[arm]
        if s[0] < 1:
            lost[s[1]] += 1 - s[0]
    res[arm] = {
        'points_after_resume': sum(per_q(arm).values()),
        'full_answers_after_resume': full(arm),
        'points_first_pass_timeouts_zero': sum(per_q(arm, first_fail).values()),
        'full_answers_first_pass': full(arm, first_fail),
        'common_first_pass_questions': common_first,
        'points_on_common_first_pass': sum(v for q, v in per_q(arm).items() if q in common_first),
        'per_question': per_q(arm),
        'points_lost_by_cause': dict(lost),
        'execution_failures_first_pass': len(first_fail),
        'execution_errors_after_resume': len(mech[arm]['final_execution_errors']),
        'median_s': mech[arm]['median_s_final_attempt'], 'p90_s': mech[arm]['p90_s_final_attempt'],
        'median_s_incl_failed_attempt': mech[arm]['median_s_incl_failed_attempt'],
        'p90_s_incl_failed_attempt': mech[arm]['p90_s_incl_failed_attempt'],
        'request_tokens_per_q': mech[arm]['mean_request_tokens_per_q'], 'calls': mech[arm]['calls']}

b0, b1, m1 = (res[a] for a in ARMS)
crit_b1 = {
    'points >= B0 + 3.5': b1['points_after_resume'] >= b0['points_after_resume'] + 3.5,
    'full answers >= B0': b1['full_answers_after_resume'] >= b0['full_answers_after_resume'],
    'median <= 1.5 x B0': b1['median_s'] <= 1.5 * b0['median_s'],
    'p90 <= 120 s': b1['p90_s'] <= 120,
    'request tokens <= 3 x B0': b1['request_tokens_per_q'] <= 3 * b0['request_tokens_per_q']}
bstar = 'B1' if all(crit_b1.values()) else 'B0'
bs = res[bstar]
crit_m1 = {
    f'points >= {bstar} + 4.4': m1['points_after_resume'] >= bs['points_after_resume'] + 4.4,
    f'more full answers than {bstar}': m1['full_answers_after_resume'] > bs['full_answers_after_resume'],
    'median <= 120 s': m1['median_s'] <= 120, 'p90 <= 300 s': m1['p90_s'] <= 300,
    '<= 1 execution error after one resume': m1['execution_errors_after_resume'] <= 1}
out = {'arms': res, 'B1_criteria': crit_b1, 'B1_qualifies': all(crit_b1.values()), 'B_star': bstar,
       'M1_criteria': crit_m1, 'M1_qualifies': all(crit_m1.values()),
       'latency_note': 'Criteria use the runner-recorded wall time of the completed attempt (rules.json). Times '
                       'including the failed first attempt are reported alongside.'}
(HERE / 'results.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print(json.dumps({k: v for k, v in out.items() if k != 'arms'}, indent=1))
for a in ARMS:
    print(a, {k: v for k, v in res[a].items() if k not in ('per_question',)})

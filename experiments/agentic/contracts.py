"""Structured contracts for the experimental agentic research mode.

Every agent exchange is a Task message from the orchestrator and a Reply from the agent.
Both are plain JSON-compatible dicts so the trace can be stored, rendered and audited.
LLM outputs are validated against the JSON schemas below before any decision uses them.
"""
import itertools
import time

MAX_SUBQUESTIONS = 3
MAX_QUERY_CHARS = 300

# ---------------------------------------------------------------- orchestrator plan
PLAN_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['question_type', 'subquestions', 'business', 'chart', 'notes'],
    'properties': {
        'question_type': {'type': 'string', 'enum': [
            'single_fact', 'comparison', 'multi_part', 'table_or_chart', 'business_application', 'other']},
        'subquestions': {'type': 'array', 'minItems': 0, 'maxItems': MAX_SUBQUESTIONS, 'items': {
            'type': 'object', 'additionalProperties': False, 'required': ['query', 'purpose'],
            'properties': {'query': {'type': 'string', 'minLength': 5, 'maxLength': MAX_QUERY_CHARS},
                           'purpose': {'type': 'string', 'minLength': 1, 'maxLength': 200}}}},
        'business': {'type': 'object', 'additionalProperties': False,
                     'required': ['delegate', 'industry_in_question', 'reason'],
                     'properties': {'delegate': {'type': 'boolean'},
                                    'industry_in_question': {'type': 'string', 'maxLength': 80},
                                    'reason': {'type': 'string', 'minLength': 1, 'maxLength': 300}}},
        'chart': {'type': 'object', 'additionalProperties': False, 'required': ['delegate', 'reason'],
                  'properties': {'delegate': {'type': 'boolean'},
                                 'reason': {'type': 'string', 'minLength': 1, 'maxLength': 300}}},
        'notes': {'type': 'string', 'maxLength': 300}}}

# ---------------------------------------------------------------- verification agent
VERDICTS = ('supported', 'partially_supported', 'unsupported', 'contradicted')
ISSUES = ('missing_support', 'contradiction', 'numeric_misread', 'unit_mismatch', 'reversed_comparison',
          'denominator_error', 'missing_condition', 'unsupported_comparison', 'overgeneralization')


def verification_schema(claim_count):
    return {
        'type': 'object', 'additionalProperties': False,
        'required': ['verdicts', 'coverage', 'missing_aspects', 'retrieval_request'],
        'properties': {
            'verdicts': {'type': 'array', 'minItems': claim_count, 'maxItems': claim_count, 'items': {
                'type': 'object', 'additionalProperties': False,
                'required': ['index', 'verdict', 'issues', 'reason'],
                'properties': {
                    'index': {'type': 'integer', 'minimum': 0, 'maximum': max(claim_count - 1, 0)},
                    'verdict': {'type': 'string', 'enum': list(VERDICTS)},
                    'issues': {'type': 'array', 'maxItems': len(ISSUES), 'uniqueItems': True,
                               'items': {'type': 'string', 'enum': list(ISSUES)}},
                    'reason': {'type': 'string', 'minLength': 1, 'maxLength': 600}}}},
            'coverage': {'type': 'string', 'enum': ['full', 'partial', 'none']},
            'missing_aspects': {'type': 'array', 'maxItems': 3, 'items': {'type': 'string', 'minLength': 1, 'maxLength': 200}},
            'retrieval_request': {'type': 'object', 'additionalProperties': False,
                                  'required': ['needed', 'query', 'reason'],
                                  'properties': {'needed': {'type': 'boolean'},
                                                 'query': {'type': 'string', 'maxLength': MAX_QUERY_CHARS},
                                                 'reason': {'type': 'string', 'maxLength': 300}}}}}


def validate_json(instance, schema):
    from jsonschema import Draft202012Validator
    Draft202012Validator(schema).validate(instance)
    return instance


# ---------------------------------------------------------------- messages and trace
class Trace:
    """Append-only audit log of every delegation, tool use, model call and routing decision."""

    def __init__(self, max_steps):
        self.max_steps = max_steps
        self.entries = []
        self._ids = itertools.count(1)

    def task(self, to, kind, payload):
        if sum(1 for e in self.entries if e['type'] == 'task') >= self.max_steps:
            raise StepLimit(f'Step limit of {self.max_steps} delegations reached.')
        message = {'task_id': f't{next(self._ids)}', 'from': 'orchestrator', 'to': to, 'kind': kind,
                   'payload': payload, 'sent_at': time.time()}
        self.entries.append({'type': 'task', **message})
        return message

    def reply(self, task, status, output, *, seconds, model_calls=0, checks=None):
        entry = {'type': 'reply', 'task_id': task['task_id'], 'from': task['to'], 'to': 'orchestrator',
                 'status': status, 'output': output, 'seconds': round(seconds, 3), 'model_calls': model_calls}
        if checks is not None:
            entry['checks'] = checks
        self.entries.append(entry)
        return entry

    def decision(self, name, run, reason, **extra):
        entry = {'type': 'decision', 'actor': 'orchestrator', 'decision': name, 'run': bool(run), 'reason': reason, **extra}
        self.entries.append(entry)
        return entry

    def decisions(self):
        return [e for e in self.entries if e['type'] == 'decision']


class StepLimit(RuntimeError):
    pass


class BudgetExhausted(RuntimeError):
    pass


BUDGET_CAUSES = {'cumulative_call_cap', 'experiment_call_cap', 'ledger_unavailable', 'per_run_call_cap',
                 'stopped_after_provider_error'}


class ProviderFailure(RuntimeError):
    """A generation call did not complete. Never retried here.

    kind 'provider': the AI provider failed (timeout, rate limit, outage, error).
    kind 'budget': the call was refused before reaching the provider (a call cap, or generation
    already stopped after an earlier provider error). Neither is ever reported as insufficient evidence.
    """

    def __init__(self, cause, kind=None, diagnostic=None):
        super().__init__(cause)
        self.cause = cause
        self.kind = kind or ('budget' if cause in BUDGET_CAUSES else 'provider')
        self.diagnostic = diagnostic

    def details(self):
        details = {'cause': self.cause, 'kind': self.kind}
        if self.diagnostic:
            details['diagnostic'] = self.diagnostic
        return details


class CallBudget:
    """Per-question model-call limit, attributed to the calling agent.

    Wraps the configured generator (in the live backend: the capped Codex wrapper, whose
    cumulative cap and stop-after-error rule still apply underneath). A call beyond this
    question's limit is refused before it reaches the provider. Provider exceptions are
    recorded (safe diagnostic fields, never provider text) to distinguish them from validation
    rejections even when shared code re-wraps the exception.
    """

    def __init__(self, generate, max_calls):
        self.inner, self.max_calls = generate, int(max_calls)
        self.used, self.by_agent, self.provider_failure = 0, {}, None

    @property
    def remaining(self):
        return max(0, self.max_calls - self.used)

    def for_agent(self, agent):
        def generate(prompt, **kwargs):
            if self.provider_failure is not None:
                raise BudgetExhausted('A provider call already failed for this question; no further calls.')
            if self.used >= self.max_calls:
                raise BudgetExhausted(f'Per-question limit of {self.max_calls} model calls reached.')
            self.used += 1
            self.by_agent[agent] = self.by_agent.get(agent, 0) + 1
            try:
                return self.inner(prompt, **kwargs)
            except Exception as error:
                failure = ProviderFailure(classify_provider_error(error),
                                          diagnostic=getattr(error, 'codex_diagnostic', None))
                self.provider_failure = {'agent': agent, **failure.details()}
                raise failure from None
        generate.supports_response_schema = getattr(self.inner, 'supports_response_schema', False) is True
        return generate


def classify_provider_error(error):
    diagnostic = getattr(error, 'codex_diagnostic', None) or {}
    if diagnostic.get('category') in {
        'timeout', 'rate_limited', 'invalid_json_schema', 'authentication', 'upstream_unavailable'
    }:
        return diagnostic['category']
    text = f'{type(error).__name__} {error}'.lower()
    if 'cumulative authorized cap' in text:
        return 'cumulative_call_cap'
    if 'experiment cap' in text:
        return 'experiment_call_cap'
    if 'ledger' in text:
        return 'ledger_unavailable'
    if 'approved cap' in text and 'reached' in text:
        return 'per_run_call_cap'
    if 'stopped after a provider error' in text:
        return 'stopped_after_provider_error'
    if 'timeout' in text or 'timed out' in text:
        return 'timeout'
    if '429' in text or 'rate' in text:
        return 'rate_limited'
    return 'provider_error'

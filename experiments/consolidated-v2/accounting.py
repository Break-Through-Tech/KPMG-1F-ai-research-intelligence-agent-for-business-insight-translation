"""T4: provider-aware request accounting (consolidated-v2). Wraps the existing request_guard estimate, unchanged.

Three numbers are kept separate for every call:
  estimated  request_guard.estimate (ceil(UTF-8 bytes / 3)) of OUR prompt plus response schema;
  bounded    a conservative bound on provider input: overhead + multiplier x estimated;
  actual     provider-reported input/output tokens, from the adapter's receipt (when the adapter reports usage).

Profiles (configurable; `measured` says whether the numbers come from receipts):
  codex      measured on 40 live calls (consolidated-v1): planner prompts of ~940 estimated tokens arrived as ~10,980
             input tokens (fixed CLI system/tool prompt ~10.0k); all calls satisfy actual <= 10,040 + 1.113 x
             estimate. Profile: overhead 10,500, multiplier 1.15.
  gemini, openai, openai_compatible, bedrock   NOT measured. Conservative defaults (overhead 2,000 for system/message
             wrappers and schema handling, multiplier 1.25 for tokenizer differences) until receipts calibrate them.
The guard refuses BEFORE the call budget is touched: evidence estimate > evidence_cap, or bounded + output_reserve >
max_request. Persistent call caps are unchanged (codex_paired.Budget).
"""
from dataclasses import dataclass, asdict
import json

from request_guard import RequestTooLarge, estimate, evidence_of


@dataclass(frozen=True)
class Profile:
    name: str
    overhead: int
    multiplier: float
    max_request: int        # self-imposed bound on provider input + output reserve
    output_reserve: int
    evidence_cap: int
    measured: bool


PROFILES = {
    'codex': Profile('codex', 10_500, 1.15, 80_000, 8_000, 40_000, True),
    'gemini': Profile('gemini', 2_000, 1.25, 80_000, 8_000, 40_000, False),
    'openai': Profile('openai', 2_000, 1.25, 80_000, 8_000, 40_000, False),
    'openai_compatible': Profile('openai_compatible', 2_000, 1.25, 80_000, 8_000, 40_000, False),
    'bedrock': Profile('bedrock', 2_000, 1.25, 80_000, 8_000, 40_000, False),
}


class ProviderGuard:
    supports_response_schema = True

    def __init__(self, inner, profile, *, receipts=None):
        self.inner, self.profile = inner, PROFILES[profile] if isinstance(profile, str) else profile
        self.receipts = receipts
        self.records = []

    def __call__(self, prompt, **kwargs):
        evidence = evidence_of(prompt)
        schema = kwargs.get('response_schema')
        estimated = estimate(prompt) + (estimate(json.dumps(schema)) if schema else 0)
        bounded = int(self.profile.overhead + self.profile.multiplier * estimated)
        record = {'profile': self.profile.name, 'profile_measured': self.profile.measured,
                  'evidence_tokens_est': estimate(evidence) if evidence else 0, 'request_tokens_est': estimated,
                  'provider_input_bound': bounded, 'output_reserve': self.profile.output_reserve,
                  'actual_input_tokens': None, 'actual_output_tokens': None}
        record['allowed'] = (record['evidence_tokens_est'] <= self.profile.evidence_cap
                             and bounded + self.profile.output_reserve <= self.profile.max_request)
        self.records.append(record)
        if not record['allowed']:
            raise RequestTooLarge(f"Request over profile '{self.profile.name}' bounds (evidence "
                                  f"{record['evidence_tokens_est']}/{self.profile.evidence_cap}, provider input bound "
                                  f"{bounded}+{self.profile.output_reserve}/{self.profile.max_request}); not sent.")
        before = len(self.receipts) if self.receipts is not None else 0
        try:
            return self.inner(prompt, **kwargs)
        finally:
            if self.receipts is not None and len(self.receipts) > before:
                usage = (self.receipts[-1] or {}).get('usage') or []
                usage = usage if isinstance(usage, list) else [usage]
                record['actual_input_tokens'] = sum(u.get('input_tokens', 0) for u in usage if isinstance(u, dict)) or None
                record['actual_output_tokens'] = sum(u.get('output_tokens', 0) for u in usage if isinstance(u, dict)) or None


def calibration(records):
    """Summary of estimate vs actual, to recalibrate a profile from receipts (never applied automatically)."""
    pairs = [(r['request_tokens_est'], r['actual_input_tokens']) for r in records if r.get('actual_input_tokens')]
    if not pairs:
        return {'calls_with_receipts': 0}
    over = [a - e for e, a in pairs]
    return {'calls_with_receipts': len(pairs), 'actual_minus_estimate_min': min(over),
            'actual_minus_estimate_max': max(over),
            'bound_violations': sum(1 for r in records if r.get('actual_input_tokens')
                                    and r['actual_input_tokens'] > r['provider_input_bound'])}


def describe():
    return {name: asdict(p) for name, p in PROFILES.items()}

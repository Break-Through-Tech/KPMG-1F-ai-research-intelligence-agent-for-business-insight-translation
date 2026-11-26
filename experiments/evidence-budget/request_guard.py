"""Provider-request token guard for the combined-v1 runners (fails closed BEFORE a call is reserved or sent).

For every model request it records and checks two separate quantities:
  evidence_tokens  the serialized evidence passages inside the request ('paper_passages' or 'passages')
  request_tokens   the whole request: prompt text + response schema, plus a fixed output reserve for the cap check
Tokens are a bounded estimate: ceil(UTF-8 bytes / 3). GPT-family tokenizers average about 4 characters per token
on English prose; JSON, LaTeX and CJK text are denser, so /3 over-estimates typical requests. No tokenizer
package is installed offline. The Codex CLI adds its own system prompt, which is outside this count.

Caps (per request): evidence <= EVIDENCE_CAP, request + OUTPUT_RESERVE <= REQUEST_CAP. A request over either cap
raises RequestTooLarge; the wrapped budget is never touched, so no call is reserved, sent or counted.
"""
import json
import math
import re

# Sized from the offline packets: Baseline 6k skip-fit synthesis <= 31k estimated request tokens; Multi-Agent merged
# evidence <= 8,000 MiniLM passage tokens (~35k estimated) plus claims in the verifier request.
EVIDENCE_CAP = 40_000
REQUEST_CAP = 64_000
OUTPUT_RESERVE = 8_000
_PAYLOAD = re.compile(r'\{"question":')


class RequestTooLarge(ValueError):
    pass


def estimate(text):
    return math.ceil(len(text.encode('utf-8')) / 3)


def evidence_of(prompt):
    """The serialized evidence lists in the request's JSON payload (empty string if none)."""
    match = _PAYLOAD.search(prompt)
    if not match:
        return ''
    try:
        payload = json.loads(prompt[match.start():])
    except ValueError:
        return ''
    lists = [payload[k] for k in ('paper_passages', 'passages') if isinstance(payload.get(k), list)]
    return json.dumps(lists, ensure_ascii=False) if lists else ''


class RequestGuard:
    supports_response_schema = True

    def __init__(self, inner, *, evidence_cap=None, request_cap=None, reserve=None):
        self.inner = inner
        self.evidence_cap = EVIDENCE_CAP if evidence_cap is None else evidence_cap
        self.request_cap = REQUEST_CAP if request_cap is None else request_cap
        self.reserve = OUTPUT_RESERVE if reserve is None else reserve
        self.records = []

    def __call__(self, prompt, **kwargs):
        evidence = evidence_of(prompt)
        schema = kwargs.get('response_schema')
        record = {'evidence_tokens': estimate(evidence) if evidence else 0,
                  'evidence_passages': len(json.loads(evidence)[0]) if evidence else 0,
                  'request_tokens': estimate(prompt) + (estimate(json.dumps(schema)) if schema else 0),
                  'output_reserve': self.reserve, 'estimator': 'ceil(utf8 bytes / 3)'}
        record['allowed'] = (record['evidence_tokens'] <= self.evidence_cap
                             and record['request_tokens'] + self.reserve <= self.request_cap)
        self.records.append(record)
        if not record['allowed']:
            raise RequestTooLarge(f"Request over cap (evidence {record['evidence_tokens']}/{self.evidence_cap}, request "
                                  f"{record['request_tokens']}+{self.reserve}/{self.request_cap}); not sent.")
        return self.inner(prompt, **kwargs)

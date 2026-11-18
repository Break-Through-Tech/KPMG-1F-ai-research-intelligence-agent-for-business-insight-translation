"""Development-only adapter for decimal JSON operands, without float coercion."""
import json
import re
from rate_plan import parse

_DECIMAL = re.compile(r'[0-9]{1,3}(?:.[0-9]{1,12})?')

class NumberToken(str):
    pass

def _number(raw):
    if not _DECIMAL.fullmatch(raw):
        raise ValueError('unbounded or unsupported numeric syntax')
    return NumberToken(raw)

def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate key')
        out[key] = value
    return out

def normalize(raw):
    if len(raw) > 4096:
        raise ValueError('request too large')
    p = json.loads(raw, parse_int=_number, parse_float=_number,
                   parse_constant=_number, object_pairs_hook=_object)
    if isinstance(p, dict):
        for key in ('initial', 'final'):
            if isinstance(p.get(key), NumberToken):
                p[key] = str(p[key])
        for key in ('operation', 'source_ids'):
            v = p.get(key)
            if isinstance(v, NumberToken) or (isinstance(v, list) and any(isinstance(x, NumberToken) for x in v)):
                raise ValueError('numeric token outside operand fields')
    return json.dumps(p)

def checked_parse(raw, finish, case):
    return parse(normalize(raw), finish, case)

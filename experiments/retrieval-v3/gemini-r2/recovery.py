"""Experimental recovery at the evaluation response boundary only."""
import json

from jsonschema import Draft202012Validator

STAGES = {
    frozenset(('status', 'claims', 'limitations')): ('draft', {'claims', 'limitations'}),
    frozenset(('coverage', 'gap', 'decisions', 'limitations')): ('review', {'decisions', 'limitations'}),
}
COVERAGE_NOTICE = 'Some model output was withheld after validation. Answer coverage needs human review.'


def _unique_members(items):
    result = dict(items)
    if len(result) != len(items):
        raise ValueError('Duplicate JSON member.')
    return result


def recover_response(raw, schema, *, draft_was_recovered=False):
    """Return validated JSON and safe omission labels, or reject without altering the reply."""
    contract = STAGES.get(frozenset(schema.get('properties', {})))
    if contract is None:
        return raw, []
    stage, arrays = contract
    value = json.loads(raw, object_pairs_hook=_unique_members)
    # Reject NaN, Infinity and numeric overflow even inside a malformed item.
    json.dumps(value, allow_nan=False)
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(value))
    drops = set()
    for error in errors:
        path = list(error.absolute_path)
        if len(path) < 2 or path[0] not in arrays or type(path[1]) is not int:
            raise errors[0]
        drops.add((path[0], path[1]))

    if any(field == 'decisions' for field, _ in drops):
        indices = [item.get('index') if isinstance(item, dict) else None for item in value['decisions']]
        # A bad or ambiguous identity could otherwise make a contradictory duplicate publishable.
        max_index = schema['properties']['decisions']['items']['properties']['index']['maximum']
        if (any(type(index) is not int or not 0 <= index <= max_index for index in indices)
                or len(set(indices)) != len(indices)):
            raise errors[0]

    for field in arrays:
        value[field] = [item for index, item in enumerate(value[field]) if (field, index) not in drops]
    if stage == 'review' and (drops or draft_was_recovered):
        if value['coverage'] == 'full':
            value['coverage'] = 'partial'
        value['gap'] = COVERAGE_NOTICE
    if stage == 'draft' and drops and not value['claims']:
        value['status'] = 'insufficient_evidence'
    validator.validate(value)
    if not drops and not (stage == 'review' and draft_was_recovered):
        return raw, []
    return json.dumps(value, ensure_ascii=False), [
        {'stage': stage, 'field': field, 'index': index} for field, index in sorted(drops)
    ]

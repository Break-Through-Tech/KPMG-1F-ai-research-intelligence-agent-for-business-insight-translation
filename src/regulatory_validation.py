"""Dependency-free validation shared by regulatory and research-review paths."""

_FINDING_NAMES = (
    "regulatory_compliance", "legal_constraints", "governance", "operational_feasibility",
)
_FINDING_STATUSES = {"supported", "conflicts", "unknown", "not_applicable"}
_VERDICTS = {"potentially_feasible", "conflicts", "insufficient_evidence"}


def validate_assessment_data(assessment, evidence):
    """Validate the complete checkpoint schema, citations, and consistent verdict."""
    if not isinstance(assessment, dict) or not isinstance(evidence, dict):
        raise ValueError("Assessment and regulatory evidence must be dictionaries.")
    required = {"verdict", "summary", "risks", *_FINDING_NAMES}
    if set(assessment) != required:
        raise ValueError("Assessment schema is incomplete or has unexpected fields.")
    if not isinstance(assessment["verdict"], str) or assessment["verdict"] not in _VERDICTS:
        raise ValueError("Assessment verdict is missing or invalid.")
    if not isinstance(assessment["summary"], str) or not assessment["summary"].strip():
        raise ValueError("Assessment summary must be non-empty text.")
    if not isinstance(assessment["risks"], list) or not all(isinstance(x, str) for x in assessment["risks"]):
        raise ValueError("Assessment risks must be a list of strings.")

    valid_ids = validate_regulatory_evidence(evidence)

    statuses = set()
    for name in _FINDING_NAMES:
        finding = assessment[name]
        if not isinstance(finding, dict) or set(finding) != {"status", "explanation", "source_ids"}:
            raise ValueError("Assessment finding schema is incomplete or has unexpected fields.")
        status = finding["status"]
        if not isinstance(status, str) or status not in _FINDING_STATUSES:
            raise ValueError("Assessment finding status is invalid.")
        if not isinstance(finding["explanation"], str) or not finding["explanation"].strip():
            raise ValueError("Assessment finding explanation must be non-empty text.")
        source_ids = finding["source_ids"]
        if not isinstance(source_ids, list) or any(
                isinstance(item, bool) or not isinstance(item, int) for item in source_ids):
            raise ValueError("Assessment source IDs must be a list of integers.")
        if not set(source_ids).issubset(valid_ids):
            raise ValueError("Validator cited an unknown source ID.")
        if status != "unknown" and not source_ids:
            raise ValueError("Validator made a finding without cited evidence.")
        statuses.add(status)

    expected = ("conflicts" if "conflicts" in statuses else
                "insufficient_evidence" if "unknown" in statuses else "potentially_feasible")
    if assessment["verdict"] != expected:
        raise ValueError("Validator verdict contradicts its individual findings.")
    return assessment


def validate_regulatory_evidence(evidence):
    """Validate a source-backed regulatory evidence snapshot and return source IDs."""
    if not isinstance(evidence, dict):
        raise ValueError("Regulatory evidence must be a dictionary.")
    sources = evidence.get("sources")
    segments = evidence.get("evidence")
    if not isinstance(sources, list) or not sources or not isinstance(segments, list) or not segments:
        raise ValueError("Cited regulatory evidence is required before assessment.")
    valid_ids = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Regulatory sources must be dictionaries.")
        source_id = source.get("source_id")
        if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id <= 0 or source_id in valid_ids:
            raise ValueError("Regulatory source IDs must be unique positive integers.")
        valid_ids.add(source_id)
    for segment in segments:
        if not isinstance(segment, dict) or not isinstance(segment.get("text"), str) or not segment["text"].strip():
            raise ValueError("Regulatory evidence segments require text.")
        cited = segment.get("source_ids")
        if not isinstance(cited, list) or not cited or any(
                isinstance(item, bool) or not isinstance(item, int) or item not in valid_ids for item in cited):
            raise ValueError("Regulatory evidence cites an unknown or missing source ID.")
    return valid_ids


def validate_checkpoint(checkpoint):
    """Check a complete advisory checkpoint using the same shareable gate."""
    if not isinstance(checkpoint, dict):
        raise ValueError("Regulatory checkpoint must be a dictionary.")
    evidence = checkpoint.get("regulatory_evidence", checkpoint)
    return validate_assessment_data(checkpoint.get("assessment"), evidence)

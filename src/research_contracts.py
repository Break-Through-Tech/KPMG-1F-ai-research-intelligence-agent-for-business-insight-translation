"""Shared draft interface v1; standard library only, no model or storage imports.

Validation establishes shape and citation identity/location, not source truth,
semantic support, reviewer identity, or approval. Additive metadata is preserved.
"""
from copy import deepcopy
import json
import math
from typing import Literal, TypedDict
from urllib.parse import urlsplit

SCHEMA_VERSION = '1.0'
Status = Literal['ok', 'insufficient_evidence']


class _Request(TypedDict):
    query: str


class ResearchRequest(_Request, total=False):
    top_k: int
    industry: str
    jurisdiction: str


class _Passage(TypedDict):
    chunk_id: str
    text: str
    arxiv_id: str | None
    title: str
    pdf_url: str | None
    source: Literal['html', 'pdf', 'synthetic']
    source_url: str | None
    page_number: int | None


class EvidencePassage(_Passage, total=False):
    distance: float | None
    html_url: str
    section: str
    subsection: str


class ResearchClaim(TypedDict):
    text: str
    chunk_ids: list[str]


class ResearchSummary(TypedDict):
    status: Status
    query: str
    claims: list[ResearchClaim]
    limitations: list[str]


class BusinessImplication(ResearchClaim):
    suggested_action: str
    assumptions: list[str]


class BusinessInsight(TypedDict):
    status: Status
    industry: str
    implications: list[BusinessImplication]
    risks: list[str]
    limitations: list[str]


class HumanReview(TypedDict):
    status: Literal['pending', 'approve', 'revise', 'reject']
    reviewer: str | None
    notes: str | None


class _Result(TypedDict):
    schema_version: str
    request: ResearchRequest
    evidence: list[EvidencePassage]
    summary: ResearchSummary
    human_review: HumanReview
    approved: bool


class ResearchResult(_Result, total=False):
    business_insight: BusinessInsight
    provenance: dict
    regulatory_checkpoint: dict
    review_fingerprint: str
    review_fingerprint_version: int


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value, field):
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise ValueError(f'{field} must be a list of strings')


def _json(value):
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        raise ValueError('Research contract values must be finite JSON data') from None


def _url(value, field):
    if not _text(value) or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(f'{field} must be an absolute HTTP(S) source URL')
    try:
        parsed = urlsplit(value)
        _ = parsed.port  # Reject malformed ports as well as malformed hosts.
        valid = (parsed.scheme in {'http', 'https'} and parsed.hostname
                 and parsed.username is None and parsed.password is None)
    except ValueError:
        valid = False
    if not valid:
        raise ValueError(f'{field} must be an absolute HTTP(S) source URL')
    return parsed


def validate_request(request):
    """Return a defensive copy with top_k=5; never strip query/context or metadata."""
    if not isinstance(request, dict) or not _text(request.get('query')):
        raise ValueError('query must be nonempty text')
    normalized = deepcopy(request)
    normalized.setdefault('top_k', 5)
    k = normalized['top_k']
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError('top_k must be a positive integer')
    for key in ('industry', 'jurisdiction'):
        if key in normalized and not _text(normalized[key]):
            raise ValueError(f'{key} must be nonempty text when supplied')
    _json(normalized)
    return normalized


def validate_evidence(passages):
    """Validate source-specific locations and return IDs; no input mutation/I/O.

    Legacy PDF base URLs are valid with an explicit positive page. If a page
    fragment is supplied it must match. HTML locators preserve their exact heading
    link; a base URL remains valid when extraction supplied no heading anchor.
    Explicit synthetic passages are not paper citations and require null locators.
    """
    if not isinstance(passages, list):
        raise ValueError('Retrieval must return a list of evidence passages')
    ids = set()
    for p in passages:
        if not isinstance(p, dict) or not _text(p.get('chunk_id')) or not _text(p.get('text')):
            raise ValueError('Evidence requires chunk_id and text')
        if p['chunk_id'] in ids:
            raise ValueError('Duplicate evidence chunk IDs')
        ids.add(p['chunk_id'])
        if not _text(p.get('title')) or 'page_number' not in p:
            raise ValueError('Evidence requires title and explicit page_number')
        source = p.get('source')
        if not isinstance(source, str) or source not in {'pdf', 'html', 'synthetic'}:
            raise ValueError('Evidence source must be pdf, html, or synthetic')
        distance = p.get('distance')
        if distance is not None and (isinstance(distance, bool)
                or not isinstance(distance, (int, float)) or not math.isfinite(distance)):
            raise ValueError('distance must be a finite number or null, never confidence')
        for key in ('section', 'subsection'):
            if key in p and not isinstance(p[key], str):
                raise ValueError(f'{key} must be text when supplied')
        if source == 'synthetic':
            if any(key not in p or p[key] is not None
                   for key in ('arxiv_id', 'pdf_url', 'source_url', 'page_number')) or p.get('html_url') is not None:
                raise ValueError('Synthetic evidence must have null paper IDs and source locators')
            continue
        if not _text(p.get('arxiv_id')):
            raise ValueError('Paper evidence requires arxiv_id')
        pdf = _url(p.get('pdf_url'), 'pdf_url')
        if pdf.fragment:
            raise ValueError('pdf_url must identify the document without a page fragment')
        location = _url(p.get('source_url'), 'source_url')
        page = p['page_number']
        if source == 'pdf':
            if isinstance(page, bool) or not isinstance(page, int) or page < 1:
                raise ValueError('PDF page_number must be a positive 1-based integer')
            if (location._replace(fragment='') != pdf
                    or location.fragment not in {'', f'page={page}'}):
                raise ValueError('PDF source_url must match pdf_url and page_number')
        else:
            if page is not None:
                raise ValueError('HTML page_number must be null')
            if 'html_url' in p:
                _url(p['html_url'], 'html_url')
                if p['html_url'] != p['source_url']:
                    raise ValueError('HTML source_url must preserve the html_url heading link')
    _json(passages)
    return ids


def validate_output(output, field, ids):
    """Shared stage/citation checks; retained alias in research_pipeline for callers."""
    if field not in {'claims', 'implications'}:
        raise ValueError('Output field must be claims or implications')
    if (not isinstance(output, dict) or not isinstance(output.get('status'), str)
            or output['status'] not in {'ok', 'insufficient_evidence'}):
        raise ValueError('Adapter must return status ok or insufficient_evidence')
    rows = output.get(field)
    if not isinstance(rows, list) or (output['status'] == 'ok' and not rows):
        raise ValueError(f'Adapter must return {field}; ok requires at least one item')
    if output['status'] == 'insufficient_evidence' and rows:
        raise ValueError(f'Insufficient evidence requires empty {field}')
    _strings(output.get('limitations'), 'Adapter limitations')
    for row in rows:
        if not isinstance(row, dict) or not _text(row.get('text')):
            raise ValueError('Each claim/implication requires text')
        citations = row.get('chunk_ids')
        if (not isinstance(citations, list) or not citations
                or any(not _text(x) or x not in ids for x in citations)
                or len(set(citations)) != len(citations)):
            raise ValueError('Every claim/implication must cite unique known evidence chunk IDs')
        if field == 'implications':
            if not _text(row.get('suggested_action')):
                raise ValueError('Business implications require suggested_action and assumptions')
            _strings(row.get('assumptions'), 'Business assumptions')
    if field == 'implications':
        _strings(output.get('risks'), 'Business risks')
    _json(output)


def validate_summary(summary, ids, *, query=None):
    validate_output(summary, 'claims', ids)
    if not _text(summary.get('query')) or (query is not None and summary['query'] != query):
        raise ValueError('Summary query does not match the request')


def validate_business_insight(business, ids, *, industry=None):
    validate_output(business, 'implications', ids)
    if not _text(business.get('industry')) or (industry is not None and business['industry'] != industry):
        raise ValueError('Business industry does not match the request')


def validate_result(result):
    """Validate a fresh pending draft. Reviewed packets use research_review guards."""
    if not isinstance(result, dict) or result.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('ResearchResult schema_version must be 1.0')
    request = validate_request(result.get('request'))
    ids = validate_evidence(result.get('evidence'))
    summary = result.get('summary')
    validate_summary(summary, ids, query=request['query'])
    if 'business_insight' in result:
        if not _text(request.get('industry')):
            raise ValueError('Business mode requires explicit industry context')
        business = result['business_insight']
        validate_business_insight(business, ids, industry=request['industry'])
        if summary['status'] != 'ok' and business['status'] == 'ok':
            raise ValueError('Business output requires a supported summary')
    review = result.get('human_review')
    if (not isinstance(review, dict) or review.get('status') != 'pending'
            or 'reviewer' not in review or review['reviewer'] is not None
            or 'notes' not in review or review['notes'] is not None
            or result.get('approved') is not False):
        raise ValueError('Fresh results require pending human review and approved=false')
    for key in ('provenance', 'regulatory_checkpoint'):
        if key in result and not isinstance(result[key], dict):
            raise ValueError(f'{key} must be a separate JSON object when supplied')
    _json(result)

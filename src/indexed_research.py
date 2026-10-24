"""Explicit persistent-index UI adapter. Imports are offline; no index is built."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from src.research_chat import synthesize
from src.business_translation import translate, prompt_provenance
from src.research_contracts import validate_request, validate_result, validate_business_insight
from src.research_pipeline import PipelineError, run_research, content_fingerprint


class IndexedContextError(ValueError):
    """The active indexed run identity no longer matches the page."""


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                             ensure_ascii=True).encode()).hexdigest()


def collection_identity(collection):
    """Hash actual indexed text/locators, not the unrelated ingestion input file.

    Embedding bytes are deliberately not certified by this identity. In-place
    embedding/index changes require restarting the host; see identity_limits.
    """
    rows = collection.get(include=['documents', 'metadatas'])
    records = sorted(zip(rows['ids'], rows['documents'], rows['metadatas']))
    return {'collection': collection.name, 'count': len(records),
            'metadata': collection.metadata, 'indexed_records_sha256': fingerprint(records),
            'identity_limits': 'Indexed IDs, text and metadata only; not embedding bytes, source certification or index revision locking.'}


def open_index(path, collection_name):
    """Require an existing compatible collection and locally cached encoder."""
    path = Path(path).resolve()
    if not (path / 'chroma.sqlite3').is_file():
        raise ValueError('Persistent index missing. Select an existing --index; no index was created.')
    from src import retrieval
    client = retrieval.chromadb.PersistentClient(path=str(path))
    collection = client.get_collection(name=collection_name)  # never get_or_create
    if (collection.metadata or {}).get('embedding_model') != retrieval.EMBEDDING_MODEL:
        raise ValueError('Index has unknown/incompatible embedding model. Select a compatible index.')
    try:
        model = retrieval.SentenceTransformer(retrieval.EMBEDDING_MODEL, local_files_only=True)
    except Exception:
        raise ValueError('Embedding model is not available locally; no download or fallback was attempted.') from None
    def retrieve(query, top_k):
        return retrieval.search(query, top_k, client=client, model=model,
                                collection_name=collection_name)
    return retrieve, lambda: collection_identity(collection), str(path)


def scenario_for(result):
    if not result['evidence']:
        return 'empty'
    if result['summary']['status'] != 'ok':
        return 'insufficient'
    if not result.get('business_insight'):
        return 'summary-only'
    if result['business_insight']['status'] != 'ok':
        return 'partial'
    return 'full'


class IndexedResearch:
    """Independent indexed queries: never use client answers as research context."""
    mode = 'indexed'

    def __init__(self, *, retrieve, identity, generate, metadata, index_path,
                 top_k=5, code_revision=None, command=None):
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError('Indexed UI top_k must be between 1 and 20.')
        self.retrieve, self.identity, self.generate = retrieve, identity, generate
        self.top_k = top_k
        self.provenance = {'execution': 'persistent_index_ui', 'generation': deepcopy(metadata),
            'index_path': index_path, 'index': identity(), 'code_revision': code_revision,
            'command': command, 'retrieval': {'method': 'existing_dense_search', 'top_k': top_k,
                'embedding_model': 'all-MiniLM-L6-v2', 'reranker': None},
            'summary_adapter': 'src.research_chat:synthesize',
            'translation_adapter': 'src.business_translation:translate',
            'business_prompt': prompt_provenance(), 'history_policy': 'independent_queries'}
        self.context_id = fingerprint(self.provenance)

    def config(self):
        return {'mode': self.mode, 'context_id': self.context_id,
                'history_policy': 'independent_queries', 'index': self.provenance['index']}

    def check_context(self, context_id):
        if context_id != self.context_id or self.identity() != self.provenance['index']:
            raise IndexedContextError('Indexed context changed. Restart the server and reload the page; no stale context was used.')

    def prepare_request(self, payload):
        if payload.get('history') not in (None, []):
            raise ValueError('Indexed queries are independent; client history is not accepted.')
        query = payload.get('query')
        if not isinstance(query, str) or len(query) > 2000:
            raise ValueError('Enter a question up to 2000 characters.')
        request = {'query': query, 'top_k': self.top_k}
        industry = payload.get('industry', '')
        if not isinstance(industry, str) or len(industry) > 300:
            raise ValueError('Industry must be text up to 300 characters.')
        if industry.strip():
            request['industry'] = industry
        return validate_request(request)

    def summary(self, query, passages, *, history=None):
        return synthesize(query, passages, generate=self.generate, history=history)

    def finish(self, result, submitted, *, error=None):
        stages = {'retrieval': 'ok' if result['evidence'] else 'empty',
                  'summary': result['summary']['status'], 'business': 'not_requested'}
        if 'industry' in submitted:
            if result['summary']['status'] != 'ok':
                result['business_insight'] = {'status': 'insufficient_evidence',
                    'industry': submitted['industry'], 'implications': [], 'risks': [],
                    'limitations': ['No supported summary; business generation skipped.']}
                stages['business'] = 'skipped'
            else:
                try:
                    business = translate(result['summary'], result['evidence'],
                        industry=submitted['industry'], generate=self.generate)
                    validate_business_insight(business,
                        {p['chunk_id'] for p in result['evidence']}, industry=submitted['industry'])
                    result['business_insight'] = business
                    stages['business'] = business['status']
                except Exception:
                    # Keep the accepted summary, and label execution failure, not abstention.
                    error = {'stage': 'business', 'code': 'business_failed',
                             'message': 'Business translation failed or did not validate. The supported research summary is retained; retry the question.'}
                    stages['business'] = 'failed'
        result['provenance']['stages'] = stages
        result['review_fingerprint'] = content_fingerprint(result)
        validate_result(result)
        return {'mode': 'indexed', 'scenario': 'partial' if error else scenario_for(result),
                'submitted_request': submitted, 'result': result, 'error': error,
                'fixture_file': None, 'context_id': self.context_id}

    def execute(self, payload, *, session_id=None):
        request = self.prepare_request(payload)
        self.check_context(payload.get('context_id'))
        def retrieve(query, top_k):
            from src.research_contracts import validate_evidence
            try:
                passages = self.retrieve(query, top_k)
                validate_evidence(passages)
                return passages
            except Exception:
                raise PipelineError('Retrieval failed or its evidence contract did not validate.') from None
        try:
            result = run_research(request, retrieve=retrieve,
                summarize_fn=self.summary, provenance=self.provenance)
        except Exception as exc:
            stage = 'retrieval' if isinstance(exc, PipelineError) and str(exc).startswith('Retrieval') else 'summary'
            return {'mode': 'indexed', 'scenario': 'execution-error',
                    'submitted_request': request, 'result': None, 'fixture_file': None,
                    'provenance': {**deepcopy(self.provenance), 'stages': {stage: 'failed'}},
                    'error': {'stage': stage, 'code': stage + '_failed',
                              'message': f'{stage.capitalize()} failed or its contract did not validate. No answer was accepted. Check configuration and retry.'}}
        self.check_context(payload.get('context_id'))
        response = self.finish(result, request)
        self.check_context(payload.get('context_id'))
        return response


def code_revision():
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True,
                              text=True, check=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None

"""Opt-in production adapter for the existing KPMG backend (consolidated-v2; isolated, no shared files changed).

Seam: src.indexed_research.IndexedResearch.execute -> run_research(retrieve=..., summarize_fn=self.summary).
  - retrieve(query, top_k)  -> the consolidated EVIDENCE phase: Baseline protected packet, plus (Deep, or Adaptive when
                               activated) the planner call and bounded supplementary searches. Supplementary passages
                               must be gathered here because run_research fixes result['evidence'] from retrieve, and
                               every published citation is validated against it.
  - summary(query, passages) -> the consolidated ANSWER phase: shared synthesis, shared review, deterministic gates.
Everything downstream (finish(): business translation, regulatory checkpoint, validate_result, fingerprints, the UI
contract) is the existing IndexedResearch code, unchanged.

Checkpoints: RequestCheckpoints keys a folder by sha256 of (user/session, query, mode, index identity, engine version,
context id) and stores that fingerprint; a resume loads stages only when the stored fingerprint matches exactly, so a
request can never reuse another user's or a stale request's evidence. Timeouts and retry counts are unchanged: a failed
stage raises as before, and the next retry of the SAME request resumes after the last completed stage.

    research = create_consolidated_research('standard', retrieval=open_ranked(...), generate=..., metadata=...,
                                            checkpoint_root=Path(...))
"""
from hashlib import sha256
import json
from pathlib import Path
import threading

import env  # noqa: F401  (path setup)
import evidence as ev
from engine import CheckpointStore, ConsolidatedResearch, default_planner

ENGINE_VERSION = 'consolidated-v2'
_request = threading.local()


class FingerprintMismatch(RuntimeError):
    pass


class RequestCheckpoints:
    def __init__(self, root):
        self.root = Path(root)

    @staticmethod
    def fingerprint(*, session, query, mode, index_sha256, context_id):
        return {'engine': ENGINE_VERSION, 'session': session or 'anonymous', 'query': query, 'mode': mode,
                'index_sha256': index_sha256, 'context_id': context_id}

    def store(self, fingerprint):
        key = sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        folder = self.root / key[:2] / key
        store = CheckpointStore(folder)
        marker = folder / 'fingerprint.json'
        if marker.is_file():
            if json.loads(marker.read_text(encoding='utf-8')) != fingerprint:
                raise FingerprintMismatch('Checkpoint fingerprint differs; refusing to reuse its stages.')
        else:
            marker.write_text(json.dumps(fingerprint, sort_keys=True), encoding='utf-8')
        return store


def create_consolidated_research(mode, *, retrieval, generate, metadata, checkpoint_root, tables=None, v2=None,
                                 gate=None, planner=default_planner):
    """retrieval = evidence_budget.open_ranked(...) -> (retrieve, identity, ranked, count, path, provenance)."""
    from src.indexed_research import IndexedResearch, code_revision, fingerprint
    _retrieve, identity, ranked, count, path, provenance = retrieval
    tables = tables or ev.TableIndex(env.bundle_rows())
    engine = ConsolidatedResearch(mode, ranked=ranked, count=count, tables=tables, generate=generate,
                                  v2=v2 or env.load_v2(), gate=gate or env.load_gate(), planner=planner)
    checkpoints = RequestCheckpoints(checkpoint_root)

    class ConsolidatedIndexedResearch(IndexedResearch):
        def execute(self, payload, *, session_id=None):
            _request.session, _request.payload, _request.packets = session_id, payload, {}
            try:
                return super().execute(payload, session_id=session_id)
            finally:
                _request.packets = {}

        def _store(self, query):
            fp = checkpoints.fingerprint(session=getattr(_request, 'session', None), query=query, mode=mode,
                                         index_sha256=identity().get('indexed_records_sha256'),
                                         context_id=(getattr(_request, 'payload', None) or {}).get('context_id'))
            return checkpoints.store(fp)

        def summary(self, query, passages, *, history=None, findings_only=False, timings=None):
            timings = {} if timings is None else timings
            packet = getattr(_request, 'packets', {}).get(query)
            if packet is None or [p['chunk_id'] for p in packet['passages']] != [p['chunk_id'] for p in passages]:
                packet = {'passages': passages, 'notes': ev.table_notes(passages, tables)}
            store = self._store(query)
            # Business mode: as in Baseline, research findings only when an industry is requested.
            industry = bool((getattr(_request, 'payload', None) or {}).get('industry'))
            summary, drafted, reviewed, _flags = engine.answer(query, packet, store, timings,
                                                               findings_only=findings_only or industry)
            out = {k: v for k, v in summary.items()}
            out.update(query=query, generation_method=f'{ENGINE_VERSION}-{mode}',
                       quality_review={'policy': f'{ENGINE_VERSION} review + deterministic publication gates',
                                       'coverage': reviewed['review']['coverage'], 'gap': reviewed['review']['gap'],
                                       'reviewer': 'model_not_independent_human',
                                       'original_claims': drafted['summary']['claims'],
                                       'held_claims': summary.get('held_claims', [])})
            return out

    def retrieve(query, top_k):
        timings = {}
        store = research._store(query)
        packet, _plan, _decision = engine.gather_evidence(query, store, timings)
        _request.packets = {**getattr(_request, 'packets', {}), query: packet}
        return [dict(p) for p in packet['passages']]

    research = ConsolidatedIndexedResearch(retrieve=retrieve, identity=identity, index_path=path, generate=generate,
                                           metadata=metadata, top_k=20, quality_check=False,
                                           code_revision=code_revision(), command=[f'{ENGINE_VERSION}-{mode}'])
    research.provenance['retrieval'] = {**provenance, 'engine': f'{ENGINE_VERSION}-{mode}',
                                        'evidence': 'protected 6k skip-fit + bounded conclusion coverage'
                                                    + (' + planned supplementary (8k)' if mode != 'standard' else '')}
    research.provenance['summary_adapter'] = f'experiments/consolidated-v2/adapter.py ({mode})'
    research.context_id = fingerprint(research.provenance)
    return research

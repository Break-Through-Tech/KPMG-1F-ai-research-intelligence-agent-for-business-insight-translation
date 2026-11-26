"""Production adapter for S2 with the opt-in B1 paper-balanced selector (isolated; no shared files changed).

Same seam and behaviour as experiments/consolidated-v2/adapter.py (create_consolidated_research('standard', ...)),
with one addition: paper_balance (default False). With False the engine is exactly frozen S2. With True, evidence
selection uses B1 only when the question names >= 2 papers present in the top-120; everything else is frozen S2.
The variant is part of the checkpoint fingerprint ('standard' vs 'standard+paper-balance'), so the two never share
cached stages.

retrieval_strategy='r2' (opt-in) constructs optimized S2-R2 (s2_r2_opt.S2R2OptResearch, validated as 1d0e0ae and
optimized in a462275): B1 when >= 2 named papers resolve, otherwise component-rank fusion, otherwise S2's window.
Synthesis, review, gates, budget and the 2-call structure are frozen S2. Its variant 'standard+r2-opt' keeps its
checkpoints, provenance and generation_method separate from S2 and B1. R2 already contains the B1 route, so it cannot
be combined with paper_balance=True.

    research = create_s2_research(retrieval=open_ranked(...), generate=..., metadata=..., checkpoint_root=Path(...),
                                  paper_balance=False)
"""
import s3_env  # noqa: F401
import adapter as v2adapter  # frozen consolidated-v2 adapter (RequestCheckpoints, ENGINE_VERSION)
import env
import evidence as ev
from s2_paper_balance import S2Research

ENGINE_VERSION = v2adapter.ENGINE_VERSION


def create_s2_research(*, retrieval, generate, metadata, checkpoint_root, paper_balance=False, rows=None, tables=None,
                       v2=None, gate=None, retrieval_strategy='s2'):
    from src.indexed_research import IndexedResearch, code_revision, fingerprint
    _retrieve, identity, ranked, count, path, provenance = retrieval
    rows = rows if rows is not None else {r['chunk_id']: r for r in env.bundle_rows()}
    tables = tables or ev.TableIndex(rows.values())
    if retrieval_strategy not in ('s2', 'r2'):
        raise ValueError("retrieval_strategy must be 's2' or 'r2'")
    if retrieval_strategy == 'r2' and paper_balance:
        raise ValueError('S2-R2 already includes the B1 route; leave paper_balance off.')
    common = dict(ranked=ranked, count=count, tables=tables, generate=generate, v2=v2 or env.load_v2(),
                  gate=gate or env.load_gate(), rows=rows)
    if retrieval_strategy == 'r2':
        from s2_r2_opt import S2R2OptResearch
        variant = 'standard+r2-opt'
        engine = S2R2OptResearch(retrieval_strategy='r2', **common)
    else:
        variant = 'standard+paper-balance' if paper_balance else 'standard'
        engine = S2Research(paper_balance=paper_balance, **common)
    checkpoints = v2adapter.RequestCheckpoints(checkpoint_root)
    state = v2adapter._request

    class S2IndexedResearch(IndexedResearch):
        def execute(self, payload, *, session_id=None):
            state.session, state.payload, state.packets = session_id, payload, {}
            try:
                return super().execute(payload, session_id=session_id)
            finally:
                state.packets = {}

        def _store(self, query):
            fp = checkpoints.fingerprint(session=getattr(state, 'session', None), query=query, mode=variant,
                                         index_sha256=identity().get('indexed_records_sha256'),
                                         context_id=(getattr(state, 'payload', None) or {}).get('context_id'))
            return checkpoints.store(fp)

        def summary(self, query, passages, *, history=None, findings_only=False, timings=None):
            timings = {} if timings is None else timings
            packet = getattr(state, 'packets', {}).get(query)
            if packet is None or [p['chunk_id'] for p in packet['passages']] != [p['chunk_id'] for p in passages]:
                packet = {'passages': passages, 'notes': ev.table_notes(passages, tables)}
            store = self._store(query)
            industry = bool((getattr(state, 'payload', None) or {}).get('industry'))
            summary, drafted, reviewed, _flags = engine.answer(query, packet, store, timings,
                                                               findings_only=findings_only or industry)
            out = dict(summary)
            out.update(query=query, generation_method=f'{ENGINE_VERSION}-{variant}',
                       paper_balance=packet.get('paper_balance', {'enabled': paper_balance, 'applied': False}),
                       quality_review={'policy': f'{ENGINE_VERSION} review + deterministic publication gates',
                                       'coverage': reviewed['review']['coverage'], 'gap': reviewed['review']['gap'],
                                       'reviewer': 'model_not_independent_human',
                                       'original_claims': drafted['summary']['claims'],
                                       'held_claims': summary.get('held_claims', [])})
            return out

    def retrieve(query, top_k):
        store = research._store(query)
        packet, _plan, _decision = engine.gather_evidence(query, store, {})
        state.packets = {**getattr(state, 'packets', {}), query: packet}
        return [dict(p) for p in packet['passages']]

    research = S2IndexedResearch(retrieve=retrieve, identity=identity, index_path=path, generate=generate,
                                 metadata=metadata, top_k=20, quality_check=False, code_revision=code_revision(),
                                 command=[f'{ENGINE_VERSION}-{variant}'])
    research.provenance['retrieval'] = {**provenance, 'engine': f'{ENGINE_VERSION}-{variant}',
                                        'evidence': 'protected 6k skip-fit + bounded conclusion coverage'
                                                    + (' + B1 paper balance (>= 2 named papers)' if paper_balance else '')
                                                    + (' + S2-R2 routing (B1 for >= 2 named papers, else component-rank'
                                                       ' fusion)' if retrieval_strategy == 'r2' else '')}
    research.provenance['summary_adapter'] = f'experiments/retrieval-v3/s2_adapter.py ({variant})'
    research.context_id = fingerprint(research.provenance)
    return research

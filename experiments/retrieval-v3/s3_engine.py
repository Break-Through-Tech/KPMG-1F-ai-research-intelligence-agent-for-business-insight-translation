"""S3 = V2 Standard + component-fusion retrieval (R) + component-complete synthesis (C). Still 2 model calls.

Subclasses the frozen V2 ConsolidatedResearch: checkpointing, resume, attempt records and result shape are V2's.
Only gather_evidence (s3_evidence.s3_packet) and answer (s3_answer synthesis/review/publish) are replaced.
"""
import s3_env  # noqa: F401
import publication  # frozen V2
from engine import ConsolidatedResearch  # frozen V2
import s3_answer
import s3_evidence
from components import components

ENGINE = 's3-standard'


class S3Research(ConsolidatedResearch):
    def __init__(self, **kwargs):
        super().__init__('standard', **kwargs)
        self.engine = ENGINE

    def gather_evidence(self, question, store, timings):
        packet = self._stage(store, 'evidence', timings,
                             lambda: s3_evidence.s3_packet(question, self.ranked, self.count, self.tables,
                                                           parallel=self.parallel_search))
        return packet, None, None

    def answer(self, question, packet, store, timings, *, findings_only=False):
        passages, notes = packet['passages'], packet['notes']
        comps = packet.get('components', components(question))

        def draft():
            summary, report, raw = s3_answer.synthesize(question, passages, notes, comps, generate=self.generate,
                                                        findings_only=findings_only)
            summary = {**summary, 'component_map': {str(k): v for k, v in summary['component_map'].items()}}
            return {'summary': summary, 'report': report, 'raw': raw}
        drafted = self._stage(store, 'synthesis', timings, draft)
        summary = {**drafted['summary'],
                   'component_map': {int(k): v for k, v in drafted['summary'].get('component_map', {}).items()}}
        by_id = {p['chunk_id']: p for p in passages}
        flags = publication.precheck_flags(summary['claims'], by_id, self.v2)

        def check():
            result, report, raw = s3_answer.review(question, summary, passages, notes, flags, comps,
                                                   generate=self.generate)
            result = {**result, 'decisions': {str(k): v for k, v in result['decisions'].items()},
                      'component_checks': {str(k): v for k, v in result['component_checks'].items()}}
            return {'review': result, 'report': report, 'raw': raw}
        reviewed = self._stage(store, 'review', timings, check)
        review_result = {**reviewed['review'],
                         'decisions': {int(k): v for k, v in reviewed['review']['decisions'].items()},
                         'component_checks': {int(k): v for k, v in reviewed['review'].get('component_checks', {}).items()}}
        started = self.clock()
        self._current = 'publication'
        published = s3_answer.publish(summary, review_result, passages, notes, comps, v2=self.v2, gate=self.gate)
        timings['publication'] = round(self.clock() - started, 3)
        return published, drafted, reviewed, flags

    def result(self, question, packet, plan, decision, summary, drafted, reviewed, flags, store):
        out = super().result(question, packet, plan, decision, summary, drafted, reviewed, flags, store)
        out['engine'] = ENGINE
        out['components'] = packet.get('components', [])
        out['evidence_management']['component_searches'] = [s for s in packet.get('searches', [])
                                                            if s.get('role') == 'component']
        return out

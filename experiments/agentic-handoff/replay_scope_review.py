"""Offline before/after for scope review on the saved Stage A runs. No provider is called.

Each arm is replayed through its real orchestrator with quote grounding on, using the recorded plan, synthesis
draft, verifier reply and evidence packet. "after" adds scope fields to each recorded verdict. These are
source-reviewed labels (SCOPE below), written by reading the cited passages. They stand in for what a correct
verifier should return, so this tests the decision logic and the publication outcome, not Gemini's ability to
fill the fields. Only a live run can show that.

    python -B experiments/agentic-handoff/replay_scope_review.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'experiments/agentic'), str(Path(__file__).parent)]
import interpretation_policy  # noqa: E402
import quote_grounding  # noqa: E402
import scope_review  # noqa: E402
from agents import OrchestratorAgent, VERIFIER_PROMPT, ORCHESTRATOR_PROMPT  # noqa: E402
from handoff import EvidenceHandoffOrchestrator  # noqa: E402

RUN = ROOT / 'data/processed/gemini-handoff-paired-v3-grounded-stage-a'
ARMS = {'current': OrchestratorAgent, 'handoff': EvidenceHandoffOrchestrator}

# Source-reviewed scope labels, keyed by the start of the claim text. Sentences are verbatim from the cited passage.
SCOPE = {
    'The evaluation dataset consists of 300': ('MultiFinRAG evaluation question set', 'We created a total of 300 evaluation questions', 'MultiFinRAG evaluation question set', 'same'),
    'The MultiFinRAG evaluation dataset consists of 42': ('MultiFinRAG evaluation question set', 'We created a total of 300 evaluation questions', 'MultiFinRAG evaluation question set', 'same'),
    'For image-based questions, the Baseline': ('image-based questions, Gemma', 'Question / Type: 2. Image-based', 'Table 1 image-based row', 'same'),
    'For table-based questions, the Baseline': ('table-based questions, Gemma', 'Question / Type: 3. Table-based', 'Table 1 table-based row', 'same'),
    'The significant performance gap': (
        'image-based and table-based questions',
        'This improvement underscores the MultiFinRAG framework’s ability to retrieve relevant trunks and integrate information effectively to generate accurate final answers.',
        'questions requiring both text and image/table analysis (0% to 40% with Gemma 3)', 'different'),
    'The Cora dataset contains 2,708 nodes, while': ('Cora and Arxiv node counts', 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708', 'Table 1 Cora and Arxiv rows', 'same'),
    'The Cora dataset uses a random split': ('Cora and Arxiv splits', 'Splitting: Random', 'Table 1 Cora and Arxiv rows', 'same'),
    'The Cora dataset contains 2,708 nodes and': ('Cora', 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708', 'Table 1 Cora row', 'same'),
    'The Arxiv dataset contains 16,316 nodes': ('Arxiv', 'Dataset: Arxiv ( Hu et al., 2020 ; Chen et al., 2023 ); # Nodes: 16,316', 'Table 1 Arxiv row', 'same'),
}


def oracle(claim):
    for start, (claim_scope, sentence, evidence_scope, match) in SCOPE.items():
        if claim['text'].startswith(start):
            return {'claim_scope': claim_scope, 'evidence_sentence': sentence,
                    'evidence_scope': evidence_scope, 'scope_match': match}
    raise KeyError(f"no source-reviewed scope label for: {claim['text'][:60]}")


class Recorded:
    supports_response_schema = True

    def __init__(self, arm_dir, label=oracle):
        read = lambda name: json.loads((arm_dir / name).read_text(encoding='utf-8'))
        self.plan = json.loads((arm_dir.parent / 'shared-plan.json').read_text(encoding='utf-8'))['response']
        self.drafts = [read(f'synthesis-{n}.reply.json')['provider_text'] for n in (1, 2)
                       if (arm_dir / f'synthesis-{n}.reply.json').is_file()]
        self.reviews = [read(f'verification-{n}.reply.json')['provider_text'] for n in (1, 2)
                        if (arm_dir / f'verification-{n}.reply.json').is_file()]
        self.label, self.schemas = label, []

    def __call__(self, prompt, response_schema=None):
        if prompt.startswith(ORCHESTRATOR_PROMPT):
            return self.plan
        if prompt.startswith('Synthesize an answer'):
            return self.drafts.pop(0)
        assert prompt.startswith(VERIFIER_PROMPT)
        self.schemas.append(response_schema)
        reply = json.loads(self.reviews.pop(0))
        if self.label is not None and prompt.startswith(VERIFIER_PROMPT + scope_review.INSTRUCTIONS):
            claims = json.loads(prompt[len(VERIFIER_PROMPT + scope_review.INSTRUCTIONS):])['claims']
            for verdict in reply['verdicts']:
                verdict.update(self.label(claims[verdict['index']]))
        return json.dumps(reply, ensure_ascii=False)


def replay(arm_dir, *, scope, label=oracle, policy=False):
    """label=None replays recorded scope fields as Gemini wrote them."""
    packet = json.loads((arm_dir / 'synthesis-1.evidence.json').read_text(encoding='utf-8'))
    query = json.loads((arm_dir / 'result.json').read_text(encoding='utf-8'))['submitted_request']['query']
    provider = Recorded(arm_dir, label)
    engine = ARMS[arm_dir.name](generate=provider, retrieve=lambda q, k: [dict(p) for p in packet], top_k=8,
                                index_sha256='replay', max_calls=5,
                                **({'research_only': True} if arm_dir.name == 'current' else {}))
    quote_grounding.enable(engine)
    if scope:
        scope_review.enable(engine)
    if policy:
        interpretation_policy.enable(engine)
    result = engine.run(query)
    review = [r for e in result['trace'] if e['type'] == 'reply' and e.get('from') == 'verification_agent'
              for r in e['output'].get('scope_review', [])]
    return {'status': result['status'], 'answer_scope': result['summary'].get('answer_scope'),
            'published': [c['text'] for c in result['summary']['claims']],
            'held': [{'text': h['text'], 'reason': h['verification']['held_reason']}
                     for h in result['summary'].get('held_claims', [])],
            'scope_review': review}


def compare(run=RUN):
    rows = []
    for arm_dir in sorted(run.glob('F*/*')):
        if arm_dir.is_dir():
            rows.append({'case': f'{arm_dir.parent.name}/{arm_dir.name}',
                         'before': replay(arm_dir, scope=False), 'after': replay(arm_dir, scope=True)})
    return rows


if __name__ == '__main__':
    print(json.dumps(compare(), indent=1, ensure_ascii=False))

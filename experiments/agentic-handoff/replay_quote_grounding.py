"""Offline before/after on recorded Gemini synthesis drafts, under the identical saved evidence packets.

Replays each saved synthesis reply through the unchanged synthesis validation (before) and through quote
grounding followed by the same validation (after), then runs the unchanged deterministic number check.
No provider is called. The verifier stage did not run live for drafts that were rejected, so this does not
measure verifier verdicts or live accuracy.

    py -3.14 -B experiments/agentic-handoff/replay_quote_grounding.py [run directory]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'experiments/agentic')]
from numeric_checks import ground_claim  # noqa: E402
from quote_grounding import ground_draft  # noqa: E402
from src.research_chat import synthesize  # noqa: E402

RUN = ROOT / 'data/processed/gemini-handoff-paired-v2-simplified'


def outcome(raw, passages, query):
    def reply(prompt, **_):
        return raw
    reply.supports_response_schema = True
    try:
        summary = synthesize(query, passages, generate=reply)
    except Exception as error:  # the existing pipeline turns this into an abstention
        return {'status': 'rejected', 'reason': f'{type(error).__name__}: {error}'[:160]}
    by_id = {p['chunk_id']: p for p in passages}
    return {'status': summary['status'], 'claims': [
        {'kind': c['kind'], 'chunk_ids': c['chunk_ids'], 'numbers': ground_claim(c, by_id)['status'],
         'text': c['text']} for c in summary['claims']]}


def replay(run=RUN):
    rows = []
    for reply_file in sorted(run.glob('F*/*/synthesis-1.reply.json')):
        arm = reply_file.parent
        passages = json.loads((arm / 'synthesis-1.evidence.json').read_text(encoding='utf-8'))
        query = json.loads((arm / 'result.json').read_text(encoding='utf-8'))['submitted_request']['query']
        raw = json.loads(reply_file.read_text(encoding='utf-8'))['provider_text']
        grounded, notes = ground_draft(raw, passages)
        rows.append({'case': f'{arm.parent.name}/{arm.name}', 'before': outcome(raw, passages, query),
                     'after': outcome(grounded, passages, query), 'grounding': notes})
    return rows


if __name__ == '__main__':
    print(json.dumps(replay(Path(sys.argv[1]) if len(sys.argv) > 1 else RUN), indent=1, ensure_ascii=False))

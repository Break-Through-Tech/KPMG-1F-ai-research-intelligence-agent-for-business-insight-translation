"""Resolve contextual follow-ups into standalone research questions.

Reuses the existing query-clarification contract (src/query_clarification.py, prompt query-clarification-v1,
pre-retrieval phase, no passages). The research engine only ever receives one standalone question, so
Standard S2, its prompts, schemas and seals are untouched, and each turn's retrieval and citations stay
independent. History supplies references (what "it" or "the risks" means), never evidence.

Self-contained questions skip the call. If a context-dependent question cannot be resolved (provider
failure or invalid output), the user is asked to restate it instead of researching a guess.
"""
import re

from src.query_clarification import clarification_with_generation

CONTEXT_CUES = re.compile(
    r"^\s*(?:and|but|also|so|then|what about|how about|what else|why|how so|and what|same|compare)\b|"
    r"\b(?:it|its|it's|they|them|their|theirs|this|that|these|those|there|such|the same|above|previous|"
    r"earlier|former|latter|the risks?|the costs?|the benefits?|the limitations?|the downsides?|"
    r"the evidence|the study|the paper|the results?|that approach|this approach|more detail|elaborate)\b",
    re.I)
SHORT_QUESTION_WORDS = 6
RESTATE = ('I could not connect this follow-up to the earlier questions in this conversation. '
           'Please ask it again as a complete question, for example naming the topic or organisation.')


def needs_context(question, history):
    """Only follow-ups that refer back (or are too short to stand alone) trigger a resolution call."""
    if not history:
        return False
    words = re.findall(r"[\w'-]+", question)
    return len(words) <= SHORT_QUESTION_WORDS or bool(CONTEXT_CUES.search(question))


def resolve(question, history, generate, *, force=False):
    """Return ('research', standalone_question, resolution) or ('clarify', question_text, resolution)."""
    if not force and not needs_context(question, history):
        return 'research', question, {'kind': 'standalone', 'calls': 0}
    try:
        decision = clarification_with_generation(phase='pre', query=question, history=history, passages=[],
                                                 generate=generate)
    except Exception:  # provider, budget, schema or validation failure: never research a guess
        return 'clarify', RESTATE, {'kind': 'resolution_failed', 'calls': 1}
    if decision['decision'] == 'clarify':
        return 'clarify', decision['question'], {'kind': 'clarify', 'calls': 1,
                                                 'options': [o['text'] for o in decision['options']][:6]}
    resolved = ' '.join(decision['resolved_query'].split())
    kind = 'unchanged' if resolved.casefold() == ' '.join(question.split()).casefold() else 'resolved'
    return 'research', resolved, {'kind': kind, 'calls': 1, 'turns_used': len(history) // 2}

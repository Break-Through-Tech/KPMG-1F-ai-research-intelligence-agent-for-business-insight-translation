"""Bounded, untrusted conversation context for the local single-paper preview."""
from copy import deepcopy

MAX_MESSAGES = 12
MAX_MESSAGE_CHARS = 6000
MAX_HISTORY_CHARS = 24000


def validate_history(history):
    """Accept complete user/assistant pairs only; history is never paper evidence."""
    if not isinstance(history, list) or len(history) > MAX_MESSAGES or len(history) % 2:
        raise ValueError('History must contain at most six complete turns.')
    total = 0
    for index, message in enumerate(history):
        role = 'user' if index % 2 == 0 else 'assistant'
        if (not isinstance(message, dict) or set(message) != {'role', 'content'}
                or message['role'] != role or not isinstance(message['content'], str)
                or not message['content'].strip()
                or len(message['content']) > MAX_MESSAGE_CHARS):
            raise ValueError('History requires bounded alternating user/assistant text.')
        try:
            message['content'].encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError('History must contain valid Unicode text.') from None
        total += len(message['content'])
    if total > MAX_HISTORY_CHARS:
        raise ValueError('Conversation context exceeds 24000 characters.')
    return deepcopy(history)

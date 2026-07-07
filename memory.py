# memory.py
from collections import deque

class SessionMemory:
    """
    Lightweight rolling memory.
    Keeps last N turns only.
    """

    def __init__(self, max_turns=6):
        self.history = deque(maxlen=max_turns)

    def add(self, role: str, text: str):
        self.history.append({
            "role": role,
            "text": text
        })

    def get_context_text(self):
        """
        Convert history to short text block for LLM
        """
        lines = []
        for h in self.history:
            lines.append(f'{h["role"]}: {h["text"]}')
        return "\n".join(lines)

    def clear(self):
        self.history.clear()
class RetrievalMemory:
    """
    Cache last retrieved chunks.
    Helps follow-ups avoid re-searching.
    """

    def __init__(self):
        self.last_query = None
        self.last_hits = []

    def save(self, query, hits):
        self.last_query = query
        self.last_hits = hits

    def get(self, query, threshold=0.8):
        """
        simple similarity reuse
        """
        if not self.last_query:
            return None

        if query.lower() in self.last_query.lower():
            return self.last_hits

        return None

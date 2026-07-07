# agent.py

from memory import SessionMemory
from index import hybrid_retrieve
from corrective import needs_correction

# single global memory for this process
memory = SessionMemory(max_turns=6)


def answer_query(query: str):
    """
    Main entrypoint for chat system.
    Flow:
        memory → retrieval → answer → corrective → save → return
    """

    # =========================
    # 1. memory
    # =========================
    memory.add("user", query)

    # =========================
    # 2. retrieval (ONLY ONCE)
    # =========================
    res = hybrid_retrieve(query, k=6)
    hits = res["hits"]
    conf = res["retrieval_confidence"]

    if not hits:
        return "No relevant documents found."

    context_chunks = "\n\n".join(
    f"[{i}] ({h['source']} p.{h.get('page', '-')})\n{h['text']}"
    for i, h in enumerate(hits)
    )


    # =========================
    # 3. build prompt
    # =========================
    conversation = memory.get_context_text()

    prompt = f"""
Use ONLY the provided context.
If answer not present, say you don't know.

Conversation:
{conversation}

Context:
{context_chunks}

Question:
{query}
"""

    # =========================
    # 4. TEMP fake LLM
    # =========================
    answer = context_chunks[:500]

    # =========================
    # 5. corrective guard (AFTER answer)
    # =========================
    if needs_correction(answer, conf, len(hits)):
        answer = "I couldn't find reliable information in the documents."

    # =========================
    # 6. save assistant turn
    # =========================
    memory.add("assistant", answer)

    return answer

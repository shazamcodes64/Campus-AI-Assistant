# corrective.py

def needs_correction(answer: str, retrieval_conf: float, hits_count: int):
    """
    Cheap, deterministic guard.
    No LLM calls. Fast. Reliable.
    """

    # weak retrieval
    if retrieval_conf < 0.30:
        return True

    # nothing retrieved
    if hits_count == 0:
        return True

    # too short answer
    if len(answer.strip()) < 40:
        return True

    return False

# router.py
from faq_matcher import faq_similarity_score

FAQ_HIGH_THRESHOLD = 0.80
FAQ_LOW_THRESHOLD = 0.40


def route_query(query: str) -> dict:
    """
    Decide where a query should go.

    Returns:
    {
        "source": "faq" | "rag" | "out_of_scope",
        "confidence": float,
        "reason": str
    }
    """

    score = faq_similarity_score(query)

    # ---------- STRONG FAQ ----------
    if score >= FAQ_HIGH_THRESHOLD:
        return {
            "source": "faq",
            "confidence": score,
            "reason": "semantic_match_high",
        }

    # ---------- WEAK FAQ → RAG ----------
    if score >= FAQ_LOW_THRESHOLD:
        return {
            "source": "rag",
            "confidence": score,
            "reason": "semantic_match_weak",
        }

    # ---------- OUT OF SCOPE ----------
    return {
        "source": "out_of_scope",
        "confidence": score,
        "reason": "semantic_match_low",
    }

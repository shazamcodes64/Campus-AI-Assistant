# workflow.py

from router import route_query
from faq_matcher import match_faq
from logging_utils import log_faq_event
from llm import generate_answer
from index import retrieve_docs
from faq_promotion import log_promotion_candidate
from core.confidence import estimate_rag_confidence


# -----------------------------
# Configuration
# -----------------------------
RAG_MIN_RETRIEVAL_CONFIDENCE = 0.30
RAG_PROMOTION_THRESHOLD = 0.85
MAX_CONTEXT_CHUNKS = 4


def handle_query(query: str) -> dict:
    """
    Main execution pipeline.

    Returns:
    {
        "answer": str,
        "source": "admin" | "rag" | "out_of_scope",
        "confidence": float | None,
        "sources": list | None
    }
    """

    # ---------- ROUTING ----------
    route = route_query(query)
    source = route["source"]
    route_confidence = route.get("confidence", None)

    # ---------- ADMIN FAQ ----------
    if source == "faq":
        faq_result = match_faq(query)

        assert "confidence" in faq_result, "FAQ result missing confidence"

        log_faq_event(
            user_query=query,
            matched_faq_id=faq_result.get("faq_id"),
            confidence=faq_result["confidence"],
            decision="faq",
        )

        return {
            "answer": faq_result["answer"],
            "source": "admin",
            "confidence": faq_result["confidence"],
            "sources": None,
        }

    # ---------- OUT OF SCOPE ----------
    if source == "out_of_scope":
        log_faq_event(
            user_query=query,
            matched_faq_id=None,
            confidence=route_confidence,
            decision="out_of_scope",
        )

        return {
            "answer": (
                "This question is outside verified academic material. "
                "Please consult faculty or official documentation."
            ),
            "source": "out_of_scope",
            "confidence": None,
            "sources": None,
        }

    # ---------- RAG PIPELINE ----------
    from corrective_rag import corrective_retrieve
    from llm import get_llm  # function to return a reusable llm instance

    llm_instance = get_llm()
    retrieval = corrective_retrieve(llm_instance, query, k=6)
 

    # retrieval is expected to be:
    # {
    #   "hits": [...],
    #   "retrieval_confidence": float
    # }
    hits = retrieval.get("hits", [])
    retrieval_confidence = retrieval.get("retrieval_confidence", 0.0)

    # ---------- RETRIEVAL QUALITY GATE ----------
    if retrieval_confidence < RAG_MIN_RETRIEVAL_CONFIDENCE or not hits:
        log_faq_event(
            user_query=query,
            matched_faq_id=None,
            confidence=retrieval_confidence,
            decision="rag_low_confidence",
        )

        return {
            "answer": (
                "I couldn’t find reliable material to answer this confidently. "
                "Please verify with official sources."
            ),
            "source": "out_of_scope",
            "confidence": retrieval_confidence,
            "sources": None,
        }

    # ---------- CONTEXT BUILDING ----------
    top_hits = hits[:MAX_CONTEXT_CHUNKS]
    context = "\n\n".join(h["text"] for h in top_hits)

    # ---------- ANSWER GENERATION ----------
    answer = generate_answer(
        query=query,
        context=[context],
    )

    # ---------- CONFIDENCE ESTIMATION ----------
    from core.confidence import answer_context_similarity, hallucination_check

    context_text = "\n\n".join(h["text"] for h in top_hits)
    answer = generate_answer(query=query, context=[context_text])

    # 1) answer-context similarity
    sim = answer_context_similarity(answer, context_text)
    if sim < 0.55:
    # too low - reject / warn
        return {
            "answer": "I couldn't find sufficient supporting material to answer confidently. Please consult official sources.",
            "source": "out_of_scope",
            "confidence": sim,
            "sources": top_hits
        }

    # 2) hallucination guard
    passed, ratio = hallucination_check(answer, top_hits)
    if not passed:
    # flag and return low confidence with sources
        return {
            "answer": "The model produced content that couldn't be fully grounded in the retrieved sources. Please verify with the provided sources.",
            "source": "rag",
            "confidence": sim * ratio,
            "sources": top_hits
        }

    # otherwise proceed; estimate final rag_confidence combining retrieval_confidence and sim
    rag_confidence = (retrieval_confidence * 0.5) + (sim * 0.5)


    # ---------- LOGGING ----------
    log_faq_event(
        user_query=query,
        matched_faq_id=None,
        confidence=rag_confidence,
        decision="rag",
    )

    # ---------- AUTO-PROMOTION (LOG ONLY) ----------
    if rag_confidence >= RAG_PROMOTION_THRESHOLD and len(top_hits) >= 2:
        log_promotion_candidate(
            query=query,
            answer=answer,
            confidence=rag_confidence,
            source_docs=[h["chunk_id"] for h in top_hits],
        )


    # ---------- FINAL RESPONSE ----------
    return {
        "answer": answer,
        "source": "rag",
        "confidence": rag_confidence,
        "sources": top_hits,
    }

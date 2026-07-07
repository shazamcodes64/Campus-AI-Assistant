# faq_matcher.py

from pathlib import Path
import json
from sentence_transformers import SentenceTransformer, util

# -------------------------------
# Model (loaded once – this is OK)
# -------------------------------
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

FAQ_PATH = Path("data/faq.json")

# -------------------------------
# FAQ Loader (HOT-RELOAD SAFE)
# -------------------------------
def load_faq():
    if not FAQ_PATH.exists():
        return []
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------
# Embedding helper (recomputed safely)
# -------------------------------
def _embed_questions(faq_data):
    questions = [item["question"] for item in faq_data]
    if not questions:
        return [], None
    embeddings = _MODEL.encode(
        questions,
        normalize_embeddings=True
    )
    return questions, embeddings

# ============================================================
# ROUTER USE ONLY
# ============================================================
def faq_similarity_score(query: str) -> float:
    """
    Used ONLY by router.py
    Returns a float between 0.0 and 1.0
    """

    if not query:
        return 0.0

    faq_data = load_faq()
    questions, embeddings = _embed_questions(faq_data)

    if not questions:
        return 0.0

    query_embedding = _MODEL.encode(
        query,
        normalize_embeddings=True
    )

    scores = util.cos_sim(query_embedding, embeddings)
    max_score = float(scores.max())

    return max(0.0, min(1.0, max_score))

# ============================================================
# WORKFLOW USE ONLY
# ============================================================
def match_faq(query: str) -> dict:
    """
    Used ONLY by workflow.py
    Returns:
    {
        "answer": str,
        "confidence": float
    }
    """

    faq_data = load_faq()
    questions, embeddings = _embed_questions(faq_data)

    if not questions:
        return {
            "answer": None,
            "confidence": 0.0
        }

    query_embedding = _MODEL.encode(
        query,
        normalize_embeddings=True
    )

    scores = util.cos_sim(query_embedding, embeddings)
    best_idx = int(scores.argmax())
    confidence = float(scores.max())

    return {
        "answer": faq_data[best_idx]["answer"],
        "confidence": max(0.0, min(1.0, confidence)),
    }

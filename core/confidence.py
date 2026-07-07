# experiment/core/confidence.py

def estimate_rag_confidence(answer: str, docs_count: int) -> float:
    """
    VERY conservative heuristic.
    This is NOT a probability.
    """

    if not answer or len(answer.strip()) < 40:
        return 0.2

    base = min(0.6 + (docs_count * 0.1), 0.9)

    # Penalize vague answers
    vague_phrases = [
        "may", "might", "generally", "typically",
        "it depends", "approximately"
    ]

    penalty = sum(0.05 for p in vague_phrases if p in answer.lower())

    return max(0.0, round(base - penalty, 2))
# core/confidence.py
from sentence_transformers import SentenceTransformer, util
import numpy as np
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

_EMBED = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(texts):
    return _EMBED.encode(texts, normalize_embeddings=True)

def answer_context_similarity(answer: str, context: str) -> float:
    a_emb = _EMBED.encode([answer], normalize_embeddings=True)
    c_emb = _EMBED.encode([context], normalize_embeddings=True)
    sim = util.cos_sim(a_emb, c_emb)[0][0]
    return float(sim)

def extract_entities(text: str):
    if nlp is None:
        # simple fallback: collect capitalized tokens (naive)
        words = set([w.strip(".,") for w in text.split() if w[0].isupper()])
        return words
    doc = nlp(text)
    ents = set([ent.text for ent in doc.ents])
    return ents

def hallucination_check(answer: str, sources: list, entity_threshold=0.5):
    """
    Check if entities in answer are mostly present in sources.
    Returns (passed:bool, overlap_ratio)
    """
    answer_entities = extract_entities(answer)
    if not answer_entities:
        return True, 1.0
    source_text = " ".join([s.get("text", "") for s in sources])
    source_entities = extract_entities(source_text)
    overlap = len(answer_entities & source_entities)
    ratio = overlap / len(answer_entities)
    return (ratio >= entity_threshold), ratio

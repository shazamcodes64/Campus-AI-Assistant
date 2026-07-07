# index.py
# ======================================================
# CLEAN + PRODUCTION-READY HYBRID RETRIEVAL
# ======================================================

from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from retrieval import pdf_retrieve
from bm25_index import load_bm25_data
from rerank import apply_source_diversity, mmr_rerank
from query_utils import expand_query
from memory import RetrievalMemory
_retrieval_memory = RetrievalMemory()


# ======================================================
# GLOBALS
# ======================================================

BASE = Path(__file__).resolve().parent
META_FILE = BASE / "data" / "index" / "meta.json"

_embed_model = SentenceTransformer("all-MiniLM-L6-v2")

SEMANTIC_WEIGHT = 0.65
LEXICAL_WEIGHT = 0.35
MIN_SCORE = 0.25


# ======================================================
# BM25
# ======================================================

def _build_bm25():
    data = load_bm25_data()
    if data is None:
        return None

    tokenized = [doc.split() for doc in data["corpus"]]
    return BM25Okapi(tokenized)


# ======================================================
# MAIN RETRIEVAL
# ======================================================

def hybrid_retrieve(query: str, k: int = 6):
    """
    Pipeline:
    expand → vector → BM25 → hybrid score →
    threshold → source diversity → MMR → confidence
    """
    cached = _retrieval_memory.get(query)
    if cached:
        return {
         "hits": cached,
            "retrieval_confidence": 0.9,
         "cached": True
        }


    # --------------------------------------------------
    # 1. Query expansion
    # --------------------------------------------------
    query = expand_query(query)

    # --------------------------------------------------
    # 2. Vector retrieval
    # --------------------------------------------------
    vec_res = pdf_retrieve(query, k=k * 3)
    vec_hits = vec_res.get("hits", [])

    if not META_FILE.exists():
        return {"hits": [], "retrieval_confidence": 0.0}

    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # --------------------------------------------------
    # 3. BM25 lexical retrieval
    # --------------------------------------------------
    bm25 = _build_bm25()
    lex_scores = {}

    if bm25:
        scores = bm25.get_scores(query.split())
        for idx, s in enumerate(scores):
            lex_scores[idx] = float(s)

    # --------------------------------------------------
    # 4. Candidate union
    # --------------------------------------------------
    candidates = {}

    for h in vec_hits:
        idx = h["chunk_index"]
        candidates[idx] = {
            "meta": meta[idx],
            "vec": h["score"],
            "lex": lex_scores.get(idx, 0.0),
        }

    for idx, s in lex_scores.items():
        if idx not in candidates:
            candidates[idx] = {
                "meta": meta[idx],
                "vec": 0.0,
                "lex": s,
            }

    if not candidates:
        return {"hits": [], "retrieval_confidence": 0.0}

    # --------------------------------------------------
    # 5. Hybrid scoring
    # --------------------------------------------------
    max_lex = max((c["lex"] for c in candidates.values()), default=1.0) + 1e-9

    combined = []

    for idx, c in candidates.items():
        score = (
            SEMANTIC_WEIGHT * c["vec"] +
            LEXICAL_WEIGHT * (c["lex"] / max_lex)
        )

        if score < MIN_SCORE:
            continue

        item = c["meta"].copy()
        item["score"] = score
        item["chunk_index"] = idx
        item.setdefault("page", -1)
        item.setdefault("source", "unknown")

        combined.append(item)

    if not combined:
        return {"hits": [], "retrieval_confidence": 0.0}

    # --------------------------------------------------
    # 6. Early cut (speed)
    # --------------------------------------------------
    combined = sorted(combined, key=lambda x: x["score"], reverse=True)[:k * 4]

    # --------------------------------------------------
    # 7. Source diversity
    # --------------------------------------------------
    diverse = apply_source_diversity(combined)

    # --------------------------------------------------
    # 8. MMR rerank
    # --------------------------------------------------
    candidate_texts = [c["text"] for c in diverse]

    cand_embs = _embed_model.encode(
        candidate_texts,
        normalize_embeddings=True
    )

    q_emb = _embed_model.encode(
        [query],
        normalize_embeddings=True
    )

    hits = mmr_rerank(
        q_emb,
        cand_embs,
        diverse,
        k=k
    )

    # --------------------------------------------------
    # 9. Confidence gating
    # --------------------------------------------------
    scores = [h["score"] for h in hits]
    retrieval_conf = float(np.mean(scores)) if scores else 0.0
    _retrieval_memory.save(query, hits)


    return {
        "hits": hits,
        "retrieval_confidence": retrieval_conf,
        "needs_web": retrieval_conf < 0.30
    }

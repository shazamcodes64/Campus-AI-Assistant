# index.py
from pdf_ingest import retrieve as pdf_retrieve
from bm25_index import load_bm25_data
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util
import numpy as np
import json
from pathlib import Path
from rerank import apply_source_diversity, mmr_rerank


BASE = Path(__file__).resolve().parent
BM25_META = BASE / "data" / "index" / "bm25_meta.json"
META_FILE = BASE / "data" / "index" / "meta.json"

# weights (tune)
SEMANTIC_WEIGHT = 0.65
LEXICAL_WEIGHT = 0.35
MIN_SCORE = 0.25

_embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def _build_bm25():
    d = load_bm25_data()
    if d is None:
        # build BM25 on the fly from meta.json
        if not META_FILE.exists():
            return None
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        corpus = [m["text"].split() for m in meta]
        return BM25Okapi(corpus)
    tokenized = [doc.split() for doc in d["corpus"]]
    return BM25Okapi(tokenized)

def hybrid_retrieve(query: str, k: int = 6):
    """
    Hybrid retrieval = Vector + BM25 + Source Diversity + MMR
    Returns:
    {
        "hits": [ ... ],
        "retrieval_confidence": float
    }
    """

    # ---------- 1. Vector retrieval ----------
    vec_res = pdf_retrieve(query, k=k * 3)
    vec_hits = vec_res.get("hits", [])

    if not META_FILE.exists():
        return {"hits": [], "retrieval_confidence": 0.0}

    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # ---------- 2. BM25 retrieval ----------
    bm25 = _build_bm25()
    lex_scores = {}

    if bm25:
        tokenized_query = query.split()
        scores = bm25.get_scores(tokenized_query)
        max_score = max(scores) if scores else 1.0
        for idx, s in enumerate(scores):
            lex_scores[idx] = float(s / (max_score + 1e-9))

    # ---------- 3. Merge candidates ----------
    candidates = {}

    # from vector hits
    for h in vec_hits:
        idx = h.get("chunk_index")
        if idx is None:
            continue
        candidates[idx] = {
            "meta": meta[idx],
            "vec_score": h["score"],
            "lex_score": lex_scores.get(idx, 0.0),
        }

    # from lexical hits
    for idx, lex_s in lex_scores.items():
        if idx not in candidates:
            candidates[idx] = {
                "meta": meta[idx],
                "vec_score": 0.0,
                "lex_score": lex_s,
            }

    # ---------- 4. Combine scores ----------
    combined = []
    for idx, v in candidates.items():
        score = (
            SEMANTIC_WEIGHT * v["vec_score"]
            + LEXICAL_WEIGHT * v["lex_score"]
        )

        item = v["meta"].copy()
        item["score"] = score
        item["chunk_index"] = idx
        combined.append(item)

    if not combined:
        return {"hits": [], "retrieval_confidence": 0.0}
    # 🔒 filter weak matches
    combined = [c for c in combined if c["score"] >= MIN_SCORE]

    hits = combined[:k]

    retrieval_conf = float(np.mean([h["score"] for h in hits[:3]])) if hits else 0.0


    # =====================================================
    # 🔥 THIS IS THE PART YOU WERE ASKING ABOUT 🔥
    # =====================================================

    # ---------- 5. Source diversity penalty ----------
    diverse = apply_source_diversity(combined)

    # ---------- 6. MMR reranking ----------
    # take top candidates only (efficiency)
    candidate_pool = diverse[: k * 3]

    candidate_texts = [c["text"] for c in candidate_pool]

    cand_embs = _embed_model.encode(
        candidate_texts, normalize_embeddings=True
    )
    q_emb = _embed_model.encode(
        [query], normalize_embeddings=True
    )

    hits = mmr_rerank(
        q_emb,
        cand_embs,
        candidate_pool,
        k=k,
        lambda_param=0.6,
    )

    # ---------- 7. Final confidence ----------
    avg_score = sum(h["score"] for h in hits) / len(hits)

    return {
        "hits": hits,
        "retrieval_confidence": round(avg_score, 3),
    }


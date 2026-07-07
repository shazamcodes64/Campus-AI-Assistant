# retrieval.py
from sentence_transformers import SentenceTransformer, util
import json
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent
META_FILE = BASE / "data" / "index" / "meta.json"

_embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def pdf_retrieve(query: str, k: int = 10):
    if not META_FILE.exists():
        return {"hits": [], "retrieval_confidence": 0.0}

    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    texts = [m["text"] for m in meta]
    doc_embs = _embed_model.encode(texts, normalize_embeddings=True)
    q_emb = _embed_model.encode([query], normalize_embeddings=True)

    scores = util.cos_sim(q_emb, doc_embs)[0].cpu().numpy()
    top_idx = np.argsort(-scores)[:k]

    hits = []
    for i in top_idx:
        h = meta[i].copy()
        h["score"] = float(scores[i])
        h["chunk_index"] = i
        hits.append(h)

    return {
        "hits": hits,
        "retrieval_confidence": float(np.mean([h["score"] for h in hits])) if hits else 0.0
    }

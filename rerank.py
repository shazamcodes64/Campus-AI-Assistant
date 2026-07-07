# rerank.py
from sentence_transformers import util
import numpy as np

def apply_source_diversity(hits, decay=[1.0, 0.6, 0.35]):
    """
    Given hits (list of dicts with 'source' and 'page'), applies multiplicative decay to repeated (source,page).
    Returns new list sorted by adjusted_score.
    """
    seen = {}
    new_hits = []
    for h in hits:
        key = (h.get("source"), h.get("page"))
        count = seen.get(key, 0)
        weight = decay[count] if count < len(decay) else decay[-1] * (0.5 ** (count - len(decay) + 1))
        seen[key] = count + 1
        h2 = h.copy()
        h2["adj_score"] = h2.get("score", 0.0) * weight
        new_hits.append(h2)
    new_hits.sort(key=lambda x: x["adj_score"], reverse=True)
    return new_hits

def mmr_rerank(query_embedding, candidate_embeddings, candidates, k=4, lambda_param=0.6):
    """
    Simple MMR: candidates is list of dicts; candidate_embeddings aligned with candidates.
    Returns top-k candidates.
    """
    selected = []
    selected_embs = []
    candidate_idxs = list(range(len(candidates)))
    import numpy as np
    sim = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().numpy()
    # precompute pairwise similarities
    pairwise = util.cos_sim(candidate_embeddings, candidate_embeddings).cpu().numpy()

    while len(selected) < k and candidate_idxs:
        mmr_scores = []
        for idx in candidate_idxs:
            if not selected_embs:
                mmr = sim[idx]
            else:
                max_sim_to_selected = max(pairwise[idx][s] for s in [i for i, _ in enumerate(selected)])
                mmr = lambda_param * sim[idx] - (1 - lambda_param) * max_sim_to_selected
            mmr_scores.append((mmr, idx))
        mmr_scores.sort(reverse=True)
        best = mmr_scores[0][1]
        selected.append(candidates[best])
        selected_embs.append(candidate_embeddings[best])
        candidate_idxs.remove(best)
    return selected

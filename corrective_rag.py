# corrective_rag.py
from llm import generate_answer, llm_complete  # adapt to your llm interface
from index import hybrid_retrieve

TRANSFORM_PROMPT = (
    "Rewrite the user query to be more specific and retrieval-friendly. "
    "Original query:\n\n{query}\n\n"
    "Provide the rewritten query only."
)

def rewrite_query(llm, query: str) -> str:
    # LLM should return the rewritten query text only
    prompt = TRANSFORM_PROMPT.format(query=query)
    # if you have a function llm.complete(prompt) that returns text
    rewritten = llm.complete(prompt).text if hasattr(llm, "complete") else llm(prompt)
    return rewritten.strip()

def corrective_retrieve(llm, query: str, k=6, min_good=2):
    # first pass
    res = hybrid_retrieve(query, k=k)
    hits = res.get("hits", [])
    if len(hits) >= min_good and res.get("retrieval_confidence", 0.0) >= 0.25:
        return res

    # otherwise rewrite query and try again (one retry)
    rewritten = rewrite_query(llm, query)
    if rewritten and rewritten != query:
        res2 = hybrid_retrieve(rewritten, k=k)
        # merge results prefer higher scores
        merged = {h["chunk_index"]: h for h in (hits + res2.get("hits", []))}
        # sorted
        merged_list = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return {"hits": merged_list[:k], "retrieval_confidence": float(sum(h["score"] for h in merged_list[:k]) / (len(merged_list[:k]) or 1))}
    return res

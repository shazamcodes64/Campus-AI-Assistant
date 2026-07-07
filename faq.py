# core/faq.py

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def build_faq_index(admin_data, embeddings):
    """
    Builds FAQ embeddings from admin FAQ JSON
    """
    questions = []
    answers = []

    for item in admin_data:
        questions.append(item["question"])
        answers.append(item["answer"])

    faq_embeddings = embeddings.embed_documents(questions)

    return questions, answers, np.array(faq_embeddings)


def semantic_faq_match(
    query,
    embeddings,
    faq_embeddings,
    faq_answers,
    threshold: float = 0.75,  # HARD SAFETY GATE
):
    """
    Returns (faq_hit, score)

    faq_hit = None if below threshold
    """

    if not faq_embeddings.any():
        return None, 0.0

    query_embedding = embeddings.embed_query(query)
    scores = cosine_similarity(
        [query_embedding], faq_embeddings
    )[0]

    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])

    if best_score < threshold:
        return None, best_score

    return {
        "answer": faq_answers[best_idx],
        "score": best_score,
    }, best_score

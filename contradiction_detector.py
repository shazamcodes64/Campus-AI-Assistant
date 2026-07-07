from sentence_transformers import SentenceTransformer, util
from pathlib import Path
import json

_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
FAQ_PATH = Path("data/faq.json")

SIMILAR_QUESTION_THRESHOLD = 0.80
ANSWER_SIMILARITY_THRESHOLD = 0.70


def load_faq():
    if not FAQ_PATH.exists():
        return []
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_contradictions(new_question: str, new_answer: str):
    """
    Returns a list of possible contradictions.
    Empty list = safe
    """

    faq_data = load_faq()
    if not faq_data:
        return []

    questions = [item["question"] for item in faq_data]
    answers = [item["answer"] for item in faq_data]

    q_embeddings = _MODEL.encode(questions, normalize_embeddings=True)
    a_embeddings = _MODEL.encode(answers, normalize_embeddings=True)

    new_q_emb = _MODEL.encode(new_question, normalize_embeddings=True)
    new_a_emb = _MODEL.encode(new_answer, normalize_embeddings=True)

    q_scores = util.cos_sim(new_q_emb, q_embeddings)[0]
    a_scores = util.cos_sim(new_a_emb, a_embeddings)[0]

    contradictions = []

    for idx, q_score in enumerate(q_scores):
        if float(q_score) >= SIMILAR_QUESTION_THRESHOLD:
            answer_similarity = float(a_scores[idx])

            if answer_similarity < ANSWER_SIMILARITY_THRESHOLD:
                contradictions.append({
                    "existing_question": questions[idx],
                    "existing_answer": answers[idx],
                    "question_similarity": float(q_score),
                    "answer_similarity": answer_similarity
                })

    return contradictions

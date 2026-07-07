import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def load_faq(path="data/faq.json"):
    with open(path, "r") as f:
        data = json.load(f)
    return data


def build_faq_index(faq_data, embeddings):
    questions = [x["question"] for x in faq_data]
    answers = [x["answer"] for x in faq_data]

    vectors = embeddings.embed_documents(questions)
    return questions, answers, np.array(vectors)


def match_faq(query, embeddings, faq_vectors, faq_answers, threshold=0.75):
    query_vec = embeddings.embed_query(query)

    scores = cosine_similarity([query_vec], faq_vectors)[0]
    idx = int(np.argmax(scores))
    score = float(scores[idx])

    if score < threshold:
        return None, score

    return faq_answers[idx], score

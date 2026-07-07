# faq_promotion.py
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

PROMOTION_LOG = LOG_DIR / "promotion_queue.jsonl"


def log_promotion_candidate(query, answer, confidence, source_docs):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
        "answer": answer,
        "confidence": confidence,
        "source_docs": source_docs,
        "status": "pending_review",
    }

    with open(PROMOTION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

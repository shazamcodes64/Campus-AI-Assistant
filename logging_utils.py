from typing import Optional
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

FAQ_LOG_FILE = LOG_DIR / "faq_logs.jsonl"

def log_faq_event(
    user_query: str,
    matched_faq_id: Optional[str],
    confidence: float,
    decision: str,  # "faq" or "rag"
):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_query": user_query,
        "matched_faq_id": matched_faq_id,
        "confidence": confidence,
        "decision": decision,
    }

    with open(FAQ_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


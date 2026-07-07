import json
from pathlib import Path

FAQ_PATH = Path("faq/faq.json")

def load_faqs():
    if not FAQ_PATH.exists():
        raise FileNotFoundError("faq.json not found")

    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    # Hard validation (prevents silent bugs)
    for faq in faqs:
        if not all(k in faq for k in ("id", "question", "answer")):
            raise ValueError(f"Invalid FAQ format: {faq}")

    return faqs

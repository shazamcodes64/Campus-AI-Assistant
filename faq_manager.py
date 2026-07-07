# faq_manager.py
from pathlib import Path
import json
from datetime import datetime, timedelta

FAQ_FILE = Path("data/faq.json")
ARCHIVE_FILE = Path("logs/faq_archive.jsonl")

DEFAULT_TTL_DAYS = 365

def _now_iso():
    return datetime.utcnow().isoformat()

def load_all_faqs():
    if not FAQ_FILE.exists():
        return []
    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_faqs(faqs):
    FAQ_FILE.parent.mkdir(exist_ok=True)
    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(faqs, f, indent=2)

def active_faqs():
    faqs = load_all_faqs()
    active = []
    for f in faqs:
        expires_at = f.get("expires_at")
        if not expires_at:
            active.append(f)
            continue
        if datetime.fromisoformat(expires_at) > datetime.utcnow():
            active.append(f)
        else:
            # archive
            append_archive(f)
    return active

def add_faq(question, answer, ttl_days=None):
    faqs = load_all_faqs()
    now = datetime.utcnow()
    ttl = ttl_days if ttl_days is not None else DEFAULT_TTL_DAYS
    entry = {
        "question": question,
        "answer": answer,
        "verified": True,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=ttl)).isoformat()
    }
    faqs.append(entry)
    save_all_faqs(faqs)
    return entry

def append_archive(faq):
    ARCHIVE_FILE.parent.mkdir(exist_ok=True)
    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"archived_at": _now_iso(), **faq}) + "\n")

from pathlib import Path
import json
from rank_bm25 import BM25Okapi
import re

BASE = Path(__file__).resolve().parent
META_FILE = BASE / "data" / "index" / "meta.json"
BM25_META = BASE / "data" / "index" / "bm25_meta.json"

def _clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def build_bm25_index():
    if not META_FILE.exists():
        print("meta.json missing - run pdf_ingest.build_index() first")
        return None

    with open(META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    corpus = [_clean(m["text"]) for m in meta]
    tokenized = [doc.split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)

    BM25_META.parent.mkdir(parents=True, exist_ok=True)
    with open(BM25_META, "w", encoding="utf-8") as f:
        json.dump({"corpus": corpus}, f, indent=2)

    return bm25

def load_bm25_data():
    if not BM25_META.exists():
        return None
    with open(BM25_META, "r", encoding="utf-8") as f:
        return json.load(f)

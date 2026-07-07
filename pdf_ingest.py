# pdf_ingest.py
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from PyPDF2 import PdfReader

# ---------------- CONFIG ----------------

BASE = Path(__file__).resolve().parent
PDF_DIR = BASE / "data" / "pdfs"
INDEX_DIR = BASE / "data" / "index"

META_FILE = INDEX_DIR / "meta.json"
EMB_FILE = INDEX_DIR / "embeddings.npy"
FAISS_FILE = INDEX_DIR / "faiss.index"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# ----------------------------------------

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += size - overlap

    return chunks


def build_index():
    if not PDF_DIR.exists():
        raise RuntimeError("data/pdfs directory does not exist")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    embedder = SentenceTransformer(EMBED_MODEL_NAME)

    meta = []
    embeddings = []

    global_chunk_index = 0

    print("📄 Reading PDFs...")

    for pdf_path in PDF_DIR.glob("*.pdf"):
        pdf_name = pdf_path.name
        reader = PdfReader(str(pdf_path))

        pdf_chunk_count = 0

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if not page_text or not page_text.strip():
                continue

            chunks = chunk_text(page_text)

            for chunk_idx, chunk in enumerate(chunks):
                emb = embedder.encode(chunk, normalize_embeddings=True)

                meta.append({
                    "chunk_index": global_chunk_index,
                    "text": chunk,
                    "source": pdf_name,
                    "page": page_num,
                    "chunk_id": f"{pdf_name}:{page_num}:{chunk_idx}"
                })

                embeddings.append(emb)
                global_chunk_index += 1
                pdf_chunk_count += 1

        print(f"  → {pdf_name}: {pdf_chunk_count} chunks")

    if not embeddings:
        raise RuntimeError("No text chunks found in PDFs")

    embeddings = np.vstack(embeddings).astype("float32")

    print(f"🔢 Total chunks: {len(meta)}")
    print(f"📐 Embedding dim: {embeddings.shape[1]}")

    # ---- Save metadata ----
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    np.save(EMB_FILE, embeddings)

    # ---- FAISS index ----
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, str(FAISS_FILE))

    print("✅ Index build complete")
    print(f"   meta.json → {META_FILE}")
    print(f"   embeddings.npy → {EMB_FILE}")
    print(f"   faiss.index → {FAISS_FILE}")


if __name__ == "__main__":
    build_index()

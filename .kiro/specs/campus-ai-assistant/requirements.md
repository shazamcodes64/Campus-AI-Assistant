# Campus AI Assistant — Requirements & High-Level Design (MVP)

## 1. Document Info

- **Name**: Campus AI Assistant — Requirements & High-Level Design (MVP)
- **Target**: Single-node, classroom MVP for ~70 students (local Ollama LLM + FAISS + BM25)
- **Goal**: Produce a working hybrid FAQ + RAG assistant with clear confidence, citations and admin-driven FAQ promotion

## 2. Purpose & Scope

Provide an on-prem / local Streamlit web app that answers academic questions using:

- **Curated FAQ** (hot-reloadable JSON), and
- **Hybrid RAG** over institutional PDFs (FAISS + BM25)

With a confidence estimator, citations, and admin promotion workflow.

**MVP Constraints**: Single-node, 8–16GB RAM recommended, local LLM via Ollama, quick ship-first then optimize.

## 3. Glossary

- **RAG** — Retrieval-Augmented Generation (vector + lexical + LLM)
- **FAQ DB** — Curated JSON of Q/A pairs (hot-reloadable)
- **Chunk** — A text slice of a PDF (keeps text, source, page, chunk_id)
- **Retrieval Confidence** — Mean (top-k) chunk scores
- **Auto-promotion** — Flagging high-confidence generated answers for admin review

## 4. System Limits & Non-Functional Requirements (MVP)

- **Max corpus size**: 5GB (total PDFs)
- **Max FAQ entries initially**: 1,000
- **Concurrent users target**: 70 (class), QPS target < 10
- **Cold-start time target**: <60s
- **Memory budget**: ≤4GB typical, 8–16GB recommended for smooth operations
- **Response time SLA (95%)**: <5–10s end-to-end
- **Logging retention**: 30 days (JSONL rotated)

## 5. Functional Requirements (Condensed)

### 5.1 Query Routing

1. Validate and sanitize query (max 1000 chars)
2. Compute embedding with `all-MiniLM-L6-v2` (singleton)
3. Compute routing confidence:
   - **FAQ route** if similarity ≥ 0.8
   - **Document route** if similarity ≥ 0.5
   - **Out-of-scope** otherwise
4. Log classification decision

### 5.2 FAQ Engine

1. Load FAQ JSON; validate schema
2. Compute FAQ embeddings; cache for 1 hour
3. Return an FAQ answer with confidence = similarity if ≥ 0.8
4. Hot-reload support for admins

### 5.3 RAG / Document Retrieval

**Index**: FAISS (IndexFlatIP, 384-dim) + BM25 (rank_bm25 or Whoosh)

**Chunking**: 400–512 tokens, overlap ~50 (tune; starting 400)

**Retrieval Flow**:
1. Query expansion (WordNet / synonyms optional)
2. Run FAISS (top-5) and BM25 (top-5) in parallel
3. Normalize scores (min-max) then fuse: semantic_weight default 0.6, lexical 0.4
4. Apply source diversity penalty
5. Optionally MMR rerank to top-k (λ=0.6–0.7)
6. Filter by MIN_SCORE = 0.25
7. Return chunks with metadata: `{text, source, page, chunk_index, score}`

### 5.4 Response Generation

1. If a single chunk has very high similarity (> 0.85) — return chunk text directly (no LLM)
2. Otherwise synthesize with local Ollama model (llama2:7b or chosen model)
3. Prompt template: include explicit instruction to cite only given sources
4. Confidence = weighted function: 0.4 * retrieval + 0.3 * relevance + 0.3 * coherence
5. If confidence < 0.6, append uncertainty disclaimer and provide sources

### 5.5 Admin / FAQ Promotion

1. Auto-flag responses with confidence >= 0.85 and source_docs >= 2
2. Admins review flagged items: approve → create new FAQ version (never overwrite)
3. Maintain versioned FAQ snapshots and audit logs

## 6. Data Schemas

### 6.1 faq.json (Example)

```json
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process consists of ...",
      "category": "placements",
      "created_date": "2025-07-01T10:00:00Z",
      "ttl_days": 365,
      "embedding": [0.001, -0.002, ...]
    }
  ],
  "metadata": {
    "last_updated": "2025-07-01T10:00:00Z",
    "total_entries": 1,
    "embedding_model": "all-MiniLM-L6-v2"
  }
}
```

### 6.2 Chunk/Meta (meta.json Entry)

```json
{
  "chunk_index": 123,
  "chunk_id": "filename.pdf:page:chunknum",
  "text": "chunk text ...",
  "source": "filename.pdf",
  "page": 12,
  "created_date": "2025-07-01T10:00:00Z"
}
```

### 6.3 Interaction Log (JSONL)

```json
{
  "timestamp": "ISO8601",
  "session_id": "xxx",
  "query": "...",
  "route": "faq|rag|out_of_scope",
  "response": "...",
  "confidence": 0.72,
  "sources": ["file.pdf#page"]
}
```

## 7. Component Interfaces (APIs / Function Signatures)

### Query Router
```python
def classify_query(query: str) -> {
    "route": "faq"|"rag"|"out_of_scope",
    "confidence": float
}
```

### FAQ Engine
```python
def search_faq(query: str) -> {
    "answer": str | None,
    "confidence": float,
    "source_id": str | None
}
```

### Document Retrieval (RAG)
```python
def retrieve_documents(query: str, top_k: int=6) -> {
    "hits": [chunks],
    "retrieval_confidence": float
}
```

### Response Generator
```python
def generate_response(query: str, chunks: list, route: str) -> {
    "answer": str,
    "confidence": float,
    "sources": list
}
```

### Indexer (Offline)
```python
def build_indices(pdf_dir: str) -> write(
    meta.json,
    embeddings.npy,
    faiss.index,
    bm25_meta.json
)
```

## 8. High-Level Architecture (ASCII)

```
User (Streamlit)
   │
   ▼
Input validation -> QueryRouter
   ├─ FAQ path -> FAQ Engine (json, embeddings cache) -> quick answer
   └─ Document path -> Document Retrieval Engine
                        ├─ FAISS (dense) (top N)
                        ├─ BM25 (sparse) (top N)
                        ├─ Score fusion + divergence + MMR
                        └─ return top chunks
   ▼
Response Generator
   ├─ single-high-confidence chunk? return chunk
   └─ else call LLM (Ollama) with context + citations
   ▼
UI display + logs
```

## 9. Reranking & Safety Rules (Core Logic)

- **Source diversity penalty**: Multiplicative decay per repeated (source, page) using decay list [1.0, 0.6, 0.35, 0.175...]
- **MMR**: `mmr(q_emb, candidate_embs, k, lambda=0.6)` to avoid semantic duplicates
- **Hallucination guard**: Parse LLM output; reject claims referencing entities not in provided chunks (if detected, return uncertainty + sources)
- **Minimum combined score**: MIN_SCORE = 0.25 (drop low matches)
- **FAQ vs doc comparison**: FAQ can only win if `faq_score >= 0.8 AND faq_score >= best_doc_score + delta` (delta configurable, e.g., 0.05)

## 10. Implementation Milestones (MVP Two-Week Plan)

### Week 1 — Foundation & Retrieval

- **Day 1**: Project skeleton, config, Streamlit skeleton, singleton model loads, indexer.py initial
- **Day 2**: PDF ingestion, chunking, FAISS + BM25 build, meta.json generation
- **Day 3**: retrieve_documents with merged scoring, min-score filtering, source diversity
- **Day 4**: faq_engine + hot-reload of faq.json
- **Day 5**: Local integration tests + test_system.py smoke

### Week 2 — LLM & UI & Hardening

- **Day 6**: response_generator (Ollama integration), single-chunk fast-path
- **Day 7**: Streamlit UI, confidence meter, sources panel
- **Day 8**: Failure hunting + failure_hunter.py (50-query torture list)
- **Day 9**: Performance tuning, caching @st.cache_resource for engines
- **Day 10**: Admin FAQ promotion flow, docs, deploy script

## 11. Tests & Validation

### Unit Tests
- Query routing, FAQ matching, BM25/FAISS scoring, rerank functions, indexer (sample PDFs)

### End-to-End Tests
- **Smoke tests**: Indexing + search + LLM generate
- **Automated evaluation**: `scripts/auto_eval.py` (run with `python -m scripts.auto_eval`)

### Brutal Testing
- **failure_hunter.py** — 50 messy queries (typos, missing docs, contradictory sources)

### Acceptance
- Accuracy ≥ 80% on "exists-and-correct" metric, with missing doc rate logged and surfaced

## 12. Deployment & Run Commands (MVP)

### Install
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Index PDFs
```bash
python indexer.py
# creates data/index/meta.json, embeddings.npy, faiss.index, bm25_meta.json
```

### Run Web App
```bash
# preferred: ensure working dir is project root
streamlit run app.py
```

### Run Scripts as Modules (Avoid Import Path Problems)
```bash
python -m scripts.auto_eval
python -m scripts.failure_hunter
```

## 13. Config & Requirements (Copy Ready)

### config.json (Minimal)

```json
{
  "models": {
    "embedding_model": "all-MiniLM-L6-v2",
    "ollama_url": "http://localhost:11434",
    "llm_model": "llama2:7b"
  },
  "thresholds": {
    "faq_confidence": 0.8,
    "doc_confidence": 0.5,
    "min_score": 0.25
  },
  "paths": {
    "faq_file": "./data/faq.json",
    "meta": "./data/index/meta.json",
    "faiss_index": "./data/index/faiss.index",
    "embeddings": "./data/index/embeddings.npy",
    "bm25_meta": "./data/index/bm25_meta.json"
  },
  "chunking": {
    "chunk_size": 400,
    "chunk_overlap": 50
  }
}
```

### requirements.txt (MVP)

```
streamlit
sentence-transformers
faiss-cpu
rank-bm25
requests
PyPDF2
numpy
tiktoken
```

## 14. Troubleshooting Common Dev Issues (Quick Hits)

- **ModuleNotFoundError in scripts**: Run with `python -m scripts.name` or add project root to PYTHONPATH (avoid sys.path hacks)
- **Model loaded per-request slowdown**: Use `@st.cache_resource` or module-level singletons
- **FAISS/BM25 score comparability**: Min-max normalize both scores before fusion
- **Missing meta.json**: Indexer not run; fail fast and show message in UI: "No index found, run indexer."

## 15. Security & Privacy Notes

- No PII logging for production; sanitize logs or anonymize session ids
- Keep LLM and indices local to avoid data exfiltration for campus privacy
- Admin actions require auth — restrict FAQ promotion

## 16. Next Steps & Recommended First Tasks

1. Approve this spec (or call changes now)
2. Build or validate indexer.py with 10 real PDFs
3. Implement retrieve_documents + rerank (rerank.py with source diversity + mmr)
4. Add response_generator.py with single-chunk fast path and Ollama integration
5. Wire Streamlit app.py with cached engines and simple UI
6. Run failure_hunter.py with the agreed 50-query set and iterate

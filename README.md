# Campus AI Assistant

An on-prem, privacy-first AI assistant for campus use. Answers academic questions using a hybrid FAQ matcher + Retrieval-Augmented Generation (RAG) pipeline — all running locally with Ollama, no cloud required.

Designed for ~70 concurrent students on a single node (8–16 GB RAM).

---

## Features

- **Hybrid search** — combines semantic (FAISS) and keyword (BM25) retrieval for best coverage
- **FAQ fast-path** — curated Q&A pairs matched by embedding similarity; hot-reloadable JSON
- **Local LLM** — Ollama integration (llama2:7b or swap to any supported model)
- **Smart routing** — skips LLM entirely when a single high-confidence chunk answers the query
- **Confidence scoring** — every answer shows a confidence level with uncertainty disclaimers when needed
- **Source citations** — responses link back to the exact PDF and page
- **Admin FAQ promotion** — high-confidence generated answers are auto-flagged for admin review and can be promoted to the FAQ
- **Request queue** — handles 70 concurrent users with backpressure, timeouts, and metrics
- **Memory management** — automatic GC after search and generation cycles
- **Corrective RAG** — detects low-quality retrievals and re-routes or escalates

---

## Architecture

```
User (Streamlit UI)
       │
       ▼
Input validation → Query Router
       ├── FAQ path  → FAQ Engine (JSON + embedding cache) → quick answer
       └── Doc path  → Document Retrieval Engine
                          ├── FAISS (dense, top-5)
                          ├── BM25  (sparse, top-5)
                          ├── Score fusion + source diversity + MMR rerank
                          └── return top chunks
       ▼
Response Generator
       ├── single high-confidence chunk? → return directly (no LLM)
       └── else → Ollama LLM with context + citations
       ▼
Streamlit UI + JSONL interaction logs
```

### Key Modules

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI with cached engine loading |
| `engines.py` | Combined FAQ + document search, smart routing |
| `router.py` | Query classification (FAQ / RAG / out-of-scope) |
| `faq_matcher.py` | Embedding-based FAQ lookup |
| `faq_manager.py` | FAQ CRUD, hot-reload, versioning |
| `faq_promotion.py` | Admin approval workflow for promoted FAQs |
| `retrieval.py` | Hybrid FAISS + BM25 retrieval |
| `rerank.py` | MMR reranking + source diversity penalty |
| `llm.py` | Ollama client with performance optimisations |
| `indexer.py` | PDF ingestion, chunking, FAISS + BM25 index build |
| `indexer_enhanced.py` | Enhanced indexer with batch encoding |
| `chunking.py` | Token-aware chunking (400 tokens, 50 overlap) |
| `corrective_rag.py` | Detects weak retrievals and applies corrective logic |
| `request_queue.py` | Async queue for concurrent request management |
| `memory.py` | Session/conversation memory (SQLite) |
| `memory_monitor.py` | GC and memory usage tracking |
| `admin_guard.py` | Auth guard for admin-only actions |
| `logging_utils.py` | JSONL structured logging with 30-day rotation |
| `workflow.py` | End-to-end query workflow orchestration |

---

## Quick Start

### 1. Set up environment

```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

### 2. Install and start Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

ollama pull llama2:7b
ollama serve          # runs on http://localhost:11434
```

### 3. Add your documents and FAQs

Drop PDF files into `data/documents/`:

```bash
mkdir -p data/documents
# copy your .pdf files here
```

Optionally create `data/faq.json`:

```json
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process consists of...",
      "category": "placements"
    }
  ]
}
```

### 4. Build the search index

```bash
python indexer.py
# outputs: data/index/meta.json, embeddings.npy, faiss.index, bm25_meta.json
```

### 5. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Configuration

Edit `config.json`:

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

---

## Concurrent User Support

The request queue (`request_queue.py`) handles load gracefully:

| Setting | Default |
|---|---|
| Queue capacity | 100 requests |
| Concurrent workers | 10 |
| Request timeout | 30 seconds |
| Behaviour at capacity | Rejects with user-friendly message |

---

## Testing

```bash
# Unit + integration tests
python -m pytest

# Automated eval (accuracy benchmarks)
python -m scripts.auto_eval

# Stress test — 50 messy queries (typos, missing docs, contradictions)
python -m scripts.failure_hunter

# Concurrent queue test
python test_concurrent_queue.py

# Memory / GC test
python test_memory_gc.py

# Batch encoding performance
python test_batch_performance.py
```

---

## File Structure

```
├── app.py                   # Streamlit UI
├── engines.py               # Search engine (FAQ + RAG)
├── router.py                # Query routing
├── retrieval.py             # FAISS + BM25 hybrid retrieval
├── rerank.py                # MMR + source diversity reranking
├── llm.py                   # Ollama LLM client
├── indexer.py               # PDF indexer
├── indexer_enhanced.py      # Batch-optimised indexer
├── chunking.py              # Text chunking
├── faq_matcher.py           # FAQ similarity search
├── faq_manager.py           # FAQ management + hot-reload
├── faq_promotion.py         # Admin FAQ promotion workflow
├── corrective_rag.py        # Corrective retrieval logic
├── request_queue.py         # Concurrent request queue
├── memory.py                # Session memory (SQLite)
├── memory_monitor.py        # GC + memory tracking
├── admin_guard.py           # Admin auth guard
├── logging_utils.py         # Structured JSONL logging
├── workflow.py              # Query workflow orchestration
├── config.json              # Configuration
├── requirements.txt         # Python dependencies
├── scripts/
│   ├── auto_eval.py         # Automated accuracy evaluation
│   └── failure_hunter.py    # Adversarial query testing
├── data/
│   ├── documents/           # PDF source files
│   ├── faq.json             # FAQ database
│   └── index/               # Built search indices
├── docs/                    # Extended documentation
└── logs/                    # Interaction logs (JSONL, 30-day retention)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| No results returned | Run `python indexer.py` — index may not exist |
| Slow responses | Make sure `ollama serve` is running locally |
| High memory usage | Reduce `chunk_size` in `config.json` |
| Import errors | Use `python -m scripts.name` instead of `python scripts/name.py` |
| Model loads on every request | Ensure `@st.cache_resource` is applied to engine init |

---

## System Requirements

- Python 3.9+
- 8 GB RAM minimum (16 GB recommended for 70 concurrent users)
- Ollama installed and running
- ~5 GB disk space for PDFs + indices

---

## Security & Privacy

- All data stays local — no external API calls for LLM or embeddings
- No PII is logged; session IDs are anonymised
- Admin FAQ promotion requires authentication (`admin_guard.py`)
- FAQ snapshots are versioned; originals are never overwritten

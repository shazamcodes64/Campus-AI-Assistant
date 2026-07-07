# High-Level Design Document - MVP Architecture

## Design Philosophy

**MVP-First Approach**: Prioritizing simplicity and fast delivery over premature optimization
**Target Load**: Single node, ~70 concurrent students, <10 QPS
**Deployment**: Local single-node Streamlit application

## System Architecture - Simplified

```
┌─────────────────────────────────────────────────────────────┐
│                    Campus AI Assistant MVP                 │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────┐ │
│  │  Streamlit UI   │    │  Session Store  │    │ Logging │ │
│  │                 │    │                 │    │         │ │
│  │ - Query Input   │    │ - Chat History  │    │ - JSONL │ │
│  │ - Response      │    │ - User Context  │    │ - Simple│ │
│  │ - Source Display│    │ - Simple Dict   │    │         │ │
│  └─────────────────┘    └─────────────────┘    └─────────┘ │
│           │                       │                  ▲     │
│           ▼                       ▼                  │     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Query Processing                         │ │
│  │                                                         │ │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐ │ │
│  │  │ Query Router    │    │     Processing Engines      │ │ │
│  │  │                 │    │                             │ │ │
│  │  │ - Embed Query   │───▶│  ┌─────────┐ ┌─────────────┐ │ │ │
│  │  │ - Route Logic   │    │  │FAQ      │ │Document     │ │ │ │
│  │  │ - Confidence    │    │  │Engine   │ │Retrieval    │ │ │ │
│  │  └─────────────────┘    │  └─────────┘ │Engine       │ │ │ │
│  │                         │              └─────────────┘ │ │ │
│  │                         └─────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                    │                         │
│                                    ▼                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Response Generation                        │ │
│  │                                                         │ │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐ │ │
│  │  │Response Builder │    │      LLM Service            │ │ │
│  │  │                 │    │                             │ │ │
│  │  │- Format Context │───▶│ - Ollama Local              │ │ │
│  │  │- Build Citations│    │ - Simple Prompts            │ │ │
│  │  │- Calc Confidence│    │ - Basic Error Handling      │ │ │
│  │  └─────────────────┘    └─────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                    │                         │
│                                    ▼                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Data Layer                              │ │
│  │                                                         │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│  │ │FAQ JSON     │ │PDF Files    │ │    Simple Indices   │ │ │
│  │ │             │ │             │ │                     │ │ │
│  │ │- Hot Reload │ │- Raw Docs   │ │- FAISS Vector      │ │ │
│  │ │- No Cache   │ │- Text Chunks│ │- BM25 Keyword      │ │ │
│  │ │- Direct Load│ │- Metadata   │ │- Load at Startup   │ │ │
│  │ └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow - MVP Simplified

```
User Query
    │
    ▼
┌─────────────────┐
│Input Validation │
│- Basic checks   │
│- Length limit   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│Query Router     │
│- Embed once     │
│- Simple routing │
│- No caching     │
└─────────────────┘
    │
    ├─── FAQ Route (≥0.8)
    │    │
    │    ▼
    │    ┌─────────────────┐
    │    │FAQ Engine       │
    │    │- Load JSON      │
    │    │- Compute sim    │
    │    │- Return answer  │
    │    └─────────────────┘
    │
    ├─── Document Route (≥0.5)
    │    │
    │    ▼
    │    ┌─────────────────┐
    │    │Document Engine  │
    │    │- FAISS search   │
    │    │- BM25 search    │
    │    │- Simple merge   │
    │    │- Basic rerank   │
    │    └─────────────────┘
    │    │
    │    ▼
    │    ┌─────────────────┐
    │    │LLM Generation   │
    │    │- Format prompt  │
    │    │- Call Ollama    │
    │    │- Add citations  │
    │    └─────────────────┘
    │
    └─── Out-of-Scope (<0.5)
         │
         ▼
         ┌─────────────────┐
         │Simple Rejection │
         └─────────────────┘
    │
    ▼
┌─────────────────┐
│Response + Log   │
│- Format output  │
│- Log to JSONL   │
│- Update session │
└─────────────────┘
```

## Component Interfaces - MVP

### 1. Query Router (Simple)

```python
class QueryRouter:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def route_query(self, query: str) -> dict:
        """
        Returns: {
            "route": "faq" | "document" | "out_of_scope",
            "confidence": float
        }
        """
        # Simple embedding + classification
        # No caching, no optimization
```

### 2. FAQ Engine (Minimal)

```python
class FAQEngine:
    def __init__(self, faq_path: str):
        self.faq_path = faq_path
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def search_faq(self, query: str) -> dict:
        """
        Returns: {
            "answer": str | None,
            "confidence": float,
            "source_id": str | None
        }
        """
        # Load JSON fresh each time (hot reload)
        # Compute embeddings on-demand
        # No caching layer
```

### 3. Document Retrieval Engine (Basic)

```python
class DocumentEngine:
    def __init__(self, faiss_path: str, bm25_path: str):
        self.faiss_index = faiss.read_index(faiss_path)
        self.bm25 = self._load_bm25(bm25_path)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def retrieve_documents(self, query: str, k: int = 3) -> dict:
        """
        Returns: {
            "chunks": [{"text": str, "source": str, "page": int, "score": float}],
            "confidence": float
        }
        """
        # FAISS search (5 results)
        # BM25 search (5 results)  
        # Simple score fusion
        # Basic diversity reranking
```

### 4. Response Generator (Straightforward)

```python
class ResponseGenerator:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama2:7b"
    
    def generate_response(self, query: str, context: list) -> dict:
        """
        Returns: {
            "response": str,
            "confidence": float,
            "sources": [str]
        }
        """
        # Simple prompt template
        # Direct Ollama API call
        # Basic error handling
        # Citation formatting
```

## Data Storage - MVP Simple

### File Structure
```
data/
├── faq.json                    # Single FAQ file
├── documents/                  # PDF storage
│   ├── doc1.pdf
│   └── doc2.pdf
├── indices/
│   ├── faiss.index            # Vector index
│   ├── bm25_index.pkl         # BM25 index
│   └── metadata.json          # Chunk metadata
└── logs/
    └── interactions.jsonl      # Simple logging
```

### FAQ Schema (Minimal)
```json
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process...",
      "category": "placement"
    }
  ]
}
```

### Log Schema (Simple)
```json
{"timestamp": "2024-01-15T10:00:00Z", "query": "...", "route": "faq", "response": "...", "confidence": 0.85}
```

## Technology Stack - MVP

### Core Dependencies
```
streamlit==1.28.0
sentence-transformers==2.2.2
faiss-cpu==1.7.4
rank-bm25==0.2.2
requests==2.31.0
PyPDF2==3.0.1
numpy==1.24.3
```

### Infrastructure
- **UI**: Streamlit (single process)
- **LLM**: Ollama (local installation)
- **Storage**: Local files (JSON + binary indices)
- **Logging**: Simple JSONL files
- **Session**: Streamlit session_state

## Operational Requirements - Minimal

### Startup Sequence (Simple)
1. **Load Models** (30s): SentenceTransformer + indices
2. **Validate Data** (5s): Check FAQ JSON + indices exist
3. **Test LLM** (5s): Ping Ollama service
4. **Start UI** (5s): Launch Streamlit

### Memory Management (Basic)
- **No caching**: Fresh computation each request
- **Session isolation**: Use st.session_state only
- **Memory target**: <2GB total usage
- **No monitoring**: Basic Python logging only

### Error Handling (Minimal)
- **LLM failure**: Return "Service unavailable" message
- **Index failure**: Return "Search unavailable" message  
- **FAQ failure**: Route to document search
- **No circuit breakers**: Simple try/catch blocks

## Configuration - Single File

```json
{
  "models": {
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model": "llama2:7b"
  },
  "thresholds": {
    "faq_confidence": 0.8,
    "document_confidence": 0.5
  },
  "paths": {
    "faq_file": "./data/faq.json",
    "faiss_index": "./data/indices/faiss.index",
    "bm25_index": "./data/indices/bm25_index.pkl",
    "documents": "./data/documents/",
    "logs": "./data/logs/"
  },
  "generation": {
    "max_tokens": 500,
    "temperature": 0.3,
    "timeout_seconds": 30
  }
}
```

## MVP Scope Summary

### Phase 1 (MVP) - What We Build
✅ **FAQ semantic matching** with JSON storage
✅ **Hybrid retrieval** (FAISS + BM25) with basic fusion
✅ **Simple reranking** and source diversity
✅ **LLM generation** with Ollama integration
✅ **Basic citations** and confidence scoring
✅ **Streamlit UI** with session management
✅ **JSONL logging** for interactions
✅ **Single-node deployment** with local files

### Deferred to Later Phases
❌ Complex caching layers (L1/L2/L3/L4)
❌ Request queues and backpressure
❌ Circuit breakers and auto-recovery
❌ Advanced monitoring pipelines
❌ Distributed deployment
❌ Performance optimization
❌ Memory pressure management
❌ Advanced error handling

### Rationale
At <10 QPS with 70 students, the MVP approach will:
- **Ship faster**: 2-3 weeks vs 2-3 months
- **Validate assumptions**: Real usage data before optimization
- **Reduce complexity**: Easier debugging and maintenance
- **Meet requirements**: All functional needs satisfied
- **Enable iteration**: Quick changes based on feedback

**This lean design focuses on core functionality while maintaining the flexibility to add enterprise features when actual bottlenecks are identified through real usage.**

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  Query Router    │    │  FAQ Engine     │
│                 │    │                  │    │                 │
│ - Input Form    │───▶│ - Route Decision │───▶│ - Semantic      │
│ - Response      │    │ - Confidence     │    │   Matching      │
│   Display       │    │   Scoring        │    │ - TTL Cache     │
│ - Source Links  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        │                       │
         │                        ▼                       ▼
         │               ┌──────────────────┐    ┌─────────────────┐
         │               │   RAG Engine     │    │ Response        │
         │               │                  │    │ Generator       │
         └───────────────│ - FAISS Vector  │───▶│                 │
                         │   Search         │    │ - LLM           │
                         │ - BM25 Lexical   │    │   Integration   │
                         │   Search         │    │ - Confidence    │
                         │ - MMR Reranking  │    │   Calculation   │
                         └──────────────────┘    └─────────────────┘
                                  │                       │
                                  ▼                       ▼
                         ┌──────────────────┐    ┌─────────────────┐
                         │ Document Store   │    │ Logging &       │
                         │                  │    │ Monitoring      │
                         │ - PDF Corpus     │    │                 │
                         │ - FAISS Index    │    │ - Interaction   │
                         │ - BM25 Index     │    │   Logs          │
                         │ - FAQ Database   │    │ - Performance   │
                         └──────────────────┘    │   Metrics       │
                                                 └─────────────────┘
```

### Data Flow Architecture

```
User Query Input
       │
       ▼
┌─────────────────┐
│ Input Validation│
│ & Sanitization  │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Query Router    │
│ (Semantic       │
│  Classification)│
└─────────────────┘
       │
       ├─── FAQ Route (confidence ≥ 0.8)
       │    │
       │    ▼
       │    ┌─────────────────┐
       │    │ FAQ Engine      │
       │    │ - Load FAQ DB   │
       │    │ - Compute       │
       │    │   Similarity    │
       │    │ - Return Match  │
       │    └─────────────────┘
       │
       ├─── RAG Route (0.5 ≤ confidence < 0.8)
       │    │
       │    ▼
       │    ┌─────────────────┐
       │    │ RAG Engine      │
       │    │ - Query         │
       │    │   Expansion     │
       │    │ - Hybrid        │
       │    │   Retrieval     │
       │    │ - MMR Reranking │
       │    └─────────────────┘
       │
       └─── Out of Scope (confidence < 0.5)
            │
            ▼
            ┌─────────────────┐
            │ Rejection       │
            │ Response        │
            └─────────────────┘
       │
       ▼
┌─────────────────┐
│ Response        │
│ Generator       │
│ - LLM Call      │
│ - Confidence    │
│   Calculation   │
│ - Source        │
│   Attribution   │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Response        │
│ Formatting &    │
│ UI Display      │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Logging &       │
│ Monitoring      │
└─────────────────┘
```

## Component Design

### 1. Query Router Component

**Purpose**: Intelligent routing of user queries to appropriate processing engines

**Design Decisions**:
- **Embedding Model**: SentenceTransformer `all-MiniLM-L6-v2` for consistent 384-dim embeddings
- **Classification Strategy**: Cosine similarity against predefined category embeddings
- **Threshold Strategy**: Hard thresholds (FAQ: 0.8, RAG: 0.5) for deterministic routing

**Interface**:
```python
class QueryRouter:
    def classify_query(self, query: str) -> RouteResult:
        """
        Returns: RouteResult(route="faq"|"rag"|"out_of_scope", 
                           confidence=float, 
                           processing_time_ms=int)
        """
```

**Internal Architecture**:
- Singleton pattern for model loading (memory efficiency)
- LRU cache for recent query embeddings (100 entries)
- Async processing capability for concurrent requests

### 2. FAQ Engine Component

**Purpose**: Fast semantic matching against curated FAQ database

**Design Decisions**:
- **Storage Format**: JSON with embedded vectors for hot-reload capability
- **Similarity Metric**: Dot product on normalized embeddings (equivalent to cosine similarity)
- **Caching Strategy**: In-memory embedding cache with 1-hour TTL

**Interface**:
```python
class FAQEngine:
    def search_faq(self, query: str) -> FAQResult:
        """
        Returns: FAQResult(answer=str|None, 
                          confidence=float, 
                          source_id=str|None, 
                          match_score=float)
        """
```

**Data Schema**:
```json
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process consists of...",
      "category": "placement",
      "created_date": "2024-01-15T10:00:00Z",
      "ttl_days": 365,
      "embedding": [0.1, -0.2, 0.3, ...]
    }
  ],
  "metadata": {
    "last_updated": "2024-01-15T10:00:00Z",
    "total_entries": 50,
    "embedding_model": "all-MiniLM-L6-v2"
  }
}
```

### 3. RAG Engine Component

**Purpose**: Hybrid document retrieval and ranking for complex queries

**Design Decisions**:
- **Hybrid Approach**: FAISS vector search + BM25 lexical search for comprehensive coverage
- **Reranking Strategy**: MMR (Maximal Marginal Relevance) with λ=0.7 for diversity
- **Query Enhancement**: WordNet-based synonym expansion for academic terminology

**Interface**:
```python
class RAGEngine:
    def retrieve_documents(self, query: str, top_k: int = 3) -> RetrievalResult:
        """
        Returns: RetrievalResult(chunks=List[DocumentChunk], 
                               total_retrieved=int,
                               retrieval_confidence=float)
        """
```

**Internal Pipeline**:
1. **Query Expansion**: Append 2-3 academic synonyms using WordNet
2. **Parallel Retrieval**: FAISS top-5 + BM25 top-5 simultaneously
3. **Score Fusion**: Weighted combination (FAISS: 0.6, BM25: 0.4)
4. **MMR Reranking**: Select diverse top-3 chunks
5. **Metadata Preservation**: Source file, page number, chunk ID

### 4. Response Generator Component

**Purpose**: LLM-powered response generation with confidence estimation

**Design Decisions**:
- **LLM Integration**: Ollama API with local model deployment
- **Model Selection**: `llama2:7b` or `mistral:7b` based on availability
- **Prompt Engineering**: Structured prompt with query + context + instructions

**Interface**:
```python
class ResponseGenerator:
    def generate_response(self, query: str, context: List[str]) -> GenerationResult:
        """
        Returns: GenerationResult(response=str, 
                                confidence=float, 
                                sources=List[str],
                                processing_time_ms=int)
        """
```

**Confidence Calculation**:
```python
def calculate_confidence(self, retrieval_score: float, 
                        context_relevance: float, 
                        response_coherence: float) -> float:
    return (retrieval_score * 0.4 + 
            context_relevance * 0.3 + 
            response_coherence * 0.3)
```

### 5. Document Store Component

**Purpose**: Efficient storage and indexing of academic documents

**Design Decisions**:
- **Document Format**: PDF-only with text extraction via PyPDF2
- **Chunking Strategy**: 512-token chunks with 50-token overlap using tiktoken
- **Index Types**: FAISS IndexFlatIP for vectors, Whoosh for BM25

**Storage Layout**:
```
data/
├── documents/
│   ├── syllabus_2024.pdf
│   ├── placement_guide.pdf
│   └── academic_calendar.pdf
├── indices/
│   ├── faiss_index.bin
│   ├── bm25_index/
│   └── metadata.json
└── faq_database.json
```

**Metadata Schema**:
```json
{
  "chunks": [
    {
      "chunk_id": "doc_001_page_5_chunk_2",
      "text": "The academic calendar for 2024...",
      "source_file": "academic_calendar.pdf",
      "page_number": 5,
      "embedding_index": 1234,
      "created_date": "2024-01-15T10:00:00Z"
    }
  ],
  "documents": [
    {
      "file_name": "academic_calendar.pdf",
      "file_size": 2048576,
      "page_count": 25,
      "chunk_count": 150,
      "processed_date": "2024-01-15T10:00:00Z"
    }
  ]
}
```

## Integration Patterns

### 1. Error Handling Strategy

**Graceful Degradation Pattern**:
- FAQ Engine failure → Route all queries to RAG
- FAISS Index corruption → Fall back to BM25-only retrieval
- Ollama API timeout → Return retrieval results with sources
- Memory exhaustion → Clear caches and queue requests

**Circuit Breaker Pattern**:
- Track failure rates for each component
- Open circuit after 3 consecutive failures
- Half-open state with health checks every 30 seconds

### 2. Caching Strategy

**Multi-Level Caching**:
- **L1 Cache**: Query embeddings (LRU, 100 entries, 1-hour TTL)
- **L2 Cache**: FAQ embeddings (In-memory, 1-hour TTL)
- **L3 Cache**: Retrieved document chunks (Redis-like, 24-hour TTL)

### 3. Monitoring and Observability

**Metrics Collection**:
- Response time percentiles (p50, p95, p99)
- Route distribution (FAQ vs RAG vs out-of-scope)
- Confidence score distributions
- Error rates by component
- Memory and CPU utilization

**Logging Strategy**:
- Structured JSON logging with correlation IDs
- Separate log streams for interactions, errors, and performance
- Log rotation with 30-day retention

## Deployment Architecture

### Single-Node Deployment

**System Requirements**:
- **OS**: Ubuntu 20.04+ or macOS 12+
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB SSD for indices and logs
- **CPU**: 4 cores minimum for concurrent processing

**Service Architecture**:
```
┌─────────────────────────────────────────┐
│              Host System                │
│                                         │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  Streamlit  │  │     Ollama      │   │
│  │   Server    │  │   LLM Server    │   │
│  │  (Port 8501)│  │  (Port 11434)   │   │
│  └─────────────┘  └─────────────────┘   │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │        Application Process          │ │
│  │                                     │ │
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐ │ │
│  │  │ Router  │ │FAQ Eng. │ │RAG Eng.│ │ │
│  │  └─────────┘ └─────────┘ └────────┘ │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │           File System               │ │
│  │                                     │ │
│  │  data/     logs/      config/       │ │
│  │  ├─docs/   ├─app.log  ├─config.json │ │
│  │  ├─index/  ├─perf.log ├─secrets.env │ │
│  │  └─faq.json└─error.log              │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Configuration Management

**Environment-Based Configuration**:
```python
# config/production.json
{
  "environment": "production",
  "models": {
    "sentence_transformer": "all-MiniLM-L6-v2",
    "ollama_model": "llama2:7b",
    "embedding_cache_size": 1000
  },
  "thresholds": {
    "faq_similarity": 0.8,
    "route_confidence": 0.5,
    "response_quality": 0.6
  },
  "performance": {
    "max_concurrent_users": 10,
    "request_timeout_seconds": 30,
    "memory_limit_gb": 4,
    "enable_caching": true
  },
  "logging": {
    "level": "INFO",
    "rotation": "daily",
    "retention_days": 30
  }
}
```

## Security Considerations

### Input Validation
- Query length limits (1000 characters)
- Content sanitization against injection attacks
- File type validation for document uploads

### Data Privacy
- No persistent user session storage
- Query logs anonymized after 30 days
- Local deployment eliminates external data transmission

### Access Control
- Admin interface for FAQ management
- Document upload restrictions by file type
- Rate limiting per session/IP

## Performance Optimization

### Memory Management
- Lazy loading of embedding models
- Periodic garbage collection triggers
- Memory usage monitoring with alerts

### Response Time Optimization
- Parallel processing for FAISS + BM25 retrieval
- Async I/O for file operations
- Connection pooling for Ollama API

### Scalability Considerations
- Horizontal scaling via load balancer (future)
- Database migration path from JSON to PostgreSQL
- Microservice decomposition strategy

This design provides a robust, maintainable architecture for the campus AI assistant while maintaining simplicity for single-node deployment and future scalability options.
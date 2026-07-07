# Implementation Tasks - Campus AI Assistant MVP

## 📊 Progress Summary

**Overall Progress**: ~70% Complete (Week 1 + Week 2 Days 6-7 Complete)

### ✅ Phase 1 (MVP) - Completed (Days 1-7)
- Project setup and infrastructure
- Document processing and indexing (FAISS + BM25)
- Hybrid retrieval engine with score fusion
- FAQ engine with hot-reload capability
- Query routing logic (inline in engines.py)
- LLM response generation with Ollama
- Streamlit UI with caching and error handling
- Automated evaluation scripts

**Core MVP Files**: app.py, engines.py, llm.py, indexer.py, config.json

### 🚧 Phase 1 (MVP) - In Progress (Days 8-10)
- Automated testing and failure analysis
- Performance tuning and optimization
- Deployment and documentation

### 📝 Phase 1 (MVP) - Remaining Tasks
- Run full torture test suite and analyze failures
- Performance optimization (concurrent users, memory management)
- Complete deployment guide and user documentation
- Classroom deployment and user acceptance testing

### 🔮 Phase 2 (Post-MVP) - Deferred Until After Real Usage
**Rationale**: Intentionally deferring advanced features to avoid premature complexity. Will revisit after collecting real usage data and performance metrics from classroom deployment.

**Deferred Components**:
- Advanced modularization (router.py, retrieval.py, separate services/)
- Admin workflows (admin_guard.py, approve_faq.py, faq_manager.py)
- FAQ auto-promotion (faq_promotion.py)
- Memory persistence (memory.py, memory.db)
- Agent workflows (agent.py, workflow.py)
- Corrective RAG (corrective.py, corrective_rag.py, contradiction_detector.py)
- Advanced reranking integration (rerank.py exists but not integrated)
- Service layer abstractions (services/ directory)
- Core module abstractions (core/ directory)

**Phase 2 Decision Criteria**: Deploy Phase 1, collect 2-4 weeks of real usage data, identify actual bottlenecks, then prioritize Phase 2 features based on evidence rather than assumptions.

---

## Project Structure

```
campus-ai-assistant/
├── app.py                          # Main Streamlit application
├── engines.py                      # Combined FAQ + Document retrieval
├── llm.py                          # LLM response generation
├── indexer.py                      # Document processing and indexing
├── config.json                     # System configuration
├── requirements.txt                # Python dependencies
├── README.md                       # Setup and deployment guide
│
├── data/
│   ├── faq.json                    # FAQ database (hot-reloadable)
│   ├── documents/                  # PDF storage
│   ├── indices/
│   │   ├── faiss.index            # Vector search index
│   │   ├── bm25_index.pkl         # Keyword search index
│   │   └── metadata.json          # Chunk metadata
│   └── logs/
│       └── interactions.jsonl      # Interaction logs
│
└── scripts/
    ├── auto_eval.py                # Automated evaluation (50 queries)
    ├── failure_hunter.py           # Failure analysis tool
    └── setup.py                    # Environment setup script
```

## Two-Week Implementation Plan

### Week 1: Foundation & Retrieval (Days 1-5)

#### Day 1: Project Setup & Infrastructure
- [x] 1.1 Create project structure and initialize git repository
- [x] 1.2 Create requirements.txt with all dependencies
- [x] 1.3 Implement config.json loading with validation
- [x] 1.4 Create basic Streamlit app skeleton with session management
- [x] 1.5 Test Ollama connectivity and model availability
- [x] 1.6 Set up logging infrastructure (JSONL format)

#### Day 2: Document Processing & Indexing
- [x] 2.1 Implement PDF text extraction with PyPDF2
- [x] 2.2 Create text chunking logic (400-512 tokens, 50 token overlap)
- [x] 2.3 Build FAISS index creation (IndexFlatIP, 384-dim)
- [x] 2.4 Build BM25 index creation with rank_bm25
- [x] 2.5 Generate and save metadata.json with chunk information
- [x] 2.6 Test indexer with sample academic PDFs

#### Day 3: Hybrid Retrieval Engine
- [x] 3.1 Implement SearchEngine class with model singleton
- [x] 3.2 Create FAISS vector search (top-5 results)
- [x] 3.3 Create BM25 keyword search (top-5 results)
- [x] 3.4 Implement score normalization (min-max)
- [x] 3.5 Implement score fusion (0.6 semantic + 0.4 lexical)
- [x] 3.6 Add source diversity penalty with decay list
- [-] 3.7 Implement MMR reranking (λ=0.6-0.7)
- [x] 3.8 Add MIN_SCORE filtering (0.25 threshold)

#### Day 4: FAQ Engine & Query Routing
- [x] 4.1 Implement FAQ JSON loading with schema validation
- [x] 4.2 Create FAQ semantic matching with embeddings
- [x] 4.3 Add FAQ embedding cache (1-hour TTL)
- [x] 4.4 Implement hot-reload capability for FAQ updates
- [x] 4.5 Create query routing logic (FAQ ≥0.8, Doc ≥0.5)
- [x] 4.6 Add confidence scoring for routing decisions
- [x] 4.7 Test FAQ matching with sample questions

#### Day 5: Integration Testing
- [x] 5.1 Create test_system.py with smoke tests
- [x] 5.2 Test end-to-end indexing pipeline
- [x] 5.3 Test FAQ search with various queries
- [x] 5.4 Test document retrieval with academic queries
- [x] 5.5 Validate routing logic with edge cases
- [x] 5.6 Fix critical bugs discovered during testing

### Week 2: LLM Integration & Deployment (Days 6-10)

#### Day 6: LLM Response Generation
- [x] 6.1 Implement LLMGenerator class with Ollama integration
- [x] 6.2 Create prompt templates with citation instructions
- [x] 6.3 Implement single-chunk fast-path (>0.85 similarity)
- [x] 6.4 Add LLM synthesis for multi-chunk responses
- [x] 6.5 Implement confidence calculation (retrieval-based)
- [x] 6.6 Add uncertainty disclaimer for low confidence (<0.6)
- [x] 6.7 Format citations with source and page numbers
- [x] 6.8 Add timeout handling (30s) and fallback responses

#### Day 7: Streamlit UI & User Experience
- [x] 7.1 Complete app.py with query input form
- [x] 7.2 Add response display with markdown formatting
- [x] 7.3 Create confidence visualization (progress bar/meter)
- [x] 7.4 Implement source citations panel with links
- [x] 7.5 Add session state management for chat history
- [x] 7.6 Implement error handling with user-friendly messages
- [x] 7.7 Add loading indicators and progress feedback
- [x] 7.8 Test UI with @st.cache_resource for engines

#### Day 8: Automated Testing & Failure Analysis
- [x] 8.1 Create scripts/auto_eval.py with 50-query test suite
- [x] 8.2 Implement streaming CSV output for results
- [x] 8.3 Add memory-efficient batch processing
- [x] 8.4 Create scripts/failure_hunter.py for failure analysis
- [x] 8.5 Run torture test with messy queries (typos, out-of-scope)
- [x] 8.6 Analyze failure patterns and edge cases
- [x] 8.7 Fix critical issues discovered in testing
- [x] 8.8 Validate accuracy ≥80% on "exists-and-correct" metric

#### Day 9: Performance Tuning & Optimization
- [x] 9.1 Implement model singleton pattern for memory efficiency
- [x] 9.2 Add @st.cache_resource for SearchEngine and LLMGenerator
- [x] 9.3 Optimize embedding computation with batching
- [x] 9.4 Add garbage collection triggers for memory management
- [x] 9.5 Implement request queuing for concurrent users
- [x] 9.6 Test with 10 concurrent sessions
- [x] 9.7 Measure and optimize response time (<5-10s target)
- [x] 9.8 Validate memory usage (<4GB typical, <8GB peak)

#### Day 10: Deployment & Documentation
- [x] 10.1 Create comprehensive README.md with setup instructions
- [x] 10.2 Write deployment guide for single-node setup
- [x] 10.3 Create scripts/setup.py for automated environment setup
- [x] 10.4 Test deployment on clean Ubuntu/macOS environment
- [x] 10.5 Create user guide with example queries
- [x] 10.6 Document troubleshooting common issues
- [x] 10.7 Deploy to classroom environment
- [ ] 10.8 Conduct user acceptance testing with students
- [ ] 10.9 Monitor initial usage and collect feedback
- [x] 10.10 Create post-deployment support plan

## Optional Enhancements (Post-MVP)

### Phase 2: Admin Features (After Real Usage Data)
- [ ]* Implement FAQ promotion workflow (faq_promotion.py)
- [ ]* Create admin interface for FAQ management (admin_guard.py, approve_faq.py)
- [ ]* Add versioned FAQ snapshots
- [ ]* Implement audit logging for admin actions
- [ ]* Add authentication for admin access

### Phase 2: Advanced Retrieval (Based on Performance Bottlenecks)
- [ ] Integrate MMR reranking from rerank.py into engines.py
- [ ]* Implement query expansion with WordNet synonyms
- [ ]* Add cross-encoder reranking for better relevance
- [ ]* Implement semantic caching for frequent queries
- [ ]* Add multi-hop reasoning for complex questions

### Phase 2: Monitoring & Analytics (After Deployment)
- [ ]* Create performance metrics dashboard
- [ ]* Implement real-time monitoring with alerts
- [ ]* Add user feedback collection mechanism
- [ ]* Create analytics for query patterns and trends
- [ ]* Implement A/B testing framework

### Phase 2: Scalability Improvements (If Needed)
- [ ]* Add request queue with backpressure handling
- [ ]* Implement circuit breakers for component failures
- [ ]* Add distributed caching with Redis
- [ ]* Create horizontal scaling strategy
- [ ]* Migrate from JSON to PostgreSQL for FAQ storage

### Phase 2: Advanced Features (User-Driven)
- [ ]* Memory persistence for conversation history (memory.py, memory.db)
- [ ]* Agent workflows for complex queries (agent.py, workflow.py)
- [ ]* Corrective RAG with contradiction detection (corrective_rag.py, contradiction_detector.py)
- [ ]* Service layer abstractions (services/ directory)
- [ ]* Advanced confidence scoring (core/confidence.py)

**Note**: All Phase 2 features will be prioritized based on real usage patterns, performance data, and user feedback from Phase 1 classroom deployment.

## Testing Checklist

### Unit Tests
- [ ] Query routing logic with various confidence scores
- [ ] FAQ semantic matching with edge cases
- [ ] FAISS vector search correctness
- [ ] BM25 keyword search correctness
- [ ] Score normalization and fusion
- [ ] MMR reranking algorithm
- [ ] Source diversity penalty calculation
- [ ] Confidence score calculation
- [ ] Prompt template formatting
- [ ] Citation extraction and formatting

### Integration Tests
- [ ] End-to-end indexing pipeline
- [ ] FAQ search with hot-reload
- [ ] Document retrieval with hybrid search
- [ ] LLM generation with context
- [ ] Streamlit UI session management
- [ ] Error handling and fallback behavior
- [ ] Logging and monitoring

### Performance Tests
- [ ] Response time under load (10 concurrent users)
- [ ] Memory usage during peak load
- [ ] Cold start time (<60s target)
- [ ] Query throughput (QPS measurement)
- [ ] Index loading time
- [ ] Cache hit rates

### Acceptance Tests
- [ ] Accuracy ≥80% on known-answer queries
- [ ] FAQ route precision ≥90%
- [ ] Document retrieval recall ≥70%
- [ ] Out-of-scope detection precision ≥85%
- [ ] Citation accuracy 100% (no hallucinated sources)
- [ ] User satisfaction survey results

## Success Criteria

### Functional Requirements
✅ System can index academic PDFs and build search indices
✅ FAQ search returns relevant answers with ≥0.8 confidence
✅ Document search retrieves relevant chunks with hybrid approach
✅ LLM generates coherent responses with proper citations
✅ Streamlit UI accepts queries and displays formatted responses
✅ System handles 70 concurrent students with <10 QPS
✅ Response time 95th percentile <10 seconds
✅ Memory usage stays within 8-16GB budget

### Quality Requirements
✅ Accuracy ≥80% on "exists-and-correct" test set
✅ No hallucinated citations (100% source accuracy)
✅ Graceful degradation on component failures
✅ Clear uncertainty disclaimers for low-confidence responses
✅ Comprehensive error messages for debugging

### Deployment Requirements
✅ System starts up in <60 seconds (cold start)
✅ Runs stably for full classroom session duration
✅ Documentation sufficient for independent deployment
✅ Troubleshooting guide covers common issues
✅ User guide enables self-service query formulation

## Risk Mitigation

### Technical Risks
- **Model loading slowness**: Use singleton pattern and @st.cache_resource
- **Memory exhaustion**: Implement garbage collection and request queuing
- **LLM timeout**: Add 30s timeout with fallback to retrieval-only mode
- **Index corruption**: Validate indices on startup with health checks
- **Concurrent access issues**: Use Streamlit session_state for isolation

### Operational Risks
- **Ollama service down**: Implement health checks and fallback responses
- **Disk space exhaustion**: Monitor logs and implement rotation
- **Network issues**: Local deployment eliminates external dependencies
- **User overload**: Implement rate limiting and queue management

## Deployment Checklist

### Pre-Deployment
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Performance tests meeting targets
- [ ] Documentation complete and reviewed
- [ ] Deployment environment prepared (8-16GB RAM, 50GB storage)
- [ ] Ollama installed and models downloaded
- [ ] Sample FAQ data loaded
- [ ] Academic PDFs indexed

### Deployment Steps
- [ ] Clone repository to deployment server
- [ ] Create virtual environment and install dependencies
- [ ] Copy config.json and set appropriate paths
- [ ] Run indexer.py to build search indices
- [ ] Test Ollama connectivity
- [ ] Start Streamlit app (streamlit run app.py)
- [ ] Verify health checks pass
- [ ] Test with sample queries
- [ ] Monitor logs for errors

### Post-Deployment
- [ ] User acceptance testing with students
- [ ] Monitor performance metrics (response time, memory)
- [ ] Collect user feedback
- [ ] Document issues and create bug tickets
- [ ] Plan iteration based on real usage patterns

## Notes

- **MVP Philosophy**: Ship fast, iterate based on real usage
- **No Premature Optimization**: Focus on core functionality first
- **Real Data Driven**: Let actual bottlenecks guide optimization
- **User Feedback Loop**: Continuous improvement based on student needs
- **Technical Debt**: Document shortcuts for future refactoring

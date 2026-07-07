# Campus AI Assistant

Ultra-lean MVP for academic question answering with FAQ matching and document retrieval.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install and Start Ollama
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull llama2:7b

# Start Ollama (runs on http://localhost:11434)
ollama serve
```

### 3. Add Documents and FAQs

**Documents**: Place PDF files in `data/documents/`
```bash
mkdir -p data/documents
# Copy your PDF files here
```

**FAQs** (optional): Create `data/faq.json`
```json
{
  "faqs": [
    {
      "id": "faq_001",
      "question": "What is the placement process?",
      "answer": "The placement process consists of..."
    }
  ]
}
```

### 4. Build Search Indices
```bash
python indexer.py
```

### 5. Run the App
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Architecture

- **engines.py**: Combined FAQ + document search with smart routing
- **llm.py**: Ollama integration with performance optimizations
- **indexer.py**: PDF processing and FAISS + BM25 index building
- **app.py**: Streamlit UI with proper caching

## Performance Features

- **Smart LLM usage**: Skips LLM for high-confidence single chunks
- **Streamlit caching**: Models loaded once, not per request
- **Hybrid search**: Combines semantic (FAISS) and keyword (BM25) search
- **Score comparison**: FAQ vs document search to pick best result
- **Request queuing**: Handles 70 concurrent users with backpressure and timeout management
- **Memory management**: Automatic garbage collection after search and generation

## Concurrent User Support

The system includes a request queue to handle concurrent users gracefully:

- **Queue capacity**: 100 requests (configurable)
- **Concurrent workers**: 10 (configurable)
- **Timeout handling**: 30 seconds default
- **Backpressure**: Rejects requests when at capacity with user-friendly messages
- **Metrics tracking**: Real-time monitoring of queue status and performance

See `docs/request_queue.md` for detailed documentation.

## Configuration

Edit `config.json` to adjust:
- Model settings (embedding model, LLM model)
- Confidence thresholds
- Chunk size and overlap
- Generation parameters

## Troubleshooting

**No results**: Check if indices exist in `data/indices/`
**Slow responses**: Ensure Ollama is running locally
**Memory issues**: Reduce chunk_size in config.json
**Import errors**: Install all requirements.txt dependencies

## File Structure
```
├── app.py              # Streamlit UI
├── engines.py          # Search engine
├── llm.py             # LLM integration  
├── indexer.py         # Document processing
├── config.json        # Configuration
├── requirements.txt   # Dependencies
└── data/
    ├── documents/     # PDF files
    ├── faq.json      # FAQ database
    └── indices/      # Search indices
```
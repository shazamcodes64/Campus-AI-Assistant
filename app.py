import streamlit as st
import json
import os
import gc
import uuid
import time

# Optional memory monitoring (requires psutil)
try:
    from memory_monitor import get_monitor, log_memory
    MEMORY_MONITORING = True
except ImportError:
    MEMORY_MONITORING = False

# Request queue for concurrent user management
from request_queue import get_request_queue

# Load configuration
@st.cache_data
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

# Lazy load components only when needed
@st.cache_resource
def load_search_engine():
    st.info("Loading search engine... (this takes 10-15 seconds on first load)")
    from engines import SearchEngine
    config = load_config()
    return SearchEngine(config)

@st.cache_resource  
def load_llm_generator():
    from llm import LLMGenerator
    config = load_config()
    return LLMGenerator(config)

# Initialize request queue (singleton)
@st.cache_resource
def get_queue():
    """Initialize request queue with configuration"""
    config = load_config()
    queue_config = config.get("queue", {})
    
    return get_request_queue(
        max_queue_size=queue_config.get("max_queue_size", 100),
        max_concurrent_workers=queue_config.get("max_concurrent_workers", 10),
        default_timeout=queue_config.get("default_timeout", 30.0)
    )

def main():
    st.set_page_config(
        page_title="Campus AI Assistant",
        page_icon="🎓",
        layout="wide"
    )
    
    # Initialize memory monitoring if available
    if MEMORY_MONITORING:
        monitor = get_monitor()
        if monitor.baseline_memory is None:
            monitor.set_baseline()
    
    st.title("🎓 Campus AI Assistant")
    st.markdown("Ask questions about course materials, syllabus, placement process, and academic policies.")
    
    # Show loading status in sidebar first
    with st.sidebar:
        st.markdown("### System Status")
        
        # Check if indices exist
        indices_exist = (
            os.path.exists("data/indices/faiss.index") and
            os.path.exists("data/indices/bm25_index.pkl") and
            os.path.exists("data/indices/metadata.json")
        )
        
        faq_exists = os.path.exists("data/faq.json")
        
        st.markdown(f"📊 Document Index: {'✅' if indices_exist else '❌'}")
        st.markdown(f"❓ FAQ Database: {'✅' if faq_exists else '❌'}")
        
        # Show queue metrics
        try:
            queue = get_queue()
            metrics = queue.get_metrics()
            
            st.markdown("### Queue Status")
            st.markdown(f"📋 Queue Size: {metrics['current_queue_size']}/{queue.max_queue_size}")
            st.markdown(f"⚙️ Active Workers: {metrics['active_workers']}/{queue.max_concurrent_workers}")
            
            if metrics['total_requests'] > 0:
                with st.expander("Queue Metrics"):
                    st.json(metrics)
        except Exception as e:
            st.markdown(f"⚠️ Queue Status: Error ({str(e)[:30]}...)")
        
        if not indices_exist:
            st.warning("Document index not found. Run indexer.py to process documents.")
            st.stop()
        
        if not faq_exists:
            st.info("FAQ database not found. Create data/faq.json to add FAQs.")
        
        st.markdown("### Usage Tips")
        st.markdown("""
        - Ask specific questions about course content
        - Use keywords from your documents
        - Try different phrasings if no results
        - Check sources for detailed information
        """)
    
    # Query input
    query = st.text_input(
        "Ask your question:",
        placeholder="e.g., What is the placement process? What are the course requirements?",
        help="Ask about syllabus, placement, policies, or any course-related topics"
    )
    
    if query:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Get request queue
        queue = get_queue()
        
        # Submit request to queue
        success, error_msg = queue.submit(request_id, query)
        
        if not success:
            st.error(f"❌ {error_msg}")
            st.info("The system is currently handling many requests. Please wait a moment and try again.")
            return
        
        # Show queue position
        queue_size = queue.size()
        if queue_size > 1:
            st.info(f"⏳ Your request is queued (position: ~{queue_size}). Processing...")
        
        # Only load components when user submits a query
        with st.spinner("Loading AI components..."):
            try:
                search_engine = load_search_engine()
                llm_generator = load_llm_generator()
                
                # Test LLM connection
                llm_connected = llm_generator.test_connection()
                if not llm_connected:
                    st.sidebar.markdown(f"🤖 LLM Service: ⚠️")
                    st.warning("⚠️ LLM service (Ollama) not available. System will work with limited functionality.")
                else:
                    st.sidebar.markdown(f"🤖 LLM Service: ✅")
                
            except RuntimeError as e:
                st.error(f"🚨 Setup Error: {e}")
                st.markdown("### Quick Fix:")
                st.code("python indexer.py")
                st.markdown("Then refresh this page.")
                st.stop()
            except Exception as e:
                st.error(f"❌ System Error: {e}")
                st.markdown("Check that all dependencies are installed and Ollama is running.")
                st.stop()
        
        # Define processing function
        def process_query(query_text):
            """Process a query through search and LLM generation"""
            # Log memory before search
            if MEMORY_MONITORING:
                log_memory("before search")
            
            # Search for relevant information
            search_result = search_engine.search(query_text)
            
            # Trigger GC after search to free up memory from embeddings
            gc.collect()
            
            # Log memory after search
            if MEMORY_MONITORING:
                log_memory("after search + GC")
            
            # Generate response
            response = llm_generator.generate_response(query_text, search_result)
            
            # Trigger GC after LLM generation to free up memory
            gc.collect()
            
            # Log memory after generation
            if MEMORY_MONITORING:
                log_memory("after generation + GC")
            
            return {
                "search_result": search_result,
                "response": response
            }
        
        # Process request through queue
        with st.spinner("Searching for information..."):
            start_time = time.time()
            
            # Process the request
            result = queue.process_request(process_query, timeout_seconds=1.0)
            
            if result is None:
                st.error("❌ Request processing failed. Please try again.")
                return
            
            queued_request, processed_result = result
            
            # Check for errors
            if queued_request.error:
                st.error(f"❌ Error: {queued_request.error}")
                return
            
            if processed_result is None:
                st.error("❌ No result returned. Please try again.")
                return
            
            # Extract results
            search_result = processed_result["search_result"]
            response = processed_result["response"]
            
            processing_time = time.time() - start_time
        
        # Display response
        st.markdown("### Answer")
        st.markdown(response["answer"])
        
        # Display confidence and method
        col1, col2 = st.columns(2)
        with col1:
            confidence = response.get("confidence", 0.0)
            st.metric("Confidence", f"{confidence:.2f}")
        
        with col2:
            method = response.get("method", "unknown")
            method_labels = {
                "faq_direct": "FAQ Match",
                "direct_chunk": "Direct Source",
                "llm_synthesis": "AI Generated",
                "llm_fallback": "Source Excerpts",
                "no_chunks": "No Match"
            }
            st.metric("Method", method_labels.get(method, method))
        
        # Display sources
        if response.get("sources"):
            st.markdown("### Sources")
            for i, source in enumerate(response["sources"], 1):
                st.markdown(f"{i}. {source}")
        
        # Show search details in expander
        with st.expander("Search Details"):
            st.json({
                "request_id": request_id,
                "query": query,
                "search_type": search_result["type"],
                "search_confidence": search_result["confidence"],
                "response_method": response.get("method"),
                "num_sources": len(response.get("sources", [])),
                "processing_time_seconds": round(processing_time, 2)
            })

if __name__ == "__main__":
    main()
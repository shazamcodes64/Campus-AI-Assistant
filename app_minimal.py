import streamlit as st
import json
import os

st.set_page_config(
    page_title="Campus AI Assistant - Minimal Test",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Campus AI Assistant - Minimal Test Mode")
st.markdown("Testing without heavy model loading")

# Check system status
with st.sidebar:
    st.markdown("### System Status")
    
    indices_exist = (
        os.path.exists("data/indices/faiss.index") and
        os.path.exists("data/indices/bm25_index.pkl") and
        os.path.exists("data/indices/metadata.json")
    )
    
    faq_exists = os.path.exists("data/faq.json")
    config_exists = os.path.exists("config.json")
    
    st.markdown(f"📊 Document Index: {'✅' if indices_exist else '❌'}")
    st.markdown(f"❓ FAQ Database: {'✅' if faq_exists else '❌'}")
    st.markdown(f"⚙️ Config: {'✅' if config_exists else '❌'}")

# Query input
query = st.text_input(
    "Ask your question:",
    placeholder="e.g., What is the placement process?"
)

if query:
    st.markdown("### Test Response")
    st.info("In minimal mode - would normally search and generate response here")
    
    # Show what would happen
    st.markdown(f"**Your query:** {query}")
    st.markdown(f"**Query length:** {len(query)} characters")
    
    # Test if we can load config
    try:
        with open("config.json") as f:
            config = json.load(f)
        st.success("✅ Config loaded successfully")
        st.json(config)
    except Exception as e:
        st.error(f"❌ Config error: {e}")
    
    # Test if we can load metadata
    if os.path.exists("data/indices/metadata.json"):
        try:
            with open("data/indices/metadata.json") as f:
                metadata = json.load(f)
            st.success(f"✅ Metadata loaded: {len(metadata)} chunks")
            st.markdown(f"**First chunk preview:**")
            if metadata:
                st.json(metadata[0])
        except Exception as e:
            st.error(f"❌ Metadata error: {e}")
    
    st.markdown("---")
    st.markdown("**Next step:** If this works, the issue is with model loading. We can optimize that.")

st.markdown("---")
st.markdown("### Diagnostic Info")

# Show Python info
import sys
st.markdown(f"**Python version:** {sys.version}")
st.markdown(f"**Python executable:** {sys.executable}")

# Check if sentence-transformers is available
try:
    import sentence_transformers
    st.success("✅ sentence-transformers installed")
    st.markdown(f"Version: {sentence_transformers.__version__}")
except ImportError:
    st.error("❌ sentence-transformers not installed")

# Check if faiss is available
try:
    import faiss
    st.success("✅ faiss installed")
except ImportError:
    st.error("❌ faiss not installed")

# Check if rank_bm25 is available
try:
    import rank_bm25
    st.success("✅ rank_bm25 installed")
except ImportError:
    st.error("❌ rank_bm25 not installed")

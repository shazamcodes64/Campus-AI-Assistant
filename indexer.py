import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import pickle
from PyPDF2 import PdfReader
import tiktoken
import time

class DocumentIndexer:
    def __init__(self, config):
        self.config = config
        self.model = SentenceTransformer(config["embedding_model"])
        self.chunk_size = config["chunk_size"]
        self.chunk_overlap = config["chunk_overlap"]
        self.batch_size = config.get("embedding_batch_size", 32)
        
        # Initialize tokenizer for chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def build_indices(self, document_dir="data/documents"):
        """Process PDFs and build FAISS + BM25 indices"""
        print("🔄 Starting document indexing...")
        
        # Create directories
        os.makedirs("data/indices", exist_ok=True)
        os.makedirs(document_dir, exist_ok=True)
        
        # Process all PDFs
        all_chunks = []
        pdf_files = [f for f in os.listdir(document_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            print(f"❌ No PDF files found in {document_dir}")
            return False
        
        print(f"📄 Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            print(f"Processing: {pdf_file}")
            pdf_path = os.path.join(document_dir, pdf_file)
            chunks = self._process_pdf(pdf_path, pdf_file)
            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks extracted")
        
        if not all_chunks:
            print("❌ No text chunks extracted from PDFs")
            return False
        
        print(f"📊 Total chunks: {len(all_chunks)}")
        
        # Build FAISS index
        print("🔄 Building FAISS vector index...")
        self._build_faiss_index(all_chunks)
        
        # Build BM25 index
        print("🔄 Building BM25 keyword index...")
        self._build_bm25_index(all_chunks)
        
        # Save metadata
        print("🔄 Saving metadata...")
        self._save_metadata(all_chunks)
        
        print("✅ Indexing complete!")
        return True
    
    def _process_pdf(self, pdf_path, filename):
        """Extract and chunk text from PDF"""
        chunks = []
        
        try:
            reader = PdfReader(pdf_path)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                
                if not text or not text.strip():
                    continue
                
                # Chunk the page text
                page_chunks = self._chunk_text(text, filename, page_num + 1)
                chunks.extend(page_chunks)
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")
        
        return chunks
    
    def _chunk_text(self, text, source, page):
        """Split text into overlapping chunks"""
        # Tokenize text
        tokens = self.tokenizer.encode(text)
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get chunk tokens
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            
            # Decode back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Clean up text
            chunk_text = chunk_text.strip()
            
            if chunk_text and len(chunk_text) > 50:  # Minimum chunk size
                chunks.append({
                    "text": chunk_text,
                    "source": source,
                    "page": page,
                    "chunk_id": f"{source}:p{page}:c{len(chunks)}"
                })
            
            # Move start position with overlap
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def _build_faiss_index(self, chunks):
        """Build FAISS vector index with batched embedding computation"""
        # Extract text for embedding
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings in batches for memory efficiency
        print(f"  → Generating embeddings in batches of {self.batch_size}...")
        embeddings_list = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            print(f"    Processing batch {i // self.batch_size + 1}/{(len(texts) + self.batch_size - 1) // self.batch_size}")
            
            batch_embeddings = self.model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=self.batch_size
            )
            embeddings_list.append(batch_embeddings)
        
        # Concatenate all batches
        embeddings = np.vstack(embeddings_list) if len(embeddings_list) > 1 else embeddings_list[0]
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
        
        # Add embeddings to index
        index.add(embeddings.astype('float32'))
        
        # Save index
        faiss.write_index(index, "data/indices/faiss.index")
        print(f"  → FAISS index saved ({len(chunks)} vectors, {dimension}D)")
    
    def _build_bm25_index(self, chunks):
        """Build BM25 keyword index"""
        # Tokenize texts for BM25
        tokenized_corpus = []
        for chunk in chunks:
            # Simple tokenization (split on whitespace and punctuation)
            tokens = chunk["text"].lower().split()
            # Remove punctuation and short tokens
            tokens = [token.strip('.,!?";()[]{}') for token in tokens]
            tokens = [token for token in tokens if len(token) > 2]
            tokenized_corpus.append(tokens)
        
        # Create BM25 index
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Save BM25 index
        with open("data/indices/bm25_index.pkl", "wb") as f:
            pickle.dump(bm25, f)
        
        print(f"  → BM25 index saved ({len(chunks)} documents)")
    
    def _save_metadata(self, chunks):
        """Save chunk metadata"""
        metadata = []
        for i, chunk in enumerate(chunks):
            metadata.append({
                "index": i,
                "text": chunk["text"],
                "source": chunk["source"],
                "page": chunk["page"],
                "chunk_id": chunk["chunk_id"]
            })
        
        with open("data/indices/metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"  → Metadata saved ({len(metadata)} chunks)")
    
    def generate_faq_embeddings(self, faq_path="data/faq.json"):
        """Generate and cache FAQ embeddings in the FAQ file
        
        This pre-computes embeddings for all FAQ questions and stores them
        in the FAQ JSON file for faster loading.
        """
        if not os.path.exists(faq_path):
            print(f"❌ FAQ file not found: {faq_path}")
            return False
        
        try:
            # Load FAQ data
            with open(faq_path, "r", encoding="utf-8") as f:
                faq_data = json.load(f)
            
            if not faq_data.get("faqs"):
                print("❌ No FAQs found in file")
                return False
            
            # Extract questions
            questions = [faq["question"] for faq in faq_data["faqs"]]
            print(f"📝 Found {len(questions)} FAQ questions")
            
            # Generate embeddings in batches
            print(f"🔄 Computing embeddings in batches of {self.batch_size}...")
            embeddings_list = []
            
            for i in range(0, len(questions), self.batch_size):
                batch = questions[i:i + self.batch_size]
                print(f"  Processing batch {i // self.batch_size + 1}/{(len(questions) + self.batch_size - 1) // self.batch_size}")
                
                batch_embeddings = self.model.encode(
                    batch,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    batch_size=self.batch_size
                )
                embeddings_list.append(batch_embeddings)
            
            # Concatenate all batches
            all_embeddings = np.vstack(embeddings_list) if len(embeddings_list) > 1 else embeddings_list[0]
            
            # Add embeddings to FAQ data
            for i, faq in enumerate(faq_data["faqs"]):
                faq["embedding"] = all_embeddings[i].tolist()
            
            # Update metadata
            if "metadata" not in faq_data:
                faq_data["metadata"] = {}
            
            faq_data["metadata"]["embedding_model"] = self.config["embedding_model"]
            faq_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            faq_data["metadata"]["total_entries"] = len(faq_data["faqs"])
            
            # Save updated FAQ file
            with open(faq_path, "w", encoding="utf-8") as f:
                json.dump(faq_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ FAQ embeddings saved to {faq_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating FAQ embeddings: {e}")
            return False

def main():
    """Command line interface for indexing"""
    import sys
    
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Create indexer
    indexer = DocumentIndexer(config)
    
    # Check for FAQ embedding command
    if len(sys.argv) > 1 and sys.argv[1] == "--faq":
        print("🔄 Generating FAQ embeddings...")
        success = indexer.generate_faq_embeddings()
        if success:
            print("✅ FAQ embeddings generated successfully!")
        else:
            print("❌ FAQ embedding generation failed")
        sys.exit(0 if success else 1)
    
    # Get document directory from command line or use default
    doc_dir = sys.argv[1] if len(sys.argv) > 1 else "data/documents"
    
    # Build indices
    success = indexer.build_indices(doc_dir)
    
    if success:
        print("\n🎉 Indexing completed successfully!")
        print("You can now run the Streamlit app: streamlit run app.py")
    else:
        print("\n❌ Indexing failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
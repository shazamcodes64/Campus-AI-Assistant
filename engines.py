import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
import pickle
import os
import time
import gc
from typing import List, Dict, Any

class SearchEngine:
    def __init__(self, config):
        self.config = config
        self.model = SentenceTransformer(config["embedding_model"])
        self.faq_threshold = config["faq_threshold"]
        self.doc_threshold = config["doc_threshold"]
        self.high_sim_threshold = config["high_similarity_threshold"]
        self.batch_size = config.get("embedding_batch_size", 32)
        self.faq_cache_ttl = config.get("faq_cache_ttl_seconds", 3600)
        
        # FAQ embedding cache
        self._faq_embeddings_cache = None
        self._faq_cache_timestamp = None
        self._faq_questions_cache = None
        
        # Check if indices exist - fail fast
        if not os.path.exists("data/indices/faiss.index"):
            raise RuntimeError("❌ FAISS index not found. Run: python indexer.py first")
        if not os.path.exists("data/indices/bm25_index.pkl"):
            raise RuntimeError("❌ BM25 index not found. Run: python indexer.py first")
        if not os.path.exists("data/indices/metadata.json"):
            raise RuntimeError("❌ Metadata not found. Run: python indexer.py first")
        
        # Load FAQ data
        self.faq_data = self._load_faq()
        
        # Load indices
        self.faiss_index = self._load_faiss()
        self.bm25_index = self._load_bm25()
        self.metadata = self._load_metadata()
    
    def _load_faq(self):
        """Load FAQ data from JSON file"""
        try:
            if os.path.exists("data/faq.json"):
                with open("data/faq.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading FAQ: {e}")
        return {"faqs": []}
    
    def _load_faiss(self):
        """Load FAISS index"""
        try:
            if os.path.exists("data/indices/faiss.index"):
                return faiss.read_index("data/indices/faiss.index")
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
        return None
    
    def _load_bm25(self):
        """Load BM25 index"""
        try:
            if os.path.exists("data/indices/bm25_index.pkl"):
                with open("data/indices/bm25_index.pkl", "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading BM25 index: {e}")
        return None
    
    def _load_metadata(self):
        """Load chunk metadata"""
        try:
            if os.path.exists("data/indices/metadata.json"):
                with open("data/indices/metadata.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading metadata: {e}")
        return []
    
    def _get_faq_embeddings(self) -> tuple:
        """Get FAQ embeddings with caching and batch processing"""
        if not self.faq_data.get("faqs"):
            return None, []
        
        current_time = time.time()
        faq_questions = [faq["question"] for faq in self.faq_data["faqs"]]
        
        # Check if cache is valid
        cache_valid = (
            self._faq_embeddings_cache is not None and
            self._faq_cache_timestamp is not None and
            self._faq_questions_cache == faq_questions and
            (current_time - self._faq_cache_timestamp) < self.faq_cache_ttl
        )
        
        if cache_valid:
            return self._faq_embeddings_cache, faq_questions
        
        # Compute embeddings in batches for memory efficiency
        print(f"🔄 Computing FAQ embeddings for {len(faq_questions)} questions...")
        embeddings_list = []
        
        for i in range(0, len(faq_questions), self.batch_size):
            batch = faq_questions[i:i + self.batch_size]
            batch_embeddings = self.model.encode(
                batch, 
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=self.batch_size
            )
            embeddings_list.append(batch_embeddings)
        
        # Concatenate all batches
        faq_embeddings = np.vstack(embeddings_list) if len(embeddings_list) > 1 else embeddings_list[0]
        
        # Update cache
        self._faq_embeddings_cache = faq_embeddings
        self._faq_cache_timestamp = current_time
        self._faq_questions_cache = faq_questions
        
        # Trigger GC after heavy embedding computation
        gc.collect()
        
        print(f"✅ FAQ embeddings cached ({len(faq_questions)} entries)")
        return faq_embeddings, faq_questions
    
    def encode_batch(self, texts: List[str], batch_size: int = None) -> np.ndarray:
        """Encode texts in batches for memory efficiency
        
        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding (defaults to config value)
            
        Returns:
            numpy array of embeddings
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        if not texts:
            return np.array([])
        
        # Process in batches
        embeddings_list = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=batch_size
            )
            embeddings_list.append(batch_embeddings)
        
        # Concatenate all batches
        result = np.vstack(embeddings_list) if len(embeddings_list) > 1 else embeddings_list[0]
        
        # Trigger GC after batch encoding to free memory
        gc.collect()
        
        return result
    
    def search(self, query: str) -> dict:
        """Combined FAQ + document search with smart routing"""
        
        # Always do both searches and compare scores
        faq_result = self._search_faq(query)
        doc_result = self._search_documents(query)
        
        faq_score = faq_result.get("confidence", 0.0)
        doc_score = doc_result.get("confidence", 0.0)
        
        # Smart routing: FAQ only if high confidence AND better than docs
        if faq_score >= self.faq_threshold and faq_score > doc_score:
            return {
                "type": "faq",
                "result": faq_result,
                "confidence": faq_score
            }
        
        # Use document search if above threshold
        elif doc_score >= self.doc_threshold:
            return {
                "type": "document", 
                "result": doc_result,
                "confidence": doc_score
            }
        
        # Out of scope
        else:
            return {
                "type": "out_of_scope",
                "result": {"answer": "I couldn't find this information in the uploaded documents.", "sources": []},
                "confidence": 0.0
            }
    
    def search_batch(self, queries: List[str]) -> List[dict]:
        """Batch search for multiple queries with optimized embedding computation
        
        Args:
            queries: List of query strings
            
        Returns:
            List of search results (same format as search())
        """
        if not queries:
            return []
        
        # Compute all query embeddings in one batch for efficiency
        query_embeddings = self.encode_batch(queries)
        
        # Process each query with pre-computed embeddings
        results = []
        for i, query in enumerate(queries):
            query_embedding = query_embeddings[i:i+1]  # Keep 2D shape
            
            # Search FAQ and documents with pre-computed embedding
            faq_result = self._search_faq_with_embedding(query, query_embedding)
            doc_result = self._search_documents_with_embedding(query, query_embedding)
            
            faq_score = faq_result.get("confidence", 0.0)
            doc_score = doc_result.get("confidence", 0.0)
            
            # Smart routing
            if faq_score >= self.faq_threshold and faq_score > doc_score:
                results.append({
                    "type": "faq",
                    "result": faq_result,
                    "confidence": faq_score
                })
            elif doc_score >= self.doc_threshold:
                results.append({
                    "type": "document",
                    "result": doc_result,
                    "confidence": doc_score
                })
            else:
                results.append({
                    "type": "out_of_scope",
                    "result": {"answer": "I couldn't find this information in the uploaded documents.", "sources": []},
                    "confidence": 0.0
                })
        
        # Trigger GC after batch processing to free memory
        gc.collect()
        
        return results
    
    def _search_faq(self, query: str) -> dict:
        """Search FAQ database with cached embeddings"""
        if not self.faq_data.get("faqs"):
            return {"answer": None, "confidence": 0.0, "source_id": None}
        
        try:
            # Get query embedding (single query, no batching needed)
            query_embedding = self.model.encode([query], normalize_embeddings=True)
            return self._search_faq_with_embedding(query, query_embedding)
        
        except Exception as e:
            print(f"Error in FAQ search: {e}")
        
        return {"answer": None, "confidence": 0.0, "source_id": None}
    
    def _search_faq_with_embedding(self, query: str, query_embedding: np.ndarray) -> dict:
        """Search FAQ database with pre-computed query embedding
        
        Args:
            query: Original query string (for logging/debugging)
            query_embedding: Pre-computed normalized embedding (2D array)
        """
        if not self.faq_data.get("faqs"):
            return {"answer": None, "confidence": 0.0, "source_id": None}
        
        try:
            # Get FAQ embeddings from cache
            faq_embeddings, faq_questions = self._get_faq_embeddings()
            
            if faq_embeddings is None:
                return {"answer": None, "confidence": 0.0, "source_id": None}
            
            # Compute similarities
            similarities = util.cos_sim(query_embedding, faq_embeddings)[0]
            best_idx = int(similarities.argmax())
            best_score = float(similarities.max())
            
            if best_score >= 0.5:  # Minimum threshold for FAQ
                return {
                    "answer": self.faq_data["faqs"][best_idx]["answer"],
                    "confidence": best_score,
                    "source_id": self.faq_data["faqs"][best_idx].get("id", f"faq_{best_idx}"),
                    "sources": [f"FAQ: {self.faq_data['faqs'][best_idx]['question']}"]
                }
        
        except Exception as e:
            print(f"Error in FAQ search with embedding: {e}")
        
        return {"answer": None, "confidence": 0.0, "source_id": None}
    
    def _search_documents(self, query: str) -> dict:
        """Hybrid document search (FAISS + BM25)"""
        if not self.faiss_index or not self.bm25_index or not self.metadata:
            return {"chunks": [], "confidence": 0.0, "sources": []}
        
        try:
            # Get query embedding
            query_embedding = self.model.encode([query], normalize_embeddings=True)
            return self._search_documents_with_embedding(query, query_embedding)
        
        except Exception as e:
            print(f"Error in document search: {e}")
            return {"chunks": [], "confidence": 0.0, "sources": []}
    
    def _search_documents_with_embedding(self, query: str, query_embedding: np.ndarray) -> dict:
        """Hybrid document search with pre-computed query embedding
        
        Args:
            query: Original query string (for BM25 search)
            query_embedding: Pre-computed normalized embedding (2D array)
        """
        if not self.faiss_index or not self.bm25_index or not self.metadata:
            return {"chunks": [], "confidence": 0.0, "sources": []}
        
        try:
            # FAISS search (semantic)
            faiss_scores, faiss_indices = self.faiss_index.search(query_embedding, 5)
            faiss_results = []
            for score, idx in zip(faiss_scores[0], faiss_indices[0]):
                if idx < len(self.metadata):
                    faiss_results.append({
                        "chunk_idx": int(idx),
                        "score": float(score),
                        "text": self.metadata[idx]["text"],
                        "source": self.metadata[idx]["source"],
                        "page": self.metadata[idx]["page"]
                    })
            
            # BM25 search (keyword)
            bm25_scores = self.bm25_index.get_scores(query.split())
            bm25_results = []
            for idx, score in enumerate(bm25_scores):
                if score > 0 and idx < len(self.metadata):
                    bm25_results.append({
                        "chunk_idx": idx,
                        "score": float(score),
                        "text": self.metadata[idx]["text"],
                        "source": self.metadata[idx]["source"],
                        "page": self.metadata[idx]["page"]
                    })
            
            # Sort BM25 results and take top 5
            bm25_results = sorted(bm25_results, key=lambda x: x["score"], reverse=True)[:5]
            
            # Combine and deduplicate results with PROPER NORMALIZATION
            all_results = {}
            
            # Normalize FAISS scores (0-1 range)
            if faiss_results:
                max_faiss = max([r["score"] for r in faiss_results])
                min_faiss = min([r["score"] for r in faiss_results])
                faiss_range = max_faiss - min_faiss if max_faiss > min_faiss else 1.0
                
                for result in faiss_results:
                    idx = result["chunk_idx"]
                    normalized_faiss = (result["score"] - min_faiss) / faiss_range
                    all_results[idx] = result.copy()
                    all_results[idx]["faiss_score"] = normalized_faiss
                    all_results[idx]["bm25_score"] = 0.0
            
            # Normalize BM25 scores (0-1 range)
            if bm25_results:
                max_bm25 = max([r["score"] for r in bm25_results])
                min_bm25 = min([r["score"] for r in bm25_results]) if len(bm25_results) > 1 else 0.0
                bm25_range = max_bm25 - min_bm25 if max_bm25 > min_bm25 else 1.0
                
                for result in bm25_results:
                    idx = result["chunk_idx"]
                    normalized_bm25 = (result["score"] - min_bm25) / bm25_range if bm25_range > 0 else 0.0
                    
                    if idx in all_results:
                        all_results[idx]["bm25_score"] = normalized_bm25
                    else:
                        all_results[idx] = result.copy()
                        all_results[idx]["faiss_score"] = 0.0
                        all_results[idx]["bm25_score"] = normalized_bm25
            
            # Hybrid scoring (60% semantic, 40% keyword)
            final_results = []
            for result in all_results.values():
                hybrid_score = (0.6 * result.get("faiss_score", 0.0) + 
                              0.4 * result.get("bm25_score", 0.0))
                result["score"] = hybrid_score
                final_results.append(result)
            
            # Sort by hybrid score and take top 3
            final_results = sorted(final_results, key=lambda x: x["score"], reverse=True)[:3]
            
            # Calculate overall confidence
            confidence = sum([r["score"] for r in final_results]) / len(final_results) if final_results else 0.0
            
            # Format sources
            sources = []
            for result in final_results:
                sources.append(f"{result['source']} (page {result['page']})")
            
            return {
                "chunks": final_results,
                "confidence": confidence,
                "sources": sources
            }
        
        except Exception as e:
            print(f"Error in document search with embedding: {e}")
            return {"chunks": [], "confidence": 0.0, "sources": []}
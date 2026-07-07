import requests
import json
import gc

class LLMGenerator:
    def __init__(self, config):
        self.ollama_url = config["ollama_url"]
        self.model_name = config["model_name"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        self.high_sim_threshold = config["high_similarity_threshold"]
    
    def generate_response(self, query: str, search_result: dict) -> dict:
        """Generate response with smart LLM usage"""
        
        if search_result["type"] == "faq":
            # Direct FAQ answer - no LLM needed
            faq_result = search_result["result"]
            return {
                "answer": faq_result["answer"],
                "confidence": search_result["confidence"],
                "sources": faq_result.get("sources", []),
                "method": "faq_direct"
            }
        
        elif search_result["type"] == "document":
            doc_result = search_result["result"]
            chunks = doc_result["chunks"]
            
            if not chunks:
                return {
                    "answer": "No relevant information found.",
                    "confidence": 0.0,
                    "sources": [],
                    "method": "no_chunks"
                }
            
            # Smart LLM usage: skip LLM for high-similarity single chunks
            if len(chunks) == 1 and chunks[0]["score"] >= self.high_sim_threshold:
                return {
                    "answer": chunks[0]["text"],
                    "confidence": search_result["confidence"],
                    "sources": doc_result["sources"],
                    "method": "direct_chunk"
                }
            
            # Use LLM for multi-chunk synthesis or lower confidence
            return self._generate_llm_response(query, chunks, doc_result["sources"], search_result["confidence"])
        
        else:  # out_of_scope
            return search_result["result"]
    
    def _generate_llm_response(self, query: str, chunks: list, sources: list, confidence: float) -> dict:
        """Generate LLM response for document chunks"""
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source {i+1}: {chunk['source']}, page {chunk['page']}]")
            context_parts.append(chunk["text"])
            context_parts.append("")  # Empty line between chunks
        
        context = "\n".join(context_parts)
        
        # Build prompt
        prompt = f"""You are an academic assistant. Answer the question based only on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Answer concisely and accurately based only on the provided context
- Include source references like [Source 1] when mentioning information
- If the context doesn't contain enough information, say so
- Maximum 500 tokens

Answer:"""
        
        try:
            # Call Ollama API with proper timeout and error handling
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=30  # MANDATORY timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                # Trigger GC after LLM generation to free memory
                gc.collect()
                
                if answer:
                    return {
                        "answer": answer,
                        "confidence": confidence,
                        "sources": sources,
                        "method": "llm_synthesis"
                    }
            
            # Fallback if LLM fails
            return self._create_fallback_response(chunks, sources, confidence, "llm_http_error")
        
        except requests.exceptions.Timeout:
            print("LLM request timed out after 30 seconds")
            return self._create_fallback_response(chunks, sources, confidence, "llm_timeout")
        
        except requests.exceptions.ConnectionError:
            print("Cannot connect to Ollama service")
            return self._create_fallback_response(chunks, sources, confidence, "llm_connection_error")
        
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return self._create_fallback_response(chunks, sources, confidence, "llm_error")
    
    def _create_fallback_response(self, chunks, sources, confidence, error_type):
        """Create fallback response when LLM fails"""
        fallback_answer = "LLM service unavailable. Here are the relevant excerpts:\n\n" + \
                         "\n\n".join([f"From {chunk['source']} (page {chunk['page']}):\n{chunk['text']}" 
                                     for chunk in chunks])
        
        return {
            "answer": fallback_answer,
            "confidence": confidence,
            "sources": sources,
            "method": f"llm_fallback_{error_type}"
        }
    
    def test_connection(self) -> bool:
        """Test Ollama connection with proper timeout"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.Timeout:
            print("Ollama connection timed out")
            return False
        except requests.exceptions.ConnectionError:
            print("Cannot connect to Ollama service")
            return False
        except Exception as e:
            print(f"Error testing Ollama connection: {e}")
            return False
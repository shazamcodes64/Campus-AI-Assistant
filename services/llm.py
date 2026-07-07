from llama_index.llms.ollama import Ollama

def load_llm():
    return Ollama(
        model="deepseek-r1:7b",
        request_timeout=120.0
    )

from llama_index.core.prompts import PromptTemplate

RELEVANCE_PROMPT = PromptTemplate(
    template="""
Is the following text relevant to the question?

TEXT:
{context}

QUESTION:
{query}

Answer only yes or no.
"""
)

QUERY_REWRITE_PROMPT = PromptTemplate(
    template="""
Rewrite the following query to improve search relevance.

Query:
{query}

Return only the improved query.
"""
)

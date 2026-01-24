"""
Template retrieval tool using Qdrant semantic search.
"""
from typing import Any, Dict, List

from langchain.tools import BaseTool
from pydantic import Field

from src.config.settings import get_settings
from src.data.cache import embedding_cache
from src.monitoring.metrics import cache_hit, cache_miss, track_tool_execution
from src.retrieval.embeddings import generate_embedding
from src.retrieval.qdrant_client import search_similar


class TemplateRetrievalTool(BaseTool):
    """Tool for retrieving similar response templates."""

    name: str = "template_retrieval"
    description: str = """
    Retrieves the most similar response templates for a given guest query.
    Use this tool when you need to find pre-written templates that match the guest's question.

    Input should be the guest's message/query as a string.

    Returns a list of relevant templates with their similarity scores.
    """

    @track_tool_execution("template_retrieval")
    async def _arun(self, query: str) -> str:
        """Async implementation of template retrieval."""
        settings = get_settings()

        # Check embedding cache
        embedding = embedding_cache.get_embedding(query)
        if embedding:
            cache_hit.labels(cache_type="embedding").inc()
        else:
            cache_miss.labels(cache_type="embedding").inc()
            # Generate embedding
            embedding = await generate_embedding(query)
            # Cache embedding
            embedding_cache.set_embedding(query, embedding)

        # Search Qdrant
        results = await search_similar(
            collection_name=settings.qdrant_collection_name,
            query_vector=embedding,
            limit=settings.retrieval_top_k,
            score_threshold=settings.retrieval_similarity_threshold,
        )

        if not results:
            return "No relevant templates found."

        # Format results
        output = []
        for i, result in enumerate(results, 1):
            output.append(
                f"Template {i} (similarity: {result['score']:.3f}):\n"
                f"Category: {result['payload']['category']}\n"
                f"Text: {result['payload']['text']}\n"
            )

        return "\n".join(output)

    def _run(self, query: str) -> str:
        """Sync implementation (not supported)."""
        raise NotImplementedError("Use async version")


async def retrieve_templates(query: str) -> List[Dict[str, Any]]:
    """Retrieve templates for a query (direct function for use in agent)."""
    settings = get_settings()

    # Check embedding cache
    embedding = embedding_cache.get_embedding(query)
    if embedding:
        cache_hit.labels(cache_type="embedding").inc()
    else:
        cache_miss.labels(cache_type="embedding").inc()
        embedding = await generate_embedding(query)
        embedding_cache.set_embedding(query, embedding)

    # Search Qdrant
    results = await search_similar(
        collection_name=settings.qdrant_collection_name,
        query_vector=embedding,
        limit=settings.retrieval_top_k,
        score_threshold=settings.retrieval_similarity_threshold,
    )

    return results

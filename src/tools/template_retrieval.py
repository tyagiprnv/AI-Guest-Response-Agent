"""
Template retrieval tool using Qdrant semantic search.

This module retrieves response templates by searching against trigger queries
stored in Qdrant. Since multiple trigger queries may match the same template,
results are deduplicated by template_id, keeping the highest score.
"""
from typing import Any, Dict, List

from langchain.tools import BaseTool
from pydantic import Field

from src.config.settings import get_settings
from src.data.cache import embedding_cache
from src.monitoring.metrics import cache_hit, cache_miss, track_tool_execution
from src.retrieval.embeddings import generate_embedding
from src.retrieval.qdrant_client import search_similar


def deduplicate_by_template_id(results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """
    Deduplicate search results by template_id, keeping highest score per template.

    Since each template has multiple trigger queries indexed, a user query may
    match several trigger queries from the same template. This function keeps
    only the highest-scoring match per template.

    Args:
        results: List of search results from Qdrant
        top_k: Number of unique templates to return

    Returns:
        Deduplicated list of results, up to top_k templates
    """
    seen_templates = {}

    for result in results:
        template_id = result["payload"]["template_id"]

        # Keep the highest scoring result for each template
        if template_id not in seen_templates or result["score"] > seen_templates[template_id]["score"]:
            seen_templates[template_id] = result

    # Sort by score and return top_k
    unique_results = sorted(
        seen_templates.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    return unique_results[:top_k]


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
        embedding = await embedding_cache.get_embedding(query)
        if embedding:
            cache_hit.labels(cache_type="embedding").inc()
        else:
            cache_miss.labels(cache_type="embedding").inc()
            # Generate embedding
            embedding = await generate_embedding(query)
            # Cache embedding
            await embedding_cache.set_embedding(query, embedding)

        # Search Qdrant - fetch more results to account for deduplication (reduced from 3x to 2x)
        fetch_limit = settings.retrieval_top_k * 2
        results = await search_similar(
            collection_name=settings.qdrant_collection_name,
            query_vector=embedding,
            limit=fetch_limit,
            score_threshold=settings.retrieval_similarity_threshold,
        )

        if not results:
            return "No relevant templates found."

        # Deduplicate by template_id
        unique_results = deduplicate_by_template_id(results, settings.retrieval_top_k)

        # Format results
        output = []
        for i, result in enumerate(unique_results, 1):
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
    embedding = await embedding_cache.get_embedding(query)
    if embedding:
        cache_hit.labels(cache_type="embedding").inc()
    else:
        cache_miss.labels(cache_type="embedding").inc()
        embedding = await generate_embedding(query)
        await embedding_cache.set_embedding(query, embedding)

    # Search Qdrant - fetch more results to account for deduplication (reduced from 3x to 2x)
    fetch_limit = settings.retrieval_top_k * 2
    results = await search_similar(
        collection_name=settings.qdrant_collection_name,
        query_vector=embedding,
        limit=fetch_limit,
        score_threshold=settings.retrieval_similarity_threshold,
    )

    # Deduplicate by template_id before returning
    return deduplicate_by_template_id(results, settings.retrieval_top_k)

"""
Embedding generation using OpenAI.
"""
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from src.config.settings import get_settings


@lru_cache(maxsize=1)
def get_embeddings_model() -> OpenAIEmbeddings:
    """Get cached OpenAI embeddings model."""
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text."""
    embeddings_model = get_embeddings_model()
    embedding = await embeddings_model.aembed_query(text)
    return embedding


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    embeddings_model = get_embeddings_model()
    embeddings = await embeddings_model.aembed_documents(texts)
    return embeddings

"""
Embedding generation using sentence-transformers.
"""
import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.config.settings import get_settings


@lru_cache(maxsize=1)
def get_embeddings_model() -> SentenceTransformer:
    """Get cached sentence-transformers model."""
    settings = get_settings()
    # Load model (downloads on first run, ~80MB)
    # Model: all-MiniLM-L6-v2 (384 dimensions, ~120M params)
    # Performance: ~2000 sentences/sec on CPU, ~10000/sec on GPU
    return SentenceTransformer(
        settings.embedding_model,
        device="cpu",  # Use "cuda" if GPU available
    )


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for text.

    sentence-transformers is sync, so run in executor to avoid blocking.
    """
    model = get_embeddings_model()
    loop = asyncio.get_event_loop()

    # Run sync model.encode() in thread pool to not block event loop
    embedding = await loop.run_in_executor(
        None,  # Use default executor
        lambda: model.encode(text, convert_to_tensor=False)
    )

    return embedding.tolist()


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    sentence-transformers batches efficiently, so run entire batch in executor.
    """
    model = get_embeddings_model()
    loop = asyncio.get_event_loop()

    # Batch encoding is efficient (processes in parallel internally)
    embeddings = await loop.run_in_executor(
        None,
        lambda: model.encode(texts, convert_to_tensor=False)
    )

    return [emb.tolist() for emb in embeddings]

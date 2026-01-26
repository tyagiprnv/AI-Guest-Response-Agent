"""
Application configuration using Pydantic settings.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = Field(..., description="OpenAI API key")
    deepseek_api_key: str = Field(..., description="DeepSeek API key")

    # LangSmith Configuration
    langsmith_api_key: str = Field(..., description="LangSmith API key")
    langsmith_project: str = Field(
        default="guest-response-agent", description="LangSmith project name"
    )
    langsmith_tracing_v2: bool = Field(default=True, description="Enable LangSmith tracing")

    # Vector Database
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection_name: str = Field(
        default="response_templates", description="Qdrant collection name"
    )

    # Application Settings
    environment: Literal["development", "production", "test"] = Field(
        default="development", description="Application environment"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # Embedding Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )
    embedding_dimension: int = Field(default=1536, description="Embedding dimension")

    # LLM Configuration
    llm_model: str = Field(default="deepseek-chat", description="DeepSeek model")
    llm_temperature: float = Field(default=0.7, description="LLM temperature")
    llm_max_tokens: int = Field(default=1000, description="LLM max tokens")

    # Retrieval Configuration
    retrieval_top_k: int = Field(default=3, description="Number of templates to retrieve")
    retrieval_similarity_threshold: float = Field(
        default=0.70, description="Similarity threshold for template matching (with trigger-query embeddings)"
    )

    # Direct Template Substitution
    direct_substitution_enabled: bool = Field(
        default=True, description="Enable direct template substitution for high-confidence matches"
    )
    direct_substitution_threshold: float = Field(
        default=0.85, description="Similarity threshold for direct template substitution (skips LLM, requires trigger-query embeddings)"
    )

    # Cache Configuration
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds")
    embedding_cache_size: int = Field(default=1000, description="Embedding cache size")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

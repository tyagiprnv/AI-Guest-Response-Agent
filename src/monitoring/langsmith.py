"""
LangSmith tracing integration.
"""
import os
from functools import lru_cache

from src.config.settings import get_settings


@lru_cache(maxsize=1)
def setup_langsmith() -> None:
    """Set up LangSmith tracing."""
    settings = get_settings()

    # Set environment variables for LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langsmith_tracing_v2).lower()
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    print(f"LangSmith tracing enabled for project: {settings.langsmith_project}")


def get_trace_url(run_id: str) -> str:
    """Get LangSmith trace URL for a run."""
    settings = get_settings()
    return f"https://smith.langchain.com/o/default/projects/p/{settings.langsmith_project}/r/{run_id}"

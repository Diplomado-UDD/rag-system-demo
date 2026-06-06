"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str

    # OpenRouter API
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Models
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "~openai/gpt-latest"

    # Chunking
    chunk_size: int = 600
    chunk_overlap: int = 100

    # Retrieval
    top_k_results: int = 5
    min_similarity_threshold: float = 0.3

    # File Upload
    max_file_size_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

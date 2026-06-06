"""Tests for configuration module."""

import os
import pytest
from src.core.config import Settings


def test_settings_loads_from_env(monkeypatch):
    """Test that Settings loads values from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql://test:test@localhost/test"
    assert settings.openrouter_api_key == "test-key"
    assert settings.chunk_size == 600
    assert settings.max_file_size_mb == 50


def test_settings_has_default_values(monkeypatch):
    """Test that Settings has sensible default values."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.llm_model == "~openai/gpt-latest"
    assert settings.top_k_results == 5
    assert settings.min_similarity_threshold == 0.3

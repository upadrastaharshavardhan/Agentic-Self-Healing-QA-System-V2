"""Central configuration using Pydantic Settings. All tunables live here."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # Fully deterministic offline mode for demos & tests


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Runtime mode ──────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    mock_llm: bool = True  # Default True so the system runs without API keys

    # ── LLM ───────────────────────────────────────────────────────────────
    llm_provider: LLMProvider = LLMProvider.MOCK
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_timeout_seconds: float = 60.0

    # ── Bounds (hard safety limits) ───────────────────────────────────────
    max_investigation_iterations: int = 3
    max_test_retries: int = 2
    max_recovery_attempts: int = 1
    classification_confidence_threshold: float = 0.65
    rca_confidence_threshold: float = 0.70
    auto_recovery_max_risk: Literal["LOW", "MEDIUM"] = "LOW"

    # ── Persistence ───────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/ashqa.db"
    enable_vector_memory: bool = False  # Requires pgvector setup

    # ── Observability ─────────────────────────────────────────────────────
    otel_enabled: bool = False
    otel_service_name: str = "agentic-self-healing-qa"
    log_level: str = "INFO"

    # ── API ───────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # ── Safety ────────────────────────────────────────────────────────────
    allow_level_2_recovery: bool = True
    allow_level_3_proposals: bool = True
    require_human_for_level_3_plus: bool = True
    mask_secrets_in_logs: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()

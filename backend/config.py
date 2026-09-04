"""
LedgerLens — Application Configuration
Driven entirely by environment variables (or .env file).
Never hardcode secrets or tuning parameters.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://ledgerlens:ledgerlens@localhost:5432/ledgerlens",
        description="Async PostgreSQL connection URL",
    )

    # ── LLM Provider ─────────────────────────────────────────────────────────
    llm_provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    gemini_model: str = "gemini-2.5-pro"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-opus-4-5"

    @computed_field
    @property
    def active_llm_model(self) -> str:
        """Returns the model name for the active LLM provider."""
        return {
            "gemini": self.gemini_model,
            "openai": self.openai_model,
            "anthropic": self.anthropic_model,
        }[self.llm_provider]

    @computed_field
    @property
    def active_llm_api_key(self) -> str:
        """Returns the API key for the active LLM provider."""
        return {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }[self.llm_provider]

    # ── Reconciliation Tuning ─────────────────────────────────────────────────
    fuzzy_match_window_hours: float = Field(
        default=6.0,
        description="Timestamp tolerance for Level-4 fuzzy matching (hours)",
    )
    strict_match_window_hours: float = Field(
        default=24.0,
        description="Timestamp tolerance for Level-5 relational matching (hours)",
    )
    amount_tolerance_inr: float = Field(
        default=0.01,
        description="Max INR difference to still consider an exact amount match",
    )

    # ── Confidence Thresholds ─────────────────────────────────────────────────
    auto_resolve_threshold: float = Field(
        default=0.95,
        description="Confidence ≥ this → eligible for auto-resolve (if type allows)",
    )
    review_threshold: float = Field(
        default=0.75,
        description="Confidence ≥ this but < auto_resolve → review queue; below → escalate",
    )

    # ── AI Agent ─────────────────────────────────────────────────────────────
    max_tool_calls_per_investigation: int = Field(
        default=8,
        description="Hard cap on LLM tool calls per exception investigation",
    )

    # ── Data Generator ───────────────────────────────────────────────────────
    generator_seed: int = Field(
        default=42,
        description="Fixed random seed for reproducible synthetic data generation",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    backend_cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of Settings()."""
    return Settings()

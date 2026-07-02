"""
Application settings using Pydantic Settings.

Loads configuration from environment variables and .env file.
Supports multiple LLM providers: OpenAI, DeepSeek, Qwen, Ollama.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM provider options."""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OLLAMA = "ollama"
    GEMINI = "gemini"


class SearchProvider(str, Enum):
    """Supported search provider options."""

    SERPAPI = "serpapi"
    GOOGLE = "google"
    TAVILY = "tavily"


class Settings(BaseSettings):
    """Global application settings — loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "FinTech Sales Intelligence"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me-to-a-random-secret-key"

    # ---- Database ----
    database_url: str = "postgresql+asyncpg://fintech:fintech_secret@localhost:5432/fintech_sales"
    postgres_user: str = "fintech"
    postgres_password: str = "fintech_secret"
    postgres_db: str = "fintech_sales"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379

    # ---- LLM Provider Selection ----
    llm_provider: LLMProvider = LLMProvider.OPENAI

    # ---- OpenAI ----
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_model_mini: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # ---- DeepSeek ----
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # ---- Qwen ----
    qwen_api_key: str = ""
    qwen_model: str = "qwen-plus"
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ---- Gemini ----
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # ---- Ollama ----
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3"

    # ---- Search ----
    search_provider: SearchProvider = SearchProvider.SERPAPI
    serpapi_key: str = ""
    google_api_key: str = ""
    google_cse_id: str = ""
    tavily_api_key: str = ""

    # ---- Crawling ----
    crawl_rate_limit: int = Field(default=2, ge=1, le=10)
    crawl_timeout: int = Field(default=30, ge=5, le=120)
    crawl_max_pages_per_site: int = Field(default=20, ge=1, le=100)
    respect_robots_txt: bool = True

    # ---- Logging ----
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def active_llm_api_key(self) -> str:
        """Return the API key for the currently selected LLM provider."""
        key_map = {
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.DEEPSEEK: self.deepseek_api_key,
            LLMProvider.QWEN: self.qwen_api_key,
            LLMProvider.OLLAMA: "",  # Ollama runs locally
        }
        return key_map[self.llm_provider]

    @property
    def active_llm_model(self) -> str:
        """Return the model name for the currently selected LLM provider."""
        model_map = {
            LLMProvider.OPENAI: self.openai_model,
            LLMProvider.DEEPSEEK: self.deepseek_model,
            LLMProvider.QWEN: self.qwen_model,
            LLMProvider.OLLAMA: self.ollama_model,
        }
        return model_map[self.llm_provider]

    @property
    def active_llm_base_url(self) -> str:
        """Return the base URL for the currently selected LLM provider."""
        url_map = {
            LLMProvider.OPENAI: self.openai_base_url,
            LLMProvider.DEEPSEEK: self.deepseek_base_url,
            LLMProvider.QWEN: self.qwen_base_url,
            LLMProvider.OLLAMA: self.ollama_base_url,
        }
        return url_map[self.llm_provider]

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

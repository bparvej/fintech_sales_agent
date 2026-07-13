"""
LLM Client Factory — Multi-provider support.

Supports OpenAI, DeepSeek, Qwen, and Ollama through a unified interface.
All providers use the OpenAI-compatible API format.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from openai import AsyncOpenAI

from app.shared.config.settings import LLMProvider, get_settings
from app.shared.logging.logger import get_logger

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    """Abstract interface for LLM clients."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Send a completion request and return structured result."""
        ...

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a completion request expecting JSON output."""
        ...


class OpenAICompatibleClient(BaseLLMClient):
    """
    Unified LLM client for OpenAI-compatible APIs.

    Works with: OpenAI, DeepSeek, Qwen (DashScope), Ollama.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        provider_name: str,
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key if api_key else "ollama",
            base_url=base_url,
        )
        self._model = model
        self._provider_name = provider_name
        self._total_tokens = 0
        self._total_cost = 0.0

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def total_tokens_used(self) -> int:
        return self._total_tokens

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Send a completion request and return structured result."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        start_time = time.monotonic()

        try:
            response = await self._client.chat.completions.create(**kwargs)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Track usage
            tokens_used = 0
            if response.usage:
                tokens_used = response.usage.total_tokens
                self._total_tokens += tokens_used

            content = response.choices[0].message.content or ""

            logger.info(
                "LLM completion",
                provider=self._provider_name,
                model=self._model,
                tokens=tokens_used,
                duration_ms=duration_ms,
            )

            return {
                "content": content,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
                "model": self._model,
                "provider": self._provider_name,
            }

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            
            # Extract readable error message for API keys, quotas, etc.
            error_msg = str(exc)
            if "401" in error_msg or "unauthorized" in error_msg.lower() or "api key" in error_msg.lower():
                error_msg = f"API Key Invalid or Missing for {self._provider_name}."
            elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                error_msg = f"Quota Exceeded or Rate Limit Hit for {self._provider_name}."
                
            logger.error(
                "LLM completion failed",
                provider=self._provider_name,
                model=self._model,
                error=error_msg,
                duration_ms=duration_ms,
            )
            # Raise a user-friendly ValueError that will be caught by the orchestrator
            raise ValueError(error_msg) from exc

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a completion expecting JSON. Adds JSON instruction to system prompt."""
        json_system = (system_prompt or "") + "\n\nYou MUST respond with valid JSON only. No markdown, no code fences."

        return await self.complete(
            prompt=prompt,
            system_prompt=json_system.strip(),
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )


class LLMFactory:
    """Factory for creating LLM clients based on provider configuration."""

    _PROVIDER_MAP = {
        LLMProvider.OPENAI: lambda s: OpenAICompatibleClient(
            api_key=s.openai_api_key,
            base_url=s.openai_base_url,
            model=s.openai_model,
            provider_name="OpenAI",
        ),
        LLMProvider.DEEPSEEK: lambda s: OpenAICompatibleClient(
            api_key=s.deepseek_api_key,
            base_url=s.deepseek_base_url,
            model=s.deepseek_model,
            provider_name="DeepSeek",
        ),
        LLMProvider.QWEN: lambda s: OpenAICompatibleClient(
            api_key=s.qwen_api_key,
            base_url=s.qwen_base_url,
            model=s.qwen_model,
            provider_name="Qwen",
        ),
        LLMProvider.OLLAMA: lambda s: OpenAICompatibleClient(
            api_key="",
            base_url=s.ollama_base_url,
            model=s.ollama_model,
            provider_name="Ollama",
        ),
        LLMProvider.GEMINI: lambda s: OpenAICompatibleClient(
            api_key=s.gemini_api_key,
            base_url=s.gemini_base_url,
            model=s.gemini_model,
            provider_name="Gemini",
        ),
        LLMProvider.GROQ: lambda s: OpenAICompatibleClient(
            api_key=s.groq_api_key,
            base_url=s.groq_base_url,
            model=s.groq_model,
            provider_name="Groq",
        ),
    }

    @classmethod
    def create(cls, provider: Optional[LLMProvider] = None) -> OpenAICompatibleClient:
        """Create an LLM client for the specified or configured provider."""
        settings = get_settings()
        provider = provider or settings.llm_provider
        factory_fn = cls._PROVIDER_MAP.get(provider)
        if not factory_fn:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        client = factory_fn(settings)
        logger.info("LLM client created", provider=client.provider_name, model=client.model_name)
        return client

    @classmethod
    def create_for_provider_name(cls, provider_name: str) -> OpenAICompatibleClient:
        """Create an LLM client from a string provider name (for API/UI selection)."""
        try:
            provider = LLMProvider(provider_name.lower())
        except ValueError:
            raise ValueError(f"Unknown provider: {provider_name}. Options: {[p.value for p in LLMProvider]}")
        return cls.create(provider)

    @classmethod
    def available_providers(cls) -> list[dict[str, str]]:
        """Return list of available LLM providers for UI dropdown."""
        settings = get_settings()
        providers = []
        for p in LLMProvider:
            info = {
                "value": p.value,
                "label": p.value.title(),
                "configured": False,
            }
            if p == LLMProvider.OPENAI and settings.openai_api_key:
                info["configured"] = True
                info["model"] = settings.openai_model
            elif p == LLMProvider.DEEPSEEK and settings.deepseek_api_key:
                info["configured"] = True
                info["model"] = settings.deepseek_model
            elif p == LLMProvider.QWEN and settings.qwen_api_key:
                info["configured"] = True
                info["model"] = settings.qwen_model
            elif p == LLMProvider.OLLAMA:
                info["configured"] = True  # Ollama is always local
                info["model"] = settings.ollama_model
            elif p == LLMProvider.GEMINI and settings.gemini_api_key:
                info["configured"] = True
                info["model"] = settings.gemini_model
            elif p == LLMProvider.GROQ and settings.groq_api_key:
                info["configured"] = True
                info["model"] = settings.groq_model
            providers.append(info)
        return providers

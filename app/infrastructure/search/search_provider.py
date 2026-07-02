"""
Web search provider abstraction.

Supports SerpAPI, Google Custom Search, and Tavily.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.shared.config.settings import SearchProvider, get_settings
from app.shared.logging.logger import get_logger
from app.shared.utils.retry import async_retry

logger = get_logger(__name__)


class SearchResult:
    """Represents a single search result."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str = "",
        position: int = 0,
    ) -> None:
        self.title = title
        self.url = url
        self.snippet = snippet
        self.position = position

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "position": self.position,
        }


class BaseSearchProvider(ABC):
    """Abstract interface for search providers."""

    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        ...


class SerpAPIProvider(BaseSearchProvider):
    """SerpAPI search implementation."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @async_retry(max_attempts=3)
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://serpapi.com/search.json",
                params={
                    "q": query,
                    "api_key": self._api_key,
                    "num": num_results,
                    "engine": "google",
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("API Key Invalid or Missing for SerpAPI.") from e
                elif e.response.status_code == 429:
                    raise ValueError("Quota Exceeded or Rate Limit Hit for SerpAPI.") from e
                raise ValueError(f"SerpAPI Error: {e}") from e
            data = response.json()

        results = []
        for i, item in enumerate(data.get("organic_results", [])[:num_results]):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=i + 1,
            ))

        logger.info("Search completed", provider="serpapi", query=query, results=len(results))
        return results


class GoogleSearchProvider(BaseSearchProvider):
    """Google Custom Search API implementation."""

    def __init__(self, api_key: str, cse_id: str) -> None:
        self._api_key = api_key
        self._cse_id = cse_id

    @async_retry(max_attempts=3)
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "q": query,
                    "key": self._api_key,
                    "cx": self._cse_id,
                    "num": min(num_results, 10),
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 or e.response.status_code == 403:
                    raise ValueError("API Key Invalid or Missing for Google Custom Search.") from e
                elif e.response.status_code == 429:
                    raise ValueError("Quota Exceeded or Rate Limit Hit for Google Custom Search.") from e
                raise ValueError(f"Google Search Error: {e}") from e
            data = response.json()

        results = []
        for i, item in enumerate(data.get("items", [])[:num_results]):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=i + 1,
            ))

        logger.info("Search completed", provider="google", query=query, results=len(results))
        return results


class TavilySearchProvider(BaseSearchProvider):
    """Tavily search implementation."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @async_retry(max_attempts=3)
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._api_key,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": "advanced",
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("API Key Invalid or Missing for Tavily.") from e
                elif e.response.status_code == 429:
                    raise ValueError("Quota Exceeded or Rate Limit Hit for Tavily.") from e
                raise ValueError(f"Tavily Error: {e}") from e
            data = response.json()

        results = []
        for i, item in enumerate(data.get("results", [])[:num_results]):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                position=i + 1,
            ))

        logger.info("Search completed", provider="tavily", query=query, results=len(results))
        return results


class SearchProviderFactory:
    """Factory for creating the configured search provider."""

    @classmethod
    def create(cls, provider: Optional[SearchProvider] = None) -> BaseSearchProvider:
        settings = get_settings()
        provider = provider or settings.search_provider

        if provider == SearchProvider.SERPAPI:
            return SerpAPIProvider(api_key=settings.serpapi_key)
        elif provider == SearchProvider.GOOGLE:
            return GoogleSearchProvider(
                api_key=settings.google_api_key,
                cse_id=settings.google_cse_id,
            )
        elif provider == SearchProvider.TAVILY:
            return TavilySearchProvider(api_key=settings.tavily_api_key)
    @classmethod
    def available_providers(cls) -> list[dict[str, str]]:
        """Return list of available Search providers for UI dropdown."""
        settings = get_settings()
        providers = []
        for p in SearchProvider:
            info = {
                "value": p.value,
                "label": p.value.title(),
                "configured": False,
            }
            if p == SearchProvider.SERPAPI and settings.serpapi_key:
                info["configured"] = True
            elif p == SearchProvider.GOOGLE and settings.google_api_key and settings.google_cse_id:
                info["configured"] = True
            elif p == SearchProvider.TAVILY and settings.tavily_api_key:
                info["configured"] = True
            providers.append(info)
        return providers

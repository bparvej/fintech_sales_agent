"""
Custom domain exceptions.

Hierarchical exception classes for clean error handling throughout the system.
"""

from __future__ import annotations

from typing import Optional


# ---- Base ----

class DomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# ---- Entity Not Found ----

class EntityNotFoundError(DomainException):
    """Raised when a requested entity does not exist."""
    pass


class ExchangeNotFoundError(EntityNotFoundError):
    """Raised when a stock exchange cannot be found."""
    pass


class InstitutionNotFoundError(EntityNotFoundError):
    """Raised when a financial institution cannot be found."""
    pass


# ---- Agent Errors ----

class AgentExecutionError(DomainException):
    """Raised when an AI agent fails during execution."""

    def __init__(
        self,
        message: str,
        agent_name: str,
        details: Optional[dict] = None,
    ) -> None:
        self.agent_name = agent_name
        super().__init__(message, details)


class AgentTimeoutError(AgentExecutionError):
    """Raised when an agent exceeds its allowed execution time."""
    pass


# ---- Crawling Errors ----

class CrawlError(DomainException):
    """Base exception for web crawling failures."""
    pass


class CrawlFailedError(CrawlError):
    """Raised when a page cannot be crawled."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        super().__init__(f"Failed to crawl {url}: {reason}")


class RateLimitedError(CrawlError):
    """Raised when rate limiting is detected."""

    def __init__(self, url: str, retry_after: Optional[int] = None) -> None:
        self.url = url
        self.retry_after = retry_after
        super().__init__(f"Rate limited on {url}")


class CaptchaDetectedError(CrawlError):
    """Raised when a captcha is encountered."""

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"Captcha detected on {url}")


# ---- LLM Errors ----

class LLMError(DomainException):
    """Base exception for LLM-related failures."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when the LLM API rate limit is exceeded."""
    pass


class LLMResponseParsingError(LLMError):
    """Raised when the LLM response cannot be parsed."""
    pass


# ---- Search Errors ----

class SearchError(DomainException):
    """Base exception for web search failures."""
    pass


class SearchQuotaExceededError(SearchError):
    """Raised when the search API quota is exhausted."""
    pass


# ---- Pipeline Errors ----

class PipelineError(DomainException):
    """Raised when the orchestration pipeline encounters a fatal error."""
    pass


class PipelineStepError(PipelineError):
    """Raised when a specific pipeline step fails."""

    def __init__(self, step_name: str, message: str) -> None:
        self.step_name = step_name
        super().__init__(f"Pipeline step '{step_name}' failed: {message}")


# ---- Validation Errors ----

class ValidationError(DomainException):
    """Raised for domain validation failures."""
    pass

"""
Async retry utilities with exponential backoff.

Wraps tenacity for consistent retry behavior across agents,
crawlers, and external API calls.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.shared.logging.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Default retryable exceptions
TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
    OSError,
)


def async_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    retryable_exceptions: tuple[type[Exception], ...] = TRANSIENT_EXCEPTIONS,
) -> Callable[[F], F]:
    """
    Decorator for async functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum wait time in seconds between retries.
        max_wait: Maximum wait time in seconds between retries.
        retryable_exceptions: Tuple of exception types to retry on.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt < max_attempts:
                        wait_time = min(min_wait * (2 ** (attempt - 1)), max_wait)
                        logger.warning(
                            "Retrying function",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            wait_seconds=wait_time,
                            error=str(exc),
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(exc),
                        )
                        raise

            # Should not reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Retry logic error in {func.__name__}")

        return wrapper  # type: ignore[return-value]

    return decorator

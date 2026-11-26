# resilience/retry_jitter.py
"""Decorrelated Jitter retry decorator with sliding window retry budget enforcement."""

from __future__ import annotations
import asyncio
from collections import deque
from collections.abc import Callable, Coroutine
from functools import wraps
import logging
import random
import time
from typing import Any, TypeVar

logger = logging.getLogger("retry_jitter")

T = TypeVar("T")


class RetryBudgetExhaustedError(Exception):
    """Raised when the application exceeds its global retry allowance over a sliding window."""
    pass


class RetryBudget:
    """Enforces a maximum retry percentage over a sliding time window (e.g., max 20% retries)."""

    def __init__(self, max_retry_ratio: float = 0.20, window_seconds: float = 60.0) -> None:
        self.max_retry_ratio = max_retry_ratio
        self.window_seconds = window_seconds
        self._calls: deque[tuple[float, bool]] = deque()  # (timestamp, is_retry)
        self._lock = asyncio.Lock()

    async def can_retry(self) -> bool:
        """Determines if the global system retry allowance is currently available."""
        async with self._lock:
            now = time.monotonic()
            # Evict expired events outside the sliding window
            while self._calls and now - self._calls[0][0] > self.window_seconds:
                self._calls.popleft()

            total_calls = len(self._calls)
            if total_calls < 20:
                # Minimum sample size before enforcing budget
                self._calls.append((now, True))
                return True

            retry_count = sum(1 for _, is_retry in self._calls if is_retry)
            if (retry_count / total_calls) >= self.max_retry_ratio:
                logger.error("Global retry budget exhausted! Current retry ratio: %.1f%%", (retry_count / total_calls) * 100)
                return False

            self._calls.append((now, True))
            return True

    async def record_initial_call(self) -> None:
        async with self._lock:
            self._calls.append((time.monotonic(), False))


def with_decorrelated_jitter_retry(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    budget: RetryBudget | None = None,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    """Decorator retrying asynchronous functions using Decorrelated Jitter and retry budgeting."""

    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if budget:
                await budget.record_initial_call()

            sleep_duration = base_delay
            attempt = 0

            while True:
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    attempt += 1
                    if attempt > max_retries:
                        logger.error("Function '%s' failed after %d retries. Raising: %s", func.__name__, max_retries, exc)
                        raise

                    if budget and not await budget.can_retry():
                        logger.critical("Retry aborted: System retry budget exceeded for '%s'", func.__name__)
                        raise RetryBudgetExhaustedError("Global retry budget exhausted.") from exc

                    # Calculate Decorrelated Jitter: Uniform(base_delay, sleep_duration * 3)
                    sleep_duration = min(max_delay, random.uniform(base_delay, sleep_duration * 3.0))
                    logger.warning(
                        "Call to '%s' failed (Attempt %d/%d). Retrying in %.3fs. Error: %s",
                        func.__name__,
                        attempt,
                        max_retries,
                        sleep_duration,
                        exc,
                    )
                    await asyncio.sleep(sleep_duration)

        return wrapper
    return decorator

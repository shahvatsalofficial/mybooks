"""
Recipe 02.2: Industrial Decorator Typing with ParamSpec & Concatenate
File: recipe_02_2_typed_decorator.py
Python Version: 3.12+
"""

from __future__ import annotations
import time
import logging
import functools
from typing import Callable, TypeVar, ParamSpec, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelemetryDecorator")

P = ParamSpec("P")
R = TypeVar("R")


class ResilientCircuitBreaker:
    """Circuit breaker state controller for external API integrations."""

    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error("Circuit breaker tripped to OPEN state! Tripped threshold reached.")

    def allow_execution(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.reset_timeout_sec:
                self.state = "HALF_OPEN"
                logger.warning("Circuit breaker entering HALF_OPEN trial state.")
                return True
            return False
        return True  # HALF_OPEN permits trial execution


def with_resilience(
    retries: int = 3,
    backoff_factor: float = 0.5,
    circuit_breaker: Optional[ResilientCircuitBreaker] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Production decorator providing exponential backoff and circuit breaker protection.
    Preserves exact parameter signatures and return types using ParamSpec.
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if circuit_breaker and not circuit_breaker.allow_execution():
                raise ConnectionResetError(f"Circuit breaker OPEN. Request to {func.__name__} denied.")

            last_exception: Optional[Exception] = None
            delay = backoff_factor

            for attempt in range(1, retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result
                except Exception as ex:
                    last_exception = ex
                    logger.warning(
                        f"Invocation {func.__name__} failed attempt {attempt}/{retries}: {ex}"
                    )
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    if attempt < retries:
                        time.sleep(delay)
                        delay *= 2.0

            assert last_exception is not None
            raise last_exception

        return wrapper
    return decorator


# Verification of Type Preservation
breaker = ResilientCircuitBreaker(failure_threshold=2, reset_timeout_sec=2.0)

@with_resilience(retries=3, backoff_factor=0.1, circuit_breaker=breaker)
def fetch_exchange_rate(source_currency: str, target_currency: str, timeout_ms: int = 500) -> float:
    """Fetches high-frequency forex exchange rates from an upstream gateway."""
    if source_currency == "INVALID":
        raise ValueError("Unknown currency denomination")
    return 1.0845


if __name__ == "__main__":
    # 1. Correct invocation verified by Mypy:
    rate = fetch_exchange_rate("EUR", "USD", timeout_ms=300)
    print(f"[*] Successfully retrieved exchange rate: {rate}")

    # 2. Mypy strict mode automatically catches invalid arguments at build-time:
    # fetch_exchange_rate(123, target_currency=True) -> Flagged by Mypy!

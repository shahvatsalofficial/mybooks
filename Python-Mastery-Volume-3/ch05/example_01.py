# resilience/circuit_breaker.py
"""Production-grade asynchronous Circuit Breaker with sliding window metrics."""

from __future__ import annotations
import asyncio
from collections import deque
from enum import Enum
import logging
import time
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger("circuit_breaker")

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""
    pass


class CircuitBreaker:
    """Manages failure tracking and transitions between CLOSED, OPEN, and HALF_OPEN states."""

    def __init__(
        self,
        name: str,
        failure_threshold: float = 0.5,  # Trip if >= 50% failures
        recovery_time: float = 30.0,       # Wait 30 seconds before half-open trial
        window_size: int = 50,             # Track the last 50 calls
        min_requests: int = 10,            # Require at least 10 requests before tripping
        half_open_probes: int = 3,         # Require 3 consecutive successes to close
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.window_size = window_size
        self.min_requests = min_requests
        self.half_open_probes = half_open_probes

        self._state = CircuitState.CLOSED
        self._window: deque[bool] = deque(maxlen=window_size)  # True = Success, False = Failure
        self._last_state_change = time.monotonic()
        self._half_open_successes = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def call(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        fallback: Callable[..., Coroutine[Any, Any, T]] | None = None,
        **kwargs: Any,
    ) -> T:
        """Executes coroutine protected by circuit breaker state boundaries."""
        async with self._lock:
            now = time.monotonic()

            # State Transition: Check if OPEN cooldown has expired
            if self._state == CircuitState.OPEN:
                if now - self._last_state_change >= self.recovery_time:
                    logger.info("CircuitBreaker [%s]: Recovery cooldown expired. Transitioning to HALF_OPEN.", self.name)
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_successes = 0
                    self._last_state_change = now
                else:
                    # Fail fast locally
                    if fallback:
                        logger.debug("CircuitBreaker [%s]: OPEN. Executing fallback.", self.name)
                        return await fallback(*args, **kwargs)
                    raise CircuitBreakerOpenException(f"CircuitBreaker '{self.name}' is OPEN. Request rejected.")

        # Execute remote call outside the lock to prevent concurrency bottlenecks
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as exc:
            await self._record_failure()
            if fallback:
                logger.warning("CircuitBreaker [%s]: Call failed (%s). Executing fallback.", self.name, exc)
                return await fallback(*args, **kwargs)
            raise

    async def _record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                logger.info(
                    "CircuitBreaker [%s]: HALF_OPEN probe success (%d/%d)",
                    self.name,
                    self._half_open_successes,
                    self.half_open_probes,
                )
                if self._half_open_successes >= self.half_open_probes:
                    logger.info("CircuitBreaker [%s]: Probes verified. Transitioning to CLOSED.", self.name)
                    self._state = CircuitState.CLOSED
                    self._window.clear()
                    self._last_state_change = time.monotonic()
            elif self._state == CircuitState.CLOSED:
                self._window.append(True)

    async def _record_failure(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if self._state == CircuitState.HALF_OPEN:
                logger.warning("CircuitBreaker [%s]: HALF_OPEN probe failed. Re-tripping to OPEN.", self.name)
                self._state = CircuitState.OPEN
                self._last_state_change = now
            elif self._state == CircuitState.CLOSED:
                self._window.append(False)
                # Evaluate failure rate threshold
                if len(self._window) >= self.min_requests:
                    failures = self._window.count(False)
                    failure_rate = failures / len(self._window)
                    if failure_rate >= self.failure_threshold:
                        logger.critical(
                            "CircuitBreaker [%s]: Failure rate %.1f%% exceeded threshold %.1f%%. TRIPPING TO OPEN!",
                            self.name,
                            failure_rate * 100,
                            self.failure_threshold * 100,
                        )
                        self._state = CircuitState.OPEN
                        self._last_state_change = now

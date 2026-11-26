"""
Recipe 06.3: Asynchronous Circuit Breaker Guard
File: recipe_06_3_circuit_breaker.py
Python Version: 3.12+
"""

from __future__ import annotations
import asyncio
from enum import Enum
import time
import logging
from typing import Callable, Coroutine, Any, TypeVar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CircuitBreaker")

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "CLOSED"        # Normal: Passing all traffic
    OPEN = "OPEN"            # Tripped: Failing fast locally
    HALF_OPEN = "HALF_OPEN"  # Testing: Passing single canary probe


class CircuitBreakerOpenException(Exception):
    """Raised immediately when call is attempted while circuit is OPEN."""
    pass


class AsyncCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 10.0,
        expected_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.expected_exceptions = expected_exceptions

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.monotonic()
        self._lock = asyncio.Lock()

    async def execute(self, func: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any) -> T:
        """Wraps async network call with state-machine fail-fast protection."""
        async with self._lock:
            now = time.monotonic()
            
            # Check if recovery timeout expired while in OPEN state
            if self.state == CircuitState.OPEN:
                if (now - self.last_state_change) > self.recovery_timeout_sec:
                    logger.info("CircuitBreaker recovery timeout expired. Transitioning to HALF-OPEN.")
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                else:
                    # Fail-fast in ~15 microseconds without touching network!
                    raise CircuitBreakerOpenException(
                        f"Circuit is OPEN. Fail-fast active for {self.recovery_timeout_sec - (now - self.last_state_change):.1f}s."
                    )

        # Execute call outside lock to allow concurrency
        try:
            result = await func(*args, **kwargs)
        except self.expected_exceptions as exc:
            await self._handle_failure(exc)
            raise
        else:
            await self._handle_success()
            return result

    async def _handle_failure(self, exc: Exception) -> None:
        async with self._lock:
            self.failure_count += 1
            logger.warning(f"Call failed ({self.failure_count}/{self.failure_threshold}): {exc}")

            if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
                if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
                    logger.critical("Failure threshold breached! Tripping Circuit to OPEN.")
                    self.state = CircuitState.OPEN
                    self.last_state_change = time.monotonic()

    async def _handle_success(self) -> None:
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Canary probe succeeded! Resetting Circuit to CLOSED.")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = time.monotonic()
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset counter on healthy traffic


# Demonstration
async def mock_remote_service(should_fail: bool) -> str:
    await asyncio.sleep(0.05)
    if should_fail:
        raise ConnectionResetError("Remote database host unreachable.")
    return "Service Response 200 OK"


async def run_circuit_demo() -> None:
    breaker = AsyncCircuitBreaker(failure_threshold=3, recovery_timeout_sec=2.0)

    # 1. Normal traffic
    logger.info("Phase 1: Sending healthy traffic...")
    res = await breaker.execute(mock_remote_service, should_fail=False)
    logger.info(f"Outcome: {res}")

    # 2. Trigger failures to trip circuit
    logger.info("\nPhase 2: Inducing failures...")
    for _ in range(3):
        try:
            await breaker.execute(mock_remote_service, should_fail=True)
        except Exception:
            pass

    # 3. Verify immediate fail-fast behavior
    logger.info("\nPhase 3: Attempting call while OPEN...")
    try:
        await breaker.execute(mock_remote_service, should_fail=False)
    except CircuitBreakerOpenException as e:
        logger.error(f"Captured expected fail-fast: {e}")

    # 4. Wait for cooldown to test HALF-OPEN recovery
    logger.info("\nPhase 4: Waiting for cooldown (2.1s)...")
    await asyncio.sleep(2.1)
    
    # Canary call should reset breaker
    res = await breaker.execute(mock_remote_service, should_fail=False)
    logger.info(f"Canary probe outcome: {res}")
    logger.info(f"Final Circuit State: {breaker.state.value}")


if __name__ == "__main__":
    asyncio.run(run_circuit_demo())

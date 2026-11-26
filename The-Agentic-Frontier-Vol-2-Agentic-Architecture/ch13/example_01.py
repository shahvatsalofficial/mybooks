# adaptive_circuit_breaker.py
"""
Adaptive Token-Bucket Circuit Breaker for Model API Protection.
Prevents thundering herd cascading failures under 429 rate limit storms.
"""
import time
import asyncio
import logging
from enum import Enum

logger = logging.getLogger("agent-circuit-breaker")

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Healthy: Requests flow through normally
    OPEN = "OPEN"          # Tripped: Requests fail fast or reroute to fallback
    HALF_OPEN = "HALF_OPEN"# Testing: Allowing small probe traffic to verify recovery

class AdaptiveModelCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_time_sec: float = 30.0,
        fallback_model: str = "local-llama-3-8b"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.fallback_model = fallback_model
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_state_change = time.time()

    async def execute(self, model_call_coroutine, fallback_coroutine):
        """Executes model invocation protected by circuit state."""
        current_time = time.time()

        # Check if OPEN circuit should transition to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if current_time - self.last_state_change > self.recovery_time_sec:
                logger.warning("Circuit entering HALF_OPEN probe state...")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = current_time
            else:
                # Fail fast to fallback model
                logger.info(f"Circuit OPEN: Rerouting immediately to {self.fallback_model}")
                return await fallback_coroutine()

        try:
            result = await model_call_coroutine()
            
            # If successful in HALF_OPEN, reset circuit to CLOSED
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Probe succeeded. Resetting circuit to CLOSED.")
                self.state = CircuitState.CLOSED
                self.consecutive_failures = 0
                self.last_state_change = current_time

            return result

        except Exception as e:
            error_str = str(e).lower()
            # Detect rate-limit storms and upstream server collapses
            if "429" in error_str or "rate limit" in error_str or "overloaded" in error_str:
                self.consecutive_failures += 1
                logger.error(
                    f"Upstream model error ({self.consecutive_failures}/{self.failure_threshold}): {e}"
                )

                if self.consecutive_failures >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.last_state_change = current_time
                    logger.critical(
                        f"CIRCUIT TRIPPED TO OPEN! Model provider unreachable/throttled. "
                        f"All traffic diverted to {self.fallback_model} for {self.recovery_time_sec}s."
                    )
            
            # Execute fallback execution immediately
            return await fallback_coroutine()

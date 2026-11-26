"""
Circuit-Breaker Proxy Middleware: Tracks failure frequencies per tool,
tripping to OPEN state when thresholds breach and enabling canary recovery probes.
"""

import time
from typing import Dict, Any, Callable, Tuple


class ToolCircuitBreaker:
    """Enforces circuit breaker state transitions (CLOSED, OPEN, HALF_OPEN) on agent tools."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: float = 60.0):
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_timestamp = 0.0

    def execute_tool_call(
        self,
        tool_fn: Callable[[], Any]
    ) -> Tuple[bool, Any, str]:
        """
        Executes tool if circuit is CLOSED or HALF_OPEN.
        Returns: (success, result, circuit_state)
        """
        now = time.time()

        # Check if OPEN circuit can transition to HALF_OPEN canary probe
        if self.state == "OPEN":
            if now - self.last_failure_timestamp >= self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                return False, {
                    "error": "CIRCUIT_BREAKER_OPEN",
                    "cooldown_remaining": round(self.recovery_timeout - (now - self.last_failure_timestamp), 1)
                }, "OPEN"

        # Attempt invocation
        try:
            result = tool_fn()
            # Success in HALF_OPEN resets circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return True, result, self.state
        except Exception as exc:
            self.failure_count += 1
            self.last_failure_timestamp = now
            if self.failure_count >= self.threshold or self.state == "HALF_OPEN":
                self.state = "OPEN"
            return False, {"error": str(exc)}, self.state

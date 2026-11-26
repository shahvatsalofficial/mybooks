"""
Enterprise Three-State Circuit Breaker
Implements CLOSED, OPEN, and HALF-OPEN state transitions with jittered reset.
Author: Vatsal Shah, Enterprise AI Architect
"""
import time
import random
from enum import Enum
from typing import Callable, Any

class BreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_success_needed: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_success_needed = half_open_success_needed

        self.state = BreakerState.CLOSED
        self.failure_count = 0
        self.consecutive_success_count = 0
        self.last_state_change = time.time()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()

        if self.state == BreakerState.OPEN:
            # Check if recovery timeout has elapsed (with jitter)
            jittered_timeout = self.recovery_timeout_sec + random.uniform(0, 5.0)
            if now - self.last_state_change > jittered_timeout:
                print("⚡ Circuit Breaker transitioning to HALF-OPEN (Canary Probe)")
                self.state = BreakerState.HALF_OPEN
                self.consecutive_success_count = 0
                self.last_state_change = now
            else:
                raise CircuitBreakerOpenException("Circuit Breaker is OPEN. Call rejected.")

        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure(e)
            raise e

    def _handle_success(self):
        if self.state == BreakerState.HALF_OPEN:
            self.consecutive_success_count += 1
            if self.consecutive_success_count >= self.half_open_success_needed:
                print("✅ Circuit Breaker RESET to CLOSED (Primary healthy)")
                self.state = BreakerState.CLOSED
                self.failure_count = 0
                self.last_state_change = time.time()
        elif self.state == BreakerState.CLOSED:
            self.failure_count = 0

    def _handle_failure(self, error: Exception):
        self.failure_count += 1
        now = time.time()
        print(f"⚠️ Execution failure: {error} (Failure count: {self.failure_count})")

        if self.state == BreakerState.HALF_OPEN:
            print("🚨 Canary probe failed! Circuit tripping back to OPEN.")
            self.state = BreakerState.OPEN
            self.last_state_change = now
        elif self.state == BreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            print(f"🚨 Failure threshold ({self.failure_threshold}) exceeded! Circuit TRIPPED to OPEN.")
            self.state = BreakerState.OPEN
            self.last_state_change = now

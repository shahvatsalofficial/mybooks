from dataclasses import dataclass, field
import enum
import time
import random

class CircuitState(enum.Enum):
    CLOSED = "CLOSED"       # Normal operation: Traffic flows freely
    OPEN = "OPEN"           # Tripped: Fast-fail all requests immediately
    HALF_OPEN = "HALF_OPEN" # Canary state: Allow single probe request to test recovery

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_sec: float = 30.0
    consecutive_failures: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_state_change: float = field(default_factory=time.monotonic)

    def record_success(self) -> None:
        self.consecutive_failures = 0
        if self.state != CircuitState.CLOSED:
            logger.info("Circuit breaker recovered: Transitioning to CLOSED.")
            self.state = CircuitState.CLOSED
            self.last_state_change = time.monotonic()

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        now = time.monotonic()
        if self.consecutive_failures >= self.failure_threshold and self.state == CircuitState.CLOSED:
            logger.error(f"Circuit tripped! {self.consecutive_failures} consecutive failures. Entering OPEN state.")
            self.state = CircuitState.OPEN
            self.last_state_change = now

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        now = time.monotonic()
        if self.state == CircuitState.OPEN and (now - self.last_state_change) > self.recovery_timeout_sec:
            logger.info("Recovery timeout elapsed. Testing upstream service: Transitioning to HALF_OPEN.")
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = now
            return True
        return self.state == CircuitState.HALF_OPEN

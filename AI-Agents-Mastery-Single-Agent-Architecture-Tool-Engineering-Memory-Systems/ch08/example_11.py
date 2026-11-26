import time
from typing import Dict, Any, Optional

class GatewayCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time_sec: float = 10.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time_sec
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.consecutive_failures = 0
        self.last_failure_time = 0.0

    def record_call_result(self, success: bool) -> None:
        now = time.time()
        if success:
            if self.state == "HALF-OPEN":
                print("[CIRCUIT BREAKER] Canary probe succeeded! Transitioning to CLOSED.")
                self.state = "CLOSED"
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.last_failure_time = now
            if self.consecutive_failures >= self.failure_threshold:
                print(f"[CIRCUIT BREAKER] Failure threshold ({self.failure_threshold}) exceeded! Tripping to OPEN.")
                self.state = "OPEN"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_time:
                print("[CIRCUIT BREAKER] Recovery window elapsed. Transitioning to HALF-OPEN canary probe.")
                self.state = "HALF-OPEN"
                return True
            return False
        return self.state == "HALF-OPEN"

cb = GatewayCircuitBreaker(failure_threshold=2, recovery_time_sec=1.0)
cb.record_call_result(False)
cb.record_call_result(False)  # Trips breaker
print("Allowed to execute request?", cb.can_execute())

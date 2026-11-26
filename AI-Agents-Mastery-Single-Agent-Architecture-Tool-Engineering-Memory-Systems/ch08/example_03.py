from enum import Enum

class BreakerState(str, Enum):
    CLOSED = "closed"         # Normal operation: requests pass through
    OPEN = "open"             # Outage detected: requests fail immediately
    HALF_OPEN = "half_open"   # Probing: test request sent to check recovery

class ProductionCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 2.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.state = BreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == BreakerState.CLOSED:
            return True
        
        if self.state == BreakerState.OPEN:
            # Check if recovery timeout has elapsed to enter HALF_OPEN
            if (now - self.last_failure_time) >= self.recovery_timeout:
                self.state = BreakerState.HALF_OPEN
                return True
            return False

        if self.state == BreakerState.HALF_OPEN:
            # Allow single probe request
            return True
            
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = BreakerState.CLOSED

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = BreakerState.OPEN

# Verification
breaker = ProductionCircuitBreaker(failure_threshold=2, recovery_timeout_sec=0.1)
print(f"Initial State: {breaker.state.value} | Can Execute: {breaker.can_execute()}")

breaker.record_failure()
breaker.record_failure()
print(f"Post 2 Failures: {breaker.state.value} | Can Execute: {breaker.can_execute()}")

time.sleep(0.15)
print(f"After Timeout: Can Execute (Probe): {breaker.can_execute()} | State: {breaker.state.value}")
breaker.record_success()
print(f"After Probe Success: State: {breaker.state.value}")

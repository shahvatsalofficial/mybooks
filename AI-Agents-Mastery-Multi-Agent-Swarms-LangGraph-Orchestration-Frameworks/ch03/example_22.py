class SubgraphCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 30.0):
        self.threshold = failure_threshold
        self.reset_timeout = reset_timeout_sec
        self.failures = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "OPEN"
            print(f"[CIRCUIT BREAKER] Threshold reached! State is now OPEN. Fast-failing child calls.")

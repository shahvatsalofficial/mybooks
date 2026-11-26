class LeakyTokenBucket:
    def __init__(self, capacity: float, refill_rate_per_sec: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.last_update = time.time()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

    def acquire(self, tokens_requested: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True
        return False

    def wait_and_acquire(self, tokens_requested: float = 1.0, timeout: float = 2.0) -> bool:
        start = time.time()
        while (time.time() - start) < timeout:
            if self.acquire(tokens_requested):
                return True
            time.sleep(0.02)
        return False

# Verification
bucket = LeakyTokenBucket(capacity=5.0, refill_rate_per_sec=2.0)
print("Acquire 3 tokens:", bucket.acquire(3.0))
print("Acquire 3 tokens (should fail):", bucket.acquire(3.0))
print("Waiting to acquire 1 token:", bucket.wait_and_acquire(1.0, timeout=1.0))

class TokenBucketLimiter:
    def __init__(self, capacity: int = 10, refill_rate_per_sec: float = 2.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self, tokens_needed: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.capacity), self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens_needed:
            self.tokens -= tokens_needed
            return True
        print(f"[RATE LIMIT] Token bucket exhausted ({self.tokens:.1f}/{self.capacity} tokens available). Throttling.")
        return False

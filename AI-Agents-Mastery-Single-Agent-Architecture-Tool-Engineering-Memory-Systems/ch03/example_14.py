import time
from typing import Dict

class InMemoryTokenBucketGovernor:
    def __init__(self, capacity: int, fill_rate_per_sec: float):
        self.capacity = capacity
        self.fill_rate = fill_rate_per_sec
        self.tokens = capacity
        self.last_update = time.time()

    def acquire(self, tool_name: str, requested_tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Replenish tokens based on elapsed duration
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

        if self.tokens >= requested_tokens:
            self.tokens -= requested_tokens
            print(f"[RATE GOVERNOR] Tool '{tool_name}' APPROVED ({self.tokens:.1f} tokens remaining)")
            return True
        else:
            print(f"[RATE GOVERNOR] Tool '{tool_name}' THROTTLED! Needs {requested_tokens}, has {self.tokens:.1f}")
            return False

governor = InMemoryTokenBucketGovernor(capacity=5, fill_rate_per_sec=2.0)
governor.acquire("web_search", 3)
governor.acquire("web_search", 3)  # Exceeds current capacity

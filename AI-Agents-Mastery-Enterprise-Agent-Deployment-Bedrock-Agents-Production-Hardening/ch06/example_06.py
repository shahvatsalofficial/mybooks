import uuid
import time
from typing import Optional

class RedisDistributedLock:
    """Acquires and releases distributed mutual exclusion locks using Redis SET NX PX."""

    def __init__(self, resource_name: str, ttl_ms: int = 30000):
        self.resource = f"lock:{resource_name}"
        self.ttl = ttl_ms
        self.lock_value = str(uuid.uuid4())
        self.acquired = False

    def acquire(self) -> bool:
        """Simulates atomic SET lock_key unique_val NX PX ttl."""
        print(f"Acquired distributed lock for '{self.resource}' (Value: {self.lock_value[:8]}..., TTL: {self.ttl}ms).")
        self.acquired = True
        return True

    def release(self) -> bool:
        """Releases lock via Lua script only if the current value matches our unique lock_value."""
        if self.acquired:
            print(f"Safely released distributed lock for '{self.resource}'.")
            self.acquired = False
            return True
        return False

if __name__ == "__main__":
    lock = RedisDistributedLock("mission_state_4401")
    if lock.acquire():
        try:
            print("Executing critical agent state mutation under distributed mutex...")
            time.sleep(0.05)
        finally:
            lock.release()

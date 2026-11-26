import time
import uuid
from typing import Optional

class DistributedSessionLock:
    def __init__(self, resource_id: str, ttl_seconds: float = 10.0):
        self.resource_id = f"lock:agent:session:{resource_id}"
        self.ttl = ttl_seconds
        self.lock_token: Optional[str] = None
        self.simulated_redis_store: dict[str, tuple[str, float]] = {}

    def acquire(self) -> bool:
        token = str(uuid.uuid4())
        now = time.time()
        # Simulated atomic SET NX PX
        if self.resource_id in self.simulated_redis_store:
            existing_token, expiry = self.simulated_redis_store[self.resource_id]
            if now < expiry:
                print(f"[REDLOCK] Lock acquisition FAILED for session '{self.resource_id}' (Held by {existing_token[:8]})")
                return False

        self.simulated_redis_store[self.resource_id] = (token, now + self.ttl)
        self.lock_token = token
        print(f"[REDLOCK] Lock ACQUIRED for session '{self.resource_id}' | Token: {token[:8]} (TTL: {self.ttl}s)")
        return True

    def release(self) -> bool:
        if not self.lock_token:
            return False
        # Simulated Lua script: atomic release only if token matches
        if self.resource_id in self.simulated_redis_store:
            token, _ = self.simulated_redis_store[self.resource_id]
            if token == self.lock_token:
                del self.simulated_redis_store[self.resource_id]
                print(f"[REDLOCK] Lock RELEASED for session '{self.resource_id}'")
                self.lock_token = None
                return True
        return False

lock = DistributedSessionLock("usr_9912_cart")
if lock.acquire():
    # Critical section: Agent reads and mutates state
    time.sleep(0.02)
    lock.release()

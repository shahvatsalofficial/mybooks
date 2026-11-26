import time
import redis
from contextlib import contextmanager

redis_client = redis.Redis(host="localhost", port=6379, db=0)

@contextmanager
def acquire_agent_lock(resource_key: str, lock_timeout_ms: int = 10000, retry_delay_s: float = 0.2):
    """
    Distributed Redis lock semaphore ensuring single-agent access to shared critical resources.
    Prevents race conditions in parallel agent execution squads.
    """
    lock_id = f"lock:{resource_key}"
    acquired = False
    start_time = time.time()
    
    while not acquired:
        # Attempt atomic SETNX with expiration
        acquired = redis_client.set(lock_id, "LOCKED", nx=True, px=lock_timeout_ms)
        if acquired:
            break
        if time.time() - start_time > (lock_timeout_ms / 1000.0):
            raise TimeoutError(f"DEADLOCK_PREVENTION: Could not acquire lock for resource '{resource_key}'.")
        time.sleep(retry_delay_s)
        
    try:
        yield
    finally:
        # Atomic lock release
        redis_client.delete(lock_id)

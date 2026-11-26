import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")

class ResilientHTTPGateway:
    def __init__(self, max_retries: int = 4, base_delay: float = 0.5, max_delay: float = 8.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute_with_jitter(self, request_fn: Callable[[], T]) -> T:
        for attempt in range(self.max_retries + 1):
            try:
                return request_fn()
            except Exception as err:
                if attempt == self.max_retries:
                    raise RuntimeError(f"All {self.max_retries} retry attempts failed: {err}") from err
                
                # Full Jitter Formula: sleep = random_between(0, min(max_delay, base * 2^attempt))
                backoff_limit = min(self.max_delay, self.base_delay * (2 ** attempt))
                sleep_duration = random.uniform(0, backoff_limit)
                
                print(f"[RETRY NOTICE] Attempt {attempt + 1} failed ({err}). Retrying in {sleep_duration:.3f}s with jitter...")
                time.sleep(sleep_duration)

# Verification
call_counter = 0
def flaky_api_call():
    global call_counter
    call_counter += 1
    if call_counter < 3:
        raise ConnectionError("HTTP 429 Too Many Requests: Rate limit exceeded.")
    return {"status": "success", "tokens": 420}

gateway = ResilientHTTPGateway(max_retries=3, base_delay=0.1, max_delay=1.0)
result = gateway.execute_with_jitter(flaky_api_call)
print("Successful Result:", result)

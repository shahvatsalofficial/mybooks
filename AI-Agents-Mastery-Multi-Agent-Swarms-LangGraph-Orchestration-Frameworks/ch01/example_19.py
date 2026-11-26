import random

class AdaptiveBackoffRetry:
    def __init__(self, base_delay: float = 0.5, max_delay: float = 10.0, max_retries: int = 4):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

    def execute_with_jitter(self, operation_fn: Callable[[], Any], operation_name: str) -> Any:
        attempts = 0
        while attempts < self.max_retries:
            try:
                return operation_fn()
            except Exception as exc:
                attempts += 1
                if attempts >= self.max_retries:
                    raise RuntimeError(f"Operation '{operation_name}' failed after {attempts} retries: {exc}")
                # Full jitter formula: sleep = Uniform(0, min(max_delay, base * 2^attempt))
                ceiling = min(self.max_delay, self.base_delay * (2 ** attempts))
                sleep_duration = random.uniform(0, ceiling)
                print(f"[RETRY JITTER] {operation_name} failed ({exc}). Retrying in {sleep_duration:.2f}s (Attempt {attempts}/{self.max_retries})...")
                time.sleep(sleep_duration)

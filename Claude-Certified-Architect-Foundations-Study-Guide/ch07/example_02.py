import json
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable

STATIC_SYSTEM_PROMPT = (
    "You are a support triage classifier. Extract severity, category, "
    "and whether a code fix is required. Return strict JSON only."
)

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay_s: float = 0.01  # Set to 1.0s in production

def call_with_backoff(fn: Callable[[], dict[str, Any]], cfg: RetryConfig) -> dict[str, Any]:
    """Retry transient 429/529 responses with jittered exponential backoff."""
    for attempt in range(cfg.max_retries + 1):
        resp = fn()
        status = resp.get("status", 200)
        if status == 200:
            return resp
        if status not in (429, 529) or attempt == cfg.max_retries:
            raise RuntimeError(f"Unrecoverable API status: {status}")
        retry_after = resp.get("retry_after")
        delay = float(retry_after) if retry_after else (cfg.base_delay_s * (2 ** attempt))
        time.sleep(delay + random.uniform(0, 0.005))
    raise RuntimeError("Exhausted retry budget")

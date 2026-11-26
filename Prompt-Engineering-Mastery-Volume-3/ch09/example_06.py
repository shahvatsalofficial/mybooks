"""
Exponential Backoff with Full Jitter Engine.
Computes mathematically decorrelated sleep intervals to eliminate thundering herd storms.
"""

import random
import time
from typing import Optional


class JitteredBackoffGovernor:
    """Manages decorrelated exponential backoff with full jitter (Amazon Architecture Standard)."""

    def __init__(
        self,
        base_interval_seconds: float = 1.0,
        max_ceiling_seconds: float = 32.0,
        max_retries: int = 4
    ):
        self.base = base_interval_seconds
        self.ceiling = max_ceiling_seconds
        self.max_retries = max_retries

    def calculate_sleep_interval(self, retry_attempt: int) -> float:
        """
        Computes sleep = Uniform(0, min(ceiling, base * 2^attempt)).
        retry_attempt is zero-indexed (0, 1, 2, ...).
        """
        if retry_attempt >= self.max_retries:
            raise RuntimeError(f"Maximum retry limit ({self.max_retries}) exceeded.")

        exponential_window = min(self.ceiling, self.base * (2.0 ** retry_attempt))
        sleep_duration = random.uniform(0.0, exponential_window)
        return round(sleep_duration, 3)

    def execute_sleep(self, retry_attempt: int) -> float:
        """Calculates sleep duration and blocks thread."""
        duration = self.calculate_sleep_interval(retry_attempt)
        time.sleep(duration)
        return duration

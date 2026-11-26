def calculate_full_jitter_delay(attempt: int, base: float = 0.5, cap: float = 60.0) -> float:
    """Calculates backoff duration using the Full Jitter algorithm."""
    ceiling = min(cap, base * (2 ** attempt))
    return random.uniform(0.0, ceiling)

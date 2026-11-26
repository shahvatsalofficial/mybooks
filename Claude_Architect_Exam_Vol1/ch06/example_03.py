def compute_delay(resp: dict[str, Any], attempt: int, base_delay: float, cap_delay: float, rng: random.Random) -> float:
    exp_ceiling = min(cap_delay, base_delay * (2 ** (attempt - 1)))
    jittered = rng.uniform(0.0, exp_ceiling)
    header_wait = float(resp.get("retry_after", 0.0))
    return round(min(cap_delay, max(jittered, header_wait)), 3)

def compute_elo_update(rating_a: float, rating_b: float, score_a: float, k: float = 32) -> Tuple[float, float]:
    expected_a = 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
    expected_b = 1.0 - expected_a
    new_a = rating_a + k * (score_a - expected_a)
    new_b = rating_b + k * ((1.0 - score_a) - expected_b)
    return round(new_a, 1), round(new_b, 1)

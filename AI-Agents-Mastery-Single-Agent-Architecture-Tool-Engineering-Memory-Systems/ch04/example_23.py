import math
import time

def calculate_decayed_score(initial_score: float, creation_timestamp: float, half_life_days: float = 30.0) -> float:
    now = time.time()
    elapsed_days = (now - creation_timestamp) / 86400.0
    decay_constant = math.log(2) / half_life_days
    decay_factor = math.exp(-decay_constant * elapsed_days)
    return round(initial_score * decay_factor, 4)

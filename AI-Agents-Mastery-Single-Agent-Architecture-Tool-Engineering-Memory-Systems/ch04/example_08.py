import math

class TemporalDecayScorer:
    def __init__(self, half_life_days: float = 14.0):
        self.half_life = half_life_days
        self.decay_lambda = math.log(2) / half_life_days

    def score_memory(self, raw_cosine_sim: float, memory_epoch_seconds: float) -> float:
        now = time.time()
        elapsed_days = max(0.0, (now - memory_epoch_seconds) / 86400.0)
        decay_factor = math.exp(-self.decay_lambda * elapsed_days)
        return round(raw_cosine_sim * decay_factor, 4)

# Verification
decay_scorer = TemporalDecayScorer(half_life_days=30.0)
fresh_score = decay_scorer.score_memory(raw_cosine_sim=0.90, memory_epoch_seconds=time.time())
old_score = decay_scorer.score_memory(raw_cosine_sim=0.90, memory_epoch_seconds=time.time() - (60 * 86400))
print(f"Fresh Memory (Today) Score: {fresh_score} | 60-Day Old Memory Score: {old_score}")

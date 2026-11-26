# finops_anomaly_detector.py — Machine Learning Cost Spike Detector
import numpy as np
from typing import List, Dict, Any

class FinOpsAnomalyDetector:
    def __init__(self, alpha: float = 0.2, beta: float = 0.1, gamma: float = 0.3, season_len: int = 96):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.season_len = season_len
        self.level = 0.0
        self.trend = 0.0
        self.seasonals = np.ones(season_len)
        self.residuals: List[float] = []

    def evaluate_consumption(self, current_period_tokens: float, period_idx: int) -> Dict[str, Any]:
        season_idx = period_idx % self.season_len
        expected = (self.level + self.trend) * self.seasonals[season_idx]
        residual = abs(current_period_tokens - expected)
        self.residuals.append(residual)

        # Calculate dynamic threshold based on recent residual standard deviation
        sigma = np.std(self.residuals[-48:]) if len(self.residuals) >= 48 else 1000.0
        is_anomaly = (current_period_tokens - expected) > (3.5 * sigma)

        # Update Holt-Winters State
        last_level = self.level
        self.level = self.alpha * (current_period_tokens / self.seasonals[season_idx]) + (1 - self.alpha) * (self.level + self.trend)
        self.trend = self.beta * (self.level - last_level) + (1 - self.beta) * self.trend
        self.seasonals[season_idx] = self.gamma * (current_period_tokens / self.level) + (1 - self.gamma) * self.seasonals[season_idx]

        return {
            "is_anomaly": bool(is_anomaly),
            "current_tokens": current_period_tokens,
            "expected_baseline": round(expected, 2),
            "divergence_sigma": round(residual / max(1.0, sigma), 2),
            "action": "TRIGGER_CIRCUIT_THROTTLE" if is_anomaly else "NORMAL"
        }

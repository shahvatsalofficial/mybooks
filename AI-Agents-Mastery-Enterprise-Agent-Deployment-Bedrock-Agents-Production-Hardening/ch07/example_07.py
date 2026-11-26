import numpy as np
from typing import Dict, Any, List

class TokenAnomalyDetector:
    """Detects statistical outliers in agent token consumption to prevent denial-of-wallet loops."""

    def __init__(self, z_threshold: float = 3.0, window_size: int = 50):
        self.z_threshold = z_threshold
        self.window_size = window_size
        self.history: List[int] = [1200, 1400, 1100, 1350, 1500, 1250, 1300] * 5

    def evaluate_consumption(self, session_id: str, tokens_consumed: int) -> Dict[str, Any]:
        mean = float(np.mean(self.history))
        std = float(np.std(self.history))
        
        z_score = (tokens_consumed - mean) / std if std > 0 else 0.0
        is_anomaly = z_score > self.z_threshold
        
        if not is_anomaly:
            self.history.append(tokens_consumed)
            if len(self.history) > self.window_size:
                self.history.pop(0)

        return {
            "session_id": session_id,
            "tokens": tokens_consumed,
            "mean": round(mean, 1),
            "z_score": round(z_score, 2),
            "is_anomaly": is_anomaly,
            "action": "THROTTLE_AND_TERMINATE_SESSION" if is_anomaly else "NORMAL"
        }

if __name__ == '__main__':
    detector = TokenAnomalyDetector()
    print("Normal turn check:", detector.evaluate_consumption("sess-01", 1450)["action"])
    runaway = detector.evaluate_consumption("sess-runaway-99", 28000)
    print(f"Runaway turn check (Z={runaway['z_score']}):", runaway["action"])

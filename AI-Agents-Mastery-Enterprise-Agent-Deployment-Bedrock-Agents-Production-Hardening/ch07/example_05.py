import numpy as np
from typing import List, Dict, Any

class SemanticDriftDetector:
    """Monitors vector retrieval similarity distributions for statistical drift."""

    def __init__(self, baseline_mean_similarity: float = 0.88, drift_threshold: float = 0.12):
        self.baseline_mean = baseline_mean_similarity
        self.drift_threshold = drift_threshold
        self.recent_similarity_scores: List[float] = []

    def record_retrieval_event(self, similarity_scores: List[float]) -> None:
        if similarity_scores:
            self.recent_similarity_scores.append(float(np.mean(similarity_scores)))
            if len(self.recent_similarity_scores) > 100:
                self.recent_similarity_scores.pop(0)

    def check_drift(self) -> Dict[str, Any]:
        if len(self.recent_similarity_scores) < 10:
            return {"status": "INSUFFICIENT_DATA"}
            
        current_mean = float(np.mean(self.recent_similarity_scores))
        drift_delta = self.baseline_mean - current_mean
        is_drifting = drift_delta > self.drift_threshold
        
        return {
            "status": "DRIFT_DETECTED" if is_drifting else "HEALTHY",
            "baseline_mean": round(self.baseline_mean, 3),
            "current_mean": round(current_mean, 3),
            "drift_delta": round(drift_delta, 3),
            "action_required": "Re-index vector database and regenerate embeddings" if is_drifting else "None"
        }

if __name__ == "__main__":
    detector = SemanticDriftDetector(baseline_mean_similarity=0.88, drift_threshold=0.10)
    
    # Simulate healthy retrievals
    for _ in range(15):
        detector.record_retrieval_event([0.89, 0.87, 0.91])
    print("Healthy check:", detector.check_drift()["status"])
    
    # Simulate degraded retrieval due to schema drift
    for _ in range(25):
        detector.record_retrieval_event([0.62, 0.65, 0.59])
    degraded = detector.check_drift()
    print("Degraded check:", degraded["status"], f"(Current Mean: {degraded['current_mean']}, Delta: {degraded['drift_delta']})")

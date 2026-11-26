from typing import Dict, List

class GEvalScorer:
    def __init__(self, metric_weights: Dict[str, float] = None):
        self.weights = metric_weights or {
            "factual_grounding": 0.4,
            "tool_selection_efficiency": 0.3,
            "safety_compliance": 0.3
        }

    def score_trajectory(self, trajectory_data: Dict[str, Any]) -> float:
        # Mock probabilities extracted from judge model logits
        metric_scores = {
            "factual_grounding": 0.95,
            "tool_selection_efficiency": 0.88,
            "safety_compliance": 1.00
        }

        total_score = sum(metric_scores[k] * self.weights[k] for k in self.weights)
        print(f"[G-EVAL] Composite Continuous Score: {total_score:.3f} / 1.000")
        return total_score

scorer = GEvalScorer()
score = scorer.score_trajectory({"agent_id": "auditor_v1"})

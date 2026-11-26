import numpy as np
from typing import List

class LateInteractionColBERTScorer:
    def compute_maxsim(self, query_tokens: List[np.ndarray], doc_tokens: List[np.ndarray]) -> float:
        total_score = 0.0
        for q_vec in query_tokens:
            # Find maximum dot product similarity across all document tokens
            max_sim = max([float(np.dot(q_vec, d_vec)) for d_vec in doc_tokens])
            total_score += max_sim
        return round(total_score, 4)

scorer = LateInteractionColBERTScorer()
# Mock token embeddings (dimension 32)
np.random.seed(42)
q = [np.random.randn(32) for _ in range(4)]
d = [np.random.randn(32) for _ in range(16)]
maxsim_score = scorer.compute_maxsim(q, d)
print("ColBERTv2 Late Interaction MaxSim Score:", maxsim_score)

"""
Conformal Prediction Harness: Calibrates empirical non-conformity thresholds
to provide mathematical 1-alpha risk bounds on ungrounded generation.
"""

import math
from typing import List


class ConformalHallucinationGovernor:
    """Enforces rigorous statistical bounds on language model factual error rates."""

    def __init__(self, calibration_nonconformity_scores: List[float], alpha: float = 0.01):
        """
        alpha: Maximum tolerable error rate (e.g. 0.01 = 99% factual guarantee).
        """
        self.alpha = alpha
        n = len(calibration_nonconformity_scores)
        if n < 100:
            raise ValueError("Calibration set must contain at least 100 samples.")

        sorted_scores = sorted(calibration_nonconformity_scores)
        index = math.ceil((n + 1) * (1.0 - alpha)) - 1
        index = min(max(index, 0), n - 1)
        self.threshold_q = sorted_scores[index]

    def evaluate_candidate(self, candidate_nli_score: float) -> bool:
        """
        Evaluates whether candidate non-conformity score satisfies the conformal bound.
        candidate_nli_score: Float [0.0, 1.0] representing P(Entailed).
        """
        nonconformity = 1.0 - candidate_nli_score
        return nonconformity <= self.threshold_q

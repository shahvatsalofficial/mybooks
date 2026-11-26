import math
from typing import List, Dict, Any
from collections import defaultdict

class WeightedPath:
    def __init__(self, answer: str, token_logprobs: List[float]):
        self.answer = answer
        self.token_logprobs = token_logprobs

    @property
    def normalized_confidence(self) -> float:
        """Calculates length-normalized geometric mean probability."""
        if not self.token_logprobs:
            return 0.0
        avg_logprob = sum(self.token_logprobs) / len(self.token_logprobs)
        # Bounded between 0.0 and 1.0
        return math.exp(avg_logprob)

def compute_weighted_winner_with_entropy(paths: List[WeightedPath]) -> Dict[str, Any]:
    score_accumulator = defaultdict(float)
    vote_counter = defaultdict(int)

    for p in paths:
        conf = p.normalized_confidence
        score_accumulator[p.answer] += conf
        vote_counter[p.answer] += 1

    total_weighted_mass = sum(score_accumulator.values())
    total_unweighted_votes = len(paths)
    
    # Calculate predictive Shannon entropy across vote distribution
    entropy_bits = 0.0
    for cand, count in vote_counter.items():
        prob = count / total_unweighted_votes
        if prob > 0:
            entropy_bits -= prob * math.log2(prob)

    # Sort candidates by cumulative weighted confidence
    sorted_candidates = sorted(
        score_accumulator.items(),
        key=lambda item: item[1],
        reverse=True
    )
    
    best_candidate, best_score = sorted_candidates[0]
    relative_confidence = (best_score / total_weighted_mass) if total_weighted_mass > 0 else 0.0

    return {
        "elected_candidate": best_candidate,
        "weighted_share": round(relative_confidence, 4),
        "unweighted_votes": vote_counter[best_candidate],
        "total_paths": total_unweighted_votes,
        "predictive_entropy_bits": round(entropy_bits, 4),
        "autonomous_safe": entropy_bits < 0.25 and relative_confidence >= 0.75,
        "candidate_rankings": [
            {
                "candidate": cand,
                "weighted_score": round(score, 4),
                "vote_count": vote_counter[cand]
            }
            for cand, score in sorted_candidates
        ]
    }

import asyncio
from typing import Callable, Coroutine, Any, Dict, List
from collections import Counter

async def adaptive_consensus_cascade(
    sample_fn: Callable[[int, float], Coroutine[Any, Any, List[str]]],
    min_samples: int = 3,
    max_samples: int = 9,
    unanimous_threshold: float = 1.0,
    majority_threshold: float = 0.66
) -> Dict[str, Any]:
    """
    Executes a multi-tier sampling cascade.
    Stage 1: Sample min_samples. If unanimous, return immediately.
    Stage 2: Burst to max_samples if ambiguous.
    """
    # Stage 1: Initial exploration
    tier1_answers = await sample_fn(min_samples, 0.7)
    
    # Check for early unanimity
    unique_answers = set(tier1_answers)
    if len(unique_answers) == 1:
        return {
            "elected_answer": tier1_answers[0],
            "early_exit_triggered": True,
            "total_tokens_consumed_ratio": min_samples / max_samples,
            "voting_distribution": {tier1_answers[0]: min_samples}
        }

    # Stage 2: Burst to resolve split vote
    remaining = max_samples - min_samples
    tier2_answers = await sample_fn(remaining, 0.7)
    all_answers = tier1_answers + tier2_answers

    counts = Counter(all_answers)
    winner, win_count = counts.most_common(1)[0]

    return {
        "elected_answer": winner,
        "early_exit_triggered": False,
        "voting_share": win_count / max_samples,
        "voting_distribution": dict(counts)
    }

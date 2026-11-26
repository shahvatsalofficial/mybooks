"""
Graceful Degradation Strategy Runner.
Orchestrates hierarchical multi-tier fallbacks across live, cached, and heuristic tools.
"""

from typing import List, Dict, Any, Callable, Tuple


class DegradationStrategyRunner:
    """Executes cascading tool fallbacks when primary services degrade."""

    def __init__(self, fallback_tiers: List[Dict[str, Any]]):
        self.tiers = fallback_tiers

    def execute_with_fallback(self, request_payload: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """
        Iterates through tiers sequentially until a handler succeeds.
        Returns: (success, result_payload, active_tier_name)
        """
        collected_errors = []

        for tier in self.tiers:
            tier_name = tier["tier_name"]
            handler = tier["handler"]

            try:
                result = handler(request_payload)
                return True, result, tier_name
            except Exception as exc:
                collected_errors.append(f"{tier_name} FAILED: {str(exc)}")
                continue

        return False, {"errors": collected_errors}, "ALL_TIERS_EXHAUSTED"

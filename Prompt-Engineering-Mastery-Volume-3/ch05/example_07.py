"""
Multi-Agent Consensus Adjudicator: Resolves conflicting domain evaluations
across specialized worker agents using confidence-weighted voting and arbitration.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class AgentProposal:
    agent_id: str
    proposed_decision: str
    confidence_score: float  # [0.0, 1.0]
    rationale: str
    domain_priority: int  # 1 = Highest (Compliance), 5 = Lowest (Cost)


class ConsensusAdjudicator:
    """Resolves divergent decisions across multi-agent deliberations."""

    QUORUM_THRESHOLD = 0.65

    def resolve_consensus(
        self,
        proposals: List[AgentProposal]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluates proposals using priority-weighted voting and dialectical arbitration.
        Returns: (final_decision, resolution_metadata)
        """
        if not proposals:
            raise ValueError("Cannot resolve consensus over empty proposal set.")

        # Check for High-Priority Veto (Priority 1: Safety/Compliance)
        for p in proposals:
            if p.domain_priority == 1 and p.confidence_score >= 0.85:
                if "REJECT" in p.proposed_decision.upper() or "VETO" in p.proposed_decision.upper():
                    return p.proposed_decision, {
                        "resolution_method": "PRIORITY_VETO",
                        "arbiter_agent": p.agent_id,
                        "rationale": p.rationale
                    }

        # Calculate Confidence-Weighted Score
        decision_weights: Dict[str, float] = {}
        total_weight = 0.0

        for p in proposals:
            weight = p.confidence_score * (6 - p.domain_priority)
            decision_weights[p.proposed_decision] = decision_weights.get(p.proposed_decision, 0.0) + weight
            total_weight += weight

        best_decision = max(decision_weights.items(), key=lambda x: x[1])
        normalized_confidence = best_decision[1] / total_weight if total_weight > 0 else 0.0

        if normalized_confidence >= self.QUORUM_THRESHOLD:
            return best_decision[0], {
                "resolution_method": "CONFIDENCE_WEIGHTED_MAJORITY",
                "confidence": normalized_confidence,
                "breakdown": decision_weights
            }
        else:
            return "ESCALATE_TO_HUMAN", {
                "resolution_method": "QUORUM_FAILURE",
                "top_candidate": best_decision[0],
                "confidence": normalized_confidence,
                "reason": "Agent proposals are split below quorum threshold."
            }

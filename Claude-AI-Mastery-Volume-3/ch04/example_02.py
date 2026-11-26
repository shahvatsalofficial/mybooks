"""
Recipe 04.2: Production Multi-Model Consensus Voting & Quorum Arbiter.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import nacl.signing
import nacl.encoding

logger = logging.getLogger("ConsensusQuorumSwarm")
logger.setLevel(logging.INFO)


class AgentVoteResult(BaseModel):
    agent_id: str
    model_name: str
    vote: str = Field(..., pattern="^(APPROVE|REJECT|ESCALATE)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    latency_ms: float


class SwarmConsensusResult(BaseModel):
    decision: str
    aggregate_confidence: float
    quorum_percentage: float
    participating_votes: List[AgentVoteResult]
    is_supermajority: bool
    ed25519_signature: Optional[str] = None
    audit_timestamp: str


class MultiModelConsensusArbiter:
    """
    Orchestrates parallel blind voting across heterogeneous Claude models.
    Enforces supermajority quorums and generates cryptographically signed proofs.
    """

    def __init__(self, private_signing_key_hex: Optional[str] = None):
        # Initialize Ed25519 cryptographic signing key for non-repudiation
        if private_signing_key_hex:
            self.signing_key = nacl.signing.SigningKey(private_signing_key_hex, encoder=nacl.encoding.HexEncoder)
        else:
            self.signing_key = nacl.signing.SigningKey.generate()
        self.verify_key = self.signing_key.verify_key

    async def _evaluate_reviewer_a(self, payload: Dict[str, Any]) -> AgentVoteResult:
        """Reviewer A: Claude 3.5 Sonnet (AML & Sanctions Expert)."""
        t0 = time.time()
        await asyncio.sleep(0.180) # Simulated inference latency
        return AgentVoteResult(
            agent_id="agent_aml_sonnet",
            model_name="claude-3-5-sonnet@v2",
            vote="APPROVE",
            confidence=0.96,
            reasoning="Beneficiary account passes all OFAC sanctions checks. Zero PEP matches.",
            latency_ms=(time.time() - t0) * 1000
        )

    async def _evaluate_reviewer_b(self, payload: Dict[str, Any]) -> AgentVoteResult:
        """Reviewer B: Claude 3.5 Haiku (Velocity & Volume Expert)."""
        t0 = time.time()
        await asyncio.sleep(0.095) # Ultra-fast inference latency
        return AgentVoteResult(
            agent_id="agent_velocity_haiku",
            model_name="claude-3-5-haiku@v1",
            vote="APPROVE",
            confidence=0.92,
            reasoning="Daily transfer volume within 1.2 standard deviations of 90-day baseline.",
            latency_ms=(time.time() - t0) * 1000
        )

    async def _evaluate_reviewer_c(self, payload: Dict[str, Any]) -> AgentVoteResult:
        """Reviewer C: Claude 3 Opus (Constitutional & Corporate Charter Expert)."""
        t0 = time.time()
        await asyncio.sleep(0.310) # Deep reasoning latency
        return AgentVoteResult(
            agent_id="agent_legal_opus",
            model_name="claude-3-opus@v1",
            vote="APPROVE",
            confidence=0.98,
            reasoning="Dual executive signing thresholds verified against registered corporate bylaws.",
            latency_ms=(time.time() - t0) * 1000
        )

    async def evaluate_transaction_swarm(
        self,
        transaction_payload: Dict[str, Any],
        minimum_quorum: float = 0.667,
        confidence_threshold: float = 0.90
    ) -> SwarmConsensusResult:
        """
        Executes parallel blind voting, evaluates weighted quorum, and signs approval proof.
        """
        logger.info(f"Fanning out swarm review for TX: {transaction_payload.get('tx_id')}")

        # Fan-out parallel evaluation tasks
        tasks = [
            self._evaluate_reviewer_a(transaction_payload),
            self._evaluate_reviewer_b(transaction_payload),
            self._evaluate_reviewer_c(transaction_payload),
        ]
        votes: List[AgentVoteResult] = await asyncio.gather(*tasks)

        # Model weights: Sonnet=1.0, Haiku=0.7, Opus=1.3
        weights = {"agent_aml_sonnet": 1.0, "agent_velocity_haiku": 0.7, "agent_legal_opus": 1.3}
        total_weight = sum(weights.values())

        approve_weight = sum(weights[v.agent_id] for v in votes if v.vote == "APPROVE")
        weighted_confidence_sum = sum(weights[v.agent_id] * v.confidence for v in votes if v.vote == "APPROVE")

        quorum_pct = approve_weight / total_weight
        agg_confidence = weighted_confidence_sum / approve_weight if approve_weight > 0 else 0.0

        is_supermajority = quorum_pct >= minimum_quorum
        passed = is_supermajority and (agg_confidence >= confidence_threshold)
        final_decision = "APPROVE" if passed else "ESCALATE_TO_HUMAN"

        # Generate cryptographic proof if approved
        signature_hex = None
        if final_decision == "APPROVE":
            proof_data = json.dumps({
                "tx_id": transaction_payload.get("tx_id"),
                "decision": final_decision,
                "confidence": round(agg_confidence, 4),
                "timestamp": time.time()
            }, sort_keys=True).encode("utf-8")
            
            signed_block = self.signing_key.sign(proof_data)
            signature_hex = signed_block.signature.hex()
            logger.info(f"Transaction APPROVED with Ed25519 Proof: {signature_hex[:16]}...")

        return SwarmConsensusResult(
            decision=final_decision,
            aggregate_confidence=round(agg_confidence, 4),
            quorum_percentage=round(quorum_pct, 4),
            participating_votes=votes,
            is_supermajority=is_supermajority,
            ed25519_signature=signature_hex,
            audit_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )

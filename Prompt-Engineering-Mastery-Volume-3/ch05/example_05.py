"""
Hierarchical Multi-Agent Supervisor Orchestrator.
Decomposes complex objectives, dispatches typed handoffs to specialized worker agents,
and aggregates distributed results within strict recursion ceilings.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class HandoffPacket:
    correlation_id: str
    delegation_depth: int
    sender_id: str
    target_id: str
    objective: str
    payload: Dict[str, Any]
    expected_schema: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({
            "correlation_id": self.correlation_id,
            "delegation_depth": self.delegation_depth,
            "sender_id": self.sender_id,
            "target_id": self.target_id,
            "objective": self.objective,
            "payload": self.payload,
            "expected_schema": self.expected_schema
        }, indent=2)


class BaseWorkerAgent:
    """Abstract interface for domain-specialized worker agents."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def execute_handoff(self, packet: HandoffPacket) -> Dict[str, Any]:
        raise NotImplementedError


class SupervisorOrchestrator:
    """Root supervisor coordinating subagent delegation with depth clamping."""

    MAX_DELEGATION_DEPTH = 3

    def __init__(self):
        self.worker_registry: Dict[str, BaseWorkerAgent] = {}
        self.execution_audit_log: List[Dict[str, Any]] = []

    def register_worker(self, worker: BaseWorkerAgent):
        self.worker_registry[worker.agent_id] = worker

    def dispatch_delegation(
        self,
        sender_id: str,
        target_worker_id: str,
        objective: str,
        payload: Dict[str, Any],
        expected_schema: Dict[str, Any],
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """Dispatches typed handoff packet to target worker with invariant checks."""
        if current_depth >= self.MAX_DELEGATION_DEPTH:
            raise RecursionError(
                f"Delegation depth limit reached ({self.MAX_DELEGATION_DEPTH}). "
                f"Cannot delegate from '{sender_id}' to '{target_worker_id}'."
            )

        if target_worker_id not in self.worker_registry:
            raise KeyError(f"Target worker '{target_worker_id}' not found in registry.")

        correlation_id = str(uuid.uuid4())
        packet = HandoffPacket(
            correlation_id=correlation_id,
            delegation_depth=current_depth + 1,
            sender_id=sender_id,
            target_id=target_worker_id,
            objective=objective,
            payload=payload,
            expected_schema=expected_schema
        )

        self.execution_audit_log.append({
            "event": "HANDOFF_DISPATCHED",
            "packet": packet.__dict__
        })

        target_agent = self.worker_registry[target_worker_id]
        raw_result = target_agent.execute_handoff(packet)

        self.execution_audit_log.append({
            "event": "HANDOFF_COMPLETED",
            "correlation_id": correlation_id,
            "result_status": "SUCCESS"
        })

        return raw_result

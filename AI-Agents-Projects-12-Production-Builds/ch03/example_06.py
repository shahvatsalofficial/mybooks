from __future__ import annotations

import asyncio
from typing import Dict, List, Protocol
from pydantic import BaseModel, Field


class AgentActionLog(BaseModel):
    agent_name: str
    tool_invoked: str
    outcome: str
    duration_ms: float


class SwarmExecutionResult(BaseModel):
    ticket_id: str
    resolved_by_agent: bool
    final_agent: str
    hops_used: int
    escalate_to_human: bool
    escalation_reason: str = ""
    draft_response: str
    action_logs: List[AgentActionLog] = Field(default_factory=list)


class SpecialistAgent(Protocol):
    name: str

    async def handle(self, ticket_id: str, body: str) -> tuple[bool, str, str, AgentActionLog]:
        ...


class TechOpsSpecialist:
    name = "tech_ops_specialist"

    async def handle(self, ticket_id: str, body: str) -> tuple[bool, str, str, AgentActionLog]:
        await asyncio.sleep(0.02)
        log = AgentActionLog(
            agent_name=self.name,
            tool_invoked="query_service_health(service='payouts-api')",
            outcome="CONFIRMED_REGIONAL_DEGRADATION_EU_WEST_1",
            duration_ms=21.4,
        )
        return (
            False,
            "human_oncall",
            "Confirmed active eu-west-1 gateway degradation affecting /v2/payouts. Escalating to incident commander.",
            log,
        )


class BillingSpecialist:
    name = "billing_specialist"

    async def handle(self, ticket_id: str, body: str) -> tuple[bool, str, str, AgentActionLog]:
        await asyncio.sleep(0.015)
        log = AgentActionLog(
            agent_name=self.name,
            tool_invoked="fetch_invoice_ledger(limit=3)",
            outcome="INVOICE_VERIFIED_ELIGIBLE",
            duration_ms=15.8,
        )
        return (
            True,
            "resolved",
            "Verified invoice #INV-2026-8841 and queued eligible credit within tenant policy cap.",
            log,
        )


class SecuritySpecialist:
    name = "security_specialist"

    async def handle(self, ticket_id: str, body: str) -> tuple[bool, str, str, AgentActionLog]:
        await asyncio.sleep(0.01)
        log = AgentActionLog(
            agent_name=self.name,
            tool_invoked="revoke_exposed_api_key_dry_run()",
            outcome="REQUIRES_SOC_ANALYST_SIGN_OFF",
            duration_ms=11.2,
        )
        return (
            False,
            "human_soc",
            "Potential credential exposure detected. Suspended automated replies and paged SOC analyst.",
            log,
        )


class SwarmOrchestrator:
    """Routes tickets across least-privilege specialist agents with a strict hop budget."""

    def __init__(self, max_hops: int = 3) -> None:
        self._max_hops = max_hops
        self._agents: Dict[str, SpecialistAgent] = {
            "tech_ops": TechOpsSpecialist(),
            "billing": BillingSpecialist(),
            "security": SecuritySpecialist(),
        }

    async def dispatch(self, ticket_id: str, initial_domain: str, body: str) -> SwarmExecutionResult:
        current_domain = initial_domain
        logs: List[AgentActionLog] = []
        hops = 0

        while hops < self._max_hops:
            hops += 1
            agent = self._agents.get(current_domain)
            if agent is None:
                return SwarmExecutionResult(
                    ticket_id=ticket_id,
                    resolved_by_agent=False,
                    final_agent="router",
                    hops_used=hops,
                    escalate_to_human=True,
                    escalation_reason=f"Unknown domain '{current_domain}'",
                    draft_response="",
                    action_logs=logs,
                )

            resolved, next_target, draft, log = await agent.handle(ticket_id, body)
            logs.append(log)

            if resolved:
                return SwarmExecutionResult(
                    ticket_id=ticket_id,
                    resolved_by_agent=True,
                    final_agent=agent.name,
                    hops_used=hops,
                    escalate_to_human=False,
                    draft_response=draft,
                    action_logs=logs,
                )
            if next_target.startswith("human_"):
                return SwarmExecutionResult(
                    ticket_id=ticket_id,
                    resolved_by_agent=False,
                    final_agent=agent.name,
                    hops_used=hops,
                    escalate_to_human=True,
                    escalation_reason=f"Specialist requested {next_target}",
                    draft_response=draft,
                    action_logs=logs,
                )
            current_domain = next_target

        return SwarmExecutionResult(
            ticket_id=ticket_id,
            resolved_by_agent=False,
            final_agent=current_domain,
            hops_used=hops,
            escalate_to_human=True,
            escalation_reason="Max swarm hop budget exhausted",
            draft_response="",
            action_logs=logs,
        )


async def main() -> None:
    orchestrator = SwarmOrchestrator(max_hops=3)
    res = await orchestrator.dispatch(
        "TKT-A49E1C7B2D",
        "tech_ops",
        "Production payouts are failing with 502s since 06:40 UTC.",
    )
    print(res.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())

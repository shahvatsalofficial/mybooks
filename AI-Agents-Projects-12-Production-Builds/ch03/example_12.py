from __future__ import annotations

from typing import List
from pydantic import BaseModel


class EscalationHandoffPacket(BaseModel):
    ticket_id: str
    tenant_name: str
    tier: str
    severity: str
    remaining_sla_minutes: float
    linked_channels: List[str]
    summary: str
    completed_checks: List[str]
    recommended_action: str


class HandoffPacketBuilder:
    """Assembles zero-context-loss escalation packets for human specialists."""

    @staticmethod
    def build(
        ticket_id: str,
        tenant_name: str,
        tier: str,
        severity: str,
        remaining_sla_minutes: float,
        linked_channels: List[str],
        symptom_summary: str,
        action_logs: List[dict],
        recommended_action: str,
    ) -> EscalationHandoffPacket:
        checks = [
            f"{log['agent_name']} -> {log['tool_invoked']} = {log['outcome']}"
            for log in action_logs
        ]
        return EscalationHandoffPacket(
            ticket_id=ticket_id,
            tenant_name=tenant_name,
            tier=tier,
            severity=severity,
            remaining_sla_minutes=remaining_sla_minutes,
            linked_channels=linked_channels,
            summary=symptom_summary,
            completed_checks=checks,
            recommended_action=recommended_action,
        )


if __name__ == "__main__":
    packet = HandoffPacketBuilder.build(
        ticket_id="TKT-A49E1C7B2D",
        tenant_name="Acme Fintech Corp",
        tier="enterprise",
        severity="P1",
        remaining_sla_minutes=3.0,
        linked_channels=["zendesk", "slack"],
        symptom_summary="Enterprise tenant experiencing 502 errors on /v2/payouts since 06:40 UTC.",
        action_logs=[
            {
                "agent_name": "tech_ops_specialist",
                "tool_invoked": "query_service_health('payouts-api')",
                "outcome": "CONFIRMED_REGIONAL_DEGRADATION_EU_WEST_1",
            }
        ],
        recommended_action="Join #inc-eu-west-payouts and post tenant status update.",
    )
    print(packet.model_dump_json(indent=2))

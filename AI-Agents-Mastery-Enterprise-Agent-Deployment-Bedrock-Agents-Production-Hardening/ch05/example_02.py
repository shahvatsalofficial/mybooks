import json
from typing import Dict, Any

class SlackApprovalCardBuilder:
    """Constructs interactive Slack Block Kit payloads for agent mutation approvals."""

    @staticmethod
    def build_card(
        incident_id: str,
        thread_id: str,
        agent_name: str,
        target_resource: str,
        proposed_action: str,
        risk_level: str = "HIGH"
    ) -> Dict[str, Any]:
        color = "#EF4444" if risk_level == "CRITICAL" else "#F59E0B"
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"⚠️ Agent Action Approval Required [{risk_level}]"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident_id}`"},
                    {"type": "mrkdwn", "text": f"*Agent:*\n{agent_name}"},
                    {"type": "mrkdwn", "text": f"*Target Resource:*\n`{target_resource}`"},
                    {"type": "mrkdwn", "text": f"*Risk Level:*\n*{risk_level}*"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Proposed Mutation Plan:*\n```{proposed_action}```"}
            },
            {
                "type": "actions",
                "block_id": f"approval_actions_{thread_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve & Execute"},
                        "style": "primary",
                        "value": json.dumps({"action": "APPROVE", "thread_id": thread_id, "incident_id": incident_id}),
                        "action_id": "btn_approve_action"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject Action"},
                        "style": "danger",
                        "value": json.dumps({"action": "REJECT", "thread_id": thread_id, "incident_id": incident_id}),
                        "action_id": "btn_reject_action"
                    }
                ]
            }
        ]
        
        return {"blocks": blocks}

if __name__ == "__main__":
    card = SlackApprovalCardBuilder.build_card(
        incident_id="INC-88910",
        thread_id="th_9921_k8s",
        agent_name="AutonomousSREAgent",
        target_resource="k8s://prod-east/orders-db-replica-3",
        proposed_action="pg_ctl restart -m fast -D /var/lib/postgresql/data",
        risk_level="CRITICAL"
    )
    print("Generated Slack Block Kit JSON (Total Blocks:", len(card["blocks"]), ")")
    print(json.dumps(card, indent=2)[:400] + "\n...")

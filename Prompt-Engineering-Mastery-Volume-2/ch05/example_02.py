from enum import Enum
from typing import Dict, Any

class TicketIntent(str, Enum):
    BILLING_DISPUTE = "BILLING_DISPUTE"
    TECHNICAL_BUG = "TECHNICAL_BUG"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"

class SemanticRouterPipeline:
    def __init__(self, client: Anthropic):
        self.client = client

    def route_intent(self, text: str) -> TicketIntent:
        system_prompt = (
            "You are a High-Speed Semantic Classifier. Classify incoming customer messages into exactly one category: "
            "BILLING_DISPUTE, TECHNICAL_BUG, SECURITY_INCIDENT, or GENERAL_INQUIRY. "
            "Output ONLY the category name. Zero punctuation or preamble."
        )
        res = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=20,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": text}]
        )
        raw_intent = res.content[0].text.strip()
        try:
            return TicketIntent(raw_intent)
        except ValueError:
            return TicketIntent.GENERAL_INQUIRY

    def dispatch(self, raw_ticket: str) -> Dict[str, Any]:
        intent = self.route_intent(raw_ticket)
        
        # Branching execution
        if intent == TicketIntent.SECURITY_INCIDENT:
            return self._execute_security_subchain(raw_ticket)
        elif intent == TicketIntent.BILLING_DISPUTE:
            return self._execute_billing_subchain(raw_ticket)
        else:
            return self._execute_standard_subchain(raw_ticket)

    def _execute_security_subchain(self, text: str) -> Dict[str, Any]:
        return {"action": "PAGERDUTY_ALERT", "tier": "SEV-1", "payload": text}

    def _execute_billing_subchain(self, text: str) -> Dict[str, Any]:
        return {"action": "STRIPE_RECONCILIATION", "tier": "FINANCE", "payload": text}

    def _execute_standard_subchain(self, text: str) -> Dict[str, Any]:
        return {"action": "KNOWLEDGE_BASE_REPLY", "tier": "TIER-1", "payload": text}

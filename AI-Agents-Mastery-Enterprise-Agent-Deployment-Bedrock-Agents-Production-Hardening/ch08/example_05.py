from typing import Dict, Any

class EnterpriseGovernanceOrchestrator:
    """Central gateway enforcing PII redaction, OPA policy checks, and WORM audit logging."""

    def __init__(self, pii_engine: PresidioPIISanitizationEngine, pdp: OPAPolicyDecisionPoint, logger: WORMComplianceLogger):
        self.pii = pii_engine
        self.pdp = pdp
        self.logger = logger

    def process_agent_turn(
        self,
        user_id: str,
        user_role: str,
        environment: str,
        raw_user_input: str,
        proposed_tool: str,
        tool_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Step 1: PII Sanitization
        pii_result = self.pii.sanitize_text(raw_user_input)
        
        # Step 2: Policy Evaluation (OPA)
        policy_allowed, reason = self.pdp.evaluate_tool_policy(user_role, environment, proposed_tool, tool_params)
        
        # Step 3: WORM Audit Logging
        status = "EXECUTED" if policy_allowed else "BLOCKED_BY_POLICY"
        audit_event = self.logger.record_compliance_event(
            event_type="AGENT_EXECUTION_TURN",
            agent_id="AutonomousEnterpriseAgent",
            user_id=user_id,
            action=proposed_tool,
            status=status,
            payload={"sanitized_input": pii_result["clean_text"], "policy_decision": reason}
        )
        
        return {
            "status": status,
            "policy_decision": reason,
            "sanitized_input": pii_result["clean_text"],
            "audit_hash": audit_event["record_hash"]
        }

if __name__ == "__main__":
    orch = EnterpriseGovernanceOrchestrator(
        PresidioPIISanitizationEngine(),
        OPAPolicyDecisionPoint(),
        WORMComplianceLogger()
    )
    
    out = orch.process_agent_turn(
        user_id="sre_alice",
        user_role="SeniorSRE",
        environment="production",
        raw_user_input="Restart pod payment-v2 for user Bob (SSN 000-11-2222)",
        proposed_tool="restart_service",
        tool_params={"service": "payment-v2"}
    )
    print("\nGovernance Gateway Execution Result:")
    print(json.dumps(out, indent=2))

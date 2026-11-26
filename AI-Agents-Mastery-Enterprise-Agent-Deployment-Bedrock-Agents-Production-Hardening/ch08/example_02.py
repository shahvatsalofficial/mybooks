import json
from typing import Dict, Any, Tuple

class OPAPolicyDecisionPoint:
    """Evaluates agent tool execution requests against Open Policy Agent Rego policies."""

    @staticmethod
    def evaluate_tool_policy(
        user_role: str,
        environment: str,
        tool_name: str,
        tool_parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Simulates OPA evaluation of the enterprise 'agent.authorization' Rego policy."""
        # Policy Rule 1: No schema drops or table truncation in any environment
        if tool_name == "execute_sql" and any(k in str(tool_parameters).upper() for k in ["DROP", "TRUNCATE"]):
            return False, "DENY: Schema drops and table truncations are strictly forbidden by enterprise policy."
            
        # Policy Rule 2: Production mutations require Senior SRE or Admin role
        if environment == "production" and tool_name in ["restart_service", "scale_replicas"]:
            if user_role not in ["SeniorSRE", "PrincipalArchitect", "SecOpsLead"]:
                return False, f"DENY: Production mutation '{tool_name}' requires SeniorSRE role (User has: {user_role})."
                
        # Policy Rule 3: Financial payouts exceeding $10,000 require CFO or TreasuryDirector
        if tool_name == "initiate_treasury_transfer":
            amount = tool_parameters.get("amount_usd", 0)
            if amount > 10000 and user_role != "TreasuryDirector":
                return False, f"DENY: Transfers over $10,000 require TreasuryDirector approval (Amount: ${amount})."
                
        return True, "ALLOW: Policy constraints satisfied."

if __name__ == "__main__":
    pdp = OPAPolicyDecisionPoint()
    
    # Test 1: Junior developer attempting production restart
    allowed_1, reason_1 = pdp.evaluate_tool_policy(
        user_role="JuniorDeveloper",
        environment="production",
        tool_name="restart_service",
        tool_parameters={"service": "auth-core"}
    )
    print(f"Test 1 Evaluation: {allowed_1} - {reason_1}")
    
    # Test 2: Senior SRE authorized execution
    allowed_2, reason_2 = pdp.evaluate_tool_policy(
        user_role="SeniorSRE",
        environment="production",
        tool_name="restart_service",
        tool_parameters={"service": "auth-core"}
    )
    print(f"Test 2 Evaluation: {allowed_2} - {reason_2}")

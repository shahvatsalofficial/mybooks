# opa_client_evaluator.py
import httpx
import json
from typing import Dict, Any

class OPAPolicyEvaluator:
    def __init__(self, opa_url: str = "http://localhost:8181/v1/data/enterprise/ai/authorization"):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient(timeout=0.05) # 50ms strict timeout

    async def evaluate_request(self, user_claims: Dict[str, Any], prompt: str, target_region: str) -> Dict[str, Any]:
        payload = {
            "input": {
                "identity": {
                    "authenticated": bool(user_claims.get("sub")),
                    "tenant_status": user_claims.get("tenant_status", "ACTIVE"),
                    "data_residency_region": user_claims.get("region", "US"),
                    "groups": user_claims.get("groups", [])
                },
                "request": {
                    "prompt": prompt,
                    "target_region": target_region,
                    "contains_cross_border_data": user_claims.get("region") != target_region
                },
                "department_metrics": {
                    "monthly_spend_usd": user_claims.get("dept_spend", 0),
                    "monthly_budget_cap_usd": user_claims.get("dept_cap", 10000)
                }
            }
        }
        
        try:
            resp = await self.client.post(self.opa_url, json=payload)
            result = resp.json().get("result", {})
            return {
                "allow": result.get("allow", False),
                "redact_exec": result.get("redact_executive_comp", True)
            }
        except httpx.RequestError as exc:
            # Fail closed in enterprise zero-trust security postures
            return {"allow": False, "error": f"OPA policy server unreachable: {str(exc)}"}

class ResilientPlanExecutor:
    def __init__(self, plan_steps: List[str], tool_dispatcher: Callable[[str], Dict[str, Any]]):
        self.steps = plan_steps
        self.dispatcher = tool_dispatcher
        self.execution_log: List[Dict[str, Any]] = []

    def execute_with_remediation(self) -> Dict[str, Any]:
        for idx, step in enumerate(self.steps):
            result = self.dispatcher(step)
            self.execution_log.append({"step": step, "status": result["status"], "output": result.get("output")})
            
            if result["status"] == "failed":
                print(f"[REPLAN TRIGGER] Step '{step}' failed. Formulating alternative branch...")
                # Synthesize fallback step
                fallback_step = f"Fallback: Alternative routing for '{step}'"
                fb_result = self.dispatcher(fallback_step)
                self.execution_log.append({"step": fallback_step, "status": fb_result["status"], "output": fb_result.get("output")})
                if fb_result["status"] == "failed":
                    return {"success": False, "halted_at": step, "log": self.execution_log}
                    
        return {"success": True, "log": self.execution_log}

# Verification
def mock_dispatcher(action: str) -> Dict[str, Any]:
    if "Region 2" in action:
        return {"status": "failed", "output": "QuotaExceeded: vCPU limit reached in us-west-2"}
    return {"status": "success", "output": "Resources provisioned."}

executor = ResilientPlanExecutor(
    plan_steps=["Provision VPC in Region 1", "Provision VPC in Region 2", "Configure peering"],
    tool_dispatcher=mock_dispatcher
)
print("Plan Outcome:", executor.execute_with_remediation()["success"])

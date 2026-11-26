import asyncio

class SubgraphTimeoutGovernor:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    async def invoke_with_timeout(self, subgraph: Any, input_state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            print(f"[TIMEOUT GOVERNOR] Executing subgraph (Timeout Ceiling: {self.timeout_seconds}s)...")
            result = await asyncio.wait_for(
                subgraph.ainvoke(input_state),
                timeout=self.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            print(f"[TIMEOUT GOVERNOR] CRITICAL: Subgraph execution timed out after {self.timeout_seconds}s!")
            return {
                "resolution_status": "escalated",
                "final_resolution_summary": f"SLA Violation: Subgraph timed out after {self.timeout_seconds} seconds."
            }

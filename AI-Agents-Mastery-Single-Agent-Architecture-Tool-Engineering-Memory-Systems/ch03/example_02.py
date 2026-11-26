import asyncio
import time
from typing import NamedTuple

class ToolCallRequest(NamedTuple):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]

class ParallelToolDispatcher:
    def __init__(self, gateway: EnterpriseToolGateway, timeout_seconds: float = 5.0):
        self.gateway = gateway
        self.timeout = timeout_seconds

    async def _execute_single(self, req: ToolCallRequest) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            # Run synchronous tool in threadpool to avoid blocking event loop
            res = await asyncio.to_thread(self.gateway.dispatch, req.tool_name, req.arguments)
            elapsed = (time.perf_counter() - start) * 1000.0
            return {
                "call_id": req.call_id,
                "tool_name": req.tool_name,
                "success": res.success,
                "result": res.data if res.success else res.error,
                "latency_ms": round(elapsed, 2)
            }
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000.0
            return {
                "call_id": req.call_id,
                "tool_name": req.tool_name,
                "success": False,
                "result": f"Execution failed: {str(e)}",
                "latency_ms": round(elapsed, 2)
            }

    async def dispatch_parallel(self, requests: List[ToolCallRequest]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            async with asyncio.timeout(self.timeout):
                async with asyncio.TaskGroup() as tg:
                    tasks = [tg.create_task(self._execute_single(r)) for r in requests]
                results = [t.result() for t in tasks]
        except TimeoutError:
            return [{"error": f"Execution batch exceeded deadline of {self.timeout}s"}]
        return results

# Verification
async def run_parallel_demo():
    dispatcher = ParallelToolDispatcher(gateway=gateway, timeout_seconds=3.0)
    batch = [
        ToolCallRequest(call_id="call_01", tool_name="calculate_discount", arguments={"tier": "enterprise", "volume_units": 1500}),
        ToolCallRequest(call_id="call_02", tool_name="calculate_discount", arguments={"tier": "standard", "volume_units": 200, "is_nonprofit": True})
    ]
    outputs = await dispatcher.dispatch_parallel(batch)
    print("Parallel Execution Output:")
    print(json.dumps(outputs, indent=2))

asyncio.run(run_parallel_demo())

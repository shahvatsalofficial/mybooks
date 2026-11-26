import time
import logging
from typing import Callable, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToolDispatcher")

class ToolExecutionCircuitBreaker:
    """Circuit breaker pattern preventing repeated calls to failing enterprise backends."""
    
    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, float] = {}
        self.state: Dict[str, str] = {} # CLOSED, OPEN, HALF_OPEN

    def record_success(self, tool_name: str) -> None:
        self.failure_counts[tool_name] = 0
        self.state[tool_name] = "CLOSED"

    def record_failure(self, tool_name: str) -> None:
        self.failure_counts[tool_name] = self.failure_counts.get(tool_name, 0) + 1
        self.last_failure_times[tool_name] = time.time()
        if self.failure_counts[tool_name] >= self.failure_threshold:
            self.state[tool_name] = "OPEN"
            logger.warning(f"Circuit breaker OPEN for tool: {tool_name}")

    def is_allowed(self, tool_name: str) -> bool:
        state = self.state.get(tool_name, "CLOSED")
        if state == "CLOSED":
            return True
        if state == "OPEN":
            if time.time() - self.last_failure_times.get(tool_name, 0) > self.recovery_time_seconds:
                self.state[tool_name] = "HALF_OPEN"
                logger.info(f"Circuit breaker HALF_OPEN for tool: {tool_name}")
                return True
            return False
        return True # HALF_OPEN allows single test call

class ResilientToolDispatcher:
    """Executes agent-requested tools with circuit breaking and structured error reporting."""
    
    def __init__(self):
        self.registry: Dict[str, Callable[..., Dict[str, Any]]] = {}
        self.breaker = ToolExecutionCircuitBreaker()

    def register(self, name: str, fn: Callable[..., Dict[str, Any]]) -> None:
        self.registry[name] = fn

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.registry:
            return {
                "status": "ERROR",
                "error_code": "TOOL_NOT_FOUND",
                "message": f"Requested tool '{tool_name}' is not registered."
            }
        
        if not self.breaker.is_allowed(tool_name):
            return {
                "status": "ERROR",
                "error_code": "CIRCUIT_BREAKER_TRIPPED",
                "message": f"Tool '{tool_name}' is temporarily disabled due to backend outages."
            }

        try:
            fn = self.registry[tool_name]
            result = fn(**arguments)
            self.breaker.record_success(tool_name)
            return {"status": "SUCCESS", "result": result}
        except Exception as e:
            self.breaker.record_failure(tool_name)
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "status": "ERROR",
                "error_code": "EXECUTION_FAILURE",
                "message": str(e)
            }

# Demonstration mocks
def mock_restart_pod(namespace: str, pod_name: str, grace_period_seconds: int = 30):
    return {"restarted": True, "pod": pod_name, "namespace": namespace, "status": "Pending"}

if __name__ == "__main__":
    dispatcher = ResilientToolDispatcher()
    dispatcher.register("restart_kubernetes_pod", mock_restart_pod)
    
    res = dispatcher.dispatch("restart_kubernetes_pod", {
        "namespace": "production",
        "pod_name": "checkout-svc-v2-49a",
        "grace_period_seconds": 15
    })
    print("Dispatcher execution result:", json.dumps(res, indent=2))

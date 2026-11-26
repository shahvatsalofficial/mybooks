import time
from typing import Dict, Any

class DistributedToolCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 5.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_sec
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = 0.0

    def call_tool(self, tool_func) -> Dict[str, Any]:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
                print("[CIRCUIT BREAKER] State transitioning: OPEN -> HALF_OPEN (Canary probe allowed)")
            else:
                return {"status": "BLOCKED", "error": "Circuit Breaker OPEN. Fast-failing tool call."}

        try:
            result = tool_func()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                print("[CIRCUIT BREAKER] State transitioning: HALF_OPEN -> CLOSED (Service restored)")
            return {"status": "SUCCESS", "data": result}
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                print(f"[CIRCUIT BREAKER] Threshold reached! State transitioning -> OPEN ({self.failure_count} errors)")
            return {"status": "ERROR", "error": str(e)}

breaker = DistributedToolCircuitBreaker(failure_threshold=2, reset_timeout_sec=0.5)
def failing_api(): raise TimeoutError("Gateway 504")
breaker.call_tool(failing_api)
breaker.call_tool(failing_api)
res = breaker.call_tool(failing_api)
print("Throttled Call Result:", res["status"])

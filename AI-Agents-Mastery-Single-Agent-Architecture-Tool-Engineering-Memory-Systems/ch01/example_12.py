import time
from typing import Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("agent.runtime", "1.0.0")

class TelemetryInstrumentedAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def execute_turn(self, prompt: str, turn_number: int) -> Dict[str, Any]:
        with tracer.start_as_current_span("agent_turn") as span:
            span.set_attribute("agent.id", self.agent_id)
            span.set_attribute("agent.turn_number", turn_number)
            span.set_attribute("agent.prompt_length", len(prompt))

            start_think = time.perf_counter()
            with tracer.start_as_current_span("llm_reasoning_step"):
                time.sleep(0.045)  # Simulated LLM generation
                action = "query_database"
                action_input = {"sql": "SELECT COUNT(*) FROM transactions WHERE status = 'failed'"}

            think_ms = (time.perf_counter() - start_think) * 1000
            span.set_attribute("agent.latency.reasoning_ms", round(think_ms, 2))

            start_tool = time.perf_counter()
            with tracer.start_as_current_span("tool_execution") as tool_span:
                tool_span.set_attribute("tool.name", action)
                time.sleep(0.012)  # Simulated DB latency
                observation = {"count": 42}
                tool_span.set_status(Status(StatusCode.OK))

            tool_ms = (time.perf_counter() - start_tool) * 1000
            span.set_attribute("agent.latency.tool_ms", round(tool_ms, 2))

            return {
                "turn": turn_number,
                "action": action,
                "observation": observation,
                "metrics": {"think_ms": round(think_ms, 2), "tool_ms": round(tool_ms, 2)}
            }

agent = TelemetryInstrumentedAgent("fin-audit-01")
res = agent.execute_turn("Audit failed transactions for Q3", 1)

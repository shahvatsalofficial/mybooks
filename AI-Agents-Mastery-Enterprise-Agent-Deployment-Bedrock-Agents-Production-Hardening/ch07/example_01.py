import time
import json
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.semconv.trace import SpanAttributes

class PhoenixObservabilityQuickWin:
    """Sets up local Arize Phoenix tracing server and OpenTelemetry exporter."""

    def __init__(self, project_name: str = "enterprise-agent-core"):
        self.project_name = project_name
        # Register Phoenix as the OpenTelemetry trace exporter
        self.tracer_provider = register(
            project_name=self.project_name,
            endpoint="http://localhost:6006/v1/traces"
        )
        # Instrument LangChain/LlamaIndex frameworks automatically
        LangChainInstrumentor().instrument(tracer_provider=self.tracer_provider)
        print(f"Arize Phoenix Tracing initialized for project '{self.project_name}' on port 6006.")

    def trace_agent_step(self, session_id: str, prompt: str, tool_name: str, cost_usd: float):
        """Simulates recording custom trace attributes using OpenInference semantic conventions."""
        tracer = self.tracer_provider.get_tracer("agent.runtime")
        with tracer.start_as_current_span("agent_reasoning_loop") as span:
            span.set_attribute(SpanAttributes.INPUT_VALUE, prompt)
            span.set_attribute("session.id", session_id)
            span.set_attribute("llm.cost_usd", cost_usd)
            
            # Child span representing external tool call
            with tracer.start_as_current_span(f"tool_exec:{tool_name}") as tool_span:
                tool_span.set_attribute(SpanAttributes.TOOL_NAME, tool_name)
                time.sleep(0.05)
                tool_span.set_attribute(SpanAttributes.OUTPUT_VALUE, '{"status": "SUCCESS"}')
                
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, "Synthesized final answer from tool telemetry.")
            
        print(f"Recorded trace span for session {session_id} with tool '{tool_name}'.")

if __name__ == "__main__":
    obs = PhoenixObservabilityQuickWin()
    obs.trace_agent_step("sess-obs-101", "Audit IAM policies", "aws_iam_list_users", 0.042)

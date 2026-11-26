# observability/tracer_setup.py
"""
OpenTelemetry Setup for Agent Observability with Arize Phoenix & OpenInference.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace

def init_agent_observability(project_name: str = "agentic-frontier-vol2"):
    """
    Initializes OTel tracing and exports spans to local Arize Phoenix or LangSmith server.
    """
    collector_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
    
    tracer_provider = register(
        project_name=project_name,
        endpoint=collector_endpoint
    )
    
    # Auto-instrument OpenAI SDK and LangChain / LangGraph calls
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    
    tracer = trace.get_tracer("agent.tracer")
    print(f" OpenTelemetry Tracing initialized -> Exporting to {collector_endpoint}")
    return tracer

# Decorator for custom agent tool instrumentation
def trace_tool_execution(tool_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer("agent.tools")
            with tracer.start_as_current_span(f"Tool Execution: {tool_name}") as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("tool.args", str(kwargs))
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("tool.status", "SUCCESS")
                    return result
                except Exception as e:
                    span.set_attribute("tool.status", "ERROR")
                    span.record_exception(e)
                    raise e
        return wrapper
    return decorator

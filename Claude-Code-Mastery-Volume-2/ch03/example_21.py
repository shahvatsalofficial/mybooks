import os
from mcp.server.fastmcp import FastMCP, Context
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# 1. Initialize Global OpenTelemetry Tracer
provider = TracerProvider()
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector.corp.internal:4317")
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("enterprise.mcp.tracer", "1.0.0")

mcp = FastMCP("Instrumented-Enterprise-Gateway")

@mcp.tool()
async def execute_traced_workload(workload_id: str, ctx: Context) -> str:
    """Executes a business-critical workload with end-to-end OpenTelemetry distributed tracing."""
    with tracer.start_as_current_span("mcp.tool.execute_traced_workload") as span:
        span.set_attribute("mcp.tool_name", "execute_traced_workload")
        span.set_attribute("mcp.workload_id", workload_id)
        
        ctx.info(f"Executing traced workload {workload_id} with Trace ID: {span.get_span_context().trace_id:x}")
        
        # Child span representing downstream microservice invocation
        with tracer.start_as_current_span("downstream.service.call") as child_span:
            child_span.set_attribute("rpc.system", "grpc")
            # Simulate enterprise microservice communication
            await asyncio.sleep(0.15)
            child_span.set_attribute("rpc.status_code", 0)
            
        span.set_attribute("workload.status", "COMPLETED")
        return f"Workload {workload_id} completed. Trace ID: {span.get_span_context().trace_id:x}"

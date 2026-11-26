// OpenTelemetry Context Injector for MCP Outbound Calls
import crypto from "crypto";

export function generateW3cTraceContext(): { traceparent: string; tracestate: string } {
  const traceId = crypto.randomBytes(16).toString("hex");
  const spanId = crypto.randomBytes(8).toString("hex");
  const traceFlags = "01"; // Sampled

  return {
    traceparent: `00-${traceId}-${spanId}-${traceFlags}`,
    tracestate: "mcp=agent_v4"
  };
}

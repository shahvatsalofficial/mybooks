#!/usr/bin/env node
/**
 * Enterprise OpenTelemetry & Distributed Tracing MCP Server
 * Language: TypeScript / Node.js
 * Enables Claude Code to query distributed trace spans and error root causes
 */

import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import axios from "axios";

const JAEGER_API_URL = process.env.JAEGER_API_URL || "http://localhost:16686/api";

const server = new McpServer({
  name: "enterprise-otel-tracer",
  version: "1.0.0"
});

// Tool: Query Slow Traces
server.tool(
  "find_slow_traces",
  "Searches distributed traces exceeding a specific latency threshold in a microservice",
  {
    serviceName: z.string().describe("Target microservice name (e.g., auth-service, payment-gateway)"),
    operationName: z.string().optional().describe("Specific HTTP route or gRPC method name"),
    minDurationMs: z.number().int().min(100).default(1000).describe("Minimum trace duration in milliseconds"),
    limit: z.number().int().min(1).max(50).default(10).describe("Maximum number of traces to return")
  },
  async ({ serviceName, operationName, minDurationMs, limit }) => {
    try {
      const response = await axios.get(`${JAEGER_API_URL}/traces`, {
        params: {
          service: serviceName,
          operation: operationName,
          minDuration: `${minDurationMs}ms`,
          limit
        },
        timeout: 8000
      });

      const traces = response.data?.data || [];
      const summaries = traces.map((t: any) => {
        const rootSpan = t.spans.find((s: any) => !s.references || s.references.length === 0) || t.spans[0];
        const errorSpans = t.spans.filter((s: any) => s.tags?.some((tag: any) => tag.key === "error" && tag.value === true));

        return {
          traceId: t.traceID,
          rootOperation: rootSpan?.operationName,
          durationMs: (rootSpan?.duration || 0) / 1000,
          totalSpans: t.spans.length,
          hasErrors: errorSpans.length > 0,
          errorSummary: errorSpans.map((s: any) => s.operationName)
        };
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ service: serviceName, matchedTraces: summaries.length, traces: summaries }, null, 2)
        }]
      };
    } catch (err: any) {
      return {
        content: [{ type: "text", text: `OTEL QUERY ERROR: ${err.message}` }],
        isError: true
      };
    }
  }
);

// Resource Template: Detailed Trace Span Waterfall
const traceWaterfallTemplate = new ResourceTemplate(
  "trace://spans/{trace_id}",
  { list: undefined }
);

server.resource(
  "trace-span-waterfall",
  traceWaterfallTemplate,
  { description: "Inspects the full span timeline and error logs for a specific trace ID", mimeType: "application/json" },
  async (uri, { trace_id }) => {
    try {
      const res = await axios.get(`${JAEGER_API_URL}/traces/${trace_id}`);
      const traceData = res.data?.data?.[0];

      if (!traceData) {
        return {
          contents: [{ uri: uri.href, text: `Trace ${trace_id} not found`, mimeType: "text/plain" }]
        };
      }

      // Compact span tree for model context preservation
      const compactSpans = traceData.spans.map((s: any) => ({
        spanId: s.spanID,
        operation: s.operationName,
        durationMs: s.duration / 1000,
        logs: s.logs?.map((l: any) => l.fields)
      }));

      return {
        contents: [{
          uri: uri.href,
          text: JSON.stringify({ traceId: trace_id, spans: compactSpans }, null, 2),
          mimeType: "application/json"
        }]
      };
    } catch (err: any) {
      return {
        contents: [{ uri: uri.href, text: `FAILED TO FETCH TRACE: ${err.message}`, mimeType: "text/plain" }]
      };
    }
  }
);

async function startTracer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[OTEL TRACER READY] Connected to Jaeger telemetry mesh.");
}

startTracer().catch((e) => {
  console.error("[FATAL]", e);
  process.exit(1);
});

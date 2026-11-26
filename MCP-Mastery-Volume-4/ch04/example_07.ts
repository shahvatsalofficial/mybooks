import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const PROMETHEUS_URL = process.env.PROMETHEUS_URL || "http://prometheus-k8s.monitoring.svc:9090";

const mcpServer = new Server(
  { name: "prometheus-promql-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "prometheus_instant_query",
        description: "Executes an instant PromQL query returning current metric values across services.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "PromQL expression (e.g. 'sum(rate(http_requests_total{status=~\"5..\"}[5m]))')." }
          },
          required: ["query"]
        }
      },
      {
        name: "prometheus_range_query",
        description: "Executes a time-windowed PromQL query with strict 6-hour evaluation caps and auto-calculated step resolution.",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "PromQL expression." },
            duration_minutes: { type: "number", description: "Minutes to look back (max: 360 / 6 hours).", default: 30 }
          },
          required: ["query"]
        }
      }
    ]
  };
});

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "prometheus_instant_query") {
    const query = String(args?.query);
    try {
      const url = `${PROMETHEUS_URL}/api/v1/query?query=${encodeURIComponent(query)}`;
      const res = await fetch(url);
      const data = await res.json();

      if (data.status !== "success") {
        return { isError: true, content: [{ type: "text", text: `PromQL Error: ${data.error}` }] };
      }

      // Compact vector output: extract metric labels and scalar values
      const results = (data.data?.result || []).map((r: any) => ({
        metric: r.metric,
        value: r.value ? Number(r.value[1]) : null
      }));

      return {
        content: [{ type: "text", text: JSON.stringify(results.slice(0, 25), null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Prometheus Network Error: ${err.message}` }] };
    }
  }

  if (name === "prometheus_range_query") {
    const query = String(args?.query);
    const durationMinutes = Math.min(Number(args?.duration_minutes) || 30, 360);
    const endSeconds = Math.floor(Date.now() / 1000);
    const startSeconds = endSeconds - (durationMinutes * 60);

    // Auto-calculate step to ensure no more than 60 data points per series
    const stepSeconds = Math.max(Math.floor((durationMinutes * 60) / 60), 15);

    try {
      const url = `${PROMETHEUS_URL}/api/v1/query_range?query=${encodeURIComponent(query)}&start=${startSeconds}&end=${endSeconds}&step=${stepSeconds}`;
      const res = await fetch(url);
      const data = await res.json();

      if (data.status !== "success") {
        return { isError: true, content: [{ type: "text", text: `PromQL Range Error: ${data.error}` }] };
      }

      // Synthesize statistical summary: min, max, avg, latest value
      const seriesSummaries = (data.data?.result || []).map((series: any) => {
        const values: number[] = (series.values || []).map((v: any) => Number(v[1])).filter((v: number) => !isNaN(v));
        if (values.length === 0) return { metric: series.metric, summary: "No data points" };

        const min = Math.min(...values);
        const max = Math.max(...values);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const latest = values[values.length - 1];

        return {
          metric: series.metric,
          dataPointsEvaluated: values.length,
          min: Number(min.toFixed(3)),
          max: Number(max.toFixed(3)),
          avg: Number(avg.toFixed(3)),
          latest: Number(latest.toFixed(3))
        };
      });

      return {
        content: [{ type: "text", text: JSON.stringify(seriesSummaries.slice(0, 15), null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Prometheus Range Network Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function run() {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error("Prometheus PromQL MCP Server initialized.");
}

run().catch(console.error);

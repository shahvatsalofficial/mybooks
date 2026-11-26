// metrics_exporter.ts — Production Prometheus Metrics Pipeline for MCP
import http from 'http';
import client from 'prom-client';

export class McpMetricsRegistry {
    public readonly register: client.Registry;

    // Counters
    public readonly toolInvocationsTotal: client.Counter<string>;
    public readonly tokenCostUsdTotal: client.Counter<string>;

    // Histograms
    public readonly toolDurationSeconds: client.Histogram<string>;

    // Gauges
    public readonly activeSseConnections: client.Gauge<string>;

    constructor() {
        this.register = new client.Registry();
        client.collectDefaultMetrics({ register: this.register, prefix: 'mcp_gateway_' });

        this.toolInvocationsTotal = new client.Counter({
            name: 'mcp_tool_calls_total',
            help: 'Total number of MCP tool invocations',
            labelNames: ['tool', 'tenant', 'status'],
            registers: [this.register]
        });

        this.tokenCostUsdTotal = new client.Counter({
            name: 'mcp_token_cost_usd_total',
            help: 'Cumulative token cost incurred in USD',
            labelNames: ['tenant', 'model'],
            registers: [this.register]
        });

        this.toolDurationSeconds = new client.Histogram({
            name: 'mcp_tool_duration_seconds',
            help: 'End-to-end tool execution duration in seconds',
            labelNames: ['tool', 'tenant'],
            buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
            registers: [this.register]
        });

        this.activeSseConnections = new client.Gauge({
            name: 'mcp_active_sse_connections',
            help: 'Number of currently active SSE streams connected to the gateway',
            labelNames: ['node'],
            registers: [this.register]
        });
    }

    public startMetricsServer(port: number = 9090): http.Server {
        const server = http.createServer(async (req, res) => {
            if (req.url === '/metrics') {
                res.setHeader('Content-Type', this.register.contentType);
                res.end(await this.register.metrics());
            } else {
                res.statusCode = 404;
                res.end('Not Found');
            }
        });

        server.listen(port, () => {
            console.log(`[PROMETHEUS] Metrics server listening on :${port}/metrics`);
        });

        return server;
    }
}

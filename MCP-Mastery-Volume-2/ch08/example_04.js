// benchmarks/mcp_sse_load.js - k6 Distributed Concurrency Benchmark
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom Enterprise Telemetry Metrics
const mcpToolLatency = new Trend('mcp_tool_call_duration_ms');
const mcpErrorRate = new Rate('mcp_failure_rate');
const mcpTotalInvocations = new Counter('mcp_total_tool_invocations');

export const options = {
  stages: [
    { duration: '30s', target: 200 },  // Ramp-up to 200 concurrent agent sessions
    { duration: '1m',  target: 1000 }, // Scale to 1,000 peak concurrent agents
    { duration: '2m',  target: 1000 }, // Sustain peak stress load
    { duration: '30s', target: 0 },    // Graceful ramp-down
  ],
  thresholds: {
    'mcp_tool_call_duration_ms': ['p(95)<45', 'p(99)<120'], // 95% of calls < 45ms
    'mcp_failure_rate': ['rate<0.001'],                    // Less than 0.1% errors
    'http_req_failed': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.MCP_SERVER_URL || 'http://localhost:8000';

export default function () {
  // Session setup: Each virtual user acquires an active SSE session endpoint
  const sessionId = `vu-${__VU}-${__ITER}`;
  const endpoint = `${BASE_URL}/messages?sessionId=${sessionId}`;

  // Formulate JSON-RPC 2.0 tool invocation payload
  const payload = JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'check_inventory',
      arguments: {
        sku: 'SKU-8819',
        warehouse_id: 'WH-NORTH',
      },
    },
    id: `req-${__VU}-${Date.now()}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Agent-ID': `agent-runner-${__VU}`,
    },
    timeout: '5s',
  };

  const startTime = Date.now();
  const res = http.post(endpoint, payload, params);
  const latency = Date.now() - startTime;

  mcpToolLatency.add(latency);
  mcpTotalInvocations.add(1);

  // Validate response status and payload integrity
  const isOk = check(res, {
    'status is 200': (r) => r.status === 200,
    'valid jsonrpc': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.jsonrpc === '2.0' && body.result !== undefined && !body.result.isError;
      } catch (e) {
        return false;
      }
    },
  });

  if (!isOk) {
    mcpErrorRate.add(1);
  } else {
    mcpErrorRate.add(0);
  }

  // Realistic human / LLM thinking time distribution between turns
  sleep(Math.random() * 0.5 + 0.1);
}

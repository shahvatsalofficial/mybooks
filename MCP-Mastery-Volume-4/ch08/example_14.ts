import { McpTestHarness } from "./mcp-test-harness.js";

export async function executeStressBenchmark(
  serverPath: string,
  totalRequests: number = 1000,
  concurrency: number = 10
): Promise<{ totalTimeMs: number; avgLatencyMs: number; p99LatencyMs: number; errorRate: number }> {
  const harness = new McpTestHarness(serverPath);
  await harness.assertInitialize();

  const latencies: number[] = [];
  let errorCount = 0;
  const startTime = Date.now();

  async function worker(requestsPerWorker: number) {
    for (let i = 0; i < requestsPerWorker; i++) {
      const t0 = Date.now();
      try {
        const res = await harness.sendRequest("tools/call", {
          name: "query_postgres",
          arguments: { sql: "SELECT 1 as healthcheck;", limit: 1 }
        });
        if (res.error) errorCount++;
        latencies.push(Date.now() - t0);
      } catch {
        errorCount++;
        latencies.push(Date.now() - t0);
      }
    }
  }

  const reqPerWorker = Math.floor(totalRequests / concurrency);
  const workers = Array.from({ length: concurrency }, () => worker(reqPerWorker));
  await Promise.all(workers);

  await harness.close();
  const totalDuration = Date.now() - startTime;
  latencies.sort((a, b) => a - b);

  const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
  const p99Index = Math.floor(latencies.length * 0.99);
  const p99Latency = latencies[p99Index] || 0;

  return {
    totalTimeMs: totalDuration,
    avgLatencyMs: Number(avgLatency.toFixed(2)),
    p99LatencyMs: p99Latency,
    errorRate: Number((errorCount / totalRequests).toFixed(4))
  };
}

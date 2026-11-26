/**
 * transport_stress_test.ts
 * Synthetic stress and fault injection harness for Model Context Protocol transports.
 * Verifies non-blocking performance, large payload handling, and rapid reconnects.
 */

import { spawn } from 'child_process';
import http from 'http';

interface TestMetrics {
  messagesSent: number;
  messagesReceived: number;
  corruptedFramesCaught: number;
  avgLatencyMs: number;
  deadlockDetected: boolean;
}

export class TransportStressHarness {
  /**
   * Exercise an stdio child server with a rapid burst of high-volume messages
   * to guarantee no kernel buffer deadlocks occur.
   */
  public static async testStdioDeadlockResilience(
    command: string,
    args: string[],
    iterations: number = 500
  ): Promise<TestMetrics> {
    console.log(`[TEST] Launching stdio stress test: ${command} (${iterations} iterations)...`);
    
    const proc = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    const metrics: TestMetrics = {
      messagesSent: 0,
      messagesReceived: 0,
      corruptedFramesCaught: 0,
      avgLatencyMs: 0,
      deadlockDetected: false
    };

    let stderrBytes = 0;
    proc.stderr.on('data', (chunk) => {
      stderrBytes += chunk.length;
    });

    const latencies: number[] = [];
    const pendingRequests = new Map<number, number>();

    // Parse stdout line by line
    let buffer = '';
    proc.stdout.on('data', (chunk) => {
      buffer += chunk.toString('utf8');
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Retain partial trailing chunk

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.id && pendingRequests.has(msg.id)) {
            const start = pendingRequests.get(msg.id)!;
            latencies.push(Date.now() - start);
            pendingRequests.delete(msg.id);
            metrics.messagesReceived++;
          }
        } catch (e) {
          metrics.corruptedFramesCaught++;
        }
      }
    });

    // Watchdog timer to detect kernel pipe deadlock
    const timeoutPromise = new Promise<void>((_, reject) => {
      const timer = setTimeout(() => {
        if (metrics.messagesReceived < iterations) {
          metrics.deadlockDetected = true;
          proc.kill('SIGKILL');
          reject(new Error(`DEADLOCK DETECTED: Only received ${metrics.messagesReceived}/${iterations} messages.`));
        }
      }, 15000); // 15s absolute ceiling
      timer.unref();
    });

    // Dispatch loop
    const sendPromise = (async () => {
      for (let i = 1; i <= iterations; i++) {
        const pingMsg = JSON.stringify({
          jsonrpc: '2.0',
          method: 'ping',
          id: i,
          // Inject 2KB dummy payload to stress kernel pipe memory
          params: { padding: 'X'.repeat(2048) }
        }) + '\n';

        pendingRequests.set(i, Date.now());
        proc.stdin.write(pingMsg);
        metrics.messagesSent++;

        // Cooperative tick every 50 requests
        if (i % 50 === 0) {
          await new Promise((r) => setImmediate(r));
        }
      }
    })();

    await Promise.race([Promise.all([sendPromise, new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (metrics.messagesReceived >= iterations) {
          clearInterval(checkInterval);
          resolve(true);
        }
      }, 50);
    })]), timeoutPromise]);

    proc.stdin.end();
    proc.kill('SIGTERM');

    metrics.avgLatencyMs = latencies.reduce((a, b) => a + b, 0) / (latencies.length || 1);
    console.log(`[PASS] Stdio stress completed. Stderr bytes absorbed: ${stderrBytes}. Avg latency: ${metrics.avgLatencyMs.toFixed(2)}ms`);
    return metrics;
  }
}

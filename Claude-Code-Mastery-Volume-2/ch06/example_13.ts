/**
 * @file multi_agent_swarm.test.ts
 * Integration test suite for autonomous multi-agent swarm orchestration.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { EventEmitter } from 'events';
import { Readable, Writable } from 'stream';

// --- Test Fixtures & Mocks ---

interface SwarmMessage {
  jsonrpc: '2.0';
  id?: string;
  method?: string;
  params?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: { code: number; message: string };
}

class MockWorkerProcess extends EventEmitter {
  public stdin: Writable;
  public stdout: Readable;
  public stderr: Readable;
  public killed: boolean = false;
  public pid: number;

  constructor(pid: number) {
    super();
    this.pid = pid;
    this.stdin = new Writable({
      write: (chunk, encoding, callback) => {
        this.handleIncoming(chunk.toString('utf8'));
        callback();
      }
    });
    this.stdout = new Readable({ read() {} });
    this.stderr = new Readable({ read() {} });
  }

  private handleIncoming(data: string) {
    try {
      const msg: SwarmMessage = JSON.parse(data.trim());
      if (msg.method === 'execute_task') {
        const payload = msg.params as { taskId: string; action: string };
        if (payload.action === 'fail') {
          this.stdout.push(JSON.stringify({
            jsonrpc: '2.0',
            id: msg.id,
            error: { code: -32000, message: 'Simulated worker execution failure' }
          }) + '\n');
        } else {
          this.stdout.push(JSON.stringify({
            jsonrpc: '2.0',
            id: msg.id,
            result: { taskId: payload.taskId, status: 'COMPLETED', confidence: 0.95 }
          }) + '\n');
        }
      }
    } catch {
      // Ignore parse error in mock
    }
  }

  kill(signal: string = 'SIGTERM') {
    this.killed = true;
    this.emit('exit', 0, signal);
  }
}

class SwarmCoordinator {
  private workers: Map<number, MockWorkerProcess> = new Map();
  private nextPid: number = 1000;

  spawnWorker(): MockWorkerProcess {
    const pid = this.nextPid++;
    const worker = new MockWorkerProcess(pid);
    this.workers.set(pid, worker);
    worker.on('exit', () => {
      this.workers.delete(pid);
    });
    return worker;
  }

  async dispatchTaskWithTimeout(
    worker: MockWorkerProcess,
    task: { taskId: string; action: string },
    timeoutMs: number
  ): Promise<Record<string, unknown>> {
    return new Promise((resolve, reject) => {
      const requestId = `req-${Math.random().toString(36).substring(7)}`;
      let timer: NodeJS.Timeout;

      const onData = (chunk: Buffer) => {
        const response: SwarmMessage = JSON.parse(chunk.toString('utf8').trim());
        if (response.id === requestId) {
          clearTimeout(timer);
          worker.stdout.off('data', onData);
          if (response.error) {
            reject(new Error(response.error.message));
          } else {
            resolve(response.result!);
          }
        }
      };

      worker.stdout.on('data', onData);

      timer = setTimeout(() => {
        worker.stdout.off('data', onData);
        reject(new Error(`Worker execution timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      const request: SwarmMessage = {
        jsonrpc: '2.0',
        id: requestId,
        method: 'execute_task',
        params: task
      };

      worker.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  terminateAll(signal: string = 'SIGTERM'): number {
    let terminatedCount = 0;
    for (const [pid, worker] of this.workers.entries()) {
      worker.kill(signal);
      terminatedCount++;
    }
    this.workers.clear();
    return terminatedCount;
  }

  get activeWorkerCount(): number {
    return this.workers.size;
  }
}

// --- Test Suite Execution ---

describe('Autonomous Multi-Agent Swarm Orchestration Suite', () => {
  let coordinator: SwarmCoordinator;

  beforeEach(() => {
    coordinator = new SwarmCoordinator();
  });

  afterEach(() => {
    coordinator.terminateAll();
  });

  it('should successfully spawn worker and execute JSON-RPC task over STDIO pipes', async () => {
    const worker = coordinator.spawnWorker();
    expect(coordinator.activeWorkerCount).toBe(1);

    const result = await coordinator.dispatchTaskWithTimeout(
      worker,
      { taskId: 'task-auth-01', action: 'generate_jwt_validation' },
      2000
    );

    expect(result.status).toBe('COMPLETED');
    expect(result.taskId).toBe('task-auth-01');
    expect(result.confidence).toBe(0.95);
  });

  it('should reject when worker returns JSON-RPC protocol error', async () => {
    const worker = coordinator.spawnWorker();

    await expect(
      coordinator.dispatchTaskWithTimeout(
        worker,
        { taskId: 'task-db-02', action: 'fail' },
        2000
      )
    ).rejects.toThrow('Simulated worker execution failure');
  });

  it('should enforce execution timeout and prevent orchestrator hanging on deadlocked worker', async () => {
    const worker = coordinator.spawnWorker();
    // Simulate deadlocked worker by overwriting handler to not respond
    worker.stdin.removeAllListeners('data');

    await expect(
      coordinator.dispatchTaskWithTimeout(
        worker,
        { taskId: 'task-deadlock', action: 'infinite_loop' },
        150 // Short timeout for test
      )
    ).rejects.toThrow('Worker execution timed out after 150ms');
  });

  it('should atomically kill all registered workers upon emergency kill-switch activation', () => {
    const worker1 = coordinator.spawnWorker();
    const worker2 = coordinator.spawnWorker();
    const worker3 = coordinator.spawnWorker();

    expect(coordinator.activeWorkerCount).toBe(3);

    const terminated = coordinator.terminateAll('SIGKILL');

    expect(terminated).toBe(3);
    expect(coordinator.activeWorkerCount).toBe(0);
    expect(worker1.killed).toBe(true);
    expect(worker2.killed).toBe(true);
    expect(worker3.killed).toBe(true);
  });

  it('should correctly tally consensus ballots across heterogeneous reviewer models', () => {
    interface Ballot {
      voterId: string;
      vote: 'APPROVE' | 'REJECT';
      confidence: number;
    }

    const ballots: Ballot[] = [
      { voterId: 'claude-3-7-sonnet', vote: 'APPROVE', confidence: 0.96 },
      { voterId: 'gpt-4o', vote: 'APPROVE', confidence: 0.88 },
      { voterId: 'gemini-1-5-pro', vote: 'REJECT', confidence: 0.72 }
    ];

    const approvalThreshold = 0.66;
    const approvalCount = ballots.filter(b => b.vote === 'APPROVE').length;
    const approvalRatio = approvalCount / ballots.length;

    // Weighted confidence calculation
    const weightedSum = ballots.reduce((acc, b) => acc + (b.vote === 'APPROVE' ? b.confidence : -b.confidence), 0);

    expect(approvalRatio).toBeGreaterThanOrEqual(approvalThreshold);
    expect(weightedSum).toBeGreaterThan(0); // Net positive confidence
  });
});

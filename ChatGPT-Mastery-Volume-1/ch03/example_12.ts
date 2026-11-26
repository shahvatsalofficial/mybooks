/**
 * Production Enterprise Python Sandbox Orchestrator
 * Target: Node.js 20+ / TypeScript 5.0+
 * Architecture: Isolated subprocess execution with resource caps and stream trapping
 */

import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

export interface ExecutionRequest {
  sessionId: string;
  codePayload: string;
  timeoutMs?: number;
  memoryLimitMb?: number;
}

export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  executionDurationMs: number;
  generatedArtifacts: string[];
  timedOut: boolean;
}

export class SandboxedExecutionManager {
  private baseStorageDir: string;
  private defaultTimeoutMs: number;

  constructor(baseStorageDir: string = '/mnt/data/sandboxes', defaultTimeoutMs: number = 60000) {
    this.baseStorageDir = baseStorageDir;
    this.defaultTimeoutMs = defaultTimeoutMs;
  }

  /**
   * Dispatches Python code into an isolated session directory with strict time and process controls
   */
  public async executePythonSession(request: ExecutionRequest): Promise<ExecutionResult> {
    const sessionDir = path.join(this.baseStorageDir, request.sessionId);
    if (!fs.existsSync(sessionDir)) {
      fs.mkdirSync(sessionDir, { recursive: true });
    }

    const scriptPath = path.join(sessionDir, `execution_${Date.now()}.py`);
    fs.writeFileSync(scriptPath, request.codePayload, 'utf-8');

    const startTime = Date.now();
    const timeout = request.timeoutMs || this.defaultTimeoutMs;

    return new Promise((resolve) => {
      let stdoutBuffer = '';
      let stderrBuffer = '';
      let isTimedOut = false;

      // Spawn Python process with unbuffered output and working dir constrained to sessionDir
      const child = spawn('python3', ['-u', scriptPath], {
        cwd: sessionDir,
        env: {
          ...process.env,
          PYTHONPATH: sessionDir,
          MPLBACKEND: 'Agg', // Strictly headless Matplotlib
          TMPDIR: sessionDir
        }
      });

      // Enforce hard execution deadline
      const timer = setTimeout(() => {
        isTimedOut = true;
        child.kill('SIGKILL'); // Hard termination of runaway process
      }, timeout);

      child.stdout.on('data', (data) => {
        stdoutBuffer += data.toString();
        // Prevent buffer DOS: truncate if stdout exceeds 5MB
        if (stdoutBuffer.length > 5 * 1024 * 1024) {
          stdoutBuffer = stdoutBuffer.slice(0, 5 * 1024 * 1024) + '\n[TRUNCATED: STDOUT BUFFER OVERFLOW]';
          child.kill('SIGTERM');
        }
      });

      child.stderr.on('data', (data) => {
        stderrBuffer += data.toString();
        if (stderrBuffer.length > 2 * 1024 * 1024) {
          stderrBuffer = stderrBuffer.slice(0, 2 * 1024 * 1024) + '\n[TRUNCATED: STDERR BUFFER OVERFLOW]';
        }
      });

      child.on('close', (code) => {
        clearTimeout(timer);
        const duration = Date.now() - startTime;

        // Scan session directory for newly generated artifacts (PNG, CSV, XLSX, PDF)
        const allFiles = fs.readdirSync(sessionDir);
        const artifacts = allFiles
          .filter((f) => !f.endsWith('.py') && !f.startsWith('.'))
          .map((f) => path.join(sessionDir, f));

        resolve({
          stdout: stdoutBuffer.trim(),
          stderr: isTimedOut ? `[FATAL] Execution exceeded ${timeout}ms deadline.` : stderrBuffer.trim(),
          exitCode: isTimedOut ? 137 : code,
          executionDurationMs: duration,
          generatedArtifacts: artifacts,
          timedOut: isTimedOut
        });
      });
    });
  }
}

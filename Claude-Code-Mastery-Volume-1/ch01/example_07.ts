// agent_harness.ts — Enterprise Terminal Agent Orchestrator
import { spawn, ChildProcess } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

interface ExecutionConfig {
  projectDir: string;
  maxExecutionTimeMs: number;
  maxOutputBytes: number;
  environmentVariables: Record<string, string>;
  auditLogPath: string;
}

interface TelemetryEvent {
  timestamp: string;
  eventType: 'START' | 'STDOUT' | 'STDERR' | 'TIMEOUT' | 'TERMINATE';
  payload: string;
  exitCode?: number;
}

export class TerminalAgentHarness {
  private config: ExecutionConfig;
  private childProcess: ChildProcess | null = null;
  private telemetryStream: fs.WriteStream;

  constructor(config: ExecutionConfig) {
    this.config = config;
    this.telemetryStream = fs.createWriteStream(config.auditLogPath, { flags: 'a' });
  }

  private logEvent(eventType: TelemetryEvent['eventType'], payload: string, exitCode?: number): void {
    const event: TelemetryEvent = {
      timestamp: new Date().toISOString(),
      eventType,
      payload: payload.trim(),
      exitCode
    };
    this.telemetryStream.write(JSON.stringify(event) + '\n');
  }

  public async executeObjective(objective: string): Promise<number> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      this.logEvent('START', `Initiating objective: ${objective}`);

      // Merge environment, enforcing strict non-interactive shell defaults
      const mergedEnv: NodeJS.ProcessEnv = {
        ...process.env,
        ...this.config.environmentVariables,
        CI: 'true',
        PAGER: 'cat',
        FORCE_COLOR: '0',
        PROJECT_ROOT: this.config.projectDir
      };

      // Spawn Claude Code CLI with bypass-sandbox and headless objective flags
      this.childProcess = spawn('claude', ['--dangerously-skip-permissions', '-p', objective], {
        cwd: this.config.projectDir,
        env: mergedEnv,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let totalOutputBytes = 0;

      // Watchdog Timer to prevent runaway execution loops
      const timeoutWatchdog = setTimeout(() => {
        if (this.childProcess && !this.childProcess.killed) {
          this.logEvent('TIMEOUT', `Execution exceeded ${this.config.maxExecutionTimeMs}ms. Forcing SIGTERM.`);
          this.childProcess.kill('SIGTERM');
          
          // Escalate to SIGKILL if not terminated within 5 seconds
          setTimeout(() => {
            if (this.childProcess && !this.childProcess.killed) {
              this.childProcess.kill('SIGKILL');
            }
          }, 5000);
        }
      }, this.config.maxExecutionTimeMs);

      // Stream stdout telemetry with truncation protection
      this.childProcess.stdout?.on('data', (chunk: Buffer) => {
        totalOutputBytes += chunk.length;
        if (totalOutputBytes <= this.config.maxOutputBytes) {
          const text = chunk.toString('utf8');
          process.stdout.write(text);
          this.logEvent('STDOUT', text);
        } else if (totalOutputBytes - chunk.length < this.config.maxOutputBytes) {
          const warning = '\n[WARN: Maximum output buffer threshold reached. Suppressing remaining telemetry.]\n';
          process.stdout.write(warning);
          this.logEvent('STDOUT', warning);
        }
      });

      // Stream stderr telemetry
      this.childProcess.stderr?.on('data', (chunk: Buffer) => {
        const text = chunk.toString('utf8');
        process.stderr.write(text);
        this.logEvent('STDERR', text);
      });

      // Process completion handler
      this.childProcess.on('close', (code: number | null) => {
        clearTimeout(timeoutWatchdog);
        const exitCode = code ?? 1;
        const duration = Date.now() - startTime;
        this.logEvent('TERMINATE', `Process completed in ${duration}ms`, exitCode);
        this.telemetryStream.end();

        if (exitCode === 0) {
          resolve(exitCode);
        } else {
          reject(new Error(`Agent exited with non-zero status code: ${exitCode}`));
        }
      });

      this.childProcess.on('error', (err: Error) => {
        clearTimeout(timeoutWatchdog);
        this.logEvent('TERMINATE', `Fatal process error: ${err.message}`);
        this.telemetryStream.end();
        reject(err);
      });
    });
  }
}

// Example usage in an enterprise CI pipeline:
async function run() {
  const orchestrator = new TerminalAgentHarness({
    projectDir: path.resolve(__dirname, '..'),
    maxExecutionTimeMs: 120000, // 2-minute safety limit
    maxOutputBytes: 1024 * 1024,  // 1MB log buffer
    environmentVariables: {
      NODE_ENV: 'test',
      AUTH_TOKEN: 'ephemeral-ci-token'
    },
    auditLogPath: path.resolve(__dirname, 'audit_telemetry.jsonl')
  });

  try {
    const code = await orchestrator.executeObjective(
      "Audit all package.json files for CVE-2025-4122 and apply semver patches."
    );
    console.log(`Pipeline successfully converged with exit code ${code}`);
  } catch (err: any) {
    console.error(`Pipeline failure: ${err.message}`);
    process.exit(1);
  }
}

// Production Patch: Structured Subprocess Execution with Automatic Reaping
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

server.tool(
  'run_git_checkout_safe',
  'Executes git status with timeout and deterministic process reaping',
  { repoPath: z.string() },
  async ({ repoPath }) => {
    try {
      // execFile automatically closes file descriptors and reaps child process
      const { stdout } = await execFileAsync('git', ['status', '--porcelain'], {
        cwd: repoPath,
        timeout: 5000, // Hard 5.0s execution timeout
        maxBuffer: 1024 * 1024, // 1MB buffer ceiling prevents pipe saturation
        killSignal: 'SIGKILL'
      });
      return {
        content: [{ type: 'text', text: stdout || 'Working tree clean' }]
      };
    } catch (err: any) {
      return {
        isError: true,
        content: [{ type: 'text', text: `Command execution failed: ${err.message}` }]
      };
    }
  }
);

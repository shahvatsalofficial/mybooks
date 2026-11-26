import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

export async function secureGitCheckout(workspaceDir: string, branchName: string): Promise<string> {
  // Validate branch name against Git ref naming rules (no spaces, no tildes, no colons)
  if (!/^[a-zA-Z0-9_\-\.\/]+$/.test(branchName) || branchName.startsWith("-")) {
    throw new Error(`Invalid git branch name: ${branchName}`);
  }

  // Double-dash '--' guarantees that branchName is NEVER parsed as a git CLI option!
  const { stdout, stderr } = await execFileAsync(
    "git",
    ["checkout", "--", branchName],
    {
      cwd: workspaceDir,
      shell: false, // MANDATORY: Bypass shell interpreter
      timeout: 10000 // 10 second execution ceiling
    }
  );

  return stdout || stderr;
}

import { z } from "zod";
import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs";

const execFileAsync = promisify(execFile);

export const GitBranchCreateSchema = z.object({
  repositoryPath: z.string().describe("Relative or absolute path to local Git repository"),
  branchName: z.string()
    .min(3, "Branch name must be at least 3 characters")
    .max(64, "Branch name cannot exceed 64 characters")
    .regex(/^[a-z0-9][a-z0-9_\-\/]+$/, "Branch name must contain only lowercase alphanumeric characters, dashes, and slashes")
    .refine(val => !val.includes(".."), "Branch name cannot contain path traversal sequences")
    .refine(val => !val.startsWith("-"), "Branch name cannot start with a hyphen (option injection defense)")
    .describe("Name of new Git branch to create"),
  startPoint: z.string()
    .default("HEAD")
    .describe("Commit hash or branch to branch from (defaults to HEAD)")
});

export async function handleGitBranchCreate(args: z.infer<typeof GitBranchCreateSchema>): Promise<string> {
  // 1. Resolve repository directory and verify existence
  const repoDir = path.resolve(args.repositoryPath);
  if (!fs.existsSync(repoDir) || !fs.existsSync(path.join(repoDir, ".git"))) {
    throw new Error(`DIRECTORY_ERROR: Path '${args.repositoryPath}' is not a valid Git repository.`);
  }

  // 2. Validate startPoint does not begin with a hyphen
  if (args.startPoint.startsWith("-")) {
    throw new Error(`SECURITY_ERROR: Start point cannot start with a hyphen: '${args.startPoint}'`);
  }

  try {
    // 3. Execute git command using execFile with shell: false and double-dash '--' barrier
    const { stdout, stderr } = await execFileAsync(
      "git",
      ["checkout", "-b", args.branchName, "--", args.startPoint],
      {
        cwd: repoDir,
        shell: false, // Bypasses shell execution completely
        timeout: 10000,
        env: {
          ...process.env,
          GIT_TERMINAL_PROMPT: "0" // Prevent git from hanging waiting for interactive auth
        }
      }
    );

    return `### Git Branch Creation Successful\n` +
           `* **Repository:** \`${repoDir}\`\n` +
           `* **New Branch:** \`${args.branchName}\`\n` +
           `* **Base Reference:** \`${args.startPoint}\`\n\n` +
           `${stdout || stderr || "Switched to new branch."}`;
  } catch (err: any) {
    return `GIT_COMMAND_FAILED: Failed to create branch '${args.branchName}': ${err.message}`;
  }
}

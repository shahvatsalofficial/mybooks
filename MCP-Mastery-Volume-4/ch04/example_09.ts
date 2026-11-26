import { execFile } from "child_process";
import fs from "fs";
import path from "path";

export interface AnsibleExecutionResult {
  successful: boolean;
  tasksOk: number;
  tasksChanged: number;
  tasksFailed: number;
  tasksSkipped: number;
  rawSummary: string;
}

export class AnsibleRunnerBridge {
  static async executePlaybook(
    playbookPath: string,
    inventoryPath: string,
    dryRun: boolean = true
  ): Promise<AnsibleExecutionResult> {
    const args = ["-i", inventoryPath, playbookPath];
    if (dryRun) {
      args.push("--check"); // Dry-run simulation mode
    }

    return new Promise((resolve, reject) => {
      execFile("ansible-playbook", args, { timeout: 120000 }, (err, stdout, stderr) => {
        const output = stdout.toString("utf8");
        
        // Parse standard Ansible recap: "localhost : ok=4 changed=1 unreachable=0 failed=0 skipped=0"
        const recapMatch = output.match(/:\s+ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)\s+skipped=(\d+)/);
        
        if (recapMatch) {
          const ok = parseInt(recapMatch[1], 10);
          const changed = parseInt(recapMatch[2], 10);
          const unreachable = parseInt(recapMatch[3], 10);
          const failed = parseInt(recapMatch[4], 10);
          const skipped = parseInt(recapMatch[5], 10);

          resolve({
            successful: failed === 0 && unreachable === 0,
            tasksOk: ok,
            tasksChanged: changed,
            tasksFailed: failed,
            tasksSkipped: skipped,
            rawSummary: output.split("PLAY RECAP").pop()?.trim() || output.slice(-500)
          });
        } else {
          if (err) return reject(new Error(`Ansible Execution Failed: ${stderr || err.message}`));
          resolve({
            successful: true,
            tasksOk: 0,
            tasksChanged: 0,
            tasksFailed: 0,
            tasksSkipped: 0,
            rawSummary: output.slice(-500)
          });
        }
      });
    });
  }
}

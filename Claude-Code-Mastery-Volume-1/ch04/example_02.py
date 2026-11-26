"""
Enterprise PTY Command Sandbox & Git Transaction Engine (Python Runtime)
Version: 3.2 | Production Grade
Author: Vatsal Shah (https://shahvatsal.com)
"""

import os
import pty
import select
import subprocess
import signal
import re
from typing import Dict, Any, Optional

class PTYCommandSandbox:
    def __init__(self, workspace_root: str, timeout_seconds: int = 30):
        self.workspace_root = os.path.abspath(workspace_root)
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = 46080 # 45KB Safety Ceiling

    def execute_command_sandboxed(self, command: str) -> Dict[str, Any]:
        """
        Executes a shell command inside an isolated PTY process group with
        streaming buffer truncation and automated process group termination.
        """
        # Enforce Tool Authorization Boundary (TAB)
        if not self._is_command_authorized(command):
            return {
                "success": False,
                "exit_code": 126,
                "output": "SECURITY_POLICY_VIOLATION: Command blocked by Tool Authorization Boundary."
            }

        master_fd, slave_fd = pty.openpty()
        env = os.environ.copy()
        env.update({
            "CI": "true",
            "DEBIAN_FRONTEND": "noninteractive",
            "GIT_TERMINAL_PROMPT": "0",
            "TERM": "xterm-256color"
        })

        try:
            # Spawn child in fresh process group
            proc = subprocess.Popen(
                command,
                shell=True,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=self.workspace_root,
                env=env,
                preexec_fn=os.setpgrp
            )
            os.close(slave_fd) # Close slave in parent process

            output_chunks = []
            total_bytes = 0
            truncated = False

            while True:
                # Poll PTY master with timeout
                rlist, _, _ = select.select([master_fd], [], [], self.timeout_seconds)
                if not rlist:
                    # Timeout exceeded -> Terminate process group
                    self._kill_process_group(proc.pid)
                    return {
                        "success": False,
                        "exit_code": 124,
                        "output": f"COMMAND_TIMEOUT: Process exceeded {self.timeout_seconds}s limit."
                    }

                try:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break # EOF reached
                    
                    total_bytes += len(data)
                    if total_bytes <= self.max_output_bytes:
                        output_chunks.append(data)
                    else:
                        truncated = True
                except OSError:
                    break # Slave closed on process exit

            proc.wait()
            os.close(master_fd)

            raw_text = b"".join(output_chunks).decode("utf-8", errors="replace")
            # Redact secrets
            clean_text = self._redact_secrets(raw_text)

            if truncated:
                clean_text += f"\n\n[WARNING: Telemetry exceeded {self.max_output_bytes} bytes. Truncated.]"

            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "output": clean_text
            }

        except Exception as e:
            return {"success": False, "exit_code": 1, "output": f"EXECUTION_ERROR: {str(e)}"}

    def _is_command_authorized(self, cmd: str) -> bool:
        # Veto dangerous commands
        veto_patterns = [
            r"rm\s+-rf\s+[/~]",
            r"git\s+reset\s+--hard",
            r"git\s+clean\s+-fdx",
            r":\(\)\{ :\|:& \};:",
            r"sudo\s+",
            r"mkfs\."
        ]
        for pattern in veto_patterns:
            if re.search(pattern, cmd):
                return False
        return True

    def _kill_process_group(self, pid: int) -> None:
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGINT)
            # Check if still running after 2s
            subprocess.run(["sleep", "2"])
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _redact_secrets(self, text: str) -> str:
        text = re.sub(r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]", text)
        text = re.sub(r"ghp_[0-9a-zA-Z]{36}", "[REDACTED_GH_TOKEN]", text)
        return text

"""
recipe_4_3_sandbox_executor.py
Secure subprocess execution sandbox with timeout enforcement and buffer clamping.
"""

import asyncio
import os
import resource
import sys
from typing import Tuple

MAX_OUTPUT_BYTES = 5 * 1024 * 1024  # 5MB buffer ceiling
EXECUTION_TIMEOUT_SECONDS = 15.0     # 15s hard execution ceiling
MAX_VIRTUAL_MEMORY_BYTES = 512 * 1024 * 1024  # 512MB RAM cap


def set_process_limits():
    """Configure POSIX resource limits (cgroups/rlimit) for child process."""
    if hasattr(resource, "RLIMIT_AS"):
        # Restrict virtual address space (RAM)
        resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY_BYTES, MAX_VIRTUAL_MEMORY_BYTES))
    if hasattr(resource, "RLIMIT_CPU"):
        # Restrict maximum CPU time in seconds
        resource.setrlimit(resource.RLIMIT_CPU, (10, 15))


async def run_sandboxed_command(
    command: list[str],
    cwd: str = "/tmp"
) -> Tuple[bool, str]:
    """
    Executes an external command within sandbox boundaries.
    Returns: (is_error: bool, output_text: str)
    """
    sys.stderr.write(f"[Sandbox] Invoking: {' '.join(command)}\n")

    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=set_process_limits,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"}
        )

        try:
            # Wait for execution with hard timeout boundary
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=EXECUTION_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            sys.stderr.write(f"[Sandbox] Timeout exceeded ({EXECUTION_TIMEOUT_SECONDS}s). Escalating kill.\n")
            proc.kill()
            await proc.wait()
            return True, f"TimeoutError: Process exceeded maximum execution window of {EXECUTION_TIMEOUT_SECONDS}s."

        # Buffer Clamping: Prevent memory exhaustion from unbounded log output
        if len(stdout_bytes) > MAX_OUTPUT_BYTES:
            stdout_bytes = stdout_bytes[:MAX_OUTPUT_BYTES] + b"\n[OUTPUT TRUNCATED: Exceeded 5MB limit]"

        stdout_str = stdout_bytes.decode("utf-8", errors="replace")
        stderr_str = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            return True, f"ProcessFailed (Exit Code {proc.returncode}):\n{stderr_str or stdout_str}"

        return False, stdout_str or "Command completed with zero output."

    except Exception as exc:
        return True, f"SandboxExecutionFailure: {str(exc)}"

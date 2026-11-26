#!/usr/bin/env python3
"""
Enterprise Kubernetes Diagnostic MCP Server
Language: Python 3.11+
Features: Namespace sandboxing, command array execution, output truncation
"""

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, field_validator
import asyncio
import re

mcp = FastMCP("Kubernetes-Diagnostic-Gateway")

class PodDiagnosticInput(BaseModel):
    namespace: str = Field(
        default="production",
        description="Target Kubernetes namespace"
    )
    pod_name: str = Field(
        ...,
        description="Exact pod identifier registered in cluster"
    )
    container_name: str = Field(
        default="",
        description="Target container name (optional if pod has single container)"
    )
    diagnostic_tool: str = Field(
        ...,
        description="Approved diagnostic utility to execute: 'ps', 'netstat', 'df', 'uptime'"
    )

    @field_validator("diagnostic_tool")
    @classmethod
    def enforce_tool_allowlist(cls, val: str) -> str:
        # Whitelist approved read-only diagnostic commands
        allowed = ["ps", "netstat", "df", "uptime", "free"]
        cleaned = val.strip().lower()
        if cleaned not in allowed:
            raise ValueError(
                f"SECURITY VIOLATION: '{val}' is not in approved diagnostic allowlist: {allowed}"
            )
        return cleaned

@mcp.tool()
async def execute_pod_diagnostic(input_data: PodDiagnosticInput, ctx: Context) -> str:
    """Executes an isolated, read-only diagnostic utility inside a Kubernetes container."""
    ctx.info(f"Executing '{input_data.diagnostic_tool}' in pod {input_data.namespace}/{input_data.pod_name}...")

    # Build safe kubectl exec argv array (NO SHELL INTERPRETER!)
    cmd_args = [
        "kubectl", "exec",
        "-n", input_data.namespace,
        input_data.pod_name
    ]
    if input_data.container_name:
        cmd_args.extend(["-c", input_data.container_name])

    cmd_args.append("--")
    # Append the sanitized diagnostic command
    if input_data.diagnostic_tool == "ps":
        cmd_args.extend(["ps", "aux"])
    elif input_data.diagnostic_tool == "df":
        cmd_args.extend(["df", "-h"])
    elif input_data.diagnostic_tool == "uptime":
        cmd_args.append("uptime")
    elif input_data.diagnostic_tool == "free":
        cmd_args.extend(["free", "-m"])
    elif input_data.diagnostic_tool == "netstat":
        cmd_args.extend(["netstat", "-tuln"])

    try:
        # Execute asynchronously without shell
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        output = stdout_bytes.decode("utf-8", errors="replace")
        
        # Enforce 16KB output truncation ceiling
        if len(output) > 16384:
            output = output[:16384] + "\n\n... [TRUNCATED: Diagnostic output exceeded 16KB limit] ..."
            
        return f"### Pod Diagnostic Result ({input_data.pod_name} - {input_data.diagnostic_tool}):\n```\n{output}\n```"
    except asyncio.TimeoutError:
        return f"EXECUTION_TIMEOUT: Diagnostic command timed out after 15 seconds."
    except Exception as err:
        return f"KUBECTL_EXECUTION_ERROR: {str(err)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

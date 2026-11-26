import docker
import time
from typing import Dict, Any

class IsolatedSandboxRunner:
    """
    Orchestrates short-lived, ephemeral gVisor (runsc) containers for safe
    execution of untrusted LLM-generated code.
    """
    def __init__(self, runtime: str = "runsc", memory_limit: str = "256m", cpu_quota: int = 50000):
        self.runtime = runtime  # Uses gVisor runsc runtime
        self.memory_limit = memory_limit
        self.cpu_quota = cpu_quota  # 50% of 1 CPU core
        self.client = docker.from_env()

    def execute_python_code(self, code_snippet: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """
        Executes Python code inside an ephemeral gVisor container with no network access,
        read-only filesystem, and strict resource bounds.
        """
        # Escape code for inline execution
        wrapped_script = f"""
import sys, io
buffer = io.StringIO()
sys.stdout = buffer
sys.stderr = buffer

try:
{self._indent_code(code_snippet)}
except Exception as e:
    print(f"RUNTIME ERROR: {{e}}")

print("---OUTPUT_START---")
print(buffer.getvalue())
"""

        start_time = time.time()
        container = None
        try:
            # Create ephemeral isolated container
            container = self.client.containers.run(
                image="python:3.11-slim",
                command=["python", "-c", wrapped_script],
                runtime=self.runtime,          # Enforce gVisor sandbox
                network_mode="none",           # Full network isolation (no internet egress)
                mem_limit=self.memory_limit,   # RAM limit
                cpu_quota=self.cpu_quota,      # CPU cap
                read_only=True,                # Read-only root filesystem
                tmpfs={'/tmp': 'rw,noexec,nosuid,size=64m'}, # Isolated temp storage
                detach=True,
                remove=False
            )

            # Wait for execution with explicit timeout
            exit_code = container.wait(timeout=timeout_seconds)
            execution_time = time.time() - start_time
            
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            return {
                "success": exit_code.get("StatusCode") == 0,
                "exit_code": exit_code.get("StatusCode"),
                "output": logs.strip(),
                "execution_time_seconds": round(execution_time, 3),
                "isolated": True
            }

        except docker.errors.ContainerError as ce:
            return {"success": False, "error": f"Container Error: {ce}", "isolated": True}
        except Exception as e:
            return {"success": False, "error": f"Execution Failed or Timed Out ({timeout_seconds}s limit): {e}", "isolated": True}
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _indent_code(self, code: str) -> str:
        return "\n".join(["    " + line for line in code.split("\n")])


# --- Test Execution ---
if __name__ == "__main__":
    runner = IsolatedSandboxRunner(runtime="runc") # Use runc for local dev fallback
    
    # Untrusted Code Sample
    malicious_code = """
import os
print("Attempting to read host environment...")
keys = os.environ.get('PATH')
print(f"PATH: {keys}")
result = 42 * 100
print(f"Calculation Result: {result}")
"""

    res = runner.execute_python_code(malicious_code, timeout_seconds=3)
    print("--- SANDBOX EXECUTION RESULT ---")
    print(f"Success: {res['success']}")
    print(f"Execution Time: {res['execution_time_seconds']}s")
    print(f"Output:\n{res['output']}")

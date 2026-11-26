import os
from e2b_code_interpreter import Sandbox

class EphemeralSandboxTool:
    """
    Executes AI-generated Python scripts inside a secure, ephemeral E2B MicroVM sandbox.
    Enforces timeout bounds and sanitizes stdout/stderr output.
    """
    def __init__(self, api_key: str, timeout_seconds: int = 10):
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def execute_python_code(self, python_code: str) -> dict:
        """Boots a fresh MicroVM, runs the code, captures execution artifacts, and destroys VM."""
        print(f"[Sandbox] Booting ephemeral E2B MicroVM (Timeout: {self.timeout_seconds}s)...")
        
        try:
            # Boot isolated MicroVM
            with Sandbox(api_key=self.api_key, timeout=self.timeout_seconds) as sbx:
                # Execute python script
                execution = sbx.run_code(python_code)
                
                # Process outputs and errors
                stdout_text = "\n".join([out.text for out in execution.logs.stdout if hasattr(out, 'text')])
                stderr_text = "\n".join([err.text for err in execution.logs.stderr if hasattr(err, 'text')])
                
                error_msg = None
                if execution.error:
                    error_msg = f"{execution.error.name}: {execution.error.value}\n{execution.error.traceback}"

                return {
                    "status": "SUCCESS" if not error_msg else "RUNTIME_ERROR",
                    "stdout": stdout_text.strip(),
                    "stderr": stderr_text.strip(),
                    "error": error_msg,
                    "results": [res.to_dict() for res in execution.results]
                }
        except Exception as err:
            return {
                "status": "SANDBOX_EXCEPTION",
                "stdout": "",
                "stderr": "",
                "error": f"MicroVM Hypervisor Error: {str(err)}",
                "results": []
            }

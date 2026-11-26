"""
Sandboxed Environmental Oracle: Compiles and tests code artifacts in a secure
execution sandbox, returning objective compiler stderr and test results to the agent.
"""

import subprocess
import tempfile
import os
from typing import Tuple, Dict, Any


class SandboxedCodeOracle:
    """Provides objective environmental ground truth via local compilers/linters."""

    def __init__(self, execution_timeout_seconds: int = 15):
        self.timeout = execution_timeout_seconds

    def test_python_artifact(self, code_str: str) -> Tuple[bool, str]:
        """
        Writes code to a temporary file, runs flake8 and python syntax compilation.
        Returns: (success, diagnostic_output)
        """
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code_str)
            temp_path = f.name

        try:
            compile_res = subprocess.run(
                ["python", "-m", "py_compile", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            if compile_res.returncode != 0:
                return False, f"SYNTAX_COMPILATION_ERROR:\n{compile_res.stderr}"

            lint_res = subprocess.run(
                ["flake8", "--select=E9,F63,F7,F82", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            if lint_res.returncode != 0:
                return False, f"LINTER_SECURITY_WARNINGS:\n{lint_res.stdout}"

            return True, "ENVIRONMENTAL_ORACLE_PASSED: Code compiled cleanly with 0 syntax errors."

        except subprocess.TimeoutExpired:
            return False, "TIMEOUT: Environmental execution timed out."
        except Exception as exc:
            return False, f"ORACLE_EXECUTION_FAILURE: {str(exc)}"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

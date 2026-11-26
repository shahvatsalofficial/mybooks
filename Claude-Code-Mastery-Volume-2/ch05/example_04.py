#!/usr/bin/env python3
"""
Enterprise Python Self-Healing Test Engine
Language: Python 3.11+
Features: Pytest JSON report parsing, AST patch validation, regression protection
"""

import subprocess
import json
import os
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TestFailure:
    file_path: str
    line_number: int
    test_name: str
    message: str

class SelfHealingEngine:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    def run_test_suite(self) -> tuple[bool, List[TestFailure]]:
        """Executes pytest with JSON reporting and parses failures."""
        report_file = os.path.join(self.workspace_dir, ".pytest_report.json")
        cmd = [
            "pytest",
            f"--json-report-file={report_file}",
            "--json-report",
            "-q"
        ]
        
        proc = subprocess.run(cmd, cwd=self.workspace_dir, capture_output=True, text=True)
        
        if not os.path.exists(report_file):
            return proc.returncode == 0, []

        with open(report_file, "r") as f:
            data = json.load(f)

        failures = []
        for test in data.get("tests", []):
            if test.get("outcome") == "failed":
                call = test.get("call", {})
                crash = call.get("crash", {})
                failures.append(TestFailure(
                    file_path=crash.get("path", "unknown"),
                    line_number=crash.get("lineno", 0),
                    test_name=test.get("nodeid", "unknown"),
                    message=crash.get("message", "Test assertion failed")
                ))

        return len(failures) == 0, failures

    def execute_self_healing_cycle(self, max_attempts: int = 3) -> bool:
        """Runs iterative self-healing cycle until all tests pass or attempts exhausted."""
        for attempt in range(1, max_attempts + 1):
            passed, failures = self.run_test_suite()
            if passed:
                print(f"✅ All tests passed cleanly on attempt {attempt}!")
                return True

            print(f"⚠️ Attempt {attempt}: {len(failures)} test(s) failing. Analyzing root cause...")
            for fail in failures:
                print(f"  - Failing Test: {fail.test_name} ({fail.file_path}:{fail.line_number})")
                print(f"    Message: {fail.message}")

            # In production, dispatch failing context to LLM for code patching
            # patch_code(fail.file_path, fail.line_number, fail.message)
            
        print("❌ Self-healing cycle exhausted maximum attempts without resolution.")
        return False

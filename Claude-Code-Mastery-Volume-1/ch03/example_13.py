"""
Enterprise Prompt Compiler & AST Boundary Guard (Python Runtime)
Version: 2.4 | Production Grade
Author: Vatsal Shah (https://shahvatsal.com)
"""

import os
import re
import xml.sax.saxutils as saxutils
from typing import List, Dict, Any, Optional

class EnterprisePromptCompiler:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        
    def build_system_prompt(self, invariants: List[Dict[str, str]], rules_files: List[str]) -> str:
        """
        Assembles immutable system directives and project rules into a cache-aligned prefix.
        """
        rules_xml = []
        for rf in rules_files:
            target_path = os.path.join(self.project_root, rf)
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    content = f.read()
                rules_xml.append(f'    <rule_document file="{rf}">\n{saxutils.escape(content)}\n    </rule_document>')
                
        invariants_xml = []
        for inv in invariants:
            invariants_xml.append(
                f'    <invariant id="{inv["id"]}" priority="{inv.get("priority", "P0")}">'
                f'{saxutils.escape(inv["text"])}</invariant>'
            )

        envelope = [
            '<enterprise_system_constitution version="2.4">',
            '  <immutable_invariants>',
            "\n".join(invariants_xml),
            '  </immutable_invariants>',
            '  <project_memory_lattice>',
            "\n".join(rules_xml),
            '  </project_memory_lattice>',
            '  <tool_governance strict_json="true" preflight_ast="required" />',
            '</enterprise_system_constitution>'
        ]
        return "\n".join(envelope)

    @staticmethod
    def execute_atomic_file_patch(
        file_path: str,
        start_line: int,
        end_line: int,
        target_str: str,
        replacement_str: str
    ) -> Dict[str, Any]:
        """
        Performs pre-flight validation and atomic line-range patch.
        """
        if not os.path.isabs(file_path):
            return {"success": False, "error": f"Path must be absolute: {file_path}"}
            
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File does not exist: {file_path}"}

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)
        if start_line < 1 or end_line > total_lines or start_line > end_line:
            return {
                "success": False,
                "error": f"Line range [{start_line}, {end_line}] invalid for {total_lines}-line file."
            }

        # Extract target window
        window_raw = "".join(lines[start_line - 1 : end_line])
        
        # Normalize CRLF / LF
        window_norm = window_raw.replace("\r\n", "\n")
        target_norm = target_str.replace("\r\n", "\n")

        if target_norm not in window_norm:
            diagnostic = "".join(lines[max(0, start_line - 2) : min(total_lines, end_line + 2)])
            return {
                "success": False,
                "error": "TARGET_MISMATCH",
                "diagnostic_snippet": diagnostic,
                "message": f"Target content not found within lines {start_line}-{end_line}."
            }

        # Perform replacement within window
        patched_window = window_norm.replace(target_norm, replacement_str.replace("\r\n", "\n"), 1)

        # Reconstruct file
        new_content = "".join(lines[: start_line - 1]) + patched_window + "".join(lines[end_line:])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {"success": True, "message": f"Successfully patched {file_path}"}

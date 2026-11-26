"""
Codebase AST Navigation Tool Runner.
Provides structural Python Abstract Syntax Tree (AST) symbol lookup and surgical
patching to eliminate token-heavy full-file inspections.
"""

import ast
from typing import List, Dict, Any, Optional


class CodebaseASTNavigator:
    """Extracts function boundaries and signatures directly via Python AST."""

    @staticmethod
    def extract_symbol_map(source_code: str) -> List[Dict[str, Any]]:
        """Parses source code and returns symbol index with line ranges."""
        tree = ast.parse(source_code)
        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append({
                    "name": node.name,
                    "type": type(node).__name__,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "docstring": ast.get_docstring(node) or ""
                })

        return symbols

    @staticmethod
    def extract_method_source(source_code: str, method_name: str) -> Optional[str]:
        """Extracts the exact source lines of a specific function or class."""
        lines = source_code.splitlines()
        symbols = CodebaseASTNavigator.extract_symbol_map(source_code)

        for sym in symbols:
            if sym["name"] == method_name:
                start = sym["start_line"] - 1
                end = sym["end_line"]
                return "\n".join(lines[start:end])

        return None

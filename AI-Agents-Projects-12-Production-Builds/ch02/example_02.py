from __future__ import annotations

import ast
import hashlib
from pathlib import Path


class SymbolExtractor(ast.NodeVisitor):
    def __init__(self, module_name: str, file_path: str, source_lines: list[str]) -> None:
        self.module_name = module_name
        self.file_path = file_path
        self.source_lines = source_lines
        self.spans: list[SymbolSpan] = []
        self._class_stack: list[str] = []

    def _record(self, node: ast.AST, name: str, kind: SymbolKind) -> None:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start) or start
        segment = "\n".join(self.source_lines[start - 1 : end])
        digest = hashlib.sha256(segment.encode("utf-8")).hexdigest()
        qual_name = f"{'.'.join(self._class_stack)}.{name}" if self._class_stack else name
        self.spans.append(
            SymbolSpan(
                symbol_id=f"{self.module_name}:{qual_name}",
                file_path=self.file_path,
                name=qual_name,
                kind=kind,
                start_line=start,
                end_line=end,
                source_sha256=digest,
            )
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._record(node, node.name, SymbolKind.CLASS)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        kind = SymbolKind.METHOD if self._class_stack else SymbolKind.FUNCTION
        self._record(node, node.name, kind)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        kind = SymbolKind.METHOD if self._class_stack else SymbolKind.ASYNC_FUNCTION
        self._record(node, node.name, kind)
        self.generic_visit(node)


def index_python_source(module_name: str, file_path: str, source_code: str) -> list[SymbolSpan]:
    tree = ast.parse(source_code, filename=file_path)
    extractor = SymbolExtractor(module_name, file_path, source_code.splitlines())
    extractor.visit(tree)
    return extractor.spans


if __name__ == "__main__":
    code = """
class SettlementEngine:
    def validate_batch(self, batch_id: str) -> bool:
        return bool(batch_id)

    async def commit_ledger(self, records: list[dict]) -> int:
        return len(records)

def healthcheck() -> str:
    return "ok"
"""
    found = index_python_source("ledger.engine", "ledger/engine.py", code)
    for sp in found:
        print(f"{sp.kind.value:<15} {sp.symbol_id:<38} lines={sp.start_line}-{sp.end_line}")

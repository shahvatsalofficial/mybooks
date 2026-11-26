from __future__ import annotations

import ast
from dataclasses import dataclass


BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.AsyncWith,
    ast.IfExp,
)


@dataclass(frozen=True)
class ComplexityMetric:
    symbol_name: str
    complexity: int
    line_count: int


def measure_function_complexity(source_code: str) -> list[ComplexityMetric]:
    tree = ast.parse(source_code)
    metrics: list[ComplexityMetric] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score = 1
            for child in ast.walk(node):
                if isinstance(child, BRANCH_NODES):
                    score += 1
                elif isinstance(child, ast.BoolOp):
                    score += max(0, len(child.values) - 1)
            lines = (getattr(node, "end_lineno", node.lineno) - node.lineno) + 1
            metrics.append(ComplexityMetric(symbol_name=node.name, complexity=score, line_count=lines))

    return sorted(metrics, key=lambda m: m.complexity, reverse=True)


if __name__ == "__main__":
    sample = """
def simple_add(a: int, b: int) -> int:
    return a + b

def route_settlement(tx: dict, retry: bool) -> str:
    if not tx or tx.get("amount", 0) <= 0:
        return "reject"
    if tx.get("currency") == "USD" and (tx.get("tier") == "VIP" or retry):
        for step in tx.get("checks", []):
            if step == "sanctions":
                return "hold"
        return "fast_track"
    return "standard"
"""
    for item in measure_function_complexity(sample):
        print(f"symbol={item.symbol_name:<20} mccabe={item.complexity:<3} lines={item.line_count}")

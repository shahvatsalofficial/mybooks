from __future__ import annotations

import ast
import operator
from decimal import Decimal
from typing import Dict


class IsolatedMathSandbox:
    """Safely evaluates arithmetic formulas using AST node allowlisting."""

    BINARY_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    @classmethod
    def evaluate(cls, expression: str, variables: Dict[str, Decimal]) -> Decimal:
        tree = ast.parse(expression.strip(), mode="eval")
        return cls._eval_node(tree.body, variables)

    @classmethod
    def _eval_node(cls, node: ast.AST, variables: Dict[str, Decimal]) -> Decimal:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError(f"Unbound variable '{node.id}' in formula.")
            return variables[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls.UNARY_OPS:
            return cls.UNARY_OPS[type(node.op)](cls._eval_node(node.operand, variables))
        if isinstance(node, ast.BinOp) and type(node.op) in cls.BINARY_OPS:
            left = cls._eval_node(node.left, variables)
            right = cls._eval_node(node.right, variables)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("Division by zero in financial formula.")
            return cls.BINARY_OPS[type(node.op)](left, right)
        raise SecurityError(f"Disallowed AST node: {type(node).__name__}")


class SecurityError(Exception):
    pass


if __name__ == "__main__":
    vars_map = {
        "ebitda": Decimal("2950"),
        "capex": Decimal("1420"),
        "interest": Decimal("240"),
    }
    coverage = IsolatedMathSandbox.evaluate("(ebitda - capex) / interest", vars_map)
    print(f"Cash Interest Coverage: {coverage:.2f}x")
    try:
        IsolatedMathSandbox.evaluate("__import__('os').system('whoami')", vars_map)
    except SecurityError as exc:
        print(f"Blocked unsafe payload: {exc}")

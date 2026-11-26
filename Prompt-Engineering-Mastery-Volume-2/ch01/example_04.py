import ast
import operator
import re
from typing import Dict, Any

class AssertionParser:
    """Safely evaluates basic arithmetic expressions emitted in thought traces."""
    SAFE_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    @classmethod
    def evaluate_expression(cls, expr_str: str) -> float:
        node = ast.parse(expr_str, mode='eval').body
        return cls._eval(node)

    @classmethod
    def _eval(cls, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = cls.SAFE_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(cls._eval(node.left), cls._eval(node.right))
        else:
            raise TypeError(f"Unsupported AST node: {type(node)}")

def audit_scratchpad_assertions(scratchpad_text: str) -> Dict[str, Any]:
    # Regex to match patterns like: [CHECK: 4.8 - 3.4 = 1.4]
    check_pattern = r"\[CHECK:\s*([0-9\.\s\+\-\*/]+)=\s*([0-9\.]+)\]"
    matches = re.findall(check_pattern, scratchpad_text)
    
    audit_results = []
    for expr, claimed_val in matches:
        expr = expr.strip()
        claimed = float(claimed_val.strip())
        actual = AssertionParser.evaluate_expression(expr)
        is_valid = abs(actual - claimed) < 1e-4
        audit_results.append({
            "expression": expr,
            "claimed": claimed,
            "actual": actual,
            "valid": is_valid
        })
        if not is_valid:
            return {
                "passed": False,
                "violation": f"Arithmetic failure: {expr} evaluates to {actual}, but thought trace claimed {claimed}."
            }
            
    return {"passed": True, "audited_count": len(audit_results), "details": audit_results}

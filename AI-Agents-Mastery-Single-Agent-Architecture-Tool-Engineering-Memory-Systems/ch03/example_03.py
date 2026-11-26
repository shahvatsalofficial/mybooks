import ast
import math

class SecureASTEvaluator:
    # Whitelist safe AST nodes
    SAFE_NODES = {
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Num, ast.Str, ast.List, ast.Dict, ast.Tuple,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.Name, ast.Load, ast.Call
    }

    # Safe built-in functions
    SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp
    }

    @classmethod
    def evaluate(cls, expression: str, context_vars: Optional[Dict[str, Any]] = None) -> Any:
        context = dict(cls.SAFE_FUNCTIONS)
        if context_vars:
            context.update(context_vars)

        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}") from e

        # Walk tree and assert all nodes are in whitelist
        for node in ast.walk(tree):
            if type(node) not in cls.SAFE_NODES:
                raise PermissionError(f"Security Violation: Prohibited AST node '{type(node).__name__}' detected.")
            
            # Guard against attribute access: e.g. __class__, __subclasses__, os.system
            if isinstance(node, ast.Attribute):
                raise PermissionError(f"Security Violation: Attribute access ('.{node.attr}') is strictly forbidden.")
            
            # Guard against unauthorized function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id not in context:
                        raise PermissionError(f"Security Violation: Call to unauthorized function '{node.func.id}'.")
                else:
                    raise PermissionError("Security Violation: Complex function calls are forbidden.")

        # Execute verified AST
        compiled = compile(tree, filename="<sandbox>", mode="eval")
        return eval(compiled, {"__builtins__": None}, context)

# Verification
print("Safe Evaluation:", SecureASTEvaluator.evaluate("sqrt(144) + sum([10, 20, 30])"))

try:
    # Malicious injection attempt
    SecureASTEvaluator.evaluate("__import__('os').system('ls')")
except PermissionError as p_err:
    print("Caught Exploit Attempt:", p_err)

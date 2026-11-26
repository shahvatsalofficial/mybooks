from __future__ import annotations

import ast


def synthesize_pytest_module(module_import: str, source_code: str) -> str:
    tree = ast.parse(source_code)
    lines: list[str] = [
        "from __future__ import annotations",
        "import pytest",
        f"from {module_import} import *",
        "",
    ]
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args if a.arg != "self"]
            raised = [
                child.exc.func.id
                for child in ast.walk(node)
                if isinstance(child, ast.Raise)
                and isinstance(child.exc, ast.Call)
                and isinstance(child.exc.func, ast.Name)
            ]
            # Nominal smoke test
            sample_args = ", ".join("100" if "amount" in a or "int" in a else "'ok'" for a in args)
            lines.append(f"def test_{node.name}_nominal() -> None:")
            lines.append(f"    result = {node.name}({sample_args})")
            lines.append("    assert result is not None")
            lines.append("")

            if raised:
                exc_name = raised[0]
                bad_args = ", ".join("-1" if "amount" in a else "''" for a in args)
                lines.append(f"def test_{node.name}_raises_{exc_name.lower()}() -> None:")
                lines.append(f"    with pytest.raises({exc_name}):")
                lines.append(f"        {node.name}({bad_args})")
                lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    target_src = """
def compute_fee(amount: int) -> float:
    if amount < 0:
        raise ValueError("amount must be non-negative")
    return round(amount * 0.025, 2)
"""
    generated = synthesize_pytest_module("billing.fees", target_src)
    print(generated.strip())

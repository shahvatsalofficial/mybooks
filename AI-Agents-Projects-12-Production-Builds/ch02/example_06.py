from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class SignatureSnapshot:
    name: str
    pos_args: list[str]
    required_count: int
    kwonly_args: list[str]


def extract_signature(source_code: str, func_name: str) -> SignatureSnapshot:
    tree = ast.parse(source_code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            pos = [a.arg for a in node.args.posonlyargs + node.args.args]
            req_count = len(pos) - len(node.args.defaults)
            kwonly = [a.arg for a in node.args.kwonlyargs]
            return SignatureSnapshot(
                name=func_name,
                pos_args=pos,
                required_count=req_count,
                kwonly_args=kwonly,
            )
    raise ValueError(f"Function '{func_name}' not found")


def check_backward_compatibility(before: SignatureSnapshot, after: SignatureSnapshot) -> list[str]:
    warnings: list[str] = []
    if after.required_count > before.required_count:
        warnings.append(
            f"Breaking change: required positional args increased from "
            f"{before.required_count} to {after.required_count}"
        )
    removed_args = set(before.pos_args) - set(after.pos_args)
    if removed_args:
        warnings.append(f"Breaking change: removed positional args {sorted(removed_args)}")
    return warnings


if __name__ == "__main__":
    v1 = "def charge(user_id: str, cents: int) -> bool:\n    return True\n"
    v2_ok = "def charge(user_id: str, cents: int, currency: str = 'USD') -> bool:\n    return True\n"
    v2_break = "def charge(user_id: str, cents: int, currency: str) -> bool:\n    return True\n"

    s1 = extract_signature(v1, "charge")
    print("Compat check (defaulted arg):", check_backward_compatibility(s1, extract_signature(v2_ok, "charge")))
    print("Compat check (required arg): ", check_backward_compatibility(s1, extract_signature(v2_break, "charge")))

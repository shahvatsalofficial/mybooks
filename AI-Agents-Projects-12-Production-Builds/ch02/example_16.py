from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class ByteRange:
    start_byte: int
    end_byte: int
    node_type: str


def compute_line_offsets(source_bytes: bytes) -> list[int]:
    offsets = [0]
    for idx, byte_val in enumerate(source_bytes):
        if byte_val == 10:  # '\n'
            offsets.append(idx + 1)
    return offsets


def node_to_byte_range(source_code: str, func_name: str) -> ByteRange:
    raw = source_code.encode("utf-8")
    line_offsets = compute_line_offsets(raw)
    tree = ast.parse(source_code)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            start_line_idx = node.lineno - 1
            end_line_idx = (node.end_lineno or node.lineno) - 1
            start_b = line_offsets[start_line_idx] + node.col_offset
            end_col = getattr(node, "end_col_offset", 0) or 0
            end_b = line_offsets[end_line_idx] + end_col
            return ByteRange(start_byte=start_b, end_byte=end_b, node_type=type(node).__name__)
    raise ValueError(f"Symbol '{func_name}' not found in AST")


def splice_byte_range(source_code: str, byte_range: ByteRange, replacement: str) -> str:
    raw = source_code.encode("utf-8")
    updated = raw[: byte_range.start_byte] + replacement.encode("utf-8") + raw[byte_range.end_byte :]
    result = updated.decode("utf-8")
    ast.parse(result)
    return result


if __name__ == "__main__":
    original = (
        "# Header comment preserved verbatim\n"
        "def legacy_tax(amount: int) -> float:\n"
        "    return amount * 0.08\n\n"
        "# Footer comment preserved verbatim\n"
    )
    br = node_to_byte_range(original, "legacy_tax")
    new_fn = (
        "def legacy_tax(amount: int, rate: float = 0.08) -> float:\n"
        "    if amount < 0:\n"
        "        raise ValueError('amount must be non-negative')\n"
        "    return round(amount * rate, 2)"
    )
    patched = splice_byte_range(original, br, new_fn)
    print(f"Spliced {br.node_type} bytes=[{br.start_byte}:{br.end_byte}]")
    print(patched.strip())

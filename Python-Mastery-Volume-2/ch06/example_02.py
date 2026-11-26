"""
Recipe 06.1: Specialized Bytecode Quickening & Micro-Op JIT Inspector
Architecture: Introspects PEP 659 adaptive opcode specialization and inline caches.
Target Runtime: Python 3.12+ / 3.13+ (CPython)
"""

from __future__ import annotations
import dis
import io
import sys
from typing import Any, Callable


def inspect_adaptive_specialization(fn: Callable[..., Any], *args: Any) -> None:
    """Warms up a target function and displays opcode specialization transitions.
    
    Args:
        fn: The target Python function to inspect.
        args: Representative arguments to exercise the execution path.
    """
    print(f"=== BYTECODE INSPECTION FOR '{fn.__name__}' ===")

    # 1. Capture Cold Bytecode Disassembly
    buffer_cold = io.StringIO()
    dis.dis(fn, file=buffer_cold, adaptive=False)
    cold_instructions = buffer_cold.getvalue()

    print("\n--- 1. Cold Unspecialized Bytecode (Tier 0) ---")
    for line in cold_instructions.strip().splitlines()[:10]:
        print(f"  {line}")

    # 2. Warm up the function to trigger PEP 659 Quickening (>58 iterations)
    print("\nExecuting warmup loop (100 iterations) to trigger adaptive specialization...")
    for _ in range(100):
        fn(*args)

    # 3. Capture Specialized Bytecode Disassembly
    buffer_warm = io.StringIO()
    # adaptive=True displays specialized opcodes (e.g. BINARY_OP_ADD_INT)
    dis.dis(fn, file=buffer_warm, adaptive=True)
    warm_instructions = buffer_warm.getvalue()

    print("\n--- 2. Specialized Adaptive Bytecode (Tier 1 Quickened) ---")
    specialized_count = 0
    for line in warm_instructions.strip().splitlines():
        # Highlight specialized instructions
        if any(marker in line for marker in ("_INT", "_FLOAT", "_VALUE", "_ATTR", "_BUILTIN")):
            print(f"  >>> [SPECIALIZED] {line}")
            specialized_count += 1
        else:
            print(f"      {line}")

    print(f"\nTotal Specialized Opcodes Activated: {specialized_count}")


# Demonstration Target Function
def compute_vector_magnitude(x: int, y: int) -> int:
    """Arithmetic kernel with integer specialization targets."""
    return (x * x) + (y * y)


if __name__ == "__main__":
    inspect_adaptive_specialization(compute_vector_magnitude, 12, 16)
